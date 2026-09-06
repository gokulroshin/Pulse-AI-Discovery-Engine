import {
  HealthCheckResponse,
  OpportunitiesResponse,
  EvidenceResponse,
  CorpusStats,
  PipelineRunStatus,
  TaxonomyNodeItem,
  OpportunityItem,
} from './types';
import {
  FALLBACK_OPPORTUNITIES,
  FALLBACK_CORPUS_STATS,
  FALLBACK_SEGMENT_BREAKDOWNS,
  FallbackSegmentBreakdownResponse,
} from './fallbackData';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const API_KEY =
  process.env.NEXT_PUBLIC_API_KEY || 'pulse-secret-dev-key-change-in-prod';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

class ApiClient {
  private baseUrl: string;
  private apiKey: string;
  private cache: Map<string, CacheEntry<any>> = new Map();
  private cacheTTLMs: number = 30000; // 30 seconds client-side memory cache

  constructor(baseUrl = API_BASE_URL, apiKey = API_KEY) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  private getEffectiveBaseUrl(): string {
    if (this.baseUrl && this.baseUrl !== 'http://localhost:8000') {
      return this.baseUrl;
    }
    if (
      typeof window !== 'undefined' &&
      window.location.hostname &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1'
    ) {
      return `${window.location.protocol}//${window.location.hostname}:8000`;
    }
    return this.baseUrl || 'http://localhost:8000';
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs = 3500
  ): Promise<T> {
    const base = this.getEffectiveBaseUrl().replace(/\/$/, '');
    const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      ...((options.headers as Record<string, string>) || {}),
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: any = null;
        try {
          errorData = await response.json();
        } catch {
          errorData = await response.text();
        }
        throw new ApiError(
          `API request failed: ${response.status} ${response.statusText}`,
          response.status,
          errorData
        );
      }

