# === RESEARCH MANAGER ADAPTER - BRIDGE BETWEEN OLD AND NEW ARCHITECTURES ===
# Purpose: Enable seamless integration of the new Manager-as-Agent architecture
# with existing UI code while maintaining backward compatibility

import asyncio
import logging
import time
import random
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

# Import both architectures
from research_manager import ResearchManager
from integrated_research_manager import IntegratedResearchManager
from performance_optimizer import performance_optimizer

# Import monitoring
from monitoring import metrics, alert_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchManagerAdapter:
    """Adapter to make IntegratedResearchManager compatible with existing UI"""
    
    def __init__(self, use_new_architecture: Optional[bool] = None, monitoring_enabled: bool = True):
        """Initialize adapter with architecture selection
        
        Args:
            use_new_architecture: True for new, False for old, None to check env var
            monitoring_enabled: Whether to enable performance monitoring
        """
        # Architecture selection
        if use_new_architecture is None:
            # Check environment variable with default to False (safe rollout)
            self.use_new = os.getenv("USE_NEW_ARCHITECTURE", "false").lower() == "true"
        else:
            self.use_new = use_new_architecture
        
        # Initialize managers
        self.old_manager = ResearchManager()
        self.new_manager = IntegratedResearchManager()
        
        # Monitoring configuration
        self.monitoring = monitoring_enabled
        self.comparison_metrics = {}
        
        # Shadow mode configuration (for A/B testing)
        self.shadow_mode_percentage = float(os.getenv("SHADOW_MODE_PERCENTAGE", "0.1"))
        
        logger.info(f"ResearchManagerAdapter initialized with:")
        logger.info(f"  Architecture: {'NEW (Manager-as-Agent)' if self.use_new else 'OLD (Procedural)'}")
        logger.info(f"  Monitoring: {self.monitoring}")
        logger.info(f"  Shadow mode: {self.shadow_mode_percentage * 100}%")
    
    async def run(self, query: str):
        """Run research with selected architecture
        
        Args:
            query: Research query to process
            
        Yields:
            str: Status updates and final report
        """
        start_time = time.time()
        architecture_used = "new" if self.use_new else "old"
        
        # Log architecture selection
        logger.info(f"Processing query with {architecture_used} architecture: {query[:100]}...")
        
        # Optionally run shadow comparison
        if self.monitoring and random.random() < self.shadow_mode_percentage:
            # Run both architectures in parallel for comparison
            asyncio.create_task(self._run_shadow_comparison(query))
        
        try:
            # Add architecture indicator to first yield
            yield f"🏗️ Using {'Intelligent Manager-as-Agent' if self.use_new else 'Standard Pipeline'} Architecture"
            
            # Execute with selected architecture
            if self.use_new:
                async for update in self.new_manager.run(query):
                    yield update
            else:
                async for update in self.old_manager.run(query):
                    yield update
            
            # Record successful execution
            execution_time = time.time() - start_time
            self._record_execution_metrics(query, architecture_used, execution_time, success=True)
            
        except Exception as e:
            # Record failure
            execution_time = time.time() - start_time
            self._record_execution_metrics(query, architecture_used, execution_time, success=False, error=str(e))
            
            # Re-raise to maintain original behavior
            raise
    
    async def _run_shadow_comparison(self, query: str):
        """Run both architectures in shadow mode for comparison
        
        Args:
            query: Research query to process
        """
        logger.info(f"Starting shadow comparison for query: {query[:50]}...")
        
        # Prepare comparison data
        comparison = {
            "query": query[:200],  # Truncate for storage
            "timestamp": datetime.now().isoformat(),
            "results": {}
        }
        
        # Run old architecture
        old_start = time.time()
        old_success = False
        old_word_count = 0
        
        try:
            old_updates = []
            async for update in self.old_manager.run(query):
                old_updates.append(update)
            
            # Extract word count from final report
            final_report = old_updates[-1] if old_updates else ""
            old_word_count = len(final_report.split())
            old_success = True
            
        except Exception as e:
            logger.warning(f"Shadow comparison - old architecture failed: {str(e)}")
        
        old_time = time.time() - old_start
        
        # Run new architecture
        new_start = time.time()
        new_success = False
        new_word_count = 0
        new_quality_score = 0.0
        
        try:
            new_updates = []
            async for update in self.new_manager.run(query):
                new_updates.append(update)
                # Extract quality score if present
                if "Quality score:" in update:
                    try:
                        new_quality_score = float(update.split("Quality score:")[1].split()[0].rstrip('%')) / 100
                    except:
                        pass
            
            # Extract word count from final report
            final_report = new_updates[-1] if new_updates else ""
            new_word_count = len(final_report.split())
            new_success = True
            
        except Exception as e:
            logger.warning(f"Shadow comparison - new architecture failed: {str(e)}")
        
        new_time = time.time() - new_start
        
        # Record comparison results
        comparison["results"] = {
            "old": {
                "success": old_success,
                "execution_time": old_time,
                "word_count": old_word_count
            },
            "new": {
                "success": new_success,
                "execution_time": new_time,
                "word_count": new_word_count,
                "quality_score": new_quality_score
            },
            "improvement": {
                "speed": (old_time - new_time) / old_time * 100 if old_time > 0 else 0,
                "success_rate": 1 if new_success and not old_success else 0
            }
        }
        
        # Log comparison results
        logger.info(f"Shadow comparison complete:")
        logger.info(f"  Old: {old_time:.2f}s, {old_word_count} words, success={old_success}")
        logger.info(f"  New: {new_time:.2f}s, {new_word_count} words, quality={new_quality_score:.2f}, success={new_success}")
        logger.info(f"  Speed improvement: {comparison['results']['improvement']['speed']:.1f}%")
        
        # Update comparison metrics
        if old_time > 0 and new_time > 0:
            speed_ratio = new_time / old_time
            quality_delta = new_quality_score - 0.5  # Assume 0.5 baseline for old
            metrics.update_comparison_metrics(speed_ratio, quality_delta)
        
        # Save comparison for analysis
        self._save_comparison_data(comparison)
    
    def _record_execution_metrics(self, query: str, architecture: str, execution_time: float, 
                                success: bool, error: Optional[str] = None, 
                                quality_score: Optional[float] = None):
        """Record execution metrics for monitoring
        
        Args:
            query: Research query
            architecture: "old" or "new"
            execution_time: Total execution time
            success: Whether execution succeeded
            error: Error message if failed
            quality_score: Quality score if available
        """
        # Record to Prometheus metrics
        status = "success" if success else "failure"
        metrics.record_request(architecture, status)
        metrics.record_duration(architecture, "total", execution_time)
        
        if quality_score is not None:
            metrics.record_quality(architecture, "research", quality_score)
        
        if error:
            metrics.record_error(architecture, error.split(':')[0], "total")
        
        # Check for performance degradation
        baseline_key = f"{architecture}_execution_time"
        if baseline_key in alert_manager.baseline_metrics:
            alert_manager.check_degradation(baseline_key, execution_time)
        else:
            # Set baseline after first 10 successful runs
            if architecture not in self.comparison_metrics:
                self.comparison_metrics[architecture] = {
                    "total_runs": 0,
                    "successful_runs": 0,
                    "total_time": 0.0,
                    "errors": []
                }
            
            if self.comparison_metrics[architecture]["successful_runs"] == 10:
                avg_time = (self.comparison_metrics[architecture]["total_time"] / 
                           self.comparison_metrics[architecture]["successful_runs"])
                alert_manager.set_baseline(baseline_key, avg_time)
        
        # Original metrics tracking
        metrics_data = {
            "timestamp": datetime.now().isoformat(),
            "architecture": architecture,
            "execution_time": execution_time,
            "success": success,
            "error": error,
            "query_length": len(query),
            "has_preferences": "Report Preferences:" in query
        }
        
        # Log to monitoring system
        logger.info(f"Execution metrics: {json.dumps(metrics_data)}")
        
        # Update in-memory metrics
        if architecture not in self.comparison_metrics:
            self.comparison_metrics[architecture] = {
                "total_runs": 0,
                "successful_runs": 0,
                "total_time": 0.0,
                "errors": []
            }
        
        self.comparison_metrics[architecture]["total_runs"] += 1
        if success:
            self.comparison_metrics[architecture]["successful_runs"] += 1
        else:
            self.comparison_metrics[architecture]["errors"].append(error)
        self.comparison_metrics[architecture]["total_time"] += execution_time
    
    def _save_comparison_data(self, comparison: Dict[str, Any]):
        """Save comparison data for later analysis
        
        Args:
            comparison: Comparison data to save
        """
        # Create comparisons directory if it doesn't exist
        os.makedirs("comparisons", exist_ok=True)
        
        # Save with timestamp-based filename
        filename = f"comparisons/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, "w") as f:
                json.dump(comparison, f, indent=2)
            logger.info(f"Saved comparison data to {filename}")
        except Exception as e:
            logger.error(f"Failed to save comparison data: {str(e)}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for both architectures
        
        Returns:
            Performance metrics comparison
        """
        summary = {"architectures": {}}
        
        for arch, metrics in self.comparison_metrics.items():
            if metrics["total_runs"] > 0:
                summary["architectures"][arch] = {
                    "total_runs": metrics["total_runs"],
                    "success_rate": metrics["successful_runs"] / metrics["total_runs"],
                    "avg_execution_time": metrics["total_time"] / metrics["total_runs"],
                    "error_count": len(metrics["errors"])
                }
        
        # Add comparison if both architectures have been used
        if len(summary["architectures"]) == 2:
            old_metrics = summary["architectures"].get("old", {})
            new_metrics = summary["architectures"].get("new", {})
            
            if old_metrics and new_metrics:
                summary["comparison"] = {
                    "speed_improvement": (
                        (old_metrics["avg_execution_time"] - new_metrics["avg_execution_time"]) / 
                        old_metrics["avg_execution_time"] * 100
                    ) if old_metrics.get("avg_execution_time", 0) > 0 else 0,
                    "reliability_delta": new_metrics.get("success_rate", 0) - old_metrics.get("success_rate", 0)
                }
        
        return summary
    
    def set_architecture(self, use_new: bool):
        """Dynamically switch architecture
        
        Args:
            use_new: True to use new architecture, False for old
        """
        self.use_new = use_new
        logger.info(f"Architecture switched to: {'NEW' if use_new else 'OLD'}")
    
    def get_current_architecture(self) -> str:
        """Get currently selected architecture
        
        Returns:
            "new" or "old"
        """
        return "new" if self.use_new else "old"

# === CONVENIENCE FUNCTIONS ===

async def run_research_with_adapter(query: str, use_new_architecture: Optional[bool] = None):
    """Convenience function to run research with the adapter
    
    Args:
        query: Research query
        use_new_architecture: Architecture selection (None = use env var)
        
    Yields:
        str: Status updates and final report
    """
    adapter = ResearchManagerAdapter(use_new_architecture=use_new_architecture)
    async for update in adapter.run(query):
        yield update

def get_adapter_instance() -> ResearchManagerAdapter:
    """Get a singleton adapter instance for the UI
    
    Returns:
        ResearchManagerAdapter instance
    """
    if not hasattr(get_adapter_instance, "_instance"):
        get_adapter_instance._instance = ResearchManagerAdapter()
    return get_adapter_instance._instance