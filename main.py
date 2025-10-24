import os
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as redis
import uvicorn

app = FastAPI(title="Graphiti API")
redis_client = None

class IngestRequest(BaseModel):
    text: str
    metadata: dict = {}

@app.on_event("startup")
async def startup():
    global redis_client
    redis_url = os.getenv("REDIS_URL", "redis://graphiti-redis:6379")
    redis_client = await redis.from_url(redis_url, decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()

@app.get("/")
async def root():
    return {"service": "Graphiti API", "status": "running"}

@app.get("/health")
async def health():
    redis_status = "connected" if redis_client else "disconnected"
    return {"status": "healthy", "redis": redis_status}

@app.post("/ingest")
async def ingest(request: IngestRequest):
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis not connected")
    
    job = {
        "text": request.text,
        "metadata": request.metadata,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await redis_client.lpush("graphiti:jobs", json.dumps(job))
    
    return {"status": "queued", "job": job}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)    
