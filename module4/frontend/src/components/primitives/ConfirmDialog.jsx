import React, { useEffect, useRef } from 'react';

/**
 * ConfirmDialog
 *
 * Lightweight confirm step before destructive resolution actions.
 * Styled consistently with SearchCommand's modal treatment.
 *
 * Props:
 *   open        — boolean
 *   title       — string
 *   description — string
 *   confirmLabel  — string (e.g. "Escalate")
 *   confirmTone   — 'danger' | 'success' | 'warning'
 *   onConfirm   — () => void
 *   onCancel    — () => void
 */
export default function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = 'Confirm',
  confirmTone = 'danger',
  onConfirm,
  onCancel,
}) {
  const confirmRef = useRef(null);

  useEffect(() => {
    if (open) {
      // Focus the cancel button by default — safer default per UX convention
      confirmRef.current?.focus();
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function handleKey(e) {
      if (e.key === 'Escape') onCancel?.();
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [open, onCancel]);

  if (!open) return null;

  const toneColor = {
    danger:  'var(--color-danger)',
    success: 'var(--color-success)',
    warning: 'var(--color-warning)',
  }[confirmTone] || 'var(--color-primary)';

  return (
    <div
      onClick={onCancel}
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-dialog-title"
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(15, 23, 42, 0.40)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 200,
        backdropFilter: 'blur(2px)',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-card)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-lg)',
          boxShadow: 'var(--shadow-lg)',
          padding: 'var(--space-6)',
          width: 400,
          maxWidth: '90vw',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <h2
            id="confirm-dialog-title"
            style={{ fontSize: 'var(--text-md)', fontWeight: 650, color: 'var(--color-text-primary)' }}
          >
            {title}
          </h2>
          {description && (
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', lineHeight: 'var(--leading-relaxed)' }}>
              {description}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'flex-end' }}>
          <button
            onClick={onCancel}
            style={{
              background: 'var(--color-card)',
              border: '1px solid var(--color-border)',
              color: 'var(--color-text-secondary)',
              borderRadius: 'var(--radius-md)',
              padding: '8px 16px',
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => { e.target.style.background = 'var(--color-background)'; }}
            onMouseLeave={(e) => { e.target.style.background = 'var(--color-card)'; }}
          >
            Cancel
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            style={{
              background: toneColor,
              border: 'none',
              color: '#fff',
              borderRadius: 'var(--radius-md)',
              padding: '8px 16px',
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => { e.target.style.opacity = '0.88'; }}
            onMouseLeave={(e) => { e.target.style.opacity = '1'; }}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
