import os
from typing import Dict, Optional

import sendgrid
from sendgrid.helpers.mail import Email, Mail, Content, To
from agents import Agent, ModelSettings, function_tool


DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")
DEFAULT_TO_EMAIL = os.getenv("DEFAULT_TO_EMAIL")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")


@function_tool
def send_email(
    subject: str,
    html_body: str,
    to_email: Optional[str] = None,
) -> Dict[str, str]:
    """
    Send an HTML email using SendGrid.

    Args:
        subject: Subject line for the email.
        html_body: HTML body content.
        to_email: Optional recipient email. Falls back to DEFAULT_TO_EMAIL.

    Returns:
        A structured status dictionary describing the outcome.
    """
    sender = DEFAULT_FROM_EMAIL
    recipient = to_email or DEFAULT_TO_EMAIL

    if not SENDGRID_API_KEY:
        return {
            "status": "error",
            "message": "Missing SENDGRID_API_KEY environment variable."
        }

    if not sender:
        return {
            "status": "error",
            "message": "Missing DEFAULT_FROM_EMAIL environment variable."
        }

    if not recipient:
        return {
            "status": "error",
            "message": "Missing recipient email. Provide to_email or set DEFAULT_TO_EMAIL."
        }

    if not subject or not subject.strip():
        return {
            "status": "error",
            "message": "Email subject cannot be empty."
        }

    if not html_body or not html_body.strip():
        return {
            "status": "error",
            "message": "Email body cannot be empty."
        }

    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)

        mail = Mail(
            from_email=Email(sender),
            to_emails=To(recipient),
            subject=subject.strip(),
            html_content=Content("text/html", html_body.strip()),
        )

        response = sg.client.mail.send.post(request_body=mail.get())

        return {
            "status": "success",
            "message": "Email sent successfully.",
            "recipient": recipient,
            "status_code": str(response.status_code),
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to send email: {str(e)}"
        }


INSTRUCTIONS = """
You are an email formatting and delivery assistant for a deep research system.

You will be given a completed research report, usually in markdown.
Your job is to:

1. Convert the report into a clean, professional HTML email.
2. Create a strong, relevant subject line based on the report topic.
3. Preserve readability using clear section headings, short paragraphs, bullet points where useful, and a polished layout.
4. Use simple inline HTML formatting only. Do not include CSS, JavaScript, markdown fences, or commentary outside the email content.
5. Make the email look appropriate for a professional business/research audience.
6. Then call the send_email tool exactly once.

Important rules:
- Output should be suitable for a polished commercial-style product.
- Keep the subject concise and professional.
- Do not invent facts not present in the report.
- Do not ask follow-up questions.
- Do not return the email body as plain text if you can format it as HTML.
"""

email_agent = Agent(
    name="EmailAgent",
    instructions=INSTRUCTIONS,
    tools=[send_email],
    model="gpt-5.4-mini",
    model_settings=ModelSettings(tool_choice="required"),
)