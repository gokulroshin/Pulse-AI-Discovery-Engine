'use client';

import React from 'react';
import { PLATFORM_METADATA } from '@/lib/constants';
import { PieChart as PieIcon } from 'lucide-react';

interface SourcePieProps {
  distribution: Record<string, number>;
  title?: string;
  totalDocs?: number;
}

export const SourceDistributionPie: React.FC<SourcePieProps> = ({
  distribution,
  title = 'Platform Source Breakdown',
  totalDocs,
}) => {
  const entries = Object.entries(distribution);
  const total = totalDocs || entries.reduce((acc, [, val]) => acc + val, 0) || 1;

  // Compute angles for SVG donut
  let cumulativeAngle = 0;
  const slices = entries.map(([platform, count]) => {
    const fraction = count / total;
    const angle = fraction * 360;
    const startAngle = cumulativeAngle;
    cumulativeAngle += angle;
    const meta = PLATFORM_METADATA[platform] || {
      label: platform,
      color: '#6366f1',
    };

    return {
      platform,
      count,
      fraction,
      startAngle,
      angle,
      color: meta.color,
      label: meta.label,
    };
  });

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
        <PieIcon size={18} color="#6366f1" />
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

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around',
          gap: '20px',
          flexWrap: 'wrap',
        }}
      >
        {/* SVG Donut */}
        <div style={{ position: 'relative', width: '130px', height: '130px' }}>
          <svg width="130" height="130" viewBox="0 0 100 100" style={{ transform: 'rotate(-90deg)' }}>
            {slices.map((slice, i) => {
              const r = 38;
              const cx = 50;
              const cy = 50;
              const strokeDasharray = `${(slice.fraction * 238.76).toFixed(2)} 238.76`;
              const strokeDashoffset = `-${((slice.startAngle / 360) * 238.76).toFixed(2)}`;

              return (
                <circle
                  key={i}
                  cx={cx}
                  cy={cy}
                  r={r}
                  fill="transparent"
                  stroke={slice.color}
                  strokeWidth="14"
                  strokeDasharray={strokeDasharray}
                  strokeDashoffset={strokeDashoffset}
                  style={{ transition: 'stroke-dasharray 0.3s ease' }}
                />
              );
            })}
          </svg>

          {/* Center text */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none',
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.1rem',
                fontWeight: 800,
                color: 'var(--text-primary)',
                lineHeight: '1',
              }}
            >
              {total.toLocaleString()}
            </span>
            <span style={{ fontSize: '0.62rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Docs
            </span>
          </div>
        </div>

        {/* Legend List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1, minWidth: '150px' }}>
          {slices.map((slice) => (
            <div
              key={slice.platform}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.8rem',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    width: '8px',
                    height: '8px',
                    borderRadius: '50%',
                    backgroundColor: slice.color,
                  }}
                />
                <span style={{ color: 'var(--text-secondary)' }}>{slice.label}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                  {slice.count.toLocaleString()}
                </span>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                  ({(slice.fraction * 100).toFixed(0)}%)
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
