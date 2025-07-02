"""
Deep Research System - All Features Visible
Complete UI with all configuration options visible from the start
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
    return os.getenv("UI_TOGGLE_ENABLED", "false").lower() == "true"

# --- RESEARCH FUNCTION ---
async def run_research_with_clarifications(
    query: str,
    skip_clarifications: bool,
    report_format: str,
    report_length: str,
    target_audience: str,
    use_enhanced: bool,
    use_new_architecture: bool,
    send_email_flag: bool,
    email_address: str,
    progress=gr.Progress()
):
    """Run research with optional clarification step."""
    global current_report_context
    
    if not query:
        yield "Please enter a research question.", "", None, gr.update(visible=False)
        return
    
    status_updates = []
    report_content = ""
    clarification_questions = None
    
    try:
        # Step 1: Get clarifying questions (unless skipped)
        if not skip_clarifications:
            progress(0.05, desc="Getting clarifying questions...")
            manager = ResearchManager()
            clarification_plan = await manager.get_clarifications(query)
            
            if clarification_plan.questions and not clarification_plan.skip_reason:
                # Format questions for display
                questions_display = "### 🤔 Clarifying Questions:\n\n"
                questions_list = []
                
                for i, q in enumerate(clarification_plan.questions, 1):
                    questions_display += f"**{i}. {q.question}**\n"
                    questions_display += f"   *Category: {q.category} | Priority: {q.priority}*\n\n"
                    questions_list.append({
                        "question": q.question,
                        "category": q.category,
                        "priority": q.priority
                    })
                
                clarification_questions = questions_list
                status_updates.append("💡 Generated clarifying questions")
                status_updates.append("⏸️ Paused for your input - please answer the questions below")
                
                yield "\n".join(status_updates), "", clarification_questions, gr.update(visible=True)
                return  # Stop here and wait for user to continue with answers
        
        # Step 2: Run full research
        progress(0.1, desc="Starting research...")
        
        # Build query with preferences
        enhanced_query = f"""{query}

