# === SEARCH AGENT FOR TARGETED WEB RESEARCH ===
# Purpose: Create a specialized agent to conduct web searches and produce concise summaries, optimized for
# military innovation (e.g., munitions, defense tech), cryptocurrency (e.g., meme coin trading), options trading 
# (US and Japanese markets), and agentic AI development, with flexibility for unrelated queries.

# --- CORE AGENT FRAMEWORK ---
# Base components for creating and running intelligent agents
from agents import Agent, WebSearchTool, ModelSettings
import logging

# --- LOGGING CONFIGURATION ---
# Set up logging for debugging and monitoring agent execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEFINE AGENT INSTRUCTIONS ---
# These instructions shape how the agent processes and summarizes information
# Enhanced instructions with domain specialization
INSTRUCTIONS = """You are a research assistant specializing in military innovation (e.g., munitions, defense tech), 
cryptocurrency (e.g., meme coin trading, blockchain), options trading (US and Japanese markets), and agentic AI 
development. Given a search term, search the web and produce a concise summary of results. Summary must:
- Be 2-3 paragraphs and less than 300 words.
- Focus on main points, technical details, or trends relevant to the query and specialization areas.
- Use succinct style, no complete sentences or proper grammar needed.
- Capture essence, ignore fluff, no extra commentary.
- For unrelated queries, identify key concepts and summarize accurately.
Output a structured summary with the search term and word count."""

# --- INITIALIZE SEARCH AGENT ---
# Create the agent with specific configuration for targeted research
try:
    search_agent = Agent(
        # Agent identifier for logging and tracing
        name="SearchAgent",
        
        # Guidelines that shape agent behavior - defines expertise and output format
        instructions=INSTRUCTIONS,
        
        # Tools available to the agent
        tools=[
            WebSearchTool(
                search_context_size="high"  # Changed from "low" to "high" for more detailed context
                # "low" = concise results, "high" = more detailed context
            )
        ],
        
        # Model selection - efficient model balancing speed/cost with quality
        model="gpt-4o-mini",  # Optimized for speed and cost-efficiency
        
        # Model behavior configuration
        model_settings=ModelSettings(
            tool_choice="required"  # Forces agent to use WebSearchTool (no skipping searches)
            # Prevents agent from answering without searching
            # Ensures fresh, web-based information
        )
    )
    
    # Log successful initialization
    logger.info("Search agent initialized successfully with enhanced configuration.")
    
except Exception as e:
    # Capture and log any initialization errors
    logger.error(f"Failed to initialize search agent: {e}")
    raise  # Re-raise to halt execution if agent creation fails

# === AGENT CONFIGURATION EXPLAINED ===
# 1. name="SearchAgent": Identifies agent in traces and logs for debugging
# 2. instructions: Custom prompt engineering for domain expertise
# 3. WebSearchTool(search_context_size="high"): 
#    - "low" returns concise snippets (faster, cheaper)
#    - "medium" returns moderate context
#    - "high" returns extensive context (slower, more tokens)
# 4. model="gpt-4o-mini": 
#    - Optimized for speed and cost-efficiency
#    - Sufficient for summarization tasks
#    - Alternative: "gpt-4" for complex reasoning
# 5. tool_choice="required": 
#    - Prevents agent from answering without searching
#    - Ensures fresh, web-based information
#    - Alternative: "auto" lets agent decide when to search

# === WHY THIS AGENT ===
# 1. Specialized Research: Tailored prompts for military tech, crypto, options, and AI
# 2. Efficiency: gpt-4o-mini model balances quality with speed/cost
# 3. Reliability: Error handling prevents silent failures
# 4. Flexibility: Can handle queries outside specialty areas

# === CONNECTION TO WORKFLOW ===
# Previous: Environment setup and imports
# This Module: Creates a specialized search agent with domain expertise
# Next: Planner agent will use this to execute strategic searches