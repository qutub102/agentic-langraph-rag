"""Qdrant vector storage and retrieval operations."""
import os
from dotenv import load_dotenv
load_dotenv()

from typing import List, Optional, Tuple

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.utils.logging import log_error, logger


class QdrantService:
    """Service for Qdrant vector operations."""
    
    COLLECTION_NAME = "document_chunks"
    VECTOR_SIZE = 1536  # text-embedding-3-small dimension
    
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
    
    async def connect(self):
        """Connect to Qdrant."""
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        
        self.client = AsyncQdrantClient(
            url=url,
            api_key=api_key,
            timeout=60.0
        )
        
    async def ensure_collection(self, collection_name: str):
        """Ensure a collection exists, creating it if necessary."""
        if not self.client:
            await self.connect()
            
        collections = await self.client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        if collection_name not in collection_names:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
    
    async def store_chunks(
        self,
        chunks: List[Tuple[str, str, List[float], str]],
        collection_name: str = COLLECTION_NAME
    ) -> bool:
        """
        Store document chunks in Qdrant.
        
        Args:
            chunks: List of (chunk_id, chunk_text, embedding, source_filename) tuples
            collection_name: Qdrant collection name
            
        Returns:
            True if successful
        """
        if not chunks:
            return True
        
        try:
            import hashlib
            points = []
            for chunk_id, chunk_text, embedding, source in chunks:
                # Use hash of chunk_id for Qdrant point ID (must be int or UUID)
                point_id = int(hashlib.md5(chunk_id.encode()).hexdigest()[:8], 16)
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": chunk_text,
                        "source": source,
                        "chunk_id": chunk_id
                    }
                )
                points.append(point)
            
            await self.ensure_collection(collection_name)
            
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"Stored {len(points)} chunks in Qdrant")
            return True
            
        except Exception as e:
            log_error(e, {"context": "Qdrant storage", "chunk_count": len(chunks)})
            raise
    
    async def search_chunks(
        self,
        query_embedding: List[float],
        collection_name: str = COLLECTION_NAME,
        top_k: int = 8,
        limit: int = 8
    ) -> List[dict]:
        """
        Search for similar chunks using semantic search.
        
        Args:
            query_embedding: Query embedding vector
            collection_name: Qdrant collection name
            top_k: Number of results to return
            limit: Maximum number of results
            score_threshold: Minimum similarity score for chunks to be considered relevant
            
        Returns:
            List of chunk dictionaries with text, source, chunk_id, and score
        """
        try:
            # We don't automatically create the collection here, but we check if it exists implicitly by querying it.
            # If it doesn't exist, qdrant-client will raise an error which we catch.
            results = await self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=min(top_k, limit),
                score_threshold=0.25
            )
            
            chunks = []
            for result in results:
                payload = result.payload
                chunks.append({
                    "chunk_id": payload.get("chunk_id", ""),
                    "content": payload.get("text", ""),
                    "source": payload.get("source", ""),
                    "score": result.score
                })
            
            logger.info(f"Retrieved {len(chunks)} chunks from Qdrant")
            return chunks
            
        except Exception as e:
            log_error(e, {"context": "Qdrant search", "top_k": top_k})
            raise


# Global Qdrant instance
qdrant_service = QdrantService()
