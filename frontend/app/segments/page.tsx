'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { FALLBACK_SEGMENT_BREAKDOWNS, FallbackSegmentBreakdownResponse } from '@/lib/fallbackData';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import {
  PieChart,
  ChevronRight,
  Shirt,
  User,
  Tag,
  RefreshCw,
  Sparkles,
  Layers,
  ArrowUpRight,
} from 'lucide-react';

const DIMENSIONS = [
  { id: 'category', label: 'Product Category', icon: Shirt, desc: 'Prevalence across apparel & footwear sectors' },
  { id: 'gender', label: 'Gender Context', icon: User, desc: 'Distribution across target demographics' },
  { id: 'brand_tier', label: 'Brand & Price Tier', icon: Tag, desc: 'Prevalence across budget, mid-market, and premium' },
];

const SEGMENT_LABELS: Record<string, string> = {
  ethnic_wear: 'Ethnic Wear',
  western: 'Western Wear',
  western_wear: 'Western Wear',
  general: 'General Fashion & Apparel',
  footwear: 'Footwear',
  accessories: 'Accessories & Jewelry',
  women: "Women's Fashion",
  men: "Men's Fashion",
  unisex: 'Unisex',
  premium: 'Premium Brand Tier',
  mid: 'Mid-Market Tier',
  value: 'Value & Budget Tier',
};

export default function SegmentExplorerPage() {
  const [selectedDimension, setSelectedDimension] = useState('category');
  const [breakdownData, setBreakdownData] = useState<FallbackSegmentBreakdownResponse>(
    FALLBACK_SEGMENT_BREAKDOWNS['category']
  );
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const loadSegmentData = React.useCallback(async (dim: string, force = false) => {
    if (force) setRefreshing(true);
    try {
      const data = await api.getSegmentBreakdown(dim, force);
      if (data && data.breakdown && (Array.isArray(data.breakdown) || typeof data.breakdown === 'object')) {
        setBreakdownData(data);
      }
    } catch (err) {
      console.error('Failed to load segment breakdown:', err);
      setBreakdownData(FALLBACK_SEGMENT_BREAKDOWNS[dim] || FALLBACK_SEGMENT_BREAKDOWNS['category']);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    loadSegmentData(selectedDimension);
  }, [selectedDimension, loadSegmentData]);

  const activeDimensionMeta = DIMENSIONS.find((d) => d.id === selectedDimension) || DIMENSIONS[0];

  const groupedBySegment = React.useMemo(() => {
    if (!breakdownData?.breakdown) return {};

    const dict: Record<
      string,
      Array<{
        node_id: string;
        label: string;
        composite_score: number;
        rank: number;
        segment_share: number;
      }>
    > = {};

    if (Array.isArray(breakdownData.breakdown)) {
      breakdownData.breakdown.forEach((item: any) => {
        const dist = item.segment_distribution || {};
        Object.entries(dist).forEach(([rawKey, share]: [string, any]) => {
          const shareVal = Number(share);
          // Only associate if non-trivial correlation
          if (shareVal <= 0.03) return;

          // Exclude generic unclassified unknown
          if (rawKey === 'unknown') return;

          // Normalize category naming
          const normalizedKey = rawKey === 'western' ? 'western_wear' : rawKey;
          if (!dict[normalizedKey]) {
            dict[normalizedKey] = [];
          }

          dict[normalizedKey].push({
            node_id: item.node_id,
            label: item.label,
            composite_score: item.composite_score,
            rank: item.rank,
            segment_share: shareVal,
          });
        });
      });
    } else if (typeof breakdownData.breakdown === 'object') {
      // Handle legacy or dictionary breakdown shapes
      Object.entries(breakdownData.breakdown).forEach(([key, items]: [string, any]) => {
        if (Array.isArray(items)) {
          const normalizedKey = key === 'western' ? 'western_wear' : key;
          dict[normalizedKey] = items;
        }
      });
    }

    // Sort opportunities within each segment by share
    Object.keys(dict).forEach((k) => {
      dict[k].sort((a, b) => b.segment_share - a.segment_share);
    });

    // Strictly filter out any categories having 0 opportunities
    const filteredDict: Record<
      string,
      Array<{
        node_id: string;
        label: string;
        composite_score: number;
        rank: number;
        segment_share: number;
      }>
    > = {};

    Object.entries(dict).forEach(([key, list]) => {
      if (list && list.length >= 1) {
        filteredDict[key] = list;
      }
    });

    return filteredDict;
  }, [breakdownData]);

  const totalSegmentClusters = Object.keys(groupedBySegment).length;
  const totalCorrelatedOpps = Object.values(groupedBySegment).reduce((sum, list) => sum + list.length, 0);

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Top Header */}
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
                color: '#a855f7',
              }}
            >
              Cohort & Category Diagnostics
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
            Analyze how consumer drop-off frictions vary across merchandise categories, gender demographics, and brand tiers.
          </p>
        </div>

        {/* Action Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            onClick={() => loadSegmentData(selectedDimension, true)}
            disabled={refreshing}
            className="btn-secondary"
            style={{ padding: '8px 14px', fontSize: '0.82rem' }}
          >
            <RefreshCw size={14} className={refreshing ? 'animate-spin' : ''} />
            Recompute Cohorts
          </button>
        </div>
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
          marginBottom: '24px',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
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

        {/* Quick summary metric chip */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', paddingRight: '6px' }}>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Active Cohorts: <strong style={{ color: '#c084fc' }}>{totalSegmentClusters}</strong>
          </span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
            Total Segment Points: <strong style={{ color: '#38bdf8' }}>{totalCorrelatedOpps}</strong>
          </span>
        </div>
      </div>

      {/* Breakdown View */}
      {loading ? (
        <LoadingSpinner text={`Analyzing ${activeDimensionMeta.label} distributions...`} />
      ) : Object.keys(groupedBySegment).length === 0 ? (
        <EmptyState
          title="No Active Segment Opportunities"
          description="No opportunity clusters matched this dimension filter with significant prevalence."
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
              className="glass glow-hover animate-fade-in"
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: '#c084fc',
                      boxShadow: '0 0 10px #c084fc',
                    }}
                  />
                  <h3
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: '1.15rem',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      margin: 0,
                    }}
                  >
                    {SEGMENT_LABELS[segmentKey] || segmentKey.replace('_', ' ')}
                  </h3>
                </div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    padding: '3px 9px',
                    borderRadius: 'var(--radius-pill)',
                    backgroundColor: 'rgba(168, 85, 247, 0.15)',
                    color: '#c084fc',
                    border: '1px solid rgba(168, 85, 247, 0.25)',
                    fontWeight: 600,
                  }}
                >
                  {oppList.length} {oppList.length === 1 ? 'Opportunity' : 'Opportunities'}
                </span>
              </div>

              {/* Ranked opportunities in this segment */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {oppList.map((item) => (
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
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      transition: 'all var(--transition-fast)',
                      textDecoration: 'none',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(168, 85, 247, 0.1)';
                      e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.3)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
                      e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.06)';
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

                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginLeft: '12px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#34d399', display: 'block' }}>
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
