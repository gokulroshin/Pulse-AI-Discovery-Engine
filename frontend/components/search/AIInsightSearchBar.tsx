'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { InsightResponse } from '@/lib/types';
import { PlatformBadge } from '@/components/shared/Badge';
import {
  Sparkles,
  Search,
  ArrowRight,
  MessageSquareQuote,
  CheckCircle2,
  Layers,
  ChevronRight,
  X,
  ExternalLink,
  Bot,
  Lightbulb,
  Compass,
} from 'lucide-react';

const SUGGESTED_QUESTIONS = [
  'Why do users add fashion products to their wishlist?',
  'What prevents wishlisted products from eventually being purchased?',
  'What uncertainties remain after users have identified a product they like?',
];

export const AIInsightSearchBar: React.FC = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [insightResult, setInsightResult] = useState<InsightResponse | null>(null);
  const [showResultModal, setShowResultModal] = useState(false);

  const handleSearch = async (questionToAsk: string) => {
    const q = questionToAsk.trim();
    if (!q) return;

    setQuery(q);
    setLoading(true);
    setShowResultModal(true);

    try {
      const res = await api.askInsight(q);
      setInsightResult(res);
    } catch (err) {
      console.error('Failed to query insight:', err);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(query);
  };

  return (
    <div style={{ width: '100%', marginBottom: '32px' }}>
      {/* Search Bar Container */}
      <div
        className="glass glow-hover"
        style={{
          padding: '24px 28px',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
          background: 'linear-gradient(135deg, rgba(23, 31, 50, 0.85) 0%, rgba(17, 23, 38, 0.95) 100%)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.45)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '8px',
              background: 'var(--accent-indigo-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Sparkles size={16} color="#ffffff" />
          </div>
          <h2
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.25rem',
              fontWeight: 800,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Ask AI Discovery Engine
          </h2>
          <span
            style={{
              fontSize: '0.72rem',
              padding: '3px 8px',
              borderRadius: '9999px',
              backgroundColor: 'rgba(99, 102, 241, 0.15)',
              color: '#a5b4fc',
              fontWeight: 600,
            }}
          >
            Corpus-Grounded Synthesis
          </span>
        </div>

        <form onSubmit={onSubmit} style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div
            style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              backgroundColor: 'rgba(10, 13, 20, 0.75)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 'var(--radius-md)',
              padding: '12px 18px',
              transition: 'border-color var(--transition-fast)',
            }}
          >
            <Search size={18} color="#818cf8" />
            <input
              type="text"
              placeholder="Ask anything (e.g., 'What causes users to postpone wishlisted items?', 'Why do users seek YouTube try-ons?')..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                fontSize: '0.92rem',
                outline: 'none',
                width: '100%',
                fontFamily: 'var(--font-body)',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary"
            style={{ padding: '12px 24px', fontSize: '0.92rem', flexShrink: 0 }}
          >
            <Sparkles size={16} />
            {loading ? 'Synthesizing...' : 'Ask Engine'}
          </button>
        </form>

        {/* Suggested Question Chips */}
        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
            <Compass size={13} color="var(--text-muted)" />
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
              Core Discovery Questions:
            </span>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {SUGGESTED_QUESTIONS.map((qText, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSearch(qText)}
                style={{
                  padding: '6px 12px',
                  borderRadius: 'var(--radius-pill)',
                  backgroundColor: 'rgba(255, 255, 255, 0.04)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  color: 'var(--text-secondary)',
                  fontSize: '0.78rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all var(--transition-fast)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.15)';
                  e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.35)';
                  e.currentTarget.style.color = '#ffffff';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                {qText}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* AI Insight Response Panel */}
      {showResultModal && (
        <div
          className="glass animate-fade-in"
          style={{
            marginTop: '20px',
            padding: '28px 32px',
            borderRadius: 'var(--radius-xl)',
            border: '1px solid rgba(99, 102, 241, 0.4)',
            backgroundColor: 'rgba(15, 20, 35, 0.95)',
            boxShadow: '0 12px 40px rgba(0, 0, 0, 0.6)',
            position: 'relative',
          }}
        >
          {/* Close button */}
          <button
            onClick={() => setShowResultModal(false)}
            style={{
              position: 'absolute',
              top: '20px',
              right: '20px',
              background: 'rgba(255, 255, 255, 0.06)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '50%',
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)',
              cursor: 'pointer',
            }}
          >
            <X size={16} />
          </button>

          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  border: '3px solid rgba(99, 102, 241, 0.15)',
                  borderTopColor: '#6366f1',
                  animation: 'spin 0.8s linear infinite',
                  margin: '0 auto 16px auto',
                }}
              />
              <p style={{ color: '#a5b4fc', fontSize: '0.9rem' }}>
                Analyzing multi-channel consumer reviews & synthesized opportunity clusters...
              </p>
              <style jsx>{`
                @keyframes spin {
                  to { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          ) : insightResult ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
              {/* Question Header */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <Bot size={18} color="#818cf8" />
                  <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#818cf8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Pulse AI Synthesis
                  </span>
                </div>
                <h3
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '1.45rem',
                    fontWeight: 800,
                    color: 'var(--text-primary)',
                    margin: 0,
                    lineHeight: '1.3',
                  }}
                >
                  {insightResult.question}
                </h3>
              </div>

              {/* Executive Summary Box */}
              <div
                style={{
                  padding: '16px 20px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'rgba(99, 102, 241, 0.12)',
                  borderLeft: '4px solid #6366f1',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                  <Lightbulb size={16} color="#fbbf24" />
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#c7d2fe', textTransform: 'uppercase' }}>
                    Executive Takeaway
                  </span>
                </div>
                <p style={{ fontSize: '0.95rem', color: '#ffffff', lineHeight: '1.55', margin: 0, fontWeight: 500 }}>
                  {insightResult.summary}
                </p>
              </div>

              {/* Detailed Synthesis */}
              <div>
                <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '8px' }}>
                  In-Depth Consumer Behavior Analysis
                </h4>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.65', margin: 0 }}>
                  {insightResult.detailed_synthesis}
                </p>
              </div>

              {/* Key Behavioral Drivers */}
              {insightResult.key_drivers && insightResult.key_drivers.length > 0 && (
                <div>
                  <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    Primary Behavioral Drivers
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
                    {insightResult.key_drivers.map((driver, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '12px 14px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: 'rgba(255, 255, 255, 0.03)',
                          border: '1px solid var(--border-subtle)',
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: '10px',
                        }}
                      >
                        <CheckCircle2 size={16} color="#34d399" style={{ flexShrink: 0, marginTop: '2px' }} />
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: '1.45' }}>
                          {driver}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Supporting Verbatim Evidence Quotes */}
              {insightResult.supporting_evidence && insightResult.supporting_evidence.length > 0 && (
                <div>
                  <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '10px' }}>
                    Corroborating Verbatim Customer Evidence
                  </h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '12px' }}>
                    {insightResult.supporting_evidence.map((ev, idx) => (
                      <div
                        key={idx}
                        style={{
                          padding: '14px 16px',
                          borderRadius: 'var(--radius-md)',
                          backgroundColor: 'rgba(99, 102, 241, 0.04)',
                          border: '1px solid rgba(99, 102, 241, 0.2)',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '8px',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <PlatformBadge platform={ev.source_platform} />
                          {ev.source_url && (
                            <a
                              href={ev.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              style={{ display: 'inline-flex', alignItems: 'center', gap: '3px', fontSize: '0.72rem', color: '#818cf8' }}
                            >
                              Source <ExternalLink size={10} />
                            </a>
                          )}
                        </div>
                        <p style={{ fontSize: '0.85rem', fontStyle: 'italic', color: '#e2e8f0', lineHeight: '1.45', margin: 0 }}>
                          "{ev.verbatim_quote}"
                        </p>
                        <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>
                          Identified friction: {ev.reason_text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Linked Opportunity Areas */}
              {insightResult.linked_opportunities && insightResult.linked_opportunities.length > 0 && (
                <div style={{ paddingTop: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                    <Layers size={15} color="#818cf8" />
                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      Related Opportunity Areas in Taxonomy:
                    </span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {insightResult.linked_opportunities.map((opp) => (
                      <Link
                        key={opp.node_id}
                        href={`/opportunities/${opp.node_id}`}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          padding: '6px 12px',
                          borderRadius: '8px',
                          backgroundColor: 'rgba(255, 255, 255, 0.04)',
                          border: '1px solid var(--border-subtle)',
                          fontSize: '0.8rem',
                          fontWeight: 600,
                          color: '#c7d2fe',
                          transition: 'all var(--transition-fast)',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(99, 102, 241, 0.15)';
                          e.currentTarget.style.borderColor = 'rgba(99, 102, 241, 0.4)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.04)';
                          e.currentTarget.style.borderColor = 'var(--border-subtle)';
                        }}
                      >
                        <span>#{opp.rank} {opp.label}</span>
                        <ChevronRight size={13} />
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};
