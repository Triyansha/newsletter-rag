"""
gmail_client.py - Gmail OAuth Integration and Email Fetching

Handles OAuth 2.0 authentication with Gmail and fetching email messages.
Uses google-api-python-client for API interactions.
"""

import os
import base64
import pickle
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from dataclasses import dataclass

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config


# ============================================================================
# Data Classes for Email Structure
# ============================================================================

@dataclass
class EmailMessage:
    """Represents a parsed email message."""
    id: str
    thread_id: str
    subject: str
    sender: str
    sender_email: str
    date: datetime
    snippet: str
    body_html: str
    body_text: str
    headers: dict
    labels: list


# ============================================================================
# Gmail Client Class
# ============================================================================

class GmailClient:
    """
    Gmail API client for fetching newsletter emails.
    
    Handles OAuth authentication and provides methods to fetch
    and parse email messages.
    """
    
    def __init__(self):
        """Initialize the Gmail client."""
        self.creds: Optional[Credentials] = None
        self.service = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail using OAuth 2.0.
        
        Returns:
            bool: True if authentication successful
        """
        # Check for existing valid credentials
        if Path(config.GMAIL_TOKEN_FILE).exists():
            with open(config.GMAIL_TOKEN_FILE, "rb") as token:
                self.creds = pickle.load(token)
        
        # Refresh or get new credentials if needed
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh expired credentials
                try:
                    self.creds.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    self.creds = None
            
            if not self.creds:
                # Run OAuth flow for new credentials
                if not Path(config.GMAIL_CREDENTIALS_FILE).exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {config.GMAIL_CREDENTIALS_FILE}. "
                        "Download it from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GMAIL_CREDENTIALS_FILE,
                    config.GMAIL_SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(config.GMAIL_TOKEN_FILE, "wb") as token:
                pickle.dump(self.creds, token)
        
        # Build the Gmail API service
        self.service = build("gmail", "v1", credentials=self.creds)
        return True
    
    def _parse_headers(self, headers: list) -> dict:
        """
        Parse email headers into a dictionary.
        
        Args:
            headers: List of header dictionaries from Gmail API
            
        Returns:
            Dictionary of header name -> value
        """
        return {h["name"].lower(): h["value"] for h in headers}
    
    def _extract_email_address(self, from_header: str) -> tuple:
        """
        Extract name and email from From header.
        
        Args:
            from_header: The From header value
            
        Returns:
            Tuple of (name, email)
        """
        if "<" in from_header and ">" in from_header:
            # Format: "Name <email@example.com>"
            parts = from_header.rsplit("<", 1)
            name = parts[0].strip().strip('"')
            email = parts[1].rstrip(">").strip()
        else:
            # Just an email address
            name = from_header
            email = from_header
        
        return name, email
    
    def _get_body_content(self, payload: dict) -> tuple:
        """
        Extract HTML and plain text body from email payload.
        
        Args:
            payload: The message payload from Gmail API
            
        Returns:
            Tuple of (html_content, text_content)
        """
        html_content = ""
        text_content = ""
        
        def extract_parts(part):
            nonlocal html_content, text_content
            
            mime_type = part.get("mimeType", "")
            
            if mime_type == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            
            elif mime_type == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    text_content = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            
            elif "parts" in part:
                for subpart in part["parts"]:
                    extract_parts(subpart)
        
        # Handle single part messages
        if "body" in payload and payload.get("body", {}).get("data"):
            data = payload["body"]["data"]
            content = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if payload.get("mimeType") == "text/html":
                html_content = content
            else:
                text_content = content
        
        # Handle multipart messages
        if "parts" in payload:
            for part in payload["parts"]:
                extract_parts(part)
        
        return html_content, text_content
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse email date string to datetime.
        
        Args:
            date_str: Date string from email header
            
        Returns:
            Parsed datetime object
        """
        # Common date formats in emails
        formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S%z",
        ]
        
        # Clean up the date string
        date_str = date_str.strip()
        # Remove parenthetical timezone names like "(PST)"
        if "(" in date_str:
            date_str = date_str.split("(")[0].strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Fallback to current time if parsing fails
        return datetime.now()
    
    def get_message(self, message_id: str) -> Optional[EmailMessage]:
        """
        Fetch and parse a single email message.
        
        Args:
            message_id: The Gmail message ID
            
        Returns:
            Parsed EmailMessage or None if error
        """
        try:
            msg = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()
            
            headers = self._parse_headers(msg.get("payload", {}).get("headers", []))
            sender_name, sender_email = self._extract_email_address(headers.get("from", ""))
            html_body, text_body = self._get_body_content(msg.get("payload", {}))
            
            return EmailMessage(
                id=msg["id"],
                thread_id=msg["threadId"],
                subject=headers.get("subject", "(No Subject)"),
                sender=sender_name,
                sender_email=sender_email,
                date=self._parse_date(headers.get("date", "")),
                snippet=msg.get("snippet", ""),
                body_html=html_body,
                body_text=text_body,
                headers=headers,
                labels=msg.get("labelIds", [])
            )
        
        except HttpError as e:
            print(f"Error fetching message {message_id}: {e}")
            return None
    
    def fetch_emails(
        self,
        query: str = "",
        max_results: int = None,
        after_date: datetime = None
    ) -> list[EmailMessage]:
        """
        Fetch emails matching the given query.
        
        Args:
            query: Gmail search query (e.g., "from:newsletter@example.com")
            max_results: Maximum number of emails to fetch
            after_date: Only fetch emails after this date
            
        Returns:
            List of EmailMessage objects
        """
        if not self.service:
            raise RuntimeError("Gmail client not authenticated. Call authenticate() first.")
        
        max_results = max_results or config.MAX_EMAILS_PER_FETCH
        
        # Build the query
        search_query = query
        if after_date:
            date_str = after_date.strftime("%Y/%m/%d")
            search_query = f"{search_query} after:{date_str}".strip()
        
        if config.DEBUG:
            print(f"Fetching emails with query: {search_query}")
        
        messages = []
        page_token = None
        
        try:
            while len(messages) < max_results:
                # Fetch message IDs
                result = self.service.users().messages().list(
                    userId="me",
                    q=search_query,
                    maxResults=min(100, max_results - len(messages)),
                    pageToken=page_token
                ).execute()
                
                msg_refs = result.get("messages", [])
                if not msg_refs:
                    break
                
                # Fetch full message content
                for msg_ref in msg_refs:
                    email = self.get_message(msg_ref["id"])
                    if email:
                        messages.append(email)
                    
                    if len(messages) >= max_results:
                        break
                
                # Check for more pages
                page_token = result.get("nextPageToken")
                if not page_token:
                    break
        
        except HttpError as e:
            print(f"Error fetching emails: {e}")
        
        return messages
    
    def fetch_recent_emails(self, days: int = None) -> list[EmailMessage]:
        """
        Fetch emails from the last N days.
        
        Args:
            days: Number of days to look back (default from config)
            
        Returns:
            List of EmailMessage objects
        """
        days = days or config.DAYS_TO_FETCH
        after_date = datetime.now() - timedelta(days=days)
        return self.fetch_emails(after_date=after_date)


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    # Test the Gmail client
    print("Testing Gmail Client...")
    print("=" * 50)
    
    client = GmailClient()
    
    try:
        print("Authenticating...")
        client.authenticate()
        print("✓ Authentication successful!")
        
        print("\nFetching recent emails...")
        emails = client.fetch_recent_emails(days=7)
        print(f"✓ Found {len(emails)} emails from the last 7 days")
        
        if emails:
            print("\nFirst email:")
            email = emails[0]
            print(f"  Subject: {email.subject}")
            print(f"  From: {email.sender} <{email.sender_email}>")
            print(f"  Date: {email.date}")
            print(f"  Has HTML: {bool(email.body_html)}")
            print(f"  Has Text: {bool(email.body_text)}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
