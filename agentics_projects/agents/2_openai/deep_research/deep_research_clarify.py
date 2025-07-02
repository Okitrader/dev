"""
Deep Research System with Clarifying Questions
Simplified version for proof of concept
"""
import gradio as gr
import asyncio
from typing import List, Dict, Any, Tuple
import logging
import os
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

# Import core components
from research_manager_adapter import ResearchManagerAdapter
from research_manager import ResearchManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for the report
current_report = ""

# --- CORE FUNCTIONS ---
async def get_clarifying_questions(query: str):
    """Get clarifying questions for the query."""
    try:
        # Create a research manager instance
        manager = ResearchManager()
        
        # Get clarifications
        clarification_plan = await manager.get_clarifications(query)
        
        if clarification_plan.questions and not clarification_plan.skip_reason:
            # Format questions for display
            questions_text = "### 🤔 Clarifying Questions:\n\n"
            question_list = []
            
            for i, q in enumerate(clarification_plan.questions, 1):
                questions_text += f"**{i}. {q.question}**\n"
                questions_text += f"   *Category: {q.category} | Priority: {q.priority}*\n\n"
                question_list.append(q.question)
            
            return True, questions_text, question_list
        else:
            return False, "No clarifications needed - query is clear!", []
            
    except Exception as e:
        logger.error(f"Error getting clarifications: {e}")
        return False, f"Error: {str(e)}", []

async def run_research_with_context(
    query: str,
    answer1: str,
    answer2: str,
    answer3: str,
    answer4: str,
    answer5: str,
    questions: List[str],
    report_format: str,
    report_length: str,
    target_audience: str,
    use_enhanced: bool,
    progress=gr.Progress()
):
    """Run research with clarification answers."""
    global current_report
    
    # Build enhanced query with answers
    enhanced_query = query
    
    # Add clarification answers if provided
    answers = [answer1, answer2, answer3, answer4, answer5]
    clarification_context = ""
    
    for i, (question, answer) in enumerate(zip(questions, answers)):
        if answer and answer.strip():
            clarification_context += f"\n- {question}: {answer}"
    
    if clarification_context:
        enhanced_query += f"\n\nAdditional Context:{clarification_context}"
    
    # Add preferences
    enhanced_query += f"""

Report Preferences:
- Format: {report_format}
- Length: {report_length}
- Audience: {target_audience}
- Enhanced Features: {use_enhanced}
"""
    
    # Create manager
    manager = ResearchManagerAdapter(use_new_architecture=False)
    
    # Track progress
    status_updates = []
    report_content = ""
    
    progress(0, desc="Starting research...")
    
    # Progress mapping
    progress_steps = {
        "🔍 Analyzing": 0.1,
        "📋 Planning": 0.2,
        "🔍 Searching": 0.4,
        "✅ Collected": 0.6,
        "📝 Writing": 0.8,
        "✅ Complete": 1.0
    }
    
    try:
        async for chunk in manager.run(enhanced_query):
            # Update progress
            for key, value in progress_steps.items():
                if any(k in chunk for k in key.split()):
                    progress(value, desc=chunk.split('\n')[0][:50])
                    break
            
            if chunk.startswith("---"):
                report_content = chunk
                current_report = report_content
            else:
                status_updates.append(chunk)
                yield "\n".join(status_updates[-10:]), report_content
        
        progress(1.0, desc="Research complete!")
        
    except Exception as e:
        logger.error(f"Research error: {e}")
        yield f"Error: {str(e)}", "Research failed. Please try again."

