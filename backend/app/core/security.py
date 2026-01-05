"""
AIEco - Security Middleware & Utilities
Rate limiting, input validation, request encryption
"""

import time
import hashlib
import hmac
from typing import Dict, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.config import settings

logger = structlog.get_logger()


class RateLimiter:
    """
    Token bucket rate limiter with per-user and per-API-key limits.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        tokens_per_minute: int = 100000
    ):
        self.rpm = requests_per_minute
        self.tpm = tokens_per_minute
        self._request_counts: Dict[str, list] = defaultdict(list)
        self._token_counts: Dict[str, int] = defaultdict(int)
        self._last_reset: Dict[str, datetime] = {}
    
    def _get_key(self, request: Request) -> str:
        """Get rate limit key from request"""
        # Try API key first
        api_key = request.headers.get(settings.api_key_header)
        if api_key:
            return f"api_key:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def check_rate_limit(self, request: Request) -> tuple[bool, Dict]:
        """Check if request is within rate limits"""
        key = self._get_key(request)
        now = datetime.utcnow()
        
        # Reset if new minute
        if key not in self._last_reset or (now - self._last_reset[key]).seconds >= 60:
            self._request_counts[key] = []
            self._token_counts[key] = 0
            self._last_reset[key] = now
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        self._request_counts[key] = [
            t for t in self._request_counts[key] 
            if t > minute_ago
        ]
        
        # Check request rate
        if len(self._request_counts[key]) >= self.rpm:
            return False, {
                "error": "Rate limit exceeded",
                "type": "requests",
                "limit": self.rpm,
                "reset_in": 60 - (now - self._last_reset[key]).seconds
            }
        
        # Add request
        self._request_counts[key].append(now)
        
        return True, {
            "remaining_requests": self.rpm - len(self._request_counts[key]),
            "remaining_tokens": self.tpm - self._token_counts[key]
        }
    
    def add_tokens(self, request: Request, tokens: int):
        """Add tokens used by a request"""
        key = self._get_key(request)
        self._token_counts[key] += tokens


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, limiter: RateLimiter = None):
        super().__init__(app)
        self.limiter = limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/ready", "/metrics"]:
            return await call_next(request)
        
        allowed, info = self.limiter.check_rate_limit(request)
        
        if not allowed:
            logger.warning("Rate limit exceeded", path=request.url.path, **info)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": info["error"], "retry_after": info["reset_in"]},
                headers={"Retry-After": str(info["reset_in"])}
            )
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(info["remaining_requests"])
        
        return response


class InputValidator:
    """Validate and sanitize user inputs"""
    
    # Dangerous patterns to block
    BLOCKED_PATTERNS = [
        "ignore previous instructions",
        "ignore all previous",
        "disregard previous",
        "forget your instructions",
        "you are now",
        "act as if",
        "<script>",
        "javascript:",
        "eval(",
        "exec(",
        "__import__",
    ]
    
    @classmethod
    def validate_message(cls, content: str) -> tuple[bool, Optional[str]]:
        """Validate a message for injection attempts"""
        content_lower = content.lower()
        
        for pattern in cls.BLOCKED_PATTERNS:
            if pattern in content_lower:
                return False, f"Blocked pattern detected: {pattern[:20]}..."
        
        # Check for excessive length
        if len(content) > 1_000_000:  # 1M chars
            return False, "Message too long"
        
        return True, None
    
    @classmethod
    def sanitize_message(cls, content: str) -> str:
        """Sanitize a message (remove dangerous patterns)"""
        for pattern in cls.BLOCKED_PATTERNS:
            content = content.replace(pattern, "[REDACTED]")
        return content


class RequestSigner:
    """Sign requests for integrity verification"""
    
    def __init__(self, secret_key: str = None):
        self.secret = (secret_key or settings.jwt_secret_key).encode()
    
    def sign_request(self, payload: str, timestamp: int = None) -> str:
        """Generate HMAC signature for payload"""
        timestamp = timestamp or int(time.time())
        message = f"{timestamp}:{payload}".encode()
        signature = hmac.new(self.secret, message, hashlib.sha256).hexdigest()
        return f"{timestamp}.{signature}"
    
    def verify_signature(
        self,
        payload: str,
        signature: str,
        max_age: int = 300
    ) -> bool:
        """Verify request signature"""
        try:
            timestamp_str, sig = signature.split(".")
            timestamp = int(timestamp_str)
            
            # Check timestamp freshness
            if abs(time.time() - timestamp) > max_age:
                return False
            
            # Verify signature
            expected = self.sign_request(payload, timestamp).split(".")[1]
            return hmac.compare_digest(sig, expected)
            
        except Exception:
            return False


# Audit logging
class AuditLogger:
    """Log security-relevant events"""
    
    @staticmethod
    def log_auth_attempt(
        email: str,
        success: bool,
        ip: str,
        details: str = None
    ):
        """Log authentication attempt"""
        logger.info(
            "🔐 Auth attempt",
            email=email,
            success=success,
            ip=ip,
            details=details,
            event_type="auth"
        )
    
    @staticmethod
    def log_api_access(
        user_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        tokens_used: int = 0
    ):
        """Log API access"""
        logger.info(
            "📡 API access",
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            tokens_used=tokens_used,
            event_type="api_access"
        )
    
    @staticmethod
    def log_security_event(
        event_type: str,
        details: Dict,
        severity: str = "warning"
    ):
        """Log security event"""
        log_func = getattr(logger, severity, logger.warning)
        log_func(
            f"⚠️ Security event: {event_type}",
            **details,
            event_type="security"
        )


# Global instances
rate_limiter = RateLimiter(
    requests_per_minute=settings.rate_limit_per_minute,
    tokens_per_minute=100000
)
input_validator = InputValidator()
audit_logger = AuditLogger()
