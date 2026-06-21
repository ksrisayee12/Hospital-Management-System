import React from 'react';
import StatusBadge from './StatusBadge';

const SEVERITY_TONE = {
  CRITICAL: 'danger',
  HIGH: 'warning',
  MEDIUM: 'info',
  LOW: 'neutral',
};

/**
 * AlertCard
 *
 * Compact card for a single security alert / risk signal. Used on
 * Command Center (Attention Center, Threat Feed) and as a list row
 * in the Investigations left panel.
 */
export default function AlertCard({ title, subtitle, severity = 'MEDIUM', riskScore, timestamp, onClick, selected = false }) {
  const tone = SEVERITY_TONE[severity] || 'neutral';

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        width: '100%',
        textAlign: 'left',
        background: selected ? 'var(--color-primary-soft)' : 'var(--color-card)',
        border: `1px solid ${selected ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        transition: 'border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out)',
        cursor: onClick ? 'pointer' : 'default',
      }}
      onMouseEnter={(e) => { if (onClick && !selected) e.currentTarget.style.boxShadow = 'var(--shadow-sm)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = 'none'; }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
        <StatusBadge tone={tone} label={severity} />
        {riskScore !== undefined && (
          <span className="tabular" style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-text-secondary)' }}>
            Risk {riskScore}
          </span>
        )}
      </div>
      <span style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
        {title}
      </span>
      {subtitle && (
        <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)' }}>{subtitle}</span>
      )}
      {timestamp && (
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{timestamp}</span>
      )}
    </button>
  );
}
