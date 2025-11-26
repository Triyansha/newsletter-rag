"""
content_cleaner.py - HTML Content Extraction and Cleaning

Uses Trafilatura to extract clean, readable text from newsletter HTML.
Handles various newsletter formats and preserves important structure.
"""

import re
from dataclasses import dataclass
from typing import Optional
from html import unescape as html_unescape

import trafilatura
from trafilatura.settings import use_config

from gmail_client import EmailMessage


# ============================================================================
# Cleaned Content Structure
# ============================================================================

@dataclass
class CleanedContent:
    """Represents cleaned newsletter content."""
    title: str
    text: str
    word_count: int
    source_email_id: str
    source_subject: str
    source_sender: str
    source_date: str


# ============================================================================
# Trafilatura Configuration
# ============================================================================

def get_trafilatura_config():
    """
    Get optimized Trafilatura configuration for newsletters.
    
    Returns:
        Trafilatura configuration object
    """
    config = use_config()
    
    # Optimize for newsletter content extraction
    config.set("DEFAULT", "EXTRACTION_TIMEOUT", "30")
    config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")
    config.set("DEFAULT", "MIN_OUTPUT_SIZE", "50")
    
    return config


# ============================================================================
# Content Cleaner Class
# ============================================================================

class ContentCleaner:
    """
    Cleans and extracts readable content from newsletter HTML.
    
    Uses Trafilatura as the primary extraction engine with
    fallback methods for edge cases.
    """
    
    def __init__(self):
        """Initialize the content cleaner."""
        self.trafilatura_config = get_trafilatura_config()
        
        # Patterns to clean from text
        self._url_pattern = re.compile(
            r'https?://\S+|www\.\S+',
            re.IGNORECASE
        )
        self._email_pattern = re.compile(
            r'[\w\.-]+@[\w\.-]+\.\w+',
            re.IGNORECASE
        )
        self._whitespace_pattern = re.compile(r'\s+')
        self._separator_pattern = re.compile(r'[-=_]{10,}')
    
    def _extract_with_trafilatura(self, html: str) -> Optional[str]:
        """
        Extract text using Trafilatura.
        
        Args:
            html: HTML content to extract from
            
        Returns:
            Extracted text or None if extraction fails
        """
        try:
            extracted = trafilatura.extract(
                html,
                config=self.trafilatura_config,
                include_comments=False,
                include_tables=True,
                include_links=False,
                include_images=False,
                no_fallback=False,
                output_format='txt',
            )
            return extracted
        except Exception as e:
            print(f"Trafilatura extraction error: {e}")
            return None
    
    def _fallback_extraction(self, html: str) -> str:
        """
        Simple fallback HTML extraction when Trafilatura fails.
        
        Args:
            html: HTML content to extract from
            
        Returns:
            Extracted text
        """
        from html.parser import HTMLParser
        
        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.skip_tags = {'script', 'style', 'head', 'title', 'meta'}
                self.current_skip = False
            
            def handle_starttag(self, tag, attrs):
                if tag in self.skip_tags:
                    self.current_skip = True
            
            def handle_endtag(self, tag):
                if tag in self.skip_tags:
                    self.current_skip = False
                elif tag in {'p', 'div', 'br', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
                    self.text_parts.append('\n')
            
            def handle_data(self, data):
                if not self.current_skip:
                    self.text_parts.append(data)
        
        try:
            extractor = TextExtractor()
            extractor.feed(html)
            return ' '.join(extractor.text_parts)
        except Exception:
            # Last resort: regex-based extraction
            text = re.sub(r'<[^>]+>', ' ', html)
            return html_unescape(text)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text for better readability.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Unescape HTML entities
        text = html_unescape(text)
        
        # Remove excessive whitespace while preserving paragraph breaks
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Clean each line
            line = self._whitespace_pattern.sub(' ', line).strip()
            
            # Skip empty lines and separator lines
            if line and not self._separator_pattern.match(line):
                cleaned_lines.append(line)
        
        # Join with single newlines, collapse multiple blank lines
        text = '\n'.join(cleaned_lines)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove common newsletter footer patterns
        footer_patterns = [
            r'(unsubscribe|update preferences|manage preferences).*$',
            r'(sent to|you received this).*$',
            r'(view in browser|view online).*$',
            r'©\s*\d{4}.*$',
            r'all rights reserved.*$',
        ]
        
        for pattern in footer_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text.strip()
    
    def _extract_title(self, email: EmailMessage, text: str) -> str:
        """
        Extract or generate a title for the content.
        
        Args:
            email: Source email
            text: Extracted text content
            
        Returns:
            Title string
        """
        # Use subject line as base title
        title = email.subject
        
        # Clean up common prefixes
        prefixes_to_remove = [
            r'^(fwd?|re|fw):\s*',  # Forward/Reply prefixes
            r'^\[.+?\]\s*',  # [Newsletter] type prefixes
        ]
        
        for pattern in prefixes_to_remove:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        
        return title.strip() or "Untitled Newsletter"
    
    def clean(self, email: EmailMessage) -> Optional[CleanedContent]:
        """
        Extract and clean content from a newsletter email.
        
        Args:
            email: The email to extract content from
            
        Returns:
            CleanedContent object or None if extraction fails
        """
        # Prefer HTML content, fall back to plain text
        if email.body_html:
            text = self._extract_with_trafilatura(email.body_html)
            
            if not text or len(text) < 50:
                # Fallback if Trafilatura fails or returns too little
                text = self._fallback_extraction(email.body_html)
        else:
            text = email.body_text
        
        if not text:
            return None
        
        # Clean the extracted text
        cleaned_text = self._clean_text(text)
        
        if not cleaned_text or len(cleaned_text) < 50:
            return None
        
        # Calculate word count
        word_count = len(cleaned_text.split())
        
        return CleanedContent(
            title=self._extract_title(email, cleaned_text),
            text=cleaned_text,
            word_count=word_count,
            source_email_id=email.id,
            source_subject=email.subject,
            source_sender=f"{email.sender} <{email.sender_email}>",
            source_date=email.date.isoformat() if email.date else ""
        )
    
    def clean_batch(
        self, 
        emails: list[EmailMessage]
    ) -> list[CleanedContent]:
        """
        Clean multiple emails in batch.
        
        Args:
            emails: List of emails to clean
            
        Returns:
            List of successfully cleaned content
        """
        cleaned = []
        
        for email in emails:
            result = self.clean(email)
            if result:
                cleaned.append(result)
        
        return cleaned


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("Content Cleaner Test")
    print("=" * 50)
    
    # Test with sample HTML
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>.header { color: blue; }</style>
    </head>
    <body>
        <div class="header">
            <h1>The Weekly Tech Digest</h1>
        </div>
        <div class="content">
            <h2>AI News This Week</h2>
            <p>This week saw major developments in artificial intelligence.
            OpenAI announced new capabilities for their models, while
            Google unveiled updates to Gemini.</p>
            
            <h2>Industry Updates</h2>
            <p>The tech industry continues to evolve rapidly. Companies
            are investing heavily in AI infrastructure and talent.</p>
            
            <p>Here are the key takeaways:</p>
            <ul>
                <li>AI adoption is accelerating across industries</li>
                <li>New regulations are being proposed in the EU</li>
                <li>Startups are raising record amounts of funding</li>
            </ul>
        </div>
        <div class="footer">
            <p>Unsubscribe | View in browser</p>
            <p>© 2024 Tech Digest Inc. All rights reserved.</p>
        </div>
    </body>
    </html>
    """
    
    # Create mock email
    from datetime import datetime
    
    class MockEmail:
        def __init__(self):
            self.id = "test123"
            self.subject = "[Weekly] Tech Digest #42"
            self.sender = "Tech Digest"
            self.sender_email = "digest@techdigest.com"
            self.date = datetime.now()
            self.body_html = sample_html
            self.body_text = ""
    
    cleaner = ContentCleaner()
    result = cleaner.clean(MockEmail())
    
    if result:
        print(f"Title: {result.title}")
        print(f"Word Count: {result.word_count}")
        print(f"Source: {result.source_sender}")
        print()
        print("Extracted Text:")
        print("-" * 40)
        print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
    else:
        print("Failed to extract content")
