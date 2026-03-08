import os
from dotenv import load_dotenv
load_dotenv()

"""Chunking and OpenAI embedding generation."""
import uuid
from typing import List, Tuple

from openai import AsyncOpenAI

from app.utils.logging import log_error, log_llm_call, logger

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class EmbeddingService:
    """Service for text chunking and embedding generation."""
    
    # Target: ~500 words per chunk (approximately 2000-3000 characters)
    CHUNK_SIZE = 2500  # characters
    CHUNK_OVERLAP = 200  # characters for context preservation
    
    @staticmethod
    def chunk_text(text: str) -> List[Tuple[str, str]]:
        """
        Chunk text into smaller pieces.
        
        Args:
            text: Full text content
            
        Returns:
            List of tuples (chunk_id, chunk_text)
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end position
            end = min(start + EmbeddingService.CHUNK_SIZE, text_length)
            
            # Try to break at sentence boundary if possible
            if end < text_length:
                # Look for sentence endings near the chunk boundary
                for punct in ['. ', '.\n', '! ', '!\n', '? ', '?\n']:
                    last_punct = text.rfind(punct, start, end)
                    if last_punct > start + EmbeddingService.CHUNK_SIZE // 2:
                        end = last_punct + 1
                        break
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = str(uuid.uuid4())[:8]
                chunks.append((chunk_id, chunk_text))
            
            if end >= text_length:
                break
                
            # Move start position with overlap
            start = end - EmbeddingService.CHUNK_OVERLAP
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    @staticmethod
    async def generate_embeddings(chunks: List[Tuple[str, str]]) -> List[Tuple[str, List[float]]]:
        """
        Generate embeddings for text chunks using OpenAI.
        
        Args:
            chunks: List of (chunk_id, chunk_text) tuples
            
        Returns:
            List of (chunk_id, embedding_vector) tuples
        """
        if not chunks:
            return []
        
        try:
            # Extract texts
            texts = [chunk_text for _, chunk_text in chunks]
            
            # Generate embeddings
            response = await openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            
            embeddings = []
            for i, (chunk_id, _) in enumerate(chunks):
                embedding = response.data[i].embedding
                embeddings.append((chunk_id, embedding))
            
            log_llm_call(
                model="text-embedding-3-small",
                prompt_length=sum(len(text) for text in texts),
                response_length=len(embeddings) * len(embeddings[0][1]) if embeddings else 0
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            log_error(e, {"context": "Embedding generation", "chunk_count": len(chunks)})
            raise
