import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Toaster } from '@/components/ui/sonner';
import { toast } from 'sonner';
import { 
  MessageSquare, 
  FileText, 
  Network, 
  TreePine, 
  Settings, 
  Activity,
  Database
} from 'lucide-react';
import { api, IndexStatus } from '@/lib/api';
import { QueryPanel } from '@/components/QueryPanel';
import { DocumentsPanel } from '@/components/DocumentsPanel';
import { GraphVisualization } from '@/components/GraphVisualization';
import { RaptorVisualization } from '@/components/RaptorVisualization';
import { IndexPanel } from '@/components/IndexPanel';
import { StatusBar } from '@/components/StatusBar';

function App() {
  const [indexStatus, setIndexStatus] = useState<IndexStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [activeTab, setActiveTab] = useState('query');

  useEffect(() => {
    checkConnection();
    fetchIndexStatus();
    const interval = setInterval(fetchIndexStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkConnection = async () => {
    try {
      await api.healthCheck();
      setIsConnected(true);
    } catch (error) {
      setIsConnected(false);
      toast.error('Failed to connect to backend');
    }
  };

  const fetchIndexStatus = async () => {
    try {
      const status = await api.getIndexStatus();
      setIndexStatus(status);
    } catch (error) {
      console.error('Failed to fetch index status:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <Toaster position="top-right" />
      
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg">
                <Database className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Hybrid RAG Enterprise</h1>
                <p className="text-sm text-slate-400">RAPTOR + GraphRAG with LangGraph Orchestration</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <StatusBar isConnected={isConnected} indexStatus={indexStatus} />
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-slate-800/50 border border-slate-700 p-1">
            <TabsTrigger 
              value="query" 
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Query
            </TabsTrigger>
            <TabsTrigger 
              value="documents"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <FileText className="h-4 w-4 mr-2" />
              Documents
            </TabsTrigger>
            <TabsTrigger 
              value="graph"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <Network className="h-4 w-4 mr-2" />
              Knowledge Graph
            </TabsTrigger>
            <TabsTrigger 
              value="raptor"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <TreePine className="h-4 w-4 mr-2" />
              RAPTOR Tree
            </TabsTrigger>
            <TabsTrigger 
              value="index"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              <Settings className="h-4 w-4 mr-2" />
              Index Management
            </TabsTrigger>
          </TabsList>

          <TabsContent value="query" className="space-y-6">
            <QueryPanel onQueryComplete={fetchIndexStatus} />
          </TabsContent>

          <TabsContent value="documents" className="space-y-6">
            <DocumentsPanel onDocumentChange={fetchIndexStatus} />
          </TabsContent>

          <TabsContent value="graph" className="space-y-6">
            <GraphVisualization />
          </TabsContent>

          <TabsContent value="raptor" className="space-y-6">
            <RaptorVisualization />
          </TabsContent>

          <TabsContent value="index" className="space-y-6">
            <IndexPanel indexStatus={indexStatus} onIndexChange={fetchIndexStatus} />
          </TabsContent>
        </Tabs>
      </main>

      <footer className="border-t border-slate-700 bg-slate-900/50 mt-auto">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span>Powered by LangGraph + LangSmith</span>
            </div>
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="border-blue-500 text-blue-400">
                RAPTOR
              </Badge>
              <Badge variant="outline" className="border-purple-500 text-purple-400">
                GraphRAG
              </Badge>
              <Badge variant="outline" className="border-green-500 text-green-400">
                AG-UI
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
