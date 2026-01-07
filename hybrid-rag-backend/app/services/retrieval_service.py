from typing import Optional
import time

from app.core.database import get_db
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    QueryType,
    RetrievalSource,
    IndexStatus
)


class RetrievalService:
    def __init__(self):
        self._document_service = None
        self._raptor_service = None
        self._graphrag_service = None
        self._query_router = None
    
    @property
    def document_service(self):
        if self._document_service is None:
            from .document_service import DocumentService
            self._document_service = DocumentService()
        return self._document_service
    
    @property
    def raptor_service(self):
        if self._raptor_service is None:
            from .raptor_service import RaptorService
            self._raptor_service = RaptorService()
        return self._raptor_service
    
    @property
    def graphrag_service(self):
        if self._graphrag_service is None:
            from .graphrag_service import GraphRAGService
            self._graphrag_service = GraphRAGService()
        return self._graphrag_service
    
    @property
    def query_router(self):
        if self._query_router is None:
            from .query_router import QueryRouter
            self._query_router = QueryRouter(
                self.raptor_service,
                self.graphrag_service,
                self.document_service
            )
        return self._query_router
    
    def query(self, request: QueryRequest) -> QueryResponse:
        start_time = time.time()
        
        query_type_str = request.query_type.value if request.query_type != QueryType.AUTO else "auto"
        
        result = self.query_router.route_and_answer(
            query=request.query,
            query_type=query_type_str,
            top_k=request.top_k
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        sources = []
        if request.include_sources:
            for source in result.get("sources", []):
                sources.append(RetrievalSource(
                    source_type=source["source_type"],
                    content=source["content"],
                    score=source["score"],
                    metadata=source.get("metadata")
                ))
        
        detected_type = result.get("query_type", "hybrid")
        if detected_type == QueryType.THEMATIC_HOLISTIC.value:
            query_type = QueryType.THEMATIC_HOLISTIC
        elif detected_type == QueryType.RELATIONAL_MULTIHOP.value:
            query_type = QueryType.RELATIONAL_MULTIHOP
        else:
            query_type = QueryType.HYBRID
        
        raptor_used = any(s.source_type == "raptor" for s in sources)
        graphrag_used = any(s.source_type == "graphrag" for s in sources)
        
        self._save_query_history(
            query=request.query,
            query_type=query_type.value,
            response=result.get("answer", ""),
            sources=sources,
            latency_ms=latency_ms
        )
        
        return QueryResponse(
            query=request.query,
            query_type=query_type,
            answer=result.get("answer", "No answer generated"),
            sources=sources,
            latency_ms=latency_ms,
            raptor_context_used=raptor_used,
            graphrag_context_used=graphrag_used
        )
    
    def _save_query_history(
        self,
        query: str,
        query_type: str,
        response: str,
        sources: list[RetrievalSource],
        latency_ms: float
    ):
        import uuid
        import json
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO query_history 
                   (id, query, query_type, response, retrieval_sources, latency_ms)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    str(uuid.uuid4()),
                    query,
                    query_type,
                    response,
                    json.dumps([s.model_dump() for s in sources]),
                    latency_ms
                )
            )
            conn.commit()
    
    def get_index_status(self) -> IndexStatus:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM documents")
            total_documents = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE raptor_indexed = 1")
            raptor_indexed = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE graphrag_indexed = 1")
            graphrag_indexed = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM chunks")
            total_chunks = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM entities")
            total_entities = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM relationships")
            total_relationships = cursor.fetchone()["count"]
            
            cursor.execute("SELECT COUNT(*) as count FROM communities")
            total_communities = cursor.fetchone()["count"]
            
            cursor.execute("SELECT MAX(level) as max_level FROM raptor_nodes")
            row = cursor.fetchone()
            raptor_levels = (row["max_level"] or 0) + 1 if row["max_level"] is not None else 0
        
        return IndexStatus(
            total_documents=total_documents,
            raptor_indexed_documents=raptor_indexed,
            graphrag_indexed_documents=graphrag_indexed,
            total_chunks=total_chunks,
            total_entities=total_entities,
            total_relationships=total_relationships,
            total_communities=total_communities,
            raptor_tree_levels=raptor_levels
        )
    
    def build_raptor_index(self) -> dict:
        chunks = self.document_service.get_all_chunks()
        
        if not chunks:
            return {"status": "error", "message": "No chunks to index"}
        
        self.raptor_service.clear_tree()
        
        result = self.raptor_service.build_tree(chunks)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET raptor_indexed = 1, updated_at = CURRENT_TIMESTAMP")
            conn.commit()
        
        return {
            "status": "success",
            "levels": result["levels"],
            "nodes_created": len(result["nodes"])
        }
    
    def build_graphrag_index(self) -> dict:
        chunks = self.document_service.get_all_chunks()
        
        if not chunks:
            return {"status": "error", "message": "No chunks to index"}
        
        self.graphrag_service.clear_graph()
        
        result = self.graphrag_service.extract_and_index(chunks)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE documents SET graphrag_indexed = 1, updated_at = CURRENT_TIMESTAMP")
            conn.commit()
        
        return {
            "status": "success",
            "entities_count": result["entities_count"],
            "relationships_count": result["relationships_count"],
            "communities_count": result["communities_count"]
        }
    
    def get_graph_data(self) -> dict:
        return self.graphrag_service.get_graph_data()
    
    def get_raptor_tree(self) -> dict:
        return self.raptor_service.get_tree_data()
