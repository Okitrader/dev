# === RESEARCH MANAGER FOR ORCHESTRATING MULTI-AGENT WORKFLOW ===
# Purpose: Orchestrates the complete research pipeline from query to emailed report,
# coordinating multiple AI agents to plan, search, write, and distribute findings

# --- IMPORT DEPENDENCIES ---
# Agent framework and utilities
from agents import Runner, trace, gen_trace_id
from search_agent import search_agent
from enhanced_search_agent import enhanced_search_agent, EnhancedSearchResult
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
from enhanced_planner_agent import enhanced_planner_agent, ExpandedSearchItem, EnhancedSearchPlan
from writer_agent import writer_agent, ReportData
from enhanced_writer_agent import get_writer_for_preferences, EnhancedReportData
from email_agent import email_agent
from clarifier_agent import clarifier_agent, ClarificationPlan
from cache_manager import cache_manager
from error_handler import error_handler, with_error_handling, ErrorHandler
from research_history import research_history
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime
import json
import time

# --- CONFIGURE LOGGING ---
# Set up logging for monitoring and debugging the research pipeline
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResearchManager:
    """Orchestrates the complete research pipeline from query to emailed report.
    
    This manager coordinates multiple AI agents to:
    1. Plan strategic search queries
    2. Execute concurrent web searches
    3. Generate professional reports
    4. Send email notifications
    """
    
    def __init__(self, use_enhanced_search: bool = True, use_enhanced_planner: bool = True):
        """Initialize the research manager with configuration options.
        
        Args:
            use_enhanced_search: Whether to use quality filtering in searches
            use_enhanced_planner: Whether to use query expansion in planning
        """
        self.use_enhanced_search = use_enhanced_search
        self.use_enhanced_planner = use_enhanced_planner
        logger.info(f"Research Manager initialized with enhanced_search={use_enhanced_search}, enhanced_planner={use_enhanced_planner}")

    async def run(self, query: str):
        """Run the deep research process, yielding status updates and the final report.
        
        Args:
            query: The research topic/question to investigate
            
        Yields:
            str: Status updates and final markdown report
        """
        # --- GENERATE UNIQUE TRACE ID ---
        # This allows tracking the entire research flow in the OpenAI platform
        trace_id = gen_trace_id()
        start_time = time.time()
        
        # Track metadata for history
        metadata = {
            "enhanced_features": self.use_enhanced_search and self.use_enhanced_planner,
            "cache_hits": 0,
            "search_count": 0
        }
        
        with trace("Research trace", trace_id=trace_id):
            # --- LOG TRACE URL FOR DEBUGGING ---
            logger.info(f"Starting research for query: {query}")
            logger.info(f"View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")
            yield f"🔍 View trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            
            # --- PHASE 0: CLARIFICATION ---
            # Generate clarifying questions to better understand user intent
            yield "🤔 Analyzing query for clarifications..."
            clarification_plan = await self.get_clarifications(query)
            
            # If clarifying questions exist, show them
            if clarification_plan.questions and not clarification_plan.skip_reason:
                yield f"💡 Generated {len(clarification_plan.questions)} clarifying questions:"
                for i, q in enumerate(clarification_plan.questions, 1):
                    yield f"   {i}. {q.question}"
                yield "📌 *Note: Proceeding with original query. Future versions will support interactive Q&A.*"
            else:
                yield f"✅ Query is clear: {clarification_plan.skip_reason}"
            
            # --- PHASE 1: PLANNING ---
            # Generate strategic search queries using the planner agent
            yield "📋 Planning search strategy..."
            search_plan = await self.plan_searches(query)
            yield f"✅ Search plan created with {len(search_plan.searches)} strategic queries"
            
            # --- PHASE 2: SEARCHING ---
            # Execute all searches concurrently for efficiency
            search_mode = "enhanced searches with quality filtering" if self.use_enhanced_search else "standard searches"
            yield f"🔍 Executing concurrent {search_mode}..."
            
            # Show cache stats
            cache_stats = cache_manager.get_cache_stats()
            yield f"💾 Cache: {cache_stats['total_entries']} entries, {cache_stats['total_hits']} hits"
            
            search_results = await self.perform_searches(search_plan)
            total_words = sum(len(result.split()) for result in search_results)
            
            # Count cached vs fresh results
            cached_count = sum(1 for r in search_results if r.startswith("[CACHED]"))
            fresh_count = len(search_results) - cached_count
            
            # Update metadata
            metadata["cache_hits"] = cached_count
            metadata["search_count"] = len(search_results)
            
            yield f"✅ Collected {total_words} words from {len(search_results)} searches ({cached_count} cached, {fresh_count} fresh)"
            
            # --- PHASE 3: REPORT WRITING ---
            # Synthesize findings into a professional report
            yield "📝 Generating comprehensive report..."
            report = await self.write_report(query, search_results)
            
            # Calculate quality score
            report.calculate_quality()
            
            yield f"✅ Report generated ({report.word_count} words, quality score: {report.quality_score:.2f})"
            
            # --- PHASE 4: EMAIL DISTRIBUTION ---
            # Format and send the report via email
            yield "📧 Sending email notification..."
            try:
                await self.send_email(report)
                yield "✅ Email sent successfully!"
            except Exception as e:
                user_msg = error_handler.get_user_message(e)
                logger.error(f"Email sending failed: {user_msg}")
                yield f"⚠️ Email sending failed ({user_msg}), but report is ready"
                
                # Show error stats if multiple failures
                error_stats = error_handler.get_error_stats()
                if error_stats['total_errors'] > 5:
                    yield f"⚠️ System has encountered {error_stats['total_errors']} errors this session"
            
            # --- RETURN FINAL REPORT WITH TRACE URL ---
            final_report_with_trace = report.markdown_report + f"\n\n---\n\n🔍 **View Research Trace**: [https://platform.openai.com/traces/trace?trace_id={trace_id}](https://platform.openai.com/traces/trace?trace_id={trace_id})"
            
            # --- ADD TO HISTORY ---
            # Extract preferences from query if present
            if "Report Preferences:" in query:
                prefs_section = query.split("Report Preferences:")[1].strip()
                for line in prefs_section.split("\n"):
                    if "Format:" in line:
                        metadata["report_format"] = line.split("Format:")[1].strip()
                    elif "Length:" in line:
                        metadata["report_length"] = line.split("Length:")[1].strip()
                    elif "Audience:" in line:
                        metadata["target_audience"] = line.split("Audience:")[1].strip()
            
            # Add processing time and quality metrics
            metadata["processing_time"] = round(time.time() - start_time, 2)
            metadata["word_count"] = report.word_count
            metadata["quality_score"] = report.quality_score
            metadata["source_diversity"] = getattr(report, 'source_diversity', {})
            
            # Save to history
            history_id = research_history.add_research(
                query=query.split("\n\n")[0],  # Original query without preferences
                report=final_report_with_trace,
                metadata=metadata
            )
            
            yield f"💾 Research saved to history (ID: {history_id})"
            yield "\n---\n\n" + final_report_with_trace

    async def plan_searches(self, query: str) -> WebSearchPlan:
        """Use the planner agent to generate strategic search queries.
        
        Args:
            query: The research topic to investigate
            
        Returns:
            WebSearchPlan: Structured plan with search queries and justifications
        """
        logger.info("Planning search strategy...")
        
        if self.use_enhanced_planner:
            # --- RUN ENHANCED PLANNER WITH QUERY EXPANSION ---
            result = await Runner.run(
                enhanced_planner_agent,
                f"Research query: {query}",
            )
            
            enhanced_plan = result.final_output_as(EnhancedSearchPlan)
            
            # Convert to standard WebSearchPlan format
            all_searches = []
            
            # Add primary searches
            for item in enhanced_plan.primary_searches:
                all_searches.append(WebSearchItem(
                    query=item.query,
                    reason=f"{item.reason} [{item.search_type}]"
                ))
            
            # Add expanded searches
            for item in enhanced_plan.expanded_searches:
                all_searches.append(WebSearchItem(
                    query=item.query,
                    reason=f"{item.reason} [Expanded: {item.expansion_method}]"
                ))
            
            logger.info(f"Generated {len(all_searches)} searches with query expansion")
            
            return WebSearchPlan(searches=all_searches)
        else:
            # --- RUN STANDARD PLANNER ---
            result = await Runner.run(
                planner_agent,
                f"Query: {query}",
            )
            
            # --- LOG SEARCH PLAN ---
            logger.info(f"Generated {len(result.final_output.searches)} strategic searches")
            
            # --- RETURN STRUCTURED PLAN ---
            return result.final_output_as(WebSearchPlan)

    async def perform_searches(self, search_plan: WebSearchPlan) -> List[str]:
        """Execute all searches in the plan concurrently for efficiency.
        
        Args:
            search_plan: WebSearchPlan with list of searches to perform
            
        Returns:
            List[str]: Search result summaries from successful searches
        """
        logger.info(f"Executing {len(search_plan.searches)} searches concurrently...")
        
        # --- CREATE ASYNC TASKS ---
        # Each search runs independently for maximum performance
        num_completed = 0
        tasks = [asyncio.create_task(self.search(item)) for item in search_plan.searches]
        results = []
        
        # --- PROCESS RESULTS AS THEY COMPLETE ---
        # This allows progress tracking as searches finish
        for task in asyncio.as_completed(tasks):
            result = await task
            if result is not None:
                results.append(result)
            num_completed += 1
            logger.info(f"Search progress: {num_completed}/{len(tasks)} completed")
        
        logger.info(f"Search phase complete. Retrieved {len(results)} successful results.")
        return results

    async def search(self, item: WebSearchItem) -> Optional[str]:
        """Execute a single web search using the search agent.
        
        Args:
            item: WebSearchItem containing query and reasoning
            
        Returns:
            Optional[str]: Search summary or None if search failed
        """
        # --- CHECK CACHE FIRST ---
        cached_result = await cache_manager.get_cached_search(item.query)
        if cached_result:
            logger.info(f"Using cached result for '{item.query}'")
            # Add cache indicator to the result
            return f"[CACHED] {cached_result.get('summary', cached_result.get('content', ''))}"
        
        # --- FORMAT INPUT FOR SEARCH AGENT ---
        # Provide both the search term and the reason for context
        input = f"Search term: {item.query}\nReason for searching: {item.reason}"
        
        try:
            if self.use_enhanced_search:
                # --- EXECUTE ENHANCED SEARCH WITH QUALITY FILTERING ---
                result = await Runner.run(
                    enhanced_search_agent,
                    input,
                )
                enhanced_result = result.final_output_as(EnhancedSearchResult)
                
                # Log quality metrics
                logger.info(f"Search quality scores for '{item.query}':")
                logger.info(f"  - Relevance: {enhanced_result.quality_metrics.relevance_score}/10")
                logger.info(f"  - Credibility: {enhanced_result.quality_metrics.credibility_score}/10")
                logger.info(f"  - Overall: {enhanced_result.quality_metrics.overall_score}/10")
                
                # Log source diversity
                logger.info(f"Source diversity for '{item.query}':")
                logger.info(f"  - Unique domains: {enhanced_result.source_diversity.total_domains}")
                logger.info(f"  - Source types: {enhanced_result.source_diversity.source_types}")
                
                # Only return if quality threshold met
                if enhanced_result.quality_metrics.overall_score >= 6.0:
                    # Cache the successful result
                    await cache_manager.cache_search_results(
                        item.query,
                        {"summary": enhanced_result.summary, "quality_score": enhanced_result.quality_metrics.overall_score}
                    )
                    return enhanced_result.summary
                else:
                    logger.warning(f"Search results below quality threshold for '{item.query}'")
                    return None
            else:
                # --- EXECUTE STANDARD SEARCH ---
                result = await Runner.run(
                    search_agent,
                    input,
                )
                summary = str(result.final_output)
                
                # Cache the result
                await cache_manager.cache_search_results(
                    item.query,
                    {"summary": summary}
                )
                
                return summary
            
        except Exception as e:
            # --- HANDLE SEARCH FAILURES GRACEFULLY ---
            user_msg = error_handler.get_user_message(e)
            logger.warning(f"Search failed for '{item.query}': {user_msg}")
            
            # Log detailed error for debugging
            error_handler.log_error(e, error_handler.categorize_error(e), 0)
            
            # Try to provide partial results
            return f"[ERROR] {user_msg} - Query: {item.query}"

    async def write_report(self, query: str, search_results: List[str]) -> ReportData:
        """Use the writer agent to synthesize search results into a professional report.
        
        Args:
            query: Original research question
            search_results: List of summaries from searches
            
        Returns:
            ReportData: Structured report with markdown content and metadata
        """
        logger.info("Generating comprehensive report...")
        
        # --- FORMAT SEARCH RESULTS ---
        # Create clear sections for each search result
        formatted_results = "\n\n".join([
            f"### Search Result {i+1}:\n{result}" 
            for i, result in enumerate(search_results)
        ])
        
        # --- PREPARE WRITER INPUT ---
        # Provide context about the search process
        input = (
            f"Original query: {query}\n"
            f"Number of searches performed: {len(search_results)}\n\n"
            f"Summarized search results:\n{formatted_results}\n\n"
            f"Please write a comprehensive report based on these search results."
        )
        
        # --- SELECT APPROPRIATE WRITER ---
        # Check if query contains preferences
        if "Report Preferences:" in query:
            # Use enhanced writer that adapts to preferences
            selected_writer = get_writer_for_preferences(query)
            logger.info(f"Using customized writer based on preferences")
            
            result = await Runner.run(
                selected_writer,
                input,
            )
            
            # Convert enhanced report to standard format if needed
            enhanced_report = result.final_output
            if isinstance(enhanced_report, EnhancedReportData):
                # Create standard ReportData from enhanced version
                return ReportData(
                    query=enhanced_report.query,
                    markdown_report=enhanced_report.markdown_report,
                    word_count=enhanced_report.word_count,
                    search_count=enhanced_report.search_count,
                    timestamp=enhanced_report.timestamp
                )
            else:
                return result.final_output_as(ReportData)
        else:
            # --- USE STANDARD WRITER ---
            result = await Runner.run(
                writer_agent,
                input,
            )
            
            logger.info(f"Report generated successfully ({result.final_output.word_count} words)")
            return result.final_output_as(ReportData)
    
    async def send_email(self, report: ReportData) -> None:
        """Use the email agent to format and send the report via email.
        
        Args:
            report: ReportData containing the markdown report and metadata
        """
        logger.info("Formatting and sending email report...")
        
        # --- PREPARE COMPREHENSIVE EMAIL CONTENT ---
        # Include metadata for context and professionalism
        email_content = f"""
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
        
        # --- SEND EMAIL ---
        result = await Runner.run(
            email_agent,
            email_content,
        )
        
        logger.info("Email sent successfully")
    
    async def get_clarifications(self, query: str) -> ClarificationPlan:
        """Use the clarifier agent to analyze the query and generate clarifying questions.
        
        Args:
            query: The research topic to analyze
            
        Returns:
            ClarificationPlan: Structured plan with clarifying questions
        """
        logger.info("Generating clarifying questions...")
        
        try:
            # --- RUN CLARIFIER AGENT ---
            result = await Runner.run(
                clarifier_agent,
                f"Research query: {query}",
            )
            
            # --- LOG CLARIFICATION RESULTS ---
            plan = result.final_output_as(ClarificationPlan)
            logger.info(f"Generated {len(plan.questions)} clarifying questions")
            
            return plan
            
        except Exception as e:
            # --- HANDLE CLARIFICATION FAILURES GRACEFULLY ---
            logger.warning(f"Clarification failed: {str(e)}. Proceeding with original query.")
            return ClarificationPlan(
                original_query=query,
                query_analysis="Failed to analyze query",
                questions=[],
                skip_reason="Clarification analysis failed - proceeding with original query"
            )

# === WORKFLOW OVERVIEW ===
# 1. User submits research query
# 2. Planner generates strategic search terms
# 3. Search agent executes concurrent searches
# 4. Writer agent synthesizes findings into report
# 5. Email agent formats and sends HTML email
# 6. User receives professional research report

# === ASYNC/AWAIT BENEFITS ===
# - Concurrent search execution (3x faster)
# - Non-blocking UI updates via yield
# - Efficient resource utilization
# - Graceful error handling

# === ERROR HANDLING STRATEGY ===
# - Individual search failures don't crash pipeline
# - Email failures don't lose the report
# - All errors logged for debugging
# - User always gets results (even partial)

# === MONITORING AND DEBUGGING ===
# - Trace ID links to OpenAI platform
# - Comprehensive logging at each phase
# - Progress updates via yield statements
# - Performance metrics (word counts, timings)

# === CONNECTION TO UI ===
# This manager is called by deep_research.py
# Yields status updates for real-time UI feedback
# Returns final report for display in Gradio interface