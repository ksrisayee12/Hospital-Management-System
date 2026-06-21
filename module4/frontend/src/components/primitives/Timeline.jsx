import React from 'react';

/**
 * TimelineItem / TimelineFeed
 *
 * The vertical connected-dot timeline used across Recent Activity
 * (Command Center) and the Governance Ledger. The ledger page leans
 * on this primitive heavily since the brief asks for "visual
 * storytelling" instead of tables.
 */

const TONE_DOT = {
  neutral: 'var(--color-text-muted)',
  info: 'var(--color-primary)',
  success: 'var(--color-success)',
  warning: 'var(--color-warning)',
  danger: 'var(--color-danger)',
  purple: 'var(--color-purple)',
};

export function TimelineItem({ title, description, timestamp, tone = 'neutral', isLast = false, onClick, selected = false }) {
  const dotColor = TONE_DOT[tone] || TONE_DOT.neutral;

  return (
    <div
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      style={{
        display: 'flex',
        gap: 'var(--space-4)',
        cursor: onClick ? 'pointer' : 'default',
        padding: 'var(--space-2) var(--space-2)',
        borderRadius: 'var(--radius-md)',
        background: selected ? 'var(--color-primary-soft)' : 'transparent',
        transition: 'background var(--duration-fast) var(--ease-out)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div
          style={{
            width: 10,
            height: 10,
            borderRadius: '50%',
            background: dotColor,
            marginTop: 4,
            boxShadow: `0 0 0 3px ${dotColor}22`,
          }}
        />
        {!isLast && (
          <div style={{ width: 2, flex: 1, background: 'var(--color-border)', marginTop: 4, minHeight: 28 }} />
        )}
      </div>

      <div style={{ paddingBottom: isLast ? 0 : 'var(--space-4)', minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
            {title}
          </span>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
            {timestamp}
          </span>
        </div>
        {description && (
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 2 }}>
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

export function TimelineFeed({ items, selectedId, onSelect }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {items.map((item, idx) => (
        <TimelineItem
          key={item.id}
          title={item.title}
          description={item.description}
          timestamp={item.timestamp}
          tone={item.tone}
          isLast={idx === items.length - 1}
          selected={item.id === selectedId}
          onClick={onSelect ? () => onSelect(item.id) : undefined}
        />
      ))}
    </div>
  );
}
