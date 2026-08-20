'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  PieChart,
  Database,
  Sparkles,
  LucideIcon,
  MessageSquare,
} from 'lucide-react';

interface SidebarItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
}

const SIDEBAR_ITEMS: SidebarItem[] = [
  {
    label: 'Overview & Insights',
    href: '/',
    icon: LayoutDashboard,
    badge: 'Rankings',
  },
  {
    label: 'Segment Explorer',
    href: '/segments',
    icon: PieChart,
    badge: 'Cohorts',
  },
  {
    label: 'Customer Voice Feed',
    href: '/corpus',
    icon: Database,
    badge: 'Corpus',
  },
];

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  return (
    <aside
      style={{
        width: '260px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 16px',
        flexShrink: 0,
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        <div style={{ padding: '0 8px' }}>
          <span
            style={{
              fontSize: '0.72rem',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
            }}
          >
            Discovery Navigation
          </span>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {SIDEBAR_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === '/'
                ? pathname === '/' || pathname.startsWith('/opportunities')
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '11px 14px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.35)' : '1px solid transparent',
                  boxShadow: isActive ? '0 0 16px rgba(99, 102, 241, 0.2)' : 'none',
                  fontWeight: isActive ? 600 : 500,
                  fontSize: '0.9rem',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <Icon size={18} color={isActive ? '#818cf8' : 'var(--text-muted)'} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span
                    style={{
                      fontSize: '0.68rem',
                      padding: '2px 7px',
                      borderRadius: 'var(--radius-pill)',
                      backgroundColor: isActive ? 'rgba(99, 102, 241, 0.3)' : 'rgba(255, 255, 255, 0.05)',
                      color: isActive ? '#c7d2fe' : 'var(--text-muted)',
                      fontWeight: 600,
                    }}
                  >
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Target Focus Banner */}
      <div
        style={{
          background: 'rgba(10, 13, 20, 0.65)',
          borderRadius: 'var(--radius-md)',
          padding: '16px 14px',
          border: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Sparkles size={14} color="#f59e0b" />
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            Customer Insights
          </span>
        </div>
        <p style={{ fontSize: '0.73rem', color: 'var(--text-muted)', lineHeight: '1.45', margin: 0 }}>
          Synthesized from Reddit, Play Store, App Store, and YouTube consumer discussions.
        </p>
      </div>
    </aside>
  );
};
