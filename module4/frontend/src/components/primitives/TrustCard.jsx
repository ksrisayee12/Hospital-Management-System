import React, { useState } from 'react';
import StatusBadge from './StatusBadge';
import Sparkline from './Sparkline';

const RISK_TONE = {
  LOW: 'success',
  MODERATE: 'info',
  HIGH: 'warning',
  CRITICAL: 'danger',
};

// Synthetic per-doctor history — shaped so lower-trust doctors show a declining line
const HISTORY_BY_RISK = {
  CRITICAL: [100, 96, 91, 85, 78, 70, 62].map((v) => ({ value: v })),
  HIGH:     [100, 98, 94, 88, 82, 76, 71].map((v) => ({ value: v })),
  MODERATE: [100, 99, 97, 93, 90, 86, 84].map((v) => ({ value: v })),
  LOW:      [96, 97, 97, 98, 98, 99, 100].map((v) => ({ value: v })),
};

const SPARKLINE_TONE = {
  CRITICAL: 'danger',
  HIGH: 'warning',
  MODERATE: 'info',
  LOW: 'success',
};

/**
 * TrustCard
 *
 * Row used in the Trust Leaderboard.
 * Click to expand an inline trust-score history sparkline.
 * The score bar remains the focal point at a glance.
 */
export default function TrustCard({ name, role, score, riskLevel, hospital, delta, history }) {
  const [expanded, setExpanded] = useState(false);
  const tone = RISK_TONE[riskLevel] || 'neutral';
  const barColor =
    riskLevel === 'CRITICAL' ? 'var(--color-danger)' :
    riskLevel === 'HIGH'     ? 'var(--color-warning)' :
    riskLevel === 'MODERATE' ? 'var(--color-primary)' :
    'var(--color-success)';

  const sparkData = history || HISTORY_BY_RISK[riskLevel] || [];
  const sparkTone = SPARKLINE_TONE[riskLevel] || 'info';

  return (
    <div
      style={{
        borderBottom: '1px solid var(--color-border)',
        transition: 'background var(--duration-fast) var(--ease-out)',
      }}
    >
      <button
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-4)',
          padding: 'var(--space-3) var(--space-2)',
          width: '100%',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
          borderRadius: 'var(--radius-sm)',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-background)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
      >
        <div style={{ flex: '0 0 160px', minWidth: 0 }}>
          <div
            style={{
              fontSize: 'var(--text-base)',
              fontWeight: 600,
              color: 'var(--color-text-primary)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {name}
          </div>
          <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
            {role} · {hospital}
          </div>
        </div>

        <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          <div
            style={{
              flex: 1,
              height: 6,
              borderRadius: 'var(--radius-full)',
              background: 'var(--color-border)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${score}%`,
                background: barColor,
                borderRadius: 'var(--radius-full)',
                transition: 'width var(--duration-slow) var(--ease-out)',
              }}
            />
          </div>
          <span
            className="tabular"
            style={{
              fontSize: 'var(--text-base)',
              fontWeight: 650,
              color: 'var(--color-text-primary)',
              width: 28,
              textAlign: 'right',
            }}
          >
            {score}
          </span>
        </div>

        <StatusBadge tone={tone} label={riskLevel} />

        {delta !== undefined && (
          <span
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 600,
              width: 40,
              textAlign: 'right',
              color:
                delta < 0 ? 'var(--color-danger)' :
                delta > 0 ? 'var(--color-success)' :
                'var(--color-text-muted)',
            }}
          >
            {delta > 0 ? '+' : ''}{delta}
          </span>
        )}

        {/* Expand chevron */}
        <svg
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          style={{
            color: 'var(--color-text-muted)',
            transform: expanded ? 'rotate(180deg)' : 'rotate(0)',
            transition: 'transform var(--duration-fast) var(--ease-out)',
            flexShrink: 0,
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Expanded history section */}
      {expanded && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-4)',
            padding: 'var(--space-3) var(--space-2) var(--space-3) calc(160px + var(--space-4) + var(--space-4))',
            background: 'var(--color-background)',
          }}
        >
          <Sparkline data={sparkData} tone={sparkTone} width={100} height={36} />
          <div>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
              7-day trust trend
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
              Started at {sparkData[0]?.value ?? '—'} · now {sparkData[sparkData.length - 1]?.value ?? '—'}
            </div>
          </div>
          <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>Risk level</div>
            <div
              style={{
                fontSize: 'var(--text-sm)',
                fontWeight: 650,
                color: barColor,
                marginTop: 2,
              }}
            >
              {riskLevel}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
