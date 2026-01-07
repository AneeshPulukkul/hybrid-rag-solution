import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'sonner';
import { 
  Network, 
  RefreshCw,
  Users,
  Link,
  Circle,
  ArrowRight
} from 'lucide-react';
import { api, GraphData, GraphNode } from '@/lib/api';

export function GraphVisualization() {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [stats, setStats] = useState<{
    total_entities: number;
    total_relationships: number;
    entity_types: Record<string, number>;
    relationship_types: Record<string, number>;
  } | null>(null);

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    setIsLoading(true);
    try {
      const [data, graphStats] = await Promise.all([
        api.getGraphData(),
        fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/visualization/graph/stats`)
          .then(r => r.json())
          .catch(() => null)
      ]);
      setGraphData(data);
      setStats(graphStats);
    } catch (error) {
      toast.error('Failed to fetch graph data');
    } finally {
      setIsLoading(false);
    }
  };

  const getNodeColor = (type: string) => {
    const colors: Record<string, string> = {
      PERSON: 'bg-blue-500',
      ORGANIZATION: 'bg-purple-500',
      LOCATION: 'bg-green-500',
      EVENT: 'bg-yellow-500',
      CONCEPT: 'bg-pink-500',
      TECHNOLOGY: 'bg-cyan-500',
      PRODUCT: 'bg-orange-500',
    };
    return colors[type] || 'bg-slate-500';
  };

  const getRelatedEdges = (nodeId: string) => {
    if (!graphData) return [];
    return graphData.edges.filter(
      edge => edge.source === nodeId || edge.target === nodeId
    );
  };

  const getConnectedNodes = (nodeId: string) => {
    if (!graphData) return [];
    const edges = getRelatedEdges(nodeId);
    const connectedIds = new Set<string>();
    edges.forEach(edge => {
      if (edge.source === nodeId) connectedIds.add(edge.target);
      if (edge.target === nodeId) connectedIds.add(edge.source);
    });
    return graphData.nodes.filter(node => connectedIds.has(node.id));
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Card className="bg-slate-800/50 border-slate-700 h-full">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <Network className="h-5 w-5 text-purple-400" />
                  Knowledge Graph
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Entity relationships extracted from documents
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={fetchGraphData}
                disabled={isLoading}
                className="border-slate-600 text-slate-300 hover:bg-slate-700"
              >
                {isLoading ? (
                  <Spinner className="h-4 w-4 mr-2" />
                ) : (
                  <RefreshCw className="h-4 w-4 mr-2" />
                )}
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-24">
                <Spinner className="h-8 w-8" />
              </div>
            ) : !graphData || graphData.nodes.length === 0 ? (
              <div className="text-center py-24 text-slate-400">
                <Network className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>No graph data available</p>
                <p className="text-sm mt-2">Build the GraphRAG index to see the knowledge graph</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <Users className="h-6 w-6 mx-auto text-purple-400 mb-1" />
                    <p className="text-2xl font-bold text-white">{graphData.nodes.length}</p>
                    <p className="text-xs text-slate-400">Entities</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <Link className="h-6 w-6 mx-auto text-blue-400 mb-1" />
                    <p className="text-2xl font-bold text-white">{graphData.edges.length}</p>
                    <p className="text-xs text-slate-400">Relationships</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <Circle className="h-6 w-6 mx-auto text-green-400 mb-1" />
                    <p className="text-2xl font-bold text-white">
                      {stats ? Object.keys(stats.entity_types).length : 0}
                    </p>
                    <p className="text-xs text-slate-400">Entity Types</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <ArrowRight className="h-6 w-6 mx-auto text-orange-400 mb-1" />
                    <p className="text-2xl font-bold text-white">
                      {stats ? Object.keys(stats.relationship_types).length : 0}
                    </p>
                    <p className="text-xs text-slate-400">Relation Types</p>
                  </div>
                </div>

                <ScrollArea className="h-96 rounded-lg border border-slate-700 bg-slate-900/50 p-4">
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-slate-300 mb-3">Entities</h3>
                    <div className="flex flex-wrap gap-2">
                      {graphData.nodes.map((node) => (
                        <Badge
                          key={node.id}
                          variant="outline"
                          className={`cursor-pointer transition-all ${
                            selectedNode?.id === node.id
                              ? 'ring-2 ring-blue-500 bg-slate-700'
                              : 'hover:bg-slate-700'
                          }`}
                          onClick={() => setSelectedNode(selectedNode?.id === node.id ? null : node)}
                        >
                          <span className={`w-2 h-2 rounded-full ${getNodeColor(node.type)} mr-2`} />
                          {node.name}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </ScrollArea>

                {stats && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-700/50 rounded-lg p-3">
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Entity Types</h4>
                      <div className="space-y-1">
                        {Object.entries(stats.entity_types).map(([type, count]) => (
                          <div key={type} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <span className={`w-2 h-2 rounded-full ${getNodeColor(type)}`} />
                              <span className="text-slate-300">{type}</span>
                            </div>
                            <span className="text-slate-400">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-slate-700/50 rounded-lg p-3">
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Relationship Types</h4>
                      <div className="space-y-1">
                        {Object.entries(stats.relationship_types).slice(0, 10).map(([type, count]) => (
                          <div key={type} className="flex items-center justify-between text-sm">
                            <span className="text-slate-300 truncate">{type}</span>
                            <span className="text-slate-400">{count}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Entity Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-3 h-3 rounded-full ${getNodeColor(selectedNode.type)}`} />
                    <h3 className="text-lg font-medium text-white">{selectedNode.name}</h3>
                  </div>
                  <Badge variant="outline" className="text-slate-300">
                    {selectedNode.type}
                  </Badge>
                </div>
                
                {selectedNode.description && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-400 mb-1">Description</h4>
                    <p className="text-sm text-slate-300">{selectedNode.description}</p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-2">
                    Connections ({getConnectedNodes(selectedNode.id).length})
                  </h4>
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {getRelatedEdges(selectedNode.id).map((edge, idx) => {
                        const isSource = edge.source === selectedNode.id;
                        const otherNode = graphData?.nodes.find(
                          n => n.id === (isSource ? edge.target : edge.source)
                        );
                        return (
                          <div
                            key={idx}
                            className="bg-slate-700/50 rounded p-2 text-sm cursor-pointer hover:bg-slate-700"
                            onClick={() => otherNode && setSelectedNode(otherNode)}
                          >
                            <div className="flex items-center gap-1 text-slate-300">
                              {isSource ? (
                                <>
                                  <span className="text-slate-400">→</span>
                                  <span className="text-blue-400">{edge.type}</span>
                                  <span className="text-slate-400">→</span>
                                  <span>{otherNode?.name}</span>
                                </>
                              ) : (
                                <>
                                  <span>{otherNode?.name}</span>
                                  <span className="text-slate-400">→</span>
                                  <span className="text-blue-400">{edge.type}</span>
                                  <span className="text-slate-400">→</span>
                                </>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">
                <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Select an entity to view details</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Legend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {['PERSON', 'ORGANIZATION', 'LOCATION', 'EVENT', 'CONCEPT', 'TECHNOLOGY', 'PRODUCT'].map(type => (
                <div key={type} className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${getNodeColor(type)}`} />
                  <span className="text-sm text-slate-300">{type}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
