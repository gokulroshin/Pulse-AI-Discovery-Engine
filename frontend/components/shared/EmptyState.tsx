import React from 'react';
import { Database, Sparkles, RefreshCw } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ElementType;
}

export function EmptyState({
  title = 'No Opportunity Data Found',
  description = 'Run the ingestion, extraction, and clustering pipeline to populate real-world consumer discovery insights.',
  actionText,
  onAction,
  icon: Icon = Database,
}: EmptyStateProps) {
  return (
    <div
      className="glass"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '50px 24px',
        textAlign: 'center',
        margin: '20px 0',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '16px',
          backgroundColor: 'rgba(99, 102, 241, 0.12)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#6366f1',
          marginBottom: '16px',
        }}
      >
        <Icon size={28} />
      </div>

      <h3
        style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '1.15rem',
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: '8px',
        }}
      >
        {title}
      </h3>

      <p
        style={{
          color: 'var(--text-secondary)',
          fontSize: '0.875rem',
          maxWidth: '440px',
          lineHeight: '1.5',
          marginBottom: actionText ? '20px' : '0',
        }}
      >
        {description}
      </p>

      {actionText && onAction && (
        <button onClick={onAction} className="btn-primary">
          <RefreshCw size={15} />
          {actionText}
        </button>
      )}
    </div>
  );
}
