'use client';

import * as React from 'react';
import { Document } from '@/types';
import { FileText, Download } from 'lucide-react';
import { buttonVariants } from '@/components/ui/button';

interface Props {
  doc: Document;
}

export function ViewerTab({ doc }: Props) {
  if (!doc.file_url) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center border rounded-lg bg-muted/20">
        <FileText className="w-12 h-12 text-muted-foreground mb-4" />
        <h3 className="text-lg font-medium">No File Available</h3>
        <p className="text-muted-foreground max-w-sm mt-2">
          The original document file could not be located or was not uploaded correctly.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[65vh]">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-muted-foreground">Previewing original document</p>
        <a 
          href={doc.file_url} 
          target="_blank" 
          rel="noopener noreferrer"
          className={buttonVariants({ variant: 'outline', size: 'sm' })}
        >
          <Download className="w-4 h-4 mr-2" />
          Download
        </a>
      </div>
      <div className="flex-1 border rounded-lg overflow-hidden bg-white dark:bg-zinc-900">
        {doc.mime_type === 'application/pdf' || doc.file_url?.toLowerCase().endsWith('.pdf') || doc.filename?.toLowerCase().endsWith('.pdf') ? (
          <iframe 
            src={`${doc.file_url}#view=FitH`} 
            className="w-full h-full border-0" 
            title={doc.filename}
          />
        ) : doc.mime_type?.startsWith('image/') || doc.file_url?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/i) || doc.filename?.toLowerCase().match(/\.(jpg|jpeg|png|gif|webp)$/i) ? (
          <div className="w-full h-full flex items-center justify-center bg-muted/20 p-4">
            <img 
              src={doc.file_url} 
              alt={doc.filename}
              className="max-w-full max-h-full object-contain rounded"
            />
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full p-8 text-center bg-muted/10">
            <FileText className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium">Preview Not Available</h3>
            <p className="text-muted-foreground max-w-sm mt-2">
              Preview is not supported for {doc.mime_type || 'this file type'}. Please download the file to view its contents.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
