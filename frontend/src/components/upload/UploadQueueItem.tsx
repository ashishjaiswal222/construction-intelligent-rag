'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocumentStatus, retryProcessing, retryChunking, deleteDocument } from '@/lib/api';
import { FileIcon, AlertCircle, CheckCircle2, Loader2, RotateCw, Trash2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { toast } from 'sonner';

interface QueueItemProps {
  item: {
    docId?: string;
    filename: string;
    size?: number;
    initialStatus: string;
    reason?: string;
    existing_id?: string;
  };
  onRemove?: (docId: string) => void;
}

const TERMINAL_STATUSES = ['indexed', 'failed', 'permanently_failed', 'rejected', 'duplicate'];

export function UploadQueueItem({ item, onRemove }: QueueItemProps) {
  const queryClient = useQueryClient();
  const isTerminalInitial = ['rejected', 'duplicate'].includes(item.initialStatus);

  const { data: statusData } = useQuery({
    queryKey: ['docStatus', item.docId],
    queryFn: () => getDocumentStatus(item.docId!),
    enabled: !!item.docId && !isTerminalInitial && item.initialStatus !== 'uploading',
    refetchInterval: (query) => {
      const isTerminal = TERMINAL_STATUSES.includes(query.state.data?.status || '');
      return isTerminal ? false : 3000;
    },
  });

  const retryOcrMutation = useMutation({
    mutationFn: () => retryProcessing(item.docId!),
    onSuccess: () => {
      toast.success('Retry OCR triggered successfully');
      queryClient.invalidateQueries({ queryKey: ['docStatus', item.docId] });
    },
    onError: (err: any) => toast.error(err.message || 'Failed to retry OCR'),
  });

  const retryChunkingMutation = useMutation({
    mutationFn: () => retryChunking(item.docId!),
    onSuccess: () => {
      toast.success('Retry Chunking triggered successfully');
      queryClient.invalidateQueries({ queryKey: ['docStatus', item.docId] });
    },
    onError: (err: any) => toast.error(err.message || 'Failed to retry chunking'),
  });

  const deleteDocMutation = useMutation({
    mutationFn: () => deleteDocument(item.docId!),
    onSuccess: () => {
      toast.success('Document deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      if (onRemove && item.docId) {
        onRemove(item.docId);
      }
    },
    onError: (err: any) => toast.error(err.message || 'Failed to delete document'),
  });

  const displayStatus = statusData?.status || item.initialStatus;

  // Visuals mapping
  const isError = ['failed', 'permanently_failed', 'rejected'].includes(displayStatus);
  const isWarning = ['needs_review', 'duplicate', 'partially_indexed'].includes(displayStatus);
  const isSuccess = displayStatus === 'indexed';
  const isProcessing = !isError && !isWarning && !isSuccess;

  const StatusIcon = isSuccess ? CheckCircle2 : isError ? AlertCircle : isWarning ? AlertCircle : Loader2;
  const iconColor = isSuccess ? 'text-emerald-500' : isError ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-primary';

  const renderQualityPill = () => {
    if (statusData?.refinement_quality_avg == null) return null;
    const avg = statusData.refinement_quality_avg;
    if (avg > 0.80) return <span className="text-emerald-600 font-medium">Quality: Good</span>;
    if (avg >= 0.65) return <span className="text-amber-600 font-medium">Quality: Fair</span>;
    return <span className="text-red-600 font-medium">Quality: Poor — Review needed</span>;
  };

  return (
    <div className="flex items-start gap-4 p-4 border rounded-lg bg-card shadow-sm">
      <FileIcon className="w-8 h-8 text-muted-foreground shrink-0 mt-1" />
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <p className="font-mono text-sm font-medium truncate pr-4" title={item.filename}>
            {item.filename}
          </p>
          <div className="flex items-center gap-2 shrink-0">
            {statusData?.doc_type && (
              <Badge variant="outline" className="capitalize text-xs">
                {statusData.doc_type.replace('_', ' ')}
              </Badge>
            )}
            <StatusBadge status={displayStatus} />
            {item.docId && !['rejected', 'duplicate'].includes(item.initialStatus) && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/50 -mr-2"
                onClick={(e) => {
                  e.stopPropagation();
                  if (window.confirm(`Are you sure you want to delete "${item.filename}"? This will cancel any processing and permanently remove it.`)) {
                    deleteDocMutation.mutate();
                  }
                }}
                disabled={deleteDocMutation.isPending}
                title="Delete Document"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap mt-2">
          {item.size && <span>{(item.size / 1024 / 1024).toFixed(2)} MB</span>}
          
          {statusData?.ocr_confidence != null && (
            <span className="flex items-center gap-1">
              OCR: {(statusData.ocr_confidence * 100).toFixed(0)}%
            </span>
          )}
          
          {statusData?.chunk_count != null && (
            <div className="relative group cursor-pointer border-b border-dashed border-muted-foreground">
              <span>Chunks: {statusData.chunk_count}</span>
              {statusData.chunking_strategy_breakdown && (
                <div className="absolute left-0 bottom-full mb-2 hidden group-hover:block bg-popover border text-popover-foreground p-2 rounded shadow-md z-10 w-48 text-xs">
                  <div className="font-semibold mb-1">Strategy Breakdown</div>
                  {Object.entries(statusData.chunking_strategy_breakdown).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="truncate pr-2">{k}</span>
                      <span>{v}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {renderQualityPill()}

          {item.reason && (
            <span className="text-red-500 font-medium">Reason: {item.reason}</span>
          )}
          
          {item.existing_id && (
            <span className="text-amber-500 font-medium">Already exists (ID: {item.existing_id})</span>
          )}

          {statusData?.error && (
            <span className="text-red-500 font-medium truncate max-w-sm" title={statusData.error}>
              Error: {statusData.error}
            </span>
          )}
        </div>

        {/* Action Buttons for Terminal Failures */}
        {displayStatus === 'permanently_failed' && item.docId && (
          <div className="flex items-center gap-2 mt-4">
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => retryOcrMutation.mutate()}
              disabled={retryOcrMutation.isPending}
            >
              <RotateCw className="w-3 h-3 mr-2" />
              Retry OCR
            </Button>
            <Button 
              size="sm" 
              variant="outline" 
              onClick={() => retryChunkingMutation.mutate()}
              disabled={retryChunkingMutation.isPending}
            >
              <RotateCw className="w-3 h-3 mr-2" />
              Retry Chunking
            </Button>
          </div>
        )}

        {/* Review Needed Badge */}
        {statusData?.needs_human_review_pages != null && statusData.needs_human_review_pages > 0 && (
          <div className="mt-3">
            <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/50 dark:text-amber-300">
              ⚠ {statusData.needs_human_review_pages} pages need review
            </Badge>
          </div>
        )}

      </div>

      {isProcessing && (
        <Loader2 className={`w-5 h-5 animate-spin mt-1 ${iconColor}`} />
      )}
      {!isProcessing && (
        <StatusIcon className={`w-5 h-5 mt-1 ${iconColor}`} />
      )}
    </div>
  );
}
