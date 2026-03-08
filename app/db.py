"""MongoDB connection and job status operations."""
import os
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
# import certifi

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError

from app.models import JobStatus


class MongoDB:
    """MongoDB client wrapper."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self):
        """Connect to MongoDB."""
        connection_string = os.getenv("MONGODB_URL")
        database_name = os.getenv("MONGODB_DATABASE")
        
        self.client = AsyncIOMotorClient(connection_string)
        # self.client = AsyncIOMotorClient(connection_string, tlsCAFile=certifi.where())
        self.db = self.client[database_name]
        
        # Create indexes
        await self.db.jobs.create_index("job_id", unique=True)
        await self.db.jobs.create_index("status")
        await self.db.jobs.create_index("created_at")
    
    async def disconnect(self):
        """Disconnect from MongoDB."""
        if self.client:
            self.client.close()
    
    async def create_job(self, file_name: str, file_content_base64: str) -> UUID:
        """Create a new ingestion job."""
        job_id = uuid4()
        job_doc = {
            "job_id": str(job_id),
            "file_name": file_name,
            "status": JobStatus.PENDING.value,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "file_content_base64": file_content_base64,
            "chunk_count": 0,
            "error_message": None
        }
        
        try:
            await self.db.jobs.insert_one(job_doc)
            return job_id
        except DuplicateKeyError:
            # Retry with new UUID if collision (extremely rare)
            return await self.create_job(file_name, file_content_base64)
    
    async def get_job(self, job_id: UUID) -> Optional[dict]:
        """Get job by ID."""
        job = await self.db.jobs.find_one({"job_id": str(job_id)})
        return job
    
    async def update_job_status(
        self,
        job_id: UUID,
        status: JobStatus,
        chunk_count: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Update job status."""
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow()
        }
        
        if chunk_count is not None:
            update_data["chunk_count"] = chunk_count
        
        if error_message is not None:
            update_data["error_message"] = error_message
        
        await self.db.jobs.update_one(
            {"job_id": str(job_id)},
            {"$set": update_data}
        )
    
    async def get_pending_jobs(self, limit: int = 10) -> list:
        """Get pending jobs for worker processing."""
        cursor = self.db.jobs.find(
            {"status": JobStatus.PENDING.value}
        ).sort("created_at", 1).limit(limit)
        
        jobs = await cursor.to_list(length=limit)
        return jobs
    
    async def get_all_jobs(self, limit: int = 50) -> list:
        """Get all jobs sorted by creation date."""
        cursor = self.db.jobs.find().sort("created_at", -1).limit(limit)
        jobs = await cursor.to_list(length=limit)
        return jobs


# Global MongoDB instance
mongodb = MongoDB()
