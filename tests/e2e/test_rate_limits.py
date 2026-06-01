import os
os.environ["TEST__LIGHTHOUSE"] = "False"

import pytest
import httpx
from src.config.settings import settings
from main import app

pytestmark = pytest.mark.asyncio

@pytest.fixture
async def rate_limited_client():
    # Store original
    original_lighthouse = settings.TEST.LIGHTHOUSE
    
    # Disable lighthouse bypass so rate limiters are active
    settings.TEST.LIGHTHOUSE = False
    
    transport = httpx.ASGITransport(app=app)
    
    import redis.asyncio as redis
    from fastapi_limiter import FastAPILimiter
    
    redis_conn = redis.from_url("redis://localhost:6379/0", encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_conn)
    
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as transport_client:
        yield transport_client
        
    await redis_conn.aclose()
            
    # Restore
    settings.TEST.LIGHTHOUSE = original_lighthouse

async def test_rate_limits_triggered(rate_limited_client):
    """Test that making too many requests triggers a 429 Too Many Requests response."""
    # /login has limiter(60, 60) in main.py
    
    responses = []
    # Sending 65 requests
    for _ in range(65):
        responses.append(await rate_limited_client.get("/login"))
    
    status_codes = [r.status_code for r in responses]
    for r in responses:
        if r.status_code == 500:
            raise RuntimeError(f"500 Error: {r.text}")
                
    # At least some should be 429
    assert 429 in status_codes, f"Rate limit was not triggered. Statuses: {set(status_codes)}"
