import React from 'react';
import StatusBadge from './StatusBadge';

function riskTone(score) {
  if (score >= 70) return 'danger';
  if (score >= 40) return 'warning';
  return 'success';
}

function riskLabel(score) {
  if (score >= 70) return 'High Risk';
  if (score >= 40) return 'Moderate Risk';
  return 'Low Risk';
}

/**
 * HospitalCard
 *
 * "Each hospital should feel like an entity being monitored" — per
 * brief. Now supports highlighted state (used to sync with the
 * Comparative Risk chart below when the card is clicked).
 */
export default function HospitalCard({ name, riskScore, trustScore, openComplaints, activeAlerts, onClick, highlighted }) {
  const tone = riskTone(riskScore);

  return (
    <button
      onClick={onClick}
      aria-pressed={highlighted}
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        textAlign: 'left',
        background: highlighted ? 'var(--color-primary-soft)' : 'var(--color-card)',
        border: `1.5px solid ${highlighted ? 'var(--color-primary)' : 'var(--color-border)'}`,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-6)',
        width: '100%',
        cursor: 'pointer',
        transition: 'background var(--duration-fast) var(--ease-out), border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out)',
      }}
      onMouseEnter={(e) => {
        if (!highlighted) {
          e.currentTarget.style.boxShadow = 'var(--shadow-md)';
          e.currentTarget.style.borderColor = 'var(--color-border-strong)';
        }
      }}
      onMouseLeave={(e) => {
        if (!highlighted) {
          e.currentTarget.style.boxShadow = 'none';
          e.currentTarget.style.borderColor = 'var(--color-border)';
        }
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <span style={{ fontSize: 'var(--text-md)', fontWeight: 650, color: 'var(--color-text-primary)' }}>
            {name}
          </span>
        </div>
        <StatusBadge tone={tone} label={riskLabel(riskScore)} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-3)' }}>
        <Stat label="Risk score" value={riskScore} />
        <Stat label="Trust avg" value={trustScore} />
        <Stat label="Alerts" value={activeAlerts} />
      </div>

      {openComplaints > 0 && (
        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>
          {openComplaints} open complaint{openComplaints === 1 ? '' : 's'}
        </div>
      )}
    </button>
  );
}

function Stat({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <span className="tabular" style={{ fontSize: 'var(--text-lg)', fontWeight: 650, color: 'var(--color-text-primary)' }}>
        {value}
      </span>
      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>{label}</span>
    </div>
  );
}