# --- GRADIO INTERFACE ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research") as demo:
    gr.Markdown("# 🔬 Deep Research System")
    gr.Markdown("*AI-powered research with clarifying questions*")
    
    # Hidden state for questions
    questions_state = gr.State([])
    
    with gr.Tab("Research"):
        # Step 1: Query Input
        with gr.Group():
            gr.Markdown("### Step 1: Enter Your Research Question")
            query_input = gr.Textbox(
                label="What would you like to research?",
                placeholder="e.g., 'What are the latest developments in AI?'",
                lines=2
            )
            clarify_btn = gr.Button("🤔 Get Clarifying Questions", variant="primary")
        
        # Step 2: Clarifying Questions Display
        with gr.Group(visible=False) as clarify_group:
            gr.Markdown("### Step 2: Review Clarifying Questions")
            clarify_display = gr.Markdown()
            
            gr.Markdown("### Step 3: Provide Additional Context (Optional)")
            gr.Markdown("*Answer any questions below to refine your research:*")
            
            answer1 = gr.Textbox(label="Answer to Question 1", placeholder="Your answer here...", visible=False)
            answer2 = gr.Textbox(label="Answer to Question 2", placeholder="Your answer here...", visible=False)
            answer3 = gr.Textbox(label="Answer to Question 3", placeholder="Your answer here...", visible=False)
            answer4 = gr.Textbox(label="Answer to Question 4", placeholder="Your answer here...", visible=False)
            answer5 = gr.Textbox(label="Answer to Question 5", placeholder="Your answer here...", visible=False)
        
        # Step 3: Configuration
        with gr.Group(visible=False) as config_group:
            gr.Markdown("### Step 4: Configure Your Report")
            
            with gr.Row():
                with gr.Column():
                    report_format = gr.Radio(
                        choices=["Executive Summary", "Technical Deep-Dive", "Comparative Analysis"],
                        value="Executive Summary",
                        label="Report Format"
                    )
                    
                    report_length = gr.Radio(
                        choices=["Brief (300 words)", "Standard (800 words)", "Comprehensive (1500+ words)"],
                        value="Standard (800 words)",
                        label="Report Length"
                    )
                
                with gr.Column():
                    target_audience = gr.Radio(
                        choices=["General Public", "Technical Experts", "Business Leaders"],
                        value="General Public",
                        label="Target Audience"
                    )
                    
                    use_enhanced = gr.Checkbox(
                        label="Use Enhanced Features (Better quality, slightly slower)",
                        value=True
                    )
            
            research_btn = gr.Button("🚀 Run Research", variant="primary", size="lg")
        
        # Output Section
        gr.Markdown("---")
        
        with gr.Row():
            with gr.Column(scale=1):
                status_output = gr.Textbox(
                    label="Research Progress",
                    lines=10,
                    value="Ready to start...",
                    interactive=False
                )
            
            with gr.Column(scale=2):
                report_output = gr.Markdown(
                    value="*Your research report will appear here...*",
                    label="Research Report"
                )
    
    with gr.Tab("How It Works"):
        gr.Markdown("""
        ## 🎯 Three-Step Research Process
        
        1. **Ask Your Question** - Enter any research topic
        2. **Get Clarifications** - AI generates 3-5 clarifying questions
        3. **Receive Report** - Get a comprehensive, tailored research report
        
        ### ✨ Features:
        - **Manager Agent** orchestrates the entire workflow
        - **Clarifier Agent** identifies ambiguities in your query
        - **Planner Agent** creates strategic search queries
        - **Search Agent** gathers information from the web
        - **Writer Agent** synthesizes a professional report
        - **Agent Handoff** ensures seamless context passing
        
        ### 🚀 Proof of Concept Features:
        - ✅ Clarifying questions with input fields
        - ✅ Manager agent with tools
        - ✅ Full agent handoff system
        """)
    
    # Event Handlers
    def show_clarifications(query):
        """Process query and show clarifying questions."""
        if not query:
            return (
                gr.update(visible=False),
                gr.update(visible=False),
                "",
                [],
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False)
            )
        
        # Get clarifying questions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        needs_clarify, display_text, questions = loop.run_until_complete(
            get_clarifying_questions(query)
        )
        
        # Update UI
        clarify_visible = True
        config_visible = True
        
        # Show answer fields based on number of questions
        answer_updates = []
        for i in range(5):
            if i < len(questions):
                answer_updates.append(gr.update(
                    visible=True,
                    label=f"Answer to: {questions[i]}"
                ))
            else:
                answer_updates.append(gr.update(visible=False))
        
        return (
            gr.update(visible=clarify_visible),
            gr.update(visible=config_visible),
            display_text,
            questions,
            *answer_updates
        )
    
    # Connect events
    clarify_btn.click(
        fn=show_clarifications,
        inputs=[query_input],
        outputs=[
            clarify_group,
            config_group,
            clarify_display,
            questions_state,
            answer1, answer2, answer3, answer4, answer5
        ]
    )
    
    research_btn.click(
        fn=run_research_with_context,
        inputs=[
            query_input,
            answer1, answer2, answer3, answer4, answer5,
            questions_state,
            report_format, report_length, target_audience,
            use_enhanced
        ],
        outputs=[status_output, report_output]
    )

# Launch
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 DEEP RESEARCH SYSTEM - PROOF OF CONCEPT")
    print("="*60)
    print("\n✅ Features:")
    print("  - Clarifying questions with input fields")
    print("  - Manager agent orchestration")
    print("  - Full agent handoff system")
    print("\n📍 Access the app at: http://localhost:7860")
    print("   In Codespaces: Use the PORTS tab to make port 7860 public")
    print("\n" + "="*60 + "\n")
    
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )