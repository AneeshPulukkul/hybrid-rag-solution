import json
import uuid
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings, get_langfuse_handler
from app.core.database import get_db
from app.models.schemas import RaptorNode, Chunk


SUMMARIZATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert summarizer. Your task is to create a concise, comprehensive summary 
of the following text chunks that captures the main themes, key information, and important details.
The summary should be self-contained and understandable without the original text."""),
    ("human", """Please summarize the following text chunks into a single coherent summary:

{chunks}

Summary:""")
])


class RaptorService:
    def __init__(self):
        self._llm = None
        self._embeddings = None
        self._chroma_client = None
        self._raptor_collection = None
    
    @property
    def llm(self):
        if self._llm is None:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0
            )
        return self._llm
    
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
    def raptor_collection(self):
        if self._raptor_collection is None:
            self._raptor_collection = self.chroma_client.get_or_create_collection(
                name="raptor_nodes",
                metadata={"hnsw:space": "cosine"}
            )
        return self._raptor_collection
    
    @raptor_collection.setter
    def raptor_collection(self, value):
        self._raptor_collection = value
    
    def build_tree(self, chunks: list[Chunk]) -> dict:
        if not chunks:
            return {"levels": 0, "nodes": []}
        
        level_0_nodes = []
        for chunk in chunks:
            node = RaptorNode(
                id=str(uuid.uuid4()),
                level=0,
                content=chunk.content,
                summary=None,
                parent_id=None,
                children_ids=[],
                embedding_id=chunk.id
            )
            level_0_nodes.append(node)
            self._save_node(node)
        
        current_level_nodes = level_0_nodes
        all_nodes = list(level_0_nodes)
        current_level = 0
        
        while len(current_level_nodes) > 1 and current_level < settings.raptor_max_levels:
            current_level += 1
            
            embeddings = self._get_node_embeddings(current_level_nodes)
            
            clusters = self._cluster_nodes(embeddings, current_level_nodes)
            
            next_level_nodes = []
            for cluster_nodes in clusters:
                if len(cluster_nodes) == 1:
                    cluster_nodes[0].level = current_level
                    next_level_nodes.append(cluster_nodes[0])
                    continue
                
                combined_content = "\n\n---\n\n".join([
                    node.summary if node.summary else node.content 
                    for node in cluster_nodes
                ])
                
                summary = self._generate_summary(combined_content)
                
                parent_node = RaptorNode(
                    id=str(uuid.uuid4()),
                    level=current_level,
                    content=combined_content[:2000],
                    summary=summary,
                    parent_id=None,
                    children_ids=[n.id for n in cluster_nodes],
                    embedding_id=None
                )
                
                for child_node in cluster_nodes:
                    child_node.parent_id = parent_node.id
                    self._update_node(child_node)
                
                parent_embedding = self.embeddings.embed_query(summary)
                self.raptor_collection.add(
                    ids=[parent_node.id],
                    embeddings=[parent_embedding],
                    documents=[summary],
                    metadatas=[{"level": current_level, "type": "summary"}]
                )
                parent_node.embedding_id = parent_node.id
                
                self._save_node(parent_node)
                next_level_nodes.append(parent_node)
                all_nodes.append(parent_node)
            
            current_level_nodes = next_level_nodes
        
        return {
            "levels": current_level + 1,
            "nodes": [self._node_to_dict(n) for n in all_nodes]
        }
    
    def _get_node_embeddings(self, nodes: list[RaptorNode]):
        import numpy as np
        embeddings = []
        for node in nodes:
            text = node.summary if node.summary else node.content
            embedding = self.embeddings.embed_query(text)
            embeddings.append(embedding)
        return np.array(embeddings)
    
    def _cluster_nodes(self, embeddings, nodes: list[RaptorNode]) -> list[list[RaptorNode]]:
        if len(nodes) <= 2:
            return [nodes]
        
        from sklearn.cluster import AgglomerativeClustering
        
        n_clusters = max(2, len(nodes) // 3)
        n_clusters = min(n_clusters, len(nodes) - 1)
        
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric="cosine",
            linkage="average"
        )
        
        labels = clustering.fit_predict(embeddings)
        
        clusters: dict[int, list[RaptorNode]] = {}
        for idx, label in enumerate(labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(nodes[idx])
        
        return list(clusters.values())
    
    def _generate_summary(self, content: str) -> str:
        chain = SUMMARIZATION_PROMPT | self.llm
        callbacks = [h for h in [get_langfuse_handler()] if h is not None]
        response = chain.invoke({"chunks": content[:8000]}, config={"callbacks": callbacks})
        return response.content
    
    def _save_node(self, node: RaptorNode):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO raptor_nodes 
                   (id, level, content, summary, parent_id, children_ids, embedding_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    node.id,
                    node.level,
                    node.content,
                    node.summary,
                    node.parent_id,
                    json.dumps(node.children_ids),
                    node.embedding_id
                )
            )
            conn.commit()
    
    def _update_node(self, node: RaptorNode):
        self._save_node(node)
    
    def _node_to_dict(self, node: RaptorNode) -> dict:
        return {
            "id": node.id,
            "level": node.level,
            "content": node.content[:500] + "..." if len(node.content) > 500 else node.content,
            "summary": node.summary,
            "parent_id": node.parent_id,
            "children_ids": node.children_ids
        }
    
    def get_tree_data(self) -> dict:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM raptor_nodes ORDER BY level, id")
            rows = cursor.fetchall()
            
            if not rows:
                return {"nodes": [], "levels": 0}
            
            nodes = []
            max_level = 0
            for row in rows:
                max_level = max(max_level, row["level"])
                nodes.append({
                    "id": row["id"],
                    "level": row["level"],
                    "content": row["content"][:200] + "..." if len(row["content"]) > 200 else row["content"],
                    "summary": row["summary"],
                    "parent_id": row["parent_id"],
                    "children_ids": json.loads(row["children_ids"]) if row["children_ids"] else []
                })
            
            return {"nodes": nodes, "levels": max_level + 1}
    
    def retrieve_context(self, query: str, top_k: int = 5, mode: str = "collapsed") -> list[tuple[str, float]]:
        query_embedding = self.embeddings.embed_query(query)
        
        if mode == "collapsed":
            results = self.raptor_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )
        else:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(level) as max_level FROM raptor_nodes")
                row = cursor.fetchone()
                max_level = row["max_level"] if row and row["max_level"] else 0
            
            results = self.raptor_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"level": {"$gte": max_level - 1}},
                include=["documents", "distances", "metadatas"]
            )
        
        context_with_scores = []
        if results["ids"] and results["ids"][0]:
            for idx, doc in enumerate(results["documents"][0]):
                score = 1 - results["distances"][0][idx]
                context_with_scores.append((doc, score))
        
        return context_with_scores
    
    def clear_tree(self):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM raptor_nodes")
            conn.commit()
        
        try:
            self.chroma_client.delete_collection("raptor_nodes")
            self.raptor_collection = self.chroma_client.get_or_create_collection(
                name="raptor_nodes",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            pass
