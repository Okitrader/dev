# === INTEGRATED RESEARCH MANAGER - MANAGER-AS-AGENT ARCHITECTURE ===
# Purpose: New intelligent research manager that uses the Manager Agent
# to orchestrate workflows dynamically

from agents import Runner, trace, gen_trace_id
from manager_agent import (
    manager_agent, ManagerOrchestrator, ManagerDecision,
    QueryComplexity, WorkflowStrategy, PerformanceMetrics,
    AgentHandoff
)
from agent_tools import tool_registry, execute_tools_parallel
from performance_optimizer import performance_optimizer, PerformanceRecord
from cache_manager import cache_manager
from error_handler import error_handler
from research_history import research_history

import asyncio
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegratedResearchManager:
    """Intelligent research manager using Manager-as-Agent architecture"""
    
    def __init__(self):
        self.orchestrator = ManagerOrchestrator()
        self.current_handoff: Optional[AgentHandoff] = None
        
    async def run(self, query: str):
        """Run intelligent research process with dynamic workflow"""
        # Generate trace ID
        trace_id = gen_trace_id()
        start_time = time.time()
        
        # Initialize performance tracking
        workflow_metrics = PerformanceMetrics(
            execution_time=0,
            quality_score=0,
            search_count=0,
            cache_hits=0,
            error_count=0,
            token_usage=0
        )
        
        with trace("Intelligent Research Trace", trace_id=trace_id):
            logger.info(f"Starting intelligent research for: {query}")
            logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"🔍 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # === PHASE 1: QUERY ANALYSIS ===
            yield "🧠 Analyzing query complexity..."
            complexity, analysis = await self.orchestrator.analyze_query(query)
            yield f"📊 Complexity: {complexity.value}"
            
            # === PHASE 2: STRATEGY SELECTION ===
            yield "🎯 Selecting optimal workflow strategy..."
            strategy = self.orchestrator.select_strategy(complexity, analysis)
            agent_sequence = self.orchestrator.determine_agent_sequence(strategy, analysis)
            
            yield f"📋 Strategy: {strategy.value}"
            yield f"🔧 Agent sequence: {' → '.join(agent_sequence)}"
            
            # === PHASE 3: GET OPTIMIZATION SUGGESTIONS ===
            suggestions = performance_optimizer.get_optimization_suggestions(query, analysis)
            if suggestions:
                yield f"💡 Found {len(suggestions)} optimization opportunities"
                
                # Apply top suggestion if confident
                if suggestions[0].get("confidence", 0) > 0.7:
                    action = suggestions[0].get("action", {})
                    if "skip_agent" in action:
                        agent_to_skip = action["skip_agent"]
                        if agent_to_skip in agent_sequence:
                            agent_sequence.remove(agent_to_skip)
                            yield f"⚡ Optimization: Skipping {agent_to_skip} agent"
            
            # === PHASE 4: PREDICT PERFORMANCE ===
            predicted_performance = performance_optimizer.predict_performance(analysis, agent_sequence)
            yield f"⏱️  Predicted duration: {predicted_performance['speed']:.1f}s"
            yield f"📈 Expected quality: {predicted_performance['quality']:.2%}"
            
            # === PHASE 5: EXECUTE WORKFLOW ===
            yield "\n🚀 Executing intelligent workflow..."
            
            # Initialize handoff
            self.current_handoff = AgentHandoff(
                from_agent="manager",
                to_agent=agent_sequence[0] if agent_sequence else "none",
                context={
                    "query": query,
                    "complexity": complexity,
                    "strategy": strategy,
                    "analysis": analysis,
                    "trace_id": trace_id
                },
                metrics=workflow_metrics
            )
            
            # Execute agents in sequence
            for i, agent_name in enumerate(agent_sequence):
                yield f"\n🔄 Running {agent_name} agent..."
                
                try:
                    # Prepare context for agent
                    agent_context = {
                        "use_enhanced": "enhanced" in agent_name or strategy == WorkflowStrategy.DEEP_DIVE,
                        "handoff": self.current_handoff,
                        "remaining_agents": agent_sequence[i+1:]
                    }
                    
                    # Execute agent
                    result = await self._execute_agent(agent_name, agent_context)
                    
                    if result.success:
                        yield f"✅ {agent_name} completed successfully"
                        
                        # Update handoff
                        self.current_handoff.from_agent = agent_name
                        self.current_handoff.to_agent = agent_sequence[i+1] if i+1 < len(agent_sequence) else "complete"
                        self.current_handoff.suggested_next = result.next_suggested_tool
                        self.current_handoff.confidence = result.confidence
                        
                        # Check if we should adapt strategy
                        if self.orchestrator.should_adapt_strategy(workflow_metrics, predicted_performance):
                            yield "🔄 Adapting strategy based on intermediate results..."
                            # Potentially modify remaining agent sequence
                            
                    else:
                        yield f"⚠️ {agent_name} encountered an error: {result.error_message}"
                        workflow_metrics.error_count += 1
                        
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {str(e)}")
                    yield f"❌ {agent_name} failed: {error_handler.get_user_message(e)}"
                    workflow_metrics.error_count += 1
            
            # === PHASE 6: GENERATE FINAL REPORT ===
            report = self.current_handoff.get_result("report")
            if report:
                # Calculate quality score if not already done
                if hasattr(report, 'calculate_quality') and report.quality_score == 0.0:
                    report.calculate_quality()
                
                yield f"\n✅ Research completed successfully!"
                yield f"📝 Report length: {report.word_count} words"
                yield f"📊 Quality score: {report.quality_score:.2%}"
                
                # Add trace URL to report
                final_report = report.markdown_report + f"\n\n---\n\n🔍 **View Research Trace**: [{trace_id}](https://platform.openai.com/traces/trace?trace_id={trace_id})"
                
                # === PHASE 7: RECORD PERFORMANCE ===
                end_time = time.time()
                workflow_metrics.execution_time = end_time - start_time
                workflow_metrics.quality_score = self._calculate_quality_score(report)
                
                performance_record = PerformanceRecord(
                    workflow_id=trace_id,
                    query=query,
                    agent_sequence=agent_sequence,
                    start_time=datetime.fromtimestamp(start_time),
                    end_time=datetime.fromtimestamp(end_time),
                    total_duration=workflow_metrics.execution_time,
                    agent_metrics=self._extract_agent_metrics(),
                    overall_quality=workflow_metrics.quality_score,
                    cache_hits=workflow_metrics.cache_hits,
                    total_tokens=workflow_metrics.token_usage,
                    error_count=workflow_metrics.error_count,
                    successful=True
                )
                
                performance_optimizer.record_performance(performance_record)
                
                # Record decision for learning
                self.orchestrator.record_decision(
                    query=query,
                    complexity=complexity,
                    strategy=strategy,
                    agent_sequence=agent_sequence,
                    performance=workflow_metrics
                )
                
                # === PHASE 8: SAVE TO HISTORY ===
                metadata = {
                    "complexity": complexity.value,
                    "strategy": strategy.value,
                    "agent_sequence": agent_sequence,
                    "execution_time": workflow_metrics.execution_time,
                    "quality_score": workflow_metrics.quality_score,
                    "optimizations_applied": len(suggestions)
                }
                
                history_id = research_history.add_research(
                    query=query,
                    report=final_report,
                    metadata=metadata
                )
                
                yield f"💾 Research saved to history (ID: {history_id})"
                
                # === PHASE 9: SHOW PERFORMANCE INSIGHTS ===
                yield "\n📊 Performance Summary:"
                yield f"   • Execution time: {workflow_metrics.execution_time:.1f}s (predicted: {predicted_performance['speed']:.1f}s)"
                yield f"   • Quality score: {workflow_metrics.quality_score:.2%} (predicted: {predicted_performance['quality']:.2%})"
                yield f"   • Cache utilization: {workflow_metrics.cache_hits} hits"
                yield f"   • Tokens used: {workflow_metrics.token_usage}"
                
                # Get optimization insights
                insights = performance_optimizer.export_insights()
                if insights["detected_patterns"]:
                    yield "\n🔍 Detected Patterns:"
                    for pattern in insights["detected_patterns"][:2]:
                        yield f"   • {pattern['type']}: {pattern['recommendation']}"
                
                yield "\n---\n\n" + final_report
            else:
                yield "❌ Failed to generate report"
    
    async def _execute_agent(self, agent_name: str, context: Dict[str, Any]) -> Any:
        """Execute a single agent through the tool registry"""
        handoff = context["handoff"]
        
        # Prepare input based on agent type
        if agent_name == "clarifier":
            input_data = {"query": handoff.get_result("query")}
            
        elif agent_name in ["planner", "enhanced_planner"]:
            input_data = {"query": handoff.get_result("query")}
            
        elif agent_name in ["search", "enhanced_search"]:
            # Get search items from planner
            search_plan = handoff.get_result("search_plan")
            if search_plan:
                # Execute searches in parallel
                search_items = search_plan.searches if hasattr(search_plan, 'searches') else []
                if hasattr(search_plan, 'primary_searches'):
                    search_items.extend(search_plan.primary_searches)
                if hasattr(search_plan, 'expanded_searches'):
                    search_items.extend(search_plan.expanded_searches)
                
                # Execute multiple searches in parallel
                search_configs = [
                    {
                        "name": "search",
                        "input": {"search_item": {"query": item.query, "reason": item.reason}},
                        "context": context
                    }
                    for item in search_items
                ]
                
                search_results = await execute_tools_parallel(tool_registry, search_configs)
                
                # Collect successful results
                successful_results = []
                for result in search_results:
                    if result.success and result.result:
                        successful_results.append(result.result)
                        if hasattr(result.result, 'quality_metrics'):
                            logger.info(f"Search quality: {result.result.quality_metrics.overall_score}/10")
                
                handoff.add_result("search_results", successful_results)
                handoff.update_metrics(search_count=len(successful_results))
                
                # Return aggregated result
                from agent_tools import ToolResult
                return ToolResult(
                    success=True,
                    result=successful_results,
                    metrics={"searches_completed": len(successful_results)},
                    next_suggested_tool="writer"
                )
            
            input_data = {"search_item": {"query": "", "reason": ""}}
            
        elif agent_name in ["writer", "enhanced_writer"]:
            search_results = handoff.get_result("search_results", [])
            # Format search results
            formatted_results = []
            for result in search_results:
                if hasattr(result, 'summary'):
                    formatted_results.append(result.summary)
                else:
                    formatted_results.append(str(result))
            
            input_data = {
                "query": handoff.get_result("query"),
                "search_results": formatted_results
            }
            
        elif agent_name == "email":
            report = handoff.get_result("report")
            input_data = {"report": report}
            
        else:
            input_data = {"query": handoff.get_result("query")}
        
        # Execute through tool registry
        result = await tool_registry.execute_tool(agent_name, input_data, context)
        
        # Store result in handoff
        if result.success and result.result:
            if agent_name in ["clarifier"]:
                handoff.add_result("clarification_plan", result.result)
            elif agent_name in ["planner", "enhanced_planner"]:
                handoff.add_result("search_plan", result.result)
            elif agent_name in ["writer", "enhanced_writer"]:
                handoff.add_result("report", result.result)
            elif agent_name == "email":
                handoff.add_result("email_sent", True)
        
        # Update metrics
        if result.metrics:
            if "execution_time" in result.metrics:
                handoff.metrics.execution_time += result.metrics["execution_time"]
            if "cache_hits" in result.metrics:
                handoff.metrics.cache_hits += result.metrics.get("cache_hits", 0)
            if "token_usage" in result.metrics:
                handoff.metrics.token_usage += result.metrics.get("token_usage", 0)
        
        return result
    
    def _calculate_quality_score(self, report) -> float:
        """Calculate quality score for a report"""
        if not report:
            return 0.0
        
        # Use pre-calculated quality score if available
        if hasattr(report, 'quality_score') and report.quality_score > 0:
            return report.quality_score
        
        # Otherwise calculate it
        score = 0.0
        
        # Word count (optimal range: 800-1500)
        if 800 <= report.word_count <= 1500:
            score += 0.3
        elif 500 <= report.word_count < 800:
            score += 0.2
        elif report.word_count > 1500:
            score += 0.25
        else:
            score += 0.1
        
        # Search count (more sources = better)
        if report.search_count >= 5:
            score += 0.3
        elif report.search_count >= 3:
            score += 0.2
        else:
            score += 0.1
        
        # Report structure (check for sections)
        report_text = report.markdown_report
        if "##" in report_text:  # Has sections
            score += 0.2
        if "###" in report_text:  # Has subsections
            score += 0.1
        if "- " in report_text or "* " in report_text:  # Has lists
            score += 0.1
        
        return min(score, 1.0)
    
    def _extract_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Extract per-agent metrics from handoff"""
        # This would extract detailed metrics from the handoff context
        # For now, returning placeholder
        return {
            "manager": {"execution_time": 1.0},
            # Add more as agents report their metrics
        }

# === ASYNC MANAGER FOR USE WITH EXISTING UI ===
async def run_intelligent_research(query: str):
    """Convenience function for running intelligent research"""
    manager = IntegratedResearchManager()
    async for update in manager.run(query):
        yield update