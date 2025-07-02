"""
Deep Research System - Complete Version with All Features
Includes: Clarifying Questions, Email, Follow-up, History, Analytics, Beta Toggle
"""
import gradio as gr
import asyncio
from typing import List, Dict, Any, Tuple
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment configuration
load_dotenv()

# Import core components
from research_manager_adapter import ResearchManagerAdapter
from research_manager import ResearchManager
from email_agent import send_email
from research_history import ResearchHistory
from followup_agent import followup_agent
from agents import Runner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
research_history = ResearchHistory()

# Global state for follow-up context
current_report_context = {"report": "", "query": ""}

# --- HELPER FUNCTIONS ---
def load_history():
    """Load research history for display."""
    history_data = research_history.get_history(limit=20)
    if not history_data:
        return "No research history yet."
    
    # Format history for display
    formatted = []
    for entry in history_data:
        formatted.append(f"📅 {entry['timestamp']}")
        formatted.append(f"❓ Query: {entry['query'][:100]}...")
        formatted.append(f"📝 Report: {len(entry.get('report', ''))} characters")
        formatted.append("-" * 50)
    
    return "\n".join(formatted)

def load_analytics():
    """Load analytics data."""
    return research_history.get_analytics()

def check_beta_eligibility():
    """Check if beta features should be shown."""
    # For POC, we'll show beta features if enabled in env
    return os.getenv("UI_TOGGLE_ENABLED", "false").lower() == "true"

# --- CLARIFYING QUESTIONS FUNCTION ---
async def get_clarifying_questions(query: str):
    """Get clarifying questions for the query."""
    try:
        manager = ResearchManager()
        clarification_plan = await manager.get_clarifications(query)
        
        if clarification_plan.questions and not clarification_plan.skip_reason:
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

# --- MAIN RESEARCH FUNCTION ---
async def run_research_complete(
    query: str,
    answer1: str, answer2: str, answer3: str, answer4: str, answer5: str,
    questions: List[str],
    report_format: str,
    report_length: str,
    target_audience: str,
    use_enhanced: bool,
    use_new_architecture: bool,
    send_email_flag: bool,
    email_address: str,
    progress=gr.Progress()
):
    """Run research with all features."""
    global current_report_context
    
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
    
    # Create manager with architecture preference
    manager = ResearchManagerAdapter(
        use_new_architecture=use_new_architecture,
        enable_monitoring=True
    )
    
    # Track progress
    status_updates = []
    report_content = ""
    
    progress(0, desc="Starting research...")
    
    # Progress mapping
    progress_steps = {
        "🔍 View trace": 0.05,
        "🤔 Analyzing": 0.1,
        "💡 Generated": 0.15,
        "📋 Planning": 0.25,
        "🔍 Executing": 0.5,
        "✅ Collected": 0.7,
        "📝 Generating": 0.85,
        "📧 Sending": 0.95,
        "✅ Complete": 1.0,
        "---": 1.0
    }
    
    try:
        async for chunk in manager.run(enhanced_query):
            # Update progress
            for key, value in progress_steps.items():
                if key in chunk:
                    progress(value, desc=chunk.split('\n')[0][:50])
                    break
            
            if chunk.startswith("---"):
                report_content = chunk
                current_report_context = {"report": report_content, "query": query}
            else:
                status_updates.append(chunk)
                yield "\n".join(status_updates[-10:]), report_content, gr.update(visible=False), ""
        
        # Save to history
        research_history.add_entry(query, report_content, {
            "clarification_answers": clarification_context,
            "report_format": report_format,
            "report_length": report_length,
            "target_audience": target_audience,
            "architecture": "new" if use_new_architecture else "old"
        })
        
        # Send email if requested
        if send_email_flag and email_address and report_content:
            try:
                await send_email(email_address, query, report_content)
                status_updates.append("✅ Email sent successfully!")
            except Exception as e:
                status_updates.append(f"❌ Email failed: {str(e)}")
        
        progress(1.0, desc="Research complete!")
        
        # Show follow-up section if report generated
        if report_content and "---" in report_content:
            yield "\n".join(status_updates[-10:]), report_content, gr.update(visible=True), ""
        else:
            yield "\n".join(status_updates[-10:]), report_content, gr.update(visible=False), ""
            
    except Exception as e:
        logger.error(f"Research error: {e}")
        yield f"Error: {str(e)}", "Research failed. Please try again.", gr.update(visible=False), ""

