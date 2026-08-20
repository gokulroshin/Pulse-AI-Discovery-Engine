'use client';

import React from 'react';
import { OpportunityItem } from '@/lib/types';

interface CompositeScoreBarProps {
  opportunity: OpportunityItem;
  showLabels?: boolean;
}

export const CompositeScoreBar: React.FC<CompositeScoreBarProps> = ({
  opportunity,
  showLabels = false,
}) => {
  // Sub-scores
  const freq = Math.round(opportunity.frequency_score * 100);
  const tri = Math.round(opportunity.triangulation_score * 100);
  const conv = Math.round(opportunity.conversion_relevance_score * 100);
  const breadth = Math.round(opportunity.segment_breadth_score * 100);
  const act = Math.round(opportunity.actionability_score * 100);

  // Weighted score contributions (out of 100 total)
  const wFreq = (opportunity.frequency_score * 25).toFixed(1);
  const wTri = (opportunity.triangulation_score * 25).toFixed(1);
  const wConv = (opportunity.conversion_relevance_score * 25).toFixed(1);
  const wBreadth = (opportunity.segment_breadth_score * 15).toFixed(1);
  const wAct = (opportunity.actionability_score * 10).toFixed(1);

  const compositePct = Math.round(opportunity.composite_score * 100);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', width: '100%' }}>
      {/* Bar container */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}
      >
        <div
          style={{
            flex: 1,
            height: '8px',
            backgroundColor: 'rgba(255, 255, 255, 0.06)',
            borderRadius: '9999px',
            overflow: 'hidden',
            display: 'flex',
            position: 'relative',
          }}
          title={`Freq: ${freq}% (w: ${wFreq}), Tri: ${tri}% (w: ${wTri}), Conv: ${conv}% (w: ${wConv}), Breadth: ${breadth}% (w: ${wBreadth}), Act: ${act}% (w: ${wAct})`}
        >
          {/* Segmented bar representation */}
          <div style={{ width: `${wFreq}%`, backgroundColor: '#6366f1' }} />
          <div style={{ width: `${wTri}%`, backgroundColor: '#38bdf8' }} />
          <div style={{ width: `${wConv}%`, backgroundColor: '#10b981' }} />
          <div style={{ width: `${wBreadth}%`, backgroundColor: '#a855f7' }} />
          <div style={{ width: `${wAct}%`, backgroundColor: '#f59e0b' }} />
        </div>

        <span
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '0.85rem',
            fontWeight: 700,
            color: compositePct >= 50 ? '#34d399' : '#c7d2fe',
            minWidth: '38px',
            textAlign: 'right',
          }}
        >
          {opportunity.composite_score.toFixed(2)}
        </span>
      </div>

      {showLabels && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            fontSize: '0.72rem',
            color: 'var(--text-muted)',
            flexWrap: 'wrap',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#6366f1' }} />
            Freq: {freq}%
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#38bdf8' }} />
            Triang: {tri}%
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#10b981' }} />
            Relevance: {conv}%
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#a855f7' }} />
            Breadth: {breadth}%
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#f59e0b' }} />
            Action: {act}%
          </span>
        </div>
      )}
    </div>
  );
};
