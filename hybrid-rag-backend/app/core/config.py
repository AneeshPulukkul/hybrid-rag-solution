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
    
    langfuse_secret_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
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
if settings.langfuse_secret_key and settings.langfuse_public_key:
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_host

    from langfuse import Langfuse
    langfuse_client = Langfuse()
else:
    langfuse_client = None


def get_langfuse_handler():
    """Return a Langfuse CallbackHandler for LangChain tracing, or None if not configured."""
    if langfuse_client is not None:
        from langfuse.langchain import CallbackHandler
        return CallbackHandler()
    return None
