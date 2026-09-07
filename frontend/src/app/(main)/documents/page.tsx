import { DocumentsTable } from '@/components/documents/DocumentsTable';

export default function DocumentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Documents</h2>
        <p className="text-muted-foreground">Browse and search the centralized document repository.</p>
      </div>
      <DocumentsTable />
    </div>
  );
}
