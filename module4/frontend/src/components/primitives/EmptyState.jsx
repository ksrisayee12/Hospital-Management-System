import React from 'react';

/**
 * EmptyState
 *
 * Per the writing guidance: "an empty screen is an invitation to
 * act," not an apology. Always pair with a concrete next step where
 * one exists.
 */
export default function EmptyState({ icon, title, description, actionLabel, onAction }) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        gap: 'var(--space-3)',
        padding: 'var(--space-16) var(--space-8)',
        color: 'var(--color-text-secondary)',
      }}
    >
      {icon && (
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 'var(--radius-lg)',
            background: 'var(--color-primary-soft)',
            color: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {icon}
        </div>
      )}
      <span style={{ fontSize: 'var(--text-md)', fontWeight: 650, color: 'var(--color-text-primary)' }}>
        {title}
      </span>
      {description && (
        <p style={{ fontSize: 'var(--text-sm)', maxWidth: 360, margin: 0 }}>{description}</p>
      )}
      {actionLabel && (
        <button
          onClick={onAction}
          style={{
            marginTop: 'var(--space-2)',
            background: 'var(--color-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '8px 16px',
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
          }}
        >
          {actionLabel}
        </button>
      )}
    </div>
  );
}
