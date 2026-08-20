'use client';

import React from 'react';
import Link from 'next/link';
import { Sparkles, Compass } from 'lucide-react';
import { APP_CONFIG } from '@/lib/constants';

export const Navbar: React.FC = () => {
  return (
    <header
      style={{
        height: '68px',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(10, 13, 20, 0.85)',
        backdropFilter: 'blur(20px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 36px',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Brand & Title */}
      <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '12px',
            background: 'var(--accent-indigo-gradient)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 18px rgba(99, 102, 241, 0.45)',
          }}
        >
          <Sparkles size={22} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontFamily: 'var(--font-heading)',
                fontSize: '1.35rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                background: 'linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              {APP_CONFIG.name}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {APP_CONFIG.tagline}
          </span>
        </div>
      </Link>

      {/* Center Subtitle */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.03)',
          padding: '6px 18px',
          borderRadius: 'var(--radius-pill)',
          border: '1px solid var(--border-subtle)',
          fontSize: '0.82rem',
          color: 'var(--text-secondary)',
        }}
      >
        <Compass size={15} color="#818cf8" />
        <span>Continuous Customer Voice & Wishlist Behavior Intelligence</span>
      </div>

      {/* Right User Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            padding: '6px 14px',
            borderRadius: 'var(--radius-pill)',
            background: 'rgba(99, 102, 241, 0.12)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            fontSize: '0.8rem',
            fontWeight: 600,
            color: '#c7d2fe',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Sparkles size={14} color="#818cf8" />
          <span>AI Discovery Engine</span>
        </div>
      </div>
    </header>
  );
};
