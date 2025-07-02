# === DEEP RESEARCH GRADIO INTERFACE ===
# Purpose: Create a user-friendly web interface for the deep research system,
# allowing users to input queries and receive comprehensive research reports

# --- IMPORT DEPENDENCIES ---
# UI framework and utilities
import gradio as gr
from dotenv import load_dotenv
from research_manager_adapter import ResearchManagerAdapter
from followup_agent import followup_agent, FollowUpContext, FollowUpResponse
from agents import Runner
from beta_feature_manager import check_beta_eligibility, record_beta_usage
import os
import hashlib

# --- LOAD ENVIRONMENT VARIABLES ---
# Read .env file and inject variables into the system environment
load_dotenv(override=True)  # override=True ensures fresh configs override any existing values

# --- GLOBAL CONTEXT FOR FOLLOW-UPS ---
follow_up_context = FollowUpContext()

# --- IMPORT HISTORY MODULE ---
from research_history import research_history

# --- USER IDENTIFICATION ---
def get_user_id(request: gr.Request) -> str:
    """Get a consistent user ID from request headers"""
    if request:
        # Try to get user ID from headers or session
        user_agent = request.headers.get("user-agent", "")
        client_host = request.client.host if hasattr(request, "client") else "unknown"
        
        # Create a simple hash-based user ID
        user_string = f"{client_host}:{user_agent}"
        user_id = hashlib.md5(user_string.encode()).hexdigest()[:16]
    else:
        # Fallback for local testing
        user_id = "local_user"
    
    return user_id

# === WHAT THIS DOES ===
# 1. Reads .env file from project root (typically contains):
#    - OPENAI_API_KEY: For LLM model access (GPT-4, etc.)
#    - SERPER_API_KEY: For web search capabilities via Serper API
#    - SENDGRID_API_KEY: For email notifications of research results
#    - LANGSMITH_API_KEY: For tracing and debugging agent interactions
#
# 2. Makes these variables accessible via os.environ['KEY_NAME']
#
# 3. override=True ensures that:
#    - Fresh values from .env replace any existing environment variables
#    - Prevents stale configurations from previous runs
#    - Useful when switching between development/production environments

