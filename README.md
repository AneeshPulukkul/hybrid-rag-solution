# Hybrid RAG Enterprise

A production-ready Hybrid Retrieval Augmented Generation system combining **RAPTOR** (Recursive Abstractive Processing for Tree-Organized Retrieval) and **GraphRAG** (Knowledge Graph-based RAG) with modern agentic AI standards.

## Overview

This enterprise solution provides intelligent document retrieval and question answering by combining two complementary RAG approaches:

- **RAPTOR**: Builds hierarchical summary trees for complex thematic questions and multi-step reasoning across document sections
- **GraphRAG**: Extracts entities and relationships to build knowledge graphs for multi-hop reasoning and relationship-centric queries

### Key Features

- **Intelligent Query Routing**: LangGraph-based router automatically classifies queries and routes to the optimal retrieval strategy
- **AG-UI Protocol**: Real-time streaming responses with standardized agent-to-UI communication
- **Langfuse Observability**: Full tracing, monitoring, and evaluation capabilities
- **Cloud-Native Architecture**: Docker containerization and Kubernetes manifests for deployment across AWS, Azure, GCP, or on-premises

## Architecture

```
                                    +------------------+
                                    |   React Frontend |
                                    |   (AG-UI Client) |
                                    +--------+---------+
                                             |
                                             v
+------------------+              +----------+----------+
|   Langfuse       |<------------>|   FastAPI Backend   |
|   Observability  |              |                     |
+------------------+              +----------+----------+
                                             |
                    +------------------------+------------------------+
                    |                        |                        |
                    v                        v                        v
           +--------+--------+      +--------+--------+      +--------+--------+
           |  Query Router   |      |  Document       |      |  Retrieval      |
           |  (LangGraph)    |      |  Service        |      |  Service        |
           +-----------------+      +-----------------+      +-----------------+
                    |                        |                        |
        +-----------+-----------+            |            +-----------+-----------+
        |                       |            |            |                       |
        v                       v            v            v                       v
+-------+-------+       +-------+-------+  +-+--+  +------+------+       +-------+-------+
| RAPTOR        |       | GraphRAG      |  |    |  | RAPTOR      |       | GraphRAG      |
| Service       |       | Service       |  |    |  | Retrieval   |       | Retrieval     |
| (Tree Build)  |       | (KG Build)    |  |    |  |             |       |               |
+-------+-------+       +-------+-------+  |    |  +-------------+       +---------------+
        |                       |          |    |
        v                       v          v    v
+-------+-------+       +-------+-------+  +----+----+
| ChromaDB      |       | NetworkX      |  | SQLite  |
| (Embeddings)  |       | (Graph)       |  | (Data)  |
+---------------+       +---------------+  +---------+
```

## Component Details

### Query Types

| Query Type | Best For | RAG Strategy |
|------------|----------|--------------|
| **Thematic/Holistic** | Summarization, main themes, high-level understanding | RAPTOR |
| **Relational/Multi-hop** | Entity relationships, "who/what" questions, multi-hop reasoning | GraphRAG |
| **Hybrid** | Complex queries requiring both approaches | Combined |

### Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI (Python) |
| Frontend Framework | React + TypeScript + Vite |
| UI Components | shadcn/ui + Tailwind CSS |
| Orchestration | LangGraph |
| Observability | Langfuse |
| Vector Store | ChromaDB |
| Graph Store | NetworkX |
| Database | SQLite |
| LLM Provider | OpenAI |
| Containerization | Docker |
| Orchestration | Kubernetes |

## Project Structure

```
hybrid-rag-enterprise/
├── hybrid-rag-backend/          # FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── core/
│   │   │   ├── config.py        # Configuration settings
│   │   │   └── database.py      # SQLite database setup
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── routers/
│   │   │   ├── documents.py     # Document management endpoints
│   │   │   ├── query.py         # Query endpoints
│   │   │   ├── index.py         # Index management endpoints
│   │   │   └── visualization.py # Graph/tree visualization endpoints
│   │   └── services/
│   │       ├── document_service.py   # Document ingestion & chunking
│   │       ├── raptor_service.py     # RAPTOR tree building
│   │       ├── graphrag_service.py   # GraphRAG knowledge graph
│   │       ├── retrieval_service.py  # Unified retrieval
│   │       └── query_router.py       # LangGraph query routing
│   ├── pyproject.toml           # Python dependencies
│   ├── Dockerfile               # Backend container
│   └── .env                     # Environment variables
├── hybrid-rag-frontend/         # React frontend
│   ├── src/
│   │   ├── App.tsx              # Main application
│   │   ├── components/
│   │   │   ├── QueryPanel.tsx        # Query interface
│   │   │   ├── DocumentsPanel.tsx    # Document management
│   │   │   ├── GraphVisualization.tsx # Knowledge graph view
│   │   │   ├── RaptorVisualization.tsx # RAPTOR tree view
│   │   │   └── IndexPanel.tsx        # Index management
│   │   └── lib/
│   │       └── api.ts           # API client
│   ├── package.json             # Node dependencies
│   ├── Dockerfile               # Frontend container
│   └── .env                     # Environment variables
├── k8s/                         # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── pvc.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── docker-compose.yml           # Local development
└── .env.example                 # Environment template
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for containerized deployment)
- OpenAI API key

### Local Development

1. **Clone and setup backend:**

```bash
cd hybrid-rag-backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install poetry
poetry install

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start backend
poetry run fastapi dev app/main.py
```

2. **Setup frontend:**

```bash
cd hybrid-rag-frontend

