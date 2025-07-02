# === RESEARCH HISTORY AND ANALYTICS MODULE ===
# Purpose: Track research history, provide analytics, and enable research comparison

# --- IMPORT DEPENDENCIES ---
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import pandas as pd
from collections import Counter
import logging

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- HISTORY CONFIGURATION ---
HISTORY_DIR = Path(".research_history")
MAX_HISTORY_ENTRIES = 1000
ANALYTICS_CACHE_HOURS = 1

class ResearchHistory:
    """Manages research history, analytics, and comparisons."""
    
    def __init__(self, history_dir: Path = HISTORY_DIR):
        """Initialize history manager."""
        self.history_dir = history_dir
        self.history_dir.mkdir(exist_ok=True)
        self.history_file = self.history_dir / "research_log.json"
        self.analytics_file = self.history_dir / "analytics_cache.json"
        self.history = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load research history from disk."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
        return []
    
    def _save_history(self):
        """Save research history to disk."""
        try:
            # Keep only recent entries
            if len(self.history) > MAX_HISTORY_ENTRIES:
                self.history = self.history[-MAX_HISTORY_ENTRIES:]
            
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    def add_research(self, query: str, report: str, metadata: Dict[str, Any]):
        """Add a research entry to history."""
        entry = {
            "id": hashlib.sha256(f"{query}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "report_preview": report[:500] + "..." if len(report) > 500 else report,
            "full_report": report,
            "metadata": {
                "word_count": metadata.get("word_count", len(report.split())),
                "search_count": metadata.get("search_count", 0),
                "report_format": metadata.get("report_format", "standard"),
                "target_audience": metadata.get("target_audience", "general"),
                "enhanced_features": metadata.get("enhanced_features", False),
                "cache_hits": metadata.get("cache_hits", 0),
                "processing_time": metadata.get("processing_time", 0)
            },
            "tags": self._extract_tags(query, report)
        }
        
        self.history.append(entry)
        self._save_history()
        
        # Invalidate analytics cache
        if self.analytics_file.exists():
            self.analytics_file.unlink()
        
        logger.info(f"Added research to history: {entry['id']}")
        return entry["id"]
    
    def _extract_tags(self, query: str, report: str) -> List[str]:
        """Extract relevant tags from query and report."""
        tags = []
        
        # Domain tags
        domain_keywords = {
            "military": ["military", "defense", "weapon", "army", "navy", "air force"],
            "crypto": ["crypto", "bitcoin", "blockchain", "defi", "token"],
            "ai": ["ai", "artificial intelligence", "machine learning", "llm", "agent"],
            "trading": ["trading", "options", "stocks", "market", "investment"]
        }
        
        combined_text = (query + " " + report).lower()
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                tags.append(domain)
        
        return tags
    
    def get_history(self, limit: int = 50, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get research history with optional filtering."""
        filtered_history = self.history
        
        # Filter by tags if specified
        if tags:
            filtered_history = [
                entry for entry in filtered_history
                if any(tag in entry.get("tags", []) for tag in tags)
            ]
        
        # Sort by timestamp (newest first)
        filtered_history.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Return limited results
        return filtered_history[:limit]
    
    def get_analytics(self) -> Dict[str, Any]:
        """Generate analytics from research history."""
        # Check cache
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r') as f:
                    cache = json.load(f)
                    cache_time = datetime.fromisoformat(cache["generated"])
                    if datetime.now() - cache_time < timedelta(hours=ANALYTICS_CACHE_HOURS):
                        return cache["analytics"]
            except:
                pass
        
        # Generate fresh analytics
        analytics = self._generate_analytics()
        
        # Cache results
        cache = {
            "generated": datetime.now().isoformat(),
            "analytics": analytics
        }
        
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(cache, f, indent=2)
        except:
            pass
        
        return analytics
    
    def _generate_analytics(self) -> Dict[str, Any]:
        """Generate comprehensive analytics from history."""
        if not self.history:
            return {"message": "No research history available"}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(self.history)
        
        # Time-based analytics
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['hour'] = df['timestamp'].dt.hour
        
        # Basic statistics
        total_researches = len(df)
        unique_days = df['date'].nunique()
        avg_per_day = total_researches / max(unique_days, 1)
        
        # Query analysis
        all_queries = " ".join(df['query'].tolist()).lower().split()
        common_terms = Counter(word for word in all_queries if len(word) > 4).most_common(10)
        
        # Tag distribution
        all_tags = []
        for tags in df['tags']:
            all_tags.extend(tags)
        tag_distribution = Counter(all_tags)
        
        # Metadata analysis
        metadata_df = pd.json_normalize(df['metadata'])
        
        analytics = {
            "summary": {
                "total_researches": total_researches,
                "unique_days": unique_days,
                "average_per_day": round(avg_per_day, 2),
                "total_words_generated": int(metadata_df['word_count'].sum()),
                "total_searches_performed": int(metadata_df['search_count'].sum()),
                "cache_hit_rate": round(metadata_df['cache_hits'].sum() / max(metadata_df['search_count'].sum(), 1), 2)
            },
            "temporal": {
                "researches_by_date": {str(k): v for k, v in df.groupby('date').size().to_dict().items()},
                "peak_hours": {str(k): v for k, v in df['hour'].value_counts().head(5).to_dict().items()},
                "recent_7_days": len(df[df['timestamp'] > datetime.now() - timedelta(days=7)])
            },
            "content": {
                "common_query_terms": dict(common_terms),
                "tag_distribution": dict(tag_distribution),
                "average_report_length": int(metadata_df['word_count'].mean()),
                "format_preferences": metadata_df['report_format'].value_counts().to_dict(),
                "audience_distribution": metadata_df['target_audience'].value_counts().to_dict()
            },
            "performance": {
                "average_processing_time": round(metadata_df['processing_time'].mean(), 2),
                "enhanced_features_usage": round(metadata_df['enhanced_features'].sum() / len(metadata_df), 2)
            }
        }
        
        return analytics
    
    def search_history(self, keyword: str) -> List[Dict[str, Any]]:
        """Search history by keyword in queries and reports."""
        keyword_lower = keyword.lower()
        results = []
        
        for entry in self.history:
            if keyword_lower in entry['query'].lower() or keyword_lower in entry['full_report'].lower():
                results.append({
                    "id": entry['id'],
                    "timestamp": entry['timestamp'],
                    "query": entry['query'],
                    "preview": entry['report_preview'],
                    "relevance": self._calculate_relevance(keyword_lower, entry)
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:20]
    
    def _calculate_relevance(self, keyword: str, entry: Dict[str, Any]) -> float:
        """Calculate relevance score for search results."""
        query_count = entry['query'].lower().count(keyword)
        report_count = entry['full_report'].lower().count(keyword)
        
        # Weight query matches higher
        return query_count * 3 + report_count
    
    def compare_researches(self, id1: str, id2: str) -> Dict[str, Any]:
        """Compare two research entries."""
        entry1 = next((e for e in self.history if e['id'] == id1), None)
        entry2 = next((e for e in self.history if e['id'] == id2), None)
        
        if not entry1 or not entry2:
            return {"error": "One or both research IDs not found"}
        
        comparison = {
            "research_1": {
                "id": id1,
                "query": entry1['query'],
                "timestamp": entry1['timestamp'],
                "word_count": entry1['metadata']['word_count'],
                "tags": entry1['tags']
            },
            "research_2": {
                "id": id2,
                "query": entry2['query'],
                "timestamp": entry2['timestamp'],
                "word_count": entry2['metadata']['word_count'],
                "tags": entry2['tags']
            },
            "similarities": {
                "common_tags": list(set(entry1['tags']) & set(entry2['tags'])),
                "time_difference": str(
                    datetime.fromisoformat(entry2['timestamp']) - 
                    datetime.fromisoformat(entry1['timestamp'])
                )
            }
        }
        
        return comparison
    
    def export_history(self, format: str = "json") -> str:
        """Export history in various formats."""
        if format == "json":
            return json.dumps(self.history, indent=2)
        
        elif format == "csv":
            # Flatten for CSV export
            flattened = []
            for entry in self.history:
                flat_entry = {
                    "id": entry["id"],
                    "timestamp": entry["timestamp"],
                    "query": entry["query"],
                    "word_count": entry["metadata"]["word_count"],
                    "tags": ", ".join(entry["tags"])
                }
                flattened.append(flat_entry)
            
            df = pd.DataFrame(flattened)
            return df.to_csv(index=False)
        
        else:
            return "Unsupported format"

# === SINGLETON HISTORY INSTANCE ===
research_history = ResearchHistory()

# === BENEFITS OF RESEARCH HISTORY ===
# 1. Knowledge Base: Build institutional memory of researches
# 2. Analytics: Understand usage patterns and preferences  
# 3. Efficiency: Quickly find and reuse previous research
# 4. Insights: Identify trending topics and gaps
# 5. Comparison: See how understanding evolves over time