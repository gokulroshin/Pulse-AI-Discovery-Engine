'use client';

import React from 'react';
import { EvidenceItem } from '@/lib/types';
import { PlatformBadge, ConfidenceBadge, SignalBadge } from '@/components/shared/Badge';
import { MessageSquare, ExternalLink, ThumbsUp, Calendar } from 'lucide-react';

interface QuoteCardProps {
  evidence: EvidenceItem;
}

export const QuoteCard: React.FC<QuoteCardProps> = ({ evidence }) => {
  return (
    <div
      className="glass glow-hover"
      style={{
        padding: '20px 22px',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
      }}
    >
      {/* Top Header: Platform & Signal Badges */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PlatformBadge platform={evidence.source_platform} />
          <ConfidenceBadge level={evidence.confidence} />
          {evidence.signal_type && <SignalBadge signal={evidence.signal_type} />}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {evidence.engagement_score > 0 && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ThumbsUp size={13} color="#818cf8" />
              {evidence.engagement_score} upvotes
            </span>
          )}
          {evidence.source_timestamp && (
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Calendar size={13} />
              {new Date(evidence.source_timestamp).toLocaleDateString()}
            </span>
          )}
        </div>
      </div>

      {/* Verbatim Quote Highlight */}
      <div
        style={{
          background: 'rgba(99, 102, 241, 0.05)',
          borderLeft: '3px solid #6366f1',
          padding: '12px 16px',
          borderRadius: '0 8px 8px 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
          <MessageSquare size={16} color="#818cf8" style={{ flexShrink: 0, marginTop: '2px' }} />
          <p
            style={{
              fontSize: '0.9rem',
              color: 'var(--text-primary)',
              fontStyle: 'italic',
              lineHeight: '1.5',
              margin: 0,
            }}
          >
            "{evidence.verbatim_quote}"
          </p>
        </div>
      </div>

      {/* Extracted Causal Reason */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '4px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
            Extracted Causal Friction:
          </span>
          <span style={{ fontSize: '0.82rem', fontWeight: 600, color: '#c7d2fe' }}>
            {evidence.reason_text}
          </span>
        </div>

        {evidence.source_url && (
          <a
            href={evidence.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '0.75rem',
              color: '#818cf8',
              textDecoration: 'none',
            }}
          >
            <span>Source URL</span>
            <ExternalLink size={12} />
          </a>
        )}
      </div>
    </div>
  );
};
