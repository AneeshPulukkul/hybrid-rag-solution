import hashlib
import json
import uuid
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import Document, DocumentResponse, Chunk


class DocumentService:
    def __init__(self):
        self._text_splitter = None
        self._embeddings = None
        self._chroma_client = None
        self._collection = None
    
    @property
    def text_splitter(self):
        if self._text_splitter is None:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            self._text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        return self._text_splitter
    
    @property
    def embeddings(self):
        if self._embeddings is None:
            from langchain_openai import OpenAIEmbeddings
            self._embeddings = OpenAIEmbeddings(
                model=settings.openai_embedding_model
            )
        return self._embeddings
    
    @property
    def chroma_client(self):
        if self._chroma_client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._chroma_client = chromadb.PersistentClient(
                path=settings.chroma_persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
        return self._chroma_client
    
    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.chroma_client.get_or_create_collection(
                name="document_chunks",
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection
    
    def _compute_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()
    
    def ingest_document(self, filename: str, content: str) -> DocumentResponse:
        doc_id = str(uuid.uuid4())
        content_hash = self._compute_hash(content)
        
        chunks = self.text_splitter.split_text(content)
        chunk_count = len(chunks)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO documents (id, filename, content_hash, chunk_count)
                   VALUES (?, ?, ?, ?)""",
                (doc_id, filename, content_hash, chunk_count)
            )
            
            chunk_ids = []
            chunk_contents = []
            chunk_metadatas = []
            
            for idx, chunk_content in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                chunk_ids.append(chunk_id)
                chunk_contents.append(chunk_content)
                chunk_metadatas.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_index": idx
                })
                
                cursor.execute(
                    """INSERT INTO chunks (id, document_id, content, chunk_index, metadata)
                       VALUES (?, ?, ?, ?, ?)""",
                    (chunk_id, doc_id, chunk_content, idx, json.dumps(chunk_metadatas[-1]))
                )
            
            conn.commit()
        
        if chunk_ids:
            embeddings = self.embeddings.embed_documents(chunk_contents)
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_contents,
                metadatas=chunk_metadatas
            )
        
        return DocumentResponse(
            id=doc_id,
            filename=filename,
            chunk_count=chunk_count,
            raptor_indexed=False,
            graphrag_indexed=False,
            created_at=self._get_document(doc_id).created_at
        )
    
    def _get_document(self, doc_id: str) -> Document:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            if row:
                return Document(
                    id=row["id"],
                    filename=row["filename"],
                    content_hash=row["content_hash"],
                    chunk_count=row["chunk_count"],
                    raptor_indexed=bool(row["raptor_indexed"]),
                    graphrag_indexed=bool(row["graphrag_indexed"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"]
                )
            raise ValueError(f"Document {doc_id} not found")
    
    def get_all_documents(self) -> list[DocumentResponse]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                DocumentResponse(
                    id=row["id"],
                    filename=row["filename"],
                    chunk_count=row["chunk_count"],
                    raptor_indexed=bool(row["raptor_indexed"]),
                    graphrag_indexed=bool(row["graphrag_indexed"]),
                    created_at=row["created_at"]
                )
                for row in rows
            ]
    
    def get_document_chunks(self, doc_id: str) -> list[Chunk]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index",
                (doc_id,)
            )
            rows = cursor.fetchall()
            return [
                Chunk(
                    id=row["id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None
                )
                for row in rows
            ]
    
    def get_all_chunks(self) -> list[Chunk]:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks ORDER BY document_id, chunk_index")
            rows = cursor.fetchall()
            return [
                Chunk(
                    id=row["id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    chunk_index=row["chunk_index"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None
                )
                for row in rows
            ]
    
    def delete_document(self, doc_id: str) -> bool:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM chunks WHERE document_id = ?", (doc_id,))
            chunk_rows = cursor.fetchall()
            chunk_ids = [row["id"] for row in chunk_rows]
            
            if chunk_ids:
                try:
                    self.collection.delete(ids=chunk_ids)
                except Exception:
                    pass
            
            cursor.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            conn.commit()
            
            return True
    
    def search_similar_chunks(self, query: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
        query_embedding = self.embeddings.embed_query(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        chunks_with_scores = []
        if results["ids"] and results["ids"][0]:
            for idx, chunk_id in enumerate(results["ids"][0]):
                chunk = Chunk(
                    id=chunk_id,
                    document_id=results["metadatas"][0][idx].get("document_id", ""),
                    content=results["documents"][0][idx],
                    chunk_index=results["metadatas"][0][idx].get("chunk_index", 0),
                    metadata=results["metadatas"][0][idx]
                )
                score = 1 - results["distances"][0][idx]
                chunks_with_scores.append((chunk, score))
        
        return chunks_with_scores
    
    def update_document_index_status(self, doc_id: str, raptor_indexed: Optional[bool] = None, graphrag_indexed: Optional[bool] = None):
        with get_db() as conn:
            cursor = conn.cursor()
            updates = []
            params = []
            
            if raptor_indexed is not None:
                updates.append("raptor_indexed = ?")
                params.append(raptor_indexed)
            
            if graphrag_indexed is not None:
                updates.append("graphrag_indexed = ?")
                params.append(graphrag_indexed)
            
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(doc_id)
                cursor.execute(
                    f"UPDATE documents SET {', '.join(updates)} WHERE id = ?",
                    params
                )
                conn.commit()
