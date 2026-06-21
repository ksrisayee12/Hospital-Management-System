import React from 'react';

/**
 * StatusBadge
 *
 * Small pill used everywhere a state needs a name: alert status,
 * complaint status, override status, risk tier. Tone maps to the
 * brief's semantic colors — never pass a raw hex through this
 * component, add a new tone instead.
 */

const TONE_STYLES = {
  neutral: { bg: 'var(--color-border)', fg: 'var(--color-text-secondary)' },
  info: { bg: 'var(--color-primary-soft)', fg: 'var(--color-primary)' },
  success: { bg: 'var(--color-success-soft)', fg: 'var(--color-success)' },
  warning: { bg: 'var(--color-warning-soft)', fg: 'var(--color-warning)' },
  danger: { bg: 'var(--color-danger-soft)', fg: 'var(--color-danger)' },
  purple: { bg: 'var(--color-purple-soft)', fg: 'var(--color-purple)' },
};

export default function StatusBadge({ tone = 'neutral', label, dot = true }) {
  const t = TONE_STYLES[tone] || TONE_STYLES.neutral;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        padding: '4px 10px',
        borderRadius: 'var(--radius-full)',
        background: t.bg,
        color: t.fg,
        fontSize: 'var(--text-xs)',
        fontWeight: 600,
        letterSpacing: '0.01em',
        whiteSpace: 'nowrap',
      }}
    >
      {dot && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            background: 'currentColor',
            flexShrink: 0,
          }}
        />
      )}
      {label}
    </span>
  );
}
