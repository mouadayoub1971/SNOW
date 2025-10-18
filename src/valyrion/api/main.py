"""
FastAPI Application for Valyrion RAG System
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import time
import logging

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Valyrion API",
    description="Dragon-powered Financial Research Agent with RAG",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class QueryRequest(BaseModel):
    """Query request model"""

    query: str = Field(..., description="User query")
    filters: Optional[Dict] = Field(None, description="Filters (company, date range, etc.)")
    max_results: Optional[int] = Field(10, description="Maximum number of results")


class Source(BaseModel):
    """Source document model"""

    document_id: str
    document_type: str
    company: str
    date: str
    excerpt: str
    score: float


class QueryResponse(BaseModel):
    """Query response model"""

    answer: str = Field(..., description="Generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source documents")
    confidence: float = Field(..., description="Confidence score (0-1)")
    latency_ms: int = Field(..., description="Query latency in milliseconds")


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()

    response = await call_next(request)

    latency = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {latency:.2f}ms"
    )

    return response


# Routes
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Valyrion API - Dragon-powered Financial Research",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Main query endpoint

    Process user query using RAG and multi-agent system
    """
    start_time = time.time()

    try:
        # TODO: Implement full RAG pipeline
        # 1. Query understanding
        # 2. Hybrid retrieval
        # 3. Re-ranking
        # 4. Agent processing
        # 5. Answer generation

        # Placeholder response
        answer = f"Processed query: {request.query}"
        sources = []
        confidence = 0.85

        latency_ms = int((time.time() - start_time) * 1000)

        return QueryResponse(
            answer=answer, sources=sources, confidence=confidence, latency_ms=latency_ms
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint (placeholder)
    """
    return {
        "queries_total": 0,
        "queries_success": 0,
        "queries_error": 0,
        "avg_latency_ms": 0,
    }


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
