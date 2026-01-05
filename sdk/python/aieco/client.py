"""
AIEco Python SDK
Simple, intuitive SDK for the AIEco API
"""

from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx
import json


class AIEcoClient:
    """
    AIEco API Client
    
    Example:
        client = AIEcoClient(api_key="your-key")
        
        # Chat
        response = client.chat("Hello!")
        
        # Streaming
        for chunk in client.chat_stream("Tell me a story"):
            print(chunk, end="")
        
        # RAG
        results = client.rag_query("How does auth work?")
        
        # Agents
        result = client.run_agent("code", "Write a sorting function")
    """
    
    def __init__(
        self,
        api_key: str = None,
        base_url: str = "http://localhost:8080",
        model: str = "glm-4.7"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._get_headers(),
            timeout=120.0
        )
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    # ===== Chat =====
    
    def chat(
        self,
        message: str,
        system: str = None,
        history: List[Dict] = None,
        **kwargs
    ) -> str:
        """Send a chat message and get a response"""
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": message})
        
        response = self._client.post(
            "/api/v1/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                **kwargs
            }
        )
        response.raise_for_status()
        
        return response.json()["choices"][0]["message"]["content"]
    
    def chat_stream(
        self,
        message: str,
        system: str = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream a chat response"""
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": message})
        
        with self._client.stream(
            "POST",
            "/api/v1/chat/completions",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                **kwargs
            }
        ) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    
    # ===== RAG =====
    
    def rag_query(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 5,
        generate_answer: bool = True
    ) -> Dict[str, Any]:
        """Query documents using RAG"""
        response = self._client.post(
            "/api/v1/rag/query",
            json={
                "query": query,
                "collection": collection,
                "top_k": top_k,
                "generate_answer": generate_answer
            }
        )
        response.raise_for_status()
        return response.json()
    
    def rag_upload(
        self,
        file_path: str,
        collection: str = "default"
    ) -> Dict[str, Any]:
        """Upload a document for RAG"""
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = self._client.post(
                "/api/v1/rag/documents/upload",
                files=files,
                params={"collection": collection}
            )
        response.raise_for_status()
        return response.json()
    
    # ===== Agents =====
    
    def run_agent(
        self,
        agent: str,
        task: str,
        context: Dict = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """Run an AI agent"""
        response = self._client.post(
            "/api/v1/agents/run",
            json={
                "agent": agent,
                "task": task,
                "context": context or {},
                "max_iterations": max_iterations,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json()
    
    def list_agents(self) -> List[Dict]:
        """List available agents"""
        response = self._client.get("/api/v1/agents/list")
        response.raise_for_status()
        return response.json()
    
    # ===== Skills =====
    
    def list_skills(self) -> List[Dict]:
        """List available skills"""
        response = self._client.get("/api/v1/skills/list")
        response.raise_for_status()
        return response.json()
    
    def activate_skill(self, skill_name: str) -> Dict:
        """Activate a skill"""
        response = self._client.post(
            "/api/v1/skills/activate",
            json={"skill_name": skill_name}
        )
        response.raise_for_status()
        return response.json()
    
    # ===== MCP Tools =====
    
    def execute_tool(
        self,
        tool: str,
        parameters: Dict = None
    ) -> Dict[str, Any]:
        """Execute an MCP tool"""
        response = self._client.post(
            "/api/v1/mcp/execute",
            json={
                "tool": tool,
                "parameters": parameters or {}
            }
        )
        response.raise_for_status()
        return response.json()
    
    def list_tools(self) -> List[Dict]:
        """List available MCP tools"""
        response = self._client.get("/api/v1/mcp/tools")
        response.raise_for_status()
        return response.json()
    
    # ===== Models =====
    
    def list_models(self) -> List[Dict]:
        """List available models"""
        response = self._client.get("/api/v1/models")
        response.raise_for_status()
        return response.json().get("data", [])
    
    # ===== Cleanup =====
    
    def close(self):
        """Close the client"""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()


# Convenience function
def create_client(api_key: str = None, base_url: str = None) -> AIEcoClient:
    """Create an AIEco client"""
    return AIEcoClient(
        api_key=api_key,
        base_url=base_url or "http://localhost:8080"
    )
