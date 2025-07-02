# === CLARIFIER AGENT FOR INTELLIGENT QUERY REFINEMENT ===
# Purpose: Analyze user queries and generate context-specific clarifying questions
# to improve research quality by understanding user intent and requirements

# --- IMPORT DEPENDENCIES ---
from pydantic import BaseModel, Field
from agents import Agent
from typing import List
import logging

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEFINE CLARIFIER AGENT INSTRUCTIONS ---
INSTRUCTIONS = """You are an expert research assistant specializing in understanding user intent.
Given a research query, generate 3-5 highly specific clarifying questions that will help 
narrow down and improve the research results.

Your questions should:
1. Be specific to the query content (not generic)
2. Address potential ambiguities or missing context
3. Help understand the user's actual goal or use case
4. Identify scope boundaries (time period, geography, domain)
5. Clarify technical depth needed (beginner, expert, academic)

DO NOT ask generic questions like "What's your budget?" or "What's your timeline?"
Instead, focus on questions that directly impact what information should be researched.

Examples:
Query: "top aircraft in UK air force"
Good questions:
- "What time period interests you? (Current fleet, WWII era, Cold War, or all-time)"
- "Which criteria matter most: combat effectiveness, speed, range, or versatility?"
- "Are you looking for fighters, bombers, transport aircraft, or all types?"

Query: "best AI frameworks for agents"
Good questions:
- "Are you building conversational agents, autonomous agents, or multi-agent systems?"
- "What programming language do you prefer: Python, JavaScript, or others?"
- "Do you need production-ready frameworks or are research/experimental ones acceptable?"
"""

# --- DEFINE OUTPUT SCHEMAS ---
class ClarifyingQuestion(BaseModel):
    """A single clarifying question with its purpose"""
    question: str = Field(description="The clarifying question to ask the user")
    purpose: str = Field(description="Why this question helps improve research quality")
    impact: str = Field(description="How the answer will affect search strategy")

class ClarificationPlan(BaseModel):
    """Collection of clarifying questions for a research query"""
    original_query: str = Field(description="The user's original research query")
    query_analysis: str = Field(description="Brief analysis of what's unclear or could be refined")
    questions: List[ClarifyingQuestion] = Field(description="3-5 clarifying questions")
    skip_reason: str = Field(default="", description="If no clarification needed, explain why")

# --- INITIALIZE CLARIFIER AGENT ---
try:
    clarifier_agent = Agent(
        name="ClarifierAgent",
        instructions=INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=ClarificationPlan,
        tools=[]  # No tools needed - pure analysis
    )
    logger.info("Clarifier agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize clarifier agent: {e}")
    raise

# === USAGE EXAMPLE ===
# The clarifier agent is called before the main research pipeline:
# 1. User submits query
# 2. Clarifier analyzes and generates questions
# 3. User answers questions (optional)
# 4. Enhanced query passed to research pipeline