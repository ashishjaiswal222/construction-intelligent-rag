'use client';

import * as React from 'react';
import { useDropzone } from 'react-dropzone';
import { useAppStore } from '@/store';
import { UploadCloud, FolderOpen } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface Props {
  onFilesAccepted: (files: File[]) => void;
}

export function UploadZone({ onFilesAccepted }: Props) {
  const { activeProject } = useAppStore();

  const onDrop = React.useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0 && activeProject) {
        onFilesAccepted(acceptedFiles);
      }
    },
    [activeProject, onFilesAccepted]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled: !activeProject,
  });

  if (!activeProject) {
    return (
      <div className="p-12 text-center border-2 border-dashed rounded-xl bg-card/50 flex flex-col items-center justify-center">
        <FolderOpen className="w-12 h-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">Select a Project First</h3>
        <p className="text-muted-foreground mt-2 max-w-sm">
          You must select a project from the top navigation bar before you can upload documents.
        </p>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        'p-12 border-2 border-dashed rounded-xl transition-colors cursor-pointer flex flex-col items-center justify-center text-center',
        isDragActive
          ? 'border-primary bg-primary/5'
          : 'border-muted hover:border-primary/50 hover:bg-muted/50'
      )}
    >
      <input {...getInputProps()} />
      <UploadCloud
        className={cn(
          'w-12 h-12 mb-4 transition-colors',
          isDragActive ? 'text-primary' : 'text-muted-foreground'
        )}
      />
      <h3 className="text-lg font-semibold mb-2">
        {isDragActive ? 'Drop files here...' : 'Drag & drop files here'}
      </h3>
      <p className="text-muted-foreground text-sm max-w-sm mb-6">
        Supports PDF, DOCX, XLSX, Images, and ZIP archives containing multiple documents.
      </p>
      <Button variant="secondary" disabled={!activeProject}>
        Browse Files
      </Button>
    </div>
  );
}
