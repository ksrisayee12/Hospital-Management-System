import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

/**
 * Toast primitive
 *
 * Usage:
 *   const toast = useToast();
 *   toast.show('Alert escalated.', 'success');
 *   toast.show('Action failed.', 'danger');
 *
 * Tones: 'success' | 'danger' | 'warning' | 'info'
 * Auto-dismisses after 3.5 s. Keyboard-accessible (Escape removes top toast).
 */

const ToastContext = createContext(null);

let _id = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const show = useCallback((message, tone = 'info') => {
    const id = ++_id;
    setToasts((prev) => [...prev, { id, message, tone }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  useEffect(() => {
    function handleKey(e) {
      if (e.key === 'Escape') {
        setToasts((prev) => prev.slice(0, -1));
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used inside <ToastProvider>');
  return ctx;
}

const TONE_STYLES = {
  success: { bg: 'var(--color-success)', icon: '✓' },
  danger:  { bg: 'var(--color-danger)',  icon: '!' },
  warning: { bg: 'var(--color-warning)', icon: '⚠' },
  info:    { bg: 'var(--color-primary)', icon: 'i' },
};

function ToastStack({ toasts, onDismiss }) {
  if (toasts.length === 0) return null;
  return (
    <div
      role="region"
      aria-live="polite"
      aria-label="Notifications"
      style={{
        position: 'fixed',
        bottom: 'var(--space-6)',
        right: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
        zIndex: 1000,
        pointerEvents: 'none',
      }}
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onDismiss }) {
  const ref = useRef(null);
  const { bg, icon } = TONE_STYLES[toast.tone] || TONE_STYLES.info;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.opacity = '0';
    el.style.transform = 'translateY(8px)';
    requestAnimationFrame(() => {
      el.style.transition = 'opacity var(--duration-base) var(--ease-out), transform var(--duration-base) var(--ease-out)';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    });
  }, []);

  return (
    <div
      ref={ref}
      role="alert"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-3)',
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderLeft: `3px solid ${bg}`,
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        padding: 'var(--space-3) var(--space-4)',
        minWidth: 280,
        maxWidth: 380,
        pointerEvents: 'all',
      }}
    >
      <span
        style={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          background: bg,
          color: '#fff',
          fontSize: 11,
          fontWeight: 700,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {icon}
      </span>
      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-primary)', flex: 1, fontWeight: 500 }}>
        {toast.message}
      </span>
      <button
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss notification"
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--color-text-muted)',
          cursor: 'pointer',
          padding: 0,
          fontSize: 16,
          lineHeight: 1,
          flexShrink: 0,
        }}
      >
        ×
      </button>
    </div>
  );
}
