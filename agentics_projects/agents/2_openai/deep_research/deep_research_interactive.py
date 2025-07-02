# === DEEP RESEARCH GRADIO INTERFACE WITH INTERACTIVE CLARIFICATION ===
# Purpose: Create a user-friendly web interface for the deep research system,
# with interactive clarification questions before research execution

# --- IMPORT DEPENDENCIES ---
import gradio as gr
from dotenv import load_dotenv
from research_manager import ResearchManager
from followup_agent import followup_agent, FollowUpContext, FollowUpResponse
from clarifier_agent import clarifier_agent, ClarificationPlan
from agents import Runner
from research_history import research_history
import asyncio

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv(override=True)

# --- GLOBAL CONTEXT ---
follow_up_context = FollowUpContext()
current_clarification_plan = None
current_query_info = {}

# --- CLARIFICATION PHASE ---
async def get_clarifications(query: str, report_format: str, report_length: str, 
                           target_audience: str, use_enhanced_features: bool):
    """First phase: Get clarifying questions for the query."""
    global current_clarification_plan, current_query_info
    
    # Store query info for later use
    current_query_info = {
        "query": query,
        "report_format": report_format,
        "report_length": report_length,
        "target_audience": target_audience,
        "use_enhanced_features": use_enhanced_features
    }
    
    try:
        # Get clarifying questions
        result = await Runner.run(
            clarifier_agent,
            f"Research query: {query}",
        )
        
        current_clarification_plan = result.final_output_as(ClarificationPlan)
        
        if current_clarification_plan.questions and not current_clarification_plan.skip_reason:
            # Format questions for display
            questions_html = f"""
            <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin: 10px 0;">
                <h3>💡 Clarifying Questions</h3>
                <p><em>{current_clarification_plan.query_analysis}</em></p>
            </div>
            """
            
            # Create input components for each question
            inputs = []
            for i, q in enumerate(current_clarification_plan.questions):
                questions_html += f"""
                <div style="margin: 10px 0;">
                    <strong>Question {i+1}:</strong> {q.question}<br>
                    <em style="color: #666;">Purpose: {q.purpose}</em><br>
                    <em style="color: #666;">Impact: {q.impact}</em>
                </div>
                """
            
            return (
                questions_html,
                gr.update(visible=True),  # Show clarification section
                gr.update(visible=False),  # Hide research button
                "Ready for clarification"
            )
        else:
            # No clarification needed, proceed directly
            return (
                f"✅ Query is clear: {current_clarification_plan.skip_reason}",
                gr.update(visible=False),
                gr.update(visible=True),
                "No clarification needed - ready to research"
            )
            
    except Exception as e:
        return (
            f"⚠️ Error getting clarifications: {str(e)}",
            gr.update(visible=False),
            gr.update(visible=True),
            "Error in clarification"
        )

