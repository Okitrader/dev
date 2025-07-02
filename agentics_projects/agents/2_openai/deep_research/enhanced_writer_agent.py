# === ENHANCED WRITER AGENT WITH CUSTOMIZATION SUPPORT ===
# Purpose: Advanced report writer that adapts style, length, and complexity
# based on user preferences

# --- IMPORT DEPENDENCIES ---
from pydantic import BaseModel, Field
from agents import Agent
from datetime import datetime
import logging
import re
from typing import Dict, Any, List

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- REPORT TEMPLATES ---
# Different structures for different formats
REPORT_TEMPLATES = {
    "Executive Summary": {
        "structure": [
            "## Executive Overview",
            "## Key Findings",
            "## Strategic Implications", 
            "## Recommended Actions",
            "## Risk Assessment"
        ],
        "style": "concise, bullet-pointed, decision-focused"
    },
    "Technical Deep-Dive": {
        "structure": [
            "## Technical Abstract",
            "## Background & Context",
            "## Technical Analysis",
            "## Implementation Details",
            "## Performance Metrics",
            "## Technical Recommendations",
            "## Future Considerations"
        ],
        "style": "detailed, technical terminology, code examples when relevant"
    },
    "Comparative Analysis": {
        "structure": [
            "## Overview",
            "## Comparison Framework",
            "## Option Analysis",
            "## Comparative Matrix",
            "## Strengths & Weaknesses",
            "## Recommendation",
            "## Decision Criteria"
        ],
        "style": "analytical, balanced, uses tables and comparisons"
    }
}

# --- LENGTH SPECIFICATIONS ---
LENGTH_TARGETS = {
    "Brief (300 words)": {"min": 250, "target": 300, "max": 350},
    "Standard (800 words)": {"min": 700, "target": 800, "max": 900},
    "Comprehensive (1500+ words)": {"min": 1400, "target": 1600, "max": 2000}
}

# --- AUDIENCE ADAPTATIONS ---
AUDIENCE_STYLES = {
    "General Public": "simple language, avoid jargon, use analogies, explain technical concepts",
    "Technical Experts": "technical precision, industry terminology, detailed specifications, assume background knowledge",
    "Business Leaders": "focus on ROI, strategic implications, risk/opportunity, executive summaries, clear action items"
}

# --- ENHANCED WRITER INSTRUCTIONS ---
def get_customized_instructions(format_type: str, length: str, audience: str) -> str:
    """Generate customized instructions based on preferences."""
    
    template = REPORT_TEMPLATES.get(format_type, REPORT_TEMPLATES["Executive Summary"])
    length_spec = LENGTH_TARGETS.get(length, LENGTH_TARGETS["Standard (800 words)"])
    audience_style = AUDIENCE_STYLES.get(audience, AUDIENCE_STYLES["General Public"])
    
    return f"""You are an adaptive professional report writer specializing in military innovation, 
cryptocurrency, options trading, and agentic AI development.

REPORT FORMAT: {format_type}
Required sections: {', '.join(template['structure'])}
Writing style: {template['style']}

TARGET LENGTH: {length_spec['target']} words (acceptable range: {length_spec['min']}-{length_spec['max']})

TARGET AUDIENCE: {audience}
Adaptation required: {audience_style}

Additional requirements:
1. Match the exact format structure provided
2. Calibrate language complexity for the audience
3. Ensure word count falls within specified range
4. Use markdown formatting appropriately
5. Include relevant data, statistics, and examples
6. For technical audiences, include specifications and implementation details
7. For business audiences, emphasize ROI and strategic value
8. For general audiences, use clear explanations and avoid jargon

Parse any "Report Preferences" section in the input and adapt accordingly."""

