# === ENHANCED PLANNER AGENT WITH QUERY EXPANSION ===
# Purpose: Advanced planner that generates strategic search queries with semantic expansion,
# synonym generation, and multi-perspective exploration

# --- IMPORT DEPENDENCIES ---
from pydantic import BaseModel, Field
from agents import Agent
from typing import List, Dict
import logging

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BASE_SEARCHES = 3  # Base number of primary searches
EXPANDED_SEARCHES = 2  # Additional expanded/variant searches

# --- QUERY EXPANSION PATTERNS ---
# Domain-specific expansions for better coverage
DOMAIN_EXPANSIONS = {
    'military': {
        'aircraft': ['fighter jets', 'combat aircraft', 'military aviation', 'air force planes'],
        'weapon': ['munitions', 'armament', 'ordnance', 'weapons system'],
        'defense': ['military technology', 'defense systems', 'military innovation']
    },
    'crypto': {
        'cryptocurrency': ['digital currency', 'blockchain assets', 'crypto tokens'],
        'trading': ['crypto trading', 'DeFi trading', 'cryptocurrency exchange'],
        'meme coin': ['memecoin', 'community tokens', 'social tokens']
    },
    'ai': {
        'AI': ['artificial intelligence', 'machine learning', 'deep learning'],
        'agent': ['AI agent', 'autonomous agent', 'intelligent agent', 'agentic system'],
        'LLM': ['large language model', 'foundation model', 'generative AI']
    },
    'trading': {
        'options': ['options trading', 'derivatives', 'calls and puts'],
        'strategy': ['trading strategy', 'investment approach', 'trading system'],
        'analysis': ['technical analysis', 'fundamental analysis', 'market analysis']
    }
}

# --- ENHANCED PLANNER INSTRUCTIONS ---
ENHANCED_INSTRUCTIONS = f"""You are an advanced research strategist specializing in military innovation, 
cryptocurrency, options trading, and AI development. Your task is to create a comprehensive search 
strategy using query expansion techniques.

Given a research query, generate {BASE_SEARCHES + EXPANDED_SEARCHES} strategic web searches:

1. **Primary Searches ({BASE_SEARCHES})**:
   - Direct searches addressing the main query
   - Include specific technical terms and proper nouns
   - Target authoritative sources with precise queries

2. **Expanded Searches ({EXPANDED_SEARCHES})**:
   - Semantic variations using synonyms and related terms
   - Different perspectives (technical, business, practical)
   - Adjacent topics that provide context

For each search term:
- Consider multiple phrasings and synonyms
- Include temporal qualifiers when relevant (2024, latest, recent)
- Add domain-specific modifiers (military, crypto, AI, trading)
- Use quotes for exact phrases when precision matters
- Include negative keywords to filter irrelevant results

Query Expansion Techniques:
1. **Synonym Expansion**: Replace key terms with synonyms
2. **Specification**: Add specific details (country, timeframe, type)
3. **Generalization**: Broaden to capture related concepts
4. **Perspective Shift**: Academic vs practical vs news coverage
5. **Question Reformulation**: Convert statements to questions

Example:
Query: "best AI frameworks for agents"
Primary: 
- "AI agent frameworks 2024 comparison"
- "LangChain vs AutoGen agent development"
- "production ready agent frameworks Python"
Expanded:
- "multi-agent systems libraries open source"
- "autonomous agent development tools enterprise"

Ensure searches complement each other without excessive overlap."""

# --- OUTPUT SCHEMAS WITH EXPANSION METADATA ---
class ExpandedSearchItem(BaseModel):
    """Enhanced search item with expansion metadata"""
    query: str = Field(description="The search term to use")
    reason: str = Field(description="Why this search is important")
    search_type: str = Field(description="Type: primary, synonym, perspective, or adjacent")
    expansion_method: str = Field(description="How the query was expanded")
    expected_insights: str = Field(description="What unique information this search targets")

class EnhancedSearchPlan(BaseModel):
    """Comprehensive search plan with query expansion"""
    original_query: str = Field(description="The user's original research question")
    query_analysis: str = Field(description="Analysis of query intent and key concepts")
    primary_searches: List[ExpandedSearchItem] = Field(description=f"First {BASE_SEARCHES} direct searches")
    expanded_searches: List[ExpandedSearchItem] = Field(description=f"Additional {EXPANDED_SEARCHES} expanded searches")
    search_strategy: str = Field(description="Overall strategy explanation")
    coverage_gaps: List[str] = Field(description="Potential blind spots to address in future")

# --- INITIALIZE ENHANCED PLANNER ---
try:
    enhanced_planner_agent = Agent(
        name="EnhancedPlannerAgent",
        instructions=ENHANCED_INSTRUCTIONS,
        model="gpt-4o",  # Use more powerful model for better planning
        output_type=EnhancedSearchPlan,
        
        tools=[]  # Planning doesn't need tools
    )
    
    logger.info("Enhanced planner agent initialized with query expansion capabilities")
    
except Exception as e:
    logger.error(f"Failed to initialize enhanced planner agent: {e}")
    raise

# === BENEFITS OF QUERY EXPANSION ===
# 1. Comprehensive Coverage: Captures information from multiple angles
# 2. Synonym Handling: Finds content using different terminology
# 3. Reduced Blind Spots: Identifies adjacent relevant topics
# 4. Better Recall: Increases chances of finding crucial information
# 5. Perspective Diversity: Academic, industry, and practical viewpoints