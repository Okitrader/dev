"""
Production Monitoring Module
Provides Prometheus metrics and health checks for the Deep Research System
"""

import time
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps

# Check if prometheus_client is available
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("prometheus_client not installed. Metrics will be logged only.")

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and exposes metrics for monitoring"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        self.start_time = time.time()
        
        if self.enabled:
            # Request metrics
            self.request_count = Counter(
                'deep_research_requests_total',
                'Total number of research requests',
                ['architecture', 'status']
            )
            
            self.request_duration = Histogram(
                'deep_research_request_duration_seconds',
                'Request duration in seconds',
                ['architecture', 'agent'],
                buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120, 300)
            )
            
            # Quality metrics
            self.quality_score = Histogram(
                'deep_research_quality_score',
                'Report quality scores',
                ['architecture', 'report_type'],
                buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0)
            )
            
            # Cache metrics
            self.cache_hits = Counter(
                'deep_research_cache_hits_total',
                'Total cache hits',
                ['cache_type']
            )
            
            self.cache_misses = Counter(
                'deep_research_cache_misses_total',
                'Total cache misses',
                ['cache_type']
            )
            
            # Error metrics
            self.errors = Counter(
                'deep_research_errors_total',
                'Total errors',
                ['architecture', 'error_type', 'agent']
            )
            
            # Performance comparison metrics
            self.architecture_comparison = Gauge(
                'deep_research_architecture_speed_ratio',
                'Speed ratio between new and old architecture (new/old)'
            )
            
            self.architecture_quality_delta = Gauge(
                'deep_research_architecture_quality_delta',
                'Quality score difference (new - old)'
            )
            
            # System metrics
            self.active_requests = Gauge(
                'deep_research_active_requests',
                'Number of active requests'
            )
            
            self.uptime = Gauge(
                'deep_research_uptime_seconds',
                'Uptime in seconds'
            )
    
    def record_request(self, architecture: str, status: str):
        """Record a request"""
        if self.enabled:
            self.request_count.labels(architecture=architecture, status=status).inc()
        else:
            logger.info(f"Request recorded: architecture={architecture}, status={status}")
    
    def record_duration(self, architecture: str, agent: str, duration: float):
        """Record operation duration"""
        if self.enabled:
            self.request_duration.labels(architecture=architecture, agent=agent).observe(duration)
        else:
            logger.info(f"Duration recorded: architecture={architecture}, agent={agent}, duration={duration:.2f}s")
    
    def record_quality(self, architecture: str, report_type: str, score: float):
        """Record quality score"""
        if self.enabled:
            self.quality_score.labels(architecture=architecture, report_type=report_type).observe(score)
        else:
            logger.info(f"Quality recorded: architecture={architecture}, type={report_type}, score={score:.2f}")
    
    def record_cache_hit(self, cache_type: str = "search"):
        """Record cache hit"""
        if self.enabled:
            self.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str = "search"):
        """Record cache miss"""
        if self.enabled:
            self.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_error(self, architecture: str, error_type: str, agent: str = "unknown"):
        """Record an error"""
        if self.enabled:
            self.errors.labels(
                architecture=architecture,
                error_type=error_type,
                agent=agent
            ).inc()
        else:
            logger.error(f"Error recorded: architecture={architecture}, type={error_type}, agent={agent}")
    
    def update_comparison_metrics(self, speed_ratio: float, quality_delta: float):
        """Update architecture comparison metrics"""
        if self.enabled:
            self.architecture_comparison.set(speed_ratio)
            self.architecture_quality_delta.set(quality_delta)
        else:
            logger.info(f"Comparison metrics: speed_ratio={speed_ratio:.2f}, quality_delta={quality_delta:.2f}")
    
    def set_active_requests(self, count: int):
        """Set number of active requests"""
        if self.enabled:
            self.active_requests.set(count)
    
    def update_uptime(self):
        """Update uptime metric"""
        if self.enabled:
            self.uptime.set(time.time() - self.start_time)
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics"""
        if self.enabled:
            self.update_uptime()
            return generate_latest()
        return b"# Metrics not available (prometheus_client not installed)\n"

# Global metrics instance
metrics = MetricsCollector(enabled=os.getenv("ENABLE_METRICS", "true").lower() == "true")

def track_duration(architecture: str, agent: str):
    """Decorator to track function duration"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                metrics.record_duration(architecture, agent, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                metrics.record_duration(architecture, agent, duration)
                metrics.record_error(architecture, type(e).__name__, agent)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                metrics.record_duration(architecture, agent, duration)
                return result
            except Exception as e:
                duration = time.time() - start
                metrics.record_duration(architecture, agent, duration)
                metrics.record_error(architecture, type(e).__name__, agent)
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator

class HealthChecker:
    """Health check implementation"""
    
    def __init__(self):
        self.checks = {}
        
    def add_check(self, name: str, check_func):
        """Add a health check"""
        self.checks[name] = check_func
    
    async def check_health(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                results["checks"][name] = {
                    "status": "healthy" if result else "unhealthy",
                    "result": result
                }
                if not result:
                    results["status"] = "unhealthy"
            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["status"] = "unhealthy"
        
        return results

# Global health checker
health_checker = HealthChecker()

# Add default health checks
def check_disk_space():
    """Check if there's enough disk space"""
    import shutil
    stat = shutil.disk_usage(".")
    # Warn if less than 10% free
    return (stat.free / stat.total) > 0.1

def check_memory():
    """Check memory usage"""
    try:
        import psutil
        return psutil.virtual_memory().percent < 90
    except ImportError:
        return True  # Assume OK if psutil not available

health_checker.add_check("disk_space", check_disk_space)
health_checker.add_check("memory", check_memory)

# Alert manager integration
class AlertManager:
    """Manages alerts for performance degradation"""
    
    def __init__(self, threshold_percentage: float = 20.0):
        self.threshold = threshold_percentage / 100.0
        self.baseline_metrics = {}
        self.alerts = []
        
    def set_baseline(self, metric_name: str, value: float):
        """Set baseline for a metric"""
        self.baseline_metrics[metric_name] = value
        
    def check_degradation(self, metric_name: str, current_value: float) -> Optional[str]:
        """Check if metric has degraded beyond threshold"""
        if metric_name not in self.baseline_metrics:
            return None
            
        baseline = self.baseline_metrics[metric_name]
        if baseline == 0:
            return None
            
        degradation = (current_value - baseline) / baseline
        
        if degradation > self.threshold:
            alert = f"ALERT: {metric_name} degraded by {degradation*100:.1f}% (threshold: {self.threshold*100}%)"
            self.alerts.append({
                "timestamp": datetime.now().isoformat(),
                "metric": metric_name,
                "baseline": baseline,
                "current": current_value,
                "degradation_percentage": degradation * 100,
                "message": alert
            })
            logger.warning(alert)
            return alert
        
        return None
    
    def get_alerts(self, last_n: int = 10) -> list:
        """Get recent alerts"""
        return self.alerts[-last_n:]

# Global alert manager
alert_manager = AlertManager(threshold_percentage=float(os.getenv("ALERT_THRESHOLD_PERCENTAGE", "20")))

# Import asyncio for async support
import asyncio