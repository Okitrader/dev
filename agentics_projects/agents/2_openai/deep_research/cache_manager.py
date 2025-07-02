# === CACHE MANAGER FOR PERFORMANCE OPTIMIZATION ===
# Purpose: Implement intelligent caching to reduce API calls and improve response times

# --- IMPORT DEPENDENCIES ---
import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import asyncio
from pathlib import Path
import aiofiles

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CACHE CONFIGURATION ---
CACHE_DIR = Path(".research_cache")
CACHE_TTL_HOURS = 24  # Cache time-to-live
MAX_CACHE_SIZE_MB = 100  # Maximum cache size
SIMILARITY_THRESHOLD = 0.85  # For fuzzy query matching

class CacheManager:
    """Manages caching of search results and research reports."""
    
    def __init__(self, cache_dir: Path = CACHE_DIR):
        """Initialize cache manager with specified directory."""
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
        
        # Note: Cleanup will be done on first cache operation
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cache metadata: {e}")
        return {"entries": {}, "total_size_mb": 0}
    
    async def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(self.metadata, indent=2))
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _generate_cache_key(self, query: str, search_type: str = "search") -> str:
        """Generate a unique cache key for a query."""
        # Normalize query for better cache hits
        normalized = query.lower().strip()
        
        # Remove preferences section for base query caching
        if "Report Preferences:" in normalized:
            normalized = normalized.split("Report Preferences:")[0].strip()
        
        # Create hash
        key_string = f"{search_type}:{normalized}"
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    async def get_cached_search(self, query: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached search results if available and not expired."""
        cache_key = self._generate_cache_key(query, "search")
        
        if cache_key in self.metadata["entries"]:
            entry = self.metadata["entries"][cache_key]
            
            # Check if expired
            created_time = datetime.fromisoformat(entry["created"])
            if datetime.now() - created_time > timedelta(hours=CACHE_TTL_HOURS):
                logger.info(f"Cache expired for query: {query[:50]}...")
                await self._remove_entry(cache_key)
                return None
            
            # Load cached data
            cache_file = self.cache_dir / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    async with aiofiles.open(cache_file, 'r') as f:
                        data = json.loads(await f.read())
                    
                    logger.info(f"Cache hit for query: {query[:50]}...")
                    entry["hits"] = entry.get("hits", 0) + 1
                    entry["last_accessed"] = datetime.now().isoformat()
                    await self._save_metadata()
                    
                    return data
                except Exception as e:
                    logger.error(f"Failed to load cache file: {e}")
        
        return None
    
    async def cache_search_results(self, query: str, results: Dict[str, Any]):
        """Cache search results for future use."""
        cache_key = self._generate_cache_key(query, "search")
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Save cache file
            async with aiofiles.open(cache_file, 'w') as f:
                await f.write(json.dumps(results, indent=2))
            
            # Update metadata
            file_size_mb = cache_file.stat().st_size / (1024 * 1024)
            
            self.metadata["entries"][cache_key] = {
                "query": query[:100],  # Store truncated query
                "created": datetime.now().isoformat(),
                "last_accessed": datetime.now().isoformat(),
                "size_mb": file_size_mb,
                "hits": 0,
                "type": "search"
            }
            
            self.metadata["total_size_mb"] += file_size_mb
            
            # Check cache size limit
            if self.metadata["total_size_mb"] > MAX_CACHE_SIZE_MB:
                await self._evict_lru_entries()
            
            await self._save_metadata()
            logger.info(f"Cached search results for: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to cache search results: {e}")
    
    async def get_similar_queries(self, query: str, threshold: float = SIMILARITY_THRESHOLD) -> list:
        """Find similar cached queries using simple string similarity."""
        similar = []
        normalized_query = query.lower().strip()
        
        for cache_key, entry in self.metadata["entries"].items():
            cached_query = entry["query"].lower().strip()
            
            # Simple similarity check (can be enhanced with embeddings)
            common_words = set(normalized_query.split()) & set(cached_query.split())
            similarity = len(common_words) / max(len(normalized_query.split()), 
                                                  len(cached_query.split()))
            
            if similarity >= threshold:
                similar.append({
                    "cache_key": cache_key,
                    "query": entry["query"],
                    "similarity": similarity,
                    "created": entry["created"]
                })
        
        return sorted(similar, key=lambda x: x["similarity"], reverse=True)
    
    async def _cleanup_expired(self):
        """Remove expired cache entries."""
        expired_keys = []
        
        for cache_key, entry in self.metadata["entries"].items():
            created_time = datetime.fromisoformat(entry["created"])
            if datetime.now() - created_time > timedelta(hours=CACHE_TTL_HOURS):
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            await self._remove_entry(key)
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _evict_lru_entries(self):
        """Evict least recently used entries when cache is full."""
        # Sort by last accessed time
        entries = [(k, v) for k, v in self.metadata["entries"].items()]
        entries.sort(key=lambda x: x[1].get("last_accessed", x[1]["created"]))
        
        # Remove oldest entries until under size limit
        while self.metadata["total_size_mb"] > MAX_CACHE_SIZE_MB * 0.9:  # 90% threshold
            if not entries:
                break
            
            cache_key, _ = entries.pop(0)
            await self._remove_entry(cache_key)
    
    async def _remove_entry(self, cache_key: str):
        """Remove a cache entry."""
        if cache_key in self.metadata["entries"]:
            entry = self.metadata["entries"][cache_key]
            cache_file = self.cache_dir / f"{cache_key}.json"
            
            if cache_file.exists():
                cache_file.unlink()
            
            self.metadata["total_size_mb"] -= entry.get("size_mb", 0)
            del self.metadata["entries"][cache_key]
            await self._save_metadata()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.metadata["entries"])
        total_hits = sum(e.get("hits", 0) for e in self.metadata["entries"].values())
        
        return {
            "total_entries": total_entries,
            "total_size_mb": round(self.metadata["total_size_mb"], 2),
            "total_hits": total_hits,
            "cache_efficiency": round(total_hits / max(total_entries, 1), 2),
            "size_limit_mb": MAX_CACHE_SIZE_MB,
            "ttl_hours": CACHE_TTL_HOURS
        }

# === SINGLETON CACHE INSTANCE ===
cache_manager = CacheManager()

# === BENEFITS OF CACHING ===
# 1. Reduced API Costs: Fewer calls to search and LLM APIs
# 2. Faster Response: Instant results for repeated queries
# 3. Offline Capability: Can serve cached results when APIs are down
# 4. Query Learning: Track popular queries for optimization
# 5. Bandwidth Savings: Less data transfer for common searches