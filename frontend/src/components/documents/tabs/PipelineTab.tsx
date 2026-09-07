import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProcessingJob, retryProcessing, getRefinementSummary, getChunkingStats, retryChunking } from '@/lib/api';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { Button } from '@/components/ui/button';
import { RotateCw, Loader2, Hash } from 'lucide-react';
import { toast } from 'sonner';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#14b8a6', '#6366f1'];

export function PipelineTab({ docId }: { docId: string }) {
  const queryClient = useQueryClient();

  // Queries
  const { data: processing, isLoading: loadProc } = useQuery({
    queryKey: ['procJob', docId],
    queryFn: () => getProcessingJob(docId),
  });

  const { data: refinement, isLoading: loadRef } = useQuery({
    queryKey: ['refSummary', docId],
    queryFn: () => getRefinementSummary(docId),
  });

  const { data: chunking, isLoading: loadChunk } = useQuery({
    queryKey: ['chunkStats', docId],
    queryFn: () => getChunkingStats(docId),
  });

  // Mutations
  const procMutation = useMutation({
    mutationFn: () => retryProcessing(docId),
    onSuccess: () => {
      toast.success('Processing retry started');
      queryClient.invalidateQueries({ queryKey: ['procJob', docId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const chunkMutation = useMutation({
    mutationFn: () => retryChunking(docId),
    onSuccess: () => {
      toast.success('Chunking retry started');
      queryClient.invalidateQueries({ queryKey: ['chunkStats', docId] });
    },
    onError: (err: any) => toast.error(err.message),
  });

  const isLoading = loadProc || loadRef || loadChunk;

  if (isLoading) {
    return <div className="flex justify-center p-8"><Loader2 className="w-6 h-6 animate-spin text-muted-foreground" /></div>;
  }

  const procChartData = processing?.strategy_breakdown ? Object.entries(processing.strategy_breakdown).map(([name, value]) => ({ name, value })) : [];
  const chunkChartData = chunking?.strategy_breakdown ? Object.entries(chunking.strategy_breakdown).map(([name, value]) => ({ name, value })) : [];

  return (
    <div className="space-y-8 pb-8">
      {/* SECTION A: OCR Processing */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            1. OCR Processing
            {processing?.status && <StatusBadge status={processing.status} className="ml-2" />}
          </h3>
          <Button variant="outline" size="sm" onClick={() => procMutation.mutate()} disabled={procMutation.isPending}>
            <RotateCw className={`w-3 h-3 mr-2 ${procMutation.isPending ? 'animate-spin' : ''}`} />
            Retry
          </Button>
        </div>
        
        {processing ? (
          <div className="grid md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-muted/50 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold">{processing.total_pages}</div>
                  <div className="text-xs text-muted-foreground">Total Pages</div>
                </div>
                <div className="bg-emerald-500/10 p-3 rounded-lg text-center">
                  <div className="text-2xl font-bold text-emerald-600">{processing.processed_pages}</div>
                  <div className="text-xs text-emerald-600">Processed</div>
                </div>
                <div className={processing.failed_pages > 0 ? "bg-red-500/10 p-3 rounded-lg text-center" : "bg-muted/50 p-3 rounded-lg text-center"}>
                  <div className={`text-2xl font-bold ${processing.failed_pages > 0 ? 'text-red-600' : ''}`}>{processing.failed_pages}</div>
                  <div className={`text-xs ${processing.failed_pages > 0 ? 'text-red-600' : 'text-muted-foreground'}`}>Failed</div>
                </div>
              </div>
            </div>
            
            <div className="h-32 border rounded-lg p-2 flex flex-col">
              <span className="text-xs font-semibold text-muted-foreground mb-1 ml-1">Strategy Breakdown</span>
              {procChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={procChartData} layout="vertical" margin={{ top: 0, right: 10, left: 20, bottom: 0 }}>
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} fontSize={10} width={80} />
                    <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="value" fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={12} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs text-muted-foreground">No data</div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">No processing data available.</div>
        )}
      </section>

      {/* SECTION B: Refinement */}
      <section className="space-y-4">
        <div className="border-b pb-2">
          <h3 className="text-lg font-semibold">2. Semantic Refinement</h3>
        </div>
        
        {refinement ? (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="col-span-1 space-y-4">
              <div className="p-4 border rounded-lg text-center bg-card">
                <div className="text-xs text-muted-foreground mb-1 uppercase tracking-wider font-semibold">Quality Improvement</div>
                <div className="flex items-center justify-center gap-3 mt-2">
                  <div className="text-xl font-bold text-slate-500">{(refinement.avg_quality_before * 100).toFixed(0)}%</div>
                  <div className="text-emerald-500 font-bold">&rarr;</div>
                  <div className="text-2xl font-bold text-emerald-600">{(refinement.avg_quality_after * 100).toFixed(0)}%</div>
                </div>
                <div className="text-xs text-emerald-600 mt-1">+{((refinement.avg_quality_delta) * 100).toFixed(1)}% boost</div>
              </div>
            </div>

            <div className="col-span-2 grid grid-cols-2 gap-4">
              <div className="border p-3 rounded-lg flex justify-between items-center bg-amber-500/5">
                <span className="text-sm font-medium">Needs Human Review</span>
                <span className={`font-bold ${refinement.needs_review_count > 0 ? 'text-amber-600' : ''}`}>
                  {refinement.needs_review_count} pages
                </span>
              </div>
              <div className="border p-3 rounded-lg flex justify-between items-center">
                <span className="text-sm font-medium">Semantic Validations</span>
                <span className="font-bold">{refinement.semantic_validation_used_count}</span>
              </div>
              
              <div className="border p-3 rounded-lg col-span-2">
                <span className="text-xs font-semibold text-muted-foreground block mb-2">Refinement Intensity</span>
                <div className="flex gap-4">
                  {Object.entries(refinement.level_breakdown || {}).map(([level, count]) => (
                    <div key={level} className="flex-1 text-center bg-muted/30 rounded py-1">
                      <div className="font-mono text-lg font-bold">{count}</div>
                      <div className="text-[10px] uppercase">{level}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">No refinement data available.</div>
        )}
      </section>

      {/* SECTION C: Chunking */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b pb-2">
          <h3 className="text-lg font-semibold">3. Chunking & Indexing</h3>
          <Button variant="outline" size="sm" onClick={() => chunkMutation.mutate()} disabled={chunkMutation.isPending}>
            <RotateCw className={`w-3 h-3 mr-2 ${chunkMutation.isPending ? 'animate-spin' : ''}`} />
            Retry
          </Button>
        </div>
        
        {chunking ? (
          <div className="grid md:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div className="bg-primary/5 p-4 rounded-lg text-center border border-primary/20">
                <div className="flex items-center justify-center text-primary mb-1"><Hash className="w-4 h-4 mr-1"/></div>
                <div className="text-4xl font-black text-primary">{chunking.total_chunks}</div>
                <div className="text-xs text-primary/80 font-medium uppercase tracking-wider mt-1">Total Chunks</div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-center">
                <div className="bg-muted p-2 rounded">
                  <div className="text-lg font-mono font-bold">{chunking.avg_chunk_length}</div>
                  <div className="text-[10px] text-muted-foreground">Avg Chars</div>
                </div>
                <div className={`p-2 rounded ${chunking.chunks_needing_review > 0 ? 'bg-amber-100 text-amber-900' : 'bg-muted'}`}>
                  <div className="text-lg font-mono font-bold">{chunking.chunks_needing_review}</div>
                  <div className="text-[10px] opacity-80">Review Needed</div>
                </div>
              </div>
            </div>

            <div className="col-span-2 h-40 border rounded-lg p-2 flex items-center">
              {chunkChartData.length > 0 ? (
                <>
                  <div className="h-full w-1/2">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={chunkChartData}
                          cx="50%"
                          cy="50%"
                          innerRadius={30}
                          outerRadius={50}
                          paddingAngle={2}
                          dataKey="value"
                        >
                          {chunkChartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ fontSize: '12px' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="w-1/2 pr-4 overflow-auto max-h-full">
                    <span className="text-xs font-semibold text-muted-foreground block mb-2">Strategy Breakdown</span>
                    <div className="space-y-1">
                      {chunkChartData.map((entry, idx) => (
                        <div key={idx} className="flex justify-between text-xs items-center">
                          <div className="flex items-center gap-1.5 truncate pr-2">
                            <div className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: COLORS[idx % COLORS.length] }} />
                            <span className="truncate">{entry.name}</span>
                          </div>
                          <span className="font-mono font-medium">{entry.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="flex-1 text-center text-xs text-muted-foreground">No chunk data</div>
              )}
            </div>
          </div>
        ) : (
          <div className="text-sm text-muted-foreground">No chunking data available.</div>
        )}
      </section>
    </div>
  );
}
