import React, { useMemo, useState, useEffect } from 'react';
import { PageHeader } from '../components/layout';
import {
  InvestigationCard,
  StatusBadge,
  InspectorPanel,
  InspectorSection,
  InspectorRow,
  TimelineFeed,
  EmptyState,
  ConfirmDialog,
  useToast,
} from '../components/primitives';
import { api } from '../lib/api';

const FILTERS = ['All', 'Alerts', 'Complaints', 'Emergency'];

function statusTone(status) {
  const map = {
    OPEN: 'danger', NEW: 'danger', PENDING: 'warning', UNDER_REVIEW: 'warning',
    ESCALATED: 'purple', RESOLVED: 'success', APPROVED: 'success',
    REJECTED: 'neutral', DISMISSED: 'neutral',
  };
  return map[status] || 'neutral';
}

function buildList(alerts, complaints, overrides) {
  const a = alerts.map((x) => ({
    id: `alert-${x.id}`, type: 'alert',
    title: x.description, entity: x.user_id,
    status: x.status, timestamp: new Date(x.created_at).toLocaleDateString(), raw: x,
  }));
  const c = complaints.map((x) => ({
    id: `complaint-${x.id}`, type: 'complaint',
    title: x.description, entity: x.doctor_id,
    status: x.status, timestamp: new Date(x.created_at).toLocaleDateString(), raw: x,
  }));
  const e = overrides.map((x) => ({
    id: `emergency-${x.id}`, type: 'emergency',
    title: x.reason, entity: `${x.doctor_id} → ${x.patient_id}`,
    status: x.status, timestamp: new Date(x.requested_at).toLocaleDateString(), raw: x,
  }));
  return [...a, ...c, ...e].sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));
}

