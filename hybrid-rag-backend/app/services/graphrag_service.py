import json
import uuid
from typing import Optional
from collections import defaultdict

from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings
from app.core.database import get_db
from app.models.schemas import Entity, Relationship, Community, Chunk


ENTITY_EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at extracting entities and relationships from text.
Extract entities of the following types: {entity_types}

For each entity, provide:
- name: The entity name
- type: One of the allowed types
- description: A brief description

For each relationship, provide:
- source: Source entity name
- target: Target entity name  
- type: Relationship type (e.g., WORKS_FOR, LOCATED_IN, RELATED_TO, PART_OF, etc.)
- description: Brief description of the relationship

Return your response as JSON with two arrays: "entities" and "relationships"."""),
    ("human", """Extract entities and relationships from the following text:

{text}

Return as JSON:""")
])

COMMUNITY_SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at summarizing information about groups of related entities.
Create a comprehensive summary that captures the key themes, relationships, and important facts about this community of entities."""),
    ("human", """Summarize the following community of entities and their relationships:

Entities:
{entities}

Relationships:
{relationships}

Community Summary:""")
])


class GraphRAGService:
    def __init__(self):
        self._llm = None
        self._embeddings = None
        self._chroma_client = None
        self._entity_collection = None
        self._community_collection = None
        self._graph = None
        self._graph_loaded = False
    
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
    def entity_collection(self):
        if self._entity_collection is None:
            self._entity_collection = self.chroma_client.get_or_create_collection(
                name="entities",
                metadata={"hnsw:space": "cosine"}
            )
        return self._entity_collection
    
    @entity_collection.setter
    def entity_collection(self, value):
        self._entity_collection = value
    
    @property
    def community_collection(self):
        if self._community_collection is None:
            self._community_collection = self.chroma_client.get_or_create_collection(
                name="communities",
                metadata={"hnsw:space": "cosine"}
            )
        return self._community_collection
    
    @community_collection.setter
    def community_collection(self, value):
        self._community_collection = value
    
    @property
    def graph(self):
        if self._graph is None:
            import networkx as nx
            self._graph = nx.Graph()
            if not self._graph_loaded:
                self._load_graph()
                self._graph_loaded = True
        return self._graph
    
    def _load_graph(self):
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM entities")
            for row in cursor.fetchall():
                self.graph.add_node(
                    row["id"],
                    name=row["name"],
                    entity_type=row["entity_type"],
                    description=row["description"]
                )
            
            cursor.execute("SELECT * FROM relationships")
            for row in cursor.fetchall():
                self.graph.add_edge(
                    row["source_entity_id"],
                    row["target_entity_id"],
                    id=row["id"],
                    relationship_type=row["relationship_type"],
                    description=row["description"],
                    weight=row["weight"]
                )
    
    def extract_and_index(self, chunks: list[Chunk]) -> dict:
        all_entities: dict[str, Entity] = {}
        all_relationships: list[Relationship] = []
        
        for chunk in chunks:
            entities, relationships = self._extract_from_chunk(chunk)
            
            for entity in entities:
                key = f"{entity.name.lower()}_{entity.entity_type}"
                if key in all_entities:
                    existing = all_entities[key]
                    existing.document_ids = list(set(existing.document_ids + entity.document_ids))
                else:
                    all_entities[key] = entity
            
            all_relationships.extend(relationships)
        
        for entity in all_entities.values():
            self._save_entity(entity)
            self.graph.add_node(
                entity.id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description
            )
            
            if entity.description:
                embedding = self.embeddings.embed_query(f"{entity.name}: {entity.description}")
                self.entity_collection.add(
                    ids=[entity.id],
                    embeddings=[embedding],
                    documents=[f"{entity.name}: {entity.description}"],
                    metadatas=[{"name": entity.name, "type": entity.entity_type}]
                )
        
        entity_name_to_id = {e.name.lower(): e.id for e in all_entities.values()}
        
        for rel in all_relationships:
            source_id = entity_name_to_id.get(rel.source_entity_id.lower())
            target_id = entity_name_to_id.get(rel.target_entity_id.lower())
            
            if source_id and target_id:
                rel.source_entity_id = source_id
                rel.target_entity_id = target_id
                self._save_relationship(rel)
                self.graph.add_edge(
                    source_id,
                    target_id,
                    id=rel.id,
                    relationship_type=rel.relationship_type,
                    description=rel.description,
                    weight=rel.weight
                )
        
        communities = self._detect_communities()
        for community in communities:
            self._save_community(community)
            
            if community.summary:
                embedding = self.embeddings.embed_query(community.summary)
                self.community_collection.add(
                    ids=[community.id],
                    embeddings=[embedding],
                    documents=[community.summary],
                    metadatas=[{"level": community.level}]
                )
        
        return {
            "entities_count": len(all_entities),
            "relationships_count": len(all_relationships),
            "communities_count": len(communities)
        }
    
    def _extract_from_chunk(self, chunk: Chunk) -> tuple[list[Entity], list[Relationship]]:
        chain = ENTITY_EXTRACTION_PROMPT | self.llm
        
        try:
            response = chain.invoke({
                "entity_types": ", ".join(settings.graphrag_entity_types),
                "text": chunk.content
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            
            entities = []
            for e in data.get("entities", [])[:settings.graphrag_max_triplets_per_chunk]:
                entity = Entity(
                    id=str(uuid.uuid4()),
                    name=e.get("name", ""),
                    entity_type=e.get("type", "CONCEPT"),
                    description=e.get("description", ""),
                    document_ids=[chunk.document_id]
                )
                if entity.name:
                    entities.append(entity)
            
            relationships = []
            for r in data.get("relationships", [])[:settings.graphrag_max_triplets_per_chunk]:
                rel = Relationship(
                    id=str(uuid.uuid4()),
                    source_entity_id=r.get("source", ""),
                    target_entity_id=r.get("target", ""),
                    relationship_type=r.get("type", "RELATED_TO"),
                    description=r.get("description", ""),
                    document_ids=[chunk.document_id]
                )
                if rel.source_entity_id and rel.target_entity_id:
                    relationships.append(rel)
            
            return entities, relationships
            
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return [], []
    
    def _detect_communities(self) -> list[Community]:
        if len(self.graph.nodes()) == 0:
            return []
        
        communities = []
        
        try:
            from networkx.algorithms.community import louvain_communities
            detected = louvain_communities(self.graph, resolution=1.0)
        except Exception:
            if len(self.graph.nodes()) > 0:
                detected = [set(self.graph.nodes())]
            else:
                detected = []
        
        for idx, community_nodes in enumerate(detected):
            if len(community_nodes) < 2:
                continue
            
            entity_ids = list(community_nodes)
            
            entities_info = []
            for node_id in entity_ids[:10]:
                if node_id in self.graph.nodes:
                    node_data = self.graph.nodes[node_id]
                    entities_info.append(f"- {node_data.get('name', 'Unknown')} ({node_data.get('entity_type', 'Unknown')}): {node_data.get('description', 'No description')}")
            
            relationships_info = []
            subgraph = self.graph.subgraph(entity_ids)
            for u, v, data in list(subgraph.edges(data=True))[:10]:
                source_name = self.graph.nodes[u].get('name', 'Unknown')
                target_name = self.graph.nodes[v].get('name', 'Unknown')
                rel_type = data.get('relationship_type', 'RELATED_TO')
                relationships_info.append(f"- {source_name} --[{rel_type}]--> {target_name}")
            
            summary = self._generate_community_summary(
                "\n".join(entities_info),
                "\n".join(relationships_info)
            )
            
            community = Community(
                id=str(uuid.uuid4()),
                level=0,
                entity_ids=entity_ids,
                summary=summary
            )
            communities.append(community)
        
        return communities
    
    def _generate_community_summary(self, entities: str, relationships: str) -> str:
        if not entities:
            return "Empty community"
        
        chain = COMMUNITY_SUMMARY_PROMPT | self.llm
        response = chain.invoke({
            "entities": entities,
            "relationships": relationships or "No relationships"
        })
        return response.content
    
    def _save_entity(self, entity: Entity):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO entities 
                   (id, name, entity_type, description, document_ids)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    entity.id,
                    entity.name,
                    entity.entity_type,
                    entity.description,
                    json.dumps(entity.document_ids)
                )
            )
            conn.commit()
    
    def _save_relationship(self, rel: Relationship):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO relationships 
                   (id, source_entity_id, target_entity_id, relationship_type, description, weight, document_ids)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    rel.id,
                    rel.source_entity_id,
                    rel.target_entity_id,
                    rel.relationship_type,
                    rel.description,
                    rel.weight,
                    json.dumps(rel.document_ids)
                )
            )
            conn.commit()
    
    def _save_community(self, community: Community):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO communities 
                   (id, level, entity_ids, summary)
                   VALUES (?, ?, ?, ?)""",
                (
                    community.id,
                    community.level,
                    json.dumps(community.entity_ids),
                    community.summary
                )
            )
            conn.commit()
    
    def get_graph_data(self) -> dict:
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "name": data.get("name", "Unknown"),
                "type": data.get("entity_type", "Unknown"),
                "description": data.get("description", "")
            })
        
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "type": data.get("relationship_type", "RELATED_TO"),
                "description": data.get("description", "")
            })
        
        return {"nodes": nodes, "edges": edges}
    
    def retrieve_context(self, query: str, top_k: int = 5, mode: str = "local") -> list[tuple[str, float]]:
        query_embedding = self.embeddings.embed_query(query)
        
        context_with_scores = []
        
        if mode in ["local", "hybrid"]:
            entity_results = self.entity_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "distances", "metadatas"]
            )
            
            if entity_results["ids"] and entity_results["ids"][0]:
                for idx, entity_id in enumerate(entity_results["ids"][0]):
                    score = 1 - entity_results["distances"][0][idx]
                    doc = entity_results["documents"][0][idx]
                    
                    if entity_id in self.graph.nodes:
                        neighbors = list(self.graph.neighbors(entity_id))[:3]
                        neighbor_info = []
                        for n in neighbors:
                            n_data = self.graph.nodes[n]
                            edge_data = self.graph.edges.get((entity_id, n), {})
                            rel_type = edge_data.get("relationship_type", "RELATED_TO")
                            neighbor_info.append(f"{n_data.get('name', 'Unknown')} ({rel_type})")
                        
                        if neighbor_info:
                            doc += f"\nRelated entities: {', '.join(neighbor_info)}"
                    
                    context_with_scores.append((doc, score))
        
        if mode in ["global", "hybrid"]:
            community_results = self.community_collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, 3),
                include=["documents", "distances"]
            )
            
            if community_results["ids"] and community_results["ids"][0]:
                for idx, doc in enumerate(community_results["documents"][0]):
                    score = 1 - community_results["distances"][0][idx]
                    context_with_scores.append((f"[Community Summary] {doc}", score * 0.9))
        
        context_with_scores.sort(key=lambda x: x[1], reverse=True)
        return context_with_scores[:top_k]
    
    def clear_graph(self):
        self.graph.clear()
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM entities")
            cursor.execute("DELETE FROM relationships")
            cursor.execute("DELETE FROM communities")
            conn.commit()
        
        try:
            self.chroma_client.delete_collection("entities")
            self.chroma_client.delete_collection("communities")
            self.entity_collection = self.chroma_client.get_or_create_collection(
                name="entities",
                metadata={"hnsw:space": "cosine"}
            )
            self.community_collection = self.chroma_client.get_or_create_collection(
                name="communities",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            pass
