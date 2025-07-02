# === WRITER AGENT FOR REPORT GENERATION ===
# Purpose: Create a specialized agent that converts research results into 
# well-formatted reports with professional structure and actionable insights

# --- IMPORT DEPENDENCIES ---
# Data validation and utilities
from pydantic import BaseModel, Field
from agents import Agent
from datetime import datetime
import logging
from typing import Dict, Any, Optional
from dataclasses import field

# --- LOGGING CONFIGURATION ---
# Set up logging for debugging and monitoring agent execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEFINE WRITER AGENT INSTRUCTIONS ---
# These instructions shape how the agent formats and structures reports
# Enhanced writer instructions with domain specialization
INSTRUCTIONS = """You are a professional report writer specializing in military innovation, 
cryptocurrency, options trading, and agentic AI development. Given a research query and summarized 
search results, write a comprehensive report that:

1. Starts with an executive summary (2-3 sentences)
2. Organizes findings into clear sections with headers
3. Highlights key insights relevant to the specialized domains
4. Uses markdown formatting (##, **, -, etc.)
5. Concludes with actionable recommendations
6. Maintains professional tone while being concise

Target length: 500-800 words (more focused than before).

Output a structured report with all required fields."""

# --- DEFINE STRUCTURED OUTPUT SCHEMAS ---
# Using Pydantic for type safety and validation

class ReportData(BaseModel):
    """Structured report data with markdown content and metadata"""
    query: str = Field(description="Original research query")
    markdown_report: str = Field(description="Full report in markdown format")
    word_count: int = Field(description="Report length in words")
    search_count: int = Field(description="Number of searches performed")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="When report was generated"
    )
    quality_score: float = Field(default=0.0, description="Quality score (0-1) for the report")
    source_diversity: Dict[str, Any] = Field(default_factory=dict, description="Source diversity metrics")
    
    def calculate_quality(self):
        """Calculate quality score for the report"""
        # Import here to avoid circular dependency
        from performance_optimizer import performance_optimizer
        
        self.quality_score = performance_optimizer.calculate_quality_score({
            "word_count": self.word_count,
            "search_count": self.search_count,
            "markdown_report": self.markdown_report,
            "source_diversity": self.source_diversity
        })
        
        logger.info(f"Report quality score calculated: {self.quality_score:.2f}")

# --- INITIALIZE WRITER AGENT ---
# Create the agent with specific configuration for report generation
try:
    writer_agent = Agent(
        name="WriterAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=ReportData,  # Structured output for reports
        
        tools=[]  # No tools needed - pure text generation
    )
    logger.info("Writer agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize writer agent: {e}")
    raise

# === WHAT THIS AGENT DOES ===
# 1. Receives a text report (from search agent or other source)
# 2. Analyzes content structure and key points
# 3. Creates professional report with:
#    - Executive summary
#    - Organized sections with clear headers
#    - Key insights and findings
#    - Actionable recommendations
#    - Metadata (word count, timestamp)
# 4. Returns structured ReportData object

# === REPORT STRUCTURE EXAMPLE ===
# ## Executive Summary
# Recent developments in military AI show significant advances in autonomous 
# systems and decision support tools, with implications for defense strategy...
#
# ## Key Findings
# 
# ### Autonomous Systems
# - **Drone Swarms**: Distributed decision-making with human oversight
# - **Ground Vehicles**: Enhanced navigation in contested environments
# - **Maritime Systems**: Underwater autonomous vehicles for reconnaissance
#
# ### Cryptocurrency and Trading Applications  
# - **DeFi Automation**: AI agents managing yield optimization
# - **Risk Assessment**: Real-time portfolio analysis
# - **Market Prediction**: Options trading strategy generation
#
# ### Defense Technology Integration
# - **Command & Control**: AI-assisted tactical planning
# - **Logistics**: Predictive maintenance and supply chain optimization
# - **Cyber Defense**: Autonomous threat detection and response
#
# ## Recommendations
# 1. **Invest in Dual-Use Technologies**: Focus on AI systems with both 
#    military and commercial applications
# 2. **Develop Ethical Guidelines**: Establish clear boundaries for 
#    autonomous decision-making in critical systems
# 3. **Enhance Human-AI Collaboration**: Prioritize systems that augment 
#    rather than replace human judgment

# === WHY SEPARATE WRITER AGENT ===
# 1. Separation of Concerns: Search vs. formatting vs. analysis
# 2. Reusability: Can format results from any research source
# 3. Specialization: Focused on report best practices
# 4. Modularity: Easy to update report format without changing search logic

# === METADATA TRACKING ===
# The ReportData model tracks:
# - query: Original research question for context
# - word_count: Ensures reports meet target length
# - search_count: Documents research comprehensiveness
# - timestamp: Records when report was generated

# === CONNECTION TO WORKFLOW ===
# Previous: Planner and search agents gather information
# This Module: Synthesizes findings into professional report
# Next: Email agent will format and send the report