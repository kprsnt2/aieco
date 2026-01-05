"""
AIEco - Prompt Caching
Save 90% on repeated contexts like Anthropic's prompt caching
"""

import hashlib
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class PromptCache:
    """
    Intelligent prompt caching system.
    
    Caches:
    - System prompts
    - Repeated context blocks
    - Skill instructions
    - RAG results
    
    Savings: Up to 90% on input tokens for repeated contexts.
    """
    
    def __init__(self, redis_client=None, ttl_minutes: int = 60):
        self.redis = redis_client
        self.ttl = timedelta(minutes=ttl_minutes)
        self._local_cache: Dict[str, Dict] = {}
        self._stats = {"hits": 0, "misses": 0, "tokens_saved": 0}
    
    def get_cache_key(
        self,
        messages: List[Dict],
        model: str,
        prefix_length: int = None
    ) -> str:
        """Generate cache key for a message prefix"""
        # Only cache system messages and stable context
        cacheable = []
        for msg in messages:
            if msg.get("role") in ["system", "assistant"]:
                cacheable.append(msg)
            elif msg.get("cache", False):
                cacheable.append(msg)
        
        if not cacheable:
            return None
        
        content = json.dumps(cacheable, sort_keys=True)
        hash_input = f"{model}:{content}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    async def get_cached_prefix(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached prefix embedding/KV cache reference"""
        if not cache_key:
            return None
        
        # Try Redis first
        if self.redis:
            try:
                cached = await self.redis.get(f"prompt_cache:{cache_key}")
                if cached:
                    self._stats["hits"] += 1
                    data = json.loads(cached)
                    self._stats["tokens_saved"] += data.get("token_count", 0)
                    logger.debug("🎯 Cache hit", key=cache_key[:16])
                    return data
            except Exception as e:
                logger.warning("Cache get failed", error=str(e))
        
        # Fallback to local cache
        if cache_key in self._local_cache:
            self._stats["hits"] += 1
            return self._local_cache[cache_key]
        
        self._stats["misses"] += 1
        return None
    
    async def set_cached_prefix(
        self,
        cache_key: str,
        data: Dict[str, Any],
        token_count: int = 0
    ):
        """Cache a prefix for future use"""
        if not cache_key:
            return
        
        cache_data = {
            **data,
            "token_count": token_count,
            "cached_at": datetime.utcnow().isoformat()
        }
        
        # Store in Redis
        if self.redis:
            try:
                await self.redis.setex(
                    f"prompt_cache:{cache_key}",
                    int(self.ttl.total_seconds()),
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning("Cache set failed", error=str(e))
        
        # Also store locally
        self._local_cache[cache_key] = cache_data
        
        # Limit local cache size
        if len(self._local_cache) > 1000:
            # Remove oldest entries
            oldest = sorted(
                self._local_cache.items(),
                key=lambda x: x[1].get("cached_at", "")
            )[:100]
            for key, _ in oldest:
                del self._local_cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        # Estimate cost savings (assuming $3/M input tokens)
        tokens_saved = self._stats["tokens_saved"]
        cost_saved = (tokens_saved / 1_000_000) * 3.0 * 0.9  # 90% discount
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": f"{hit_rate:.1%}",
            "tokens_saved": tokens_saved,
            "estimated_cost_saved": f"${cost_saved:.2f}"
        }
    
    async def invalidate(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            # Invalidate matching keys
            if self.redis:
                keys = await self.redis.keys(f"prompt_cache:{pattern}*")
                if keys:
                    await self.redis.delete(*keys)
            self._local_cache = {
                k: v for k, v in self._local_cache.items()
                if not k.startswith(pattern)
            }
        else:
            # Clear all
            if self.redis:
                keys = await self.redis.keys("prompt_cache:*")
                if keys:
                    await self.redis.delete(*keys)
            self._local_cache.clear()
        
        self._stats = {"hits": 0, "misses": 0, "tokens_saved": 0}


# Helper functions
def generate_cache_key(messages: List[Dict], model: str) -> str:
    """Generate a cache key for messages"""
    content = json.dumps(messages, sort_keys=True)
    return hashlib.sha256(f"{model}:{content}".encode()).hexdigest()


def mark_cacheable(message: Dict) -> Dict:
    """Mark a message as cacheable"""
    return {**message, "cache": True}


# Global instance
_prompt_cache: Optional[PromptCache] = None


def get_prompt_cache() -> PromptCache:
    """Get or create prompt cache instance"""
    global _prompt_cache
    if _prompt_cache is None:
        _prompt_cache = PromptCache()
    return _prompt_cache
