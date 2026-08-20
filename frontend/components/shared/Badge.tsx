import React from 'react';
import { ConfidenceLevel, SourcePlatform, SignalType } from '@/lib/types';
import { PLATFORM_METADATA, SIGNAL_TYPE_METADATA } from '@/lib/constants';

interface BadgeProps {
  children?: React.ReactNode;
  variant?: 'platform' | 'confidence' | 'signal' | 'rank' | 'status' | 'custom';
  value?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function PlatformBadge({ platform }: { platform: SourcePlatform }) {
  const meta = PLATFORM_METADATA[platform.toLowerCase()] || {
    label: platform,
    color: '#94a3b8',
    bg: 'rgba(148, 163, 184, 0.12)',
    border: 'rgba(148, 163, 184, 0.25)',
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '2px 9px',
        borderRadius: '9999px',
        fontSize: '0.72rem',
        fontWeight: 600,
        backgroundColor: meta.bg,
        color: meta.color,
        border: `1px solid ${meta.border}`,
        whiteSpace: 'nowrap',
        textTransform: 'capitalize',
      }}
    >
      <span
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: meta.color,
        }}
      />
      {meta.label}
    </span>
  );
}

export function ConfidenceBadge({ level }: { level: ConfidenceLevel }) {
  const isHigh = level === 'high';
  const isMedium = level === 'medium';

  const color = isHigh ? '#34d399' : isMedium ? '#fbbf24' : '#94a3b8';
  const bg = isHigh
    ? 'rgba(16, 185, 129, 0.12)'
    : isMedium
      ? 'rgba(245, 158, 11, 0.12)'
      : 'rgba(148, 163, 184, 0.12)';
  const border = isHigh
    ? 'rgba(16, 185, 129, 0.3)'
    : isMedium
      ? 'rgba(245, 158, 11, 0.3)'
      : 'rgba(148, 163, 184, 0.25)';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        padding: '2px 8px',
        borderRadius: '9999px',
        fontSize: '0.7rem',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${border}`,
      }}
    >
      <span
        style={{
          width: '5px',
          height: '5px',
          borderRadius: '50%',
          backgroundColor: color,
          boxShadow: isHigh ? '0 0 6px rgba(52, 211, 153, 0.6)' : 'none',
        }}
      />
      {level}
    </span>
  );
}

export function SignalBadge({ signal }: { signal: SignalType }) {
  const meta = SIGNAL_TYPE_METADATA[signal] || {
    label: signal,
    color: '#8b5cf6',
    bg: 'rgba(139, 92, 246, 0.12)',
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: '6px',
        fontSize: '0.72rem',
        fontWeight: 600,
        backgroundColor: meta.bg,
        color: meta.color,
        border: `1px solid ${meta.color}33`,
        textTransform: 'capitalize',
      }}
    >
      {meta.label}
    </span>
  );
}

export function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 60 ? '#10b981' : pct >= 40 ? '#6366f1' : pct >= 25 ? '#f59e0b' : '#94a3b8';
  const bg =
    pct >= 60
      ? 'rgba(16, 185, 129, 0.12)'
      : pct >= 40
        ? 'rgba(99, 102, 241, 0.12)'
        : pct >= 25
          ? 'rgba(245, 158, 11, 0.12)'
          : 'rgba(148, 163, 184, 0.12)';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3px 10px',
        borderRadius: '8px',
        fontSize: '0.85rem',
        fontWeight: 700,
        fontFamily: 'var(--font-heading)',
        backgroundColor: bg,
        color: color,
        border: `1px solid ${color}40`,
        minWidth: '48px',
      }}
    >
      {score.toFixed(2)}
    </span>
  );
}
