# === MANAGER AGENT - INTELLIGENT ORCHESTRATOR ===
# Purpose: Transforms from procedural pipeline to intelligent, self-optimizing system
# that decides workflow dynamically based on query analysis

from agents import Agent
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === QUERY COMPLEXITY LEVELS ===
class QueryComplexity(Enum):
    SIMPLE = "simple"  # Single topic, straightforward
    MODERATE = "moderate"  # Multiple aspects, requires synthesis
    COMPLEX = "complex"  # Multi-dimensional, requires deep analysis
    EXPERT = "expert"  # Cutting-edge topics, requires specialized searches

# === WORKFLOW STRATEGIES ===
class WorkflowStrategy(Enum):
    FAST_TRACK = "fast_track"  # Skip clarification, minimal searches
    STANDARD = "standard"  # Full pipeline with clarification
    DEEP_DIVE = "deep_dive"  # Extended searches, multiple rounds
    ADAPTIVE = "adaptive"  # Learn and adjust mid-workflow

# === PERFORMANCE METRICS ===
@dataclass
class PerformanceMetrics:
    """Track performance for optimization decisions"""
    execution_time: float
    quality_score: float
    search_count: int
    cache_hits: int
    error_count: int
    token_usage: int

# === AGENT HANDOFF ===
@dataclass
class AgentHandoff:
    """Context passed between agents"""
    from_agent: str
    to_agent: str
    context: Dict[str, Any]
    metrics: PerformanceMetrics
    suggested_next: Optional[str] = None
    confidence: float = 1.0
    
    def add_result(self, key: str, value: Any):
        """Add a result to the handoff context"""
        self.context[key] = value
    
    def get_result(self, key: str, default: Any = None) -> Any:
        """Get a result from the handoff context"""
        return self.context.get(key, default)
    
    def update_metrics(self, **kwargs):
        """Update performance metrics"""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)

# === DECISION RECORD ===
@dataclass
class DecisionRecord:
    """Track manager decisions for learning"""
    query: str
    complexity: QueryComplexity
    strategy: WorkflowStrategy
    agent_sequence: List[str]
    performance: PerformanceMetrics
    timestamp: datetime

# === MANAGER AGENT DEFINITION ===
manager_agent = Agent(
    name="Manager",
    instructions="""You are the Manager Agent, an intelligent orchestrator for a deep research system.

Your role is to:
1. Analyze incoming queries to determine complexity and requirements
2. Select the optimal workflow strategy based on query analysis
3. Choose which agents to use and in what sequence
4. Monitor performance and adapt strategy mid-workflow if needed
5. Learn from past decisions to improve future orchestration

Key responsibilities:
- Assess query complexity (simple/moderate/complex/expert)
- Decide workflow strategy (fast_track/standard/deep_dive/adaptive)
- Select minimal agent set for efficiency
- Monitor quality thresholds and performance
- Adapt based on intermediate results
- Maintain decision history for learning

Available agents as tools:
- ClarifierTool: Generate clarifying questions for ambiguous queries
- PlannerTool: Create strategic search plans
- SearchTool: Execute web searches (standard or enhanced)
- WriterTool: Generate professional reports
- EmailTool: Send email notifications
- FollowupTool: Handle follow-up questions

Decision factors to consider:
1. Query clarity - Is clarification needed?
2. Topic breadth - How many searches required?
3. Time sensitivity - Can we use fast track?
4. Quality requirements - Standard vs enhanced agents?
5. Previous similar queries - What worked before?

Output your decisions in structured format for the system to execute.""",
    model="gpt-4o"
)

