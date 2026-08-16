"""Gmail tools: send_email, gmail_search, gmail_read (+ auth & formatting helpers)."""

import os
import base64

from langchain_core.tools import tool
from langchain_community.tools.gmail import GmailSendMessage, GmailSearch
import langchain_community.tools.gmail as gmail_send_module
from langchain_community.tools.gmail.utils import build_resource_service

from googleapiclient.discovery import Resource
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

import markdown as md

from config import Config

# Fix for pydantic v2 + Python 3.14
gmail_send_module.Resource = Resource
GmailSendMessage.model_rebuild()
GmailSearch.model_rebuild()


def _get_gmail_creds():
    """Auto-refreshes expired token. Re-auths via browser if revoked."""
    SCOPES = ["https://mail.google.com/"]
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                os.remove("token.json")
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return creds


def _build_professional_html_email(message: str) -> str:
    """Convert a plain or markdown message into a polished HTML email body."""
    if not message or not message.strip():
        return "<p></p>"

    if "<html" in message.lower() or "<body" in message.lower():
        return message.strip()

    clean_message = message.strip()
    converted_body = md.markdown(clean_message, extensions=["extra"])

    return f"""
    <html>
        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #222; max-width: 700px; margin: 0; padding: 16px;">
            <style>
                p {{ margin: 0 0 6px 0; padding: 0; }}
                ul {{ margin: 4px 0 6px 0; padding-left: 18px; }}
                li {{ margin: 0; padding: 0; }}
                br {{ line-height: 1.2; }}
            </style>
            {converted_body}
        </body>
    </html>
    """


def _extract_email_body(payload) -> str:
    """Recursively decode text/plain (or HTML fallback) body from a Gmail message payload."""
    mime = payload.get("mimeType", "")
    data = (payload.get("body") or {}).get("data")
    if data and mime.startswith("text/"):
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        text = _extract_email_body(part)
        if text:
            return text
    return ""


@tool
def send_email(to: list, subject: str, message: str):
    """Send a polished email via Gmail. Requires to, subject, and message parameters."""
    credentials = _get_gmail_creds()
    api_resource = build_resource_service(credentials=credentials)
    gmail_tool = GmailSendMessage(api_resource=api_resource)
    html_message = _build_professional_html_email(message)
    return gmail_tool.run({
        "to": to,
        "subject": subject,
        "message": html_message
    })


@tool
def gmail_search(query: str, max_results: int = 5) -> str:
    """
    Search Gmail messages and return matching emails with their IDs, subjects, senders, dates, and snippets.

    Uses Gmail search operators in 'query', e.g.:
    - 'from:someone@example.com'
    - 'subject:invoice'
    - 'is:unread'
    - 'newer_than:7d'
    - 'has:attachment'

    ALWAYS use this first to find emails. Use gmail_read with the returned message ID to see the full body.
    """
    try:
        credentials = _get_gmail_creds()
        api_resource = build_resource_service(credentials=credentials)
        search_tool = GmailSearch(api_resource=api_resource)
        results = search_tool.run({
            "query": query,
            "resource": "messages",
            "max_results": max_results,
        })
        return str(results)
    except Exception as e:
        return f"Error searching Gmail: {str(e)}"


@tool
def gmail_read(message_id: str) -> str:
    """
    Read the full content of a single Gmail message by its message ID.
    Get the message ID from gmail_search results first.
    Returns sender, subject, date, and the full plain-text body.
    """
    try:
        credentials = _get_gmail_creds()
        api_resource = build_resource_service(credentials=credentials)
        msg = (
            api_resource.users().messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = _extract_email_body(msg.get("payload", {}))
        return (
            f"From: {headers.get('from', 'Unknown')}\n"
            f"To: {headers.get('to', 'Unknown')}\n"
            f"Date: {headers.get('date', 'Unknown')}\n"
            f"Subject: {headers.get('subject', '(no subject)')}\n\n"
            f"Body:\n{body.strip() or '(empty body)'}"
        )
    except Exception as e:
        return f"Error reading Gmail message: {str(e)}"
