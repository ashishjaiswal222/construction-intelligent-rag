import * as React from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { overrideMetadata, ExtractedMetadata } from '@/lib/api/metadata';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface Props {
  doc: ExtractedMetadata | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function MetadataEditDialog({ doc, open, onOpenChange }: Props) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = React.useState<Partial<ExtractedMetadata>>({});

  React.useEffect(() => {
    if (doc) {
      setFormData(doc);
    }
  }, [doc]);

  const overrideMutation = useMutation({
    mutationFn: (updates: Partial<ExtractedMetadata>) => overrideMetadata(doc!.document_id, updates),
    onSuccess: () => {
      toast.success('Metadata updated and verified');
      queryClient.invalidateQueries({ queryKey: ['metadataQueue'] });
      queryClient.invalidateQueries({ queryKey: ['adminQueue'] });
      onOpenChange(false);
    },
    onError: (err: any) => toast.error(`Update failed: ${err.message}`),
  });

  if (!doc) return null;

  const editableFields = [
    'title', 'doc_number', 'revision', 'drawing_number', 'discipline', 
    'project_name', 'document_date', 'approval_status', 'risk_level'
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl max-h-[90vh] flex flex-col p-6">
        <DialogHeader>
          <DialogTitle className="text-lg font-bold">Review & Verify Document Metadata</DialogTitle>
        </DialogHeader>
        
        <div className="bg-amber-50 border border-amber-200 text-amber-900 p-3 rounded-md text-xs font-medium my-2">
          <strong>Confidence: {(doc.metadata_confidence * 100).toFixed(0)}%.</strong> The AI extracted fields with low confidence. Please verify or correct fields below and click <strong>Save & Verify</strong>.
        </div>

        <ScrollArea className="flex-1 max-h-[50vh] pr-4 my-2">
          <div className="grid gap-3 py-2">
            {editableFields.map((field) => (
              <div key={field} className="grid grid-cols-4 items-center gap-3">
                <Label htmlFor={field} className="text-right capitalize text-xs font-mono font-medium text-muted-foreground">
                  {field.replace('_', ' ')}
                </Label>
                <Input
                  id={field}
                  value={formData[field as keyof ExtractedMetadata] as string || ''}
                  onChange={(e) => setFormData({ ...formData, [field]: e.target.value })}
                  className="col-span-3 h-9 text-sm"
                  placeholder={`Enter ${field.replace('_', ' ')}`}
                />
              </div>
            ))}
          </div>
        </ScrollArea>
        
        <DialogFooter className="pt-4 border-t flex justify-end gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button 
            size="sm"
            variant="default"
            className="bg-primary text-primary-foreground font-semibold px-4"
            onClick={() => overrideMutation.mutate(formData)}
            disabled={overrideMutation.isPending}
          >
            {overrideMutation.isPending && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
            Save & Verify Metadata
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
