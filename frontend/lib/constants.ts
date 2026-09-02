export const APP_CONFIG = {
  name: 'Pulse',
  tagline: 'Consumer Behaviour Discovery Engine',
  team: 'Fashion E-Commerce Product Intelligence',
  targetMetric: 'Consumer Behaviour & Intent Intelligence',
  mission: 'Continuous unstructured customer feedback ingestion, causal extraction, semantic clustering, and qualitative opportunity discovery.',
};

export const PLATFORM_METADATA: Record<string, { label: string; color: string; bg: string; border: string }> = {
  reddit: { label: 'Reddit', color: '#ff5722', bg: 'rgba(255, 87, 34, 0.12)', border: 'rgba(255, 87, 34, 0.3)' },
  playstore: { label: 'Google Play', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.3)' },
  appstore: { label: 'App Store', color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.3)' },
  youtube: { label: 'YouTube', color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.12)', border: 'rgba(244, 63, 94, 0.3)' },
  twitter: { label: 'X / Twitter', color: '#60a5fa', bg: 'rgba(96, 165, 250, 0.12)', border: 'rgba(96, 165, 250, 0.3)' },
  manual_upload: { label: 'Customer Signal', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.12)', border: 'rgba(168, 85, 247, 0.3)' },
  forum: { label: 'Forums & Q&A', color: '#eab308', bg: 'rgba(234, 179, 8, 0.12)', border: 'rgba(234, 179, 8, 0.3)' },
  ecommerce: { label: 'E-Commerce Reviews', color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)', border: 'rgba(249, 115, 22, 0.3)' },
};

export const SIGNAL_TYPE_METADATA: Record<string, { label: string; color: string; bg: string }> = {
  friction: { label: 'Friction', color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.12)' },
  motivation: { label: 'Motivation', color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' },
  behavior: { label: 'Behavior', color: '#6366f1', bg: 'rgba(99, 102, 241, 0.12)' },
  uncertainty: { label: 'Uncertainty', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' },
  comparison: { label: 'Competitor Comparison', color: '#a855f7', bg: 'rgba(168, 85, 247, 0.12)' },
  external_validation: { label: 'Social Proof / Validation', color: '#06b6d4', bg: 'rgba(6, 182, 212, 0.12)' },
};

export const NAV_ITEMS = [
  { label: 'Overview & Insights', href: '/', icon: 'LayoutDashboard', description: 'Executive discovery & ranking' },
  { label: 'Segment Explorer', href: '/segments', icon: 'PieChart', description: 'Category & demographic drill-downs' },
  { label: 'Customer Voice Feed', href: '/corpus', icon: 'Database', description: 'Multi-channel customer reviews' },
];
