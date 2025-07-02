# === PLANNER AGENT FOR WEB SEARCH STRATEGY ===
# Purpose: Create a planner agent to generate a strategic set of web search queries 
# to answer research questions effectively, optimized for military innovation, 
# cryptocurrency, options trading, and agentic AI development

# --- IMPORT DEPENDENCIES ---
# Data validation and agent framework
from pydantic import BaseModel, Field
from agents import Agent
import logging

# --- LOGGING CONFIGURATION ---
# Set up logging for debugging and monitoring agent execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Control the number of search queries to generate
# Configuration - reduced from 5 to 3 for better focus and cost efficiency
HOW_MANY_SEARCHES = 3  # Balance between comprehensive research and API costs

# --- DEFINE PLANNER INSTRUCTIONS ---
# These instructions shape how the agent creates search strategies
# Enhanced instructions with domain specialization
INSTRUCTIONS = f"""You are a specialized research assistant focused on military innovation (e.g., munitions, defense tech), 
cryptocurrency (e.g., meme coin trading, blockchain), options trading (US and Japanese markets), and agentic AI development. 
Given a query, generate a set of {HOW_MANY_SEARCHES} web search terms to best answer it. 

Prioritize terms that align with these focus areas when relevant, but adapt to unrelated queries by identifying key concepts. 

For each term:
- Ensure specificity to capture high-quality, targeted results.
- Avoid broad or generic terms unless the query is vague.
- Include a mix of technical, trend-based, and application-specific terms when applicable.

Output concise, actionable search terms tailored to the query's intent."""

# --- DEFINE STRUCTURED OUTPUT SCHEMAS ---
# Using Pydantic for type safety and validation

class WebSearchItem(BaseModel):
    """Individual search query with justification"""
    reason: str = Field(
        description="Your reasoning for why this search is important to the query."
    )
    query: str = Field(
        description="The search term to use for the web search."
    )

class WebSearchPlan(BaseModel):
    """Complete search strategy with multiple queries"""
    searches: list[WebSearchItem] = Field(
        description="A list of web searches to perform to best answer the query."
    )

# --- INITIALIZE PLANNER AGENT ---
# Create the agent with specific configuration for strategic planning
try:
    planner_agent = Agent(
        name="PlannerAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=WebSearchPlan,
        
        tools=[]  # No tools needed - reasoning only
    )
    
    logger.info(f"Planner agent initialized to generate {HOW_MANY_SEARCHES} strategic searches")
        
except Exception as e:
    logger.error(f"Failed to initialize planner agent: {e}")
    raise

# === HOW THE PLANNER WORKS ===
# 1. Receives a research query (e.g., "autonomous drone swarms for defense")
# 2. Analyzes query through specialized lens (military/crypto/trading/AI)
# 3. Generates HOW_MANY_SEARCHES strategic search terms
# 4. For each search, provides:
#    - reason: Why this search helps answer the query
#    - query: The actual search term to use
# 5. Returns structured WebSearchPlan object

# === EXAMPLE OUTPUT STRUCTURE ===
# Query: "Latest military AI applications"
# Output:
# {
#   "searches": [
#     {
#       "reason": "Find current military AI programs and deployments",
#       "query": "military AI systems 2025 deployment Pentagon DARPA"
#     },
#     {
#       "reason": "Identify autonomous weapons and decision support systems",
#       "query": "autonomous military drones AI targeting systems 2025"
#     },
#     {
#       "reason": "Explore AI in military logistics and planning",
#       "query": "AI military logistics predictive maintenance defense tech"
#     }
#   ]
# }

# === WHY USE A PLANNER AGENT ===
# 1. Strategic Research: Better results through thoughtful query design
# 2. Cost Optimization: Fewer, more targeted searches save API costs
# 3. Domain Expertise: Leverages specialized knowledge areas
# 4. Reusability: Can generate search plans for any research topic
# 5. Transparency: Explains reasoning for each search term

# === PLANNER VS DIRECT SEARCH ===
# Direct Search: "military AI" → Generic, broad results
# Planned Search: 
#   - "DARPA AI autonomous systems contracts 2025"
#   - "military AI ethics autonomous weapons policy"
#   - "NATO AI defense integration standards"
# Result: More specific, actionable intelligence

# === CONNECTION TO WORKFLOW ===
# Previous: Search agent defined for executing searches
# This Module: Creates strategic planner to optimize search queries
# Next: Research manager will orchestrate planner + search execution