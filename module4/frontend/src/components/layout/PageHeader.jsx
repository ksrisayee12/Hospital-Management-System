import React from 'react';

/**
 * PageHeader
 *
 * Consistent title + description + optional right-aligned actions
 * for every page below Command Center (which uses HeroBanner instead).
 */
export default function PageHeader({ title, description, actions }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 'var(--space-4)',
        marginBottom: 'var(--space-8)',
      }}
    >
      <div>
        <h1 style={{ fontSize: 'var(--text-2xl)', fontWeight: 650, color: 'var(--color-text-primary)', letterSpacing: '-0.01em' }}>
          {title}
        </h1>
        {description && (
          <p style={{ fontSize: 'var(--text-base)', color: 'var(--color-text-secondary)', marginTop: 'var(--space-2)', maxWidth: 640 }}>
            {description}
          </p>
        )}
      </div>
      {actions && <div style={{ display: 'flex', gap: 'var(--space-3)', flexShrink: 0 }}>{actions}</div>}
    </div>
  );
}
