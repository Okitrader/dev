# === PERFORMANCE OPTIMIZER - TRACKING AND OPTIMIZATION ===
# Purpose: Monitor performance, learn patterns, and optimize agent workflows

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import statistics
import logging
from collections import defaultdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === PERFORMANCE DIMENSIONS ===
class PerformanceDimension(Enum):
    SPEED = "speed"
    QUALITY = "quality"
    COST = "cost"
    RELIABILITY = "reliability"

# === OPTIMIZATION STRATEGIES ===
class OptimizationStrategy(Enum):
    CACHE_HEAVY = "cache_heavy"  # Maximize cache usage
    QUALITY_FIRST = "quality_first"  # Prioritize quality over speed
    SPEED_OPTIMIZED = "speed_optimized"  # Minimize execution time
    BALANCED = "balanced"  # Balance all dimensions
    ADAPTIVE = "adaptive"  # Learn and adapt

# === PERFORMANCE RECORD ===
@dataclass
class PerformanceRecord:
    """Record of a single workflow execution"""
    workflow_id: str
    query: str
    agent_sequence: List[str]
    start_time: datetime
    end_time: datetime
    total_duration: float
    agent_metrics: Dict[str, Dict[str, Any]]  # Per-agent metrics
    overall_quality: float
    cache_hits: int
    total_tokens: int
    error_count: int
    successful: bool

# === PATTERN DETECTION ===
@dataclass
class PerformancePattern:
    """Detected pattern in performance data"""
    pattern_type: str  # e.g., "slow_search", "quality_drop", "cache_effective"
    conditions: Dict[str, Any]
    impact: Dict[str, float]  # Impact on each dimension
    frequency: int
    confidence: float
    recommendation: str

# === OPTIMIZATION RULE ===
@dataclass
class OptimizationRule:
    """Rule for optimizing workflows"""
    rule_id: str
    condition: Dict[str, Any]  # When to apply
    action: Dict[str, Any]  # What to do
    expected_improvement: Dict[str, float]
    success_rate: float = 0.0
    applications: int = 0

