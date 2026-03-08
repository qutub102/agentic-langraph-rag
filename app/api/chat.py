"""Chat API endpoint."""
from fastapi import APIRouter, HTTPException, status

from app.agent.graph import langgraph_agent
from app.models import ChatRequest, ChatResponse, Citation
from app.utils.logging import log_request, log_response, logger

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Submit question and receive answer with citations.
    
    React frontend calls this when user submits a question.
    """
    log_request("POST", "/chat", question_length=len(request.question))
    
    try:
        # Invoke LangGraph workflow
        result = await langgraph_agent.process_question(
            question=request.question,
            collection_name=request.collection_name
        )
        
        # Convert to response model
        citations = [
            Citation(
                chunk_id=cit["chunk_id"],
                source=cit["source"],
                quote=cit["quote"]
            )
            for cit in result.get("citations", [])
        ]
        
        response = ChatResponse(
            answer=result.get("answer", ""),
            citations=citations,
            confidence=result.get("confidence", "LOW")
        )
        
        log_response(200, "/chat", confidence=response.confidence, citation_count=len(citations))
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process question"
        )
