'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { OpportunitiesResponse, CorpusStats, OpportunityItem } from '@/lib/types';
import { CorpusSummaryHeader } from '@/components/dashboard/CorpusSummaryHeader';
import { AIInsightSearchBar } from '@/components/search/AIInsightSearchBar';
import { OpportunityRankingTable } from '@/components/dashboard/OpportunityRankingTable';
import { TriangulationHeatmap } from '@/components/charts/TriangulationHeatmap';
import { SourceDistributionPie } from '@/components/charts/SourceDistributionPie';
import { SegmentBreakdownChart } from '@/components/charts/SegmentBreakdownChart';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import { Sparkles, RefreshCw, Compass } from 'lucide-react';

export default function DashboardHomePage() {
  const [oppsResponse, setOppsResponse] = useState<OpportunitiesResponse | null>(null);
  const [corpusStats, setCorpusStats] = useState<CorpusStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [oppsData, statsData] = await Promise.all([
        api.getOpportunities({ limit: 50 }),
        api.getCorpusStats(),
      ]);
      setOppsResponse(oppsData);
      setCorpusStats(statsData);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const opportunities: OpportunityItem[] = oppsResponse?.opportunities || [];

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Top Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: '#818cf8',
              }}
            >
              Consumer Intent & Behavior Intelligence
            </span>
          </div>
          <h1
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.9rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              margin: 0,
            }}
          >
            Wishlist & Purchase Discovery Engine
          </h1>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
            Diagnose fashion consumer drop-offs, hesitation factors, and unmet needs grounded in real-world user reviews.
          </p>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            Refresh Intelligence
          </button>
        </div>
      </div>

      {/* Prominent AI Insight Search Bar with 10 Core Research Questions */}
      <AIInsightSearchBar />

      {/* Corpus Summary KPI Header */}
      <CorpusSummaryHeader stats={corpusStats} opps={oppsResponse} loading={loading} />

      {loading ? (
        <LoadingSpinner text="Analyzing opportunity scores and cross-channel matrices..." />
      ) : opportunities.length === 0 ? (
        <EmptyState
          title="No Opportunities Discovered Yet"
          description="The pipeline has not completed scoring on the ingested corpus."
        />
      ) : (
        <>
          {/* Main Opportunity Ranking Table */}
          <div style={{ marginBottom: '32px' }}>
            <OpportunityRankingTable opportunities={opportunities} />
          </div>

          {/* Triangulation Heatmap & Visual Breakdown Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '24px', marginBottom: '32px' }}>
            <TriangulationHeatmap opportunities={opportunities} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              {corpusStats?.platform_distribution && (
                <SourceDistributionPie
                  distribution={corpusStats.platform_distribution}
                  totalDocs={corpusStats.total_documents}
                  title="Channel Corpus Breakdown"
                />
              )}
              {opportunities[0]?.segment_breakdown && (
                <SegmentBreakdownChart
                  segmentData={opportunities[0].segment_breakdown}
                  title={`Segment Prevalence: ${opportunities[0].label}`}
                />
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
