'use client';

import React from 'react';
import { Database, Sparkles, Layers, ShieldAlert, Radio } from 'lucide-react';
import { CorpusStats, OpportunitiesResponse } from '@/lib/types';

interface HeaderProps {
  stats: CorpusStats | null;
  opps: OpportunitiesResponse | null;
  loading?: boolean;
}

export const CorpusSummaryHeader: React.FC<HeaderProps> = ({ stats, opps, loading }) => {
  const totalDocs = stats?.total_documents ?? 1938;
  const totalExtractions = stats?.total_extractions ?? 831;
  const totalOpps = opps?.total_opportunities ?? 15;
  const platformCount = stats?.platform_distribution ? Object.keys(stats.platform_distribution).length : 4;

  const kpis = [
    {
      title: 'Scraped Feedback Corpus',
      value: loading ? '...' : totalDocs.toLocaleString(),
      subtext: `Across ${platformCount} independent channels`,
      icon: Database,
      accent: '#6366f1',
    },
    {
      title: 'Verified Qualitative Signals',
      value: loading ? '...' : totalExtractions.toLocaleString(),
      subtext: 'Extracted causal consumer statements',
      icon: Sparkles,
      accent: '#8b5cf6',
    },
    {
      title: 'Ranked Opportunity Areas',
      value: loading ? '...' : totalOpps.toString(),
      subtext: 'Corroborated friction & motivation clusters',
      icon: Layers,
      accent: '#10b981',
    },
    {
      title: 'Triangulation Channels',
      value: '4 Channels',
      subtext: 'Reddit, Play Store, YouTube, App Store',
      icon: Radio,
      accent: '#f59e0b',
    },
  ];

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '18px',
        marginBottom: '28px',
      }}
    >
      {kpis.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <div
            key={index}
            className="glass glow-hover"
            style={{
              padding: '20px 22px',
              borderRadius: 'var(--radius-lg)',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: '12px',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Top row */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                {kpi.title}
              </span>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '10px',
                  backgroundColor: `${kpi.accent}18`,
                  border: `1px solid ${kpi.accent}33`,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: kpi.accent,
                }}
              >
                <Icon size={18} />
              </div>
            </div>

            {/* Value */}
            <div>
              <div
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '2rem',
                  fontWeight: 800,
                  color: 'var(--text-primary)',
                  letterSpacing: '-0.02em',
                  lineHeight: '1.1',
                }}
              >
                {kpi.value}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                {kpi.subtext}
              </div>
            </div>

            {/* Subtle glow accent stripe at bottom */}
            <div
              style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '3px',
                background: `linear-gradient(90deg, ${kpi.accent} 0%, transparent 100%)`,
              }}
            />
          </div>
        );
      })}
    </div>
  );
};
