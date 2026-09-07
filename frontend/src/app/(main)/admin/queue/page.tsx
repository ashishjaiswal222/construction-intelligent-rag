'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAdminQueue } from '@/lib/api';
import { getReviewQueue as getMetadataQueue } from '@/lib/api/metadata';
import { AdminQueueTable } from '@/components/admin/AdminQueueTable';
import { RefinementReviewTable } from '@/components/admin/RefinementReviewTable';
import { MetadataReviewTable } from '@/components/admin/MetadataReviewTable';
import { ShieldAlert, Loader2 } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

export default function AdminQueuePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['adminQueue'],
    queryFn: getAdminQueue,
    refetchInterval: 10000,
  });

  const { data: metadataData } = useQuery({
    queryKey: ['metadataQueue'],
    queryFn: getMetadataQueue,
    refetchInterval: 10000,
  });

  const queue = data?.queue || [];
  const metadataQueueCount = metadataData?.length || 0;
  
  // Documents that need refinement review
  const refinementQueue = queue.filter(doc => doc.needs_human_review_pages > 0);
  
  // Documents in classification or other general failure states
  const classificationQueue = queue;

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-primary" />
            Admin Review Queue
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Documents requiring manual intervention or review.
          </p>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64 border rounded-lg bg-card">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="p-4 bg-red-50 text-red-900 border border-red-200 rounded-lg">
          Failed to load queue. Please try again later.
        </div>
      ) : (
        <Tabs defaultValue="classification" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="classification">
              Classification & Failures
              <span className="ml-2 bg-muted text-muted-foreground text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                {classificationQueue.length}
              </span>
            </TabsTrigger>
            <TabsTrigger value="refinement">
              Refinement Review
              {refinementQueue.length > 0 && (
                <span className="ml-2 bg-amber-100 text-amber-700 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                  {refinementQueue.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="metadata">
              Metadata Extraction Review
              {metadataQueueCount > 0 && (
                <span className="ml-2 bg-purple-100 text-purple-700 text-[10px] px-1.5 py-0.5 rounded-full font-bold">
                  {metadataQueueCount}
                </span>
              )}
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="classification" className="outline-none">
            <div className="border rounded-lg bg-card overflow-hidden">
              <AdminQueueTable items={classificationQueue} />
            </div>
          </TabsContent>
          
          <TabsContent value="refinement" className="outline-none">
            <div className="border rounded-lg bg-card overflow-hidden p-4">
              <RefinementReviewTable documents={refinementQueue} />
            </div>
          </TabsContent>
          
          <TabsContent value="metadata" className="outline-none">
            <div className="border rounded-lg bg-card overflow-hidden p-4">
              <MetadataReviewTable />
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
