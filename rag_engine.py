"""
rag_engine.py - Retrieval-Augmented Generation Engine (IMPROVED)

Combines vector search with Gemini chat to answer questions
about newsletter content using relevant context.
"""

from dataclasses import dataclass
from typing import Optional

import google.generativeai as genai

import config
from embeddings import EmbeddingGenerator
from vector_store import VectorStore, SearchResult


# ============================================================================
# Configure Gemini
# ============================================================================

genai.configure(api_key=config.GEMINI_API_KEY)


# ============================================================================
# RAG Response Structure
# ============================================================================

@dataclass
class RAGResponse:
    """Response from the RAG engine."""
    answer: str
    sources: list[SearchResult]
    query: str
    context_used: str


# ============================================================================
# RAG Engine Class
# ============================================================================

class RAGEngine:
    """
    Retrieval-Augmented Generation engine for newsletter Q&A.
    
    Retrieves relevant context from the vector store and
    generates answers using Gemini.
    """
    
    def __init__(
        self,
        vector_store: VectorStore = None,
        model: str = None
    ):
        """
        Initialize the RAG engine.
        
        Args:
            vector_store: VectorStore instance (creates new if None)
            model: Gemini model for chat completions
        """
        self.vector_store = vector_store or VectorStore()
        self.embedder = EmbeddingGenerator()
        self.model = genai.GenerativeModel(model or config.CHAT_MODEL)
        
        # ================================================================
        # IMPROVED SYSTEM PROMPT - This is the key to better responses!
        # ================================================================
        self.system_prompt = """You are an intelligent newsletter analyst and research assistant. Your job is to help users extract valuable insights from their newsletter subscriptions.

## YOUR CAPABILITIES:
- Analyze and synthesize information from multiple newsletter sources
- Identify key trends, insights, and actionable takeaways
- Compare different perspectives on the same topic
- Provide accurate summaries with proper attribution

## RESPONSE GUIDELINES:

### Be Specific & Accurate
- Always cite which newsletter each piece of information comes from
- Include specific dates, numbers, names, and facts when available
- Quote directly when the original wording is particularly impactful

### Be Insightful
- Don't just repeat information - analyze and synthesize it
- Connect related ideas across different newsletters
- Highlight what's most important or actionable

### Be Honest
- If the newsletters don't contain relevant information, say so clearly
- Distinguish between facts stated in newsletters vs. your interpretations
- Acknowledge when information might be outdated or incomplete

### Format Well
- Use bullet points for multiple items
- Use **bold** for key terms and newsletter names
- Keep responses focused and scannable
- Start with the most important information

## CONTEXT FORMAT:
You'll receive newsletter excerpts in this format:
---
[Newsletter Title] - [Sender] - [Date]
[Content excerpt]
---

Use this context to provide accurate, well-sourced answers."""
    
    def _format_context(self, results: list[SearchResult]) -> str:
        """
        Format search results into context string.
        
        Args:
            results: Search results to format
            
        Returns:
            Formatted context string
        """
        if not results:
            return "No relevant newsletter content found."
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            # Format date nicely if available
            date = result.source_date[:10] if result.source_date else "Unknown date"
            
            # Clean up sender name (remove email if present)
            sender = result.source_sender
            if "<" in sender:
                sender = sender.split("<")[0].strip()
            
            context_parts.append(f"""---
**Source {i}: {result.source_title}**
From: {sender}
Date: {date}

{result.text}
---""")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, query: str, context: str) -> str:
        """
        Build the complete prompt for the chat model.
        
        Args:
            query: User's question
            context: Formatted context from newsletters
            
        Returns:
            Complete prompt string
        """
        return f"""{self.system_prompt}

=== NEWSLETTER CONTEXT ===

{context}

=== USER QUESTION ===

{query}

=== YOUR RESPONSE ===

Provide a helpful, accurate answer based on the newsletter content above. Remember to cite your sources."""
    
    def query(
        self,
        question: str,
        top_k: int = None,
        filter_sender: str = None
    ) -> RAGResponse:
        """
        Answer a question using RAG.
        
        Args:
            question: The user's question
            top_k: Number of context chunks to retrieve
            filter_sender: Optional sender filter
            
        Returns:
            RAGResponse with answer and sources
        """
        top_k = top_k or config.TOP_K_RESULTS
        
        # Generate query embedding
        query_embedding = self.embedder.generate_query_embedding(question)
        
        if not query_embedding:
            return RAGResponse(
                answer="I'm sorry, I encountered an error processing your question. Please try again.",
                sources=[],
                query=question,
                context_used=""
            )
        
        # Search for relevant content
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_sender=filter_sender
        )
        
        # Format context
        context = self._format_context(results)
        
        # Build and send prompt
        prompt = self._build_prompt(question, context)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=config.MAX_OUTPUT_TOKENS,
                    temperature=0.4,  # Lower = more focused & accurate
                    top_p=0.8,        # Nucleus sampling for better quality
                    top_k=40          # Limit token choices for consistency
                )
            )
            
            answer = response.text
        
        except Exception as e:
            answer = f"I encountered an error generating a response: {str(e)}"
        
        return RAGResponse(
            answer=answer,
            sources=results,
            query=question,
            context_used=context
        )
    
    def summarize_newsletter(self, email_id: str) -> str:
        """
        Generate a summary of a specific newsletter.
        
        Args:
            email_id: The email ID to summarize
            
        Returns:
            Summary text
        """
        # Get all chunks for this newsletter
        all_data = self.vector_store.collection.get(
            where={"source_email_id": email_id},
            include=["documents", "metadatas"]
        )
        
        if not all_data or not all_data['documents']:
            return "Newsletter not found in the database."
        
        # Combine all chunks
        full_text = "\n\n".join(all_data['documents'])
        title = all_data['metadatas'][0].get('source_title', 'Unknown')
        sender = all_data['metadatas'][0].get('source_sender', 'Unknown')
        
        prompt = f"""Analyze and summarize this newsletter in a clear, actionable format.

## Newsletter Details
**Title:** {title}
**From:** {sender}

## Content:
{full_text[:10000]}

## Your Summary Should Include:

1. **TL;DR** (2-3 sentences max)

2. **Key Points** (bullet points)

3. **Notable Quotes or Data** (if any)

4. **Action Items** (if any recommendations were made)

Keep the summary concise but comprehensive."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.3
                )
            )
            return response.text
        
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def find_related(self, text: str, top_k: int = 5) -> list[SearchResult]:
        """
        Find newsletters related to a given text.
        
        Args:
            text: Text to find related content for
            top_k: Number of results
            
        Returns:
            List of related search results
        """
        embedding = self.embedder.generate_query_embedding(text)
        
        if not embedding:
            return []
        
        return self.vector_store.search(
            query_embedding=embedding,
            top_k=top_k
        )
    
    def get_topics(self) -> list[str]:
        """
        Extract common topics from the newsletters.
        
        Returns:
            List of topic strings
        """
        # Get a sample of newsletters
        newsletters = self.vector_store.list_newsletters(limit=20)
        
        if not newsletters:
            return []
        
        titles = [n['title'] for n in newsletters]
        
        prompt = f"""Based on these newsletter titles, identify 5-7 main topics or themes:

