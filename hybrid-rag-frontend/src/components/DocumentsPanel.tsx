import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Spinner } from '@/components/ui/spinner';
import { toast } from 'sonner';
import { 
  Upload, 
  FileText, 
  Trash2, 
  Plus,
  CheckCircle,
  Clock
} from 'lucide-react';
import { api, Document } from '@/lib/api';

interface DocumentsPanelProps {
  onDocumentChange?: () => void;
}

export function DocumentsPanel({ onDocumentChange }: DocumentsPanelProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [showTextDialog, setShowTextDialog] = useState(false);
  const [textFilename, setTextFilename] = useState('');
  const [textContent, setTextContent] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (error) {
      toast.error('Failed to fetch documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setIsUploading(true);
    try {
      for (const file of Array.from(files)) {
        await api.uploadDocument(file);
        toast.success(`Uploaded: ${file.name}`);
      }
      await fetchDocuments();
      onDocumentChange?.();
    } catch (error) {
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleTextUpload = async () => {
    if (!textFilename.trim() || !textContent.trim()) {
      toast.error('Please provide both filename and content');
      return;
    }

    setIsUploading(true);
    try {
      await api.uploadText(textFilename, textContent);
      toast.success(`Uploaded: ${textFilename}`);
      setShowTextDialog(false);
      setTextFilename('');
      setTextContent('');
      await fetchDocuments();
      onDocumentChange?.();
    } catch (error) {
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (documentId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
      await api.deleteDocument(documentId);
      toast.success(`Deleted: ${filename}`);
      await fetchDocuments();
      onDocumentChange?.();
    } catch (error) {
      toast.error(`Delete failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="space-y-6">
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-400" />
                Document Management
              </CardTitle>
              <CardDescription className="text-slate-400">
                Upload and manage documents for indexing
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".txt,.md,.json"
                multiple
                className="hidden"
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {isUploading ? (
                  <Spinner className="h-4 w-4 mr-2" />
                ) : (
                  <Upload className="h-4 w-4 mr-2" />
                )}
                Upload File
              </Button>
              
              <Dialog open={showTextDialog} onOpenChange={setShowTextDialog}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Text
                  </Button>
                </DialogTrigger>
                <DialogContent className="bg-slate-800 border-slate-700">
                  <DialogHeader>
                    <DialogTitle className="text-white">Add Text Document</DialogTitle>
                    <DialogDescription className="text-slate-400">
                      Paste or type text content to add as a document
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-slate-300 mb-1 block">Filename</label>
                      <Input
                        value={textFilename}
                        onChange={(e) => setTextFilename(e.target.value)}
                        placeholder="document.txt"
                        className="bg-slate-700 border-slate-600 text-white"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-slate-300 mb-1 block">Content</label>
                      <Textarea
                        value={textContent}
                        onChange={(e) => setTextContent(e.target.value)}
                        placeholder="Paste your text content here..."
                        className="bg-slate-700 border-slate-600 text-white min-h-48"
                      />
                    </div>
                    <Button
                      onClick={handleTextUpload}
                      disabled={isUploading || !textFilename.trim() || !textContent.trim()}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                    >
                      {isUploading ? (
                        <Spinner className="h-4 w-4 mr-2" />
                      ) : (
                        <Upload className="h-4 w-4 mr-2" />
                      )}
                      Upload Text
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="h-8 w-8" />
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No documents uploaded yet</p>
              <p className="text-sm mt-2">Upload documents to start building your knowledge base</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700">
                  <TableHead className="text-slate-300">Filename</TableHead>
                  <TableHead className="text-slate-300">Chunks</TableHead>
                  <TableHead className="text-slate-300">RAPTOR</TableHead>
                  <TableHead className="text-slate-300">GraphRAG</TableHead>
                  <TableHead className="text-slate-300">Created</TableHead>
                  <TableHead className="text-slate-300 text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.map((doc) => (
                  <TableRow key={doc.id} className="border-slate-700">
                    <TableCell className="text-white font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-slate-400" />
                        {doc.filename}
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-300">
                      <Badge variant="outline" className="border-slate-600">
                        {doc.chunk_count} chunks
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {doc.raptor_indexed ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <Clock className="h-5 w-5 text-yellow-500" />
                      )}
                    </TableCell>
                    <TableCell>
                      {doc.graphrag_indexed ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : (
                        <Clock className="h-5 w-5 text-yellow-500" />
                      )}
                    </TableCell>
                    <TableCell className="text-slate-400 text-sm">
                      {formatDate(doc.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                        onClick={() => handleDelete(doc.id, doc.filename)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
