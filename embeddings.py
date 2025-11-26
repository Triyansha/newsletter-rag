"""
embeddings.py - Text Chunking and Embedding Generation

Handles text chunking with overlap and generates embeddings
using Google Gemini API for semantic search capability.
"""

import time
from typing import Optional
from dataclasses import dataclass

import google.generativeai as genai

import config
from content_cleaner import CleanedContent


# ============================================================================
# Configure Gemini API
# ============================================================================

genai.configure(api_key=config.GEMINI_API_KEY)


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class TextChunk:
    """Represents a chunk of text with metadata."""
    id: str
    text: str
    embedding: Optional[list[float]]
    # Metadata for retrieval
    source_email_id: str
    source_title: str
    source_sender: str
    source_date: str
    chunk_index: int
    total_chunks: int


# ============================================================================
# Text Chunking
# ============================================================================

class TextChunker:
    """
    Splits text into overlapping chunks for embedding.
    
    Uses a sliding window approach with configurable
    chunk size and overlap.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        overlap: int = None
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.overlap = overlap or config.CHUNK_OVERLAP
    
    def _split_into_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences for cleaner chunk boundaries.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        import re
        
        # Split on sentence endings while preserving the delimiter
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Also split on double newlines (paragraph breaks)
        final_sentences = []
        for sentence in sentences:
            if '\n\n' in sentence:
                parts = sentence.split('\n\n')
                final_sentences.extend(parts)
            else:
                final_sentences.append(sentence)
        
        return [s.strip() for s in final_sentences if s.strip()]
    
    def chunk(self, content: CleanedContent) -> list[TextChunk]:
        """
        Split cleaned content into chunks.
        
        Args:
            content: Cleaned newsletter content
            
        Returns:
            List of TextChunk objects
        """
        text = content.text
        
        if len(text) <= self.chunk_size:
            # Small enough to be a single chunk
            return [TextChunk(
                id=f"{content.source_email_id}_0",
                text=text,
                embedding=None,
                source_email_id=content.source_email_id,
                source_title=content.title,
                source_sender=content.source_sender,
                source_date=content.source_date,
                chunk_index=0,
                total_chunks=1
            )]
        
        # Split into sentences for cleaner boundaries
        sentences = self._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Current chunk is full, save it
                chunk_text = ' '.join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_text = ' '.join(current_chunk[-2:]) if len(current_chunk) >= 2 else ''
                if len(overlap_text) > self.overlap:
                    overlap_text = overlap_text[-self.overlap:]
                
                current_chunk = [overlap_text] if overlap_text else []
                current_length = len(overlap_text)
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1  # +1 for space
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        # Create TextChunk objects
        total_chunks = len(chunks)
        return [
            TextChunk(
                id=f"{content.source_email_id}_{i}",
                text=chunk_text.strip(),
                embedding=None,
                source_email_id=content.source_email_id,
                source_title=content.title,
                source_sender=content.source_sender,
                source_date=content.source_date,
                chunk_index=i,
                total_chunks=total_chunks
            )
            for i, chunk_text in enumerate(chunks)
        ]


# ============================================================================
# Embedding Generator
# ============================================================================

class EmbeddingGenerator:
    """
    Generates embeddings using Google Gemini API.
    
    Handles rate limiting and batch processing.
    """
    
    def __init__(self, model: str = None):
        """
        Initialize the embedding generator.
        
        Args:
            model: Gemini embedding model to use
        """
        self.model = model or config.EMBEDDING_MODEL
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    def _rate_limit(self):
        """Apply rate limiting between API calls."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()
    
    def generate(self, text: str) -> Optional[list[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if error
        """
        try:
            self._rate_limit()
            
            result = genai.embed_content(
                model=self.model,
                content=text,
                task_type="retrieval_document"
            )
            
            return result['embedding']
        
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None
    
    def generate_query_embedding(self, query: str) -> Optional[list[float]]:
        """
        Generate embedding for a search query.
        
        Uses a different task type optimized for queries.
        
        Args:
            query: Search query text
            
        Returns:
            Embedding vector or None if error
        """
        try:
            self._rate_limit()
            
            result = genai.embed_content(
                model=self.model,
                content=query,
                task_type="retrieval_query"
            )
            
            return result['embedding']
        
        except Exception as e:
            print(f"Query embedding error: {e}")
            return None
    
    def generate_batch(
        self, 
        chunks: list[TextChunk],
        show_progress: bool = True
    ) -> list[TextChunk]:
        """
        Generate embeddings for multiple chunks.
        
        Args:
            chunks: List of TextChunk objects
            show_progress: Whether to print progress
            
        Returns:
            List of TextChunk objects with embeddings populated
        """
        total = len(chunks)
        
        for i, chunk in enumerate(chunks):
            if show_progress and (i + 1) % 10 == 0:
                print(f"Generating embeddings: {i + 1}/{total}")
            
            embedding = self.generate(chunk.text)
            chunk.embedding = embedding
        
        if show_progress:
            print(f"Completed: {total}/{total} embeddings generated")
        
        return chunks


# ============================================================================
# Combined Pipeline
# ============================================================================

class EmbeddingPipeline:
    """
    Complete pipeline for chunking and embedding content.
    """
    
    def __init__(self):
        """Initialize the pipeline components."""
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()
    
    def process(
        self, 
        contents: list[CleanedContent],
        show_progress: bool = True
    ) -> list[TextChunk]:
        """
        Process cleaned content through the full pipeline.
        
        Args:
            contents: List of cleaned newsletter content
            show_progress: Whether to print progress
            
        Returns:
            List of TextChunk objects with embeddings
        """
        all_chunks = []
        
        # Chunk all content
        if show_progress:
            print(f"Chunking {len(contents)} newsletters...")
        
        for content in contents:
            chunks = self.chunker.chunk(content)
            all_chunks.extend(chunks)
        
        if show_progress:
            print(f"Created {len(all_chunks)} chunks")
        
        # Generate embeddings
        if show_progress:
            print("Generating embeddings...")
        
        embedded_chunks = self.embedder.generate_batch(
            all_chunks, 
            show_progress=show_progress
        )
        
        # Filter out chunks with failed embeddings
        successful = [c for c in embedded_chunks if c.embedding is not None]
        
        if show_progress:
            failed = len(embedded_chunks) - len(successful)
            if failed > 0:
                print(f"Warning: {failed} chunks failed embedding generation")
        
        return successful


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("Embeddings Module Test")
    print("=" * 50)
    
    # Test chunking
    print("\n1. Testing Text Chunking")
    print("-" * 30)
    
    from datetime import datetime
    
    sample_content = CleanedContent(
        title="Test Newsletter",
        text="""
        This is the first paragraph of the newsletter. It contains some
        interesting information about technology and innovation.
        
        The second paragraph discusses recent developments in AI. Machine
        learning models are becoming more sophisticated every day.
        
        Here are some key points to remember. First, always stay curious.
        Second, keep learning new things. Third, share knowledge with others.
        
        In conclusion, this newsletter has covered important topics that
        matter to our readers. Stay tuned for more updates next week.
        """ * 3,  # Repeat to make it longer
        word_count=100,
        source_email_id="test123",
        source_subject="Test Subject",
        source_sender="Test Sender",
        source_date=datetime.now().isoformat()
    )
    
    chunker = TextChunker(chunk_size=500, overlap=100)
    chunks = chunker.chunk(sample_content)
    
    print(f"Created {len(chunks)} chunks from {len(sample_content.text)} characters")
    for chunk in chunks[:2]:  # Show first 2
        print(f"  Chunk {chunk.chunk_index}: {len(chunk.text)} chars")
    
    # Test embedding generation (if API key is available)
    print("\n2. Testing Embedding Generation")
    print("-" * 30)
    
    try:
        embedder = EmbeddingGenerator()
        embedding = embedder.generate("This is a test sentence.")
        
        if embedding:
            print(f"✓ Generated embedding with {len(embedding)} dimensions")
            print(f"  First 5 values: {embedding[:5]}")
        else:
            print("✗ Failed to generate embedding")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  (This is expected if GEMINI_API_KEY is not set)")
