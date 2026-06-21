import React from 'react';
import { ResponsiveContainer, AreaChart, Area, YAxis } from 'recharts';

/**
 * TrendCard
 *
 * Like MetricCard, but the point IS the trend over time, not just the
 * current value. Use sparingly — per the brief, avoid excessive charts.
 * Tone drives both the line color and the soft fill beneath it.
 */

const TONE_COLOR = {
  primary: 'var(--color-primary)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  danger: 'var(--color-danger)',
  purple: 'var(--color-purple)',
};

export default function TrendCard({ label, value, unit, data, dataKey = 'value', tone = 'primary' }) {
  const color = TONE_COLOR[tone] || TONE_COLOR.primary;
  const gradientId = `trend-gradient-${label?.replace(/\s+/g, '-').toLowerCase()}`;

  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
          {label}
        </span>
        <span className="tabular" style={{ fontSize: 'var(--text-xl)', fontWeight: 650, color: 'var(--color-text-primary)' }}>
          {value}
          {unit && <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', fontWeight: 500 }}> {unit}</span>}
        </span>
      </div>

      <div style={{ height: 56, marginTop: 'var(--space-2)' }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.22} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <YAxis hide domain={['auto', 'auto']} />
            <Area
              type="monotone"
              dataKey={dataKey}
              stroke={color}
              strokeWidth={2}
              fill={`url(#${gradientId})`}
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
