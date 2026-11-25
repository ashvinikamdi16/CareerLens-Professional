from fastapi import HTTPException, Request
from redis import Redis
from redis.exceptions import RedisError
from backend.app.core.config import settings

# Shared Redis counter applies consistently across API processes and containers.
redis_client = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)

_FIXED_WINDOW_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return count
"""

def apply_rate_limit(scope: str, identity: str, limit: int, window_seconds: int = 3600) -> None:
    key = f"careerlens:ratelimit:{scope}:{identity}"
    try:
        count = int(redis_client.eval(_FIXED_WINDOW_SCRIPT, 1, key, window_seconds))
    except RedisError as exc:
        # Fail closed: public endpoints must not become unthrottled if Redis is unavailable.
        raise HTTPException(status_code=503, detail="Upload protection is temporarily unavailable. Please try again later.") from exc
    if count > limit:
        raise HTTPException(status_code=429, detail="Upload limit reached. Please try again later.")

def get_client_ip(request: Request) -> str:
    # In the included public deployment, Caddy is the trusted reverse proxy and
    # appends the client address to X-Forwarded-For. Use the right-most entry.
    # Do not expose the API directly when relying on this header for rate limiting.
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[-1].strip() if forwarded else (request.client.host if request.client else "unknown")
    return ip or "unknown"

def limit_guest_analysis(request: Request) -> None:
    apply_rate_limit("guest-analysis", get_client_ip(request), limit=settings.guest_uploads_per_hour, window_seconds=3600)
