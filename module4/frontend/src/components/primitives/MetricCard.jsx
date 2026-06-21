import React from 'react';

/**
 * MetricCard
 *
 * The atomic KPI unit for Command Center and other analytics screens.
 * Deliberately restrained: one number, one label, one optional delta.
 * No sparkline by default — use TrendCard when a trend visual is the point.
 */

function Delta({ value, invert }) {
  if (value === undefined || value === null) return null;
  const isPositive = invert ? value < 0 : value > 0;
  const isFlat = value === 0;
  const tone = isFlat ? 'var(--color-text-muted)' : isPositive ? 'var(--color-success)' : 'var(--color-danger)';
  const arrow = isFlat ? '—' : value > 0 ? '↑' : '↓';

  return (
    <span style={{ color: tone, fontSize: 'var(--text-sm)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span>{arrow}</span>
      <span>{Math.abs(value)}%</span>
    </span>
  );
}

export default function MetricCard({
  label,
  value,
  unit,
  delta,
  invertDelta = false,
  icon,
  accent = 'var(--color-primary)',
}) {
  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-3)',
        minWidth: 0,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
          {label}
        </span>
        {icon && (
          <span
            style={{
              width: 28,
              height: 28,
              borderRadius: 'var(--radius-md)',
              background: accent + '1A',
              color: accent,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {icon}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span className="tabular" style={{ fontSize: 'var(--text-3xl)', fontWeight: 650, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
          {value}
        </span>
        {unit && (
          <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>{unit}</span>
        )}
      </div>

      {delta !== undefined && <Delta value={delta} invert={invertDelta} />}
    </div>
  );
}