# --- FOLLOW-UP FUNCTION ---
async def handle_followup(question: str):
    """Handle follow-up questions about the report."""
    if not current_report_context["report"]:
        return "No report available for follow-up questions."
    
    try:
        # Create context-aware prompt
        messages = [
            {
                "role": "system",
                "content": f"""Previous research query: {current_report_context['query']}
                
Full report:
{current_report_context['report']}

Provide a detailed, helpful response to the follow-up question."""
            },
            {
                "role": "user",
                "content": question
            }
        ]
        
        # Use followup agent
        result = await Runner.run(
            followup_agent,
            messages=messages
        )
        
        return f"### Follow-up Response:\n\n{result.data.response}"
        
    except Exception as e:
        logger.error(f"Follow-up error: {e}")
        return f"Error processing follow-up: {str(e)}"

# --- GRADIO INTERFACE ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky"), title="Deep Research") as demo:
    gr.Markdown("# 🔬 Deep Research System - Complete Edition")
    gr.Markdown("*AI-powered research with clarifying questions, follow-ups, and history*")
    
    # Hidden states
    questions_state = gr.State([])
    
    with gr.Tab("🔍 Research"):
        # Step 1: Query Input
        with gr.Group():
            gr.Markdown("### Step 1: Enter Your Research Question")
            query_input = gr.Textbox(
                label="What would you like to research?",
                placeholder="e.g., 'What are the latest developments in quantum computing?'",
                lines=3
            )
            clarify_btn = gr.Button("🤔 Get Clarifying Questions", variant="primary")
        
        # Step 2: Clarifying Questions
        with gr.Group(visible=False) as clarify_group:
            gr.Markdown("### Step 2: Review Clarifying Questions")
            clarify_display = gr.Markdown()
            
            gr.Markdown("### Step 3: Provide Additional Context (Optional)")
            answer1 = gr.Textbox(label="Answer 1", visible=False)
            answer2 = gr.Textbox(label="Answer 2", visible=False)
            answer3 = gr.Textbox(label="Answer 3", visible=False)
            answer4 = gr.Textbox(label="Answer 4", visible=False)
            answer5 = gr.Textbox(label="Answer 5", visible=False)
        
        # Step 3: Configuration
        with gr.Group(visible=False) as config_group:
            gr.Markdown("### Step 4: Configure Your Report")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Report options
                    with gr.Row():
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
                    
                    target_audience = gr.Radio(
                        choices=["General Public", "Technical Experts", "Business Leaders"],
                        value="General Public",
                        label="Target Audience"
                    )
                
                with gr.Column(scale=1):
                    # Features
                    use_enhanced = gr.Checkbox(
                        label="Use Enhanced Features",
                        value=True,
                        info="Quality filtering & query expansion"
                    )
                    
                    use_new_architecture = gr.Checkbox(
                        label="🚀 Use Beta Architecture",
                        value=False,
                        info="AI-powered workflow (30-50% faster)",
                        visible=check_beta_eligibility()
                    )
                    
                    # Email options
                    send_email_checkbox = gr.Checkbox(
                        label="Send report via email"
                    )
                    email_input = gr.Textbox(
                        label="Email Address",
                        placeholder="your@email.com",
                        visible=False
                    )
            
            research_btn = gr.Button("🚀 Run Research", variant="primary", size="lg")
        
        # Progress bar
        with gr.Row():
            progress_bar = gr.Progress()
        
        # Output Section
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
                    value="*Your research report will appear here...*"
                )
        
        # Follow-up Section
        with gr.Group(visible=False) as followup_group:
            gr.Markdown("### 🔄 Follow-up Questions")
            with gr.Row():
                followup_input = gr.Textbox(
                    label="Ask a follow-up question about the report",
                    placeholder="e.g., 'Can you elaborate on the security implications?'",
                    lines=2,
                    scale=4
                )
                followup_btn = gr.Button("Ask", variant="secondary", scale=1)
            
            followup_output = gr.Markdown()
    
    with gr.Tab("📊 History & Analytics"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Research History")
                history_display = gr.Textbox(
                    label="Past Researches",
                    lines=20,
                    value=load_history(),
                    interactive=False
                )
                refresh_history_btn = gr.Button("🔄 Refresh History")
            
            with gr.Column():
                gr.Markdown("### Analytics Dashboard")
                analytics_display = gr.JSON(
                    value=load_analytics(),
                    label="Research Analytics"
                )
                refresh_analytics_btn = gr.Button("🔄 Refresh Analytics")
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## Deep Research System - Proof of Concept
        
        ### ✨ Key Features:
        
        1. **Clarifying Questions** - AI generates 3-5 questions to refine your query
        2. **Manager Agent** - Orchestrates the entire research workflow
        3. **Agent Handoff** - Seamless context passing between specialized agents
        4. **Follow-up Questions** - Ask additional questions about your report
        5. **Email Delivery** - Send reports directly to your inbox
        6. **Research History** - Track all your past research
        7. **Analytics Dashboard** - Insights into your research patterns
        8. **Beta Architecture** - Test the new AI-powered workflow
        
        ### 🤖 Agent Team:
        - **Clarifier Agent** - Identifies ambiguities
        - **Planner Agent** - Creates search strategies
        - **Search Agent** - Gathers information
        - **Writer Agent** - Synthesizes reports
        - **Email Agent** - Handles delivery
        - **Follow-up Agent** - Answers questions
        
        ### 🚀 Architecture Options:
        - **Classic**: Procedural pipeline (reliable)
        - **Beta**: AI-orchestrated workflow (30-50% faster)
        """)
    
    # --- EVENT HANDLERS ---
    def show_clarifications(query):
        """Process query and show clarifying questions."""
        if not query:
            return (
                gr.update(visible=False), gr.update(visible=False),
                "", [],
                gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False)
            )
        
        # Get clarifying questions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        needs_clarify, display_text, questions = loop.run_until_complete(
            get_clarifying_questions(query)
        )
        
        # Update UI
        answer_updates = []
        for i in range(5):
            if i < len(questions):
                answer_updates.append(gr.update(
                    visible=True,
                    label=f"Answer to: {questions[i]}",
                    placeholder="Type your answer here (optional)"
                ))
            else:
                answer_updates.append(gr.update(visible=False))
        
        return (
            gr.update(visible=True),
            gr.update(visible=True),
            display_text,
            questions,
            *answer_updates
        )
    
    # Email visibility
    send_email_checkbox.change(
        fn=lambda x: gr.update(visible=x),
        inputs=[send_email_checkbox],
        outputs=[email_input]
    )
    
    # Connect events
    clarify_btn.click(
        fn=show_clarifications,
        inputs=[query_input],
        outputs=[
            clarify_group, config_group,
            clarify_display, questions_state,
            answer1, answer2, answer3, answer4, answer5
        ]
    )
    
    research_btn.click(
        fn=run_research_complete,
        inputs=[
            query_input,
            answer1, answer2, answer3, answer4, answer5,
            questions_state,
            report_format, report_length, target_audience,
            use_enhanced, use_new_architecture,
            send_email_checkbox, email_input
        ],
        outputs=[status_output, report_output, followup_group, followup_output]
    )
    
    followup_btn.click(
        fn=handle_followup,
        inputs=[followup_input],
        outputs=[followup_output]
    )
    
    refresh_history_btn.click(
        fn=load_history,
        outputs=[history_display]
    )
    
    refresh_analytics_btn.click(
        fn=load_analytics,
        outputs=[analytics_display]
    )

# Launch
if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 DEEP RESEARCH SYSTEM - COMPLETE VERSION")
    print("="*70)
    print("\n✅ All Features Included:")
    print("  1. Clarifying questions with input fields")
    print("  2. Manager agent orchestration")
    print("  3. Agent handoff system")
    print("  4. Follow-up questions")
    print("  5. Email delivery")
    print("  6. Research history")
    print("  7. Analytics dashboard")
    print("  8. Beta architecture toggle")
    print("\n📍 Access: http://localhost:7860")
    print("   Codespaces: Make port 7860 public in PORTS tab")
    print("\n" + "="*70 + "\n")
    
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )