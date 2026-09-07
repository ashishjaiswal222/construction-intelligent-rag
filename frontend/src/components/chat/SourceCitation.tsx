'use client';

import * as React from 'react';
import { Badge } from '@/components/ui/badge';
import { Citation } from '@/types';
import { FileText, Eye } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";

interface SourceProps {
  source: Citation;
  index: number;
}

export function SourceCitation({ source, index }: SourceProps) {
  return (
    <Dialog>
      <DialogTrigger
        render={
          <button type="button" className="flex flex-col gap-2 p-3 text-left rounded-md border bg-card text-sm w-full cursor-pointer hover:border-primary/50 transition-colors group" />
        }
      >
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="font-mono text-[10px] px-1.5 py-0.5 shrink-0">
            [{index}]
          </Badge>
          <FileText className="w-4 h-4 text-muted-foreground shrink-0 group-hover:text-primary transition-colors" />
          <p className="font-mono text-xs font-medium truncate flex-1" title={source.filename}>
            {source.filename}
          </p>
          {source.doc_type && (
            <Badge variant="outline" className="text-[10px] uppercase h-5 ml-2 shrink-0">
              {source.doc_type.replace('_', ' ')}
            </Badge>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
          {source.revision && <span className="bg-muted px-1.5 py-0.5 rounded">Rev {source.revision}</span>}
          {source.drawing_number && <span className="bg-muted px-1.5 py-0.5 rounded">Dwg: {source.drawing_number}</span>}
          {source.clause_number && <span className="bg-muted px-1.5 py-0.5 rounded">Clause: {source.clause_number}</span>}
          {source.page_number && <span className="bg-muted px-1.5 py-0.5 rounded">Page {source.page_number}</span>}
        </div>

        {source.excerpt && (
          <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded italic border-l-2 border-primary/30 mt-1 line-clamp-2 relative">
            "{source.excerpt}"
            <div className="absolute inset-y-0 right-0 w-8 bg-gradient-to-l from-muted/50 to-transparent flex items-center justify-end pr-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <Eye className="w-3 h-3 text-primary" />
            </div>
          </div>
        )}
      </DialogTrigger>
      
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-lg">
            <FileText className="w-5 h-5 text-primary" />
            {source.filename}
          </DialogTitle>
        </DialogHeader>
        
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground border-b pb-4">
          <Badge variant="outline" className="uppercase">
            {source.doc_type?.replace('_', ' ') || 'Document'}
          </Badge>
          {source.revision && <span>• Revision: {source.revision}</span>}
          {source.drawing_number && <span>• Drawing: {source.drawing_number}</span>}
          {source.clause_number && <span>• Clause: {source.clause_number}</span>}
          {source.page_number && <span>• Page: {source.page_number}</span>}
        </div>
        
        <div className="flex-1 overflow-auto bg-muted/30 p-4 rounded-md mt-2">
          <p className="text-sm leading-relaxed whitespace-pre-wrap font-mono">
            {source.excerpt}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
