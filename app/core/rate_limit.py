import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status, Depends
from app.core.config import get_settings

settings = get_settings()

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()

    def allow(self, cost: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        refill = elapsed * self.refill_rate
        if refill > 0:
            self.tokens = min(self.capacity, self.tokens + refill)
            self.last_refill = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

class InMemoryStore:
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}

    def get_bucket(self, key: str, capacity: int, window: int) -> TokenBucket:
        rate = capacity / float(window)
        bucket = self.buckets.get(key)
        if bucket is None or bucket.capacity != capacity or bucket.refill_rate != rate:
            bucket = TokenBucket(capacity, rate)
            self.buckets[key] = bucket
        return bucket

store = InMemoryStore()

def rate_limit(bucket_id: str, limit: int, window: int):
    async def dependency(request: Request):
        uid = getattr(request.state, "user_id", None)
        ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown").split(",")[0].strip()
        suffix = str(uid) if uid is not None else ip
        key = f"{bucket_id}:{suffix}"
        bucket = store.get_bucket(key, limit, window)
        if not bucket.allow(1):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    return dependency
