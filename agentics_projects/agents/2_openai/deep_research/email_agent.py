# === EMAIL AGENT FOR REPORT DISTRIBUTION ===
# Purpose: Create a specialized agent that converts research reports into 
# well-formatted HTML emails and sends them using the send_email tool

# --- IMPORT DEPENDENCIES ---
# System utilities and email services
import os
from typing import Dict
import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, function_tool
import logging

# --- LOGGING CONFIGURATION ---
# Set up logging for debugging and monitoring agent execution
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DEFINE EMAIL SENDING FUNCTION ---
@function_tool
def send_email(subject: str, html_body: str) -> Dict[str, str]:
    """
    Send out an email with the given subject and HTML body.

    Args:
        subject: Email subject line
        html_body: HTML-formatted email content

    Returns:
        Dict with status indicating success/failure
    """
    try:
        # --- INITIALIZE SENDGRID CLIENT ---
        sg = sendgrid.SendGridAPIClient(
            api_key=os.environ.get('SENDGRID_API_KEY')
        )

        # --- CONFIGURE EMAIL PARAMETERS ---
        from_email = "lites.e@gmail.com"  # Your verified sender
        to_emails = "lites.e@gmail.com"   # Recipient

        # --- CONSTRUCT AND SEND EMAIL ---
        mail = Mail(
            from_email=from_email,
            to_emails=to_emails,
            subject=subject,
            html_content=html_body
        )
        response = sg.send(mail)

        # --- LOG SUCCESS ---
        logger.info(f"Email sent successfully to {to_emails} (status: {response.status_code})")
        
        # --- RETURN SUCCESS ---
        return {
            "status": "success",
            "message": f"Email sent to {to_emails}",
            "status_code": response.status_code
        }

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "error_type": type(e).__name__
        }

# === WHAT @function_tool DOES ===
# 1. Converts regular Python function into agent-compatible tool
# 2. Automatically generates tool description from docstring
# 3. Handles parameter validation and type checking
# 4. Makes function callable by AI agents

# === USE CASES FOR EMAIL TOOL ===
# 1. Daily Research Summaries: Agent emails findings automatically
# 2. Alert Notifications: Critical market movements or defense updates
# 3. Report Distribution: Share analysis with team members
# 4. Audit Trail: Document agent activities via email

# --- DEFINE EMAIL AGENT INSTRUCTIONS ---
# These instructions shape how the agent formats and sends reports
# Enhanced email agent instructions
INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report. You should use your tool to send one email, providing the 
report converted into clean, well presented HTML with an appropriate subject line.

When formatting the HTML:
1. Use proper headings (<h1>, <h2>, <h3>) for structure
2. Apply bold (<strong>) and italic (<em>) for emphasis
3. Create lists (<ul>, <ol>) for enumerated items
4. Preserve any links with proper <a href="..."> tags
5. Add appropriate spacing and typography for readability
6. Include a professional email signature"""

# --- INITIALIZE EMAIL AGENT ---
# Create the agent with specific configuration for email handling
try:
    email_agent = Agent(
        # Agent identifier for tracing
        name="EmailAgent",
        
        # Instructions for report formatting and email composition
        instructions=INSTRUCTIONS,
        
        # Tools available - only needs send_email
        tools=[send_email],
        
        # Model choice - gpt-4o-mini sufficient for formatting
        model="gpt-4o-mini"
    )
    
    logger.info("Email agent initialized successfully")
    
except Exception as e:
    logger.error(f"Failed to initialize email agent: {e}")
    raise

# === WHAT THIS AGENT DOES ===
# 1. Receives a text report (from writer agent or other source)
# 2. Analyzes content structure and key points
# 3. Converts to professional HTML format with:
#    - Proper headings and sections
#    - Bold text for emphasis
#    - Bullet points or numbered lists
#    - Links preserved from source
#    - Clean typography and spacing
# 4. Generates appropriate subject line
# 5. Sends via send_email tool

# === HTML FORMATTING CAPABILITIES ===
# The agent will automatically:
# - Add <h1>, <h2>, <h3> tags for structure
# - Use <strong> and <em> for emphasis
# - Create <ul>/<ol> lists for frameworks or points
# - Wrap content in <p> tags for readability
# - Include <a href="..."> for any links
# - Add styling for professional appearance

# === EXAMPLE AGENT USAGE ===
# An agent with this tool could:
# ```
# email_agent = Agent(
#     name="EmailReporter",
#     instructions="Research the topic and email a summary",
#     tools=[send_email, WebSearchTool()],
#     model="gpt-4o-mini"
# )
# ```

# === HTML BODY EXAMPLE ===
# Agents can create rich HTML content:
# ```html
# <h2>AI Framework Research Results</h2>
# <p><strong>Date:</strong> June 28, 2025</p>
# <ul>
#   <li><strong>LangChain:</strong> Leading framework for LLM apps</li>
#   <li><strong>AutoGen:</strong> Microsoft's multi-agent system</li>
# </ul>
# <p>View full report <a href="...">here</a></p>
# ```

# === SECURITY CONSIDERATIONS ===
# - Keep SENDGRID_API_KEY in .env file only
# - Verify sender email in SendGrid dashboard
# - Consider rate limiting for production use
# - Sanitize HTML content to prevent injection

# === ERROR HANDLING BEST PRACTICES ===
# For production use, consider:
# 1. Retry logic for transient failures
# 2. Fallback to plain text if HTML fails
# 3. Queue system for failed emails
# 4. Monitoring for delivery rates

# === CONNECTION TO WORKFLOW ===
# Previous: Writer agent generates markdown report
# This Module: Converts to HTML and sends via email
# Next: User receives professional research report in inbox