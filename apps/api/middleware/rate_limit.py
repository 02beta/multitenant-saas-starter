"""Rate Limiting Middleware for FastAPI."""

import time
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import hashlib

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    For production use, consider using Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        auth_endpoints_per_minute: int = 10,  # Stricter for auth endpoints
        ban_duration_seconds: int = 300,  # 5 minutes ban for violations
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.auth_endpoints_per_minute = auth_endpoints_per_minute
        self.ban_duration = ban_duration_seconds
        
        # Storage: {client_id: deque of timestamps}
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.banned_clients: Dict[str, float] = {}  # {client_id: ban_expiry_time}
        
        # Auth endpoint patterns
        self.auth_endpoints = [
            "/v1/auth/login",
            "/v1/auth/signup",
            "/v1/auth/forgot-password",
            "/v1/auth/reset-password"
        ]
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier from request."""
        # Use IP address + User-Agent for identification
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        user_agent = request.headers.get("User-Agent", "")
        
        # Create hash for privacy
        client_string = f"{client_ip}:{user_agent}"
        return hashlib.sha256(client_string.encode()).hexdigest()[:16]
    
    def _is_auth_endpoint(self, path: str) -> bool:
        """Check if the path is an authentication endpoint."""
        return any(path.startswith(endpoint) for endpoint in self.auth_endpoints)
    
    def _clean_old_requests(self, timestamps: Deque[float], current_time: float):
        """Remove timestamps older than 1 hour."""
        cutoff_time = current_time - 3600  # 1 hour ago
        while timestamps and timestamps[0] < cutoff_time:
            timestamps.popleft()
    
    def _check_rate_limit(
        self, 
        timestamps: Deque[float], 
        current_time: float,
        is_auth: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if rate limit is exceeded.
        Returns (is_allowed, error_message)
        """
        # Clean old timestamps
        self._clean_old_requests(timestamps, current_time)
        
        # Count requests in different time windows
        one_minute_ago = current_time - 60
        requests_in_minute = sum(1 for t in timestamps if t > one_minute_ago)
        
        # Check auth endpoint limits
        if is_auth:
            if requests_in_minute >= self.auth_endpoints_per_minute:
                return False, f"Rate limit exceeded: {self.auth_endpoints_per_minute} auth requests per minute"
        
        # Check general limits
        if requests_in_minute >= self.requests_per_minute:
            return False, f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
        
        if len(timestamps) >= self.requests_per_hour:
            return False, f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
        
        return True, None
    
    def _check_banned(self, client_id: str, current_time: float) -> bool:
        """Check if client is banned."""
        if client_id in self.banned_clients:
            if current_time < self.banned_clients[client_id]:
                return True
            else:
                # Ban expired, remove from list
                del self.banned_clients[client_id]
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/"]:
            return await call_next(request)
        
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Check if client is banned
        if self._check_banned(client_id, current_time):
            remaining_ban = int(self.banned_clients[client_id] - current_time)
            logger.warning(f"Banned client {client_id} attempted request to {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Banned for {remaining_ban} seconds.",
                headers={
                    "Retry-After": str(remaining_ban),
                    "X-RateLimit-Limit": "0",
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Get client's request history
        timestamps = self.requests[client_id]
        is_auth = self._is_auth_endpoint(request.url.path)
        
        # Check rate limit
        is_allowed, error_msg = self._check_rate_limit(timestamps, current_time, is_auth)
        
        if not is_allowed:
            # Ban the client for repeated violations
            if is_auth:
                # Stricter ban for auth endpoint abuse
                self.banned_clients[client_id] = current_time + self.ban_duration * 2
                logger.warning(
                    f"Client {client_id} banned for auth endpoint abuse: {request.url.path}"
                )
            else:
                self.banned_clients[client_id] = current_time + self.ban_duration
                logger.warning(f"Client {client_id} banned for rate limit violation")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg,
                headers={
                    "Retry-After": str(self.ban_duration),
                    "X-RateLimit-Limit": str(
                        self.auth_endpoints_per_minute if is_auth 
                        else self.requests_per_minute
                    ),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Record the request
        timestamps.append(current_time)
        
        # Calculate remaining requests
        one_minute_ago = current_time - 60
        requests_in_minute = sum(1 for t in timestamps if t > one_minute_ago)
        
        if is_auth:
            remaining = self.auth_endpoints_per_minute - requests_in_minute
            limit = self.auth_endpoints_per_minute
        else:
            remaining = self.requests_per_minute - requests_in_minute
            limit = self.requests_per_minute
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response


class RedisRateLimiter:
    """
    Redis-based rate limiter for production use.
    This is a placeholder for a more robust implementation.
    """
    
    def __init__(
        self,
        redis_client,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    async def check_rate_limit(self, client_id: str) -> Tuple[bool, int]:
        """
        Check rate limit using Redis.
        Returns (is_allowed, remaining_requests)
        """
        # Implementation would use Redis INCR with TTL
        # or sliding window with Redis sorted sets
        pass