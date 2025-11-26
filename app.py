"""
app.py - Newsletter RAG Web Interface (POLISHED DARK UI)

Clean, modern dark interface with:
- Dark mode as default
- Clean icons and typography
- Gmail links on newsletter titles
- Tabs with icons
- Polished neumorphic elements
"""

import streamlit as st
from datetime import datetime, timedelta
import time
import html

# Import our modules
import config
from gmail_client import GmailClient
from newsletter_detector import NewsletterDetector
from content_cleaner import ContentCleaner
from embeddings import EmbeddingPipeline
from vector_store import VectorStore
from rag_engine import RAGEngine, ConversationHandler


# ============================================================================
# Page Configuration
# ============================================================================

st.set_page_config(
    page_title="Newsletter RAG",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# Helper: Gmail URL Generator
# ============================================================================

def get_gmail_url(email_id: str) -> str:
    """Generate a Gmail URL to open a specific email."""
    return f"https://mail.google.com/mail/u/0/#all/{email_id}"


# ============================================================================
# CSS Styling - Polished Dark Theme
# ============================================================================

def load_css(dark_mode: bool = True):
    """Load custom CSS for polished dark design."""
    
    if dark_mode:
        theme = """
        :root {
            --bg-primary: #0f1419;
            --bg-secondary: #151b23;
            --bg-card: #1c242f;
            --bg-input: #0d1117;
            --border-color: #2a3441;
            --text-primary: #f0f6fc;
            --text-secondary: #8b949e;
            --text-muted: #6e7681;
            --accent: #2f81f7;
            --accent-hover: #388bfd;
            --accent-glow: rgba(47, 129, 247, 0.15);
            --success: #3fb950;
            --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            --card-shadow-hover: 0 8px 24px rgba(0, 0, 0, 0.5);
        }
        """
    else:
        theme = """
        :root {
            --bg-primary: #f6f8fa;
            --bg-secondary: #ffffff;
            --bg-card: #ffffff;
            --bg-input: #f6f8fa;
            --border-color: #d0d7de;
            --text-primary: #1f2328;
            --text-secondary: #656d76;
            --text-muted: #8b949e;
            --accent: #2f81f7;
            --accent-hover: #388bfd;
            --accent-glow: rgba(47, 129, 247, 0.1);
            --success: #1a7f37;
            --card-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            --card-shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.12);
        }
        """
    
    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    {theme}

    /* ========================================
       BASE STYLES
       ======================================== */
    .stApp {{
        background: var(--bg-primary);
    }}
    
    .main .block-container {{
        padding: 1.5rem 2rem;
        max-width: 1200px;
    }}
    
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* ========================================
       SIDEBAR
       ======================================== */
    [data-testid="stSidebar"] {{
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
    }}
    
    [data-testid="stSidebar"] .block-container {{
        padding: 1.5rem 1rem;
    }}
    
    .sidebar-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }}
    
    .sidebar-header svg {{
        color: var(--accent);
    }}
    
    .sidebar-header h3 {{
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0;
    }}
    
    .sidebar-section {{
        margin-bottom: 1.5rem;
    }}
    
    .sidebar-section-title {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.75rem;
    }}
    
    /* ========================================
       METRICS
       ======================================== */
    [data-testid="stMetric"] {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem;
    }}
    
    [data-testid="stMetric"] label {{
        color: var(--text-secondary) !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
    }}
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: var(--text-primary) !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
    }}

    /* ========================================
       BUTTONS
       ======================================== */
    .stButton > button {{
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.6rem 1rem !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s ease !important;
        box-shadow: var(--card-shadow) !important;
    }}
    
    .stButton > button:hover {{
        background: var(--bg-input) !important;
        border-color: var(--accent) !important;
        box-shadow: var(--card-shadow-hover) !important;
    }}
    
    /* Primary button (Sync) */
    .sync-button > button {{
        background: linear-gradient(135deg, var(--accent) 0%, #1a6dd4 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
    }}
    
    .sync-button > button:hover {{
        background: linear-gradient(135deg, var(--accent-hover) 0%, #2179e0 100%) !important;
        transform: translateY(-1px);
    }}

    /* ========================================
       INPUTS
       ======================================== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div {{
        background: var(--bg-input) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.875rem !important;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px var(--accent-glow) !important;
    }}
    
    .stTextInput > div > div > input::placeholder {{
        color: var(--text-muted) !important;
    }}

    /* ========================================
       SLIDER
       ======================================== */
    .stSlider > div > div > div {{
        background: var(--border-color) !important;
    }}
    
    .stSlider [data-baseweb="slider"] div {{
        background: var(--accent) !important;
    }}
    
    .stSlider [data-testid="stTickBar"] {{
        background: var(--accent) !important;
    }}

    /* ========================================
       HEADER
       ======================================== */
    .main-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }}
    
    .main-header-left {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .main-header-logo {{
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, var(--accent) 0%, #6366f1 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }}
    
    .main-header h1 {{
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }}
    
    .theme-toggle {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.5rem;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 1.2rem;
        line-height: 1;
    }}
    
    .theme-toggle:hover {{
        background: var(--bg-input);
        border-color: var(--accent);
    }}

    /* ========================================
       TABS
       ======================================== */
    .stTabs {{
        background: transparent;
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 6px;
        gap: 4px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background: transparent;
        color: var(--text-secondary);
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.875rem;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background: var(--bg-input);
        color: var(--text-primary);
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--accent) !important;
        color: white !important;
    }}
    
    .stTabs [data-baseweb="tab-border"] {{
        display: none;
    }}
    
    .stTabs [data-baseweb="tab-highlight"] {{
        display: none;
    }}
    
    .tab-description {{
        color: var(--text-secondary);
        font-size: 0.875rem;
        margin: 1rem 0 1.5rem 0;
    }}

    /* ========================================
       WELCOME SECTION
       ======================================== */
    .welcome-section {{
        text-align: center;
        padding: 4rem 2rem;
    }}
    
    .welcome-icon {{
        width: 80px;
        height: 80px;
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 1.5rem auto;
        font-size: 2rem;
    }}
    
    .welcome-section h2 {{
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }}
    
    .welcome-section p {{
        color: var(--text-secondary);
        font-size: 0.95rem;
    }}

    /* ========================================
       SUGGESTION BUTTONS
       ======================================== */
    .suggestion-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 2rem;
        max-width: 800px;
        margin-left: auto;
        margin-right: auto;
    }}
    
    .suggestion-btn {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.2s;
        text-align: left;
    }}
    
    .suggestion-btn:hover {{
        border-color: var(--accent);
        background: var(--bg-input);
        box-shadow: var(--card-shadow);
    }}
    
    .suggestion-icon {{
        width: 32px;
        height: 32px;
        background: var(--accent-glow);
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--accent);
        font-size: 0.9rem;
    }}
    
    .suggestion-text {{
        color: var(--text-primary);
        font-size: 0.875rem;
        font-weight: 500;
    }}

    /* ========================================
       CHAT MESSAGES
       ======================================== */
    .chat-container {{
        max-width: 800px;
        margin: 0 auto;
    }}
    
    .chat-message {{
        padding: 1rem 1.25rem;
        margin: 0.75rem 0;
        border-radius: 12px;
        font-size: 0.9rem;
        line-height: 1.6;
    }}
    
    .user-message {{
        background: var(--accent);
        color: white;
        margin-left: 3rem;
        border-bottom-right-radius: 4px;
    }}
    
    .assistant-message {{
        background: var(--bg-card);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        margin-right: 3rem;
        border-bottom-left-radius: 4px;
    }}

    /* ========================================
       NEWSLETTER CARDS
       ======================================== */
    .newsletter-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        transition: all 0.2s;
    }}
    
    .newsletter-card:hover {{
        border-color: var(--accent);
        box-shadow: var(--card-shadow);
    }}
    
    .newsletter-card a {{
        color: var(--text-primary);
        text-decoration: none;
        font-size: 0.85rem;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    
    .newsletter-card a:hover {{
        color: var(--accent);
    }}
    
    .newsletter-card .meta {{
        color: var(--text-muted);
        font-size: 0.75rem;
        margin-top: 4px;
    }}
    
    .link-icon {{
        opacity: 0.5;
        font-size: 0.7rem;
    }}

    /* ========================================
       STAT CARDS
       ======================================== */
    .stat-card {{
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
    }}
    
    .stat-card h2 {{
        color: var(--accent);
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }}
    
    .stat-card p {{
        color: var(--text-secondary);
        font-size: 0.85rem;
        margin: 0.25rem 0 0 0;
    }}

    /* ========================================
       EXPANDER
       ======================================== */
    .streamlit-expanderHeader {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }}
    
    .streamlit-expanderContent {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 10px 10px !important;
    }}

    /* ========================================
       ALERTS
       ======================================== */
    .stAlert {{
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
    }}

    /* ========================================
       HIDE DEFAULTS
       ======================================== */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px;
        height: 8px;
    }}
    ::-webkit-scrollbar-track {{
        background: var(--bg-primary);
    }}
    ::-webkit-scrollbar-thumb {{
        background: var(--border-color);
        border-radius: 4px;
    }}
    ::-webkit-scrollbar-thumb:hover {{
        background: var(--text-muted);
    }}

    /* Fix sidebar text colors */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {{
        color: var(--text-primary) !important;
    }}
    
    [data-testid="stSidebar"] .stMarkdown p {{
        color: var(--text-secondary) !important;
    }}
