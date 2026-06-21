import React from 'react';
import TopNavigation from './TopNavigation';

/**
 * AppShell
 *
 * Top-level layout: sticky top nav + a max-width, padded content
 * column. No sidebar by design (see brief: "avoid large sidebars").
 */
export default function AppShell({ active, onNavigate, children }) {
  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-background)' }}>
      <TopNavigation active={active} onNavigate={onNavigate} />
      <main
        style={{
          maxWidth: 'var(--content-max-width)',
          margin: '0 auto',
          padding: 'var(--space-8) var(--space-6) var(--space-20)',
        }}
      >
        {children}
      </main>
    </div>
  );
}
