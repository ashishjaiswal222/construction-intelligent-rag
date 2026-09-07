import * as React from 'react';
import { Document } from '@/types';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { Image as ImageIcon, Table2, PenTool, AlertTriangle, Layers } from 'lucide-react';

export function InfoTab({ doc }: { doc: Document }) {
  return (
    <div className="grid gap-6">
      <div className="grid grid-cols-2 gap-y-4 gap-x-6">
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Document ID</span>
          <p className="font-mono text-xs">{doc.doc_id}</p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Status</span>
          <div><StatusBadge status={doc.status} /></div>
        </div>
        
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Type / Sub Type</span>
          <p className="font-medium capitalize">
            {doc.doc_type?.replace('_', ' ') || 'Unknown'} {doc.doc_sub_type ? `/ ${doc.doc_sub_type}` : ''}
          </p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Revision</span>
          <p className="font-mono font-medium">{doc.revision || '-'}</p>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Approval Status</span>
          <p className="font-medium">{doc.approval_status || '-'}</p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Is Current</span>
          <p className="font-medium">{doc.is_current ? 'Yes' : 'No'}</p>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">File Size & Pages</span>
          <p className="font-medium">
            {doc.file_size_bytes ? `${(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : '-'}
            {doc.page_count != null ? ` • ${doc.page_count} pages` : ''}
          </p>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Language</span>
          <p className="font-medium uppercase">{doc.language || 'EN'}</p>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">OCR Method</span>
          <div>
            <Badge variant="outline">{doc.ocr_method || '-'}</Badge>
          </div>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Classification Conf.</span>
          <p className="font-mono font-medium">
            {doc.classification_confidence ? `${(doc.classification_confidence * 100).toFixed(1)}%` : '-'}
          </p>
        </div>

        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Content Flags</span>
          <div className="flex gap-2 mt-1">
            {doc.has_images && <Badge variant="secondary" className="px-1.5"><ImageIcon className="w-3 h-3 mr-1"/> Images</Badge>}
            {doc.has_tables && <Badge variant="secondary" className="px-1.5"><Table2 className="w-3 h-3 mr-1"/> Tables</Badge>}
            {doc.has_drawings && <Badge variant="secondary" className="px-1.5"><Layers className="w-3 h-3 mr-1"/> Drawings</Badge>}
            {doc.has_handwriting && <Badge variant="secondary" className="px-1.5"><PenTool className="w-3 h-3 mr-1"/> Handwriting</Badge>}
            {!doc.has_images && !doc.has_tables && !doc.has_drawings && !doc.has_handwriting && <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
        <div className="space-y-1">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Retries</span>
          <p className="font-medium">{doc.retry_count || 0}</p>
        </div>
      </div>

      {doc.error_message && (
        <div className="p-3 bg-red-50 text-red-900 border border-red-200 rounded-md">
          <div className="text-xs font-semibold mb-1 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Error Message</div>
          <p className="text-sm font-mono whitespace-pre-wrap break-all">{doc.error_message}</p>
        </div>
      )}

      <div className="pt-4 mt-2 border-t flex justify-between text-xs text-muted-foreground">
        <span>Created: {new Date(doc.created_at).toLocaleString()}</span>
        <span>Updated: {new Date(doc.updated_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
