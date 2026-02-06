"""
Rate Limiting Middleware

Implements rate limiting to prevent abuse and DoS attacks.
Uses Redis for distributed rate limiting across instances.
"""

import logging
import time
from typing import Optional

import redis
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from cloud_backend.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get Redis client for rate limiting."""
    global redis_client
    
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            redis_client.ping()
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            raise
    
    return redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Limits requests per IP address and endpoint to prevent abuse.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            requests_per_minute: Max requests per minute per IP
            requests_per_hour: Max requests per hour per IP
            burst_size: Max burst requests allowed
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        
        if endpoint.startswith("/health") or endpoint == "/metrics":
            return await call_next(request)
        
        try:
            redis_cli = get_redis_client()
            
            minute_key = f"rate_limit:minute:{client_ip}:{endpoint}"
            hour_key = f"rate_limit:hour:{client_ip}:{endpoint}"
            burst_key = f"rate_limit:burst:{client_ip}:{endpoint}"
            
            current_minute = int(time.time() / 60)
            current_hour = int(time.time() / 3600)
            
            minute_count = redis_cli.get(f"{minute_key}:{current_minute}")
            hour_count = redis_cli.get(f"{hour_key}:{current_hour}")
            burst_count = redis_cli.get(burst_key)
            
            if minute_count and int(minute_count) >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded (minute): {client_ip} on {endpoint}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "60"}
                )
            
            if hour_count and int(hour_count) >= self.requests_per_hour:
                logger.warning(f"Rate limit exceeded (hour): {client_ip} on {endpoint}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later.",
                    headers={"Retry-After": "3600"}
                )
            
            if burst_count and int(burst_count) >= self.burst_size:
                logger.warning(f"Burst limit exceeded: {client_ip} on {endpoint}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please slow down.",
                    headers={"Retry-After": "10"}
                )
            
            pipe = redis_cli.pipeline()
            pipe.incr(f"{minute_key}:{current_minute}")
            pipe.expire(f"{minute_key}:{current_minute}", 60)
            pipe.incr(f"{hour_key}:{current_hour}")
            pipe.expire(f"{hour_key}:{current_hour}", 3600)
            pipe.incr(burst_key)
            pipe.expire(burst_key, 1)
            pipe.execute()
        
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
        
        except HTTPException:
            raise
        
        except Exception as e:
            logger.error(f"Rate limiting error: {e}", exc_info=True)
        
        return await call_next(request)
