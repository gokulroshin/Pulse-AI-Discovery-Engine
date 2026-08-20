'use client';

import React from 'react';
import { PieChart, Layers } from 'lucide-react';

interface SegmentBreakdownProps {
  segmentData?: {
    by_category?: Record<string, number>;
    by_gender?: Record<string, number>;
    by_brand_tier?: Record<string, number>;
    by_price_tier?: Record<string, number>;
  };
  title?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  ethnic_wear: '#ec4899',
  western_wear: '#6366f1',
  footwear: '#f59e0b',
  general: '#94a3b8',
};

const GENDER_COLORS: Record<string, string> = {
  women: '#f43f5e',
  men: '#38bdf8',
  unisex: '#10b981',
  general: '#94a3b8',
};

const TIER_COLORS: Record<string, string> = {
  premium: '#a855f7',
  mid: '#6366f1',
  value: '#10b981',
  general: '#94a3b8',
};

export const SegmentBreakdownChart: React.FC<SegmentBreakdownProps> = ({
  segmentData,
  title = 'Segment Prevalence Distributions',
}) => {
  const categories = segmentData?.by_category || { ethnic_wear: 0.42, western_wear: 0.38, footwear: 0.2 };
  const genders = segmentData?.by_gender || { women: 0.65, men: 0.28, unisex: 0.07 };
  const tiers = segmentData?.by_brand_tier || segmentData?.by_price_tier || { premium: 0.35, mid: 0.45, value: 0.2 };

  const renderBarGroup = (
    label: string,
    data: Record<string, number>,
    colorMap: Record<string, string>
  ) => {
    const entries = Object.entries(data);
    const total = entries.reduce((acc, [, val]) => acc + val, 0) || 1;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
            {label}
          </span>
        </div>

        {/* Stacked bar */}
        <div
          style={{
            height: '14px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            display: 'flex',
            overflow: 'hidden',
          }}
        >
          {entries.map(([key, val]) => {
            const pct = Math.max(2, Math.round((val / total) * 100));
            const color = colorMap[key] || '#6366f1';
            return (
              <div
                key={key}
                style={{
                  width: `${pct}%`,
                  backgroundColor: color,
                  transition: 'width var(--transition-normal)',
                }}
                title={`${key.replace('_', ' ')}: ${(val * 100).toFixed(0)}%`}
              />
            );
          })}
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', fontSize: '0.72rem' }}>
          {entries.map(([key, val]) => {
            const color = colorMap[key] || '#6366f1';
            const pct = Math.round((val / total) * 100);
            return (
              <div key={key} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: color }} />
                <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                  {key.replace('_', ' ')}:
                </span>
                <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{pct}%</span>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div
      className="glass"
      style={{
        padding: '22px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
        <Layers size={18} color="#a855f7" />
        <h4
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '1rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          {title}
        </h4>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {renderBarGroup('Category Context', categories, CATEGORY_COLORS)}
        {renderBarGroup('Gender Context', genders, GENDER_COLORS)}
        {renderBarGroup('Brand / Price Tier', tiers, TIER_COLORS)}
      </div>
    </div>
  );
};
