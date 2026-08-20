'use client';

import React from 'react';
import { PLATFORM_METADATA } from '@/lib/constants';
import { Filter, Check } from 'lucide-react';

interface FilterProps {
  selectedPlatform: string;
  onSelectPlatform: (platform: string) => void;
  availablePlatforms?: string[];
}

export const SourceFilter: React.FC<FilterProps> = ({
  selectedPlatform,
  onSelectPlatform,
  availablePlatforms = ['all', 'reddit', 'playstore', 'appstore', 'youtube', 'manual_upload'],
}) => {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
      <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
        <Filter size={13} />
        Channel:
      </span>

      {availablePlatforms.map((plat) => {
        const isSelected = selectedPlatform === plat;
        const meta = PLATFORM_METADATA[plat] || {
          label: plat === 'all' ? 'All Channels' : plat,
          color: '#818cf8',
        };

        return (
          <button
            key={plat}
            onClick={() => onSelectPlatform(plat)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '5px 12px',
              borderRadius: 'var(--radius-pill)',
              fontSize: '0.78rem',
              fontWeight: isSelected ? 600 : 500,
              backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(255, 255, 255, 0.04)',
              color: isSelected ? '#ffffff' : 'var(--text-secondary)',
              border: isSelected ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid var(--border-subtle)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
          >
            {isSelected && <Check size={12} color="#818cf8" />}
            {meta.label}
          </button>
        );
      })}
    </div>
  );
};
