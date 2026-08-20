'use client';

import React, { useState, useEffect } from 'react';
import api from '@/lib/api';
import { PipelineRunStatus, PipelineStage } from '@/lib/types';
import { LoadingSpinner } from '@/components/shared/LoadingState';
import {
  Cpu,
  Play,
  RotateCcw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  Database,
  Layers,
  PieChart,
  Radio,
} from 'lucide-react';

const PIPELINE_STAGES = [
  { id: 'ingestion', label: '1. Multi-Channel Ingestion', icon: Database, desc: 'Scrape Play Store, App Store, Reddit, YouTube' },
  { id: 'extraction', label: '2. LLM Reason Extraction', icon: Sparkles, desc: 'Gemini causal extractions with prompt bias isolation' },
  { id: 'clustering', label: '3. Semantic Clustering', icon: Layers, desc: 'Agglomerative clustering & LLM cluster labeling' },
  { id: 'scoring', label: '4. Business Scoring', icon: PieChart, desc: 'Wishlist relevance, triangulation & non-monetary actionability' },
  { id: 'full_pipeline', label: 'Full End-to-End Pipeline', icon: Cpu, desc: 'Executes entire discovery engine sequentially' },
];

export default function PipelineEnginePage() {
  const [pipelineRuns, setPipelineRuns] = useState<PipelineRunStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStage, setSelectedStage] = useState<string>('full_pipeline');
  const [triggering, setTriggering] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadStatus = async () => {
    try {
      const res = await api.getPipelineStatus();
      setPipelineRuns(res.runs || []);
    } catch (err) {
      console.error('Failed to load pipeline status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async () => {
    setTriggering(true);
    setNotification(null);
    try {
      const res = await api.triggerPipeline(selectedStage, {});
      setNotification({
        type: 'success',
        message: `Pipeline stage '${selectedStage}' initiated successfully! Task Run ID: ${res.run_id}`,
      });
      loadStatus();
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: err.message || 'Failed to trigger pipeline stage.',
      });
    } finally {
      setTriggering(false);
    }
  };

  const activeRun = pipelineRuns.find((r) => r.status === 'running');

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
              color: '#6366f1',
            }}
          >
            Orchestration & Background Tasks
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
          Pipeline Orchestration Engine
        </h1>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
          Monitor background worker states and trigger automated ingestion, LLM extraction, clustering, and scoring runs.
        </p>
      </div>

      {/* Visual Pipeline Flowchart */}
      <div
        className="glass"
        style={{
          padding: '26px',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '28px',
        }}
      >
        <h3
          style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '1.05rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
            marginBottom: '18px',
          }}
        >
          Continuous Discovery Architecture
        </h3>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '14px',
            position: 'relative',
          }}
        >
          {PIPELINE_STAGES.slice(0, 4).map((stg, i) => {
            const Icon = stg.icon;
            const isCurrentActive = activeRun?.stage === stg.id;

            return (
              <div
                key={stg.id}
                style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: isCurrentActive ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.03)',
                  border: isCurrentActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid var(--border-subtle)',
                  boxShadow: isCurrentActive ? '0 0 20px rgba(99, 102, 241, 0.3)' : 'none',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '8px',
                      backgroundColor: 'rgba(99, 102, 241, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: '#818cf8',
                    }}
                  >
                    <Icon size={16} />
                  </div>
                  {isCurrentActive ? (
                    <span
                      style={{
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        color: '#34d399',
                      }}
                    >
                      RUNNING
                    </span>
                  ) : (
                    <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Layer {i + 1}</span>
                  )}
                </div>
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                    {stg.label}
                  </h4>
                  <p style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', margin: '4px 0 0 0', lineHeight: '1.4' }}>
                    {stg.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Control Console & Trigger Form */}
      <div
        className="glass"
        style={{
          padding: '26px',
          borderRadius: 'var(--radius-xl)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '32px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              Trigger Discovery Pipeline Task
            </h3>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', margin: '2px 0 0 0' }}>
              Launch an asynchronous Celery task to re-run ingestion, extraction, or opportunity scoring.
            </p>
          </div>

          <button
            onClick={handleTrigger}
            disabled={triggering || !!activeRun}
            className="btn-primary"
          >
            <Play size={15} />
            {triggering ? 'Initiating Task...' : activeRun ? 'Pipeline Running...' : 'Execute Selected Stage'}
          </button>
        </div>

        {/* Stage selection radios */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '12px' }}>
          {PIPELINE_STAGES.map((stg) => {
            const isSelected = selectedStage === stg.id;
            return (
              <div
                key={stg.id}
                onClick={() => setSelectedStage(stg.id)}
                style={{
                  padding: '14px 16px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(255, 255, 255, 0.02)',
                  border: isSelected ? '1px solid #6366f1' : '1px solid var(--border-subtle)',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <input
                    type="radio"
                    checked={isSelected}
                    onChange={() => setSelectedStage(stg.id)}
                    style={{ accentColor: '#6366f1' }}
                  />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: isSelected ? '#ffffff' : 'var(--text-secondary)' }}>
                    {stg.label}
                  </span>
                </div>
                <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', margin: 0, paddingLeft: '22px' }}>
                  {stg.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* Notification message */}
        {notification && (
          <div
            style={{
              marginTop: '16px',
              padding: '12px 16px',
              borderRadius: 'var(--radius-md)',
              backgroundColor: notification.type === 'success' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
              color: notification.type === 'success' ? '#34d399' : '#fb7185',
              fontSize: '0.82rem',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
            }}
          >
            {notification.type === 'success' ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
            <span>{notification.message}</span>
          </div>
        )}
      </div>

      {/* Pipeline Run History */}
      <div
        className="glass"
        style={{
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
            Pipeline Execution History
          </h3>
        </div>

        {loading ? (
          <LoadingSpinner text="Retrieving execution history..." />
        ) : pipelineRuns.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No previous pipeline runs recorded in the database.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '14px 20px', textAlign: 'left' }}>Run ID</th>
                <th style={{ padding: '14px 20px', textAlign: 'left' }}>Stage</th>
                <th style={{ padding: '14px 20px', textAlign: 'center' }}>Status</th>
                <th style={{ padding: '14px 20px', textAlign: 'left' }}>Started At</th>
                <th style={{ padding: '14px 20px', textAlign: 'left' }}>Completed At</th>
              </tr>
            </thead>
            <tbody>
              {pipelineRuns.map((run) => {
                const isCompleted = run.status === 'completed';
                const isRunning = run.status === 'running';
                const isFailed = run.status === 'failed';

                return (
                  <tr key={run.run_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '14px 20px', fontFamily: 'monospace', fontSize: '0.8rem', color: '#818cf8' }}>
                      {run.run_id.slice(0, 8)}...
                    </td>
                    <td style={{ padding: '14px 20px', fontWeight: 600, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                      {run.stage.replace('_', ' ')}
                    </td>
                    <td style={{ padding: '14px 20px', textAlign: 'center' }}>
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '5px',
                          padding: '2px 8px',
                          borderRadius: '9999px',
                          fontSize: '0.72rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          backgroundColor: isCompleted
                            ? 'rgba(16, 185, 129, 0.15)'
                            : isRunning
                            ? 'rgba(99, 102, 241, 0.2)'
                            : isFailed
                            ? 'rgba(244, 63, 94, 0.15)'
                            : 'rgba(255, 255, 255, 0.05)',
                          color: isCompleted ? '#34d399' : isRunning ? '#818cf8' : isFailed ? '#fb7185' : 'var(--text-muted)',
                        }}
                      >
                        {run.status}
                      </span>
                    </td>
                    <td style={{ padding: '14px 20px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(run.started_at).toLocaleString()}
                    </td>
                    <td style={{ padding: '14px 20px', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {run.completed_at ? new Date(run.completed_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
