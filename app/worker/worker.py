"""Background job processor for document ingestion."""
import asyncio
from uuid import UUID

from app.db import mongodb
from app.models import JobStatus
from app.services.document_parser import DocumentParser
from app.services.embedding import EmbeddingService
from app.services.qdrant import qdrant_service
from app.utils.logging import log_job_event, logger


class Worker:
    """Background worker for processing ingestion jobs."""
    
    def __init__(self, poll_interval: int = 2):
        self.poll_interval = poll_interval
        self.running = False
    
    async def process_job(self, job: dict):
        """Process a single ingestion job."""
        job_id = UUID(job["job_id"])
        file_name = job["file_name"]
        file_content_base64 = job["file_content_base64"]
        collection_name = job.get("collection_name", qdrant_service.COLLECTION_NAME)
        
        log_job_event(str(job_id), "PROCESSING_STARTED", file_name=file_name)
        
        try:
            # Update status to PROCESSING
            await mongodb.update_job_status(job_id, JobStatus.PROCESSING)
            
            # Parse PDF (CPU-bound)
            text = await asyncio.to_thread(DocumentParser.parse_pdf, file_content_base64)
            if not text:
                raise ValueError("Failed to extract text from PDF")
            
            log_job_event(str(job_id), "PDF_PARSED", text_length=len(text))
            
            # Chunk text (CPU-bound)
            chunks = await asyncio.to_thread(EmbeddingService.chunk_text, text)
            if not chunks:
                raise ValueError("No chunks created from text")
            
            log_job_event(str(job_id), "TEXT_CHUNKED", chunk_count=len(chunks))
            
            # Generate embeddings
            embeddings = await EmbeddingService.generate_embeddings(chunks)
            if len(embeddings) != len(chunks):
                raise ValueError("Embedding count mismatch")
            
            log_job_event(str(job_id), "EMBEDDINGS_GENERATED", embedding_count=len(embeddings))
            
            # Prepare chunks for Qdrant (chunk_id, chunk_text, embedding, source)
            qdrant_chunks = [
                (chunk_id, chunk_text, embedding, file_name)
                for (chunk_id, chunk_text), (_, embedding) in zip(chunks, embeddings)
            ]
            
            # Store in Qdrant
            await qdrant_service.store_chunks(qdrant_chunks, collection_name=collection_name)
            
            log_job_event(str(job_id), "QDRANT_STORED", chunk_count=len(qdrant_chunks))
            
            # Update job status to COMPLETED
            await mongodb.update_job_status(
                job_id,
                JobStatus.COMPLETED,
                chunk_count=len(chunks)
            )
            
            log_job_event(str(job_id), "PROCESSING_COMPLETED", chunk_count=len(chunks))
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing job {job_id}: {error_message}")
            
            # Update job status to FAILED
            await mongodb.update_job_status(
                job_id,
                JobStatus.FAILED,
                error_message=error_message
            )
            
            log_job_event(str(job_id), "PROCESSING_FAILED", error=error_message)
    
    async def run(self):
        """Run worker loop."""
        self.running = True
        logger.info("Worker started")
        
        while self.running:
            try:
                # Get pending jobs
                pending_jobs = await mongodb.get_pending_jobs(limit=5)
                
                if pending_jobs:
                    logger.info(f"Processing {len(pending_jobs)} pending jobs")
                    # Process jobs concurrently
                    tasks = [self.process_job(job) for job in pending_jobs]
                    await asyncio.gather(*tasks, return_exceptions=True)
                else:
                    # No jobs, wait before next poll
                    await asyncio.sleep(self.poll_interval)
                    
            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)
    
    def stop(self):
        """Stop worker."""
        self.running = False
        logger.info("Worker stopped")


# Global worker instance
worker = Worker()
