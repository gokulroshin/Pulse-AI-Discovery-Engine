'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { OpportunityItem } from '@/lib/types';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import { ScoreBadge, PlatformBadge } from '@/components/shared/Badge';
import {
  PieChart,
  Layers,
  ChevronRight,
  Sparkles,
  Shirt,
  User,
  Tag,
  Filter,
} from 'lucide-react';

interface SegmentBreakdownResponse {
  dimension: string;
  total_opportunities: number;
  breakdown: Record<
    string,
    Array<{
      node_id: string;
      label: string;
      composite_score: number;
      rank: number;
      segment_share: number;
    }>
  >;
}

const DIMENSIONS = [
  { id: 'category', label: 'Product Category', icon: Shirt, values: ['ethnic_wear', 'western_wear', 'footwear'] },
  { id: 'gender', label: 'Gender Context', icon: User, values: ['women', 'men', 'unisex'] },
  { id: 'brand_tier', label: 'Brand & Price Tier', icon: Tag, values: ['premium', 'mid', 'value'] },
];

export default function SegmentExplorerPage() {
  const [selectedDimension, setSelectedDimension] = useState('category');
  const [breakdownData, setBreakdownData] = useState<SegmentBreakdownResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadSegmentData() {
      setLoading(true);
      try {
        const data = await api.getSegmentBreakdown(selectedDimension);
        setBreakdownData(data);
      } catch (err) {
        console.error('Failed to load segment breakdown:', err);
      } finally {
        setLoading(false);
      }
    }
    loadSegmentData();
  }, [selectedDimension]);

  const activeDimensionMeta = DIMENSIONS.find((d) => d.id === selectedDimension) || DIMENSIONS[0];

  const groupedBySegment = React.useMemo(() => {
    if (!breakdownData?.breakdown) return {};

    if (!Array.isArray(breakdownData.breakdown)) {
      return breakdownData.breakdown;
    }

    const dict: Record<string, Array<{
      node_id: string;
      label: string;
      composite_score: number;
      rank: number;
      segment_share: number;
    }>> = {};

    activeDimensionMeta.values.forEach((valKey) => {
      dict[valKey] = [];
    });

    breakdownData.breakdown.forEach((item: any) => {
      const dist = item.segment_distribution || {};
      Object.entries(dist).forEach(([valKey, share]: [string, any]) => {
        if (!dict[valKey]) dict[valKey] = [];
        if (Number(share) > 0.05) {
          dict[valKey].push({
            node_id: item.node_id,
            label: item.label,
            composite_score: item.composite_score,
            rank: item.rank,
            segment_share: Number(share),
          });
        }
      });
    });

    Object.keys(dict).forEach((k) => {
      dict[k].sort((a, b) => b.segment_share - a.segment_share);
    });

    return dict;
  }, [breakdownData, activeDimensionMeta]);

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Top Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: '#a855f7',
            }}
          >
            Cohort & Category Analysis
          </span>
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '1.85rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: 0,
          }}
        >
          Segment Prevalence Explorer
        </h1>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
          Explore how consumer frictions vary across merchandise categories, gender contexts, and brand tiers.
        </p>
      </div>

      {/* Dimension Switcher Tabs */}
      <div
        className="glass"
        style={{
          padding: '10px 14px',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '28px',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginRight: '4px' }}>
          Dimension:
        </span>
        {DIMENSIONS.map((dim) => {
          const Icon = dim.icon;
          const isSelected = selectedDimension === dim.id;

          return (
            <button
              key={dim.id}
              onClick={() => setSelectedDimension(dim.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 16px',
                borderRadius: 'var(--radius-md)',
                fontSize: '0.85rem',
                fontFamily: 'var(--font-heading)',
                fontWeight: isSelected ? 700 : 500,
                backgroundColor: isSelected ? 'rgba(168, 85, 247, 0.2)' : 'transparent',
                color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                border: isSelected ? '1px solid rgba(168, 85, 247, 0.4)' : '1px solid transparent',
                boxShadow: isSelected ? '0 0 16px rgba(168, 85, 247, 0.25)' : 'none',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
              }}
            >
              <Icon size={16} color={isSelected ? '#c084fc' : 'var(--text-muted)'} />
              <span>{dim.label}</span>
            </button>
          );
        })}
      </div>

      {/* Breakdown View */}
      {loading ? (
        <LoadingSpinner text={`Analyzing ${activeDimensionMeta.label} distributions...`} />
      ) : Object.keys(groupedBySegment).length === 0 ? (
        <EmptyState
          title="No Segment Breakdown Available"
          description="Ensure the pipeline has run and extractions have segment tags populated."
          icon={PieChart}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '24px',
          }}
        >
          {Object.entries(groupedBySegment).map(([segmentKey, oppList]) => (
            <div
              key={segmentKey}
              className="glass glow-hover"
              style={{
                padding: '24px',
                borderRadius: 'var(--radius-xl)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '18px',
              }}
            >
              {/* Segment Title Banner */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#c084fc',
                    }}
                  />
                  <h3
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: '1.15rem',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      textTransform: 'capitalize',
                      margin: 0,
                    }}
                  >
                    {segmentKey.replace('_', ' ')}
                  </h3>
                </div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    backgroundColor: 'rgba(168, 85, 247, 0.12)',
                    color: '#c084fc',
                    fontWeight: 600,
                  }}
                >
                  {oppList.length} Opportunities
                </span>
              </div>

              {/* Ranked opportunities in this segment */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {oppList.map((item, idx) => (
                  <Link
                    key={item.node_id}
                    href={`/opportunities/${item.node_id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid rgba(255, 255, 255, 0.05)',
                      transition: 'all var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(168, 85, 247, 0.08)';
                      e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.25)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.05)';
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, minWidth: 0 }}>
                      <span
                        style={{
                          fontSize: '0.78rem',
                          fontWeight: 700,
                          color: 'var(--text-muted)',
                          minWidth: '22px',
                        }}
                      >
                        #{item.rank}
                      </span>
                      <span
                        style={{
                          fontSize: '0.85rem',
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {item.label}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#34d399', display: 'block' }}>
                          {item.composite_score.toFixed(2)}
                        </span>
                        <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                          {(item.segment_share * 100).toFixed(0)}% share
                        </span>
                      </div>
                      <ChevronRight size={14} color="var(--text-muted)" />
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
