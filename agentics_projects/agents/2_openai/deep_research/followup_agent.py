# === FOLLOW-UP AGENT FOR INTERACTIVE RESEARCH ===
# Purpose: Handle follow-up questions about generated research reports,
# providing deeper insights and clarifications

# --- IMPORT DEPENDENCIES ---
from pydantic import BaseModel, Field
from agents import Agent
from typing import List, Optional
import logging

# --- LOGGING CONFIGURATION ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- FOLLOW-UP INSTRUCTIONS ---
FOLLOWUP_INSTRUCTIONS = """You are an expert research analyst providing follow-up insights.
Given a research report and a follow-up question, provide a detailed, focused response.

Your role:
1. Answer specific questions about the report content
2. Provide deeper analysis on requested topics
3. Clarify technical points or terminology
4. Expand on implications or recommendations
5. Compare different aspects mentioned in the report
6. Suggest related areas for further research

Guidelines:
- Base your response primarily on the provided report
- Acknowledge if something wasn't covered in the original research
- Be concise but thorough (200-400 words)
- Use the same expertise level as the original report
- Maintain consistency with the report's findings
- Suggest specific next steps when appropriate

Do not:
- Contradict the original report without clear justification
- Introduce entirely new topics not related to the query
- Provide generic responses - be specific to the question
"""

# --- OUTPUT SCHEMAS ---
class FollowUpResponse(BaseModel):
    """Structured follow-up response"""
    question: str = Field(description="The follow-up question asked")
    response: str = Field(description="Detailed response to the question")
    related_sections: List[str] = Field(description="Sections from original report referenced")
    suggested_queries: List[str] = Field(description="Related follow-up questions user might ask")
    confidence_level: str = Field(description="High/Medium/Low confidence in response")

# --- INITIALIZE FOLLOW-UP AGENT ---
try:
    followup_agent = Agent(
        name="FollowUpAgent",
        instructions=FOLLOWUP_INSTRUCTIONS,
        model="gpt-4o-mini",
        output_type=FollowUpResponse,
        
        tools=[]
    )
    logger.info("Follow-up agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize follow-up agent: {e}")
    raise

# === FOLLOW-UP CATEGORIES ===
# Common types of follow-up questions to handle well:
# 1. Clarification: "What does X mean in this context?"
# 2. Elaboration: "Can you provide more details about Y?"
# 3. Implications: "What are the consequences of Z?"
# 4. Comparisons: "How does A compare to B?"
# 5. Applications: "How can this be applied to my situation?"
# 6. Limitations: "What are the limitations of this approach?"
# 7. Next Steps: "What should I do next?"

# === CONTEXT MANAGEMENT ===
class FollowUpContext:
    """Manages context between original report and follow-ups"""
    
    def __init__(self):
        self.original_report: Optional[str] = None
        self.follow_up_history: List[FollowUpResponse] = []
        self.key_topics: List[str] = []
    
    def set_report(self, report: str):
        """Store the original report for reference"""
        self.original_report = report
        self.extract_key_topics(report)
    
    def extract_key_topics(self, report: str):
        """Extract main topics from report for better follow-ups"""
        # Simple extraction - could be enhanced with NLP
        headers = [line.strip() for line in report.split('\n') if line.startswith('##')]
        self.key_topics = headers
    
    def add_follow_up(self, response: FollowUpResponse):
        """Track follow-up history"""
        self.follow_up_history.append(response)
    
    def get_context_prompt(self, question: str) -> str:
        """Build context-aware prompt for follow-up"""
        context = f"Original Report:\n{self.original_report}\n\n"
        
        if self.follow_up_history:
            context += "Previous Follow-ups:\n"
            for fu in self.follow_up_history[-3:]:  # Last 3 follow-ups
                context += f"Q: {fu.question}\nA: {fu.response[:200]}...\n\n"
        
        context += f"New Follow-up Question: {question}"
        return context

# === FOLLOW-UP ENHANCEMENTS ===
# 1. Dig Deeper: Automatically identify areas that could use elaboration
# 2. Cross-Reference: Link related sections of the report
# 3. Visual Aids: Suggest diagrams or charts for complex topics
# 4. External Resources: Recommend specific papers or sources
# 5. Practical Examples: Provide real-world applications