export default function InvestigationsPage() {
  const [alerts, setAlerts] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [overrides, setOverrides] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [a, c, e] = await Promise.all([
          api.get('/alerts?limit=100'),
          api.get('/complaints?limit=100'),
          api.get('/emergency?limit=100'),
        ]);
        setAlerts(a.items || []);
        setComplaints(c.items || []);
        setOverrides(e.items || []);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const allItems = useMemo(() => buildList(alerts, complaints, overrides), [alerts, complaints, overrides]);

  const [filter, setFilter] = useState('All');
  const [selectedId, setSelectedId] = useState(null);
  const [mobileShowDetail, setMobileShowDetail] = useState(false);

  useEffect(() => {
    if (!selectedId && allItems.length > 0) {
      setSelectedId(allItems[0].id);
    }
  }, [allItems, selectedId]);

  const [confirm, setConfirm] = useState(null); 
  const toast = useToast();

  const filtered = allItems.filter((item) => {
    if (filter === 'All') return true;
    if (filter === 'Alerts') return item.type === 'alert';
    if (filter === 'Complaints') return item.type === 'complaint';
    if (filter === 'Emergency') return item.type === 'emergency';
    return true;
  });

  const selected = allItems.find((i) => i.id === selectedId);

  function handleSelect(id) {
    setSelectedId(id);
    setMobileShowDetail(true);
  }

  async function applyAction(action) {
    if (!selected) return;

    const type = selected.type;
    const rawId = selected.raw.id;

    const nextStatus = {
      Escalate: 'ESCALATED',
      'Mark resolved': 'RESOLVED',
      Dismiss: 'DISMISSED',
      Approve: 'APPROVED',
      Reject: 'REJECTED',
    }[action];

    try {
      if (type === 'alert') {
        const updated = await api.patch(`/alerts/${rawId}`, { status: nextStatus });
        setAlerts((prev) => prev.map((a) => a.id === rawId ? updated : a));
      } else if (type === 'complaint') {
        const updated = await api.patch(`/complaints/${rawId}`, { status: nextStatus });
        setComplaints((prev) => prev.map((c) => c.id === rawId ? updated : c));
      } else if (type === 'emergency') {
        const actionPath = action === 'Approve' ? 'approve' : 'reject';
        const updated = await api.post(`/emergency/${rawId}/${actionPath}`);
        setOverrides((prev) => prev.map((o) => o.id === rawId ? updated : o));
      }

      const toastTone = nextStatus === 'RESOLVED' || nextStatus === 'APPROVED' ? 'success'
        : nextStatus === 'ESCALATED' ? 'warning'
        : 'info';

      toast.show(`${action} successful.`, toastTone);
    } catch (err) {
      toast.show(`Failed: ${err}`, 'danger');
    }
    setConfirm(null);
  }

  function requestAction(action) {
    const toneMap = { Escalate: 'warning', 'Mark resolved': 'success', Dismiss: 'danger', Approve: 'success', Reject: 'danger' };
    setConfirm({ action, tone: toneMap[action] || 'danger' });
  }

  function getActions(item) {
    if (!item) return [];
    const { type, status } = item;
    if (type === 'emergency') {
      if (status === 'PENDING') return [
        { label: 'Approve', tone: 'success' },
        { label: 'Reject', tone: 'danger' },
      ];
    }
    if (status === 'RESOLVED' || status === 'DISMISSED' || status === 'APPROVED' || status === 'REJECTED') return [];
    return [
      { label: 'Escalate', tone: 'warning' },
      { label: 'Mark resolved', tone: 'success' },
      { label: 'Dismiss', tone: 'neutral' },
    ];
  }

  const actions = getActions(selected);

  if (loading) return <div className="p-8 text-neutral-400">Loading investigations...</div>;

  return (
    <div>
      <PageHeader title="Investigations" description="Review and resolve alerts, complaints, and emergency access requests." />

      <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-5)', flexWrap: 'wrap' }}>
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            style={{
              background: filter === f ? 'var(--color-primary)' : 'var(--color-card)',
              color: filter === f ? '#fff' : 'var(--color-text-secondary)',
              border: `1px solid ${filter === f ? 'var(--color-primary)' : 'var(--color-border)'}`,
              borderRadius: 'var(--radius-full)',
              padding: '6px 14px',
              fontSize: 'var(--text-sm)',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out)',
            }}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="investigations-grid" style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 'var(--space-5)', minHeight: 600 }}>
        <div className={mobileShowDetail ? 'investigations-list-hidden' : ''} style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflowY: 'auto', padding: 'var(--space-2)', maxHeight: 680 }}>
          {filtered.length === 0 ? (
            <EmptyState title="Nothing here" description="No items match this filter." />
          ) : (
            filtered.map((item) => (
              <InvestigationCard key={item.id} type={item.type} title={item.title} entity={item.entity} status={item.status} timestamp={item.timestamp} selected={item.id === selectedId} onClick={() => handleSelect(item.id)} />
            ))
          )}
        </div>

        {selected ? (
          <InspectorPanel>
            <button className="mobile-back-btn" onClick={() => setMobileShowDetail(false)} style={{ display: 'none', alignItems: 'center', gap: 'var(--space-2)', background: 'none', border: 'none', fontSize: 'var(--text-sm)', color: 'var(--color-primary)', fontWeight: 600, marginBottom: 'var(--space-4)', cursor: 'pointer', padding: 0 }}>← Back to list</button>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  {selected.type === 'alert' ? 'Security Alert' : selected.type === 'complaint' ? 'Complaint' : 'Emergency Request'}
                </span>
                <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 650, color: 'var(--color-text-primary)', marginTop: 4, lineHeight: 'var(--leading-tight)' }}>{selected.title}</h2>
              </div>
              <StatusBadge tone={statusTone(selected.status)} label={selected.status} />
            </div>

            <InspectorSection title="Details">
              <InspectorRow label="Entity" value={selected.entity} />
              <InspectorRow label="Reported" value={selected.timestamp} />
              {selected.type === 'alert' && <InspectorRow label="Risk score" value={selected.raw.risk_score} />}
              {selected.type === 'alert' && <InspectorRow label="Alert type" value={selected.raw.alert_type?.replace(/_/g, ' ') || 'Unknown'} />}
              {selected.type === 'complaint' && <InspectorRow label="Category" value={selected.raw.category?.replace(/_/g, ' ') || 'Unknown'} />}
              {selected.type === 'complaint' && <InspectorRow label="Priority" value={selected.raw.priority} />}
              {selected.type === 'emergency' && <InspectorRow label="Urgency" value={selected.raw.urgency} />}
              <InspectorRow label="Hospital" value={selected.raw.hospital_id} />
            </InspectorSection>

            {actions.length > 0 && (
              <InspectorSection title="Resolution actions">
                <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
                  {actions.map(({ label, tone }) => (
                    <ActionButton key={label} label={label} tone={tone} onClick={() => requestAction(label)} />
                  ))}
                </div>
              </InspectorSection>
            )}

            {actions.length === 0 && (
              <div style={{ padding: 'var(--space-3) var(--space-4)', background: 'var(--color-background)', borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                This item is already closed — no further actions available.
              </div>
            )}
          </InspectorPanel>
        ) : (
          <InspectorPanel><EmptyState title="Select an item" description="Choose an alert, complaint, or emergency request from the list to inspect it." /></InspectorPanel>
        )}
      </div>

      {confirm && (
        <ConfirmDialog
          open title={`${confirm.action}?`}
          description="Are you sure you want to perform this action?"
          confirmLabel={confirm.action} confirmTone={confirm.tone}
          onConfirm={() => applyAction(confirm.action)} onCancel={() => setConfirm(null)}
        />
      )}

      <style>{`
        @media (max-width: 768px) {
          .investigations-grid { grid-template-columns: 1fr !important; }
          .mobile-back-btn { display: flex !important; }
        }
      `}</style>
    </div>
  );
}

function ActionButton({ label, tone, onClick }) {
  const toneColor = { danger: 'var(--color-danger)', success: 'var(--color-success)', warning: 'var(--color-warning)', neutral: 'var(--color-text-secondary)' }[tone];
  return (
    <button onClick={onClick} style={{ background: 'var(--color-card)', border: `1px solid ${tone === 'neutral' ? 'var(--color-border)' : toneColor}`, color: toneColor, borderRadius: 'var(--radius-md)', padding: '8px 14px', fontSize: 'var(--text-sm)', fontWeight: 600, cursor: 'pointer', transition: 'background var(--duration-fast) var(--ease-out)' }}>
      {label}
    </button>
  );
}
