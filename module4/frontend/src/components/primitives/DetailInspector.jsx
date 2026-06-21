import React from 'react';

/**
 * DetailInspector
 *
 * The right-hand panel in every master-detail workspace (Investigations,
 * Governance Ledger). Composed from small Row/Section helpers so each
 * page can assemble exactly the fields it needs without duplicating
 * the panel chrome.
 */
export function InspectorPanel({ children }) {
  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        height: '100%',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-6)',
      }}
    >
      {children}
    </div>
  );
}

export function InspectorSection({ title, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {title && (
        <span style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          {title}
        </span>
      )}
      {children}
    </div>
  );
}

export function InspectorRow({ label, value, mono = false }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 'var(--space-4)', alignItems: 'flex-start' }}>
      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', flexShrink: 0 }}>{label}</span>
      <span
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--color-text-primary)',
          fontWeight: 500,
          fontFamily: mono ? 'var(--font-mono)' : 'inherit',
          textAlign: 'right',
          wordBreak: mono ? 'break-all' : 'normal',
        }}
      >
        {value}
      </span>
    </div>
  );
}
