from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
from functools import lru_cache

from app.models.schemas import QueryRequest, QueryResponse, QueryType

router = APIRouter(prefix="/api/query", tags=["query"])


@lru_cache()
def get_retrieval_service():
    from app.services.retrieval_service import RetrievalService
    return RetrievalService()


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest, retrieval_service = Depends(get_retrieval_service)):
    try:
        result = retrieval_service.query(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def query_stream(request: QueryRequest, retrieval_service = Depends(get_retrieval_service)):
    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield json.dumps({"type": "start", "query": request.query}) + "\n"
            
            query_type = retrieval_service.query_router.classify_query_type(request.query)
            yield json.dumps({
                "type": "classification",
                "query_type": query_type.value
            }) + "\n"
            
            yield json.dumps({"type": "retrieving", "message": "Retrieving context..."}) + "\n"
            
            result = retrieval_service.query(request)
            
            yield json.dumps({
                "type": "sources",
                "sources": [s.model_dump() for s in result.sources]
            }) + "\n"
            
            yield json.dumps({
                "type": "answer",
                "answer": result.answer,
                "query_type": result.query_type.value,
                "latency_ms": result.latency_ms,
                "raptor_context_used": result.raptor_context_used,
                "graphrag_context_used": result.graphrag_context_used
            }) + "\n"
            
            yield json.dumps({"type": "end"}) + "\n"
            
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson"
    )


@router.get("/history")
async def get_query_history(limit: int = 50):
    from app.core.database import get_db
    
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, query, query_type, response, latency_ms, created_at 
                   FROM query_history 
                   ORDER BY created_at DESC 
                   LIMIT ?""",
                (limit,)
            )
            rows = cursor.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "query": row["query"],
                    "query_type": row["query_type"],
                    "response": row["response"][:500] + "..." if len(row["response"] or "") > 500 else row["response"],
                    "latency_ms": row["latency_ms"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/classify")
async def classify_query(query: str, retrieval_service = Depends(get_retrieval_service)):
    try:
        query_type = retrieval_service.query_router.classify_query_type(query)
        return {
            "query": query,
            "query_type": query_type.value,
            "description": _get_query_type_description(query_type)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _get_query_type_description(query_type: QueryType) -> str:
    descriptions = {
        QueryType.THEMATIC_HOLISTIC: "This query is best answered using RAPTOR's hierarchical summaries for thematic understanding.",
        QueryType.RELATIONAL_MULTIHOP: "This query is best answered using GraphRAG's knowledge graph for entity relationships.",
        QueryType.HYBRID: "This query benefits from both RAPTOR summaries and GraphRAG entity relationships.",
        QueryType.AUTO: "Query type will be automatically determined."
    }
    return descriptions.get(query_type, "Unknown query type")
