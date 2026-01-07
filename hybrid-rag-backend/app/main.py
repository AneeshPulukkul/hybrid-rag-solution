from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routers import (
    documents_router,
    query_router,
    index_router,
    visualization_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Hybrid RAG Enterprise Solution combining RAPTOR and GraphRAG",
    lifespan=lifespan
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(documents_router)
app.include_router(query_router)
app.include_router(index_router)
app.include_router(visualization_router)


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Hybrid RAG Enterprise Solution combining RAPTOR and GraphRAG",
        "endpoints": {
            "documents": "/api/documents",
            "query": "/api/query",
            "index": "/api/index",
            "visualization": "/api/visualization"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    return {"status": "ready"}


@app.get("/live")
async def live():
    return {"status": "live"}