Report Preferences:
- Format: {report_format}
- Length: {report_length}
- Audience: {target_audience}
- Enhanced Features: {use_enhanced}
"""
        
        # Create manager
        manager = ResearchManagerAdapter(
            use_new_architecture=use_new_architecture,
            enable_monitoring=True
        )
        
        # Progress mapping
        progress_steps = {
            "🔍 View trace": 0.15,
            "🤔 Analyzing": 0.2,
            "📋 Planning": 0.3,
            "🔍 Executing": 0.5,
            "✅ Collected": 0.7,
            "📝 Generating": 0.85,
            "📧 Sending": 0.95,
            "✅ Complete": 1.0
        }
        
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
                yield "\n".join(status_updates[-10:]), report_content, None, gr.update(visible=False)
        
        # Save to history
        research_history.add_entry(query, report_content, {
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
        
        # Show follow-up section
        yield "\n".join(status_updates[-10:]), report_content, None, gr.update(visible=True)
        
    except Exception as e:
        logger.error(f"Research error: {e}")
        yield f"Error: {str(e)}", "Research failed. Please try again.", None, gr.update(visible=False)

async def continue_with_answers(
    query: str,
    questions: List[Dict],
    answer1: str, answer2: str, answer3: str,
    report_format: str,
    report_length: str,
    target_audience: str,
    use_enhanced: bool,
    use_new_architecture: bool,
    send_email_flag: bool,
    email_address: str,
    progress=gr.Progress()
):
    """Continue research after answering clarifying questions."""
    # Build enhanced query with answers
    enhanced_query = query
    
    # Add clarification answers
    answers = [answer1, answer2, answer3]
    clarification_context = ""
    
    for i, answer in enumerate(answers):
        if i < len(questions) and answer and answer.strip():
            clarification_context += f"\n- {questions[i]['question']}: {answer}"
    
    if clarification_context:
        enhanced_query += f"\n\nAdditional Context from Clarifications:{clarification_context}"
    
    # Run research with enhanced query
    async for update in run_research_with_clarifications(
        enhanced_query,
        skip_clarifications=True,  # Skip clarifications since we already have them
        report_format=report_format,
        report_length=report_length,
        target_audience=target_audience,
        use_enhanced=use_enhanced,
        use_new_architecture=use_new_architecture,
        send_email_flag=send_email_flag,
        email_address=email_address,
        progress=progress
    ):
        yield update

# --- FOLLOW-UP FUNCTION ---
async def handle_followup(question: str):
    """Handle follow-up questions about the report."""
    if not current_report_context["report"]:
        return "No report available for follow-up questions."
    
    try:
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
    gr.Markdown("# 🔬 Deep Research System")
    gr.Markdown("*AI-powered research with clarifying questions and comprehensive configuration*")
    
    # Hidden state for questions
    questions_state = gr.State(None)
    
    with gr.Tab("🔍 Research"):
        # Query Input
        with gr.Row():
            with gr.Column(scale=3):
                query_input = gr.Textbox(
                    label="Research Question",
                    placeholder="Enter your research question (e.g., 'What are the latest developments in quantum computing?')",
                    lines=3
                )
            
            with gr.Column(scale=1):
                skip_clarifications = gr.Checkbox(
                    label="Skip clarifying questions",
                    value=False,
                    info="Check to go straight to research"
                )
        
        # Configuration Options (Always Visible)
        with gr.Group():
            gr.Markdown("### 📋 Report Configuration")
            
            with gr.Row():
                with gr.Column():
                    report_format = gr.Radio(
                        choices=["Executive Summary", "Technical Deep-Dive", "Comparative Analysis"],
                        value="Executive Summary",
                        label="Report Format",
                        info="Choose the style of your report"
                    )
                
                with gr.Column():
                    report_length = gr.Radio(
                        choices=["Brief (300 words)", "Standard (800 words)", "Comprehensive (1500+ words)"],
                        value="Standard (800 words)",
                        label="Report Length",
                        info="Select desired report length"
                    )
                
                with gr.Column():
                    target_audience = gr.Radio(
                        choices=["General Public", "Technical Experts", "Business Leaders"],
                        value="General Public",
                        label="Target Audience",
                        info="Who will read this report?"
                    )
        
        # Advanced Options
        with gr.Accordion("⚙️ Advanced Options", open=False):
            with gr.Row():
                with gr.Column():
                    use_enhanced = gr.Checkbox(
                        label="Use Enhanced Features",
                        value=True,
                        info="Enable quality filtering & query expansion (recommended)"
                    )
                    
                    use_new_architecture = gr.Checkbox(
                        label="🚀 Use Beta Architecture",
                        value=False,
                        info="AI-powered workflow optimization (30-50% faster)",
                        visible=check_beta_eligibility()
                    )
                
                with gr.Column():
                    send_email_checkbox = gr.Checkbox(
                        label="Send report via email",
                        value=False
                    )
                    
                    email_input = gr.Textbox(
                        label="Email Address",
                        placeholder="your@email.com",
                        visible=False
                    )
        
        # Action Button
        research_btn = gr.Button(
            "🚀 Start Research",
            variant="primary",
            size="lg"
        )
        
        # Progress Bar
        progress_bar = gr.Progress()
        
        # Clarification Section (Hidden initially)
        with gr.Group(visible=False) as clarification_section:
            gr.Markdown("### 🤔 Answer Clarifying Questions")
            gr.Markdown("*Provide answers to refine your research (all optional):*")
            
            answer1 = gr.Textbox(label="Answer 1", placeholder="Your answer here...")
            answer2 = gr.Textbox(label="Answer 2", placeholder="Your answer here...")
            answer3 = gr.Textbox(label="Answer 3", placeholder="Your answer here...")
            
            continue_btn = gr.Button("Continue with Research", variant="primary")
        
        # Output Section
        with gr.Row():
            with gr.Column(scale=1):
                status_output = gr.Textbox(
                    label="Research Progress",
                    lines=12,
                    value="Ready to start research...",
                    interactive=False
                )
            
            with gr.Column(scale=2):
                report_output = gr.Markdown(
                    value="*Your research report will appear here...*"
                )
        
        # Follow-up Section
        with gr.Group(visible=False) as followup_section:
            gr.Markdown("### 🔄 Follow-up Questions")
            with gr.Row():
                followup_input = gr.Textbox(
                    label="Ask a follow-up question",
                    placeholder="e.g., 'Can you elaborate on the security implications?'",
                    lines=2,
                    scale=4
                )
                followup_btn = gr.Button("Ask", scale=1)
            
            followup_output = gr.Markdown()
    
    with gr.Tab("📊 History & Analytics"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Research History")
                history_display = gr.Textbox(
                    lines=20,
                    value=load_history(),
                    interactive=False
                )
                refresh_history_btn = gr.Button("🔄 Refresh")
            
            with gr.Column():
                gr.Markdown("### Analytics")
                analytics_display = gr.JSON(
                    value=load_analytics()
                )
                refresh_analytics_btn = gr.Button("🔄 Refresh")
    
    with gr.Tab("ℹ️ About"):
        gr.Markdown("""
        ## Deep Research System Features
        
        ### 🎯 Core Capabilities:
        1. **Clarifying Questions** - AI identifies ambiguities and asks for clarification
        2. **Flexible Configuration** - Multiple report formats, lengths, and audiences
        3. **Manager Agent** - Orchestrates the entire research workflow
        4. **Agent Handoff** - Seamless context passing between specialized agents
        5. **Follow-up Questions** - Continue the conversation about your report
        6. **Email Delivery** - Get reports sent directly to your inbox
        7. **Research History** - Track and review all past research
        8. **Performance Analytics** - Understand your research patterns
        
        ### 🤖 Agent Team:
        - **Manager Agent** - Workflow orchestration
        - **Clarifier Agent** - Question generation
        - **Planner Agent** - Search strategy
        - **Search Agent** - Information gathering
        - **Writer Agent** - Report synthesis
        - **Email Agent** - Report delivery
        - **Follow-up Agent** - Q&A handling
        
        ### 💡 Tips:
        - Answer clarifying questions for more targeted research
        - Choose report format based on your needs
        - Use follow-up questions to dive deeper
        - Check analytics to see your research patterns
        """)
    
    # --- EVENT HANDLERS ---
    
    # Email visibility toggle
    send_email_checkbox.change(
        fn=lambda x: gr.update(visible=x),
        inputs=[send_email_checkbox],
        outputs=[email_input]
    )
    
    # Main research button
    def handle_research_click(*args):
        """Handle the research button click."""
        # Convert args to named parameters
        query = args[0]
        skip_clarify = args[1]
        
        # Generator wrapper
        async def research_generator():
            async for update in run_research_with_clarifications(*args):
                yield update
        
        return research_generator()
    
    research_outputs = [status_output, report_output, questions_state, clarification_section]
    
    research_btn.click(
        fn=handle_research_click,
        inputs=[
            query_input, skip_clarifications,
            report_format, report_length, target_audience,
            use_enhanced, use_new_architecture,
            send_email_checkbox, email_input
        ],
        outputs=research_outputs
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[followup_section]
    )
    
    # Continue button after clarifications
    continue_btn.click(
        fn=continue_with_answers,
        inputs=[
            query_input, questions_state,
            answer1, answer2, answer3,
            report_format, report_length, target_audience,
            use_enhanced, use_new_architecture,
            send_email_checkbox, email_input
        ],
        outputs=[status_output, report_output, questions_state, clarification_section]
    ).then(
        fn=lambda: gr.update(visible=True),
        outputs=[followup_section]
    )
    
    # Follow-up handling
    followup_btn.click(
        fn=handle_followup,
        inputs=[followup_input],
        outputs=[followup_output]
    )
    
    # History refresh
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
    print("🚀 DEEP RESEARCH SYSTEM - ALL FEATURES VISIBLE")
    print("="*70)
    print("\n✅ Complete Feature Set:")
    print("  • Report Format: Executive Summary, Technical, Comparative")
    print("  • Report Length: Brief, Standard, Comprehensive")
    print("  • Target Audience: General, Technical, Business")
    print("  • Clarifying Questions with input fields")
    print("  • Enhanced features toggle")
    print("  • Beta architecture option")
    print("  • Email delivery")
    print("  • Follow-up questions")
    print("  • History & Analytics")
    print("\n📍 Access: http://localhost:7860")
    print("   Codespaces: Make port 7860 public in PORTS tab")
    print("\n" + "="*70 + "\n")
    
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )