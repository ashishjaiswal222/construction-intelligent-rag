'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMetrics } from '@/lib/api';
import { useAppStore } from '@/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface KpiConfig {
  key: keyof import('@/types').MetricsResponse;
  label: string;
  format: (val: number | null) => string;
  getColor: (val: number | null) => string;
}

// target <8s, alert >15s
// retrieval_hit_rate: target >88%, alert <75%
// crag_rejection_rate: target <15%, alert >30%
// llm_error_rate: target <1%, alert >5%
// token_cost_per_query_inr: target <0.50, alert >2
// ocr_confidence_avg: target >85%, alert <75%
// queue_depth: target <50, alert >200
// human_review_queue_size: target <20, alert >100
// ragas_faithfulness: target >0.85, alert <0.75
// thumbs_up_rate: target >80%, alert <60%

const formatPct = (val: number | null) => val != null ? `${(val * (val <= 1 ? 100 : 1)).toFixed(1)}%` : 'N/A';
const formatNum = (val: number | null) => val != null ? val.toLocaleString() : 'N/A';
const formatSec = (val: number | null) => val != null ? `${val.toFixed(2)}s` : 'N/A';
const formatCurrency = (val: number | null) => {
  if (val == null) return 'N/A';
  const rupees = val / 100;
  if (rupees >= 0.01) return `₹${rupees.toFixed(2)}`;
  return `₹${rupees.toFixed(4)}`;
};

const KPI_CONFIGS: KpiConfig[] = [
  {
    key: 'query_latency_p95_seconds',
    label: 'Query Latency (P95)',
    format: formatSec,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 15 ? 'bg-red-500' : val < 8 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'retrieval_hit_rate',
    label: 'Retrieval Hit Rate',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val < 0.75 ? 'bg-red-500' : val > 0.88 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'crag_rejection_rate',
    label: 'CRAG Rejection Rate',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 0.3 ? 'bg-red-500' : val < 0.15 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'llm_error_rate',
    label: 'LLM Error Rate',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 0.05 ? 'bg-red-500' : val < 0.01 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'cost_per_query_paise',
    label: 'Cost per Query',
    format: formatCurrency,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 200 ? 'bg-red-500' : val < 50 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'classification_confidence_avg',
    label: 'Classification Confidence',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val < 0.80 ? 'bg-red-500' : val > 0.90 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'ocr_confidence_avg',
    label: 'Avg OCR Confidence',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val < 0.75 ? 'bg-red-500' : val > 0.85 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'queue_depth',
    label: 'Queue Depth',
    format: formatNum,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 200 ? 'bg-red-500' : val < 50 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'human_review_queue_size',
    label: 'Review Queue Size',
    format: formatNum,
    getColor: (val) => val == null ? 'bg-gray-400' : val > 100 ? 'bg-red-500' : val < 20 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'ragas_faithfulness',
    label: 'RAGAS Faithfulness',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val < 0.75 ? 'bg-red-500' : val > 0.85 ? 'bg-emerald-500' : 'bg-amber-500',
  },
  {
    key: 'thumbs_up_rate',
    label: 'Thumbs Up Rate',
    format: formatPct,
    getColor: (val) => val == null ? 'bg-gray-400' : val < 0.6 ? 'bg-red-500' : val > 0.8 ? 'bg-emerald-500' : 'bg-amber-500',
  },
];

export function KpiGrid() {
  const { activeProject } = useAppStore();
  const { data, isLoading, isError } = useQuery({
    queryKey: ['metrics', activeProject?.project_id],
    queryFn: () => getMetrics(activeProject?.project_id),
    refetchInterval: 60000,
  });

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:gap-6">
        {KPI_CONFIGS.map((kpi, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:gap-6 opacity-60 grayscale">
        {KPI_CONFIGS.map((kpi, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{kpi.label}</CardTitle>
              <div className="h-2 w-2 rounded-full bg-gray-300" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono">--</div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 lg:gap-6">
      {KPI_CONFIGS.map((kpi) => {
        const value = data[kpi.key];
        const colorClass = kpi.getColor(value);
        
        return (
          <Card key={kpi.key}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{kpi.label}</CardTitle>
              <div className={`h-2 w-2 rounded-full ${colorClass}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold font-mono">
                {kpi.format(value)}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