# --- RESEARCH PHASE WITH ANSWERS ---
async def run_with_clarifications(answer1: str, answer2: str, answer3: str, 
                                answer4: str, answer5: str, progress=gr.Progress()):
    """Second phase: Run research with clarification answers incorporated."""
    global current_query_info, current_clarification_plan
    
    # Build enhanced query with answers
    enhanced_query = current_query_info["query"]
    
    # Add clarification answers if provided
    answers = [answer1, answer2, answer3, answer4, answer5]
    clarification_text = "\n\nClarification Details:"
    
    if current_clarification_plan and current_clarification_plan.questions:
        for i, (q, answer) in enumerate(zip(current_clarification_plan.questions[:5], answers)):
            if answer and answer.strip():
                clarification_text += f"\n- {q.question} → {answer}"
    
    if clarification_text != "\n\nClarification Details:":
        enhanced_query += clarification_text
    
    # Add preferences
    enhanced_query += f"\n\nReport Preferences:\n- Format: {current_query_info['report_format']}\n- Length: {current_query_info['report_length']}\n- Audience: {current_query_info['target_audience']}"
    
    # Create research manager
    manager = ResearchManager(
        use_enhanced_search=current_query_info['use_enhanced_features'],
        use_enhanced_planner=current_query_info['use_enhanced_features']
    )
    
    # Track progress
    status_updates = []
    report_content = "*Research in progress...*"
    
    # Progress tracking
    progress_steps = {
        "🔍 View trace:": 0.1,
        "📋 Planning search": 0.3,
        "🔍 Executing": 0.5,
        "✅ Collected": 0.7,
        "📝 Generating": 0.8,
        "📧 Sending": 0.9,
        "✅ Email sent": 0.95,
        "💾 Research saved": 0.98,
        "---": 1.0
    }
    
    async for chunk in manager.run(enhanced_query):
        # Update progress bar
        for key, value in progress_steps.items():
            if key in chunk:
                progress(value, desc=chunk.split('\n')[0])
                break
        
        # Update status
        if chunk.startswith("---"):
            # Final report
            report_content = chunk
        else:
            # Status update
            status_updates.append(chunk)
            status_text = "\n".join(status_updates[-10:])  # Keep last 10 updates
            yield (status_text, report_content)
    
    # Store report in context for follow-ups
    follow_up_context.set_report(report_content)
    
    # Final yield with complete report
    yield (status_text, report_content)

# --- FOLLOW-UP HANDLER ---
async def handle_followup(question: str):
    """Process follow-up questions about the research report."""
    if not follow_up_context.original_report:
        return "⚠️ No research report available. Please run a research query first."
    
    if not question.strip():
        return "⚠️ Please enter a follow-up question."
    
    try:
        context_prompt = follow_up_context.get_context_prompt(question)
        result = await Runner.run(followup_agent, context_prompt)
        response = result.final_output_as(FollowUpResponse)
        follow_up_context.add_follow_up(response)
        
        formatted_response = f"""### Follow-up Response

**Your Question:** {response.question}

{response.response}

**Related Report Sections:** {', '.join(response.related_sections) if response.related_sections else 'General inquiry'}

**Suggested Follow-ups:**
{chr(10).join(f'- {q}' for q in response.suggested_queries[:3])}

*Confidence: {response.confidence_level}*
"""
        
        return formatted_response
        
    except Exception as e:
        return f"⚠️ Error processing follow-up: {str(e)}"

# --- HISTORY FUNCTIONS ---
def load_history():
    """Load and format research history for display."""
    history = research_history.get_history(limit=20)
    formatted = []
    for entry in history:
        formatted.append([
            entry['id'],
            entry['timestamp'].split('T')[0],
            entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query'],
            entry['metadata']['word_count'],
            ", ".join(entry['tags'])
        ])
    return formatted

def load_analytics():
    """Load analytics data."""
    return research_history.get_analytics()

