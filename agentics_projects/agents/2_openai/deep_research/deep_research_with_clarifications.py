"""
Deep Research System with Clarifying Questions UI
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
from email_agent import send_email
from research_history import ResearchHistory
# from beta_feature_manager import check_beta_eligibility, get_user_metrics
from followup_agent import FollowUpHandler

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
research_history = ResearchHistory()
follow_up_context = FollowUpHandler()

# --- CORE RESEARCH FUNCTION WITH CLARIFICATIONS ---
async def get_clarifying_questions(query: str) -> Tuple[bool, List[Dict[str, str]]]:
    """Get clarifying questions for the query."""
    try:
        # Create manager just for clarification
        manager = ResearchManagerAdapter()
        
        # Get clarifications
        clarification_plan = await manager.old_manager.get_clarifications(query)
        
        if clarification_plan.questions and not clarification_plan.skip_reason:
            questions = []
            for q in clarification_plan.questions:
                questions.append({
                    "question": q.question,
                    "category": q.category,
                    "priority": q.priority
                })
            return True, questions
        else:
            return False, []
    except Exception as e:
        logger.error(f"Error getting clarifications: {e}")
        return False, []

async def run_research_with_answers(
    query: str,
    clarification_answers: Dict[str, str],
    report_format: str,
    report_length: str,
    target_audience: str,
    use_enhanced: bool,
    use_new_architecture: bool,
    send_email_flag: bool,
    email_address: str
):
    """Run research with clarification answers included."""
    # Enhance query with clarification answers
    enhanced_query = f"{query}\n\nAdditional Context from Clarifications:\n"
    for question, answer in clarification_answers.items():
        if answer.strip():
            enhanced_query += f"- {question}: {answer}\n"
    
    enhanced_query += f"""
