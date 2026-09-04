import {
  HealthCheckResponse,
  OpportunitiesResponse,
  EvidenceResponse,
  CorpusStats,
  PipelineRunStatus,
  TaxonomyNodeItem,
  OpportunityItem,
} from './types';
import { FALLBACK_OPPORTUNITIES, FALLBACK_CORPUS_STATS } from './fallbackData';

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

class ApiClient {
  private baseUrl: string;
  private apiKey: string;

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
    options: RequestInit = {}
  ): Promise<T> {
    const base = this.getEffectiveBaseUrl().replace(/\/$/, '');
    const url = `${base}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      ...((options.headers as Record<string, string>) || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

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

  // System & Health
  async getHealth(): Promise<HealthCheckResponse> {
    try {
      return await this.request<HealthCheckResponse>('/health');
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
  }): Promise<OpportunitiesResponse> {
    const query = new URLSearchParams();
    if (params?.sort_by) query.set('sort_by', params.sort_by);
    if (params?.limit) query.set('limit', params.limit.toString());
    const endpoint = `/api/v1/opportunities${query.toString() ? `?${query.toString()}` : ''}`;
    try {
      return await this.request<OpportunitiesResponse>(endpoint);
    } catch (err) {
      console.warn('Backend unavailable, using cached opportunity intelligence:', err);
      return FALLBACK_OPPORTUNITIES;
    }
  }

  async getOpportunity(id: string): Promise<OpportunityItem> {
    try {
      return await this.request<OpportunityItem>(`/api/v1/opportunities/${id}`);
    } catch (err) {
      const fallback = FALLBACK_OPPORTUNITIES.opportunities.find((o) => o.node_id === id || o.score_id === id);
      if (fallback) return fallback;
      return FALLBACK_OPPORTUNITIES.opportunities[0];
    }
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
    try {
      return await this.request<EvidenceResponse>(endpoint);
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
            verbatim_quote: 'I love this olive green crop jacket on my wishlist, but I have no idea what bottoms or footwear to pair it with.',
            confidence: 'high',
            signal_type: 'friction',
            source_platform: 'reddit',
            source_url: null,
            engagement_score: 42,
          }
        ]
      };
    }
  }

  // Segments
  async getSegments(): Promise<{ dimensions: string[]; values: Record<string, string[]> }> {
    try {
      return await this.request('/api/v1/segments');
    } catch {
      return {
        dimensions: ['category', 'gender', 'brand_tier'],
        values: {
          category: ['ethnic_wear', 'western', 'footwear', 'accessories'],
          gender: ['women', 'men', 'unisex'],
          brand_tier: ['value', 'mid', 'premium']
        }
      };
    }
  }

  async getSegmentBreakdown(dimension: string): Promise<{
    dimension: string;
    total_opportunities: number;
    breakdown: Record<string, Array<{
      node_id: string;
      label: string;
      composite_score: number;
      rank: number;
      segment_share: number;
    }>>;
  }> {
    try {
      return await this.request(`/api/v1/segments/${dimension}/breakdown`);
    } catch {
      return {
        dimension,
        total_opportunities: 8,
        breakdown: {}
      };
    }
  }

  // Corpus
  async getCorpusStats(): Promise<CorpusStats> {
    try {
      return await this.request<CorpusStats>('/api/v1/corpus/stats');
    } catch (err) {
      console.warn('Backend unavailable, using cached corpus stats:', err);
      return FALLBACK_CORPUS_STATS;
    }
  }

  async uploadCorpus(payload: { items: any[] }): Promise<{ imported_count: number; total_submitted: number }> {
    return this.request('/api/v1/corpus/upload', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Pipeline Engine
  async getPipelineStatus(): Promise<{ runs: PipelineRunStatus[] }> {
    return this.request('/api/v1/pipeline/status');
  }

  async triggerPipeline(stage: string, config: Record<string, any> = {}): Promise<{ run_id: string; status: string; stage: string; message: string }> {
    return this.request('/api/v1/pipeline/run', {
      method: 'POST',
      body: JSON.stringify({ stage, config }),
    });
  }

  // Taxonomy
  async getTaxonomy(): Promise<{ total_nodes: number; root_nodes: number; nodes: TaxonomyNodeItem[] }> {
    return this.request('/api/v1/taxonomy');
  }

  // AI Insight Search & Q&A
  async askInsight(question: string, filter?: { category?: string; platform?: string }): Promise<import('./types').InsightResponse> {
    return this.request('/api/v1/insights/ask', {
      method: 'POST',
      body: JSON.stringify({ question, ...filter }),
    });
  }
}

export const api = new ApiClient();
export default api;
