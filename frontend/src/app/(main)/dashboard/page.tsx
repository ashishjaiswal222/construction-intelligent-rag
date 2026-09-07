import { KpiGrid } from '@/components/dashboard/KpiGrid';

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">Platform performance and system metrics.</p>
      </div>
      <KpiGrid />
    </div>
  );
}
