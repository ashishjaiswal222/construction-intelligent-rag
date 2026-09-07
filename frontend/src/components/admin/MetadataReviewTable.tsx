import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getReviewQueue, verifyMetadata, ExtractedMetadata } from '@/lib/api/metadata';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { CheckCircle2, Edit2, Loader2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';
import { MetadataEditDialog } from './MetadataEditDialog';

export function MetadataReviewTable() {
  const queryClient = useQueryClient();
  const [selectedDoc, setSelectedDoc] = React.useState<ExtractedMetadata | null>(null);

  const { data: queue = [], isLoading } = useQuery({
    queryKey: ['metadataQueue'],
    queryFn: getReviewQueue,
    refetchInterval: 10000,
  });

  const verifyMutation = useMutation({
    mutationFn: (docId: string) => verifyMetadata(docId),
    onSuccess: () => {
      toast.success('Document metadata verified');
      queryClient.invalidateQueries({ queryKey: ['metadataQueue'] });
    },
    onError: (err: any) => toast.error(`Failed to verify: ${err.message}`),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (queue.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground border-t border-dashed mt-4 rounded-lg">
        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-500 opacity-50" />
        No documents pending metadata review. The queue is clear!
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Document</TableHead>
            <TableHead>Created</TableHead>
            <TableHead>Confidence</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {queue.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell>
                <div className="font-medium text-sm truncate max-w-[250px]" title={doc.filename || 'Unknown'}>
                  {doc.filename || 'Unknown'}
                </div>
                <div className="text-[10px] text-muted-foreground font-mono mt-0.5" title={doc.document_id}>
                  {doc.document_id.split('-')[0]}...
                </div>
              </TableCell>
              <TableCell className="text-sm">{new Date(doc.created_at).toLocaleDateString()}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-500" />
                  <span className="font-medium text-amber-700">{(doc.metadata_confidence * 100).toFixed(0)}%</span>
                </div>
              </TableCell>
              <TableCell className="text-right">
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mr-2"
                  onClick={() => setSelectedDoc(doc)}
                >
                  <Edit2 className="w-3 h-3 mr-1" /> Review & Edit
                </Button>
                <Button 
                  size="sm"
                  onClick={() => verifyMutation.mutate(doc.document_id)}
                  disabled={verifyMutation.isPending}
                >
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Approve As-Is
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <MetadataEditDialog 
        doc={selectedDoc} 
        open={!!selectedDoc} 
        onOpenChange={(open) => !open && setSelectedDoc(null)} 
      />
    </div>
  );
}
