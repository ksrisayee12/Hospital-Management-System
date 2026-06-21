import React from 'react';

/**
 * HeroBanner
 *
 * Command Center only. A calm, confident statement of what this
 * platform watches over — not a marketing hero, just an oriented
 * opening line plus a live system-status signal.
 */
export default function HeroBanner({ title, description, systemStatus = 'All systems monitored' }) {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #0F172A 0%, #1E293B 60%, #1E3A8A 100%)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-10) var(--space-8)',
        marginBottom: 'var(--space-8)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          alignSelf: 'flex-start',
          background: 'rgba(255,255,255,0.08)',
          border: '1px solid rgba(255,255,255,0.14)',
          borderRadius: 'var(--radius-full)',
          padding: '5px 12px',
          fontSize: 'var(--text-xs)',
          fontWeight: 600,
          color: '#A7F3D0',
        }}
      >
        <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#34D399' }} />
        {systemStatus}
      </div>

      <h1 style={{ fontSize: 'var(--text-3xl)', fontWeight: 650, color: '#FFFFFF', letterSpacing: '-0.02em', maxWidth: 640 }}>
        {title}
      </h1>
      <p style={{ fontSize: 'var(--text-md)', color: 'rgba(255,255,255,0.72)', maxWidth: 560, lineHeight: 'var(--leading-relaxed)' }}>
        {description}
      </p>
    </div>
  );
}
