import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDocumentMetadata, verifyMetadata } from '@/lib/api/metadata';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Loader2, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export function MetadataTab({ docId }: { docId: string }) {
  const queryClient = useQueryClient();

  const { data: metadata, isLoading, isError } = useQuery({
    queryKey: ['metadata', docId],
    queryFn: () => getDocumentMetadata(docId),
  });

  const verifyMutation = useMutation({
    mutationFn: () => verifyMetadata(docId),
    onSuccess: () => {
      toast.success('Metadata verified');
      queryClient.invalidateQueries({ queryKey: ['metadata', docId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  if (isLoading) return <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>;
  if (isError || !metadata || Object.keys(metadata).length === 0) {
    return <div className="p-8 text-center text-muted-foreground">No extracted metadata available for this document.</div>;
  }

  const confidence = metadata.metadata_confidence * 100;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between p-4 border rounded-lg bg-card">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-lg">Extraction Confidence</h3>
            <Badge variant={confidence > 70 ? 'default' : confidence > 30 ? 'secondary' : 'destructive'}>
              {confidence.toFixed(1)}%
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">Confidence in automatically extracted values.</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            {metadata.manually_verified ? (
              <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200">
                <CheckCircle2 className="w-3 h-3 mr-1" /> Verified
              </Badge>
            ) : (
              <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                <AlertTriangle className="w-3 h-3 mr-1" /> Pending Review
              </Badge>
            )}
          </div>
          {!metadata.manually_verified && (
            <Button size="sm" onClick={() => verifyMutation.mutate()} disabled={verifyMutation.isPending}>
              Verify All
            </Button>
          )}
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead className="w-1/3">Field</TableHead>
              <TableHead>Extracted Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {Object.entries(metadata).map(([key, value]) => {
              // Skip internal fields
              if (['id', 'document_id', 'metadata_confidence', 'manually_verified', 'created_at', 'updated_at'].includes(key)) return null;
              
              const displayValue = value === null || value === '' ? (
                <span className="text-muted-foreground italic">Not found</span>
              ) : typeof value === 'boolean' ? (
                value ? 'Yes' : 'No'
              ) : (
                String(value)
              );

              return (
                <TableRow key={key}>
                  <TableCell className="font-medium text-xs font-mono">{key}</TableCell>
                  <TableCell className="text-sm">{displayValue}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
