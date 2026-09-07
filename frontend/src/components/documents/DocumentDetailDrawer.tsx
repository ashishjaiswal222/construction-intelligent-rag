'use client';

import * as React from 'react';
import { Document } from '@/types';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { InfoTab } from './tabs/InfoTab';
import { PipelineTab } from './tabs/PipelineTab';
import { MetadataTab } from './tabs/MetadataTab';
import { ViewerTab } from './tabs/ViewerTab';

interface Props {
  document: Document | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DocumentDetailDrawer({ document: doc, open, onOpenChange }: Props) {
  if (!doc) return null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[800px] h-[85vh] flex flex-col p-0 gap-0">
        <div className="p-6 pb-4 border-b">
          <DialogHeader>
            <DialogTitle className="font-mono break-all text-lg">{doc.filename}</DialogTitle>
            <DialogDescription>
              Document Details & Processing Pipeline
            </DialogDescription>
          </DialogHeader>
        </div>
        
        <Tabs defaultValue="viewer" className="flex-1 flex flex-col min-h-0">
          <div className="px-6 border-b bg-muted/20">
            <TabsList className="w-full justify-start h-12 bg-transparent">
              <TabsTrigger value="viewer" className="data-[state=active]:bg-background">Viewer</TabsTrigger>
              <TabsTrigger value="info" className="data-[state=active]:bg-background">General Info</TabsTrigger>
              <TabsTrigger value="metadata" className="data-[state=active]:bg-background">Extracted Metadata</TabsTrigger>
              <TabsTrigger value="pipeline" className="data-[state=active]:bg-background">Pipeline & Processing</TabsTrigger>
            </TabsList>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-6">
              <TabsContent value="viewer" className="mt-0 outline-none">
                <ViewerTab doc={doc} />
              </TabsContent>
              <TabsContent value="info" className="mt-0 outline-none">
                <InfoTab doc={doc} />
              </TabsContent>
              <TabsContent value="metadata" className="mt-0 outline-none">
                <MetadataTab docId={doc.doc_id} />
              </TabsContent>
              <TabsContent value="pipeline" className="mt-0 outline-none">
                <PipelineTab docId={doc.doc_id} />
              </TabsContent>
            </div>
          </ScrollArea>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