# === PERFORMANCE OPTIMIZER CLASS ===
class PerformanceOptimizer:
    """Tracks performance and suggests optimizations"""
    
    def __init__(self, history_size: int = 1000):
        self.performance_history: List[PerformanceRecord] = []
        self.patterns: List[PerformancePattern] = []
        self.optimization_rules: List[OptimizationRule] = []
        self.history_size = history_size
        
        # Performance baselines
        self.baselines = {
            PerformanceDimension.SPEED: 30.0,  # seconds
            PerformanceDimension.QUALITY: 0.8,  # 0-1 scale
            PerformanceDimension.COST: 1000,  # tokens
            PerformanceDimension.RELIABILITY: 0.95  # success rate
        }
        
        # Initialize default optimization rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize with proven optimization rules"""
        self.optimization_rules.extend([
            OptimizationRule(
                rule_id="skip_clarifier_simple",
                condition={"query_words": {"<": 10}, "query_complexity": "simple"},
                action={"skip_agent": "clarifier"},
                expected_improvement={PerformanceDimension.SPEED.value: 0.2}
            ),
            OptimizationRule(
                rule_id="use_enhanced_complex",
                condition={"query_complexity": "complex", "quality_requirement": "high"},
                action={"use_enhanced": True},
                expected_improvement={PerformanceDimension.QUALITY.value: 0.15}
            ),
            OptimizationRule(
                rule_id="parallel_search_many",
                condition={"search_count": {">": 5}},
                action={"parallel_execution": True, "batch_size": 3},
                expected_improvement={PerformanceDimension.SPEED.value: 0.4}
            ),
            OptimizationRule(
                rule_id="cache_similar_queries",
                condition={"similarity_score": {">": 0.9}},
                action={"use_cache": True, "cache_strategy": "aggressive"},
                expected_improvement={PerformanceDimension.SPEED.value: 0.8}
            )
        ])
    
    def record_performance(self, record: PerformanceRecord):
        """Record a workflow execution"""
        self.performance_history.append(record)
        
        # Maintain history size limit
        if len(self.performance_history) > self.history_size:
            self.performance_history = self.performance_history[-self.history_size:]
        
        # Update patterns after new record
        self._detect_patterns()
        
        # Log performance summary
        logger.info(f"Performance recorded for workflow {record.workflow_id}:")
        logger.info(f"  Duration: {record.total_duration:.2f}s")
        logger.info(f"  Quality: {record.overall_quality:.2f}")
        logger.info(f"  Cache hits: {record.cache_hits}")
        logger.info(f"  Tokens: {record.total_tokens}")
    
    def _detect_patterns(self):
        """Detect patterns in recent performance data"""
        if len(self.performance_history) < 10:
            return
        
        recent_records = self.performance_history[-50:]
        
        # Pattern 1: Slow searches
        slow_searches = [r for r in recent_records 
                        if "search" in r.agent_metrics and 
                        r.agent_metrics["search"].get("execution_time", 0) > 10]
        
        if len(slow_searches) > 5:
            pattern = PerformancePattern(
                pattern_type="slow_search",
                conditions={"search_time": ">10s"},
                impact={PerformanceDimension.SPEED.value: -0.3},
                frequency=len(slow_searches),
                confidence=0.8,
                recommendation="Consider using cached results or reducing search scope"
            )
            self._add_or_update_pattern(pattern)
        
        # Pattern 2: Quality drops with fast track
        fast_track_records = [r for r in recent_records 
                            if len(r.agent_sequence) < 4]
        
        if fast_track_records:
            avg_quality = statistics.mean([r.overall_quality for r in fast_track_records])
            if avg_quality < 0.7:
                pattern = PerformancePattern(
                    pattern_type="fast_track_quality_drop",
                    conditions={"agent_count": "<4", "avg_quality": avg_quality},
                    impact={PerformanceDimension.QUALITY.value: -0.2},
                    frequency=len(fast_track_records),
                    confidence=0.9,
                    recommendation="Use standard workflow for better quality"
                )
                self._add_or_update_pattern(pattern)
        
        # Pattern 3: Cache effectiveness
        cache_heavy_records = [r for r in recent_records if r.cache_hits > 2]
        if cache_heavy_records:
            avg_speed_improvement = statistics.mean([
                r.total_duration for r in recent_records if r.cache_hits == 0
            ]) / statistics.mean([r.total_duration for r in cache_heavy_records])
            
            if avg_speed_improvement > 1.5:
                pattern = PerformancePattern(
                    pattern_type="cache_effective",
                    conditions={"cache_hits": ">2"},
                    impact={PerformanceDimension.SPEED.value: avg_speed_improvement - 1},
                    frequency=len(cache_heavy_records),
                    confidence=0.85,
                    recommendation="Maximize cache usage for similar queries"
                )
                self._add_or_update_pattern(pattern)
        
        # Pattern 4: Enhanced agent quality improvement
        enhanced_records = [r for r in recent_records 
                          if any("enhanced" in agent for agent in r.agent_sequence)]
        standard_records = [r for r in recent_records 
                          if not any("enhanced" in agent for agent in r.agent_sequence)]
        
        if enhanced_records and standard_records:
            enhanced_quality = statistics.mean([r.overall_quality for r in enhanced_records])
            standard_quality = statistics.mean([r.overall_quality for r in standard_records])
            
            if enhanced_quality > standard_quality * 1.15:
                pattern = PerformancePattern(
                    pattern_type="enhanced_agent_benefit",
                    conditions={"uses_enhanced": True},
                    impact={PerformanceDimension.QUALITY.value: enhanced_quality - standard_quality},
                    frequency=len(enhanced_records),
                    confidence=0.9,
                    recommendation="Use enhanced agents for complex queries requiring high quality"
                )
                self._add_or_update_pattern(pattern)
        
        # Pattern 5: Error correlation with complexity
        error_records = [r for r in recent_records if r.error_count > 0]
        if error_records:
            complex_errors = [r for r in error_records 
                            if len(r.agent_sequence) > 5 or "complex" in r.query.lower()]
            
            if len(complex_errors) / len(error_records) > 0.7:
                pattern = PerformancePattern(
                    pattern_type="complexity_error_correlation",
                    conditions={"high_complexity": True, "error_prone": True},
                    impact={PerformanceDimension.RELIABILITY.value: -0.3},
                    frequency=len(complex_errors),
                    confidence=0.75,
                    recommendation="Break down complex queries into smaller sub-tasks"
                )
                self._add_or_update_pattern(pattern)
    
    def _add_or_update_pattern(self, new_pattern: PerformancePattern):
        """Add new pattern or update existing one"""
        for i, pattern in enumerate(self.patterns):
            if pattern.pattern_type == new_pattern.pattern_type:
                self.patterns[i] = new_pattern
                return
        self.patterns.append(new_pattern)
    
    def get_optimization_suggestions(self, query: str, 
                                   query_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get optimization suggestions for a query"""
        suggestions = []
        
        # Check each optimization rule
        for rule in self.optimization_rules:
            if self._rule_applies(rule, query_analysis):
                suggestions.append({
                    "rule_id": rule.rule_id,
                    "action": rule.action,
                    "expected_improvement": rule.expected_improvement,
                    "confidence": rule.success_rate if rule.applications > 0 else 0.5
                })
        
        # Add pattern-based suggestions
        for pattern in self.patterns:
            if pattern.confidence > 0.7:
                suggestions.append({
                    "pattern": pattern.pattern_type,
                    "recommendation": pattern.recommendation,
                    "impact": pattern.impact,
                    "confidence": pattern.confidence
                })
        
        # Sort by expected impact
        suggestions.sort(key=lambda s: sum(s.get("expected_improvement", {}).values()), reverse=True)
        
        return suggestions[:5]  # Top 5 suggestions
    
    def _rule_applies(self, rule: OptimizationRule, query_analysis: Dict[str, Any]) -> bool:
        """Check if a rule applies to the current context"""
        for key, condition in rule.condition.items():
            if key not in query_analysis:
                return False
            
            value = query_analysis[key]
            
            if isinstance(condition, dict):
                # Handle comparison operators
                for op, threshold in condition.items():
                    if op == "<" and not (value < threshold):
                        return False
                    elif op == ">" and not (value > threshold):
                        return False
                    elif op == "==" and not (value == threshold):
                        return False
            else:
                # Direct comparison
                if value != condition:
                    return False
        
        return True
    
    def update_rule_performance(self, rule_id: str, success: bool, actual_improvement: Dict[str, float]):
        """Update rule performance based on actual results"""
        for rule in self.optimization_rules:
            if rule.rule_id == rule_id:
                rule.applications += 1
                
                # Update success rate
                if success:
                    rule.success_rate = (
                        (rule.success_rate * (rule.applications - 1) + 1.0) / 
                        rule.applications
                    )
                else:
                    rule.success_rate = (
                        (rule.success_rate * (rule.applications - 1)) / 
                        rule.applications
                    )
                
                # Update expected improvement based on actual
                for dim, improvement in actual_improvement.items():
                    if dim in rule.expected_improvement:
                        # Exponential moving average
                        alpha = 0.3
                        rule.expected_improvement[dim] = (
                            alpha * improvement + 
                            (1 - alpha) * rule.expected_improvement[dim]
                        )
                
                logger.info(f"Updated rule {rule_id}: success_rate={rule.success_rate:.2f}")
                break
    
    def track_cache_performance(self, query: str, cache_hit: bool, execution_time: float):
        """Track cache performance metrics"""
        # Find similar recent queries
        similar_queries = []
        for record in self.performance_history[-100:]:
            if record.query and self._calculate_similarity(query, record.query) > 0.8:
                similar_queries.append(record)
        
        if similar_queries:
            # Calculate average performance improvement from cache
            no_cache_avg = statistics.mean([r.total_duration for r in similar_queries if r.cache_hits == 0] or [execution_time])
            cache_avg = statistics.mean([r.total_duration for r in similar_queries if r.cache_hits > 0] or [execution_time])
            
            if no_cache_avg > 0 and cache_avg > 0:
                cache_speedup = no_cache_avg / cache_avg
                logger.info(f"Cache performance: {cache_speedup:.2f}x speedup for similar queries")
                
                # Update cache optimization rule
                for rule in self.optimization_rules:
                    if rule.rule_id == "cache_similar_queries":
                        rule.expected_improvement[PerformanceDimension.SPEED.value] = max(0.8, cache_speedup - 1)
                        break
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Simple similarity calculation between queries"""
        # Basic word overlap similarity
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def get_performance_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """Get performance summary statistics"""
        if not self.performance_history:
            return {"status": "no_data"}
        
        # Filter by time window if specified
        records = self.performance_history
        if time_window:
            cutoff_time = datetime.now() - time_window
            records = [r for r in records if r.start_time > cutoff_time]
        
        if not records:
            return {"status": "no_data_in_window"}
        
        # Calculate statistics
        summary = {
            "total_workflows": len(records),
            "success_rate": sum(1 for r in records if r.successful) / len(records),
            "avg_duration": statistics.mean([r.total_duration for r in records]),
            "avg_quality": statistics.mean([r.overall_quality for r in records]),
            "avg_tokens": statistics.mean([r.total_tokens for r in records]),
            "cache_utilization": sum(r.cache_hits for r in records) / len(records),
            "error_rate": sum(r.error_count for r in records) / len(records)
        }
        
        # Add percentiles for duration
        durations = sorted([r.total_duration for r in records])
        summary["duration_p50"] = durations[len(durations) // 2]
        summary["duration_p90"] = durations[int(len(durations) * 0.9)]
        summary["duration_p95"] = durations[int(len(durations) * 0.95)]
        
        # Add agent-specific stats
        agent_stats = defaultdict(lambda: {"count": 0, "avg_time": 0, "errors": 0})
        for record in records:
            for agent, metrics in record.agent_metrics.items():
                agent_stats[agent]["count"] += 1
                agent_stats[agent]["avg_time"] += metrics.get("execution_time", 0)
                if metrics.get("error"):
                    agent_stats[agent]["errors"] += 1
        
        # Calculate averages
        for agent, stats in agent_stats.items():
            if stats["count"] > 0:
                stats["avg_time"] /= stats["count"]
                stats["error_rate"] = stats["errors"] / stats["count"]
        
        summary["agent_stats"] = dict(agent_stats)
        
        return summary
    
    def predict_performance(self, query_analysis: Dict[str, Any], 
                          agent_sequence: List[str]) -> Dict[str, float]:
        """Predict performance for a given workflow"""
        predictions = {
            PerformanceDimension.SPEED.value: 0.0,
            PerformanceDimension.QUALITY.value: 0.0,
            PerformanceDimension.COST.value: 0.0,
            PerformanceDimension.RELIABILITY.value: 1.0
        }
        
        # Base predictions on agent sequence - updated to match actual agent names
        agent_times = {
            "clarifier": 3.0,
            "planner": 4.0,
            "enhanced_planner": 5.0,
            "search": 8.0,
            "enhanced_search": 12.0,
            "writer": 6.0,
            "enhanced_writer": 8.0,
            "email": 2.0,
            "followup": 3.0
        }
        
        # Calculate expected duration
        for agent in agent_sequence:
            predictions[PerformanceDimension.SPEED.value] += agent_times.get(agent, 5.0)
        
        # Adjust for parallelization
        search_count = agent_sequence.count("search") + agent_sequence.count("enhanced_search")
        if search_count > 1:
            predictions[PerformanceDimension.SPEED.value] -= (search_count - 1) * 5.0
        
        # Quality prediction based on agent selection
        if "enhanced_search" in agent_sequence or "enhanced_writer" in agent_sequence:
            predictions[PerformanceDimension.QUALITY.value] = 0.85
        else:
            predictions[PerformanceDimension.QUALITY.value] = 0.75
        
        # Adjust quality based on clarifier usage
        if "clarifier" in agent_sequence:
            predictions[PerformanceDimension.QUALITY.value] += 0.05
        
        # Cost prediction (tokens) - updated based on actual usage patterns
        base_tokens = {
            "clarifier": 200,
            "planner": 300,
            "enhanced_planner": 400,
            "search": 500,
            "enhanced_search": 800,
            "writer": 1000,
            "enhanced_writer": 1500,
            "email": 200,
            "followup": 300
        }
        
        for agent in agent_sequence:
            predictions[PerformanceDimension.COST.value] += base_tokens.get(agent, 400)
        
        # Reliability based on historical data
        if self.performance_history:
            similar_workflows = [
                r for r in self.performance_history[-100:]
                if set(r.agent_sequence) == set(agent_sequence)
            ]
            if similar_workflows:
                predictions[PerformanceDimension.RELIABILITY.value] = (
                    sum(1 for r in similar_workflows if r.successful) / len(similar_workflows)
                )
        
        return predictions
    
    def calculate_quality_score(self, report_data: Dict[str, Any]) -> float:
        """Calculate quality score based on report characteristics"""
        score = 0.0
        
        # Word count (optimal range: 800-1500)
        word_count = report_data.get("word_count", 0)
        if 800 <= word_count <= 1500:
            score += 0.3
        elif 500 <= word_count < 800:
            score += 0.2
        elif word_count > 1500:
            score += 0.25
        else:
            score += 0.1
        
        # Search count (more sources = better)
        search_count = report_data.get("search_count", 0)
        if search_count >= 5:
            score += 0.3
        elif search_count >= 3:
            score += 0.2
        else:
            score += 0.1
        
        # Source diversity (from enhanced search)
        source_diversity = report_data.get("source_diversity", {})
        if source_diversity.get("total_domains", 0) >= 5:
            score += 0.2
        elif source_diversity.get("total_domains", 0) >= 3:
            score += 0.1
        
        # Report structure
        report_text = report_data.get("markdown_report", "")
        if "##" in report_text:  # Has sections
            score += 0.1
        if "###" in report_text:  # Has subsections
            score += 0.05
        if "- " in report_text or "* " in report_text:  # Has lists
            score += 0.05
        
        return min(score, 1.0)
    
    def get_agent_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for agent improvements"""
        if len(self.performance_history) < 20:
            return {"status": "insufficient_data"}
        
        recommendations = {
            "agent_specific": {},
            "workflow_optimizations": [],
            "quality_improvements": []
        }
        
        # Analyze agent performance
        agent_performance = defaultdict(lambda: {"total_time": 0, "count": 0, "errors": 0})
        
        for record in self.performance_history[-100:]:
            for agent, metrics in record.agent_metrics.items():
                agent_performance[agent]["total_time"] += metrics.get("execution_time", 0)
                agent_performance[agent]["count"] += 1
                if metrics.get("error"):
                    agent_performance[agent]["errors"] += 1
        
        # Generate agent-specific recommendations
        for agent, perf in agent_performance.items():
            if perf["count"] > 0:
                avg_time = perf["total_time"] / perf["count"]
                error_rate = perf["errors"] / perf["count"]
                
                if avg_time > agent_times.get(agent, 5.0) * 1.5:
                    recommendations["agent_specific"][agent] = f"Consider optimizing {agent} - running {avg_time:.1f}s on average (expected: {agent_times.get(agent, 5.0)}s)"
                
                if error_rate > 0.1:
                    recommendations["agent_specific"][agent] = f"High error rate for {agent}: {error_rate:.1%}. Consider adding retry logic or error handling"
        
        # Workflow optimizations
        if self.patterns:
            for pattern in self.patterns:
                if pattern.confidence > 0.8:
                    recommendations["workflow_optimizations"].append({
                        "pattern": pattern.pattern_type,
                        "recommendation": pattern.recommendation,
                        "confidence": pattern.confidence
                    })
        
        # Quality improvements
        low_quality_records = [r for r in self.performance_history[-50:] if r.overall_quality < 0.7]
        if len(low_quality_records) > 10:
            recommendations["quality_improvements"].append(
                "Consider using enhanced agents more frequently - many recent reports have low quality scores"
            )
        
        return recommendations
    
    def export_insights(self) -> Dict[str, Any]:
        """Export key insights for reporting"""
        return {
            "performance_summary": self.get_performance_summary(),
            "detected_patterns": [
                {
                    "type": p.pattern_type,
                    "impact": p.impact,
                    "frequency": p.frequency,
                    "recommendation": p.recommendation
                }
                for p in self.patterns if p.confidence > 0.7
            ],
            "top_optimization_rules": [
                {
                    "rule_id": r.rule_id,
                    "success_rate": r.success_rate,
                    "applications": r.applications,
                    "expected_improvement": r.expected_improvement
                }
                for r in sorted(self.optimization_rules, 
                              key=lambda r: r.success_rate * r.applications, 
                              reverse=True)[:5]
            ],
            "baselines": {k.value: v for k, v in self.baselines.items()},
            "recommendations": self.get_agent_recommendations()
        }

# Create global optimizer instance
performance_optimizer = PerformanceOptimizer()

# Agent timing constants for predictions
agent_times = {
    "clarifier": 3.0,
    "planner": 4.0,
    "enhanced_planner": 5.0,
    "search": 8.0,
    "enhanced_search": 12.0,
    "writer": 6.0,
    "enhanced_writer": 8.0,
    "email": 2.0,
    "followup": 3.0
}