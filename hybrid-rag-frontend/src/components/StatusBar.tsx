import { Badge } from '@/components/ui/badge';
import { Wifi, WifiOff, FileText, Network, TreePine } from 'lucide-react';
import { IndexStatus } from '@/lib/api';

interface StatusBarProps {
  isConnected: boolean;
  indexStatus: IndexStatus | null;
}

export function StatusBar({ isConnected, indexStatus }: StatusBarProps) {
  return (
    <div className="flex items-center gap-4">
      <div className="flex items-center gap-2">
        {isConnected ? (
          <Badge variant="outline" className="border-green-500 text-green-400 flex items-center gap-1">
            <Wifi className="h-3 w-3" />
            Connected
          </Badge>
        ) : (
          <Badge variant="outline" className="border-red-500 text-red-400 flex items-center gap-1">
            <WifiOff className="h-3 w-3" />
            Disconnected
          </Badge>
        )}
      </div>
      
      {indexStatus && (
        <div className="flex items-center gap-3 text-sm text-slate-400">
          <div className="flex items-center gap-1" title="Documents">
            <FileText className="h-4 w-4" />
            <span>{indexStatus.total_documents}</span>
          </div>
          <div className="flex items-center gap-1" title="Entities">
            <Network className="h-4 w-4" />
            <span>{indexStatus.total_entities}</span>
          </div>
          <div className="flex items-center gap-1" title="RAPTOR Levels">
            <TreePine className="h-4 w-4" />
            <span>{indexStatus.raptor_tree_levels}</span>
          </div>
        </div>
      )}
    </div>
  );
}
