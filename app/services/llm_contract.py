"""GPT-4o-mini invocation, JSON validation, and schema enforcement."""
import json
import os
from typing import Dict, List, Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.models import ChatResponse, Citation
from app.utils.logging import log_error, log_llm_call, logger

# Initialize OpenAI client
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL_NAME = os.getenv("OPENAI_MODEL")
TIMEOUT_SECONDS = 30.0


class LLMContractService:
    """Service for LLM interaction with strict contract enforcement."""
    
    SYSTEM_INSTRUCTIONS = """You are a precise document Q&A assistant. Answer questions strictly using only the provided document chunks. 
You must cite specific quotes from the chunks in your response. Output valid JSON matching the required schema. Use rich markdown formatting (like bullet points, bold text, and numbered lists) to make your answer detailed, structured, and easy to read."""
    
    @staticmethod
    def _format_chunks(chunks: List[Dict[str, str]]) -> str:
        """Format chunks for prompt."""
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"Chunk {i} (ID: {chunk['chunk_id']}, Source: {chunk['source']}):\n"
                f"{chunk['content'][:2000]}\n"
            )
        return "\n".join(formatted)
    
    @staticmethod
    def _create_user_prompt(question: str, chunks: List[Dict[str, str]]) -> str:
        """Create user prompt with question and chunks."""
        formatted_chunks = LLMContractService._format_chunks(chunks)
        
        prompt = f"""Question: {question}

Retrieved Document Chunks:
{formatted_chunks}

Instructions:
- Answer the question using ONLY information from the provided chunks
- Provide a detailed and comprehensive answer, capturing the full detail present in the chunks
- Use markdown formatting (e.g., bullet points, numbered lists, bold text, line breaks) to structure your response clearly and exactly reproduce lists found in the text
- If the answer cannot be determined from the chunks, set confidence to LOW and output exactly "I am sorry, I do not have an answer to it".
- Include at least one citation with a direct quote from a relevant chunk
- Output valid JSON matching this exact schema:
{{
  "answer": "string (markdown formatted text up to 1500 chars)",
  "citations": [
    {{
      "chunk_id": "string",
      "source": "string (filename)",
      "quote": "string (≤300 chars)"
    }}
  ],
  "confidence": "LOW | MEDIUM | HIGH"
}}"""
        return prompt
    
    @staticmethod
    async def _invoke_llm(user_prompt: str) -> Optional[ChatCompletion]:
        """Invoke GPT-4o-mini with retry logic."""
        try:
            response = await openai_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": LLMContractService.SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                timeout=TIMEOUT_SECONDS
            )
            
            log_llm_call(
                model=MODEL_NAME,
                prompt_length=len(user_prompt),
                response_length=len(response.choices[0].message.content) if response.choices else 0
            )
            
            return response
            
        except Exception as e:
            log_error(e, {"context": "LLM invocation", "model": MODEL_NAME})
            return None
    
    @staticmethod
    def _parse_and_validate_response(
        llm_response: ChatCompletion,
        retry_count: int = 0
    ) -> Optional[ChatResponse]:
        """Parse and validate LLM response."""
        try:
            content = llm_response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")
            
            # Parse JSON
            try:
                llm_output = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON response: {str(e)}")
                if retry_count < 1:
                    # Re-prompt once
                    return None
                raise ValueError("Invalid JSON response after retry")
            
            # Validate and create response
            answer = llm_output.get("answer", "")[:1500]
            citations_data = llm_output.get("citations", [])
            confidence = llm_output.get("confidence", "LOW")
            
            # Validate citations
            citations = []
            if not citations_data or len(citations_data) < 1:
                if confidence == "LOW":
                    citations.append(Citation(chunk_id="", source="", quote=""))
                else:
                    if retry_count < 1:
                        return None  # Retry
                    raise ValueError("At least one citation required")
            else:
                for cit in citations_data:
                    citations.append(Citation(
                        chunk_id=str(cit.get("chunk_id", "")),
                        source=str(cit.get("source", "")),
                        quote=str(cit.get("quote", ""))[:300]
                    ))
            
            # Validate confidence
            if confidence not in ["LOW", "MEDIUM", "HIGH"]:
                confidence = "LOW"
            
            validated_response = ChatResponse(
                answer=answer,
                citations=citations,
                confidence=confidence
            )
            
            return validated_response
            
        except Exception as e:
            log_error(e, {"context": "Response validation", "retry_count": retry_count})
            return None
    
    @staticmethod
    async def generate_answer(
        question: str,
        chunks: List[Dict[str, str]]
    ) -> ChatResponse:
        """
        Generate answer using GPT-4o-mini with strict validation.
        
        Args:
            question: User question
            chunks: Retrieved document chunks
            
        Returns:
            Validated ChatResponse
            
        Raises:
            ValueError: If LLM fails after retries
        """
        if not chunks:
            # Return fallback response
            return ChatResponse(
                answer="I am sorry, I do not have an answer to it.",
                citations=[Citation(
                    chunk_id="",
                    source="",
                    quote=""
                )],
                confidence="LOW"
            )
        
        user_prompt = LLMContractService._create_user_prompt(question, chunks)
        
        # First attempt
        response = await LLMContractService._invoke_llm(user_prompt)
        if response:
            validated = LLMContractService._parse_and_validate_response(response, retry_count=0)
            if validated:
                return validated
        
        # Retry once
        logger.info("Retrying LLM call due to invalid response")
        response = await LLMContractService._invoke_llm(user_prompt)
        if response:
            validated = LLMContractService._parse_and_validate_response(response, retry_count=1)
            if validated:
                return validated
        
        # Fallback response after retries
        logger.warning("LLM call failed after retries, returning fallback")
        return ChatResponse(
            answer="I encountered a temporary issue processing your question. Please try again.",
            citations=[Citation(
                chunk_id=chunks[0]["chunk_id"] if chunks else "",
                source=chunks[0]["source"] if chunks else "",
                quote=""
            )],
            confidence="LOW"
        )