# --- ENHANCED OUTPUT SCHEMA ---
class EnhancedReportData(BaseModel):
    """Enhanced report with customization metadata"""
    query: str = Field(description="Original research query")
    markdown_report: str = Field(description="Full report in markdown format")
    word_count: int = Field(description="Actual report length in words")
    search_count: int = Field(description="Number of searches performed")
    report_format: str = Field(description="Format style used")
    target_audience: str = Field(description="Audience the report was written for")
    readability_score: str = Field(description="Estimated readability level")
    key_takeaways: List[str] = Field(description="3-5 bullet point takeaways")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="When report was generated"
    )
    quality_score: float = Field(default=0.0, description="Quality score (0-1) for the report")
    source_diversity: Dict[str, Any] = Field(default_factory=dict, description="Source diversity metrics")
    
    def calculate_quality(self):
        """Calculate quality score for the enhanced report"""
        # Import here to avoid circular dependency
        from performance_optimizer import performance_optimizer
        
        # Enhanced reports get bonus for customization
        base_score = performance_optimizer.calculate_quality_score({
            "word_count": self.word_count,
            "search_count": self.search_count,
            "markdown_report": self.markdown_report,
            "source_diversity": self.source_diversity
        })
        
        # Add bonus for enhanced features
        bonus = 0.0
        if self.key_takeaways and len(self.key_takeaways) >= 3:
            bonus += 0.05
        if self.readability_score:
            bonus += 0.05
        
        self.quality_score = min(base_score + bonus, 1.0)
        logger.info(f"Enhanced report quality score: {self.quality_score:.2f} (base: {base_score:.2f}, bonus: {bonus:.2f})")

# --- CREATE MULTIPLE WRITER AGENTS ---
# Pre-configured agents for different scenarios
writer_agents = {}

for format_type in REPORT_TEMPLATES:
    for audience in AUDIENCE_STYLES:
        key = f"{format_type}_{audience}"
        try:
            writer_agents[key] = Agent(
                name=f"WriterAgent_{key}",
                instructions=get_customized_instructions(
                    format_type, 
                    "Standard (800 words)",  # Default length
                    audience
                ),
                model="gpt-4o",  # Use more powerful model for better adaptation
                output_type=EnhancedReportData,
                
                tools=[]
            )
            logger.info(f"Initialized writer agent variant: {key}")
        except Exception as e:
            logger.error(f"Failed to initialize writer agent {key}: {e}")

# --- DEFAULT WRITER ---
default_writer = writer_agents.get("Executive Summary_General Public")

# === INTELLIGENT REPORT PARSING ===
def extract_preferences(input_text: str) -> dict:
    """Extract report preferences from input text."""
    preferences = {
        "format": "Executive Summary",
        "length": "Standard (800 words)",
        "audience": "General Public"
    }
    
    # Look for Report Preferences section
    if "Report Preferences:" in input_text:
        pref_section = input_text.split("Report Preferences:")[1].split("\n\n")[0]
        
        # Extract format
        if "Format:" in pref_section:
            for fmt in REPORT_TEMPLATES:
                if fmt in pref_section:
                    preferences["format"] = fmt
                    break
        
        # Extract length
        if "Length:" in pref_section:
            for length in LENGTH_TARGETS:
                if length in pref_section:
                    preferences["length"] = length
                    break
        
        # Extract audience
        if "Audience:" in pref_section:
            for aud in AUDIENCE_STYLES:
                if aud in pref_section:
                    preferences["audience"] = aud
                    break
    
    return preferences

# === GET APPROPRIATE WRITER ===
def get_writer_for_preferences(input_text: str):
    """Select the best writer agent based on preferences."""
    prefs = extract_preferences(input_text)
    key = f"{prefs['format']}_{prefs['audience']}"
    
    if key in writer_agents:
        # Update instructions with specific length requirement
        agent = writer_agents[key]
        agent.instructions = get_customized_instructions(
            prefs['format'],
            prefs['length'],
            prefs['audience']
        )
        return agent
    
    return default_writer

# === BENEFITS OF CUSTOMIZATION ===
# 1. Audience Appropriate: Reports match reader's expertise level
# 2. Purpose Driven: Format aligns with use case
# 3. Length Control: Meets time/attention constraints
# 4. Consistent Quality: Templates ensure completeness
# 5. Flexibility: Can adapt to any combination of preferences