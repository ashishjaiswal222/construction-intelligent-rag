'use client';

import * as React from 'react';
import { UploadZone } from '@/components/upload/UploadZone';
import { UploadQueueItem } from '@/components/upload/UploadQueueItem';
import { useAppStore } from '@/store';
import { uploadDocuments } from '@/lib/api';
import { toast } from 'sonner';

type UploadQueueState = {
  docId?: string;
  filename: string;
  size?: number;
  initialStatus: string;
  reason?: string;
  existing_id?: string;
};

export default function UploadPage() {
  const { activeProject } = useAppStore();
  const [queue, setQueue] = React.useState<UploadQueueState[]>([]);

  const handleFilesAccepted = async (files: File[]) => {
    if (!activeProject) return;

    // Add placeholder items
    const tempIds = files.map((f, i) => ({
      docId: `temp-${Date.now()}-${i}`,
      filename: f.name,
      size: f.size,
      initialStatus: 'uploading' as const,
    }));

    setQueue((prev) => [...tempIds, ...prev]);

    try {
      const response = await uploadDocuments(activeProject.project_id, files);
      
      // Replace temp IDs with real results
      setQueue((prev) => {
        const next = [...prev];
        response.results.forEach((result, idx) => {
          const tempId = tempIds[idx].docId;
          const qIdx = next.findIndex(q => q.docId === tempId);
          if (qIdx !== -1) {
            next[qIdx] = {
              docId: result.doc_id,
              filename: result.filename,
              size: files[idx].size,
              initialStatus: result.status,
              reason: result.reason,
              existing_id: result.existing_id,
            };
          }
        });
        return next;
      });

      toast.success(`Successfully queued ${response.uploaded} documents`);
    } catch (error) {
      toast.error('Upload failed. Please try again.');
      // Mark temps as failed if network error
      setQueue((prev) => prev.map(item => 
        tempIds.some(t => t.docId === item.docId) 
          ? { ...item, initialStatus: 'rejected', reason: 'Network Error' }
          : item
      ));
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Upload Documents</h2>
        <p className="text-muted-foreground">Upload and process files for the active project.</p>
      </div>

      {activeProject ? (
        <div className="bg-primary/10 border border-primary/20 rounded-md p-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-primary/20 flex items-center justify-center text-primary font-bold">
            {activeProject.name.charAt(0)}
          </div>
          <div>
            <p className="text-sm font-medium text-primary">Active Silo: {activeProject.name}</p>
            <p className="text-xs text-primary/80">Files uploaded here will be strictly isolated to this project.</p>
          </div>
        </div>
      ) : (
        <div className="bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-900 rounded-md p-4 text-amber-800 dark:text-amber-200 text-sm">
          No project selected. Please select a project from the top navigation bar before uploading files.
        </div>
      )}

      <UploadZone onFilesAccepted={handleFilesAccepted} />

      {queue.length > 0 && (
        <div className="space-y-4 mt-8">
          <h3 className="text-lg font-semibold">Processing Queue</h3>
          <div className="space-y-3">
            {queue.map((item) => (
              <UploadQueueItem 
                key={item.docId} 
                item={item} 
                onRemove={(docId) => setQueue(prev => prev.filter(q => q.docId !== docId))}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
