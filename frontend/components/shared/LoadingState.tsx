import React from 'react';

export function SkeletonRow({ cols = 6 }: { cols?: number }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '16px 20px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
      }}
    >
      {Array.from({ length: cols }).map((_, i) => (
        <div
          key={i}
          className="skeleton"
          style={{
            height: '18px',
            flex: i === 1 ? 3 : 1,
            borderRadius: '6px',
          }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ height = '120px' }: { height?: string }) {
  return (
    <div
      className="glass skeleton"
      style={{
        height,
        borderRadius: '16px',
        width: '100%',
      }}
    />
  );
}

export function LoadingSpinner({ text = 'Analyzing corpus data...' }: { text?: string }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 20px',
        gap: '16px',
      }}
    >
      <div
        style={{
          width: '40px',
          height: '40px',
          borderRadius: '50%',
          border: '3px solid rgba(99, 102, 241, 0.15)',
          borderTopColor: '#6366f1',
          animation: 'spin 0.8s linear infinite',
        }}
      />
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{text}</p>
      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}
