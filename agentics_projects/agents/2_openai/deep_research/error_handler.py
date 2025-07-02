# === ENHANCED ERROR HANDLING FOR ROBUST RESEARCH PIPELINE ===
# Purpose: Implement comprehensive error handling with retry logic, fallbacks, and user-friendly messages

# --- IMPORT DEPENDENCIES ---
import asyncio
import logging
from typing import Optional, Any, Callable, Dict, List
from datetime import datetime
import traceback
from functools import wraps
import random

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ERROR CATEGORIES ---
class ErrorCategory:
    """Categorize errors for appropriate handling."""
    NETWORK = "network"
    API_LIMIT = "api_limit"
    AUTHENTICATION = "authentication"
    PARSING = "parsing"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"

# --- RETRY CONFIGURATION ---
RETRY_CONFIG = {
    ErrorCategory.NETWORK: {"max_retries": 3, "base_delay": 1, "max_delay": 10},
    ErrorCategory.API_LIMIT: {"max_retries": 5, "base_delay": 5, "max_delay": 60},
    ErrorCategory.TIMEOUT: {"max_retries": 2, "base_delay": 2, "max_delay": 10},
    ErrorCategory.PARSING: {"max_retries": 1, "base_delay": 0, "max_delay": 0},
    ErrorCategory.AUTHENTICATION: {"max_retries": 0, "base_delay": 0, "max_delay": 0},
    ErrorCategory.UNKNOWN: {"max_retries": 1, "base_delay": 1, "max_delay": 5}
}

# --- USER-FRIENDLY ERROR MESSAGES ---
USER_MESSAGES = {
    ErrorCategory.NETWORK: "Network connection issue. Retrying...",
    ErrorCategory.API_LIMIT: "API rate limit reached. Waiting before retry...",
    ErrorCategory.AUTHENTICATION: "Authentication failed. Please check your API keys.",
    ErrorCategory.PARSING: "Failed to process response. Trying alternative approach...",
    ErrorCategory.TIMEOUT: "Request timed out. Attempting again...",
    ErrorCategory.UNKNOWN: "Unexpected error occurred. Attempting recovery..."
}

class ErrorHandler:
    """Centralized error handling with retry logic and fallbacks."""
    
    def __init__(self):
        self.error_history: List[Dict[str, Any]] = []
        self.fallback_strategies: Dict[str, List[Callable]] = {}
    
    def categorize_error(self, error: Exception) -> str:
        """Categorize error for appropriate handling strategy."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Network errors
        if any(term in error_str for term in ["connection", "network", "refused", "unreachable"]):
            return ErrorCategory.NETWORK
        
        # API rate limits
        if any(term in error_str for term in ["rate limit", "429", "too many requests"]):
            return ErrorCategory.API_LIMIT
        
        # Authentication errors
        if any(term in error_str for term in ["401", "403", "unauthorized", "forbidden", "api key"]):
            return ErrorCategory.AUTHENTICATION
        
        # Timeout errors
        if any(term in error_str for term in ["timeout", "timed out"]):
            return ErrorCategory.TIMEOUT
        
        # Parsing errors
        if any(term in error_str for term in ["parse", "json", "decode", "invalid response"]):
            return ErrorCategory.PARSING
        
        return ErrorCategory.UNKNOWN
    
    async def handle_with_retry(self, func: Callable, *args, **kwargs) -> Optional[Any]:
        """Execute function with intelligent retry logic."""
        last_error = None
        category = ErrorCategory.UNKNOWN
        
        # Get retry configuration
        for attempt in range(5):  # Maximum attempts across all retries
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                last_error = e
                category = self.categorize_error(e)
                retry_config = RETRY_CONFIG[category]
                
                # Log error
                self.log_error(e, category, attempt)
                
                # Check if we should retry
                if attempt >= retry_config["max_retries"]:
                    break
                
                # Calculate delay with exponential backoff and jitter
                delay = min(
                    retry_config["base_delay"] * (2 ** attempt) + random.uniform(0, 1),
                    retry_config["max_delay"]
                )
                
                logger.info(f"Retrying after {delay:.1f}s (attempt {attempt + 1}/{retry_config['max_retries']})")
                await asyncio.sleep(delay)
        
        # All retries failed - try fallback
        return await self.try_fallback(func.__name__, last_error, *args, **kwargs)
    
    def log_error(self, error: Exception, category: str, attempt: int):
        """Log error with context for debugging."""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "attempt": attempt
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"[{category}] {type(error).__name__}: {str(error)} (attempt {attempt})")
    
    async def try_fallback(self, func_name: str, error: Exception, *args, **kwargs) -> Optional[Any]:
        """Try fallback strategies when primary function fails."""
        if func_name in self.fallback_strategies:
            for fallback in self.fallback_strategies[func_name]:
                try:
                    logger.info(f"Trying fallback strategy for {func_name}")
                    result = await fallback(*args, **kwargs)
                    return result
                except Exception as e:
                    logger.error(f"Fallback failed: {e}")
                    continue
        
        # No fallback available or all failed
        raise error
    
    def register_fallback(self, func_name: str, fallback: Callable):
        """Register a fallback strategy for a function."""
        if func_name not in self.fallback_strategies:
            self.fallback_strategies[func_name] = []
        self.fallback_strategies[func_name].append(fallback)
    
    def get_user_message(self, error: Exception) -> str:
        """Get user-friendly error message."""
        category = self.categorize_error(error)
        return USER_MESSAGES.get(category, "An error occurred. Please try again.")
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        if not self.error_history:
            return {"total_errors": 0, "categories": {}}
        
        stats = {
            "total_errors": len(self.error_history),
            "categories": {},
            "recent_errors": self.error_history[-5:]
        }
        
        for error in self.error_history:
            category = error["category"]
            if category not in stats["categories"]:
                stats["categories"][category] = 0
            stats["categories"][category] += 1
        
        return stats

# --- DECORATOR FOR AUTOMATIC ERROR HANDLING ---
def with_error_handling(error_handler: ErrorHandler):
    """Decorator to add error handling to async functions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.handle_with_retry(func, *args, **kwargs)
        return wrapper
    return decorator

# --- SINGLETON ERROR HANDLER ---
error_handler = ErrorHandler()

# === FALLBACK SEARCH ENGINES ===
async def fallback_search_duckduckgo(query: str) -> str:
    """Fallback search using DuckDuckGo (simplified example)."""
    # This would implement actual DuckDuckGo search
    return f"[FALLBACK] Limited results for: {query}"

async def fallback_search_cached_similar(query: str) -> str:
    """Fallback using similar cached queries."""
    from cache_manager import cache_manager
    similar = await cache_manager.get_similar_queries(query, threshold=0.7)
    if similar:
        return f"[SIMILAR] Results based on: {similar[0]['query']}"
    return None

# Register fallbacks
error_handler.register_fallback("search", fallback_search_duckduckgo)
error_handler.register_fallback("search", fallback_search_cached_similar)

# === BENEFITS OF ENHANCED ERROR HANDLING ===
# 1. Resilience: System continues despite failures
# 2. User Experience: Clear, actionable error messages
# 3. Debugging: Comprehensive error logging
# 4. Recovery: Automatic retry with smart backoff
# 5. Fallbacks: Alternative strategies when primary fails