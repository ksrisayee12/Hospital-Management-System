import React, { useEffect, useMemo, useState } from 'react';
import { mockAlerts, mockComplaints, mockHospitals, mockTrustScores } from '../../data/mockData';

/**
 * SearchCommand
 *
 * Lives in the top navigation. Opens on click or Cmd+K / Ctrl+K.
 * Performs real client-side fuzzy filter across all mock datasets,
 * grouped by type. Escape closes it.
 */

function buildSearchIndex() {
  const alerts = mockAlerts.map((a) => ({
    id: a.alert_id,
    type: 'Alert',
    label: a.alert_type.replace(/_/g, ' '),
    sub: a.description,
    tone: 'danger',
  }));
  const complaints = mockComplaints.map((c) => ({
    id: c.complaint_id,
    type: 'Complaint',
    label: c.category.replace(/_/g, ' '),
    sub: c.description,
    tone: 'warning',
  }));
  const doctors = mockTrustScores.map((d) => ({
    id: d.doctor_id,
    type: 'Doctor',
    label: d.name,
    sub: `${d.role} · ${d.hospital} · Trust ${d.score}`,
    tone: 'info',
  }));
  const hospitals = mockHospitals.map((h) => ({
    id: h.hospital_id,
    type: 'Hospital',
    label: h.hospital_name,
    sub: `Risk ${h.risk_score} · ${h.active_alerts} alerts`,
    tone: 'info',
  }));
  return [...alerts, ...complaints, ...doctors, ...hospitals];
}

const ALL_ITEMS = buildSearchIndex();

const TONE_DOT = {
  danger:  'var(--color-danger)',
  warning: 'var(--color-warning)',
  info:    'var(--color-primary)',
  success: 'var(--color-success)',
};

export default function SearchCommand({ placeholder = 'Search alerts, doctors, hospitals…' }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');

  useEffect(() => {
    function handleKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === 'Escape') setOpen(false);
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return ALL_ITEMS.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.sub.toLowerCase().includes(q) ||
        item.type.toLowerCase().includes(q)
    ).slice(0, 12);
  }, [query]);

  // Group results by type
  const grouped = useMemo(() => {
    const groups = {};
    results.forEach((r) => {
      if (!groups[r.type]) groups[r.type] = [];
      groups[r.type].push(r);
    });
    return groups;
  }, [results]);

  function handleClose() {
    setOpen(false);
    setQuery('');
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        aria-label="Open search"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2)',
          background: 'var(--color-background)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-md)',
          padding: '7px 12px',
          color: 'var(--color-text-muted)',
          fontSize: 'var(--text-sm)',
          width: 260,
          cursor: 'pointer',
          transition: 'border-color var(--duration-fast) var(--ease-out)',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-border-strong)'; }}
        onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
      >
        <SearchIcon />
        <span style={{ flex: 1, textAlign: 'left' }}>{placeholder}</span>
        <kbd
          style={{
            fontSize: 'var(--text-xs)',
            background: 'var(--color-card)',
            border: '1px solid var(--color-border)',
            borderRadius: 4,
            padding: '1px 5px',
            color: 'var(--color-text-muted)',
          }}
        >
          ⌘K
        </kbd>
      </button>

      {open && (
        <div
          onClick={handleClose}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.35)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'flex-start',
            paddingTop: '10vh',
            zIndex: 100,
            backdropFilter: 'blur(2px)',
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-label="Search"
            style={{
              width: 580,
              maxWidth: '92vw',
              background: 'var(--color-card)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              overflow: 'hidden',
            }}
          >
            {/* Input row */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
                padding: 'var(--space-4)',
                borderBottom: '1px solid var(--color-border)',
              }}
            >
              <SearchIcon />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={placeholder}
                style={{
                  flex: 1,
                  border: 'none',
                  outline: 'none',
                  fontSize: 'var(--text-md)',
                  color: 'var(--color-text-primary)',
                  background: 'transparent',
                  fontFamily: 'var(--font-body)',
                }}
              />
              <kbd
                style={{
                  fontSize: 'var(--text-xs)',
                  background: 'var(--color-background)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 4,
                  padding: '2px 6px',
                  color: 'var(--color-text-muted)',
                }}
              >
                Esc
              </kbd>
            </div>

            {/* Results */}
            <div style={{ maxHeight: 380, overflowY: 'auto', padding: query ? 'var(--space-2) 0' : 'var(--space-5) var(--space-4)' }}>
              {!query && (
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', textAlign: 'center' }}>
                  Type to search alerts, complaints, doctors, and hospitals.
                </p>
              )}
              {query && results.length === 0 && (
                <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', textAlign: 'center', padding: 'var(--space-5)' }}>
                  No results for &ldquo;{query}&rdquo;
                </p>
              )}
              {Object.entries(grouped).map(([type, items]) => (
                <div key={type}>
                  <div
                    style={{
                      fontSize: 'var(--text-xs)',
                      fontWeight: 700,
                      color: 'var(--color-text-muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.06em',
                      padding: 'var(--space-2) var(--space-4)',
                    }}
                  >
                    {type}s
                  </div>
                  {items.map((item) => (
                    <button
                      key={item.id}
                      onClick={handleClose}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 'var(--space-3)',
                        width: '100%',
                        padding: 'var(--space-2) var(--space-4)',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        textAlign: 'left',
                        borderRadius: 0,
                      }}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-background)'; }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'none'; }}
                    >
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: '50%',
                          background: TONE_DOT[item.tone] || 'var(--color-text-muted)',
                          flexShrink: 0,
                        }}
                      />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: 'var(--text-sm)',
                            fontWeight: 600,
                            color: 'var(--color-text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {item.label}
                        </div>
                        <div
                          style={{
                            fontSize: 'var(--text-xs)',
                            color: 'var(--color-text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                          }}
                        >
                          {item.sub}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}
