'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { AdminQueueItem, RefinementPageReview } from '@/types';
import { getRefinementReviewQueue } from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronRight, FileSearch, Loader2, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  documents: AdminQueueItem[];
}

export function RefinementReviewTable({ documents }: Props) {
  const [expandedDoc, setExpandedDoc] = React.useState<string | null>(null);

  if (documents.length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground flex flex-col items-center">
        <FileSearch className="w-8 h-8 mb-2 opacity-20" />
        <p>No refinement review needed.</p>
        <p className="text-sm">All semantic refinement checks passed quality thresholds.</p>
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-[30px]"></TableHead>
          <TableHead>Filename</TableHead>
          <TableHead>Pages to Review</TableHead>
          <TableHead>Pages Failed</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <React.Fragment key={doc.doc_id}>
            <TableRow 
              className={`cursor-pointer hover:bg-muted/50 ${expandedDoc === doc.doc_id ? 'bg-muted/50' : ''}`}
              onClick={() => setExpandedDoc(expandedDoc === doc.doc_id ? null : doc.doc_id)}
            >
              <TableCell>
                {expandedDoc === doc.doc_id ? (
                  <ChevronDown className="w-4 h-4 text-muted-foreground" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-muted-foreground" />
                )}
              </TableCell>
              <TableCell className="font-mono text-sm max-w-[300px] truncate" title={doc.filename}>
                {doc.filename}
              </TableCell>
              <TableCell>
                <Badge variant="secondary" className="bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-900/50 dark:text-amber-300">
                  {doc.needs_human_review_pages} pages
                </Badge>
              </TableCell>
              <TableCell>
                {doc.refinement_failed_pages > 0 ? (
                  <Badge variant="destructive">{doc.refinement_failed_pages} pages</Badge>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </TableCell>
              <TableCell>
                <Button size="sm" variant="ghost">Review Details</Button>
              </TableCell>
            </TableRow>
            
            {/* Expanded Pages List */}
            {expandedDoc === doc.doc_id && (
              <TableRow className="bg-muted/10">
                <TableCell colSpan={5} className="p-0">
                  <div className="p-4 border-l-2 border-amber-500 m-2 bg-card rounded-r-md">
                    <RefinementPagesList documentId={doc.doc_id} />
                  </div>
                </TableCell>
              </TableRow>
            )}
          </React.Fragment>
        ))}
      </TableBody>
    </Table>
  );
}

function RefinementPagesList({ documentId }: { documentId: string }) {
  const { data: pages, isLoading, error } = useQuery({
    queryKey: ['refinementReview', documentId],
    queryFn: () => getRefinementReviewQueue(documentId),
  });

  if (isLoading) {
    return <div className="flex items-center gap-2 text-sm text-muted-foreground py-4"><Loader2 className="w-4 h-4 animate-spin" /> Loading pages...</div>;
  }

  if (error || !pages) {
    return <div className="text-sm text-red-500 py-4">Failed to load pages for review.</div>;
  }

  if (pages.length === 0) {
    return <div className="text-sm text-muted-foreground py-4">No pages found for review in this document.</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-amber-700 dark:text-amber-500">
        <Info className="w-4 h-4" />
        Pages flagged during Phase 3 Refinement
      </div>
      
      <div className="border rounded-md overflow-hidden bg-background">
        <Table>
          <TableHeader className="bg-muted/50">
            <TableRow>
              <TableHead className="w-20">Page</TableHead>
              <TableHead>Quality Change</TableHead>
              <TableHead>Level</TableHead>
              <TableHead>Flags</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pages.map((page) => (
              <TableRow key={page.page_id}>
                <TableCell className="font-mono font-medium">{page.page_number}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-muted-foreground">{(page.quality_before * 100).toFixed(0)}%</span>
                    <span>&rarr;</span>
                    <span className="font-bold text-red-600">{(page.quality_after * 100).toFixed(0)}%</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="uppercase text-[10px]">{page.refinement_level}</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex gap-1 flex-wrap">
                    {page.refinement_flags.map((flag, idx) => (
                      <Badge key={idx} variant="secondary" className="text-[10px]">{flag}</Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Button size="sm" variant="outline" className="h-7 text-xs">Verify Content</Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
