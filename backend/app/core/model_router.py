"""
AIEco - Multi-Model Router
Intelligent routing between GLM-4.7 and MiniMax M2.1
"""

from typing import Dict, List, Optional
from enum import Enum
import httpx
import structlog

logger = structlog.get_logger()


class ModelType(Enum):
    """Available models in the AIEco cluster"""
    GLM_47 = "glm-4.7"           # Best for coding, reasoning, 1M context
    MINIMAX_M21 = "minimax-m2.1" # Best for fast inference, 200K context


class ModelConfig:
    """Model configuration and capabilities"""
    MODELS = {
        "glm-4.7": {
            "endpoint": "http://localhost:8000/v1",
            "max_context": 1048576,  # 1M tokens
            "strengths": ["coding", "reasoning", "long_context", "tool_calling"],
            "speed": "medium",
            "cost_weight": 1.0
        },
        "minimax-m2.1": {
            "endpoint": "http://localhost:8001/v1",
            "max_context": 204800,  # 200K tokens
            "strengths": ["fast", "general", "conversation", "creative"],
            "speed": "fast",
            "cost_weight": 0.8
        }
    }
    
    # Aliases for model names
    ALIASES = {
        "glm": "glm-4.7",
        "glm4": "glm-4.7",
        "minimax": "minimax-m2.1",
        "m2": "minimax-m2.1",
        "fast": "minimax-m2.1",
        "coding": "glm-4.7"
    }


class ModelRouter:
    """
    Intelligent model router for multi-model AIEco cluster.
    
    Routes requests to the optimal model based on:
    - Task type (coding vs conversation)
    - Context length requirements
    - Speed requirements
    - User preferences
    """
    
    def __init__(self):
        self.models = ModelConfig.MODELS
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """Initialize HTTP clients for each model"""
        for model_name, config in self.models.items():
            self.clients[model_name] = httpx.AsyncClient(
                base_url=config["endpoint"],
                timeout=300.0
            )
    
    def resolve_model(self, model_name: str) -> str:
        """Resolve model name from alias"""
        model_name = model_name.lower().strip()
        return ModelConfig.ALIASES.get(model_name, model_name)
    
    def select_model(
        self,
        task_type: str = None,
        context_length: int = 0,
        prefer_speed: bool = False,
        preferred_model: str = None
    ) -> str:
        """
        Select the optimal model for a request.
        
        Args:
            task_type: Type of task (coding, reasoning, conversation, etc.)
            context_length: Required context length in tokens
            prefer_speed: Prefer faster inference over quality
            preferred_model: User-specified model preference
        
        Returns:
            Model name to use
        """
        # If user specifies a model, use it
        if preferred_model:
            resolved = self.resolve_model(preferred_model)
            if resolved in self.models:
                return resolved
        
        # Route based on context length first
        if context_length > 200000:
            logger.info("Routing to GLM-4.7 for long context", context_length=context_length)
            return "glm-4.7"
        
        # Route based on task type
        if task_type in ["coding", "code", "programming", "debug", "reasoning"]:
            return "glm-4.7"
        
        if task_type in ["chat", "conversation", "creative", "writing"]:
            return "minimax-m2.1"
        
        # If speed is preferred, use MiniMax
        if prefer_speed:
            return "minimax-m2.1"
        
        # Default to GLM-4.7 for best quality
        return "glm-4.7"
    
    async def route_request(
        self,
        messages: List[Dict],
        model: str = None,
        **kwargs
    ) -> Dict:
        """
        Route a chat completion request to the appropriate model.
        """
        # Estimate context length
        context_length = sum(len(msg.get("content", "")) for msg in messages) // 4
        
        # Detect task type from messages
        task_type = self._detect_task_type(messages)
        
        # Select model
        selected_model = self.select_model(
            task_type=task_type,
            context_length=context_length,
            prefer_speed=kwargs.pop("prefer_speed", False),
            preferred_model=model
        )
        
        logger.info(
            "Routing request",
            selected_model=selected_model,
            task_type=task_type,
            context_estimate=context_length
        )
        
        # Make request to selected model
        client = self.clients.get(selected_model)
        if not client:
            raise ValueError(f"Model {selected_model} not available")
        
        response = await client.post(
            "/chat/completions",
            json={
                "model": selected_model,
                "messages": messages,
                **kwargs
            }
        )
        response.raise_for_status()
        
        result = response.json()
        result["_routed_to"] = selected_model
        return result
    
    def _detect_task_type(self, messages: List[Dict]) -> str:
        """Detect task type from messages"""
        last_message = messages[-1].get("content", "").lower() if messages else ""
        
        # Coding keywords
        coding_keywords = [
            "code", "function", "class", "debug", "error", "bug",
            "python", "javascript", "typescript", "implement", "algorithm",
            "def ", "import ", "const ", "let ", "var "
        ]
        
        if any(kw in last_message for kw in coding_keywords):
            return "coding"
        
        # Creative/writing keywords
        creative_keywords = [
            "write", "story", "creative", "poem", "essay",
            "describe", "imagine", "create a"
        ]
        
        if any(kw in last_message for kw in creative_keywords):
            return "creative"
        
        return "general"
    
    async def get_model_status(self) -> Dict:
        """Get status of all models"""
        status = {}
        for model_name, config in self.models.items():
            try:
                client = self.clients.get(model_name)
                response = await client.get("/health")
                status[model_name] = {
                    "healthy": response.status_code == 200,
                    "endpoint": config["endpoint"],
                    "max_context": config["max_context"],
                    "strengths": config["strengths"]
                }
            except Exception as e:
                status[model_name] = {
                    "healthy": False,
                    "error": str(e)
                }
        return status
    
    async def close(self):
        """Close all clients"""
        for client in self.clients.values():
            await client.aclose()


# Global router instance
_router: Optional[ModelRouter] = None


def get_model_router() -> ModelRouter:
    """Get or create the model router"""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