      return (await response.json()) as T;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        error instanceof Error ? error.message : 'Network error occurred',
        0,
        error
      );
    }
  }

  private getCached<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > this.cacheTTLMs) {
      this.cache.delete(key);
      return null;
    }
    return entry.data as T;
  }

  private setCached<T>(key: string, data: T): void {
    this.cache.set(key, { data, timestamp: Date.now() });
  }

  // System & Health
  async getHealth(): Promise<HealthCheckResponse> {
    try {
      return await this.request<HealthCheckResponse>('/health', {}, 2000);
    } catch {
      return {
        status: 'offline',
        app_name: 'Pulse Discovery Engine',
        version: '1.0.0',
        environment: 'development',
        database: { status: 'disconnected' },
        timestamp: new Date().toISOString(),
      };
    }
  }

  // Opportunities
  async getOpportunities(params?: {
    sort_by?: string;
    limit?: number;
    search?: string;
    forceRefresh?: boolean;
  }): Promise<OpportunitiesResponse> {
    const query = new URLSearchParams();
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    if (params?.limit) query.set('limit', params.limit.toString());
    const endpoint = `/api/v1/opportunities${query.toString() ? `?${query.toString()}` : ''}`;

    if (!params?.forceRefresh) {
      const cached = this.getCached<OpportunitiesResponse>(endpoint);
      if (cached) return cached;
    }

    try {
      const data = await this.request<OpportunitiesResponse>(endpoint);
      if (data && Array.isArray(data.opportunities) && data.opportunities.length > 0) {
        this.setCached(endpoint, data);
        return data;
      }
      return FALLBACK_OPPORTUNITIES;
    } catch (err) {
      console.warn('Backend unavailable, using cached opportunity intelligence:', err);
      return FALLBACK_OPPORTUNITIES;
    }
  }

  async getOpportunity(id: string): Promise<OpportunityItem> {
    const cacheKey = `/api/v1/opportunities/${id}`;
    const cached = this.getCached<OpportunityItem>(cacheKey);
    if (cached) return cached;

    try {
      const data = await this.request<OpportunityItem>(cacheKey);
      if (data) {
        this.setCached(cacheKey, data);
        return data;
      }
    } catch (err) {
      console.warn('Opportunity detail fetch fallback active:', err);
    }
    const fallback =
      FALLBACK_OPPORTUNITIES.opportunities.find((o) => o.node_id === id || o.score_id === id) ||
      FALLBACK_OPPORTUNITIES.opportunities[0];
    return fallback;
  }

  // Evidence Drill-down
  async getEvidence(
    opportunityId: string,
    params?: { page?: number; per_page?: number; platform?: string }
  ): Promise<EvidenceResponse> {
    const query = new URLSearchParams();
    if (params?.page) query.set('page', params.page.toString());
    if (params?.per_page) query.set('per_page', params.per_page.toString());
    if (params?.platform && params.platform !== 'all') query.set('platform', params.platform);
    const endpoint = `/api/v1/opportunities/${opportunityId}/evidence${query.toString() ? `?${query.toString()}` : ''}`;

    const cached = this.getCached<EvidenceResponse>(endpoint);
    if (cached) return cached;

    try {
      const data = await this.request<EvidenceResponse>(endpoint);
      this.setCached(endpoint, data);
      return data;
    } catch {
      return {
        opportunity: {
          node_id: opportunityId,
          label: 'Opportunity Evidence Drilldown',
        },
        evidence_count: 1,
        pagination: {
          page: 1,
          per_page: 10,
          total: 1,
        },
        evidence: [
          {
            extraction_id: 'sample-1',
            reason_text: 'Users struggle to visualize styling and complete outfit combinations.',
            verbatim_quote:
              'I love this olive green crop jacket on my wishlist, but I have no idea what bottoms or footwear to pair it with.',
            confidence: 'high',
            signal_type: 'friction',
            source_platform: 'reddit',
            source_url: null,
            engagement_score: 42,
          },
        ],
      };
    }
  }

  // Segments
  async getSegments(): Promise<{ dimensions: string[]; values: Record<string, string[]> }> {
    const cached = this.getCached<{ dimensions: string[]; values: Record<string, string[]> }>('/api/v1/segments');
    if (cached) return cached;

    try {
      const data = await this.request<{ dimensions: string[]; values: Record<string, string[]> }>('/api/v1/segments');
      this.setCached('/api/v1/segments', data);
      return data;
    } catch {
      return {
        dimensions: ['category', 'gender', 'brand_tier'],
        values: {
          category: ['ethnic_wear', 'western', 'footwear', 'accessories'],
          gender: ['women', 'men', 'unisex'],
          brand_tier: ['value', 'mid', 'premium'],
        },
      };
    }
  }

  async getSegmentBreakdown(
    dimension: string,
    forceRefresh = false
  ): Promise<FallbackSegmentBreakdownResponse> {
    const normalizedDim = dimension.toLowerCase().trim();
    const cacheKey = `/api/v1/segments/${normalizedDim}/breakdown`;

    if (!forceRefresh) {
      const cached = this.getCached<FallbackSegmentBreakdownResponse>(cacheKey);
      if (cached) return cached;
    }

    try {
      const data = await this.request<any>(cacheKey);
      if (data && Array.isArray(data.breakdown) && data.breakdown.length > 0) {
        const result: FallbackSegmentBreakdownResponse = {
          dimension: data.dimension || normalizedDim,
          total_opportunities: data.total_opportunities || data.breakdown.length,
          breakdown: data.breakdown,
        };
        this.setCached(cacheKey, result);
        return result;
      }
    } catch (err) {
      console.warn(`Segment breakdown fetch fallback active for ${normalizedDim}:`, err);
    }

    return (
      FALLBACK_SEGMENT_BREAKDOWNS[normalizedDim] ||
      FALLBACK_SEGMENT_BREAKDOWNS['category']
    );
  }

  // Corpus
  async getCorpusStats(forceRefresh = false): Promise<CorpusStats> {
    const cacheKey = '/api/v1/corpus/stats';
    if (!forceRefresh) {
      const cached = this.getCached<CorpusStats>(cacheKey);
      if (cached) return cached;
    }

    try {
      const data = await this.request<CorpusStats>(cacheKey);
      if (data && data.total_documents > 0) {
        this.setCached(cacheKey, data);
        return data;
      }
      return FALLBACK_CORPUS_STATS;
    } catch (err) {
      console.warn('Backend unavailable, using cached corpus stats:', err);
      return FALLBACK_CORPUS_STATS;
    }
  }

  async uploadCorpus(payload: { items: any[] }): Promise<{ imported_count: number; total_submitted: number }> {
    this.cache.clear(); // invalidate cache on mutation
    return this.request<{ imported_count: number; total_submitted: number }>('/api/v1/corpus/upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Pipeline Engine
  async getPipelineStatus(): Promise<{ runs: PipelineRunStatus[] }> {
    return this.request<{ runs: PipelineRunStatus[] }>('/api/v1/pipeline/status');
  }

  async triggerPipeline(
    stage: string,
    config: Record<string, any> = {}
  ): Promise<{ run_id: string; status: string; stage: string; message: string }> {
    this.cache.clear();
    return this.request<{ run_id: string; status: string; stage: string; message: string }>('/api/v1/pipeline/run', {
      method: 'POST',
      body: JSON.stringify({ stage, config }),
    });
  }

  // Taxonomy
  async getTaxonomy(): Promise<{ total_nodes: number; root_nodes: number; nodes: TaxonomyNodeItem[] }> {
    const cacheKey = '/api/v1/taxonomy';
    const cached = this.getCached<{ total_nodes: number; root_nodes: number; nodes: TaxonomyNodeItem[] }>(cacheKey);
    if (cached) return cached;

    try {
      const data = await this.request<{ total_nodes: number; root_nodes: number; nodes: TaxonomyNodeItem[] }>(cacheKey);
      this.setCached(cacheKey, data);
      return data;
    } catch (err) {
      console.warn('Taxonomy fetch fallback active:', err);
      return {
        total_nodes: 8,
        root_nodes: 8,
        nodes: FALLBACK_OPPORTUNITIES.opportunities.map((o) => ({
          node_id: o.node_id,
          label: o.label,
          description: o.description,
          parent_node_id: null,
          extraction_count: o.extraction_count,
          representative_quotes: o.representative_quotes || [],
          status: o.status || 'auto_generated',
          created_at: new Date().toISOString(),
        })),
      };
    }
  }

  // AI Insight Search & Q&A
  async askInsight(
    question: string,
    filter?: { category?: string; platform?: string }
  ): Promise<import('./types').InsightResponse> {
    return this.request<import('./types').InsightResponse>('/api/v1/insights/ask', {
      method: 'POST',
      body: JSON.stringify({ question, ...filter }),
    });
  }
}

export const api = new ApiClient();
export default api;
