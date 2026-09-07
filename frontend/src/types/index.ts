export type DocType =
  | 'contract'
  | 'boq'
  | 'drawing'
  | 'specification'
  | 'rfi'
  | 'change_order'
  | 'invoice'
  | 'safety'
  | 'inspection'
  | 'site_log'
  | 'vendor_doc'
  | 'schedule'
  | 'email'
  | 'calc'
  | 'po'
  | 'unknown';

export type ChunkType =
  | 'contract_clause'
  | 'boq_item'
  | 'specification_section'
  | 'drawing_vision'
  | 'rfi_qa_pair'
  | 'site_log_daily'
  | 'email_thread'
  | 'inspection_item'
  | 'calc_block'
  | 'generic';

export type DocumentStatus =
  | 'queued'
  | 'classifying'
  | 'classified'
  | 'ocr_processing'
  | 'splitting'
  | 'processing'
  | 'aggregating'
  | 'refinement_processing'
  | 'chunking'
  | 'embedding_index'
  | 'indexed'
  | 'failed'
  | 'needs_review'
  | 'partially_indexed'
  | 'permanently_failed'
  | 'partial';

export type ApprovalStatus =
  | 'IFC'
  | 'IFR'
  | 'IFT'
  | 'Superseded'
  | 'Approved'
  | 'Draft'
  | 'Pending';

export type Discipline =
  | 'structural'
  | 'architectural'
  | 'electrical'
  | 'mechanical'
  | 'hvac'
  | 'plumbing'
  | 'civil';

// Common Models
export interface Project {
  project_id: string;
  name: string;
  type: string;
  location: string;
  phase: string;
  created_at: string;
}

export interface Document {
  doc_id: string;
  filename: string;
  doc_type: DocType | null;
  doc_sub_type?: string | null;
  revision: string | null;
  is_current: boolean;
  approval_status: ApprovalStatus | null;
  classification_confidence: number | null;
  ocr_confidence: number | null;
  chunk_count: number | null;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
  project_id: string;
  
  // Phase 1 / Phase 3 properties added
  file_url?: string;
  file_size_bytes: number;
  page_count: number | null;
  has_images: boolean;
  has_tables: boolean;
  has_drawings: boolean;
  has_handwriting: boolean;
  language: string;
  error_message: string;
  retry_count: number;
  ocr_method: string;
}

// API Responses
export interface UploadResultItem {
  doc_id?: string;
  filename: string;
  status: 'queued' | 'rejected' | 'duplicate';
  size_mb?: number;
  reason?: string;
  existing_id?: string;
}

export interface UploadResponse {
  uploaded: number;
  results: UploadResultItem[];
}

export interface DocumentStatusResponse {
  doc_id: string;
  filename: string;
  status: DocumentStatus;
  doc_type: DocType | null;
  ocr_confidence: number | null;
  chunk_count: number | null;
  error: string | null;
  retry_count: number;

  refinement_quality_avg: number | null;
  needs_human_review_pages: number;
  chunking_strategy_breakdown: Record<string, number>;
  processing_job_status: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface Citation {
  chunk_id: string;
  document_id: string;
  filename: string;
  doc_type: DocType | string;
  page_number?: number | null;
  drawing_number?: string | null;
  clause_number?: string | null;
  revision: string;
  excerpt: string;
}

export interface GenerationResponse {
  answer: string;
  citations: Citation[];
  confidence: number;
  needs_fallback: boolean;
  answer_grounded: boolean;
  warning_message?: string | null;
  retrieval_stages: string[];
  processing_ms: number;
}

// Keeping these for legacy compatibility temporarily if needed
export interface ChatSource {
  title: string;
  revision: string | null;
  doc_type: DocType;
  drawing_number?: string | null;
  clause_number?: string | null;
  page_number?: number | null;
  is_current?: boolean;
}

export interface ChatResponse {
  answer: string;
  sources: ChatSource[];
  needs_fallback: boolean;
}

export interface ProjectListResponse {
  projects: Project[];
}

export interface AdminQueueItem {
  doc_id: string;
  filename: string;
  status: DocumentStatus;
  classification_confidence: number | null;
  retry_count: number;
  error_message: string | null;
  created_at: string;
  
  doc_type: string;
  needs_human_review_pages: number;
  refinement_failed_pages: number;
  chunking_job_status: string;
  last_error_stage: 'classification' | 'ocr' | 'refinement' | 'chunking' | null;
}

export interface AdminQueueResponse {
  queue: AdminQueueItem[];
}

export interface HealthResponse {
  status: 'ok' | 'degraded';
  services: {
    database: boolean;
    redis: boolean;
    vector_store: boolean;
  };
}

export interface MetricsResponse {
  query_latency_p95_seconds: number | null;
  retrieval_hit_rate: number | null;
  crag_rejection_rate: number | null;
  llm_error_rate: number | null;
  cost_per_query_paise: number | null;
  ocr_confidence_avg: number | null;
  classification_confidence_avg: number | null;
  queue_depth: number | null;
  human_review_queue_size: number | null;
  ragas_faithfulness: number | null;
  thumbs_up_rate: number | null;
}

// Pipeline Summary Interfaces
export interface ProcessingJobSummary {
  document_id: string;
  status: string;
  total_pages: number;
  processed_pages: number;
  failed_pages: number;
  strategy_breakdown: Record<string, number>;
  processing_time_seconds: number;
}

export interface RefinementSummary {
  total_pages: number;
  refined_pages: number;
  needs_review_count: number;
  avg_quality_before: number;
  avg_quality_after: number;
  avg_quality_delta: number;
  level_breakdown: Record<string, number>;
  semantic_validation_used_count: number;
}

export interface ChunkingStats {
  total_chunks: number;
  strategy_breakdown: Record<ChunkType, number>;
  avg_chunk_length: number;
  chunks_needing_review: number;
}

export interface RefinementPageReview {
  page_id: string;
  page_number: number;
  quality_before: number;
  quality_after: number;
  refinement_level: string;
  refinement_flags: string[];
  needs_human_review: boolean;
}
