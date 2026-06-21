import React, { useState, useEffect } from 'react';
import { HeroBanner } from '../components/layout';
import { MetricCard, AlertCard, TimelineFeed, AnalyticsPanel, EmptyState } from '../components/primitives';
import { api } from '../lib/api';

const ICONS = {
  shield: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2 4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4Z" />
    </svg>
  ),
  pulse: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 12h4l3 8 4-16 3 8h4" />
    </svg>
  ),
  bell: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M18 8a6 6 0 1 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </svg>
  ),
  folder: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7Z" />
    </svg>
  ),
};

export default function CommandCenterPage() {
  const [data, setData] = useState({
    alerts: [],
    complaints: [],
    overrides: [],
    ledger: [],
    trustScores: [],
    health: 'Checking...',
    loading: true
  });

  useEffect(() => {
    async function fetchData() {
      try {
        const [alertsRes, compRes, overrideRes, ledgerRes, trustRes, healthRes] = await Promise.all([
          api.get('/alerts?limit=100'),
          api.get('/complaints?limit=100'),
          api.get('/emergency?limit=100'),
          api.get('/ledger?limit=10'),
          api.get('/trust-scores?limit=100'),
          fetch(import.meta.env.VITE_API_BASE_URL.replace('/api/v1', '/health')).then(r => r.json()).catch(() => ({ status: 'down' }))
        ]);
        
        setData({
          alerts: alertsRes.items || [],
          complaints: compRes.items || [],
          overrides: overrideRes.items || [],
          ledger: ledgerRes.items || [],
          trustScores: trustRes.items || [],
          health: healthRes.status === 'ok' ? 'All systems monitored' : 'Database connection degraded',
          loading: false
        });
      } catch (e) {
        console.error(e);
        setData(prev => ({ ...prev, loading: false, health: 'API Error' }));
      }
    }
    fetchData();
  }, []);

  if (data.loading) {
    return <div className="p-8 text-neutral-400">Loading Command Center...</div>;
  }

  const criticalAlerts = data.alerts.filter((a) => a.risk_score >= 70 && a.status !== 'DISMISSED');
  const pendingComplaints = data.complaints.filter((c) => c.status === 'OPEN' || c.status === 'UNDER_REVIEW');
  const emergencyRequests = data.overrides.filter((o) => o.status === 'PENDING');
  
  const avgTrustScore = data.trustScores.length > 0 
    ? Math.round(data.trustScores.reduce((acc, s) => acc + s.score, 0) / data.trustScores.length)
    : 100;

  // Format ledger events for TimelineFeed
  const recentActivity = data.ledger.map(l => ({
    id: l.id,
    title: l.event_type.replace(/_/g, ' '),
    timestamp: l.timestamp,
    status: 'success'
  }));

  return (
    <div>
      <HeroBanner
        title="Healthcare Governance Center"
        description="Monitoring trust, security, compliance, and patient data access across the network."
        systemStatus={data.health}
      />

      {/* KPI Metrics */}
      <div className="kpi-grid" style={{ marginBottom: 'var(--space-8)' }}>
        <MetricCard
          label="Platform Risk Score"
          value={Math.round(criticalAlerts.reduce((a, b) => a + b.risk_score, 0) / (criticalAlerts.length || 1))}
          delta={0}
          invertDelta
          icon={ICONS.shield}
          accent="var(--color-danger)"
        />
        <MetricCard
          label="Avg Trust Score"
          value={avgTrustScore}
          delta={0}
          icon={ICONS.pulse}
          accent="var(--color-success)"
        />
        <MetricCard
          label="Open Alerts"
          value={criticalAlerts.length}
          delta={0}
          invertDelta
          icon={ICONS.bell}
          accent="var(--color-warning)"
        />
        <MetricCard
          label="Active Cases"
          value={pendingComplaints.length + emergencyRequests.length}
          delta={0}
          invertDelta
          icon={ICONS.folder}
          accent="var(--color-primary)"
        />
      </div>

      {/* Attention Center */}
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <SectionLabel title="Attention Center" subtitle="Items that need a decision today." />
        <div className="attention-grid">
          <AttentionGroup label="Critical alerts" count={criticalAlerts.length} tone="danger">
            {criticalAlerts.length === 0 ? (
              <EmptyState title="No critical alerts" description="Nothing above risk threshold right now." />
            ) : (
              criticalAlerts.slice(0, 5).map((a) => (
                <AlertCard
                  key={a.id}
                  title={a.description}
                  severity={a.risk_score >= 80 ? 'CRITICAL' : 'HIGH'}
                  riskScore={a.risk_score}
                  timestamp={new Date(a.created_at).toLocaleString()}
                />
              ))
            )}
          </AttentionGroup>

          <AttentionGroup label="Pending complaints" count={pendingComplaints.length} tone="warning">
            {pendingComplaints.length === 0 ? (
              <EmptyState title="No pending complaints" description="Inbox zero." />
            ) : (
              pendingComplaints.slice(0, 5).map((c) => (
                <AlertCard
                  key={c.id}
                  title={c.description}
                  subtitle={c.category?.replace(/_/g, ' ') || 'Unknown'}
                  severity={c.priority}
                  timestamp={new Date(c.created_at).toLocaleString()}
                />
              ))
            )}
          </AttentionGroup>

          <AttentionGroup label="Emergency requests" count={emergencyRequests.length} tone="purple">
            {emergencyRequests.length === 0 ? (
              <EmptyState title="No pending requests" description="All emergency overrides have been reviewed." />
            ) : (
              emergencyRequests.slice(0, 5).map((o) => (
                <AlertCard
                  key={o.id}
                  title={o.reason}
                  subtitle={`${o.doctor_id} → Patient ${o.patient_id}`}
                  severity={o.urgency || 'HIGH'}
                  timestamp={new Date(o.requested_at).toLocaleString()}
                />
              ))
            )}
          </AttentionGroup>
        </div>
      </div>

      {/* Recent Activity + Threat Feed */}
      <div className="activity-grid">
        <AnalyticsPanel title="Recent Activity" subtitle="A live timeline across all hospitals.">
          {recentActivity.length === 0 ? <EmptyState title="No ledger events" /> : <TimelineFeed items={recentActivity} />}
        </AnalyticsPanel>

        <AnalyticsPanel title="Threat Feed" subtitle="Live security incidents.">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {data.alerts.length === 0 ? <EmptyState title="No security alerts" /> : data.alerts.slice(0, 4).map((a) => (
              <AlertCard
                key={a.id}
                title={a.alert_type?.replace(/_/g, ' ') || 'Unknown'}
                subtitle={a.description}
                severity={a.risk_score >= 80 ? 'CRITICAL' : a.risk_score >= 60 ? 'HIGH' : 'MEDIUM'}
                riskScore={a.risk_score}
              />
            ))}
          </div>
        </AnalyticsPanel>
      </div>

      {/* Responsive CSS */}
      <style>{`
        .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: var(--space-5); }
        .attention-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-4); }
        .activity-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--space-5); }
        @media (max-width: 1024px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 768px) {
          .kpi-grid, .attention-grid, .activity-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

function SectionLabel({ title, subtitle }) {
  return (
    <div style={{ marginBottom: 'var(--space-4)' }}>
      <h2 style={{ fontSize: 'var(--text-lg)', fontWeight: 650, color: 'var(--color-text-primary)' }}>{title}</h2>
      {subtitle && <p style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', marginTop: 2 }}>{subtitle}</p>}
    </div>
  );
}

function AttentionGroup({ label, count, tone, children }) {
  const toneColor = { danger: 'var(--color-danger)', warning: 'var(--color-warning)', purple: 'var(--color-purple)' }[tone];
  return (
    <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: 'var(--text-sm)', fontWeight: 650, color: 'var(--color-text-primary)' }}>{label}</span>
        <span className="tabular" style={{ fontSize: 'var(--text-xs)', fontWeight: 700, color: toneColor, background: `${toneColor}1A`, borderRadius: 'var(--radius-full)', padding: '2px 8px' }}>{count}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {children}
      </div>
    </div>
  );
}
