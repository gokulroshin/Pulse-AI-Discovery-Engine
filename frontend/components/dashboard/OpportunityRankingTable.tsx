'use client';

import React, { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Search,
  ChevronRight,
  Filter,
  Sparkles,
  ExternalLink,
} from 'lucide-react';
import { OpportunityItem, ConfidenceLevel } from '@/lib/types';
import { PlatformBadge, ConfidenceBadge, ScoreBadge } from '@/components/shared/Badge';
import { CompositeScoreBar } from './CompositeScoreBar';

interface TableProps {
  opportunities: OpportunityItem[];
  loading?: boolean;
}

type SortField =
  | 'rank'
  | 'composite_score'
  | 'frequency_score'
  | 'triangulation_score'
  | 'conversion_relevance_score'
  | 'actionability_score'
  | 'extraction_count';

export const OpportunityRankingTable: React.FC<TableProps> = ({
  opportunities,
  loading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [confidenceFilter, setConfidenceFilter] = useState<'all' | ConfidenceLevel>('all');
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortAsc, setSortAsc] = useState(true);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === 'rank');
    }
  };

  const filteredAndSorted = useMemo(() => {
    let result = [...opportunities];

    // Filter by search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      result = result.filter(
        (item) =>
          item.label.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q)
      );
    }

    // Filter by confidence
    if (confidenceFilter !== 'all') {
      result = result.filter((item) => item.confidence_level === confidenceFilter);
    }

    // Sort
    result.sort((a, b) => {
      const valA = a[sortField] ?? 0;
      const valB = b[sortField] ?? 0;

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });

    return result;
  }, [opportunities, searchTerm, confidenceFilter, sortField, sortAsc]);

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown size={13} style={{ opacity: 0.4 }} />;
    }
    return sortAsc ? <ArrowUp size={13} color="#818cf8" /> : <ArrowDown size={13} color="#818cf8" />;
  };

  return (
    <div
      className="glass"
      style={{
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        border: '1px solid var(--border-subtle)',
      }}
    >
      {/* Controls Bar */}
      <div
        style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '14px',
          background: 'rgba(255, 255, 255, 0.01)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={18} color="#6366f1" />
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.15rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Ranked Business Opportunity Areas
          </h2>
          <span
            style={{
              fontSize: '0.75rem',
              padding: '2px 8px',
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(99, 102, 241, 0.15)',
              color: '#a5b4fc',
              fontWeight: 600,
            }}
          >
            {filteredAndSorted.length} Areas
          </span>
        </div>

        {/* Search and Filters */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Search Box */}
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
            <Search size={15} color="var(--text-muted)" />
            <input
              type="text"
              placeholder="Search opportunities..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: '0.85rem',
                outline: 'none',
                width: '100%',
              }}
            />
          </div>

          {/* Confidence Filter */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(10, 13, 20, 0.6)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              padding: '4px 8px',
            }}
          >
            <Filter size={14} color="var(--text-muted)" />
            <select
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value as any)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-secondary)',
                fontSize: '0.8rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="all" style={{ background: '#111726' }}>All Confidence</option>
              <option value="high" style={{ background: '#111726' }}>High (≥2 sources)</option>
              <option value="medium" style={{ background: '#111726' }}>Medium</option>
              <option value="low" style={{ background: '#111726' }}>Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div style={{ overflowX: 'auto' }}>
        <table
          style={{
            width: '100%',
            borderCollapse: 'collapse',
            textAlign: 'left',
            fontSize: '0.875rem',
          }}
        >
          <thead>
            <tr
              style={{
                borderBottom: '1px solid var(--border-subtle)',
                background: 'rgba(10, 13, 20, 0.4)',
                color: 'var(--text-muted)',
                fontSize: '0.75rem',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              <th
                onClick={() => handleSort('rank')}
                style={{ padding: '14px 20px', cursor: 'pointer', width: '70px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Rank {renderSortIcon('rank')}
                </div>
              </th>
              <th style={{ padding: '14px 20px', minWidth: '280px' }}>
                Opportunity Label & Description
              </th>
              <th
                onClick={() => handleSort('composite_score')}
                style={{ padding: '14px 20px', cursor: 'pointer', minWidth: '170px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  Composite Score {renderSortIcon('composite_score')}
                </div>
              </th>
              <th
                onClick={() => handleSort('conversion_relevance_score')}
                style={{ padding: '14px 16px', cursor: 'pointer', textAlign: 'center' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                  Conv. Rel {renderSortIcon('conversion_relevance_score')}
                </div>
              </th>
              <th
                onClick={() => handleSort('triangulation_score')}
                style={{ padding: '14px 16px', cursor: 'pointer', textAlign: 'center' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                  Triangulation {renderSortIcon('triangulation_score')}
                </div>
              </th>
              <th
                onClick={() => handleSort('extraction_count')}
                style={{ padding: '14px 16px', cursor: 'pointer', textAlign: 'center' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
                  Evidence {renderSortIcon('extraction_count')}
                </div>
              </th>
              <th style={{ padding: '14px 20px', minWidth: '150px' }}>Sources</th>
              <th style={{ padding: '14px 20px', textAlign: 'right' }}>Drill-Down</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSorted.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  No opportunity areas matched the filter criteria.
                </td>
              </tr>
            ) : (
              filteredAndSorted.map((item) => (
                <tr
                  key={item.node_id}
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    transition: 'background 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.04)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                  }}
                >
                  {/* Rank */}
                  <td style={{ padding: '16px 20px' }}>
                    <div
                      style={{
                        width: '28px',
                        height: '28px',
                        borderRadius: '8px',
                        backgroundColor:
                          item.rank === 1
                            ? 'rgba(245, 158, 11, 0.2)'
                            : item.rank === 2
                            ? 'rgba(148, 163, 184, 0.2)'
                            : item.rank === 3
                            ? 'rgba(180, 83, 9, 0.2)'
                            : 'rgba(255, 255, 255, 0.04)',
                        border:
                          item.rank === 1
                            ? '1px solid rgba(245, 158, 11, 0.4)'
                            : '1px solid rgba(255, 255, 255, 0.08)',
                        color:
                          item.rank === 1
                            ? '#fbbf24'
                            : item.rank === 2
                            ? '#e2e8f0'
                            : item.rank === 3
                            ? '#f97316'
                            : 'var(--text-secondary)',
                        fontFamily: 'var(--font-heading)',
                        fontWeight: 700,
                        fontSize: '0.85rem',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      #{item.rank}
                    </div>
                  </td>

                  {/* Label & Description */}
                  <td style={{ padding: '16px 20px' }}>
                    <Link
                      href={`/opportunities/${item.node_id}`}
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontWeight: 600,
                        fontSize: '0.95rem',
                        color: 'var(--text-primary)',
                        display: 'block',
                        marginBottom: '4px',
                      }}
                    >
                      {item.label}
                    </Link>
                    <p
                      style={{
                        fontSize: '0.78rem',
                        color: 'var(--text-muted)',
                        lineHeight: '1.4',
                        maxWidth: '420px',
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        margin: 0,
                      }}
                    >
                      {item.description}
                    </p>
                  </td>

                  {/* Composite Score Bar */}
                  <td style={{ padding: '16px 20px' }}>
                    <CompositeScoreBar opportunity={item} showLabels={false} />
                  </td>

                  {/* Conversion Relevance */}
                  <td style={{ padding: '16px 16px', textAlign: 'center' }}>
                    <span
                      style={{
                        fontWeight: 600,
                        color: item.conversion_relevance_score >= 0.7 ? '#34d399' : '#cbd5e1',
                        fontSize: '0.85rem',
                      }}
                    >
                      {(item.conversion_relevance_score * 100).toFixed(0)}%
                    </span>
                  </td>

                  {/* Triangulation & Confidence */}
                  <td style={{ padding: '16px 16px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px' }}>
                      <span style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.85rem' }}>
                        {(item.triangulation_score * 100).toFixed(0)}%
                      </span>
                      <ConfidenceBadge level={item.confidence_level} />
                    </div>
                  </td>

                  {/* Extractions Count */}
                  <td style={{ padding: '16px 16px', textAlign: 'center' }}>
                    <span
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontWeight: 700,
                        color: 'var(--text-primary)',
                        fontSize: '0.9rem',
                      }}
                    >
                      {item.extraction_count}
                    </span>
                    <span style={{ display: 'block', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      quotes
                    </span>
                  </td>

                  {/* Top Sources */}
                  <td style={{ padding: '16px 20px' }}>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {item.top_sources.slice(0, 3).map((plat, i) => (
                        <PlatformBadge key={i} platform={plat} />
                      ))}
                      {item.top_sources.length > 3 && (
                        <span
                          style={{
                            fontSize: '0.7rem',
                            color: 'var(--text-muted)',
                            alignSelf: 'center',
                          }}
                        >
                          +{item.top_sources.length - 3}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Action Link */}
                  <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                    <Link
                      href={`/opportunities/${item.node_id}`}
                      className="btn-secondary"
                      style={{
                        padding: '6px 12px',
                        fontSize: '0.78rem',
                        display: 'inline-flex',
                      }}
                    >
                      <span>Evidence</span>
                      <ChevronRight size={14} />
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