# Install dependencies
npm install

# Configure environment
echo "VITE_API_URL=http://localhost:8000" > .env

# Start frontend
npm run dev
```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Docker Compose Deployment

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# Build and start all services
docker-compose up --build

# Access at http://localhost:3000
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, AKS, GKE, or on-premises)
- kubectl configured
- Container registry access

### Deployment Steps

1. **Build and push images:**

```bash
# Build images
docker build -t your-registry/hybrid-rag-backend:latest ./hybrid-rag-backend
docker build -t your-registry/hybrid-rag-frontend:latest ./hybrid-rag-frontend

# Push to registry
docker push your-registry/hybrid-rag-backend:latest
docker push your-registry/hybrid-rag-frontend:latest
```

2. **Configure secrets:**

```bash
# Edit k8s/secret.yaml with base64-encoded values
echo -n "your-openai-key" | base64
# Add the output to secret.yaml
```

3. **Deploy to Kubernetes:**

```bash
# Create namespace and resources
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml
```

4. **Verify deployment:**

```bash
kubectl get pods -n hybrid-rag
kubectl get services -n hybrid-rag
kubectl get ingress -n hybrid-rag
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | LLM model for generation | gpt-4o-mini |
| `OPENAI_EMBEDDING_MODEL` | Embedding model | text-embedding-3-small |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key (optional) | - |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key (optional) | - |
| `LANGFUSE_HOST` | Langfuse host URL | https://cloud.langfuse.com |
| `DATABASE_URL` | SQLite database path | sqlite:///./data/hybrid_rag.db |
| `CHUNK_SIZE` | Document chunk size | 1000 |
| `CHUNK_OVERLAP` | Chunk overlap | 200 |
| `RAPTOR_MAX_LEVELS` | Max RAPTOR tree levels | 3 |
| `GRAPHRAG_ENTITY_TYPES_STR` | Entity types to extract | PERSON,ORGANIZATION,... |

## API Reference

### Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents` | GET | List all documents |
| `/api/documents` | POST | Upload document |
| `/api/documents/{id}` | DELETE | Delete document |
| `/api/documents/{id}/chunks` | GET | Get document chunks |

### Query

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/query` | POST | Execute RAG query |
| `/api/query/stream` | POST | Stream RAG query response |

### Index Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/index/status` | GET | Get index status |
| `/api/index/raptor/build` | POST | Build RAPTOR index |
| `/api/index/graphrag/build` | POST | Build GraphRAG index |
| `/api/index/build-all` | POST | Build all indexes |

### Visualization

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/visualization/graph` | GET | Get knowledge graph data |
| `/api/visualization/raptor/tree` | GET | Get RAPTOR tree data |

## Usage Guide

### 1. Upload Documents

Upload text documents or paste text content through the Documents tab. Supported formats include plain text files.

### 2. Build Indexes

Navigate to the Index Management tab and build both RAPTOR and GraphRAG indexes:
- **RAPTOR Index**: Creates hierarchical summary trees
- **GraphRAG Index**: Extracts entities and builds knowledge graph

### 3. Query Documents

Use the Query tab to ask questions. The system automatically routes queries:
- **Thematic questions** (e.g., "What are the main themes?") → RAPTOR
- **Relationship questions** (e.g., "How is X related to Y?") → GraphRAG
- **Complex questions** → Hybrid approach

### 4. Visualize Knowledge

- **Knowledge Graph tab**: Explore extracted entities and relationships
- **RAPTOR Tree tab**: View hierarchical document summaries

## Observability with Langfuse

To enable Langfuse observability:

1. Create a Langfuse account at https://cloud.langfuse.com (or self-host)
2. Create a project and get your API keys from the project settings
3. Set environment variables:
   ```
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

Langfuse provides:
- Request/response tracing
- Latency monitoring
- Token usage and cost tracking
- Error debugging
- Prompt management and evaluation capabilities

## Scaling Considerations

### Horizontal Scaling

The Kubernetes HPA (Horizontal Pod Autoscaler) is configured to scale based on CPU utilization:
- Backend: 2-10 replicas
- Frontend: 2-5 replicas

### Storage Scaling

For production deployments with large document collections:
- Consider using a managed vector database (Pinecone, Weaviate, Qdrant)
- Use PostgreSQL instead of SQLite for the metadata store
- Implement Redis caching for frequently accessed data

### Memory Optimization

The backend uses lazy initialization to minimize memory footprint:
- Services are only loaded when first accessed
- Heavy dependencies (ChromaDB, LangChain) are imported on-demand

## Troubleshooting

### Common Issues

1. **OOM errors in cloud deployment**
   - Ensure lazy initialization is enabled
   - Increase container memory limits
   - Consider using smaller embedding models

2. **Slow query responses**
   - Check Langfuse traces for bottlenecks
   - Reduce chunk size for faster retrieval
   - Enable response streaming

3. **Empty graph/tree visualizations**
   - Ensure documents are uploaded
   - Build indexes before querying
   - Check backend logs for indexing errors

## License

This project is provided as-is for demonstration and educational purposes.

## Support

For questions or issues, please refer to the documentation or contact the development team.
