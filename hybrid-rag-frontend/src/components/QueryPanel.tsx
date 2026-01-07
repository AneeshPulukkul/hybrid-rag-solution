import { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'sonner';
import { 
  Send, 
  Sparkles, 
  Clock, 
  TreePine, 
  Network, 
  Zap,
  ChevronDown,
  ChevronUp,
  Copy,
  Check
} from 'lucide-react';
import { api, RetrievalSource } from '@/lib/api';

interface QueryPanelProps {
  onQueryComplete?: () => void;
}

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  queryType?: string;
  sources?: RetrievalSource[];
  latencyMs?: number;
  raptorUsed?: boolean;
  graphragUsed?: boolean;
  timestamp: Date;
}

export function QueryPanel({ onQueryComplete }: QueryPanelProps) {
  const [query, setQuery] = useState('');
  const [queryType, setQueryType] = useState<'auto' | 'thematic_holistic' | 'relational_multihop' | 'hybrid'>('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>('');
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  const handleSubmit = async () => {
    if (!query.trim() || isLoading) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      type: 'user',
      content: query,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setQuery('');
    setIsLoading(true);
    setStreamingMessage('');

    try {
      let finalResponse: Partial<Message> = {};
      
      for await (const event of api.queryStream({
        query: userMessage.content,
        query_type: queryType,
        top_k: 5,
        include_sources: true,
      })) {
        switch (event.type) {
          case 'start':
            setStreamingMessage('Starting query...');
            break;
          case 'classification':
            setStreamingMessage(`Query classified as: ${event.query_type}`);
            finalResponse.queryType = event.query_type;
            break;
          case 'retrieving':
            setStreamingMessage('Retrieving context from RAPTOR and GraphRAG...');
            break;
          case 'sources':
            finalResponse.sources = event.sources;
            setStreamingMessage('Generating answer...');
            break;
          case 'answer':
            finalResponse.content = event.answer || '';
            finalResponse.latencyMs = event.latency_ms;
            finalResponse.raptorUsed = event.raptor_context_used;
            finalResponse.graphragUsed = event.graphrag_context_used;
            break;
          case 'error':
            throw new Error(event.message);
          case 'end':
            break;
        }
      }

      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        type: 'assistant',
        content: finalResponse.content || 'No response generated',
        queryType: finalResponse.queryType,
        sources: finalResponse.sources,
        latencyMs: finalResponse.latencyMs,
        raptorUsed: finalResponse.raptorUsed,
        graphragUsed: finalResponse.graphragUsed,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      onQueryComplete?.();
    } catch (error) {
      toast.error(`Query failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setStreamingMessage('');
    }
  };

  const toggleSources = (messageId: string) => {
    setExpandedSources(prev => {
      const next = new Set(prev);
      if (next.has(messageId)) {
        next.delete(messageId);
      } else {
        next.add(messageId);
      }
      return next;
    });
  };

  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const getQueryTypeBadge = (type: string) => {
    switch (type) {
      case 'thematic_holistic':
        return <Badge className="bg-blue-600">Thematic/Holistic</Badge>;
      case 'relational_multihop':
        return <Badge className="bg-purple-600">Relational/Multi-hop</Badge>;
      case 'hybrid':
        return <Badge className="bg-green-600">Hybrid</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <Card className="bg-slate-800/50 border-slate-700 h-full flex flex-col">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-400" />
              Hybrid RAG Query Interface
            </CardTitle>
            <CardDescription className="text-slate-400">
              Ask questions using RAPTOR for thematic queries or GraphRAG for entity relationships
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <ScrollArea className="flex-1 pr-4 mb-4 min-h-96">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="text-center text-slate-500 py-12">
                    <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Start a conversation by asking a question</p>
                    <p className="text-sm mt-2">
                      Try: "What are the main themes?" or "How is X related to Y?"
                    </p>
                  </div>
                )}
                
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-4xl rounded-lg p-4 ${
                        message.type === 'user'
                          ? 'bg-blue-600 text-white'
                          : message.type === 'system'
                          ? 'bg-red-900/50 text-red-200 border border-red-700'
                          : 'bg-slate-700 text-slate-100'
                      }`}
                    >
                      {message.type === 'assistant' && (
                        <div className="flex items-center gap-2 mb-2 flex-wrap">
                          {message.queryType && getQueryTypeBadge(message.queryType)}
                          {message.raptorUsed && (
                            <Badge variant="outline" className="border-blue-500 text-blue-400">
                              <TreePine className="h-3 w-3 mr-1" />
                              RAPTOR
                            </Badge>
                          )}
                          {message.graphragUsed && (
                            <Badge variant="outline" className="border-purple-500 text-purple-400">
                              <Network className="h-3 w-3 mr-1" />
                              GraphRAG
                            </Badge>
                          )}
                          {message.latencyMs && (
                            <Badge variant="outline" className="border-slate-500 text-slate-400">
                              <Clock className="h-3 w-3 mr-1" />
                              {message.latencyMs.toFixed(0)}ms
                            </Badge>
                          )}
                        </div>
                      )}
                      
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      
                      {message.type === 'assistant' && (
                        <div className="flex items-center gap-2 mt-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-slate-400 hover:text-white"
                            onClick={() => copyToClipboard(message.content, message.id)}
                          >
                            {copiedId === message.id ? (
                              <Check className="h-4 w-4" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                          
                          {message.sources && message.sources.length > 0 && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-slate-400 hover:text-white"
                              onClick={() => toggleSources(message.id)}
                            >
                              {expandedSources.has(message.id) ? (
                                <>
                                  <ChevronUp className="h-4 w-4 mr-1" />
                                  Hide Sources ({message.sources.length})
                                </>
                              ) : (
                                <>
                                  <ChevronDown className="h-4 w-4 mr-1" />
                                  Show Sources ({message.sources.length})
                                </>
                              )}
                            </Button>
                          )}
                        </div>
                      )}
                      
                      {message.sources && expandedSources.has(message.id) && (
                        <div className="mt-3 space-y-2">
                          <Separator className="bg-slate-600" />
                          <p className="text-sm font-medium text-slate-300">Sources:</p>
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className="bg-slate-800 rounded p-3 text-sm"
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <Badge variant="outline" className="text-xs">
                                  {source.source_type}
                                </Badge>
                                <span className="text-slate-400">
                                  Score: {(source.score * 100).toFixed(1)}%
                                </span>
                              </div>
                              <p className="text-slate-300 text-xs">{source.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {streamingMessage && (
                  <div className="flex justify-start">
                    <div className="bg-slate-700 text-slate-100 rounded-lg p-4 flex items-center gap-2">
                      <Spinner className="h-4 w-4" />
                      <span>{streamingMessage}</span>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>
            
            <div className="space-y-3">
              <div className="flex gap-2">
                <Select value={queryType} onValueChange={(v) => setQueryType(v as typeof queryType)}>
                  <SelectTrigger className="w-48 bg-slate-700 border-slate-600 text-white">
                    <SelectValue placeholder="Query Type" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-700 border-slate-600">
                    <SelectItem value="auto">Auto Detect</SelectItem>
                    <SelectItem value="thematic_holistic">Thematic/Holistic (RAPTOR)</SelectItem>
                    <SelectItem value="relational_multihop">Relational/Multi-hop (GraphRAG)</SelectItem>
                    <SelectItem value="hybrid">Hybrid (Both)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex gap-2">
                <Textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask a question about your documents..."
                  className="bg-slate-700 border-slate-600 text-white placeholder:text-slate-400 resize-none"
                  rows={2}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                />
                <Button
                  onClick={handleSubmit}
                  disabled={!query.trim() || isLoading}
                  className="bg-blue-600 hover:bg-blue-700 px-6"
                >
                  {isLoading ? (
                    <Spinner className="h-4 w-4" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      <div className="space-y-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <Zap className="h-5 w-5 text-yellow-400" />
              Query Types
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <TreePine className="h-4 w-4 text-blue-400" />
                <span className="text-white font-medium">Thematic/Holistic</span>
              </div>
              <p className="text-sm text-slate-400">
                Best for summarization, main themes, and high-level understanding across documents.
              </p>
            </div>
            
            <Separator className="bg-slate-700" />
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Network className="h-4 w-4 text-purple-400" />
                <span className="text-white font-medium">Relational/Multi-hop</span>
              </div>
              <p className="text-sm text-slate-400">
                Best for entity relationships, "who/what" questions, and multi-hop reasoning.
              </p>
            </div>
            
            <Separator className="bg-slate-700" />
            
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-green-400" />
                <span className="text-white font-medium">Hybrid</span>
              </div>
              <p className="text-sm text-slate-400">
                Combines both approaches for comprehensive answers.
              </p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white text-lg">Example Queries</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              'What are the main themes discussed?',
              'Summarize the key points',
              'Who are the main people mentioned?',
              'How is X related to Y?',
              'What organizations are involved?',
            ].map((example, idx) => (
              <Button
                key={idx}
                variant="ghost"
                className="w-full justify-start text-slate-300 hover:text-white hover:bg-slate-700"
                onClick={() => setQuery(example)}
              >
                {example}
              </Button>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
