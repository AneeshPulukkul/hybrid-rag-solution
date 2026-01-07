from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from functools import lru_cache

from app.models.schemas import IndexStatus

router = APIRouter(prefix="/api/index", tags=["index"])


@lru_cache()
def get_retrieval_service():
    from app.services.retrieval_service import RetrievalService
    return RetrievalService()


indexing_status = {
    "raptor": {"status": "idle", "progress": 0},
    "graphrag": {"status": "idle", "progress": 0}
}


@router.get("/status", response_model=IndexStatus)
async def get_index_status(retrieval_service = Depends(get_retrieval_service)):
    try:
        return retrieval_service.get_index_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/raptor/build")
async def build_raptor_index(background_tasks: BackgroundTasks):
    if indexing_status["raptor"]["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="RAPTOR indexing is already in progress"
        )
    
    def run_indexing():
        indexing_status["raptor"]["status"] = "running"
        indexing_status["raptor"]["progress"] = 0
        try:
            svc = get_retrieval_service()
            result = svc.build_raptor_index()
            indexing_status["raptor"]["status"] = "completed"
            indexing_status["raptor"]["progress"] = 100
            indexing_status["raptor"]["result"] = result
        except Exception as e:
            indexing_status["raptor"]["status"] = "error"
            indexing_status["raptor"]["error"] = str(e)
    
    background_tasks.add_task(run_indexing)
    
    return {
        "status": "started",
        "message": "RAPTOR indexing started in background"
    }


@router.post("/raptor/build-sync")
async def build_raptor_index_sync(retrieval_service = Depends(get_retrieval_service)):
    try:
        result = retrieval_service.build_raptor_index()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raptor/status")
async def get_raptor_index_status():
    return indexing_status["raptor"]


@router.post("/graphrag/build")
async def build_graphrag_index(background_tasks: BackgroundTasks):
    if indexing_status["graphrag"]["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="GraphRAG indexing is already in progress"
        )
    
    def run_indexing():
        indexing_status["graphrag"]["status"] = "running"
        indexing_status["graphrag"]["progress"] = 0
        try:
            svc = get_retrieval_service()
            result = svc.build_graphrag_index()
            indexing_status["graphrag"]["status"] = "completed"
            indexing_status["graphrag"]["progress"] = 100
            indexing_status["graphrag"]["result"] = result
        except Exception as e:
            indexing_status["graphrag"]["status"] = "error"
            indexing_status["graphrag"]["error"] = str(e)
    
    background_tasks.add_task(run_indexing)
    
    return {
        "status": "started",
        "message": "GraphRAG indexing started in background"
    }


@router.post("/graphrag/build-sync")
async def build_graphrag_index_sync(retrieval_service = Depends(get_retrieval_service)):
    try:
        result = retrieval_service.build_graphrag_index()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graphrag/status")
async def get_graphrag_index_status():
    return indexing_status["graphrag"]


@router.post("/build-all")
async def build_all_indexes(background_tasks: BackgroundTasks):
    if indexing_status["raptor"]["status"] == "running" or indexing_status["graphrag"]["status"] == "running":
        raise HTTPException(
            status_code=409,
            detail="Indexing is already in progress"
        )
    
    def run_all_indexing():
        indexing_status["raptor"]["status"] = "running"
        indexing_status["graphrag"]["status"] = "running"
        
        svc = get_retrieval_service()
        
        try:
            raptor_result = svc.build_raptor_index()
            indexing_status["raptor"]["status"] = "completed"
            indexing_status["raptor"]["result"] = raptor_result
        except Exception as e:
            indexing_status["raptor"]["status"] = "error"
            indexing_status["raptor"]["error"] = str(e)
        
        try:
            graphrag_result = svc.build_graphrag_index()
            indexing_status["graphrag"]["status"] = "completed"
            indexing_status["graphrag"]["result"] = graphrag_result
        except Exception as e:
            indexing_status["graphrag"]["status"] = "error"
            indexing_status["graphrag"]["error"] = str(e)
    
    background_tasks.add_task(run_all_indexing)
    
    return {
        "status": "started",
        "message": "Both RAPTOR and GraphRAG indexing started in background"
    }


@router.post("/build-all-sync")
async def build_all_indexes_sync(retrieval_service = Depends(get_retrieval_service)):
    try:
        raptor_result = retrieval_service.build_raptor_index()
        graphrag_result = retrieval_service.build_graphrag_index()
        
        return {
            "raptor": raptor_result,
            "graphrag": graphrag_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
