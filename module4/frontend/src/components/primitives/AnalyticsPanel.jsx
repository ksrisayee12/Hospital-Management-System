import React from 'react';

/**
 * AnalyticsPanel
 *
 * Generic card wrapper for any analytical block: a chart, a
 * leaderboard, a breakdown. Provides the consistent title + optional
 * action-link header used across Trust & Risk and Network Analytics.
 */
export function AnalyticsPanel({ title, subtitle, action, children }) {
  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
        <div>
          <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 650, color: 'var(--color-text-primary)' }}>{title}</h3>
          {subtitle && (
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 2 }}>{subtitle}</p>
          )}
        </div>
        {action}
      </div>
      {children}
    </div>
  );
}

/**
 * ChartContainer
 *
 * Fixed-height wrapper so every chart in the platform sits in a
 * predictable box regardless of the charting library's own sizing
 * quirks. Pass children that render a Recharts ResponsiveContainer.
 */
export function ChartContainer({ height = 240, children }) {
  return <div style={{ width: '100%', height }}>{children}</div>;
}
