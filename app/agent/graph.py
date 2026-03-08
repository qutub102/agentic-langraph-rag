"""LangGraph workflow definition for retrieval and reasoning."""
from typing import Dict, List, TypedDict

from langgraph.graph import StateGraph, END

from app.services.embedding import EmbeddingService
from app.services.llm_contract import LLMContractService
from app.services.qdrant import qdrant_service
from app.utils.logging import logger


class AgentState(TypedDict):
    """State for LangGraph agent workflow."""
    question: str
    collection_name: str
    iteration_count: int
    retrieved_chunks: List[Dict[str, str]]
    answer: str
    citations: List[Dict[str, str]]
    confidence: str


class LangGraphAgent:
    """LangGraph agent for document Q&A."""
    
    MAX_ITERATIONS = 3
    
    def __init__(self):
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("reason", self._reason_node)
        
        # Define edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "reason")
        workflow.add_conditional_edges(
            "reason",
            self._should_continue,
            {
                "continue": "retrieve",
                "end": END
            }
        )
        
        return workflow.compile()
    
    async def _retrieve_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant chunks from Qdrant."""
        try:
            # Generate query embedding
            query_chunks = EmbeddingService.chunk_text(state["question"])
            if not query_chunks:
                return state
            
            # Use first chunk for query embedding
            _, query_text = query_chunks[0]
            embeddings = await EmbeddingService.generate_embeddings([(query_chunks[0][0], query_text)])
            if not embeddings:
                return state
            
            query_embedding = embeddings[0][1]
            
            # Search Qdrant
            collection_name = state.get("collection_name", qdrant_service.COLLECTION_NAME)
            chunks = await qdrant_service.search_chunks(
                query_embedding=query_embedding,
                collection_name=collection_name,
                top_k=8,
                limit=8
            )
            
            state["retrieved_chunks"] = chunks
            logger.info(f"Retrieved {len(chunks)} chunks for question")
            
        except Exception as e:
            logger.error(f"Error in retrieve node: {str(e)}")
            state["retrieved_chunks"] = []
        
        return state
    
    async def _reason_node(self, state: AgentState) -> AgentState:
        """Generate answer using LLM."""
        try:
            chunks = state.get("retrieved_chunks", [])
            
            if not chunks:
                state["answer"] = "I am sorry, I do not have an answer to it."
                state["citations"] = [{"chunk_id": "", "source": "", "quote": ""}]
                state["confidence"] = "LOW"
                return state
            
            # Generate answer using LLM
            response = await LLMContractService.generate_answer(
                question=state["question"],
                chunks=chunks
            )
            
            state["answer"] = response.answer
            state["citations"] = [
                {
                    "chunk_id": cit.chunk_id,
                    "source": cit.source,
                    "quote": cit.quote
                }
                for cit in response.citations
            ]
            state["confidence"] = response.confidence
            
            logger.info(f"Generated answer with confidence: {response.confidence}")
            
        except Exception as e:
            logger.error(f"Error in reason node: {str(e)}")
            state["answer"] = "I encountered an error processing your question. Please try again."
            state["citations"] = [{"chunk_id": "", "source": "", "quote": ""}]
            state["confidence"] = "LOW"
        
        return state
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if workflow should continue or end."""
        iteration = state.get("iteration_count", 0) + 1
        state["iteration_count"] = iteration
        
        # End if max iterations reached or we have a good answer
        if iteration >= self.MAX_ITERATIONS:
            return "end"
        
        # End if we have high confidence answer
        if state.get("confidence") == "HIGH":
            return "end"
        
        # Continue for refinement if needed
        if iteration < self.MAX_ITERATIONS and state.get("confidence") in ["LOW", "MEDIUM"]:
            return "continue"
        
        return "end"
    
    async def process_question(self, question: str, collection_name: str = qdrant_service.COLLECTION_NAME) -> Dict:
        """
        Process a question through the LangGraph workflow.
        
        Args:
            question: User question
            collection_name: Name of the Qdrant collection to search in
            
        Returns:
            Dictionary with answer, citations, and confidence
        """
        initial_state: AgentState = {
            "question": question,
            "collection_name": collection_name,
            "iteration_count": 0,
            "retrieved_chunks": [],
            "answer": "",
            "citations": [],
            "confidence": "LOW"
        }
        
        final_state = await self.graph.ainvoke(initial_state)
        
        return {
            "answer": final_state.get("answer", ""),
            "citations": final_state.get("citations", []),
            "confidence": final_state.get("confidence", "LOW")
        }


# Global agent instance
langgraph_agent = LangGraphAgent()
