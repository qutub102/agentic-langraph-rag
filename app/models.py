"""Pydantic models for request/response validation."""
from datetime import datetime
from enum import Enum
from typing import List, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Ingest API Models
class IngestRequest(BaseModel):
    """Request model for document ingestion."""
    file_name: str = Field(..., description="Name of the file to ingest")
    file_content_base64: str = Field(..., description="Base64 encoded file content")

    @field_validator('file_name')
    @classmethod
    def validate_file_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("file_name cannot be empty")
        if not v.lower().endswith('.pdf'):
            raise ValueError("Only PDF files are supported")
        return v.strip()

    @field_validator('file_content_base64')
    @classmethod
    def validate_file_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("file_content_base64 cannot be empty")
        # Basic base64 validation
        import base64
        try:
            decoded = base64.b64decode(v, validate=True)
            if len(decoded) > 10 * 1024 * 1024:  # 10MB limit
                raise ValueError("File size exceeds 10MB limit")
        except Exception as e:
            raise ValueError(f"Invalid base64 content: {str(e)}")
        return v


class IngestResponse(BaseModel):
    """Response model for document ingestion."""
    job_id: UUID
    status: Literal["PENDING"]


class IngestStatusResponse(BaseModel):
    """Response model for job status check."""
    job_id: UUID
    status: Literal["PENDING", "PROCESSING", "COMPLETED", "FAILED"]


# Chat API Models
class Citation(BaseModel):
    """Citation model for chat responses."""
    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    source: str = Field(..., description="Source filename")
    quote: str = Field(..., max_length=300, description="Quote from the chunk (max 300 chars)")

    @field_validator('quote')
    @classmethod
    def validate_quote_length(cls, v: str) -> str:
        if len(v) > 300:
            return v[:300]
        return v


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., max_length=1000, description="User question (max 1000 chars)")

    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("question cannot be empty")
        if len(v) > 1000:
            raise ValueError("question exceeds 1000 character limit")
        return v.strip()


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str = Field(..., max_length=1500, description="Answer text (max 1500 chars)")
    citations: List[Citation] = Field(..., min_length=1, description="List of citations (at least 1 required)")
    confidence: Literal["LOW", "MEDIUM", "HIGH"] = Field(..., description="Confidence level")

    @field_validator('answer')
    @classmethod
    def validate_answer_length(cls, v: str) -> str:
        if len(v) > 1500:
            return v[:1500]
        return v

    @field_validator('citations')
    @classmethod
    def validate_citations(cls, v: List[Citation]) -> List[Citation]:
        if len(v) < 1:
            raise ValueError("At least one citation is required")
        return v
