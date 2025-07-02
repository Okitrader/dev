# === ENHANCED SEARCH AGENT WITH QUALITY FILTERING ===
# Purpose: Advanced search agent that filters results by quality, credibility, and relevance

# --- IMPORT DEPENDENCIES ---
from agents import Agent, WebSearchTool, ModelSettings
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import logging
from datetime import datetime
import re

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DOMAIN AUTHORITY PATTERNS ---
# High-quality sources for different domains
AUTHORITY_DOMAINS = {
    'military': ['.mil', '.gov', 'janes.com', 'defensenews.com', 'rand.org'],
    'crypto': ['coindesk.com', 'cointelegraph.com', 'decrypt.co', 'theblock.co'],
    'trading': ['bloomberg.com', 'reuters.com', 'wsj.com', 'ft.com', 'investopedia.com'],
    'ai': ['arxiv.org', 'papers.nips.cc', 'openai.com', 'deepmind.com', 'anthropic.com'],
    'academic': ['.edu', '.ac.uk', 'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov'],
    'general': ['.gov', '.edu', '.org', 'wikipedia.org', 'britannica.com']
}

# --- QUALITY SCORING CRITERIA ---
class QualityMetrics(BaseModel):
    """Metrics for evaluating search result quality"""
    relevance_score: float = Field(description="How well the content matches the query (0-10)")
    credibility_score: float = Field(description="Source authority and trustworthiness (0-10)")
    recency_score: float = Field(description="How current the information is (0-10)")
    depth_score: float = Field(description="Level of detail and comprehensiveness (0-10)")
    overall_score: float = Field(description="Weighted average of all scores")

class SourceDiversity(BaseModel):
    """Metrics for source diversity"""
    total_domains: int = Field(description="Number of unique domains")
    domain_distribution: Dict[str, int] = Field(description="Count per domain")
    source_types: Dict[str, int] = Field(description="Distribution by type (news, academic, gov, etc)")
    geographic_diversity: List[str] = Field(description="Countries/regions represented")
    
class EnhancedSearchResult(BaseModel):
    """Enhanced search result with quality metrics"""
    query: str = Field(description="The search query used")
    summary: str = Field(description="Concise summary of findings (200-300 words)")
    quality_metrics: QualityMetrics = Field(description="Quality assessment scores")
    sources_used: List[str] = Field(description="List of sources included in summary")
    sources_filtered: List[str] = Field(description="Low-quality sources that were filtered out")
    source_diversity: SourceDiversity = Field(description="Source diversity metrics")
    word_count: int = Field(description="Summary word count")

# --- ENHANCED SEARCH INSTRUCTIONS ---
ENHANCED_INSTRUCTIONS = """You are an advanced research assistant with expertise in military innovation, 
cryptocurrency, options trading, and AI development. Your task is to search, evaluate, and summarize 
web content with quality filtering.

For each search:
1. Evaluate each source's credibility based on:
   - Domain authority (.gov, .edu, established news outlets)
   - Publication date (prefer recent content)
   - Author credentials when available
   - Content depth and citations

2. Filter out:
   - Personal blogs without credentials
   - Social media posts (unless from verified experts)
   - Content farms and aggregator sites
   - Sources with obvious bias or promotional content
   - Outdated information (>2 years unless historically relevant)

3. Prioritize:
   - Government and academic sources
   - Industry-leading publications
   - Primary sources over secondary
   - Recent developments and breaking news

4. Generate quality scores (0-10) for:
   - Relevance: How well content addresses the query
   - Credibility: Source authority and expertise
   - Recency: Information currency
   - Depth: Comprehensiveness and detail

5. Produce a 200-300 word summary focusing on high-quality sources.

SOURCE DIVERSITY REQUIREMENTS:
- Include content from at least 3-5 different domains
- Balance source types: news (30%), academic/research (30%), official/gov (20%), industry (20%)
- Avoid over-reliance on any single source
- Prioritize geographic diversity for international topics
- Track and report diversity metrics

Output structured results with quality metrics, source lists, and diversity analysis."""

# --- INITIALIZE ENHANCED SEARCH AGENT ---
try:
    enhanced_search_agent = Agent(
        name="EnhancedSearchAgent",
        instructions=ENHANCED_INSTRUCTIONS,
        tools=[
            WebSearchTool(
                search_context_size="high"  # Get more context for quality evaluation
            )
        ],
        model="gpt-4o",  # Use more powerful model for quality assessment
        output_type=EnhancedSearchResult,
        
        model_settings=ModelSettings(
            tool_choice="required"
        )
    )
    
    logger.info("Enhanced search agent initialized with quality filtering capabilities")
    
except Exception as e:
    logger.error(f"Failed to initialize enhanced search agent: {e}")
    raise

# === QUALITY FILTERING BENEFITS ===
# 1. Improved Accuracy: Filters out unreliable sources
# 2. Time Efficiency: Users get pre-vetted information
# 3. Source Transparency: Shows what was included/excluded
# 4. Customizable Thresholds: Can adjust quality requirements
# 5. Domain Expertise: Knows authoritative sources per field