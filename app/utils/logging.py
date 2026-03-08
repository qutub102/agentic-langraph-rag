"""Structured logging and tracing."""
import os
from dotenv import load_dotenv
load_dotenv()

import logging
import sys
from typing import Any, Dict

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("agentic_rag")


def log_request(method: str, path: str, **kwargs):
    """Log API request."""
    logger.info(f"API Request: {method} {path}", extra=kwargs)


def log_response(status_code: int, path: str, **kwargs):
    """Log API response."""
    logger.info(f"API Response: {status_code} {path}", extra=kwargs)


def log_job_event(job_id: str, event: str, **kwargs):
    """Log job processing event."""
    logger.info(f"Job Event: {job_id} - {event}", extra=kwargs)


def log_llm_call(model: str, prompt_length: int, response_length: int, **kwargs):
    """Log LLM API call (without PII)."""
    logger.info(
        f"LLM Call: model={model}, prompt_len={prompt_length}, response_len={response_length}",
        extra=kwargs
    )


def log_error(error: Exception, context: Dict[str, Any] = None):
    """Log error with context."""
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        extra=context or {},
        exc_info=True
    )