{chr(10).join(titles)}

Provide a simple list of topics, one per line. Be specific and descriptive."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.3
                )
            )
            
            topics = [
                line.strip().lstrip('- •0123456789.').strip()
                for line in response.text.split('\n')
                if line.strip() and len(line.strip()) > 3
            ]
            
            return topics[:7]
        
        except Exception:
            return []
    
    def weekly_digest(self) -> str:
        """
        Generate a weekly digest of all newsletters.
        
        Returns:
            Digest text
        """
        newsletters = self.vector_store.list_newsletters(limit=15)
        
        if not newsletters:
            return "No newsletters found to summarize."
        
        # Get sample content from each
        summaries = []
        for nl in newsletters[:10]:
            all_data = self.vector_store.collection.get(
                where={"source_email_id": nl['email_id']},
                include=["documents"]
            )
            if all_data and all_data['documents']:
                text = all_data['documents'][0][:500]
                summaries.append(f"**{nl['title']}**: {text}")
        
        prompt = f"""Create a weekly digest from these newsletters. 

## Newsletters This Week:

{chr(10).join(summaries)}

## Create a Digest That Includes:

1. **This Week's Highlights** - Top 3-5 most interesting insights

2. **Trending Topics** - What themes appeared across multiple newsletters?

3. **Worth Your Time** - Which newsletter had the most valuable content?

4. **Quick Takes** - One-line summaries of other notable items

Keep it scannable and valuable."""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1000,
                    temperature=0.4
                )
            )
            return response.text
        
        except Exception as e:
            return f"Error generating digest: {str(e)}"


# ============================================================================
# Conversation Handler
# ============================================================================

class ConversationHandler:
    """
    Handles multi-turn conversations with context.
    """
    
    def __init__(self, rag_engine: RAGEngine):
        """
        Initialize the conversation handler.
        
        Args:
            rag_engine: RAGEngine instance
        """
        self.rag = rag_engine
        self.history: list[dict] = []
        self.max_history = 10
    
    def chat(self, message: str) -> RAGResponse:
        """
        Process a chat message with conversation history.
        
        Args:
            message: User's message
            
        Returns:
            RAGResponse
        """
        # Build context from conversation history
        if self.history:
            history_context = "Previous conversation:\n"
            for turn in self.history[-3:]:  # Last 3 turns
                history_context += f"User: {turn['user'][:150]}\n"
                history_context += f"Assistant: {turn['assistant'][:150]}\n"
            
            enhanced_query = f"{history_context}\nCurrent question: {message}"
        else:
            enhanced_query = message
        
        # Get response
        response = self.rag.query(enhanced_query)
        
        # Store in history
        self.history.append({
            "user": message,
            "assistant": response.answer
        })
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        return response
    
    def clear_history(self):
        """Clear conversation history."""
        self.history = []


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("RAG Engine Test")
    print("=" * 50)
    
    import tempfile
    from embeddings import TextChunk
    
    # Create temporary store with test data
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(persist_dir=tmpdir, collection_name="test")
        
        # Initialize engine
        engine = RAGEngine(vector_store=store)
        print("✓ RAG engine initialized")
        
        # Test conversation handler
        handler = ConversationHandler(engine)
        print("✓ Conversation handler initialized")
        
        # Test context formatting
        test_results = [
            SearchResult(
                chunk_id="test1",
                text="AI is revolutionizing how we work. Companies are adopting machine learning at unprecedented rates.",
                score=0.1,
                source_title="Tech Weekly",
                source_sender="tech@example.com",
                source_date="2024-01-15",
                source_email_id="email1"
            )
        ]
        
        context = engine._format_context(test_results)
        print("✓ Context formatting works")
        print(f"\nSample context:\n{context[:300]}...")
        
        print("\nAll tests passed!")
        print("\nNote: Full functionality requires GEMINI_API_KEY to be set.")
