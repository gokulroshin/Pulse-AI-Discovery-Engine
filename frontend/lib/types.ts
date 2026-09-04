/**
 * Core TypeScript definitions for Pulse Discovery Engine.
 * Synchronized with Backend ORM and API response models.
 */

export type SourcePlatform =
  | 'reddit'
  | 'playstore'
  | 'appstore'
  | 'youtube'
  | 'twitter'
  | 'forum'
  | 'ecommerce'
  | 'manual_upload'
  | string;

export type SignalType =
  | 'friction'
  | 'motivation'
  | 'behavior'
  | 'uncertainty'
  | 'comparison'
  | 'external_validation';

export type ConfidenceLevel = 'high' | 'medium' | 'low';

export type NodeStatus = 'auto_generated' | 'pm_reviewed' | 'merged' | 'archived';

export type PipelineStage =
  | 'ingestion'
  | 'extraction'
  | 'clustering'
  | 'scoring'
  | 'full_pipeline';

export type PipelineStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface RawDocumentItem {
  doc_id: string;
  source_platform: SourcePlatform;
  content_text: string;
  content_language: string;
  source_url?: string | null;
  source_subreddit?: string | null;
  engagement_score: number;
  inferred_category?: string | null;
  inferred_gender_context?: string | null;
  inferred_brand_tier?: string | null;
  source_timestamp?: string | null;
  created_at: string;
}

export interface ExtractionItem {
  extraction_id: string;
  doc_id: string;
  reason_text: string;
  verbatim_quote: string;
  confidence: ConfidenceLevel;
  signal_type: SignalType;
  preliminary_cluster_hint?: string | null;
  taxonomy_node_id?: string | null;
  created_at: string;
}

export interface TaxonomyNodeItem {
  node_id: string;
  label: string;
  description: string;
  parent_node_id?: string | null;
  extraction_count: number;
  representative_quotes: string[];
  status: NodeStatus;
  created_at: string;
}

export interface OpportunityItem {
  score_id?: string;
  rank: number;
  node_id: string;
  label: string;
  description: string;
  composite_score: number;
  frequency_score: number;
  triangulation_score: number;
  conversion_relevance_score: number;
  segment_breadth_score: number;
  actionability_score: number;
  extraction_count: number;
  confidence_level: ConfidenceLevel;
  top_sources: SourcePlatform[];
  top_segments: string[];
  representative_quotes?: string[];
  status?: NodeStatus;
  computed_at?: string;
  segment_breakdown?: {
    by_category?: Record<string, number>;
    by_gender?: Record<string, number>;
    by_brand_tier?: Record<string, number>;
    by_price_tier?: Record<string, number>;
    by_geography?: Record<string, number>;
  };
  source_platform_breakdown?: Record<string, number>;
}

export interface OpportunitiesResponse {
  scoring_run_id?: string;
  computed_at?: string;
  corpus_size: number;
  total_opportunities: number;
  opportunities: OpportunityItem[];
}

export interface EvidenceItem {
  extraction_id: string;
  reason_text: string;
  verbatim_quote: string;
  source_platform: SourcePlatform;
  source_url?: string | null;
  source_subreddit?: string | null;
  confidence: ConfidenceLevel;
  signal_type: SignalType;
  engagement_score: number;
  source_timestamp?: string | null;
}

export interface EvidenceResponse {
  opportunity: {
    node_id: string;
    label: string;
  };
  evidence_count: number;
  pagination: {
    page: number;
    per_page: number;
    total: number;
  };
  evidence: EvidenceItem[];
}

export interface CorpusStats {
  total_documents: number;
  platform_distribution: Record<string, number>;
  category_distribution: Record<string, number>;
  gender_distribution: Record<string, number>;
  brand_tier_distribution?: Record<string, number>;
  total_extractions: number;
  last_ingestion_at?: string | null;
}

export interface PipelineRunStatus {
  run_id: string;
  stage: PipelineStage;
  status: PipelineStatus;
  config: Record<string, any>;
  stats: Record<string, any>;
  started_at: string;
  completed_at?: string | null;
}

export interface HealthCheckResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  database: {
    status: string;
    error?: string | null;
  };
  timestamp: string;
}

export interface InsightSourceQuote {
  verbatim_quote: string;
  reason_text: string;
  source_platform: string;
  source_url?: string | null;
}

export interface LinkedOpportunity {
  node_id: string;
  label: string;
  rank: number;
  composite_score: number;
}

export interface InsightResponse {
  question: string;
  summary: string;
  detailed_synthesis: string;
  key_drivers: string[];
  supporting_evidence: InsightSourceQuote[];
  linked_opportunities: LinkedOpportunity[];
  segment_nuances?: Record<string, string>;
}
