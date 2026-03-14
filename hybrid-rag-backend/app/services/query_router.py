from typing import TypedDict, Literal, Annotated
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.core.config import settings, get_langfuse_handler
from app.models.schemas import QueryType


QUERY_CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at classifying user queries to determine the best retrieval strategy.

Classify the query into one of these categories:

1. THEMATIC_HOLISTIC - Use when the query:
   - Asks about themes, concepts, or high-level summaries
   - Requires understanding across multiple document sections
   - Asks "what is this about", "summarize", "main themes"
   - Needs multi-step reasoning about document content
   - Examples: "What are the main themes?", "Summarize the key points", "What is the overall message?"

2. RELATIONAL_MULTIHOP - Use when the query:
   - Asks about specific entities (people, organizations, places)
   - Requires understanding relationships between entities
   - Asks "who", "what organization", "how are X and Y related"
   - Needs multi-hop reasoning across entity relationships
   - Examples: "Who works with John?", "What companies are mentioned?", "How is X related to Y?"

3. HYBRID - Use when the query:
   - Combines both thematic and relational aspects
   - Needs both high-level understanding and specific entity information
   - Examples: "What role does Company X play in the main themes?", "How do the key people relate to the main concepts?"

Respond with ONLY the category name: THEMATIC_HOLISTIC, RELATIONAL_MULTIHOP, or HYBRID"""),
    ("human", "Classify this query: {query}")
])


class QueryState(TypedDict):
    query: str
    query_type: str
    raptor_context: list[tuple[str, float]]
    graphrag_context: list[tuple[str, float]]
    combined_context: str
    answer: str
    sources: list[dict]
    error: str | None


class QueryRouter:
    def __init__(self, raptor_service, graphrag_service, document_service):
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0
        )
        self.raptor_service = raptor_service
        self.graphrag_service = graphrag_service
        self.document_service = document_service
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(QueryState)
        
        workflow.add_node("classify_query", self._classify_query)
        workflow.add_node("retrieve_raptor", self._retrieve_raptor)
        workflow.add_node("retrieve_graphrag", self._retrieve_graphrag)
        workflow.add_node("retrieve_hybrid", self._retrieve_hybrid)
        workflow.add_node("fuse_context", self._fuse_context)
        workflow.add_node("generate_answer", self._generate_answer)
        
        workflow.set_entry_point("classify_query")
        
        workflow.add_conditional_edges(
            "classify_query",
            self._route_by_query_type,
            {
                "raptor": "retrieve_raptor",
                "graphrag": "retrieve_graphrag",
                "hybrid": "retrieve_hybrid"
            }
        )
        
        workflow.add_edge("retrieve_raptor", "fuse_context")
        workflow.add_edge("retrieve_graphrag", "fuse_context")
        workflow.add_edge("retrieve_hybrid", "fuse_context")
        workflow.add_edge("fuse_context", "generate_answer")
        workflow.add_edge("generate_answer", END)
        
        return workflow.compile()
    
    def _classify_query(self, state: QueryState) -> QueryState:
        if state.get("query_type") and state["query_type"] != "auto":
            return state
        
        chain = QUERY_CLASSIFICATION_PROMPT | self.llm
        callbacks = [h for h in [get_langfuse_handler()] if h is not None]
        response = chain.invoke({"query": state["query"]}, config={"callbacks": callbacks})
        
        classification = response.content.strip().upper()
        
        if "THEMATIC" in classification or "HOLISTIC" in classification:
            state["query_type"] = QueryType.THEMATIC_HOLISTIC.value
        elif "RELATIONAL" in classification or "MULTIHOP" in classification:
            state["query_type"] = QueryType.RELATIONAL_MULTIHOP.value
        else:
            state["query_type"] = QueryType.HYBRID.value
        
        return state
    
    def _route_by_query_type(self, state: QueryState) -> str:
        query_type = state.get("query_type", "hybrid")
        
        if query_type == QueryType.THEMATIC_HOLISTIC.value:
            return "raptor"
        elif query_type == QueryType.RELATIONAL_MULTIHOP.value:
            return "graphrag"
        else:
            return "hybrid"
    
    def _retrieve_raptor(self, state: QueryState) -> QueryState:
        try:
            context = self.raptor_service.retrieve_context(
                state["query"],
                top_k=5,
                mode="collapsed"
            )
            state["raptor_context"] = context
        except Exception as e:
            state["raptor_context"] = []
            state["error"] = f"RAPTOR retrieval error: {str(e)}"
        
        return state
    
    def _retrieve_graphrag(self, state: QueryState) -> QueryState:
        try:
            context = self.graphrag_service.retrieve_context(
                state["query"],
                top_k=5,
                mode="local"
            )
            state["graphrag_context"] = context
        except Exception as e:
            state["graphrag_context"] = []
            state["error"] = f"GraphRAG retrieval error: {str(e)}"
        
        return state
    
    def _retrieve_hybrid(self, state: QueryState) -> QueryState:
        state = self._retrieve_raptor(state)
        state = self._retrieve_graphrag(state)
        return state
    
    def _fuse_context(self, state: QueryState) -> QueryState:
        all_context = []
        sources = []
        
        raptor_context = state.get("raptor_context", [])
        for content, score in raptor_context:
            all_context.append((content, score, "raptor"))
            sources.append({
                "source_type": "raptor",
                "content": content[:500],
                "score": score
            })
        
        graphrag_context = state.get("graphrag_context", [])
        for content, score in graphrag_context:
            all_context.append((content, score, "graphrag"))
            sources.append({
                "source_type": "graphrag",
                "content": content[:500],
                "score": score
            })
        
        if not all_context:
            chunks = self.document_service.search_similar_chunks(state["query"], top_k=5)
            for chunk, score in chunks:
                all_context.append((chunk.content, score, "vector"))
                sources.append({
                    "source_type": "vector",
                    "content": chunk.content[:500],
                    "score": score
                })
        
        all_context.sort(key=lambda x: x[1], reverse=True)
        
        combined = []
        seen = set()
        for content, score, source_type in all_context[:10]:
            content_key = content[:100]
            if content_key not in seen:
                seen.add(content_key)
                combined.append(f"[{source_type.upper()}] {content}")
        
        state["combined_context"] = "\n\n---\n\n".join(combined)
        state["sources"] = sources
        
        return state
    
    def _generate_answer(self, state: QueryState) -> QueryState:
        generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that answers questions based on the provided context.
Use the context to provide accurate, well-structured answers.
If the context doesn't contain enough information, say so clearly.
Always cite which parts of the context support your answer."""),
            ("human", """Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above:""")
        ])
        
        chain = generation_prompt | self.llm
        
        try:
            callbacks = [h for h in [get_langfuse_handler()] if h is not None]
            response = chain.invoke({
                "context": state["combined_context"] or "No context available.",
                "query": state["query"]
            }, config={"callbacks": callbacks})
            state["answer"] = response.content
        except Exception as e:
            state["answer"] = f"Error generating answer: {str(e)}"
            state["error"] = str(e)
        
        return state
    
    def route_and_answer(self, query: str, query_type: str = "auto", top_k: int = 5) -> QueryState:
        initial_state: QueryState = {
            "query": query,
            "query_type": query_type if query_type != "auto" else "",
            "raptor_context": [],
            "graphrag_context": [],
            "combined_context": "",
            "answer": "",
            "sources": [],
            "error": None
        }
        
        callbacks = [h for h in [get_langfuse_handler()] if h is not None]
        result = self.graph.invoke(initial_state, config={"callbacks": callbacks})
        return result
    
    def classify_query_type(self, query: str) -> QueryType:
        chain = QUERY_CLASSIFICATION_PROMPT | self.llm
        callbacks = [h for h in [get_langfuse_handler()] if h is not None]
        response = chain.invoke({"query": query}, config={"callbacks": callbacks})
        
        classification = response.content.strip().upper()
        
        if "THEMATIC" in classification or "HOLISTIC" in classification:
            return QueryType.THEMATIC_HOLISTIC
        elif "RELATIONAL" in classification or "MULTIHOP" in classification:
            return QueryType.RELATIONAL_MULTIHOP
        else:
            return QueryType.HYBRID
