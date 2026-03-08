"""Ingest API endpoints."""
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.db import mongodb
from app.models import IngestRequest, IngestResponse, IngestStatusResponse, JobStatus
from app.utils.logging import log_request, log_response, logger

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(request: IngestRequest):
    """
    Upload document for processing.
    
    React frontend calls this when user uploads a file.
    """
    log_request("POST", "/ingest", file_name=request.file_name)
    
    try:
        # Create job in MongoDB
        job_id = await mongodb.create_job(
            file_name=request.file_name,
            file_content_base64=request.file_content_base64
        )
        
        log_response(202, "/ingest", job_id=str(job_id))
        
        return IngestResponse(
            job_id=job_id,
            status="PENDING"
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating ingestion job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ingestion job"
        )


@router.get("/{job_id}", response_model=IngestStatusResponse)
async def get_job_status(job_id: UUID):
    """
    Check ingestion job status.
    
    React frontend polls this endpoint to update job status list.
    """
    log_request("GET", f"/ingest/{job_id}")
    
    try:
        job = await mongodb.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        
        status_value = job.get("status", "PENDING")
        
        log_response(200, f"/ingest/{job_id}", status=status_value)
        
        return IngestStatusResponse(
            job_id=job_id,
            status=status_value
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job status"
        )


@router.get("", response_model=list)
async def list_jobs(limit: int = 50):
    """
    List all ingestion jobs.
    
    React frontend uses this to display job status list.
    """
    log_request("GET", "/ingest")
    
    try:
        jobs = await mongodb.get_all_jobs(limit=limit)
        
        # Format jobs for frontend
        formatted_jobs = []
        for job in jobs:
            formatted_jobs.append({
                "job_id": job["job_id"],
                "file_name": job["file_name"],
                "status": job["status"],
                "created_at": job["created_at"].isoformat() if job.get("created_at") else None,
                "updated_at": job["updated_at"].isoformat() if job.get("updated_at") else None,
                "chunk_count": job.get("chunk_count", 0),
                "error_message": job.get("error_message")
            })
        
        log_response(200, "/ingest", job_count=len(formatted_jobs))
        
        return formatted_jobs
        
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list jobs"
        )
