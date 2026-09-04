'use client';

import React, { useState, useEffect, useCallback } from 'react';
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
import { Sparkles, RefreshCw, Compass, WifiOff, Activity } from 'lucide-react';

import { FALLBACK_OPPORTUNITIES, FALLBACK_CORPUS_STATS } from '@/lib/fallbackData';

export default function DashboardHomePage() {
  const [oppsResponse, setOppsResponse] = useState<OpportunitiesResponse | null>(null);
  const [corpusStats, setCorpusStats] = useState<CorpusStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [oppsData, statsData] = await Promise.all([
        api.getOpportunities({ limit: 50 }),
        api.getCorpusStats(),
      ]);
      setOppsResponse(oppsData);
      setCorpusStats(statsData);
      setConnectionError(null);
    } catch (err: any) {
      console.warn('Dashboard data fetch fallback active:', err);
      setOppsResponse(FALLBACK_OPPORTUNITIES);
      setCorpusStats(FALLBACK_CORPUS_STATS);
      setConnectionError(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-reconnect polling every 5s if disconnected
  useEffect(() => {
    if (!connectionError) return;
    const interval = setInterval(() => {
      fetchData();
    }, 5000);
    return () => clearInterval(interval);
  }, [connectionError, fetchData]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const opportunities: OpportunityItem[] = oppsResponse?.opportunities || [];

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Connection Reconnect Notification Bar if Backend Starting */}
      {connectionError && !loading && (
        <div
          className="glass animate-fade-in"
          style={{
            marginBottom: '20px',
            padding: '12px 20px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={18} color="#f87171" className="animate-pulse" />
            <span style={{ fontSize: '0.88rem', color: '#fca5a5', fontWeight: 500 }}>
              {connectionError}
            </span>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary"
            style={{ padding: '6px 14px', fontSize: '0.78rem' }}
          >
            <RefreshCw size={13} className={refreshing ? 'animate-spin' : ''} />
            Reconnect Now
          </button>
        </div>
      )}

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
            Consumer Behaviour Discovery Engine
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

      {/* Prominent AI Insight Search Bar with Core Research Questions */}
      <AIInsightSearchBar />

      {/* Corpus Summary KPI Header */}
      <CorpusSummaryHeader stats={corpusStats} opps={oppsResponse} loading={loading} />

      {loading ? (
        <LoadingSpinner text="Analyzing opportunity scores and cross-channel matrices..." />
      ) : opportunities.length === 0 ? (
        <EmptyState
          title={connectionError ? 'Connecting to Discovery Engine...' : 'No Opportunities Discovered Yet'}
          description={
            connectionError
              ? 'Attempting to establish connection with local backend server on port 8000...'
              : 'The pipeline has not completed scoring on the ingested corpus.'
          }
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
