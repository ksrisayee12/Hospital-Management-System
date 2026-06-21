import React, { useRef, useState, useEffect } from 'react';
import {
  BarChart, Bar, ResponsiveContainer, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, ReferenceLine,
} from 'recharts';
import { PageHeader } from '../components/layout';
import { HospitalCard, AnalyticsPanel, ChartContainer, TrendCard } from '../components/primitives';
import { trendSeries } from '../data/mockData';
import { api } from '../lib/api';

function riskBarColor(score, highlighted) {
  if (highlighted) return 'var(--color-primary)';
  if (score >= 70) return 'var(--color-danger)';
  if (score >= 40) return 'var(--color-warning)';
  return 'var(--color-success)';
}

export default function NetworkAnalyticsPage() {
  const [hospitals, setHospitals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [highlightedId, setHighlightedId] = useState(null);
  const chartRef = useRef(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await api.get('/hospital-risk?limit=50');
        setHospitals(res.items || []);
        setLoading(false);
      } catch (err) {
        console.error(err);
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const comparativeData = hospitals.map((h) => ({
    name: h.hospital_id, // using hospital_id as name if not available
    risk: h.risk_score,
    id: h.hospital_id,
  }));

  function handleCardClick(hospitalId) {
    if (highlightedId === hospitalId) {
      setHighlightedId(null);
      return;
    }
    setHighlightedId(hospitalId);
    setTimeout(() => {
      chartRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 80);
  }

  const highlighted = hospitals.find((h) => h.hospital_id === highlightedId);

  if (loading) return <div className="p-8 text-neutral-400">Loading network analytics...</div>;

  return (
    <div>
      <PageHeader title="Network Analytics" description="Compare risk, trust, and complaint trends across every hospital on the network." />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-5)', marginBottom: 'var(--space-8)' }} className="hospital-cards-grid">
        {hospitals.length === 0 ? <div className="text-neutral-500 text-sm">No hospital data</div> : hospitals.map((h) => (
          <HospitalCard
            key={h.hospital_id}
            name={h.hospital_id}
            riskScore={h.risk_score}
            trustScore={h.avg_trust_score || 100}
            openComplaints={h.open_complaints}
            activeAlerts={h.active_alerts}
            highlighted={h.hospital_id === highlightedId}
            onClick={() => handleCardClick(h.hospital_id)}
          />
        ))}
      </div>

      {highlighted && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', background: 'var(--color-primary-soft)', border: '1px solid var(--color-primary)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3) var(--space-4)', marginBottom: 'var(--space-5)', fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--color-primary)' }}>
          <span>Highlighting:</span>
          <span style={{ color: 'var(--color-text-primary)' }}>{highlighted.hospital_id}</span>
          <span style={{ color: 'var(--color-text-muted)', fontWeight: 400 }}>
            Risk {highlighted.risk_score} · Trust avg {highlighted.avg_trust_score || 100} · {highlighted.active_alerts} alerts
          </span>
          <button onClick={() => setHighlightedId(null)} style={{ marginLeft: 'auto', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-primary)', fontSize: 'var(--text-sm)', fontWeight: 600 }}>Clear ×</button>
        </div>
      )}

      <div ref={chartRef} style={{ marginBottom: 'var(--space-8)' }}>
        <AnalyticsPanel title="Comparative Risk" subtitle={highlightedId ? `Highlighting ${highlighted?.hospital_id} — lower is better.` : 'Risk score by hospital — lower is better. Click a hospital card above to highlight it.'}>
          <ChartContainer height={260}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparativeData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <Tooltip formatter={(value) => [value, 'Risk Score']} contentStyle={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--text-sm)' }} />
                <Bar dataKey="risk" radius={[6, 6, 0, 0]} isAnimationActive={false}>
                  {comparativeData.map((entry) => (
                    <Cell key={entry.name} fill={riskBarColor(entry.risk, entry.id === highlightedId)} opacity={highlightedId && entry.id !== highlightedId ? 0.35 : 1} />
                  ))}
                </Bar>
                <ReferenceLine y={70} stroke="var(--color-danger)" strokeDasharray="4 4" label={{ value: 'High risk threshold', position: 'right', fontSize: 11, fill: 'var(--color-danger)' }} />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </AnalyticsPanel>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 'var(--space-5)' }} className="trends-grid">
        <TrendCard label="Platform risk trend" value={trendSeries.risk[trendSeries.risk.length - 1].value} data={trendSeries.risk} tone="danger" />
        <TrendCard label="Complaint volume" value={3} unit="this week" data={[2, 3, 1, 4, 2, 3, 3].map((v) => ({ value: v }))} tone="warning" />
        <TrendCard label="Average trust score" value={trendSeries.trust[trendSeries.trust.length - 1].value} data={trendSeries.trust} tone="success" />
      </div>

      <style>{`
        @media (max-width: 900px) {
          .hospital-cards-grid, .trends-grid { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}
