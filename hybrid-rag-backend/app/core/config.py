import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "Hybrid RAG Enterprise"
    app_version: str = "1.0.0"
    debug: bool = False
    
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    
    langchain_api_key: Optional[str] = None
    langchain_tracing_v2: bool = True
    langchain_project: str = "hybrid-rag-enterprise"
    
    database_url: str = "sqlite:///./data/hybrid_rag.db"
    chroma_persist_directory: str = "./data/chroma"
    graph_persist_directory: str = "./data/graph"
    raptor_persist_directory: str = "./data/raptor"
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    raptor_max_levels: int = 3
    raptor_cluster_threshold: float = 0.5
    raptor_summary_max_tokens: int = 500
    
    graphrag_entity_types_str: str = "PERSON,ORGANIZATION,LOCATION,EVENT,CONCEPT,PRODUCT,TECHNOLOGY"
    graphrag_max_triplets_per_chunk: int = 10
    
    cors_origins_str: str = "*"
    
    @property
    def graphrag_entity_types(self) -> list[str]:
        return [t.strip() for t in self.graphrag_entity_types_str.split(',') if t.strip()]
    
    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_str.split(',') if o.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()

if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.langchain_api_key:
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langchain_tracing_v2).lower()
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project
