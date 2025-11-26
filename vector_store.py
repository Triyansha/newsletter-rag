"""
vector_store.py - ChromaDB Vector Database Operations

Handles storing and retrieving newsletter embeddings using ChromaDB.
Provides semantic search capability over newsletter content.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

import chromadb
from chromadb.config import Settings

import config
from embeddings import TextChunk


# ============================================================================
# Search Result Structure
# ============================================================================

@dataclass
class SearchResult:
    """Represents a search result with relevance score."""
    chunk_id: str
    text: str
    score: float  # Distance (lower is more similar)
    source_title: str
    source_sender: str
    source_date: str
    source_email_id: str


# ============================================================================
# Vector Store Class
# ============================================================================

class VectorStore:
    """
    ChromaDB-based vector store for newsletter embeddings.
    
    Provides methods for storing, retrieving, and searching
    newsletter content by semantic similarity.
    """
    
    def __init__(
        self,
        persist_dir: str = None,
        collection_name: str = None
    ):
        """
        Initialize the vector store.
        
        Args:
            persist_dir: Directory to persist the database
            collection_name: Name of the collection
        """
        self.persist_dir = persist_dir or config.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        
        # Ensure directory exists
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "Newsletter content embeddings"}
        )
    
    def add_chunks(self, chunks: list[TextChunk]) -> int:
        """
        Add chunks with embeddings to the vector store.
        
        Args:
            chunks: List of TextChunk objects with embeddings
            
        Returns:
            Number of chunks successfully added
        """
        if not chunks:
            return 0
        
        # Filter chunks with valid embeddings
        valid_chunks = [c for c in chunks if c.embedding is not None]
        
        if not valid_chunks:
            return 0
        
        # Prepare data for ChromaDB
        ids = [chunk.id for chunk in valid_chunks]
        embeddings = [chunk.embedding for chunk in valid_chunks]
        documents = [chunk.text for chunk in valid_chunks]
        metadatas = [
            {
                "source_email_id": chunk.source_email_id,
                "source_title": chunk.source_title,
                "source_sender": chunk.source_sender,
                "source_date": chunk.source_date,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks
            }
            for chunk in valid_chunks
        ]
        
        # Add to collection (upsert to handle duplicates)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        return len(valid_chunks)
    
    def search(
        self,
        query_embedding: list[float],
        top_k: int = None,
        filter_sender: str = None,
        filter_date_after: str = None
    ) -> list[SearchResult]:
        """
        Search for similar content using query embedding.
        
        Args:
            query_embedding: The query vector
            top_k: Number of results to return
            filter_sender: Optional sender filter
            filter_date_after: Optional date filter (ISO format)
            
        Returns:
            List of SearchResult objects
        """
        top_k = top_k or config.TOP_K_RESULTS
        
        # Build where filter if provided
        where_filter = None
        if filter_sender or filter_date_after:
            conditions = []
            
            if filter_sender:
                conditions.append({
                    "source_sender": {"$contains": filter_sender}
                })
            
            if filter_date_after:
                conditions.append({
                    "source_date": {"$gte": filter_date_after}
                })
            
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        # Parse results
        search_results = []
        
        if results and results['ids'] and results['ids'][0]:
            ids = results['ids'][0]
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for i, chunk_id in enumerate(ids):
                search_results.append(SearchResult(
                    chunk_id=chunk_id,
                    text=documents[i],
                    score=distances[i],
                    source_title=metadatas[i].get('source_title', ''),
                    source_sender=metadatas[i].get('source_sender', ''),
                    source_date=metadatas[i].get('source_date', ''),
                    source_email_id=metadatas[i].get('source_email_id', '')
                ))
        
        return search_results
    
    def get_chunk(self, chunk_id: str) -> Optional[SearchResult]:
        """
        Retrieve a specific chunk by ID.
        
        Args:
            chunk_id: The chunk identifier
            
        Returns:
            SearchResult or None if not found
        """
        result = self.collection.get(
            ids=[chunk_id],
            include=["documents", "metadatas"]
        )
        
        if result and result['ids']:
            return SearchResult(
                chunk_id=result['ids'][0],
                text=result['documents'][0],
                score=0.0,
                source_title=result['metadatas'][0].get('source_title', ''),
                source_sender=result['metadatas'][0].get('source_sender', ''),
                source_date=result['metadatas'][0].get('source_date', ''),
                source_email_id=result['metadatas'][0].get('source_email_id', '')
            )
        
        return None
    
    def delete_by_email(self, email_id: str) -> int:
        """
        Delete all chunks from a specific email.
        
        Args:
            email_id: The source email ID
            
        Returns:
            Number of chunks deleted
        """
        # Get all chunks for this email
        results = self.collection.get(
            where={"source_email_id": email_id},
            include=[]
        )
        
        if results and results['ids']:
            self.collection.delete(ids=results['ids'])
            return len(results['ids'])
        
        return 0
    
    def get_stats(self) -> dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        
        # Get unique sources
        all_data = self.collection.get(include=["metadatas"])
        unique_emails = set()
        unique_senders = set()
        
        if all_data and all_data['metadatas']:
            for meta in all_data['metadatas']:
                unique_emails.add(meta.get('source_email_id', ''))
                unique_senders.add(meta.get('source_sender', ''))
        
        return {
            "total_chunks": count,
            "unique_newsletters": len(unique_emails),
            "unique_senders": len(unique_senders),
            "persist_directory": self.persist_dir,
            "collection_name": self.collection_name
        }
    
    def clear(self) -> bool:
        """
        Clear all data from the collection.
        
        Returns:
            True if successful
        """
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Newsletter content embeddings"}
            )
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
    
    def list_newsletters(self, limit: int = 50) -> list[dict]:
        """
        List all unique newsletters in the store.
        
        Args:
            limit: Maximum number of newsletters to return
            
        Returns:
            List of newsletter metadata dictionaries
        """
        all_data = self.collection.get(include=["metadatas"])
        
        seen_emails = set()
        newsletters = []
        
        if all_data and all_data['metadatas']:
            for meta in all_data['metadatas']:
                email_id = meta.get('source_email_id', '')
                
                if email_id not in seen_emails:
                    seen_emails.add(email_id)
                    newsletters.append({
                        "email_id": email_id,
                        "title": meta.get('source_title', ''),
                        "sender": meta.get('source_sender', ''),
                        "date": meta.get('source_date', '')
                    })
                    
                    if len(newsletters) >= limit:
                        break
        
        # Sort by date (newest first)
        newsletters.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return newsletters


# ============================================================================
# Module Testing
# ============================================================================

if __name__ == "__main__":
    print("Vector Store Test")
    print("=" * 50)
    
    import tempfile
    
    # Use temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Using temp directory: {tmpdir}")
        
        # Initialize store
        store = VectorStore(persist_dir=tmpdir, collection_name="test")
        print("✓ Vector store initialized")
        
        # Create test chunks with fake embeddings
        test_chunks = [
            TextChunk(
                id="email1_0",
                text="AI is transforming the technology landscape.",
                embedding=[0.1] * 768,  # Fake embedding
                source_email_id="email1",
                source_title="Tech Weekly",
                source_sender="tech@example.com",
                source_date="2024-01-15",
                chunk_index=0,
                total_chunks=1
            ),
            TextChunk(
                id="email2_0",
                text="Machine learning models are becoming more efficient.",
                embedding=[0.2] * 768,
                source_email_id="email2",
                source_title="AI Daily",
                source_sender="ai@example.com",
                source_date="2024-01-16",
                chunk_index=0,
                total_chunks=1
            )
        ]
        
        # Add chunks
        added = store.add_chunks(test_chunks)
        print(f"✓ Added {added} chunks")
        
        # Get stats
        stats = store.get_stats()
        print(f"✓ Stats: {stats}")
        
        # Search
        results = store.search(
            query_embedding=[0.15] * 768,
            top_k=2
        )
        print(f"✓ Search returned {len(results)} results")
        
        for result in results:
            print(f"  - {result.source_title}: {result.text[:50]}...")
        
        # List newsletters
        newsletters = store.list_newsletters()
        print(f"✓ Listed {len(newsletters)} newsletters")
        
        # Clear
        store.clear()
        print("✓ Store cleared")
        
        print("\nAll tests passed!")
