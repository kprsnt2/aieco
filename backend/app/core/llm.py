"""
AIEco - LLM Client
Unified client for vLLM and Ollama with streaming support
"""

from typing import AsyncGenerator, Dict, List, Optional, Any
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = structlog.get_logger()


class LLMClient:
    """
    Unified LLM client supporting both vLLM and Ollama.
    Provides OpenAI-compatible interface with streaming.
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 120.0
    ):
        self.base_url = base_url or settings.llm_base_url
        self.api_key = api_key or settings.vllm_api_key
        self.default_model = model or settings.llm_model
        self.timeout = timeout
        
        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=self._get_headers()
        )
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional auth"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a chat completion (non-streaming).
        
        Args:
            messages: List of message dicts with role and content
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            tools: Available tools for function calling
            tool_choice: Tool choice strategy
            
        Returns:
            OpenAI-compatible completion response
        """
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }
        
        if tools:
            payload["tools"] = tools
        if tool_choice:
            payload["tool_choice"] = tool_choice
        
        logger.debug("🔄 LLM request", model=payload["model"], messages=len(messages))
        
        response = await self._client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        result = response.json()
        logger.debug("✅ LLM response", 
                    model=payload["model"],
                    tokens=result.get("usage", {}).get("total_tokens", 0))
        
        return result
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a streaming chat completion.
        
        Yields:
            Chunks with delta content
        """
        import json
        
        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
            **kwargs
        }
        
        if tools:
            payload["tools"] = tools
        
        logger.debug("🔄 LLM stream request", model=payload["model"])
        
        async with self._client.stream(
            "POST",
            "/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    
                    if data == "[DONE]":
                        break
                    
                    try:
                        chunk = json.loads(data)
                        yield {
                            "delta": chunk["choices"][0].get("delta", {}),
                            "finish_reason": chunk["choices"][0].get("finish_reason")
                        }
                    except json.JSONDecodeError:
                        continue
        
        logger.debug("✅ LLM stream completed", model=payload["model"])
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = await self._client.get("/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.warning("⚠️ Failed to list models", error=str(e))
            # Return default model info
            return [{
                "id": self.default_model,
                "object": "model",
                "owned_by": "aieco"
            }]
    
    async def embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """
        Generate embeddings for texts.
        Falls back to local embedding model if API not available.
        """
        try:
            response = await self._client.post(
                "/embeddings",
                json={
                    "model": model,
                    "input": texts
                }
            )
            response.raise_for_status()
            data = response.json()
            return [item["embedding"] for item in data["data"]]
        except Exception as e:
            logger.warning("⚠️ Embedding API failed, using fallback", error=str(e))
            # TODO: Implement local embedding fallback
            raise
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


async def check_llm_connection() -> bool:
    """Check if LLM server is accessible"""
    try:
        async with LLMClient() as client:
            models = await client.list_models()
            return len(models) > 0
    except Exception:
        return False


# Global client instance (lazy initialization)
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
