import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'sonner';
import { 
  TreePine, 
  Network, 
  Play,
  RefreshCw,
  Database,
  FileText,
  Users,
  Link,
  Layers
} from 'lucide-react';
import { api, IndexStatus } from '@/lib/api';

interface IndexPanelProps {
  indexStatus: IndexStatus | null;
  onIndexChange?: () => void;
}

export function IndexPanel({ indexStatus, onIndexChange }: IndexPanelProps) {
  const [isBuilding, setIsBuilding] = useState<'raptor' | 'graphrag' | 'all' | null>(null);

  const handleBuildRaptor = async () => {
    setIsBuilding('raptor');
    try {
      await api.buildRaptorIndex();
      toast.success('RAPTOR indexing started');
      setTimeout(() => {
        onIndexChange?.();
        setIsBuilding(null);
      }, 2000);
    } catch (error) {
      toast.error(`Failed to build RAPTOR index: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsBuilding(null);
    }
  };

  const handleBuildGraphRAG = async () => {
    setIsBuilding('graphrag');
    try {
      await api.buildGraphRAGIndex();
      toast.success('GraphRAG indexing started');
      setTimeout(() => {
        onIndexChange?.();
        setIsBuilding(null);
      }, 2000);
    } catch (error) {
      toast.error(`Failed to build GraphRAG index: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsBuilding(null);
    }
  };

  const handleBuildAll = async () => {
    setIsBuilding('all');
    try {
      await api.buildAllIndexes();
      toast.success('All indexing started');
      setTimeout(() => {
        onIndexChange?.();
        setIsBuilding(null);
      }, 2000);
    } catch (error) {
      toast.error(`Failed to build indexes: ${error instanceof Error ? error.message : 'Unknown error'}`);
      setIsBuilding(null);
    }
  };

  const raptorProgress = indexStatus 
    ? (indexStatus.raptor_indexed_documents / Math.max(indexStatus.total_documents, 1)) * 100 
    : 0;
  
  const graphragProgress = indexStatus 
    ? (indexStatus.graphrag_indexed_documents / Math.max(indexStatus.total_documents, 1)) * 100 
    : 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total Documents</p>
                <p className="text-2xl font-bold text-white">
                  {indexStatus?.total_documents ?? 0}
                </p>
              </div>
              <FileText className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total Chunks</p>
                <p className="text-2xl font-bold text-white">
                  {indexStatus?.total_chunks ?? 0}
                </p>
              </div>
              <Database className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Entities</p>
                <p className="text-2xl font-bold text-white">
                  {indexStatus?.total_entities ?? 0}
                </p>
              </div>
              <Users className="h-8 w-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Relationships</p>
                <p className="text-2xl font-bold text-white">
                  {indexStatus?.total_relationships ?? 0}
                </p>
              </div>
              <Link className="h-8 w-8 text-orange-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <TreePine className="h-5 w-5 text-blue-400" />
                  RAPTOR Index
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Hierarchical summary tree for thematic queries
                </CardDescription>
              </div>
              <Button
                onClick={handleBuildRaptor}
                disabled={isBuilding !== null || !indexStatus?.total_documents}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isBuilding === 'raptor' ? (
                  <Spinner className="h-4 w-4 mr-2" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Build Index
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Indexed Documents</span>
                <span className="text-white">
                  {indexStatus?.raptor_indexed_documents ?? 0} / {indexStatus?.total_documents ?? 0}
                </span>
              </div>
              <Progress value={raptorProgress} className="h-2" />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Layers className="h-4 w-4" />
                  Tree Levels
                </div>
                <p className="text-xl font-bold text-white">
                  {indexStatus?.raptor_tree_levels ?? 0}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Database className="h-4 w-4" />
                  Communities
                </div>
                <p className="text-xl font-bold text-white">
                  {indexStatus?.total_communities ?? 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <Network className="h-5 w-5 text-purple-400" />
                  GraphRAG Index
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Knowledge graph for entity relationships
                </CardDescription>
              </div>
              <Button
                onClick={handleBuildGraphRAG}
                disabled={isBuilding !== null || !indexStatus?.total_documents}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {isBuilding === 'graphrag' ? (
                  <Spinner className="h-4 w-4 mr-2" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Build Index
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Indexed Documents</span>
                <span className="text-white">
                  {indexStatus?.graphrag_indexed_documents ?? 0} / {indexStatus?.total_documents ?? 0}
                </span>
              </div>
              <Progress value={graphragProgress} className="h-2" />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Users className="h-4 w-4" />
                  Entities
                </div>
                <p className="text-xl font-bold text-white">
                  {indexStatus?.total_entities ?? 0}
                </p>
              </div>
              <div className="bg-slate-700/50 rounded-lg p-3">
                <div className="flex items-center gap-2 text-slate-400 text-sm mb-1">
                  <Link className="h-4 w-4" />
                  Relationships
                </div>
                <p className="text-xl font-bold text-white">
                  {indexStatus?.total_relationships ?? 0}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white">Build All Indexes</CardTitle>
              <CardDescription className="text-slate-400">
                Build both RAPTOR and GraphRAG indexes in sequence
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={onIndexChange}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh Status
              </Button>
              <Button
                onClick={handleBuildAll}
                disabled={isBuilding !== null || !indexStatus?.total_documents}
                className="bg-green-600 hover:bg-green-700"
              >
                {isBuilding === 'all' ? (
                  <Spinner className="h-4 w-4 mr-2" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Build All
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>
    </div>
  );
}
