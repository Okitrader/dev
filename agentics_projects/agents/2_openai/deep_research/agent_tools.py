# === AGENT TOOLS - WRAPPER TOOLS FOR EXISTING AGENTS ===
# Purpose: Convert existing agents into tools that can be used by the Manager Agent

from agents import Runner
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import time
import asyncio
from datetime import datetime

# Import existing agents
from clarifier_agent import clarifier_agent, ClarificationPlan
from enhanced_planner_agent import enhanced_planner_agent, EnhancedSearchPlan
from planner_agent import planner_agent, WebSearchPlan
from enhanced_search_agent import enhanced_search_agent, EnhancedSearchResult
from search_agent import search_agent
from enhanced_writer_agent import get_writer_for_preferences, EnhancedReportData, extract_preferences
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from followup_agent import followup_agent, FollowUpResponse

# Import cache manager, monitoring, and error handler
from cache_manager import CacheManager
from monitoring import metrics
from error_handler import ErrorHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === TOOL RESULT STRUCTURE ===
@dataclass
class ToolResult:
    """Standardized result from agent tools"""
    success: bool
    result: Any
    metrics: Dict[str, Any]
    next_suggested_tool: Optional[str] = None
    error_message: Optional[str] = None
    confidence: float = 1.0

# === BASE AGENT TOOL CLASS ===
class AgentTool:
    """Base class for wrapping agents as tools"""
    
    def __init__(self, name: str, agent: Any, enhanced_agent: Optional[Any] = None):
        self.name = name
        self.description = f"Tool wrapper for {name} agent"
        self.agent = agent
        self.enhanced_agent = enhanced_agent
        self.error_handler = ErrorHandler()
        
    async def run(self, input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute the wrapped agent and return standardized result"""
        start_time = time.time()
        
        try:
            # Run with error handling and retry logic
            result = await self.error_handler.handle_with_retry(
                self._execute_agent, input, context
            )
            
            if result:
                return result
            else:
                # Fallback failed, return error result
                return ToolResult(
                    success=False,
                    result=None,
                    metrics={"execution_time": time.time() - start_time},
                    error_message="All retry attempts and fallbacks failed",
                    confidence=0.0
                )
            
        except Exception as e:
            # Record error in monitoring
            metrics.record_error(
                context.get("architecture", "unknown"),
                self.error_handler.categorize_error(e),
                self.name
            )
            
            # Get user-friendly message
            user_message = self.error_handler.get_user_message(e)
            logger.error(f"{self.name} tool failed: {str(e)}")
            
            return ToolResult(
                success=False,
                result=None,
                metrics={"execution_time": time.time() - start_time},
                error_message=user_message,
                confidence=0.0
            )
    
    async def _execute_agent(self, input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Internal method to execute agent - separated for error handling"""
        start_time = time.time()
        
        # Determine which agent to use
        use_enhanced = context.get("use_enhanced", False) and self.enhanced_agent is not None
        selected_agent = self.enhanced_agent if use_enhanced else self.agent
        
        # Format input for agent
        agent_input = self._format_input(input, context)
        
        # Run the agent
        result = await Runner.run(selected_agent, agent_input)
        
        # Process output
        processed_result = self._process_output(result, context)
        
        # Calculate metrics
        execution_time = time.time() - start_time
        metrics_data = self._calculate_metrics(processed_result, execution_time, context)
        
        # Determine next suggested tool
        next_tool = self._suggest_next_tool(processed_result, context)
        
        return ToolResult(
            success=True,
            result=processed_result,
            metrics=metrics_data,
            next_suggested_tool=next_tool,
            confidence=self._calculate_confidence(processed_result, context)
        )
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Format input for the specific agent - override in subclasses"""
        return str(input.get("query", ""))
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> Any:
        """Process agent output - override in subclasses"""
        return result.final_output
    
    def _calculate_metrics(self, result: Any, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance metrics - override in subclasses"""
        return {
            "execution_time": execution_time,
            "token_usage": getattr(result, "token_usage", 0)
        }
    
    def _suggest_next_tool(self, result: Any, context: Dict[str, Any]) -> Optional[str]:
        """Suggest next tool in workflow - override in subclasses"""
        return None
    
    def _calculate_confidence(self, result: Any, context: Dict[str, Any]) -> float:
        """Calculate confidence in result - override in subclasses"""
        return 1.0

# === CLARIFIER TOOL ===
class ClarifierTool(AgentTool):
    """Tool wrapper for clarifier agent"""
    
    def __init__(self):
        super().__init__("clarifier", clarifier_agent)
        self.description = "Generates clarifying questions for ambiguous queries"
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"Research query: {input['query']}"
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> ClarificationPlan:
        return result.final_output_as(ClarificationPlan)
    
    def _calculate_metrics(self, result: ClarificationPlan, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "execution_time": execution_time,
            "questions_generated": len(result.questions) if result else 0,
            "skip_clarification": bool(result.skip_reason) if result else False
        }
    
    def _suggest_next_tool(self, result: ClarificationPlan, context: Dict[str, Any]) -> Optional[str]:
        return "planner"
    
    def _calculate_confidence(self, result: ClarificationPlan, context: Dict[str, Any]) -> float:
        if result and result.questions:
            return 0.8  # Questions indicate uncertainty
        return 1.0  # Clear query

# === PLANNER TOOL ===
class PlannerTool(AgentTool):
    """Tool wrapper for planner agents"""
    
    def __init__(self):
        super().__init__("planner", planner_agent, enhanced_planner_agent)
        self.description = "Creates strategic search plans with query expansion"
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        return f"Research query: {input['query']}"
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> Any:
        if context.get("use_enhanced", False):
            # Convert enhanced plan to standard format
            enhanced_plan = result.final_output_as(EnhancedSearchPlan)
            return enhanced_plan
        return result.final_output_as(WebSearchPlan)
    
    def _calculate_metrics(self, result: Any, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        search_count = 0
        if hasattr(result, 'searches'):
            search_count = len(result.searches)
        elif hasattr(result, 'primary_searches'):
            search_count = len(result.primary_searches) + len(result.expanded_searches)
        
        return {
            "execution_time": execution_time,
            "search_count": search_count,
            "uses_expansion": context.get("use_enhanced", False)
        }
    
    def _suggest_next_tool(self, result: Any, context: Dict[str, Any]) -> Optional[str]:
        return "search"

# === SEARCH TOOL ===
class SearchTool(AgentTool):
    """Tool wrapper for search agents"""
    
    def __init__(self):
        super().__init__("search", search_agent, enhanced_search_agent)
        self.description = "Executes web searches with optional quality filtering"
        self.cache_manager = CacheManager()
        
        # Register fallback strategies
        self._register_fallbacks()
    
    async def run(self, input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute search with caching support"""
        start_time = time.time()
        
        try:
            # Extract search query
            search_item = input.get("search_item", {})
            query = search_item.get('query', '')
            
            # Check cache if not force refresh
            if not context.get('force_refresh', False):
                cached_result = await self.cache_manager.get_cached_search(query)
                if cached_result:
                    logger.info(f"Cache hit for search: {query[:50]}...")
                    metrics.record_cache_hit("search")
                    
                    # Return cached result
                    return ToolResult(
                        success=True,
                        result=cached_result,
                        metrics={
                            "execution_time": time.time() - start_time,
                            "cache_hit": True,
                            "uses_quality_filter": context.get("use_enhanced", False)
                        },
                        next_suggested_tool=self._suggest_next_tool(cached_result, context),
                        confidence=0.9  # High confidence for cached results
                    )
            
            # Cache miss - record it
            metrics.record_cache_miss("search")
            logger.info(f"Cache miss for search: {query[:50]}...")
            
            # Execute search normally
            result = await super().run(input, context)
            
            # Cache successful results
            if result.success and result.result:
                await self.cache_manager.cache_search_result(query, result.result)
                logger.info(f"Cached search result for: {query[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"SearchTool failed: {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                metrics={"execution_time": time.time() - start_time},
                error_message=str(e),
                confidence=0.0
            )
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        search_item = input.get("search_item", {})
        return f"Search term: {search_item.get('query', '')}\nReason for searching: {search_item.get('reason', '')}"
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> Any:
        if context.get("use_enhanced", False):
            return result.final_output_as(EnhancedSearchResult)
        return str(result.final_output)
    
    def _calculate_metrics(self, result: Any, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        metrics = {
            "execution_time": execution_time,
            "uses_quality_filter": context.get("use_enhanced", False)
        }
        
        # Add quality metrics for enhanced search
        if hasattr(result, 'quality_metrics'):
            metrics["relevance_score"] = result.quality_metrics.relevance_score
            metrics["credibility_score"] = result.quality_metrics.credibility_score
            metrics["overall_score"] = result.quality_metrics.overall_score
        
        return metrics
    
    def _suggest_next_tool(self, result: Any, context: Dict[str, Any]) -> Optional[str]:
        # Suggest writer after all searches complete
        if context.get("searches_remaining", 1) <= 1:
            return "writer"
        return "search"  # Continue searching
    
    def _calculate_confidence(self, result: Any, context: Dict[str, Any]) -> float:
        if hasattr(result, 'quality_metrics'):
            return result.quality_metrics.overall_score / 10.0
        return 0.8
    
    def _register_fallbacks(self):
        """Register fallback strategies for search failures"""
        # Fallback 1: Try with simplified query
        async def simplified_search(input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
            search_item = input.get("search_item", {})
            original_query = search_item.get('query', '')
            
            # Simplify query by removing complex terms
            simplified_query = ' '.join(original_query.split()[:5])  # First 5 words
            logger.info(f"Fallback: Trying simplified search query: {simplified_query}")
            
            simplified_input = {
                "search_item": {
                    "query": simplified_query,
                    "reason": search_item.get('reason', '')
                }
            }
            
            return await self._execute_agent(simplified_input, context)
        
        # Fallback 2: Use cached similar results
        async def cached_similar_search(input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
            search_item = input.get("search_item", {})
            query = search_item.get('query', '')
            
            logger.info(f"Fallback: Looking for similar cached results")
            similar_results = await self.cache_manager.find_similar_cached_results(query, threshold=0.7)
            
            if similar_results:
                return ToolResult(
                    success=True,
                    result=similar_results,
                    metrics={
                        "execution_time": time.time() - context.get('start_time', time.time()),
                        "fallback": "cached_similar",
                        "cache_hit": True
                    },
                    confidence=0.7
                )
            else:
                raise Exception("No similar cached results found")
        
        # Register fallbacks
        self.error_handler.register_fallback("_execute_agent", simplified_search)
        self.error_handler.register_fallback("_execute_agent", cached_similar_search)

# === WRITER TOOL ===
class WriterTool(AgentTool):
    """Tool wrapper for writer agents"""
    
    def __init__(self):
        super().__init__("writer", writer_agent)
        self.description = "Generates comprehensive reports from search results"
        self._register_fallbacks()
    
    async def run(self, input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute writer with enhanced writer support"""
        start_time = time.time()
        
        try:
            query = input.get("query", "")
            
            # Check if we should use enhanced writer
            if "Report Preferences:" in query:
                context["use_enhanced_writer"] = True
                # Get the appropriate writer based on preferences
                selected_writer = get_writer_for_preferences(query)
                if selected_writer:
                    logger.info(f"Using enhanced writer for preferences")
                    self.agent = selected_writer
                else:
                    logger.warning("Failed to get enhanced writer, using standard")
                    self.agent = writer_agent
            else:
                self.agent = writer_agent
            
            # Continue with standard execution
            return await super().run(input, context)
            
        except Exception as e:
            logger.error(f"WriterTool failed: {str(e)}")
            return ToolResult(
                success=False,
                result=None,
                metrics={"execution_time": time.time() - start_time},
                error_message=str(e)
            )
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        query = input["query"]
        search_results = input.get("search_results", [])
        
        # Check for preferences
        if "Report Preferences:" in query:
            # Use enhanced writer
            context["use_enhanced_writer"] = True
        
        formatted_results = "\n\n".join([
            f"### Search Result {i+1}:\n{result}"
            for i, result in enumerate(search_results)
        ])
        
        return (
            f"Original query: {query}\n"
            f"Number of searches performed: {len(search_results)}\n\n"
            f"Summarized search results:\n{formatted_results}\n\n"
            f"Please write a comprehensive report based on these search results."
        )
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> ReportData:
        if context.get("use_enhanced_writer", False):
            enhanced_report = result.final_output
            if isinstance(enhanced_report, EnhancedReportData):
                # Convert to standard format preserving quality information
                report = ReportData(
                    query=enhanced_report.query,
                    markdown_report=enhanced_report.markdown_report,
                    word_count=enhanced_report.word_count,
                    search_count=enhanced_report.search_count,
                    timestamp=enhanced_report.timestamp,
                    quality_score=enhanced_report.quality_score,
                    source_diversity=enhanced_report.source_diversity
                )
                # Calculate quality if not already done
                if report.quality_score == 0.0:
                    report.calculate_quality()
                return report
        
        # Standard report
        report = result.final_output_as(ReportData)
        # Calculate quality score
        if report and report.quality_score == 0.0:
            report.calculate_quality()
        return report
    
    def _calculate_metrics(self, result: ReportData, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "execution_time": execution_time,
            "word_count": result.word_count if result else 0,
            "search_count": result.search_count if result else 0
        }
    
    def _suggest_next_tool(self, result: ReportData, context: Dict[str, Any]) -> Optional[str]:
        if context.get("send_email", True):
            return "email"
        return None
    
    def _register_fallbacks(self):
        """Register fallback strategies for writer failures"""
        # Fallback 1: Use standard writer if enhanced fails
        async def use_standard_writer(input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
            logger.info("Fallback: Using standard writer instead of enhanced")
            context["use_enhanced_writer"] = False
            self.agent = writer_agent
            return await self._execute_agent(input, context)
        
        # Fallback 2: Generate summary report
        async def generate_summary_report(input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
            logger.info("Fallback: Generating summary report")
            search_results = input.get("search_results", [])
            query = input.get("query", "")
            
            # Create a simple summary
            summary_parts = [f"Summary Report for: {query}\n"]
            for i, result in enumerate(search_results[:3], 1):
                summary_parts.append(f"\n{i}. {result[:200]}...")
            
            summary = '\n'.join(summary_parts)
            
            # Create minimal report
            report = ReportData(
                query=query,
                report=summary,
                word_count=len(summary.split()),
                search_count=len(search_results),
                timestamp=datetime.now().isoformat()
            )
            report.calculate_quality()
            
            return ToolResult(
                success=True,
                result=report,
                metrics={
                    "execution_time": time.time() - context.get('start_time', time.time()),
                    "fallback": "summary_report"
                },
                confidence=0.6
            )
        
        self.error_handler.register_fallback("_execute_agent", use_standard_writer)
        self.error_handler.register_fallback("_execute_agent", generate_summary_report)

# === EMAIL TOOL ===
class EmailTool(AgentTool):
    """Tool wrapper for email agent"""
    
    def __init__(self):
        super().__init__("email", email_agent)
        self.description = "Formats and sends reports via email"
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        report = input.get("report")
        if not report:
            return ""
        
        return f"""
Please send an email with this research report:

**Research Query:** {report.query}
**Report Length:** {report.word_count} words
**Sources Consulted:** {report.search_count} searches
**Generated:** {report.timestamp}

---

{report.markdown_report}

---

Please format this nicely in HTML and use the subject line:
"Research Report: {report.query} - {datetime.now().strftime('%Y-%m-%d')}"
"""
    
    def _calculate_metrics(self, result: Any, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "execution_time": execution_time,
            "email_sent": result is not None
        }
    
    def _suggest_next_tool(self, result: Any, context: Dict[str, Any]) -> Optional[str]:
        return None  # End of workflow

# === FOLLOWUP TOOL ===
class FollowupTool(AgentTool):
    """Tool wrapper for followup agent"""
    
    def __init__(self):
        super().__init__("followup", followup_agent)
        self.description = "Handles follow-up questions based on previous research"
    
    def _format_input(self, input: Dict[str, Any], context: Dict[str, Any]) -> str:
        return (
            f"Previous report:\n{input.get('previous_report', '')}\n\n"
            f"Follow-up question: {input.get('question', '')}"
        )
    
    def _process_output(self, result: Any, context: Dict[str, Any]) -> FollowUpResponse:
        return result.final_output_as(FollowUpResponse)
    
    def _calculate_metrics(self, result: FollowUpResponse, execution_time: float, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "execution_time": execution_time,
            "confidence_level": result.confidence_level if result else "Low",
            "suggested_queries_count": len(result.suggested_queries) if result else 0
        }
    
    def _suggest_next_tool(self, result: FollowUpResponse, context: Dict[str, Any]) -> Optional[str]:
        # If confidence is low, might suggest new research
        if result and result.confidence_level == "Low":
            return "planner"  # Start new research
        return None

# === TOOL REGISTRY ===
class ToolRegistry:
    """Registry for all available agent tools"""
    
    def __init__(self):
        self.tools = {
            "clarifier": ClarifierTool(),
            "planner": PlannerTool(),
            "search": SearchTool(),
            "writer": WriterTool(),
            "email": EmailTool(),
            "followup": FollowupTool()
        }
    
    def get_tool(self, name: str) -> Optional[AgentTool]:
        """Get tool by name"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """List all available tools"""
        return list(self.tools.keys())
    
    async def execute_tool(self, name: str, input: Dict[str, Any], context: Dict[str, Any]) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get_tool(name)
        if not tool:
            return ToolResult(
                success=False,
                result=None,
                metrics={},
                error_message=f"Tool '{name}' not found"
            )
        
        return await tool.run(input, context)

# === PARALLEL EXECUTION HELPER ===
async def execute_tools_parallel(registry: ToolRegistry, tool_configs: List[Dict[str, Any]]) -> List[ToolResult]:
    """Execute multiple tools in parallel"""
    tasks = []
    for config in tool_configs:
        task = registry.execute_tool(
            config["name"],
            config["input"],
            config.get("context", {})
        )
        tasks.append(task)
    
    return await asyncio.gather(*tasks)

# Create global registry instance
tool_registry = ToolRegistry()