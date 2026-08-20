'use client';

import React, { useState, useEffect } from 'react';
import { EvidenceItem } from '@/lib/types';
import api from '@/lib/api';
import { QuoteCard } from './QuoteCard';
import { SourceFilter } from './SourceFilter';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import { MessageSquare, ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface EvidenceListProps {
  opportunityId: string;
  initialEvidence?: EvidenceItem[];
  totalEvidenceCount?: number;
}

export const EvidenceQuoteList: React.FC<EvidenceListProps> = ({
  opportunityId,
  initialEvidence = [],
  totalEvidenceCount = 0,
}) => {
  const [evidence, setEvidence] = useState<EvidenceItem[]>(initialEvidence);
  const [loading, setLoading] = useState(false);
  const [platform, setPlatform] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [perPage] = useState(10);
  const [totalCount, setTotalCount] = useState(totalEvidenceCount);

  useEffect(() => {
    async function loadEvidence() {
      setLoading(true);
      try {
        const res = await api.getEvidence(opportunityId, {
          page,
          per_page: perPage,
          platform: platform === 'all' ? undefined : platform,
        });
        setEvidence(res.evidence || []);
        setTotalCount(res.evidence_count || res.pagination?.total || 0);
      } catch (err) {
        console.error('Failed to load evidence:', err);
      } finally {
        setLoading(false);
      }
    }

    loadEvidence();
  }, [opportunityId, page, perPage, platform]);

  const filteredEvidence = evidence.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.verbatim_quote.toLowerCase().includes(q) ||
      item.reason_text.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.ceil(totalCount / perPage) || 1;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Search & Channel Filters */}
      <div
        className="glass"
        style={{
          padding: '16px 20px',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
        }}
      >
        <SourceFilter selectedPlatform={platform} onSelectPlatform={(p) => { setPlatform(p); setPage(1); }} />

        {/* Search */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: 'rgba(10, 13, 20, 0.6)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: '6px 12px',
            minWidth: '220px',
          }}
        >
          <Search size={14} color="var(--text-muted)" />
          <input
            type="text"
            placeholder="Search within quotes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.82rem',
              outline: 'none',
              width: '100%',
            }}
          />
        </div>
      </div>

      {/* Quote Feed */}
      {loading ? (
        <LoadingSpinner text="Retrieving verbatim quotes and platform traces..." />
      ) : filteredEvidence.length === 0 ? (
        <EmptyState
          title="No Verbatim Evidence Matches"
          description="Try changing the channel filter or search term to discover corroborating user reviews."
          icon={MessageSquare}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {filteredEvidence.map((item) => (
            <QuoteCard key={item.extraction_id} evidence={item} />
          ))}
        </div>
      )}

      {/* Pagination Footer */}
      {totalPages > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '14px 20px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--border-subtle)',
            fontSize: '0.82rem',
            color: 'var(--text-secondary)',
          }}
        >
          <span>
            Showing Page <strong>{page}</strong> of <strong>{totalPages}</strong> ({totalCount} total verified quotes)
          </span>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              <ChevronLeft size={14} />
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="btn-secondary"
              style={{ padding: '6px 12px', fontSize: '0.78rem' }}
            >
              Next
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
