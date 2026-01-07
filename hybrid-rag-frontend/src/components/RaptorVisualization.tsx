import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { toast } from 'sonner';
import { 
  TreePine, 
  RefreshCw,
  Layers,
  FileText,
  ChevronRight,
  Circle
} from 'lucide-react';
import { api, RaptorTreeData, RaptorNode } from '@/lib/api';

export function RaptorVisualization() {
  const [treeData, setTreeData] = useState<RaptorTreeData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<RaptorNode | null>(null);
  useEffect(() => {
    fetchTreeData();
  }, []);

  const fetchTreeData = async () => {
    setIsLoading(true);
    try {
      const data = await api.getRaptorTree();
      setTreeData(data);
    } catch (error) {
      toast.error('Failed to fetch RAPTOR tree data');
    } finally {
      setIsLoading(false);
    }
  };

  const getNodesByLevel = (level: number) => {
    if (!treeData) return [];
    return treeData.nodes.filter(node => node.level === level);
  };

  const getLevelColor = (level: number) => {
    const colors = [
      'bg-blue-500',
      'bg-purple-500',
      'bg-green-500',
      'bg-yellow-500',
      'bg-pink-500',
    ];
    return colors[level % colors.length];
  };

  const getChildNodes = (nodeId: string) => {
    if (!treeData) return [];
    const node = treeData.nodes.find(n => n.id === nodeId);
    if (!node) return [];
    return treeData.nodes.filter(n => node.children_ids.includes(n.id));
  };

  const getParentNode = (nodeId: string) => {
    if (!treeData) return null;
    const node = treeData.nodes.find(n => n.id === nodeId);
    if (!node || !node.parent_id) return null;
    return treeData.nodes.find(n => n.id === node.parent_id);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Card className="bg-slate-800/50 border-slate-700 h-full">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white flex items-center gap-2">
                  <TreePine className="h-5 w-5 text-blue-400" />
                  RAPTOR Summary Tree
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Hierarchical summaries for thematic understanding
                </CardDescription>
              </div>
              <Button
                variant="outline"
                onClick={fetchTreeData}
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
            ) : !treeData || treeData.nodes.length === 0 ? (
              <div className="text-center py-24 text-slate-400">
                <TreePine className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>No RAPTOR tree data available</p>
                <p className="text-sm mt-2">Build the RAPTOR index to see the summary tree</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <Layers className="h-6 w-6 mx-auto text-blue-400 mb-1" />
                    <p className="text-2xl font-bold text-white">{treeData.levels}</p>
                    <p className="text-xs text-slate-400">Levels</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <FileText className="h-6 w-6 mx-auto text-green-400 mb-1" />
                    <p className="text-2xl font-bold text-white">{treeData.nodes.length}</p>
                    <p className="text-xs text-slate-400">Total Nodes</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-3 text-center">
                    <Circle className="h-6 w-6 mx-auto text-purple-400 mb-1" />
                    <p className="text-2xl font-bold text-white">
                      {getNodesByLevel(0).length}
                    </p>
                    <p className="text-xs text-slate-400">Base Chunks</p>
                  </div>
                </div>

                <ScrollArea className="h-96 rounded-lg border border-slate-700 bg-slate-900/50">
                  <Accordion type="multiple" className="p-4">
                    {Array.from({ length: treeData.levels }, (_, level) => (
                      <AccordionItem key={level} value={`level-${level}`} className="border-slate-700">
                        <AccordionTrigger className="text-white hover:no-underline">
                          <div className="flex items-center gap-3">
                            <span className={`w-3 h-3 rounded-full ${getLevelColor(level)}`} />
                            <span>Level {level}</span>
                            <Badge variant="outline" className="text-slate-400">
                              {getNodesByLevel(level).length} nodes
                            </Badge>
                            {level === 0 && (
                              <Badge className="bg-blue-600">Base Chunks</Badge>
                            )}
                            {level === treeData.levels - 1 && (
                              <Badge className="bg-green-600">Root Summaries</Badge>
                            )}
                          </div>
                        </AccordionTrigger>
                        <AccordionContent>
                          <div className="space-y-2 pl-6">
                            {getNodesByLevel(level).map((node) => (
                              <div
                                key={node.id}
                                className={`p-3 rounded-lg cursor-pointer transition-all ${
                                  selectedNode?.id === node.id
                                    ? 'bg-blue-900/50 border border-blue-500'
                                    : 'bg-slate-800 hover:bg-slate-700'
                                }`}
                                onClick={() => setSelectedNode(selectedNode?.id === node.id ? null : node)}
                              >
                                <div className="flex items-start gap-2">
                                  <ChevronRight className="h-4 w-4 text-slate-400 mt-1 flex-shrink-0" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm text-slate-300 line-clamp-2">
                                      {node.summary || node.content}
                                    </p>
                                    {node.children_ids.length > 0 && (
                                      <p className="text-xs text-slate-500 mt-1">
                                        {node.children_ids.length} children
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    ))}
                  </Accordion>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Node Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`w-3 h-3 rounded-full ${getLevelColor(selectedNode.level)}`} />
                    <Badge variant="outline">Level {selectedNode.level}</Badge>
                  </div>
                </div>

                {selectedNode.summary && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-400 mb-1">Summary</h4>
                    <p className="text-sm text-slate-300 bg-slate-700/50 rounded p-3">
                      {selectedNode.summary}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-1">Content</h4>
                  <ScrollArea className="h-32">
                    <p className="text-sm text-slate-300 bg-slate-700/50 rounded p-3">
                      {selectedNode.content}
                    </p>
                  </ScrollArea>
                </div>

                {selectedNode.parent_id && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-400 mb-1">Parent</h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-slate-300 hover:bg-slate-700"
                      onClick={() => {
                        const parent = getParentNode(selectedNode.id);
                        if (parent) setSelectedNode(parent);
                      }}
                    >
                      <ChevronRight className="h-4 w-4 mr-2 rotate-180" />
                      View Parent (Level {selectedNode.level + 1})
                    </Button>
                  </div>
                )}

                {selectedNode.children_ids.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-slate-400 mb-2">
                      Children ({selectedNode.children_ids.length})
                    </h4>
                    <ScrollArea className="h-32">
                      <div className="space-y-1">
                        {getChildNodes(selectedNode.id).map((child) => (
                          <Button
                            key={child.id}
                            variant="ghost"
                            size="sm"
                            className="w-full justify-start text-slate-300 hover:bg-slate-700 text-left"
                            onClick={() => setSelectedNode(child)}
                          >
                            <ChevronRight className="h-4 w-4 mr-2 flex-shrink-0" />
                            <span className="truncate">
                              {child.summary || child.content.substring(0, 50)}...
                            </span>
                          </Button>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-400">
                <TreePine className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">Select a node to view details</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">How RAPTOR Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-400">
            <p>
              <strong className="text-slate-300">Level 0:</strong> Original document chunks
            </p>
            <p>
              <strong className="text-slate-300">Higher Levels:</strong> Clustered and summarized nodes
            </p>
            <p>
              <strong className="text-slate-300">Root:</strong> High-level thematic summaries
            </p>
            <p className="pt-2 border-t border-slate-700">
              RAPTOR uses agglomerative clustering to group similar chunks, then generates
              abstractive summaries at each level, creating a hierarchical understanding
              of the document content.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
