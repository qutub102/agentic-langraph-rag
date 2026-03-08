"""FastAPI application entry point."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, ingest
from app.db import mongodb
from app.services.qdrant import qdrant_service
from app.utils.logging import logger
from app.worker.worker import worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    logger.info("Starting application...")
    
    # Connect to MongoDB
    await mongodb.connect()
    logger.info("Connected to MongoDB")
    
    # Connect to Qdrant
    await qdrant_service.connect()
    logger.info("Connected to Qdrant")
    
    # Start worker in background
    worker_task = asyncio.create_task(worker.run())
    logger.info("Worker started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop worker
    worker.stop()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    
    # Disconnect from databases
    await mongodb.disconnect()
    logger.info("Disconnected from MongoDB")


# Create FastAPI app
app = FastAPI(
    title="Agentic Document Assistant",
    description="An Agentic RAG system for document Q&A",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[VITE_FRONTEND_BASE_URL],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    return {"message": "Welcome to the Agentic Document Assistant"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Run with: py run.py (from project root)
# Or: py -m app.main (from project root)
# Or: uvicorn app.main:app --reload (from project root)