# --- CREATE GRADIO INTERFACE ---
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    gr.Markdown("# Deep Research with Interactive Clarification")
    
    # --- INPUT SECTION ---
    with gr.Row():
        with gr.Column(scale=2):
            query_textbox = gr.Textbox(
                label="What topic would you like to research?",
                placeholder="Enter your research question here (e.g., 'Latest AI agent frameworks in 2025')",
                lines=3
            )
        
        with gr.Column(scale=1):
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
            
            use_enhanced = gr.Checkbox(
                label="Use Enhanced Features (Quality Filtering & Query Expansion)",
                value=True
            )
    
    # --- ACTION BUTTONS ---
    with gr.Row():
        analyze_button = gr.Button(
            "🔍 Analyze Query", 
            variant="primary",
            size="lg"
        )
        
        run_button = gr.Button(
            "🚀 Run Research", 
            variant="primary",
            size="lg",
            visible=False
        )
    
    # --- CLARIFICATION SECTION ---
    with gr.Column(visible=False) as clarification_section:
        clarification_display = gr.HTML()
        
        gr.Markdown("### 📝 Please answer the clarifying questions below:")
        answer1 = gr.Textbox(label="Answer to Question 1", placeholder="Your answer here...")
        answer2 = gr.Textbox(label="Answer to Question 2", placeholder="Your answer here...")
        answer3 = gr.Textbox(label="Answer to Question 3", placeholder="Your answer here...")
        answer4 = gr.Textbox(label="Answer to Question 4 (if applicable)", placeholder="Optional...")
        answer5 = gr.Textbox(label="Answer to Question 5 (if applicable)", placeholder="Optional...")
        
        proceed_button = gr.Button(
            "✅ Proceed with Research", 
            variant="primary",
            size="lg"
        )
    
    # --- PROGRESS SECTION ---
    with gr.Row():
        progress_bar = gr.Progress()
    
    # --- OUTPUT SECTION ---
    with gr.Row():
        with gr.Column():
            status_box = gr.Textbox(
                label="Progress Status",
                lines=10,
                max_lines=10,
                value="Ready to analyze your query...",
                interactive=False
            )
    
    report = gr.Markdown(
        label="Report",
        value="*Your research report will appear here...*"
    )
    
    # --- FOLLOW-UP SECTION ---
    with gr.Row(visible=False) as follow_up_section:
        gr.Markdown("### 🔄 Follow-up Questions")
        with gr.Column():
            follow_up_input = gr.Textbox(
                label="Ask a follow-up question about the report",
                placeholder="e.g., 'Can you elaborate on the security implications?'",
                lines=2
            )
            follow_up_button = gr.Button("Ask Follow-up", variant="secondary")
            follow_up_response = gr.Markdown(value="*Follow-up response will appear here...*")
    
    # --- HISTORY TAB ---
    with gr.Tab("📊 History & Analytics"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Research History")
                history_display = gr.Dataframe(
                    headers=["ID", "Date", "Query", "Words", "Tags"],
                    value=[],
                    interactive=False
                )
                refresh_history_btn = gr.Button("Refresh History", size="sm")
            
            with gr.Column():
                gr.Markdown("### Analytics Dashboard")
                analytics_display = gr.JSON(value={})
    
    # --- EVENT HANDLERS ---
    
    # Phase 1: Analyze query for clarifications
    analyze_button.click(
        fn=get_clarifications,
        inputs=[query_textbox, report_format, report_length, target_audience, use_enhanced],
        outputs=[clarification_display, clarification_section, run_button, status_box]
    )
    
    # Direct research (if no clarification needed)
    run_button.click(
        fn=run_with_clarifications,
        inputs=[gr.Textbox(value="", visible=False)] * 5,  # Empty answers
        outputs=[status_box, report]
    ).then(
        fn=lambda x: gr.update(visible=True) if x and "---" in x else gr.update(visible=False),
        inputs=[report],
        outputs=[follow_up_section]
    )
    
    # Phase 2: Proceed with clarifications
    proceed_button.click(
        fn=run_with_clarifications,
        inputs=[answer1, answer2, answer3, answer4, answer5],
        outputs=[status_box, report]
    ).then(
        fn=lambda x: gr.update(visible=True) if x and "---" in x else gr.update(visible=False),
        inputs=[report],
        outputs=[follow_up_section]
    )
    
    # Follow-up handlers
    follow_up_button.click(
        fn=handle_followup,
        inputs=[follow_up_input],
        outputs=[follow_up_response]
    )
    
    follow_up_input.submit(
        fn=handle_followup,
        inputs=[follow_up_input],
        outputs=[follow_up_response]
    )
    
    # History handlers
    refresh_history_btn.click(
        fn=load_history,
        outputs=[history_display]
    ).then(
        fn=load_analytics,
        outputs=[analytics_display]
    )
    
    # Load history on startup
    ui.load(
        fn=load_history,
        outputs=[history_display]
    ).then(
        fn=load_analytics,
        outputs=[analytics_display]
    )

# --- LAUNCH THE APPLICATION ---
ui.launch(
    inbrowser=False,
    server_name="0.0.0.0",
    server_port=7860,
    share=True
)