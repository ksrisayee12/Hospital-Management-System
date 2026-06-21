import React, { useState, useEffect } from 'react';
import { PageHeader } from '../components/layout';
import { StatusBadge, InspectorPanel, InspectorSection, InspectorRow } from '../components/primitives';
import { api } from '../lib/api';

const EVENT_TONE = {
  CONSENT_APPROVED:           'success',
  CONSENT_REVOKED:            'danger',
  EMERGENCY_OVERRIDE_APPROVED:'purple',
  EMERGENCY_OVERRIDE_REJECTED:'neutral',
  PRESCRIPTION_SIGNED:        'info',
  COMPLAINT_CREATED:          'warning',
  SECURITY_ALERT_RAISED:      'danger',
  TRUST_SCORE_UPDATED:        'info',
};

function truncateHash(hash) {
  if (!hash) return 'N/A';
  if (hash.length <= 16) return hash;
  return `${hash.slice(0, 8)}…${hash.slice(-8)}`;
}

export default function GovernanceLedgerPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    async function fetchLedger() {
      try {
        const res = await api.get('/ledger?limit=100');
        setEvents(res.items || []);
        if (res.items && res.items.length > 0) {
          setSelectedId(res.items[0].id);
        }
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    }
    fetchLedger();
  }, []);

  const selected = events.find((e) => e.id === selectedId);

  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  async function handleVerify() {
    setVerifying(true);
    setVerifyResult(null);
    try {
      const result = await api.get('/ledger/verify');
      setVerifyResult(result);
    } catch (err) {
      alert("Verification failed: " + err);
    } finally {
      setVerifying(false);
    }
  }

  if (loading) return <div className="p-8 text-neutral-400">Loading immutable ledger...</div>;

  return (
    <div>
      <PageHeader
        title="Governance Ledger"
        description="An immutable, hash-chained record of every consent, access, override, and complaint event."
        actions={
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
              Call cryptographic verification
            </span>
            <button
              onClick={handleVerify}
              disabled={verifying}
              style={{
                background: verifying ? 'var(--color-border)' : 'var(--color-primary)',
                color: verifying ? 'var(--color-text-muted)' : '#fff',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '9px 16px',
                fontSize: 'var(--text-sm)',
                fontWeight: 600,
                cursor: verifying ? 'default' : 'pointer',
                transition: 'background var(--duration-fast) var(--ease-out)',
              }}
              onMouseEnter={(e) => { if (!verifying) e.currentTarget.style.background = 'var(--color-primary-hover)'; }}
              onMouseLeave={(e) => { if (!verifying) e.currentTarget.style.background = 'var(--color-primary)'; }}
            >
              {verifying ? 'Verifying chain…' : 'Verify chain integrity'}
            </button>
          </div>
        }
      />

      {verifyResult && (
        <div
          role="status"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
            background: verifyResult.valid ? 'var(--color-success-soft)' : 'var(--color-danger-soft)',
            color: verifyResult.valid ? 'var(--color-success)' : 'var(--color-danger)',
            border: `1px solid ${verifyResult.valid ? 'var(--color-success)' : 'var(--color-danger)'}`,
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3) var(--space-4)',
            marginBottom: 'var(--space-5)',
            fontSize: 'var(--text-sm)',
            fontWeight: 600,
          }}
        >
          <span style={{ fontSize: 18 }}>{verifyResult.valid ? '✓' : '⚠'}</span>
          {verifyResult.valid
            ? `Chain verified — all ${verifyResult.total_events} events are intact. No tampering detected.`
            : `Chain integrity failure at sequence #${verifyResult.broken_at_sequence} — investigate immediately.`}
        </div>
      )}

      <div className="ledger-grid" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 'var(--space-5)' }}>
        <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)', overflowY: 'auto', maxHeight: 680 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {events.length === 0 ? <div className="text-neutral-500 text-sm">No ledger events found</div> : events.map((event, idx) => (
              <LedgerBlock
                key={event.id}
                event={event}
                isLast={idx === events.length - 1}
                selected={event.id === selectedId}
                broken={verifyResult && !verifyResult.valid && event.sequence_number === verifyResult.broken_at_sequence}
                onClick={() => setSelectedId(event.id)}
              />
            ))}
          </div>
        </div>

        {selected && (
          <InspectorPanel>
            <div>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Sequence #{selected.sequence_number}
              </span>
              <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 650, color: 'var(--color-text-primary)', marginTop: 4, lineHeight: 'var(--leading-tight)' }}>
                {selected.event_type.replace(/_/g, ' ')}
              </h2>
              <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 6, lineHeight: 'var(--leading-relaxed)' }}>
                {selected.summary}
              </p>
            </div>

            <InspectorSection title="Event metadata">
              <InspectorRow label="Timestamp" value={new Date(selected.timestamp).toLocaleString()} />
              <InspectorRow
                label="Type"
                value={<StatusBadge tone={EVENT_TONE[selected.event_type] || 'neutral'} label={selected.event_type.replace(/_/g, ' ')} />}
              />
            </InspectorSection>

            <InspectorSection title="Integrity">
              <InspectorRow label="Current hash" value={truncateHash(selected.current_hash)} mono />
              <InspectorRow label="Previous hash" value={truncateHash(selected.previous_hash)} mono />
              <InspectorRow
                label="Verification"
                value={
                  verifyResult && !verifyResult.valid && selected.sequence_number === verifyResult.broken_at_sequence
                    ? <StatusBadge tone="danger" label="Tampered" />
                    : <StatusBadge tone="success" label="Intact" />
                }
              />
            </InspectorSection>

            <InspectorSection title="Hash chain">
              <div style={{ background: 'var(--color-background)', borderRadius: 'var(--radius-md)', padding: 'var(--space-4)', fontSize: 'var(--text-xs)', fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary)', lineHeight: 1.8, wordBreak: 'break-all' }}>
                <div><span style={{ color: 'var(--color-text-muted)' }}>prev </span>{selected.previous_hash || 'GENESIS'}</div>
                <div style={{ color: 'var(--color-primary)', marginTop: 4 }}>
                  <span style={{ color: 'var(--color-text-muted)' }}>curr </span>{selected.current_hash}
                </div>
              </div>
            </InspectorSection>
          </InspectorPanel>
        )}
      </div>

      <style>{`
        @media (max-width: 900px) {
          .ledger-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

function LedgerBlock({ event, isLast, selected, broken, onClick }) {
  const tone = EVENT_TONE[event.event_type] || 'neutral';
  const toneColor = broken ? 'var(--color-danger)' : {
    success: 'var(--color-success)', danger: 'var(--color-danger)', warning: 'var(--color-warning)',
    info: 'var(--color-primary)', purple: 'var(--color-purple)', neutral: 'var(--color-text-muted)',
  }[tone];

  return (
    <div style={{ display: 'flex', gap: 'var(--space-4)' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{ width: 36, height: 36, borderRadius: 'var(--radius-md)', background: broken ? 'var(--color-danger-soft)' : `${toneColor}1A`, border: `1.5px solid ${toneColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: toneColor, fontWeight: 700, fontSize: 'var(--text-xs)' }}>
          {broken ? '!' : event.sequence_number}
        </div>
        {!isLast && <div style={{ width: 2, flex: 1, background: broken ? 'var(--color-danger)' : 'var(--color-border)', minHeight: 32 }} />}
      </div>

      <button
        onClick={onClick}
        style={{ flex: 1, textAlign: 'left', background: selected ? 'var(--color-primary-soft)' : broken ? 'var(--color-danger-soft)' : 'transparent', border: broken ? '1px solid var(--color-danger)' : '1px solid transparent', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)', marginBottom: isLast ? 0 : 'var(--space-2)', cursor: 'pointer', transition: 'background var(--duration-fast) var(--ease-out)' }}
        onMouseEnter={(e) => { if (!selected && !broken) e.currentTarget.style.background = 'var(--color-background)'; }}
        onMouseLeave={(e) => { if (!selected && !broken) e.currentTarget.style.background = 'transparent'; }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 'var(--space-3)' }}>
          <span style={{ fontSize: 'var(--text-base)', fontWeight: 650, color: broken ? 'var(--color-danger)' : 'var(--color-text-primary)' }}>
            {broken ? '⚠ ' : ''}{event.event_type.replace(/_/g, ' ')}
          </span>
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>
            {new Date(event.timestamp).toLocaleString()}
          </span>
        </div>
        <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', margin: '2px 0 4px', lineHeight: 'var(--leading-normal)' }}>
          {event.summary}
        </p>
        <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
          hash {truncateHash(event.current_hash)}
        </span>
      </button>
    </div>
  );
}
