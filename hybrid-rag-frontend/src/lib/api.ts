const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface Document {
  id: string;
  filename: string;
  chunk_count: number;
  raptor_indexed: boolean;
  graphrag_indexed: boolean;
  created_at: string;
}

export interface QueryRequest {
  query: string;
  query_type: 'auto' | 'thematic_holistic' | 'relational_multihop' | 'hybrid';
  top_k: number;
  include_sources: boolean;
}

export interface RetrievalSource {
  source_type: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface QueryResponse {
  query: string;
  query_type: string;
  answer: string;
  sources: RetrievalSource[];
  latency_ms: number;
  raptor_context_used: boolean;
  graphrag_context_used: boolean;
}

export interface IndexStatus {
  total_documents: number;
  raptor_indexed_documents: number;
  graphrag_indexed_documents: number;
  total_chunks: number;
  total_entities: number;
  total_relationships: number;
  total_communities: number;
  raptor_tree_levels: number;
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  description: string;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  description: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface RaptorNode {
  id: string;
  level: number;
  content: string;
  summary: string | null;
  parent_id: string | null;
  children_ids: string[];
}

export interface RaptorTreeData {
  nodes: RaptorNode[];
  levels: number;
}

export interface StreamEvent {
  type: 'start' | 'classification' | 'retrieving' | 'sources' | 'answer' | 'end' | 'error';
  query?: string;
  query_type?: string;
  message?: string;
  sources?: RetrievalSource[];
  answer?: string;
  latency_ms?: number;
  raptor_context_used?: boolean;
  graphrag_context_used?: boolean;
}

export const api = {
  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  async uploadText(filename: string, content: string): Promise<Document> {
    const formData = new FormData();
    formData.append('filename', filename);
    formData.append('content', content);
    
    const response = await fetch(`${API_URL}/api/documents/upload-text`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  async listDocuments(): Promise<Document[]> {
    const response = await fetch(`${API_URL}/api/documents`);
    if (!response.ok) {
      throw new Error(`Failed to list documents: ${response.statusText}`);
    }
    return response.json();
  },

  async deleteDocument(documentId: string): Promise<void> {
    const response = await fetch(`${API_URL}/api/documents/${documentId}`, {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`Failed to delete document: ${response.statusText}`);
    }
  },

  async query(request: QueryRequest): Promise<QueryResponse> {
    const response = await fetch(`${API_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }
    
    return response.json();
  },

  async *queryStream(request: QueryRequest): AsyncGenerator<StreamEvent> {
    const response = await fetch(`${API_URL}/api/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Query failed: ${response.statusText}`);
    }
    
    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }
    
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      
      for (const line of lines) {
        if (line.trim()) {
          try {
            yield JSON.parse(line);
          } catch (e) {
            console.error('Failed to parse stream event:', line);
          }
        }
      }
    }
  },

  async getIndexStatus(): Promise<IndexStatus> {
    const response = await fetch(`${API_URL}/api/index/status`);
    if (!response.ok) {
      throw new Error(`Failed to get index status: ${response.statusText}`);
    }
    return response.json();
  },

  async buildRaptorIndex(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_URL}/api/index/raptor/build`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to build RAPTOR index: ${response.statusText}`);
    }
    return response.json();
  },

  async buildGraphRAGIndex(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_URL}/api/index/graphrag/build`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to build GraphRAG index: ${response.statusText}`);
    }
    return response.json();
  },

  async buildAllIndexes(): Promise<{ status: string; message: string }> {
    const response = await fetch(`${API_URL}/api/index/build-all`, {
      method: 'POST',
    });
    if (!response.ok) {
      throw new Error(`Failed to build indexes: ${response.statusText}`);
    }
    return response.json();
  },

  async getGraphData(): Promise<GraphData> {
    const response = await fetch(`${API_URL}/api/visualization/graph`);
    if (!response.ok) {
      throw new Error(`Failed to get graph data: ${response.statusText}`);
    }
    return response.json();
  },

  async getRaptorTree(): Promise<RaptorTreeData> {
    const response = await fetch(`${API_URL}/api/visualization/raptor/tree`);
    if (!response.ok) {
      throw new Error(`Failed to get RAPTOR tree: ${response.statusText}`);
    }
    return response.json();
  },

  async classifyQuery(query: string): Promise<{ query: string; query_type: string; description: string }> {
    const response = await fetch(`${API_URL}/api/query/classify?query=${encodeURIComponent(query)}`);
    if (!response.ok) {
      throw new Error(`Failed to classify query: ${response.statusText}`);
    }
    return response.json();
  },

  async getQueryHistory(limit: number = 50): Promise<Array<{
    id: string;
    query: string;
    query_type: string;
    response: string;
    latency_ms: number;
    created_at: string;
  }>> {
    const response = await fetch(`${API_URL}/api/query/history?limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Failed to get query history: ${response.statusText}`);
    }
    return response.json();
  },

  async healthCheck(): Promise<{ status: string }> {
    const response = await fetch(`${API_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  },
};
