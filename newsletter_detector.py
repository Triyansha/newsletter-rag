"""
newsletter_detector.py - Smart Newsletter Detection & Filtering

Detects newsletters from emails AND filters out:
- Promotional/marketing emails
- Sales and discount offers
- Transactional emails (receipts, shipping)
- Auto-generated notifications
- Social media digests

Only keeps high-quality content worth reading.
"""

import re
from dataclasses import dataclass
from typing import Optional

from gmail_client import EmailMessage


# ============================================================================
# Detection Result
# ============================================================================

@dataclass
class DetectionResult:
    """Result of newsletter detection."""
    is_newsletter: bool
    is_promotional: bool
    is_worth_reading: bool
    newsletter_confidence: float
    promotional_score: float
    quality_score: float
    reasons: list[str]


# ============================================================================
# Newsletter Detector with Quality Filter
# ============================================================================

class NewsletterDetector:
    """
    Detects newsletters and filters out promotional content.
    """
    
    def __init__(
        self,
        newsletter_threshold: float = 0.4,
        promotional_threshold: float = 0.5,
        quality_threshold: float = 0.3
    ):
        self.newsletter_threshold = newsletter_threshold
        self.promotional_threshold = promotional_threshold
        self.quality_threshold = quality_threshold
        
        # Newsletter detection patterns
        self.newsletter_domains = {
            'substack.com', 'beehiiv.com', 'mailchimp.com', 
            'convertkit.com', 'buttondown.email', 'revue.co',
            'ghost.io', 'campaignmonitor.com', 'mailerlite.com',
            'sendinblue.com', 'getrevue.co', 'emailoctopus.com',
            'benchmarkemail.com', 'moosend.com', 'drip.com',
            'klaviyo.com', 'constantcontact.com', 'hubspot.com',
            'medium.com', 'linkedin.com', 'morningbrew.com',
            'axios.com', 'thenewsette.com', 'thehustle.co'
        }
        
        self.newsletter_sender_patterns = [
            r'newsletter', r'digest', r'weekly', r'daily',
            r'updates?', r'bulletin', r'dispatch', r'brief',
            r'roundup', r'recap', r'summary', r'edition',
            r'insider', r'report', r'review', r'bytes'
        ]
        
        self.newsletter_subject_patterns = [
            r'issue\s*#?\d+', r'edition\s*#?\d+', r'vol\.?\s*\d+',
            r'#\d+\s*[-:—]', r'weekly', r'daily', r'monthly',
            r'digest', r'roundup', r'newsletter', r'this\s+week',
            r'top\s+\d+', r'best\s+of', r'highlights'
        ]
        
        # Promotional patterns (to filter out)
        self.promotional_subject_patterns = [
            r'\d+%\s*off', r'save\s+\$?\d+', r'discount', r'sale\b',
            r'deal\b', r'offer\b', r'promo\b', r'coupon', r'voucher',
            r'limited\s+time', r'expires?\b', r'ends\s+(today|soon|tonight)',
            r'last\s+chance', r'final\s+(hours?|days?)', r'hurry',
            r'don\'?t\s+miss', r'act\s+(now|fast)', r'today\s+only',
            r'flash\s+sale', r'clearance', r'free\s+shipping',
            r'exclusive\s+(offer|deal|access)', r'special\s+(offer|deal|price)',
            r'order\s+(confirmed?|shipped|delivered)',
            r'shipping\s+(update|confirmation)', r'tracking',
            r'your\s+(order|package|delivery)', r'invoice',
            r'receipt', r'payment\s+(received|confirmed)',
            r'verify\s+(your|email)', r'confirm\s+(your|email)',
            r'password\s+(reset|changed)', r'account\s+(update|alert)',
            r'security\s+(alert|notice)', r'login\s+(alert|notification)',
            r'(new\s+)?(follower|like|comment|mention|reply)',
            r'tagged\s+you', r'connection\s+request', r'friend\s+request',
            r'reminder:', r'meeting\s+(invite|reminder|update)',
            r'survey', r'feedback', r'review\s+us', r'rate\s+us',
            r'we\s+miss\s+you', r'come\s+back', r'abandoned\s+cart',
        ]
        
        self.promotional_content_patterns = [
            r'shop\s+now', r'buy\s+now', r'order\s+now',
            r'click\s+here', r'sign\s+up\s+now',
            r'\$\d+(\.\d{2})?', r'£\d+', r'€\d+',
            r'limited\s+(time|stock|availability)',
            r'while\s+supplies\s+last', r'selling\s+fast',
        ]
        
        self.promotional_senders = {
            'noreply', 'no-reply', 'donotreply', 'do-not-reply',
            'notifications', 'notification', 'alerts', 'alert',
            'mailer', 'marketing', 'promo', 'promotions',
            'deals', 'offers', 'sales', 'store', 'shop',
            'orders', 'order', 'shipping', 'delivery',
            'support', 'help', 'info', 'billing', 'invoice',
        }
        
        # Quality indicators
        self.quality_subject_patterns = [
            r'analysis', r'insights?', r'deep\s+dive', r'breakdown',
            r'explained', r'how\s+to', r'why\b', r'guide\s+to',
            r'lessons?\s+(from|learned)', r'takeaways?',
            r'industry', r'market', r'trends?', r'forecast',
            r'report\b', r'research', r'study', r'findings',
            r'startup', r'venture', r'funding', r'investment',
            r'technology', r'innovation', r'future\s+of',
            r'opinion', r'perspective', r'essay', r'commentary',
            r'interview', r'conversation\s+with',
            r'reading\s+list', r'must\s+read', r'curated',
        ]
        
        # Blacklisted domains
        self.blacklisted_domains = {
            'amazon.com', 'ebay.com', 'walmart.com', 'target.com',
            'doordash.com', 'ubereats.com', 'grubhub.com',
            'booking.com', 'expedia.com', 'airbnb.com',
            'uber.com', 'lyft.com',
            'facebookmail.com', 'twitter.com', 'x.com',
            'instagram.com', 'tiktok.com', 'pinterest.com',
            'netflix.com', 'spotify.com', 'youtube.com',
            'paypal.com', 'venmo.com', 'cashapp.com',
        }
        
        self.whitelisted_domains = {
            'substack.com', 'beehiiv.com', 'buttondown.email',
            'ghost.io', 'morningbrew.com', 'axios.com', 'thehustle.co',
        }

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address."""
        if not email:
            return ''
        if '@' in str(email):
            return str(email).split('@')[-1].lower().strip('>')
        return ''
    
    def _extract_sender_name(self, sender: str) -> str:
        """Extract name from sender field."""
        if not sender:
            return ''
        sender = str(sender)
        if '<' in sender:
            return sender.split('<')[0].strip().lower()
        return sender.lower()
    
    def _check_patterns(self, text: str, patterns: list) -> tuple[bool, list]:
        """Check if text matches any patterns."""
        if not text:
            return False, []
        
        text_lower = str(text).lower()
        matches = []
        
        for pattern in patterns:
            try:
                if re.search(pattern, text_lower):
                    matches.append(pattern)
            except Exception:
                continue
        
        return len(matches) > 0, matches
    
    def _has_unsubscribe_header(self, email: EmailMessage) -> bool:
        """Safely check for List-Unsubscribe header."""
        try:
            headers = getattr(email, 'headers', None)
            
            if not headers:
                return False
            
            # Handle list of dicts
            if isinstance(headers, list):
                for h in headers:
                    if isinstance(h, dict):
                        name = h.get('name', '') or ''
                        if str(name).lower() == 'list-unsubscribe':
                            return True
                    elif isinstance(h, str):
                        if 'list-unsubscribe' in str(h).lower():
                            return True
            
            # Handle dict
            elif isinstance(headers, dict):
                for key in headers:
                    if str(key).lower() == 'list-unsubscribe':
                        return True
            
            # Handle string
            elif isinstance(headers, str):
                if 'list-unsubscribe' in headers.lower():
                    return True
            
            return False
        except Exception:
            return False
    
    def _calculate_newsletter_score(self, email: EmailMessage) -> tuple[float, list]:
        """Calculate newsletter confidence score."""
        score = 0.0
        reasons = []
        
        try:
            sender_email = str(getattr(email, 'sender_email', '') or '').lower()
            sender_name = self._extract_sender_name(getattr(email, 'sender', '') or '')
            domain = self._extract_domain(sender_email)
            subject = str(getattr(email, 'subject', '') or '')
            
            # Check unsubscribe header
            if self._has_unsubscribe_header(email):
                score += 0.35
                reasons.append("Has unsubscribe header")
            
            # Check newsletter domains
            if domain in self.newsletter_domains:
                score += 0.35
                reasons.append(f"Newsletter platform: {domain}")
            
            # Check sender patterns
            matched, _ = self._check_patterns(sender_name, self.newsletter_sender_patterns)
            if matched:
                score += 0.2
                reasons.append("Newsletter sender pattern")
            
            # Check subject patterns
            matched, _ = self._check_patterns(subject, self.newsletter_subject_patterns)
            if matched:
                score += 0.25
                reasons.append("Newsletter subject pattern")
        
        except Exception:
            pass
        
        return min(score, 1.0), reasons
    
    def _calculate_promotional_score(self, email: EmailMessage) -> tuple[float, list]:
        """Calculate promotional score (higher = more promotional)."""
        score = 0.0
        reasons = []
        
        try:
            sender_email = str(getattr(email, 'sender_email', '') or '').lower()
            domain = self._extract_domain(sender_email)
            subject = str(getattr(email, 'subject', '') or '')
            body = str(getattr(email, 'body_text', '') or '')[:2000]
            
            # Blacklisted domain = instant filter
            if domain in self.blacklisted_domains:
                return 1.0, ["Blacklisted sender domain"]
            
            # Check promotional sender
            sender_parts = re.split(r'[@.\-_]', sender_email)
            for part in sender_parts:
                if part in self.promotional_senders:
                    score += 0.3
                    reasons.append(f"Promotional sender: {part}")
                    break
            
            # Check promotional subject
            matched, patterns = self._check_patterns(subject, self.promotional_subject_patterns)
            if matched:
                score += 0.15 * min(len(patterns), 3)
                reasons.append(f"Promotional subject ({len(patterns)} patterns)")
            
            # Check promotional content
            matched, patterns = self._check_patterns(body, self.promotional_content_patterns)
            if matched:
                score += 0.1 * min(len(patterns), 4)
                reasons.append(f"Promotional content")
            
            # Check for price/discount in subject
            if re.search(r'\$\d+|%\s*off|\bsale\b|\bdeal\b', subject.lower()):
                score += 0.25
                reasons.append("Price/discount in subject")
        
        except Exception:
            pass
        
        return min(score, 1.0), reasons
    
    def _calculate_quality_score(self, email: EmailMessage) -> tuple[float, list]:
        """Calculate content quality score."""
        score = 0.0
        reasons = []
        
        try:
            sender_email = str(getattr(email, 'sender_email', '') or '').lower()
            domain = self._extract_domain(sender_email)
            subject = str(getattr(email, 'subject', '') or '')
            body = str(getattr(email, 'body_text', '') or '')[:3000]
            
            # Whitelisted domain
            if domain in self.whitelisted_domains:
                score += 0.4
                reasons.append("Quality newsletter platform")
            
            # Check quality subject patterns
            matched, patterns = self._check_patterns(subject, self.quality_subject_patterns)
            if matched:
                score += 0.15 * min(len(patterns), 2)
                reasons.append(f"Quality subject")
            
            # Content length
            word_count = len(body.split())
            if word_count > 500:
                score += 0.15
                reasons.append("Substantial content")
            elif word_count > 200:
                score += 0.1
                reasons.append("Decent content length")
            elif word_count < 100:
                score -= 0.2
        
        except Exception:
            pass
        
        return max(min(score, 1.0), 0.0), reasons
    
    def detect(self, email: EmailMessage) -> DetectionResult:
        """Analyze an email and determine if it's worth reading."""
        try:
            newsletter_score, nl_reasons = self._calculate_newsletter_score(email)
            promo_score, promo_reasons = self._calculate_promotional_score(email)
            quality_score, quality_reasons = self._calculate_quality_score(email)
            
            is_newsletter = newsletter_score >= self.newsletter_threshold
            is_promotional = promo_score >= self.promotional_threshold
            is_worth_reading = is_newsletter and not is_promotional and quality_score >= self.quality_threshold
            
            all_reasons = nl_reasons + promo_reasons + quality_reasons
            
            return DetectionResult(
                is_newsletter=is_newsletter,
                is_promotional=is_promotional,
                is_worth_reading=is_worth_reading,
                newsletter_confidence=newsletter_score,
                promotional_score=promo_score,
                quality_score=quality_score,
                reasons=all_reasons
            )
        except Exception as e:
            return DetectionResult(
                is_newsletter=False,
                is_promotional=True,
                is_worth_reading=False,
                newsletter_confidence=0.0,
                promotional_score=1.0,
                quality_score=0.0,
                reasons=[f"Error: {str(e)}"]
            )
    
    def filter_newsletters(
        self,
        emails: list[EmailMessage],
        quality_only: bool = True
    ) -> list[tuple[EmailMessage, DetectionResult]]:
        """Filter emails to only quality newsletters."""
        results = []
        
        for email in emails:
            try:
                result = self.detect(email)
                
                if quality_only:
                    if result.is_worth_reading:
                        results.append((email, result))
                else:
                    if result.is_newsletter:
                        results.append((email, result))
            except Exception:
                continue
        
        results.sort(key=lambda x: x[1].quality_score, reverse=True)
        return results


if __name__ == "__main__":
    print("Newsletter Detector initialized successfully")
