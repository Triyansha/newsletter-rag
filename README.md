# 📬 Newsletter RAG

A personal newsletter aggregator with AI-powered search and chat. Connect your Gmail, sync your newsletters, and have intelligent conversations with your curated knowledge base.

![Skeuomorphic UI](https://img.shields.io/badge/UI-Skeuomorphic-8B4513?style=for-the-badge)
![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)

## ✨ Features

- **Gmail Integration**: Secure OAuth 2.0 connection to fetch newsletters
- **Smart Detection**: Automatic identification of newsletter emails
- **Content Extraction**: Clean text extraction from HTML emails
- **Semantic Search**: Vector embeddings for intelligent content retrieval
- **AI Chat**: Ask questions about your newsletters using RAG
- **Beautiful UI**: Skeuomorphic leather notebook design

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11+ |
| Email API | Gmail API (google-api-python-client) |
| HTML Cleaning | Trafilatura |
| Vector Database | ChromaDB |
| AI Provider | Google Gemini |
| Frontend | Streamlit |

## 📁 Project Structure

```
newsletter-rag/
├── config.py              # Environment and API configuration
├── gmail_client.py        # OAuth flow and email fetching
├── newsletter_detector.py # Newsletter identification logic
├── content_cleaner.py     # HTML extraction with Trafilatura
├── embeddings.py          # Text chunking and Gemini embeddings
├── vector_store.py        # ChromaDB operations
├── rag_engine.py          # RAG query pipeline
├── app.py                 # Streamlit web interface
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

## 🚀 Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone <repo-url>
cd newsletter-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required:**
- `GEMINI_API_KEY`: Get from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Setup Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable the Gmail API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download `credentials.json` to the project root

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage

### Syncing Newsletters

1. Click "Sync from Gmail" in the sidebar
2. Complete the OAuth flow (first time only)
3. Wait for newsletters to be processed

### Chatting with Newsletters

Ask questions like:
- "What were the main topics in my newsletters this week?"
- "Summarize the latest newsletter about AI"
- "What did my newsletters say about technology trends?"
- "Find newsletters mentioning machine learning"

## ⚙️ Configuration

All settings can be customized in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `CHUNK_SIZE` | Characters per text chunk | 1000 |
| `CHUNK_OVERLAP` | Overlap between chunks | 200 |
| `TOP_K_RESULTS` | Context chunks to retrieve | 5 |
| `DAYS_TO_FETCH` | Days of emails to sync | 30 |
| `MAX_EMAILS_PER_FETCH` | Max emails per sync | 100 |

## 🎨 UI Design

The interface features a skeuomorphic design inspired by leather notebooks:

- **Leather header** with embossed gold text
- **Parchment paper** texture for content
- **Tactile buttons** with realistic shadows
- **Handcrafted** typography using Crimson Pro

## 🔒 Privacy

- All data stays local on your machine
- Gmail access is read-only
- OAuth tokens are stored locally
- No data sent to third parties (except Gemini API)

## 📝 License

MIT License - Feel free to use, modify, and share!

---

Built with ❤️ using [Streamlit](https://streamlit.io), [ChromaDB](https://www.trychroma.com), and [Google Gemini](https://deepmind.google/technologies/gemini/)
