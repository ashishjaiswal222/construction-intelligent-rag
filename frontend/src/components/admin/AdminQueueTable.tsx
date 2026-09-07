'use client';

import * as React from 'react';
import { AdminQueueItem } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { AlertCircle, FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { reviewDocumentAction } from '@/lib/api/admin';
import { CheckCircle2, XCircle } from 'lucide-react';

interface Props {
  items: AdminQueueItem[];
}

export function AdminQueueTable({ items }: Props) {
  const [expandedRow, setExpandedRow] = React.useState<string | null>(null);
  const [overrideCategory, setOverrideCategory] = React.useState<Record<string, string>>({});
  const queryClient = useQueryClient();

  const actionMutation = useMutation({
    mutationFn: ({ docId, action, docType }: { docId: string; action: 'approve' | 'reject'; docType?: string }) =>
      reviewDocumentAction(docId, action, docType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminQueue'] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['docStatus'] });
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    },
  });

  if (items.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground flex flex-col items-center">
        <FileText className="w-8 h-8 mb-2 opacity-20" />
        <p>The queue is empty.</p>
        <p className="text-sm">No documents currently need review or have permanently failed.</p>
      </div>
    );
  }

  const getFailedStageBadge = (stage: string | null) => {
    switch (stage) {
      case 'classification':
        return <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100 dark:bg-purple-900/50 dark:text-purple-300">Classification</Badge>;
      case 'ocr':
        return <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100 dark:bg-blue-900/50 dark:text-blue-300">OCR</Badge>;
      case 'refinement':
        return <Badge className="bg-violet-100 text-violet-800 hover:bg-violet-100 dark:bg-violet-900/50 dark:text-violet-300">Refinement</Badge>;
      case 'chunking':
        return <Badge className="bg-orange-100 text-orange-800 hover:bg-orange-100 dark:bg-orange-900/50 dark:text-orange-300">Chunking</Badge>;
      default:
        return <Badge variant="outline" className="text-muted-foreground">Unknown</Badge>;
    }
  };

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[30px]"></TableHead>
          <TableHead>Filename</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Failed Stage</TableHead>
          <TableHead>Conf.</TableHead>
          <TableHead>Submitted</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {items.map((item) => (
          <React.Fragment key={item.doc_id}>
            <TableRow 
              className={`hover:bg-muted/50 ${expandedRow === item.doc_id ? 'bg-muted/50' : ''}`}
            >
              <TableCell 
                className="cursor-pointer"
                onClick={() => setExpandedRow(expandedRow === item.doc_id ? null : item.doc_id)}
              >
                {expandedRow === item.doc_id ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
              </TableCell>
              <TableCell className="font-mono text-sm max-w-[200px] truncate" title={item.filename}>
                {item.filename}
              </TableCell>
              <TableCell>
                <StatusBadge status={item.status} />
              </TableCell>
              <TableCell>
                {item.doc_type ? (
                  <Badge variant="outline" className="capitalize">{item.doc_type.replace('_', ' ')}</Badge>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                {getFailedStageBadge(item.last_error_stage)}
              </TableCell>
              <TableCell className="font-mono text-xs">
                {item.classification_confidence 
                  ? `${(item.classification_confidence * 100).toFixed(0)}%` 
                  : '-'}
              </TableCell>
              <TableCell className="text-xs text-muted-foreground whitespace-nowrap">
                {new Date(item.created_at).toLocaleString(undefined, { 
                  month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' 
                })}
              </TableCell>
              <TableCell className="text-right">
                <div className="flex items-center justify-end gap-2">
                  <select
                    className="text-xs border rounded px-2 py-1 bg-background text-foreground"
                    value={overrideCategory[item.doc_id] || item.doc_type || 'specification'}
                    onChange={(e) => setOverrideCategory({ ...overrideCategory, [item.doc_id]: e.target.value })}
                  >
                    <option value="contract">Contract</option>
                    <option value="boq">Bill of Quantities (BOQ)</option>
                    <option value="drawing">Drawing</option>
                    <option value="specification">Specification</option>
                    <option value="rfi">RFI</option>
                    <option value="site_log">Site Log</option>
                    <option value="invoice">Invoice</option>
                    <option value="safety">Safety</option>
                    <option value="inspection">Inspection</option>
                  </select>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 dark:hover:bg-emerald-950/50"
                    disabled={actionMutation.isPending}
                    onClick={() => actionMutation.mutate({ docId: item.doc_id, action: 'approve', docType: overrideCategory[item.doc_id] || item.doc_type || 'specification' })}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                    Approve & Process
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-8 text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/50"
                    disabled={actionMutation.isPending}
                    onClick={() => actionMutation.mutate({ docId: item.doc_id, action: 'reject' })}
                  >
                    <XCircle className="w-3.5 h-3.5 mr-1" />
                    Reject & Purge
                  </Button>
                </div>
              </TableCell>
            </TableRow>
            
            {/* Expanded Details */}
            {expandedRow === item.doc_id && (
              <TableRow className="bg-muted/30">
                <TableCell colSpan={8} className="p-0">
                  <div className="p-4 pl-12 border-l-2 border-amber-500 m-2 bg-card rounded-r-md">
                    <div className="flex items-center gap-2 text-amber-600 mb-2 font-semibold text-sm">
                      <AlertCircle className="w-4 h-4" />
                      Review Details
                    </div>
                    {item.error_message ? (
                      <pre className="text-xs font-mono bg-muted p-3 rounded-md overflow-x-auto text-muted-foreground border">
                        {item.error_message}
                      </pre>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        This document was classified as &quot;{item.doc_type || 'unknown'}&quot; with low confidence ({((item.classification_confidence || 0) * 100).toFixed(0)}%). Pipeline halted to save resources. Approving it will reassign category and trigger OCR/Indexing. Rejecting it will purge all data.
                      </p>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            )}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>
  );
}
