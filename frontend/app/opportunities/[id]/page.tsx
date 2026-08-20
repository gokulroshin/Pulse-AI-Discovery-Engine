'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { OpportunityItem } from '@/lib/types';
import { ConfidenceBadge, PlatformBadge, ScoreBadge } from '@/components/shared/Badge';
import { SegmentBreakdownChart } from '@/components/charts/SegmentBreakdownChart';
import { EvidenceQuoteList } from '@/components/evidence/EvidenceQuoteList';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import {
  ChevronLeft,
  Sparkles,
  TrendingUp,
  Radio,
  Layers,
  Wrench,
  MessageSquareQuote,
  ShieldCheck,
  Quote,
} from 'lucide-react';

export default function OpportunityDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [opportunity, setOpportunity] = useState<OpportunityItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDetail() {
      if (!id) return;
      try {
        const data = await api.getOpportunity(id);
        setOpportunity(data);
      } catch (err) {
        console.error('Failed to load opportunity detail:', err);
      } finally {
        setLoading(false);
      }
    }
    loadDetail();
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
        <LoadingSpinner text="Loading opportunity deep-dive & evidence traces..." />
      </div>
    );
  }

  if (!opportunity) {
    return (
      <div style={{ padding: '40px', maxWidth: '1400px', margin: '0 auto' }}>
        <EmptyState
          title="Opportunity Area Not Found"
          description="The requested opportunity node ID does not exist in the taxonomy database."
          actionText="Back to Dashboard"
          onAction={() => router.push('/')}
        />
      </div>
    );
  }

  const topSources = opportunity.top_sources || Object.keys(opportunity.source_platform_breakdown || {});

  const scoreCards = [
    {
      title: 'Opportunity Score',
      value: (opportunity.composite_score * 100).toFixed(1),
      subtitle: `Rank #${opportunity.rank} of Prioritized Areas`,
      icon: Sparkles,
      color: '#6366f1',
      weight: 'Composite Index',
    },
    {
      title: 'Purchase Intent Impact',
      value: (opportunity.conversion_relevance_score * 100).toFixed(0) + '%',
      subtitle: 'Relevance to customer checkout decision',
      icon: TrendingUp,
      color: '#10b981',
      weight: 'Core Driver',
    },
    {
      title: 'Cross-Source Triangulation',
      value: (opportunity.triangulation_score * 100).toFixed(0) + '%',
      subtitle: `${topSources.length} Independent Platforms Corroborated`,
      icon: Radio,
      color: '#38bdf8',
      weight: 'High Confidence',
    },
    {
      title: 'Signal Frequency',
      value: (opportunity.frequency_score * 100).toFixed(0) + '%',
      subtitle: `${opportunity.extraction_count} Corroborating Customer Quotes`,
      icon: MessageSquareQuote,
      color: '#a855f7',
      weight: 'Corpus Share',
    },
    {
      title: 'Product Experience Lever',
      value: (opportunity.actionability_score * 100).toFixed(0) + '%',
      subtitle: 'Addressable via UX, sizing & discovery solutions',
      icon: Wrench,
      color: '#f59e0b',
      weight: 'Actionability',
    },
  ];

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Breadcrumb Navigation */}
      <div style={{ marginBottom: '20px' }}>
        <Link
          href="/"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            fontWeight: 500,
            transition: 'color var(--transition-fast)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#ffffff')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
        >
          <ChevronLeft size={16} />
          <span>Back to Opportunities Dashboard</span>
        </Link>
      </div>

      {/* Main Opportunity Banner */}
      <div
        className="glass"
        style={{
          padding: '30px 32px',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '28px',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '20px', flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '320px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '0.9rem',
                  fontWeight: 800,
                  padding: '4px 10px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(99, 102, 241, 0.2)',
                  color: '#818cf8',
                  border: '1px solid rgba(99, 102, 241, 0.4)',
                }}
              >
                RANK #{opportunity.rank}
              </span>
              <ConfidenceBadge level={opportunity.confidence_level} />
              {opportunity.status && (
                <span
                  style={{
                    fontSize: '0.72rem',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(255, 255, 255, 0.05)',
                    color: 'var(--text-muted)',
                    textTransform: 'uppercase',
                  }}
                >
                  {opportunity.status.replace('_', ' ')}
                </span>
              )}
            </div>

            <h1
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '2rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                letterSpacing: '-0.02em',
                lineHeight: '1.2',
                marginBottom: '12px',
              }}
            >
              {opportunity.label}
            </h1>

            <p
              style={{
                fontSize: '0.95rem',
                color: 'var(--text-secondary)',
                lineHeight: '1.6',
                maxWidth: '880px',
                margin: 0,
              }}
            >
              {opportunity.description}
            </p>
          </div>

          {/* Overall Score Badge Banner */}
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '18px 24px',
              borderRadius: 'var(--radius-lg)',
              backgroundColor: 'rgba(99, 102, 241, 0.1)',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              minWidth: '150px',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Composite Score
            </span>
            <span
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '2.5rem',
                fontWeight: 800,
                color: '#ffffff',
                lineHeight: '1.1',
                marginTop: '4px',
              }}
            >
              {opportunity.composite_score.toFixed(2)}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Scale: 0.00 – 1.00
            </span>
          </div>
        </div>

        {/* Channels corroborated */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '20px', paddingTop: '18px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Corroborating Channels:</span>
          {topSources.map((src, i) => (
            <PlatformBadge key={i} platform={src} />
          ))}
        </div>
      </div>

      {/* Score Breakdown Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        {scoreCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={i}
              className="glass"
              style={{
                padding: '18px 20px',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {card.title}
                </span>
                <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)', padding: '2px 5px', borderRadius: '4px', background: 'rgba(255, 255, 255, 0.04)' }}>
                  {card.weight}
                </span>
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.65rem',
                  fontWeight: 800,
                  color: card.color,
                }}
              >
                {card.value}
              </div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                {card.subtitle}
              </div>
            </div>
          );
        })}
      </div>

      {/* Representative Exemplar Quotes */}
      {opportunity.representative_quotes && opportunity.representative_quotes.length > 0 && (
        <div
          className="glass"
          style={{
            padding: '24px',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border-subtle)',
            marginBottom: '28px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <Quote size={18} color="#f59e0b" />
            <h3
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.05rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                margin: 0,
              }}
            >
              Core Cluster Exemplars
            </h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '14px' }}>
            {opportunity.representative_quotes.map((quote, idx) => (
              <div
                key={idx}
                style={{
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(245, 158, 11, 0.04)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  fontStyle: 'italic',
                  fontSize: '0.85rem',
                  color: '#fef3c7',
                  lineHeight: '1.5',
                }}
              >
                "{quote}"
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Two-Column Grid: Segment Breakdown & Evidence Explorer */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '28px' }}>
        {/* Left: Segment Prevalences */}
        <div>
          {opportunity.segment_breakdown && (
            <SegmentBreakdownChart
              segmentData={opportunity.segment_breakdown}
              title="Opportunity Segment Context Distribution"
            />
          )}
        </div>

        {/* Right: Verbatim Evidence Quote Explorer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <h3
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.2rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                margin: 0,
                marginBottom: '4px',
              }}
            >
              Verified Verbatim Evidence ({opportunity.extraction_count} Quotes)
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: 0 }}>
              Live customer quotes extracted with zero prompt bias, linked directly to source platforms.
            </p>
          </div>

          <EvidenceQuoteList
            opportunityId={opportunity.node_id}
            totalEvidenceCount={opportunity.extraction_count}
          />
        </div>
      </div>
    </div>
  );
}
