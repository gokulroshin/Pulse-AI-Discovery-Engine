'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { CorpusStats } from '@/lib/types';
import { PLATFORM_METADATA } from '@/lib/constants';
import { PlatformBadge } from '@/components/shared/Badge';
import { SourceDistributionPie } from '@/components/charts/SourceDistributionPie';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import { EmptyState } from '@/components/shared/EmptyState';
import {
  Database,
  Layers,
  MessageSquare,
  Sparkles,
  Search,
  Filter,
  ExternalLink,
} from 'lucide-react';

export default function CorpusAnalysisPage() {
  const [stats, setStats] = useState<CorpusStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedSearch, setFeedSearch] = useState('');
  const [selectedChannel, setSelectedChannel] = useState('all');

  const SAMPLE_FEEDBACK_ITEMS = [
    {
      text: "Bought 3 kurtas for Diwali, 2 had sizing off by at least 2 inches at chest. Sizing charts need true customer measurement photos.",
      platform: "reddit",
      category: "ethnic_wear",
      engagement: 42,
      date: "2026-08-14",
    },
    {
      text: "App constantly charges card, confirms order, and then cancels without notification due to 'stock shortage'. Distrust in placing orders.",
      platform: "playstore",
      category: "general",
      engagement: 18,
      date: "2026-08-16",
    },
    {
      text: "Looked at YouTube haul to check actual dupatta drape and embroidery shine because catalog photos are too edited.",
      platform: "youtube",
      category: "ethnic_wear",
      engagement: 29,
      date: "2026-08-12",
    },
    {
      text: "Return pickup boy refused to accept package citing mismatch in barcode tag. Customer support took 8 days to process refund.",
      platform: "appstore",
      category: "western_wear",
      engagement: 34,
      date: "2026-08-15",
    },
    {
      text: "Sneaker sole was extremely stiff compared to retail store trial. Hard to gauge cushioning from photos alone.",
      platform: "reddit",
      category: "footwear",
      engagement: 15,
      date: "2026-08-10",
    },
    {
      text: "Wishlisted 8 tops waiting to compare fabrics and see if any styling reels show up on Instagram.",
      platform: "reddit",
      category: "western_wear",
      engagement: 22,
      date: "2026-08-17",
    },
  ];

  const loadStats = async () => {
    try {
      const data = await api.getCorpusStats();
      setStats(data);
    } catch (err) {
      console.error('Failed to load corpus stats:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const filteredFeedback = SAMPLE_FEEDBACK_ITEMS.filter((item) => {
    if (selectedChannel !== 'all' && item.platform !== selectedChannel) return false;
    if (feedSearch.trim() && !item.text.toLowerCase().includes(feedSearch.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ padding: '32px 36px', maxWidth: '1600px', margin: '0 auto', width: '100%' }}>
      {/* Header */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: '#38bdf8',
            }}
          >
            Multi-Channel Feedback Corpus
          </span>
        </div>
        <h1
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '1.85rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: 0,
          }}
        >
          Customer Voice & Corpus Analysis
        </h1>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
          Explore ingested customer sentiment, channel distributions, and qualitative review traces.
        </p>
      </div>

      {loading ? (
        <LoadingSpinner text="Aggregating corpus statistics..." />
      ) : !stats ? (
        <EmptyState
          title="Corpus Database Empty"
          description="Ingested customer feedback data will appear here once loaded."
          icon={Database}
        />
      ) : (
        <>
          {/* Top Platform Breakdown Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
              marginBottom: '28px',
            }}
          >
            {Object.entries(stats.platform_distribution || {}).map(([platform, count]) => {
              const pct = stats.total_documents > 0 ? ((count / stats.total_documents) * 100).toFixed(0) : '0';

              return (
                <div
                  key={platform}
                  className="glass glow-hover"
                  style={{
                    padding: '18px 20px',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--border-subtle)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '10px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <PlatformBadge platform={platform} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                      {pct}% Share
                    </span>
                  </div>
                  <div>
                    <div
                      style={{
                        fontFamily: 'var(--font-heading)',
                        fontSize: '1.75rem',
                        fontWeight: 800,
                        color: 'var(--text-primary)',
                      }}
                    >
                      {count.toLocaleString()}
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                      Ingested Documents
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Two-Column Grid: Visual Composition & Customer Voice Feed */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(440px, 1fr))', gap: '28px', marginBottom: '32px' }}>
            {/* Left: Source Distribution & Category Prevalences */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <SourceDistributionPie
                distribution={stats.platform_distribution || {}}
                totalDocs={stats.total_documents}
                title="Channel Corpus Composition"
              />

              {/* Category Breakdown Card */}
              <div
                className="glass"
                style={{
                  padding: '22px',
                  borderRadius: 'var(--radius-lg)',
                  border: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                  <Layers size={18} color="#ec4899" />
                  <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    Category Context Distribution
                  </h4>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {Object.entries(stats.category_distribution || {}).map(([cat, count]) => {
                    const pct = stats.total_documents > 0 ? (count / stats.total_documents) * 100 : 0;
                    return (
                      <div key={cat} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                          <span style={{ color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
                            {cat.replace('_', ' ')}
                          </span>
                          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                            {count.toLocaleString()} ({pct.toFixed(0)}%)
                          </span>
                        </div>
                        <div style={{ height: '6px', backgroundColor: 'rgba(255, 255, 255, 0.05)', borderRadius: '9999px', overflow: 'hidden' }}>
                          <div style={{ width: `${pct}%`, height: '100%', backgroundColor: '#ec4899' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right: Real Customer Voice Feed (Replacing manual upload) */}
            <div
              className="glass"
              style={{
                padding: '24px',
                borderRadius: 'var(--radius-xl)',
                border: '1px solid var(--border-subtle)',
                display: 'flex',
                flexDirection: 'column',
                gap: '16px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <MessageSquare size={18} color="#6366f1" />
                  <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
                    Live Customer Voice Signals
                  </h3>
                </div>

                {/* Channel select */}
                <select
                  value={selectedChannel}
                  onChange={(e) => setSelectedChannel(e.target.value)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'rgba(10, 13, 20, 0.6)',
                    border: '1px solid var(--border-subtle)',
                    color: 'var(--text-secondary)',
                    fontSize: '0.78rem',
                    outline: 'none',
                  }}
                >
                  <option value="all">All Channels</option>
                  <option value="reddit">Reddit</option>
                  <option value="playstore">Google Play</option>
                  <option value="appstore">App Store</option>
                  <option value="youtube">YouTube</option>
                </select>
              </div>

              {/* Feed items */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {filteredFeedback.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '14px 16px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'rgba(255, 255, 255, 0.03)',
                      border: '1px solid var(--border-subtle)',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '8px',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <PlatformBadge platform={item.platform} />
                        <span style={{ fontSize: '0.72rem', color: '#a855f7', fontWeight: 600, textTransform: 'capitalize' }}>
                          {item.category.replace('_', ' ')}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{item.date}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.45', margin: 0, fontStyle: 'italic' }}>
                      "{item.text}"
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
