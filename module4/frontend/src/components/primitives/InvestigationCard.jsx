import React from 'react';
import StatusBadge from './StatusBadge';

const TYPE_LABEL = {
  alert: 'Security Alert',
  complaint: 'Complaint',
  emergency: 'Emergency Request',
};

const STATUS_TONE = {
  OPEN: 'danger',
  NEW: 'danger',
  UNDER_REVIEW: 'warning',
  PENDING: 'warning',
  ESCALATED: 'purple',
  RESOLVED: 'success',
  APPROVED: 'success',
  REJECTED: 'neutral',
  DISMISSED: 'neutral',
};

/**
 * InvestigationCard
 *
 * Row in the Investigations master list. Deliberately denser than
 * AlertCard since this is a scanning list, not a hero element —
 * but still respects the same spacing rhythm as everything else.
 */
export default function InvestigationCard({ type, title, entity, status, timestamp, selected, onClick }) {
  const statusTone = STATUS_TONE[status] || 'neutral';

  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
        width: '100%',
        textAlign: 'left',
        padding: 'var(--space-3) var(--space-4)',
        borderRadius: 'var(--radius-md)',
        background: selected ? 'var(--color-primary-soft)' : 'transparent',
        border: 'none',
        borderLeft: selected ? '3px solid var(--color-primary)' : '3px solid transparent',
        cursor: 'pointer',
        transition: 'background var(--duration-fast) var(--ease-out)',
      }}
      onMouseEnter={(e) => { if (!selected) e.currentTarget.style.background = 'var(--color-background)'; }}
      onMouseLeave={(e) => { if (!selected) e.currentTarget.style.background = 'transparent'; }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
          {TYPE_LABEL[type] || type}
        </span>
        <StatusBadge tone={statusTone} label={status} dot={false} />
      </div>
      <span style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--color-text-primary)' }}>
        {title}
      </span>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
        <span>{entity}</span>
        <span>{timestamp}</span>
      </div>
    </button>
  );
}