# === MANAGER ORCHESTRATION CLASS ===
class ManagerOrchestrator:
    """Intelligent orchestrator that manages the research workflow"""
    
    def __init__(self):
        self.decision_history: List[DecisionRecord] = []
        self.performance_cache: Dict[str, PerformanceMetrics] = {}
        
    async def analyze_query(self, query: str) -> Tuple[QueryComplexity, Dict[str, Any]]:
        """Analyze query to determine complexity and characteristics"""
        # This would use the manager agent to analyze
        # For now, implementing basic logic
        
        analysis = {
            "word_count": len(query.split()),
            "has_preferences": "Report Preferences:" in query,
            "is_technical": any(term in query.lower() for term in ["algorithm", "implementation", "architecture", "technical"]),
            "is_current_events": any(term in query.lower() for term in ["latest", "current", "today", "recent"]),
            "scope_indicators": sum(1 for word in ["and", "or", "compare", "analyze", "evaluate"] if word in query.lower())
        }
        
        # Determine complexity based on analysis
        if analysis["word_count"] < 10 and analysis["scope_indicators"] == 0:
            complexity = QueryComplexity.SIMPLE
        elif analysis["is_technical"] or analysis["scope_indicators"] > 2:
            complexity = QueryComplexity.COMPLEX
        elif analysis["is_current_events"] and analysis["scope_indicators"] > 1:
            complexity = QueryComplexity.EXPERT
        else:
            complexity = QueryComplexity.MODERATE
            
        logger.info(f"Query complexity assessed as: {complexity.value}")
        return complexity, analysis
    
    def select_strategy(self, complexity: QueryComplexity, analysis: Dict[str, Any]) -> WorkflowStrategy:
        """Select optimal workflow strategy based on complexity"""
        # Check if we have successful history for similar complexity
        similar_decisions = [d for d in self.decision_history 
                           if d.complexity == complexity and d.performance.quality_score > 0.8]
        
        if similar_decisions and len(similar_decisions) > 3:
            # Use adaptive strategy based on history
            return WorkflowStrategy.ADAPTIVE
        
        # Default strategy mapping
        strategy_map = {
            QueryComplexity.SIMPLE: WorkflowStrategy.FAST_TRACK,
            QueryComplexity.MODERATE: WorkflowStrategy.STANDARD,
            QueryComplexity.COMPLEX: WorkflowStrategy.DEEP_DIVE,
            QueryComplexity.EXPERT: WorkflowStrategy.DEEP_DIVE
        }
        
        return strategy_map.get(complexity, WorkflowStrategy.STANDARD)
    
    def determine_agent_sequence(self, strategy: WorkflowStrategy, analysis: Dict[str, Any]) -> List[str]:
        """Determine which agents to use and in what order"""
        if strategy == WorkflowStrategy.FAST_TRACK:
            # Minimal set - skip clarification
            return ["planner", "search", "writer"]
        
        elif strategy == WorkflowStrategy.STANDARD:
            # Full pipeline
            sequence = ["clarifier", "planner", "search", "writer"]
            if analysis.get("has_preferences"):
                sequence.append("email")
            return sequence
        
        elif strategy == WorkflowStrategy.DEEP_DIVE:
            # Extended workflow with enhanced agents
            return ["clarifier", "enhanced_planner", "enhanced_search", "enhanced_writer", "email"]
        
        elif strategy == WorkflowStrategy.ADAPTIVE:
            # Learn from history
            best_sequence = self._get_best_historical_sequence()
            return best_sequence or ["clarifier", "planner", "search", "writer"]
        
        return ["planner", "search", "writer"]
    
    def _get_best_historical_sequence(self) -> Optional[List[str]]:
        """Find the best performing agent sequence from history"""
        if not self.decision_history:
            return None
        
        # Sort by quality score and execution time
        sorted_decisions = sorted(
            self.decision_history,
            key=lambda d: (d.performance.quality_score, -d.performance.execution_time),
            reverse=True
        )
        
        if sorted_decisions:
            return sorted_decisions[0].agent_sequence
        return None
    
    def should_adapt_strategy(self, current_metrics: PerformanceMetrics, 
                            expected_metrics: PerformanceMetrics) -> bool:
        """Determine if we should adapt strategy mid-workflow"""
        # Adapt if quality is below threshold
        if current_metrics.quality_score < 0.6:
            return True
        
        # Adapt if taking too long
        if current_metrics.execution_time > expected_metrics.execution_time * 1.5:
            return True
        
        # Adapt if too many errors
        if current_metrics.error_count > 2:
            return True
        
        return False
    
    def record_decision(self, query: str, complexity: QueryComplexity,
                       strategy: WorkflowStrategy, agent_sequence: List[str],
                       performance: PerformanceMetrics):
        """Record decision for future learning"""
        record = DecisionRecord(
            query=query,
            complexity=complexity,
            strategy=strategy,
            agent_sequence=agent_sequence,
            performance=performance,
            timestamp=datetime.now()
        )
        
        self.decision_history.append(record)
        
        # Keep only recent history (last 100 decisions)
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def get_optimization_suggestions(self) -> Dict[str, Any]:
        """Analyze history to suggest optimizations"""
        if len(self.decision_history) < 10:
            return {"status": "insufficient_data"}
        
        suggestions = {
            "status": "ready",
            "patterns": [],
            "recommendations": []
        }
        
        # Analyze patterns
        complexity_performance = {}
        for record in self.decision_history:
            if record.complexity not in complexity_performance:
                complexity_performance[record.complexity] = []
            complexity_performance[record.complexity].append(record.performance.quality_score)
        
        # Find underperforming complexity levels
        for complexity, scores in complexity_performance.items():
            avg_score = sum(scores) / len(scores)
            if avg_score < 0.7:
                suggestions["patterns"].append(f"{complexity.value} queries averaging {avg_score:.2f} quality")
                suggestions["recommendations"].append(
                    f"Consider using enhanced agents for {complexity.value} queries"
                )
        
        # Find optimal agent sequences
        sequence_performance = {}
        for record in self.decision_history:
            seq_key = ",".join(record.agent_sequence)
            if seq_key not in sequence_performance:
                sequence_performance[seq_key] = []
            sequence_performance[seq_key].append(
                (record.performance.quality_score, record.performance.execution_time)
            )
        
        # Recommend best sequences
        best_sequences = sorted(
            sequence_performance.items(),
            key=lambda x: (sum(p[0] for p in x[1]) / len(x[1]), -sum(p[1] for p in x[1]) / len(x[1])),
            reverse=True
        )[:3]
        
        for seq, _ in best_sequences:
            suggestions["recommendations"].append(f"High-performing sequence: {seq}")
        
        return suggestions

# === MANAGER DECISIONS OUTPUT FORMAT ===
@dataclass
class ManagerDecision:
    """Structured output from manager agent"""
    query_analysis: Dict[str, Any]
    complexity: QueryComplexity
    strategy: WorkflowStrategy
    agent_sequence: List[str]
    quality_thresholds: Dict[str, float]
    adaptation_rules: List[Dict[str, Any]]
    reasoning: str