Report Preferences:
- Format: {report_format}
- Length: {report_length}
- Audience: {target_audience}
- Enhanced Features: {use_enhanced}
    """
    
    # Create manager
    manager = ResearchManagerAdapter(use_new_architecture=use_new_architecture)
    
    # Run research
    status_updates = []
    report_content = ""
    
    async for chunk in manager.run(enhanced_query):
        if chunk.startswith("---"):
            report_content = chunk
        else:
            status_updates.append(chunk)
            yield "\n".join(status_updates[-10:]), report_content
    
    # Store in history
    research_history.add_entry(query, report_content)
    follow_up_context.set_report(report_content)
    
    # Send email if requested
    if send_email_flag and email_address and report_content:
        try:
            await send_email(email_address, query, report_content)
            status_updates.append("✅ Email sent successfully!")
        except Exception as e:
            status_updates.append(f"❌ Email failed: {str(e)}")
    
    yield "\n".join(status_updates[-10:]), report_content

# --- GRADIO INTERFACE ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research System")
    gr.Markdown("*Ask a question, refine with clarifications, get comprehensive research*")
    
    # State to store clarifying questions
    clarification_state = gr.State({})
    
    # --- STEP 1: INITIAL QUERY ---
    with gr.Group():
        gr.Markdown("### Step 1: Enter Your Research Question")
        query_textbox = gr.Textbox(
            label="Research Question",
            placeholder="e.g., 'What are the latest AI developments?'",
            lines=2
        )
        get_clarifications_btn = gr.Button("Get Clarifying Questions", variant="primary")
    
    # --- STEP 2: CLARIFYING QUESTIONS ---
    with gr.Group(visible=False) as clarification_group:
        gr.Markdown("### Step 2: Answer Clarifying Questions")
        gr.Markdown("*These questions will help refine your research:*")
        
        # Dynamic components for questions
        clarification_components = []
        for i in range(5):  # Max 5 questions
            with gr.Row(visible=False) as row:
                label = gr.Markdown("")
                answer = gr.Textbox(
                    label=f"Answer {i+1}",
                    placeholder="Type your answer here (optional)",
                    lines=2
                )
                clarification_components.append((row, label, answer))
    
    # --- STEP 3: RESEARCH OPTIONS ---
    with gr.Group(visible=False) as options_group:
        gr.Markdown("### Step 3: Configure Research Options")
        
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
                    label="Use Enhanced Features",
                    value=True
                )
                
                use_new_architecture = gr.Checkbox(
                    label="🚀 Use Beta Architecture",
                    value=False
                )
        
        # Email options
        with gr.Row():
            send_email_checkbox = gr.Checkbox(label="Send report via email")
            email_input = gr.Textbox(
                label="Email Address",
                placeholder="your@email.com",
                visible=False
            )
        
        run_research_btn = gr.Button("Run Research", variant="primary", size="lg")
    
    # --- OUTPUT SECTION ---
    with gr.Group():
        gr.Markdown("### Research Progress & Results")
        status_box = gr.Textbox(
            label="Status",
            lines=10,
            value="Ready to start...",
            interactive=False
        )
        
        report_output = gr.Markdown(
            value="*Your research report will appear here...*"
        )
    
    # --- EVENT HANDLERS ---
    def process_clarifications(query):
        """Get clarifying questions and update UI."""
        if not query:
            return (
                gr.update(visible=False),  # clarification_group
                gr.update(visible=False),  # options_group
                {},  # clarification_state
                *[gr.update(visible=False) for _ in range(5)],  # rows
                *["" for _ in range(5)],  # labels
            )
        
        # Get clarifying questions
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        needs_clarification, questions = loop.run_until_complete(get_clarifying_questions(query))
        
        if not needs_clarification or not questions:
            # No clarifications needed, go straight to options
            return (
                gr.update(visible=False),  # clarification_group
                gr.update(visible=True),   # options_group
                {},  # clarification_state
                *[gr.update(visible=False) for _ in range(5)],  # rows
                *["" for _ in range(5)],  # labels
            )
        
        # Show clarifying questions
        updates = []
        labels = []
        state = {}
        
        for i in range(5):
            if i < len(questions):
                q = questions[i]
                updates.append(gr.update(visible=True))
                labels.append(f"**{q['question']}** ({q['category']})")
                state[q['question']] = ""
            else:
                updates.append(gr.update(visible=False))
                labels.append("")
        
        return (
            gr.update(visible=True),   # clarification_group
            gr.update(visible=True),   # options_group
            state,  # clarification_state
            *updates,  # rows
            *labels,  # labels
        )
    
    def collect_answers(*args):
        """Collect answers from clarification inputs."""
        # First 3 args are: clarification_state, query, and 5 answer inputs
        state = args[0]
        answers = args[1:6]
        
        # Update state with answers
        questions = list(state.keys())
        for i, answer in enumerate(answers):
            if i < len(questions) and answer:
                state[questions[i]] = answer
        
        return state
    
    async def run_with_clarifications(
        query, clarification_state, report_format, report_length,
        target_audience, use_enhanced, use_new_architecture,
        send_email_flag, email_address
    ):
        """Run research with all parameters."""
        async for status, report in run_research_with_answers(
            query, clarification_state, report_format, report_length,
            target_audience, use_enhanced, use_new_architecture,
            send_email_flag, email_address
        ):
            yield status, report
    
    # Connect get clarifications button
    outputs = [
        clarification_group, options_group, clarification_state,
        *[row for row, _, _ in clarification_components],
        *[label for _, label, _ in clarification_components]
    ]
    
    get_clarifications_btn.click(
        fn=process_clarifications,
        inputs=[query_textbox],
        outputs=outputs
    )
    
    # Update clarification state when answers change
    answer_inputs = [answer for _, _, answer in clarification_components]
    for answer_input in answer_inputs:
        answer_input.change(
            fn=collect_answers,
            inputs=[clarification_state, *answer_inputs],
            outputs=[clarification_state]
        )
    
    # Email checkbox handler
    send_email_checkbox.change(
        fn=lambda x: gr.update(visible=x),
        inputs=[send_email_checkbox],
        outputs=[email_input]
    )
    
    # Run research button
    run_research_btn.click(
        fn=run_with_clarifications,
        inputs=[
            query_textbox, clarification_state, report_format, report_length,
            target_audience, use_enhanced, use_new_architecture,
            send_email_checkbox, email_input
        ],
        outputs=[status_box, report_output]
    )

# Launch the app
if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 LAUNCHING DEEP RESEARCH WITH CLARIFICATIONS...")
    print("="*50)
    print("\nFeatures:")
    print("✅ Clarifying questions with input fields")
    print("✅ Manager agent orchestration")
    print("✅ Agent handoff system")
    print("\n" + "="*50 + "\n")
    
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False
    )