# --- DEFINE ASYNC RESEARCH FUNCTION ---
async def run(query: str, report_format: str, report_length: str, target_audience: str, 
              use_enhanced_features: bool, use_new_architecture: bool, request: gr.Request, progress=gr.Progress()):
    """Execute the research pipeline and yield status updates.
    
    Args:
        query: The research topic submitted by the user
        report_format: Style of report (executive, technical, comparative)
        report_length: Length preference (brief, standard, comprehensive)
        target_audience: Who the report is for (general, technical, business)
        use_enhanced_features: Whether to use enhanced search and planning
        progress: Gradio progress tracker
        
    Yields:
        tuple: (status_text, report_text) for display in UI
    """
    # --- TRACK BETA FEATURE USAGE ---
    user_id = get_user_id(request)
    if use_new_architecture:
        # Record that user enabled the beta feature
        record_beta_usage(user_id, "new_architecture_toggle", True)
    
    # --- CREATE RESEARCH MANAGER INSTANCE ---
    # Use adapter for safe architecture switching
    manager = ResearchManagerAdapter(
        use_new_architecture=use_new_architecture,
        monitoring_enabled=True
    )
    
    # Keep backward compatibility for enhanced features
    if not use_enhanced_features:
        manager.old_manager.use_enhanced_search = False
        manager.old_manager.use_enhanced_planner = False
    
    # Build enhanced query with preferences
    enhanced_query = f"{query}\n\nReport Preferences:\n- Format: {report_format}\n- Length: {report_length}\n- Audience: {target_audience}"
    
    # Track progress
    status_updates = []
    report_content = "*Research in progress...*"
    
    # Progress tracking
    progress_steps = {
        "🔍 View trace:": 0.1,
        "🤔 Analyzing query": 0.2,
        "📋 Planning search": 0.3,
        "🔍 Executing": 0.5,
        "✅ Collected": 0.7,
        "📝 Generating": 0.8,
        "📧 Sending": 0.9,
        "✅ Email sent": 0.95,
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
            yield (status_text, report_content, gr.update(visible=False), "")
    
    # Store report in context for follow-ups
    follow_up_context.set_report(report_content)
    
    # Get performance summary if using new architecture
    if use_new_architecture:
        perf_data = manager.get_performance_summary()
        arch_data = perf_data.get('architectures', {}).get('new', {})
        
        perf_text = f"""### Architecture Performance
        
**Execution Time**: {arch_data.get('avg_execution_time', 'N/A'):.1f}s
**Success Rate**: {arch_data.get('success_rate', 'N/A'):.1%}
**Quality Score**: Embedded in report

**Optimizations Applied**: 
- Dynamic workflow selection
- Intelligent agent orchestration
- Performance-based adaptation
        """
        
        # Return with performance data visible
        yield (status_text, report_content, gr.update(visible=True), perf_text)
    else:
        # Return without performance data
        yield (status_text, report_content, gr.update(visible=False), "")

# --- DEFINE FOLLOW-UP HANDLER ---
async def handle_followup(question: str):
    """Process follow-up questions about the research report.
    
    Args:
        question: The follow-up question from the user
        
    Returns:
        str: Follow-up response in markdown format
    """
    if not follow_up_context.original_report:
        return "⚠️ No research report available. Please run a research query first."
    
    if not question.strip():
        return "⚠️ Please enter a follow-up question."
    
    try:
        # Build context-aware prompt
        context_prompt = follow_up_context.get_context_prompt(question)
        
        # Get follow-up response
        result = await Runner.run(
            followup_agent,
            context_prompt
        )
        
        response = result.final_output_as(FollowUpResponse)
        
        # Add to history
        follow_up_context.add_follow_up(response)
        
        # Format response
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

# --- HISTORY AND ANALYTICS FUNCTIONS ---
def load_history():
    """Load and format research history for display."""
    history = research_history.get_history(limit=20)
    
    # Format for dataframe
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

# === HOW THE ASYNC GENERATOR WORKS ===
# 1. ResearchManager().run() is an async generator
# 2. It yields status updates throughout the research process:
#    - Trace URL for debugging
#    - Planning progress
#    - Search progress
#    - Report generation status
#    - Email sending status
#    - Final markdown report
# 3. Gradio automatically handles these yields and updates the UI

# --- BETA FEATURE CHECK ---
def update_beta_visibility(request: gr.Request):
    """Check if user is eligible for beta features"""
    user_id = get_user_id(request)
    
    # Get user metrics from history
    user_queries = [h for h in research_history.history if h.get("user_id") == user_id]
    user_metrics = {
        "total_queries": len(user_queries)
    }
    
    # Check eligibility
    is_eligible = check_beta_eligibility(user_id, "new_architecture_toggle", user_metrics)
    
    # Also check if explicitly enabled via environment
    force_show = os.getenv("UI_TOGGLE_ENABLED", "false").lower() == "true"
    
    return gr.update(visible=(is_eligible or force_show))

# --- CREATE GRADIO INTERFACE ---
# Build the web UI with custom theme and components
with gr.Blocks(theme=gr.themes.Default(primary_hue="sky")) as ui:
    # --- TITLE ---
    gr.Markdown("# Deep Research")
    
    # --- INPUT SECTION ---
    with gr.Row():
        with gr.Column(scale=2):
            query_textbox = gr.Textbox(
                label="What topic would you like to research?",
                placeholder="Enter your research question here (e.g., 'Latest AI agent frameworks in 2025')",
                lines=3
            )
        
        with gr.Column(scale=1):
            # --- CUSTOMIZATION OPTIONS ---
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
            
            use_new_architecture = gr.Checkbox(
                label="🚀 Use Intelligent Manager Architecture (Beta)",
                value=False,  # Start with false for safety
                info="Enable AI-powered workflow optimization for 30-50% faster results",
                visible=False  # Initially hidden, shown only for eligible users
            )
    
    # --- ACTION BUTTON ---
    run_button = gr.Button(
        "Run Research", 
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
                value="Ready to start research...",
                interactive=False
            )
        
    report = gr.Markdown(
        label="Report",
        value="*Your research report will appear here...*"
    )
    
    # --- PERFORMANCE INSIGHTS SECTION ---
    with gr.Accordion("📊 Performance Insights", open=False, visible=False) as perf_accordion:
        perf_summary = gr.Markdown(value="*Performance metrics will appear here...*")
    
    # --- FOLLOW-UP SECTION ---
    with gr.Row(visible=False) as follow_up_section:
        gr.Markdown("### 🔄 Follow-up Questions")
        with gr.Column():
            follow_up_input = gr.Textbox(
                label="Ask a follow-up question about the report",
                placeholder="e.g., 'Can you elaborate on the security implications?' or 'What are the implementation costs?'",
                lines=2
            )
            follow_up_button = gr.Button("Ask Follow-up", variant="secondary")
            follow_up_response = gr.Markdown(
                value="*Follow-up response will appear here...*"
            )
    
    # --- HISTORY & ANALYTICS TAB ---
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
    # Function to show follow-up section after report generation
    def show_followup_section(report_text):
        if report_text and "---" in report_text:
            return gr.update(visible=True)
        return gr.update(visible=False)
    
    # Connect button click to run function
    run_button.click(
        fn=run,              # Function to call
        inputs=[query_textbox, report_format, report_length, target_audience, use_enhanced, use_new_architecture],
        outputs=[status_box, report, perf_accordion, perf_summary]  # Update status, report, and performance
    ).then(
        fn=show_followup_section,
        inputs=[report],
        outputs=[follow_up_section]
    )
    
    # --- SUBMIT ON ENTER ---
    # Allow users to press Enter to submit (uses default settings)
    query_textbox.submit(
        fn=run,
        inputs=[query_textbox, report_format, report_length, target_audience, use_enhanced, use_new_architecture],
        outputs=[status_box, report, perf_accordion, perf_summary]
    ).then(
        fn=show_followup_section,
        inputs=[report],
        outputs=[follow_up_section]
    )
    
    # --- FOLLOW-UP HANDLERS ---
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
    
    # --- HISTORY HANDLERS ---
    refresh_history_btn.click(
        fn=load_history,
        outputs=[history_display]
    ).then(
        fn=load_analytics,
        outputs=[analytics_display]
    )
    
    # Load history on startup and check beta eligibility
    ui.load(
        fn=load_history,
        outputs=[history_display]
    ).then(
        fn=load_analytics,
        outputs=[analytics_display]
    ).then(
        fn=update_beta_visibility,
        outputs=[use_new_architecture]
    )

# === GRADIO INTERFACE FEATURES ===
# 1. Theme: Sky blue theme for professional appearance
# 2. Async Support: Handles async generators automatically
# 3. Real-time Updates: Shows progress as research proceeds
# 4. Markdown Rendering: Formats the final report nicely
# 5. Responsive Design: Works on desktop and mobile

# --- LAUNCH THE APPLICATION ---
print("\n" + "="*50)
print("🚀 LAUNCHING DEEP RESEARCH SYSTEM...")
print("="*50)
print("\nThe app will be available at:")
print("  - Local: http://localhost:7860")
print("  - In Codespaces: Check the PORTS tab and make port 7860 public")
print("\n" + "="*50 + "\n")

ui.launch(
    inbrowser=False,  # Don't auto-open in Codespaces
    server_name="0.0.0.0",  # Listen on all interfaces
    server_port=7860,  # Default Gradio port
    share=False,  # Use Codespaces port forwarding instead
    show_api=False  # Hide API docs for cleaner output
)

# === LAUNCH OPTIONS EXPLAINED ===
# inbrowser=True: Opens the UI in your default web browser
# server_name="0.0.0.0": Makes app accessible from network (not just localhost)
# server_port=7860: Standard Gradio port (change if conflicts)
# share=True: Creates a public URL for sharing (useful for demos)

# === USER WORKFLOW ===
# 1. User enters research query in textbox
# 2. Clicks "Run" or presses Enter
# 3. Sees real-time status updates:
#    - 🔍 View trace URL
#    - 📋 Planning search strategy...
#    - ✅ Search plan created
#    - 🔍 Executing searches...
#    - ✅ Collected X words
#    - 📝 Generating report...
#    - ✅ Report generated
#    - 📧 Sending email...
#    - ✅ Email sent
# 4. Final markdown report displays with:
#    - Executive summary
#    - Key findings
#    - Recommendations
#    - Professional formatting

# === ERROR HANDLING ===
# - If any phase fails, user still sees partial results
# - Email failures don't prevent report display
# - All errors logged to console for debugging
# - Graceful degradation ensures best possible output

# === CUSTOMIZATION OPTIONS ===
# 1. Change theme: gr.themes.Soft(), gr.themes.Glass(), etc.
# 2. Add examples: gr.Examples() component
# 3. Add file upload: gr.File() for document research
# 4. Add history: Store previous queries and reports
# 5. Add export: Button to download report as PDF/MD

# === SECURITY CONSIDERATIONS ===
# - API keys stored in .env, never in code
# - Input sanitization handled by Gradio
# - Rate limiting should be added for production
# - Consider authentication for sensitive deployments

# === CONNECTION TO BACKEND ===
# This UI connects to:
# - ResearchManager: Orchestrates the agent pipeline
# - Multiple AI agents: Planner, Search, Writer, Email
# - External APIs: OpenAI, Web Search, SendGrid