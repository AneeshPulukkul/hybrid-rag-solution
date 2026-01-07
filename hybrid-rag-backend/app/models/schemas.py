from datetime import datetime
from enum import Enum
from typing import Optional, Any
from pydantic import BaseModel, Field


class QueryType(str, Enum):
    THEMATIC_HOLISTIC = "thematic_holistic"
    RELATIONAL_MULTIHOP = "relational_multihop"
    HYBRID = "hybrid"
    AUTO = "auto"


class DocumentCreate(BaseModel):
    filename: str
    content: str


class Document(BaseModel):
    id: str
    filename: str
    content_hash: str
    chunk_count: int = 0
    raptor_indexed: bool = False
    graphrag_indexed: bool = False
    created_at: datetime
    updated_at: datetime


class DocumentResponse(BaseModel):
    id: str
    filename: str
    chunk_count: int
    raptor_indexed: bool
    graphrag_indexed: bool
    created_at: datetime


class Chunk(BaseModel):
    id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Optional[dict[str, Any]] = None


class Entity(BaseModel):
    id: str
    name: str
    entity_type: str
    description: Optional[str] = None
    document_ids: list[str] = []


class Relationship(BaseModel):
    id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    description: Optional[str] = None
    weight: float = 1.0
    document_ids: list[str] = []


class RaptorNode(BaseModel):
    id: str
    level: int
    content: str
    summary: Optional[str] = None
    parent_id: Optional[str] = None
    children_ids: list[str] = []
    embedding_id: Optional[str] = None


class Community(BaseModel):
    id: str
    level: int
    entity_ids: list[str]
    summary: Optional[str] = None


class RetrievalSource(BaseModel):
    source_type: str
    content: str
    score: float
    metadata: Optional[dict[str, Any]] = None


class QueryRequest(BaseModel):
    query: str
    query_type: QueryType = QueryType.AUTO
    top_k: int = Field(default=5, ge=1, le=20)
    include_sources: bool = True


class QueryResponse(BaseModel):
    query: str
    query_type: QueryType
    answer: str
    sources: list[RetrievalSource] = []
    latency_ms: float
    raptor_context_used: bool = False
    graphrag_context_used: bool = False


class IndexStatus(BaseModel):
    total_documents: int
    raptor_indexed_documents: int
    graphrag_indexed_documents: int
    total_chunks: int
    total_entities: int
    total_relationships: int
    total_communities: int
    raptor_tree_levels: int


class GraphData(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class RaptorTreeData(BaseModel):
    nodes: list[dict[str, Any]]
    levels: int
