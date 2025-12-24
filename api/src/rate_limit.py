"""Rate limiting middleware using token bucket algorithm."""
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """Token bucket rate limiter implementation.
    
    Uses the token bucket algorithm to limit request rates per client.
    """
    
    def __init__(self, rate: int, per: int) -> None:
        """Initialize rate limiter.
        
        Args:
            rate: Number of requests allowed
            per: Time window in seconds
        """
        self.rate = rate
        self.per = per
        self.buckets: dict[str, dict[str, float]] = defaultdict(
            lambda: {"tokens": rate, "last_update": time.time()}
        )
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique identifier for client.
        
        Args:
            request: HTTP request
            
        Returns:
            Client identifier (IP + User ID if available)
        """
        # Use IP address as base identifier
        client_ip = request.client.host if request.client else "unknown"
        
        # Add user ID if authenticated
        user_oid = getattr(request.state, "user_oid", None)
        if user_oid:
            return f"{client_ip}:{user_oid}"
        
        return client_ip
    
    def _refill_tokens(self, bucket: dict[str, float]) -> None:
        """Refill tokens based on elapsed time.
        
        Args:
            bucket: Token bucket for a client
        """
        now = time.time()
        elapsed = now - bucket["last_update"]
        
        # Calculate tokens to add based on elapsed time
        tokens_to_add = (elapsed / self.per) * self.rate
        bucket["tokens"] = min(self.rate, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now
    
    def is_allowed(self, request: Request) -> tuple[bool, dict[str, int | float]]:
        """Check if request is allowed under rate limit.
        
        Args:
            request: HTTP request
            
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        client_id = self._get_client_id(request)
        bucket = self.buckets[client_id]
        
        # Refill tokens
        self._refill_tokens(bucket)
        
        # Check if request is allowed
        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            allowed = True
        else:
            allowed = False
        
        # Calculate rate limit info
        retry_after = int((1 - bucket["tokens"]) * (self.per / self.rate))
        
        return allowed, {
            "limit": self.rate,
            "remaining": int(bucket["tokens"]),
            "reset": int(bucket["last_update"] + self.per),
            "retry_after": retry_after if not allowed else 0,
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limiting on API requests.
    
    Implements different rate limits for different endpoint types:
    - Authentication endpoints: Stricter limits
    - Read endpoints: Moderate limits
    - Write endpoints: Stricter limits
    """
    
    def __init__(self, app, default_rate: int = 100, default_per: int = 60) -> None:
        """Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            default_rate: Default requests per time window
            default_per: Default time window in seconds
        """
        super().__init__(app)
        
        # Different limiters for different endpoint types
        self.limiters = {
            "default": RateLimiter(rate=default_rate, per=default_per),
            "auth": RateLimiter(rate=10, per=60),  # 10 per minute
            "write": RateLimiter(rate=30, per=60),  # 30 per minute
            "read": RateLimiter(rate=100, per=60),  # 100 per minute
        }
    
    def _get_limiter_type(self, request: Request) -> str:
        """Determine which limiter to use based on request.
        
        Args:
            request: HTTP request
            
        Returns:
            Limiter type identifier
        """
        path = request.url.path
        method = request.method
        
        # Authentication endpoints
        if "login" in path or "callback" in path or "token" in path:
            return "auth"
        
        # Write operations
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return "write"
        
        # Read operations
        if method == "GET":
            return "read"
        
        return "default"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware in chain
            
        Returns:
            HTTP response
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/live", "/health/ready"]:
            return await call_next(request)
        
        # Get appropriate limiter
        limiter_type = self._get_limiter_type(request)
        limiter = self.limiters[limiter_type]
        
        # Check rate limit
        allowed, rate_info = limiter.is_allowed(request)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "retry_after": rate_info["retry_after"],
                    "limit": rate_info["limit"],
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(rate_info["reset"]),
                    "Retry-After": str(rate_info["retry_after"]),
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])
        
        return response
