'use client';

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocuments, deleteDocument } from '@/lib/api';
import { useAppStore } from '@/store';
import { formatDistanceToNow } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Filter, RefreshCcw, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { Input } from '@/components/ui/input';
import { DocumentDetailDrawer } from './DocumentDetailDrawer';
import { Document } from '@/types';

export function DocumentsTable() {
  const { activeProject } = useAppStore();
  const [docTypeFilter, setDocTypeFilter] = React.useState('');
  const [revFilter, setRevFilter] = React.useState('');
  
  const { selectedDocId, setSelectedDocId } = useAppStore();
  const [selectedDoc, setSelectedDoc] = React.useState<Document | null>(null);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => {
      toast.success('Document deleted successfully');
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (err: any) => {
      toast.error(err.message || 'Failed to delete document');
    }
  });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['documents', activeProject?.project_id, docTypeFilter, revFilter],
    queryFn: () => getDocuments({
      project_id: activeProject?.project_id,
      doc_type: docTypeFilter || undefined,
      revision: revFilter || undefined,
    }),
    enabled: !!activeProject,
  });

  const documents = data?.documents || [];

  React.useEffect(() => {
    if (selectedDocId && documents.length > 0) {
      const match = documents.find((d) => d.doc_id === selectedDocId);
      if (match) setSelectedDoc(match);
    }
  }, [selectedDocId, documents]);

  if (!activeProject) {
    return (
      <div className="p-8 text-center border rounded-lg bg-card">
        <h3 className="text-lg font-medium">No Project Selected</h3>
        <p className="text-muted-foreground mt-2">Please select a project from the top bar to view its documents.</p>
      </div>
    );
  }

  const getApprovalColor = (status: string | null) => {
    switch (status) {
      case 'IFC': return 'bg-emerald-500 hover:bg-emerald-600 text-white';
      case 'Superseded': return 'bg-gray-400 hover:bg-gray-500 text-white';
      case 'Draft': return 'bg-amber-500 hover:bg-amber-600 text-white';
      case 'Approved': return 'bg-blue-500 hover:bg-blue-600 text-white';
      default: return 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 items-end">
        <div className="space-y-1.5 flex-1 min-w-[200px] max-w-[300px]">
          <label className="text-xs font-medium text-muted-foreground">Document Type</label>
          <div className="relative">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="e.g. drawing, boq" 
              className="pl-8"
              value={docTypeFilter}
              onChange={(e) => setDocTypeFilter(e.target.value)}
            />
          </div>
        </div>
        <div className="space-y-1.5 w-[150px]">
          <label className="text-xs font-medium text-muted-foreground">Revision</label>
          <Input 
            placeholder="e.g. 01" 
            value={revFilter}
            onChange={(e) => setRevFilter(e.target.value)}
          />
        </div>
        <Button variant="outline" onClick={() => refetch()} className="shrink-0 gap-2">
          <RefreshCcw className="w-4 h-4" />
          Refresh
        </Button>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Filename</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Rev</TableHead>
              <TableHead>Approval</TableHead>
              <TableHead>Class Conf.</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Age</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              [1, 2, 3, 4].map(i => (
                <TableRow key={i}>
                  <TableCell colSpan={8}>
                    <Skeleton className="h-8 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : isError ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-red-500 py-6">
                  Failed to load documents
                </TableCell>
              </TableRow>
            ) : documents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-12 text-muted-foreground">
                  No documents found matching the current filters.
                </TableCell>
              </TableRow>
            ) : (
              documents.map((doc) => (
                <TableRow 
                  key={doc.doc_id} 
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => {
                    setSelectedDoc(doc);
                    setSelectedDocId(doc.doc_id);
                  }}
                >
                  <TableCell className="font-mono text-sm max-w-[250px] truncate" title={doc.filename}>
                    {doc.filename}
                  </TableCell>
                  <TableCell>
                    {doc.doc_type ? (
                      <Badge variant="outline" className="capitalize">{doc.doc_type.replace('_', ' ')}</Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">Unknown</span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-sm">{doc.revision || '-'}</TableCell>
                  <TableCell>
                    {doc.approval_status ? (
                      <Badge className={getApprovalColor(doc.approval_status)}>{doc.approval_status}</Badge>
                    ) : '-'}
                  </TableCell>
                  <TableCell className="text-sm">
                    {doc.classification_confidence ? `${(doc.classification_confidence * 100).toFixed(0)}%` : '-'}
                  </TableCell>
                  <TableCell>
                    <Badge variant={doc.status === 'indexed' ? 'default' : doc.status.includes('fail') ? 'destructive' : 'secondary'}>
                      {doc.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground whitespace-nowrap text-xs">
                    {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/50"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (window.confirm(`Are you sure you want to permanently delete "${doc.filename}"? This will delete all parsed data and vector chunks.`)) {
                          deleteMutation.mutate(doc.doc_id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      <DocumentDetailDrawer 
        document={selectedDoc} 
        open={!!selectedDoc} 
        onOpenChange={(isOpen) => {
          if (!isOpen) {
            setSelectedDoc(null);
            setSelectedDocId(null);
          }
        }} 
      />
    </div>
  );
}