</style>
    """, unsafe_allow_html=True)


# ============================================================================
# Session State
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    defaults = {
        'messages': [],
        'gmail_authenticated': False,
        'vector_store': None,
        'rag_engine': None,
        'conversation': None,
        'dark_mode': True,  # Dark mode by default
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    if st.session_state.vector_store is None:
        st.session_state.vector_store = VectorStore()
    
    if st.session_state.rag_engine is None:
        st.session_state.rag_engine = RAGEngine(
            vector_store=st.session_state.vector_store
        )
    
    if st.session_state.conversation is None:
        st.session_state.conversation = ConversationHandler(
            st.session_state.rag_engine
        )


# ============================================================================
# Gmail Integration
# ============================================================================

def sync_newsletters(days: int = 30):
    """Fetch and process newsletters from Gmail."""
    progress = st.progress(0)
    status = st.empty()
    
    try:
        status.text("🔐 Connecting to Gmail...")
        client = GmailClient()
        client.authenticate()
        st.session_state.gmail_authenticated = True
        progress.progress(20)
        
        status.text("📥 Fetching emails...")
        emails = client.fetch_recent_emails(days=days)
        progress.progress(40)
        
        status.text("🔍 Detecting newsletters...")
        detector = NewsletterDetector()
        newsletters = detector.filter_newsletters(emails)
        progress.progress(60)
        
        if not newsletters:
            status.text("No newsletters found.")
            progress.empty()
            return 0
        
        status.text("🧹 Extracting content...")
        cleaner = ContentCleaner()
        cleaned = cleaner.clean_batch([n[0] for n in newsletters])
        progress.progress(75)
        
        status.text("🧠 Processing with AI...")
        pipeline = EmbeddingPipeline()
        chunks = pipeline.process(cleaned, show_progress=False)
        progress.progress(90)
        
        status.text("💾 Saving...")
        added = st.session_state.vector_store.add_chunks(chunks)
        progress.progress(100)
        
        status.text(f"✅ Synced {len(newsletters)} newsletters!")
        time.sleep(1)
        progress.empty()
        status.empty()
        
        return len(newsletters)
    
    except Exception as e:
        status.error(f"❌ {str(e)}")
        progress.empty()
        return 0


# ============================================================================
# Features
# ============================================================================

def export_chat_markdown():
    """Export chat history to markdown."""
    if not st.session_state.messages:
        return None
    
    md = "# Newsletter RAG Chat Export\n\n"
    md += f"*Exported on {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n---\n\n"
    
    for msg in st.session_state.messages:
        icon = "🧑" if msg['role'] == 'user' else "🤖"
        md += f"**{icon} {'You' if msg['role'] == 'user' else 'Assistant'}:**\n{msg['content']}\n\n---\n\n"
    
    return md


def generate_weekly_digest():
    """Generate a weekly digest."""
    with st.spinner("Generating digest..."):
        try:
            return st.session_state.rag_engine.weekly_digest()
        except Exception as e:
            return f"Error: {str(e)}"


def get_analytics():
    """Get newsletter analytics."""
    stats = st.session_state.vector_store.get_stats()
    newsletters = st.session_state.vector_store.list_newsletters(limit=100)
    
    sender_counts = {}
    for nl in newsletters:
        sender = nl.get('sender', 'Unknown')
        if '<' in sender:
            sender = sender.split('<')[0].strip()
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    
    top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total_newsletters': stats['unique_newsletters'],
        'total_chunks': stats['total_chunks'],
        'unique_senders': stats['unique_senders'],
        'top_senders': top_senders,
        'newsletters': newsletters
    }


# ============================================================================
# UI Components
# ============================================================================

def render_header():
    """Render main header."""
    col1, col2 = st.columns([6, 1])
    
    with col1:
        st.markdown("""
            <div class="main-header-left">
                <div class="main-header-logo">📊</div>
                <h1 style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary); margin: 0;">
                    Newsletter RAG
                </h1>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        icon = "☀️" if st.session_state.dark_mode else "🌙"
        if st.button(icon, key="theme_toggle", help="Toggle theme"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()


def render_chat_message(role: str, content: str):
    """Render a chat message."""
    safe_content = html.escape(content)
    css_class = "user-message" if role == "user" else "assistant-message"
    
    st.markdown(f'<div class="chat-message {css_class}">{safe_content}</div>', unsafe_allow_html=True)


def render_newsletter_card(newsletter: dict):
    """Render a newsletter card with Gmail link."""
    date = newsletter.get('date', '')[:10] if newsletter.get('date') else ''
    title = html.escape(newsletter.get('title', 'Untitled'))
    email_id = newsletter.get('email_id', '')
    
    sender = newsletter.get('sender', 'Unknown')
    if '<' in sender:
        sender = sender.split('<')[0].strip()
    sender = html.escape(sender)
    
    gmail_url = get_gmail_url(email_id) if email_id else "#"
    display_title = title[:35] + '...' if len(title) > 35 else title
    
    st.markdown(f"""
        <div class="newsletter-card">
            <a href="{gmail_url}" target="_blank">
                {display_title} <span class="link-icon">↗</span>
            </a>
            <div class="meta">{sender} • {date}</div>
        </div>
    """, unsafe_allow_html=True)


def render_stat_card(value, label):
    """Render a statistic card."""
    st.markdown(f"""
        <div class="stat-card">
            <h2>{value}</h2>
            <p>{label}</p>
        </div>
    """, unsafe_allow_html=True)


# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Render sidebar."""
    with st.sidebar:
        # Library header
        st.markdown("""
            <div class="sidebar-header">
                <span style="font-size: 1.2rem;">📚</span>
                <h3>Library</h3>
            </div>
        """, unsafe_allow_html=True)
        
        # Stats
        stats = st.session_state.vector_store.get_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Newsletters", stats['unique_newsletters'])
        with col2:
            st.metric("Chunks", stats['total_chunks'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Sync section
        st.markdown("""
            <div class="sidebar-section-title">
                <span>🔄</span> Sync
            </div>
        """, unsafe_allow_html=True)
        
        days = st.slider("Days", 7, 90, 30, 7, label_visibility="collapsed")
        st.markdown(f"<p style='font-size: 0.75rem; color: var(--text-muted);'>Days: {days}</p>", unsafe_allow_html=True)
        
        # Styled sync button
        st.markdown('<div class="sync-button">', unsafe_allow_html=True)
        if st.button("Sync from Gmail", use_container_width=True):
            count = sync_newsletters(days=days)
            if count > 0:
                st.success(f"Added {count} newsletters!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Filters
        st.markdown("""
            <div class="sidebar-section-title">
                <span>🔍</span> Filters
            </div>
        """, unsafe_allow_html=True)
        
        newsletters = st.session_state.vector_store.list_newsletters(limit=50)
        senders = list(set([
            nl.get('sender', '').split('<')[0].strip() 
            for nl in newsletters if nl.get('sender')
        ]))
        
        if senders:
            st.selectbox("Filter by sender", ["All Senders"] + sorted(senders)[:10], label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Recent newsletters
        st.markdown("""
            <div class="sidebar-section-title">
                <span>📰</span> Recent
            </div>
        """, unsafe_allow_html=True)
        
        if newsletters:
            for nl in newsletters[:4]:
                render_newsletter_card(nl)
        else:
            st.info("No newsletters yet")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Settings
        with st.expander("⚙️ Settings"):
            if st.button("Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.session_state.conversation.clear_history()
                st.rerun()
            
            if st.button("Clear All Data", use_container_width=True):
                if st.session_state.vector_store.clear():
                    st.session_state.messages = []
                    st.rerun()


# ============================================================================
# Main Tabs
# ============================================================================

def render_chat_tab():
    """Render chat interface."""
    stats = st.session_state.vector_store.get_stats()
    
    st.markdown('<p class="tab-description">Chat with your newsletter knowledge base</p>', unsafe_allow_html=True)
    
    if stats['total_chunks'] == 0:
        st.markdown("""
            <div class="welcome-section">
                <div class="welcome-icon">✨</div>
                <h2>Ready to chat with your inbox</h2>
                <p>Sync your newsletters to get started. Ask about trends, summaries, or specific details.</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Show newsletter count in welcome
    if not st.session_state.messages:
        st.markdown(f"""
            <div class="welcome-section">
                <div class="welcome-icon">✨</div>
                <h2>Ready to chat with your inbox</h2>
                <p>I've indexed {stats['unique_newsletters']} newsletters. Ask me about trends, summaries, or specific details.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Suggestion buttons
        suggestions = [
            ("👤", "What were the main topics this week?"),
            ("👤", "Summarize the latest trends in Tech."),
            ("👤", "Did anyone mention React updates?"),
            ("👤", "Give me a bullet point list of finance news."),
        ]
        
        cols = st.columns(2)
        for i, (icon, text) in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(text, key=f"sug_{i}", use_container_width=True):
                    st.session_state.pending_question = text
                    st.rerun()
    else:
        # Chat messages
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for msg in st.session_state.messages:
            render_chat_message(msg["role"], msg["content"])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Ask about your newsletters..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Thinking..."):
            response = st.session_state.conversation.chat(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": response.answer})
        
        if response.sources:
            with st.expander("📚 Sources"):
                for source in response.sources:
                    email_id = source.source_email_id
                    gmail_url = get_gmail_url(email_id)
                    title = html.escape(source.source_title)
                    st.markdown(f"[{title}]({gmail_url}) ↗")
        
        st.rerun()
    
    # Handle pending question
    if hasattr(st.session_state, 'pending_question') and st.session_state.pending_question:
        prompt = st.session_state.pending_question
        st.session_state.pending_question = None
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.spinner("Thinking..."):
            response = st.session_state.conversation.chat(prompt)
        
        st.session_state.messages.append({"role": "assistant", "content": response.answer})
        st.rerun()


def render_digest_tab():
    """Render digest tab."""
    st.markdown('<p class="tab-description">Generate AI summaries of your newsletters</p>', unsafe_allow_html=True)
    
    if st.button("🔄 Generate Weekly Digest", use_container_width=False):
        digest = generate_weekly_digest()
        st.markdown(digest)
    
    st.markdown("---")
    
    st.markdown("### 📤 Export")
    if st.session_state.messages:
        md = export_chat_markdown()
        st.download_button(
            "📥 Download Chat History",
            md,
            file_name=f"newsletter_chat_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
    else:
        st.info("Start a chat to export history.")


def render_analytics_tab():
    """Render analytics tab."""
    st.markdown('<p class="tab-description">Insights and statistics about your newsletters</p>', unsafe_allow_html=True)
    
    analytics = get_analytics()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        render_stat_card(analytics['total_newsletters'], "Newsletters")
    with col2:
        render_stat_card(analytics['total_chunks'], "Text Chunks")
    with col3:
        render_stat_card(analytics['unique_senders'], "Senders")
    
    st.markdown("---")
    
    st.markdown("### 👥 Top Senders")
    if analytics['top_senders']:
        for sender, count in analytics['top_senders']:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{html.escape(sender[:30])}**")
            with col2:
                st.markdown(f"`{count}`")
    
    st.markdown("---")
    
    st.markdown("### 📰 All Newsletters")
    if analytics['newsletters']:
        for nl in analytics['newsletters'][:15]:
            render_newsletter_card(nl)


# ============================================================================
# Main
# ============================================================================

def main():
    """Main application."""
    init_session_state()
    load_css(st.session_state.dark_mode)
    
    render_sidebar()
    render_header()
    
    # Tabs with icons
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📋 Digest", "📊 Analytics"])
    
    with tab1:
        render_chat_tab()
    with tab2:
        render_digest_tab()
    with tab3:
        render_analytics_tab()


if __name__ == "__main__":
    main()
