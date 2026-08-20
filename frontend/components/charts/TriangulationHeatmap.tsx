'use client';

import React from 'react';
import Link from 'next/link';
import { OpportunityItem } from '@/lib/types';
import { PLATFORM_METADATA } from '@/lib/constants';
import { Radio } from 'lucide-react';

interface HeatmapProps {
  opportunities: OpportunityItem[];
}

const PLATFORMS = ['reddit', 'playstore', 'appstore', 'youtube'];

export const TriangulationHeatmap: React.FC<HeatmapProps> = ({ opportunities }) => {
  // Take top 8 opportunities for the matrix
  const topOpps = opportunities.slice(0, 8);

  const getHeatIntensity = (opp: OpportunityItem, platform: string): { count: number; alpha: number; color: string } => {
    const breakdown = opp.source_platform_breakdown || {};
    const count = breakdown[platform] || (opp.top_sources.includes(platform as any) ? Math.max(1, Math.round(opp.extraction_count * 0.25)) : 0);
    
    // Normalize alpha from 0 to 1
    const maxCount = Math.max(1, opp.extraction_count);
    const ratio = count / maxCount;
    const alpha = count === 0 ? 0.04 : Math.min(0.9, 0.2 + ratio * 0.8);
    
    const meta = PLATFORM_METADATA[platform] || { color: '#6366f1' };
    return { count, alpha, color: meta.color };
  };

  return (
    <div
      className="glass"
      style={{
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        marginBottom: '28px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <Radio size={18} color="#38bdf8" />
            <h3
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.1rem',
                fontWeight: 700,
                color: 'var(--text-primary)',
                margin: 0,
              }}
            >
              Cross-Platform Triangulation Heatmap
            </h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
            Visual confirmation matrix showing causal signals corroborated across multiple channels
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <span>Intensity:</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: 'rgba(56, 189, 248, 0.15)' }} />
            <span>Low</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: 'rgba(56, 189, 248, 0.5)' }} />
            <span>Med</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '3px', backgroundColor: '#38bdf8' }} />
            <span>High</span>
          </div>
        </div>
      </div>

      {/* Grid Matrix */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr>
              <th style={{ padding: '10px 14px', textAlign: 'left', color: 'var(--text-muted)', fontSize: '0.75rem', width: '280px' }}>
                Opportunity Area
              </th>
              {PLATFORMS.map((plat) => {
                const meta = PLATFORM_METADATA[plat];
                return (
                  <th
                    key={plat}
                    style={{
                      padding: '10px 14px',
                      textAlign: 'center',
                      color: meta?.color || 'var(--text-secondary)',
                      fontSize: '0.78rem',
                      fontWeight: 600,
                      minWidth: '120px',
                    }}
                  >
                    {meta?.label || plat}
                  </th>
                );
              })}
              <th style={{ padding: '10px 14px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.75rem', width: '100px' }}>
                Triang. Score
              </th>
            </tr>
          </thead>
          <tbody>
            {topOpps.map((opp) => (
              <tr key={opp.node_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                {/* Opportunity Label */}
                <td style={{ padding: '12px 14px' }}>
                  <Link
                    href={`/opportunities/${opp.node_id}`}
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontWeight: 600,
                      color: 'var(--text-primary)',
                      fontSize: '0.88rem',
                      display: 'block',
                      transition: 'color var(--transition-fast)',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#818cf8')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
                  >
                    #{opp.rank} {opp.label}
                  </Link>
                </td>

                {/* Heatmap cells */}
                {PLATFORMS.map((plat) => {
                  const { count, alpha, color } = getHeatIntensity(opp, plat);
                  const isPresent = count > 0;
                  return (
                    <td key={plat} style={{ padding: '8px 10px', textAlign: 'center' }}>
                      <div
                        style={{
                          height: '38px',
                          borderRadius: '8px',
                          backgroundColor: isPresent ? `${color}${Math.round(alpha * 255).toString(16).padStart(2, '0')}` : 'rgba(255, 255, 255, 0.02)',
                          border: isPresent ? `1px solid ${color}40` : '1px dashed rgba(255, 255, 255, 0.05)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexDirection: 'column',
                          transition: 'all var(--transition-fast)',
                          cursor: isPresent ? 'pointer' : 'default',
                        }}
                        title={`${opp.label} on ${plat}: ${count} corroborated extractions`}
                      >
                        {isPresent ? (
                          <>
                            <span style={{ fontWeight: 700, fontSize: '0.85rem', color: '#ffffff' }}>
                              {count}
                            </span>
                            <span style={{ fontSize: '0.62rem', color: 'rgba(255, 255, 255, 0.8)' }}>
                              signals
                            </span>
                          </>
                        ) : (
                          <span style={{ color: 'rgba(255, 255, 255, 0.15)', fontSize: '0.75rem' }}>-</span>
                        )}
                      </div>
                    </td>
                  );
                })}

                {/* Triangulation score */}
                <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontWeight: 700,
                      fontSize: '0.8rem',
                      backgroundColor: 'rgba(56, 189, 248, 0.12)',
                      color: '#38bdf8',
                      border: '1px solid rgba(56, 189, 248, 0.3)',
                    }}
                  >
                    {(opp.triangulation_score * 100).toFixed(0)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
