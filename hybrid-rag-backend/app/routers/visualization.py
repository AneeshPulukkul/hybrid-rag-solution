from fastapi import APIRouter, HTTPException, Depends
from functools import lru_cache

from app.models.schemas import GraphData, RaptorTreeData

router = APIRouter(prefix="/api/visualization", tags=["visualization"])


@lru_cache()
def get_retrieval_service():
    from app.services.retrieval_service import RetrievalService
    return RetrievalService()


@router.get("/graph", response_model=GraphData)
async def get_knowledge_graph(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_graph_data()
        return GraphData(nodes=data["nodes"], edges=data["edges"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/entities")
async def get_entities(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_graph_data()
        return {"entities": data["nodes"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/relationships")
async def get_relationships(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_graph_data()
        return {"relationships": data["edges"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/stats")
async def get_graph_stats(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_graph_data()
        
        entity_types = {}
        for node in data["nodes"]:
            entity_type = node.get("type", "Unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        relationship_types = {}
        for edge in data["edges"]:
            rel_type = edge.get("type", "Unknown")
            relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
        
        return {
            "total_entities": len(data["nodes"]),
            "total_relationships": len(data["edges"]),
            "entity_types": entity_types,
            "relationship_types": relationship_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raptor/tree", response_model=RaptorTreeData)
async def get_raptor_tree(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_raptor_tree()
        return RaptorTreeData(nodes=data["nodes"], levels=data["levels"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raptor/stats")
async def get_raptor_stats(retrieval_service = Depends(get_retrieval_service)):
    try:
        data = retrieval_service.get_raptor_tree()
        
        level_counts = {}
        for node in data["nodes"]:
            level = node.get("level", 0)
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_nodes": len(data["nodes"]),
            "total_levels": data["levels"],
            "nodes_per_level": level_counts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
