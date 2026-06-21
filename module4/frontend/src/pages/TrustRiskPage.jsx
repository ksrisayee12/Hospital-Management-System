import React, { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import { PageHeader } from '../components/layout';
import { TrustCard, AnalyticsPanel, ChartContainer } from '../components/primitives';
import { trendSeries } from '../data/mockData';
import { api } from '../lib/api';

const RISK_COLORS = {
  LOW:      '#10B981',
  MODERATE: '#2563EB',
  HIGH:     '#F59E0B',
  CRITICAL: '#EF4444',
};

function buildDistribution(scores) {
  const counts = { LOW: 0, MODERATE: 0, HIGH: 0, CRITICAL: 0 };
  scores.forEach((s) => { counts[s.risk_level] = (counts[s.risk_level] || 0) + 1; });
  return Object.entries(counts)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));
}

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-3) var(--space-4)',
        fontSize: 'var(--text-sm)',
        boxShadow: 'var(--shadow-md)',
      }}
    >
      <span style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{payload[0].value}</span>
      <span style={{ color: 'var(--color-text-muted)', marginLeft: 4 }}>{payload[0].name}</span>
    </div>
  );
};

export default function TrustRiskPage() {
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await api.get('/trust-scores?limit=50');
        setScores(res.items || []);
        setLoading(false);
      } catch (e) {
        console.error(e);
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const sortedByRisk = [...scores].sort((a, b) => a.score - b.score);
  const distribution = buildDistribution(scores);
  const trendData    = trendSeries.trust.map((d, i) => ({ day: `D${i + 1}`, trust: d.value }));

  if (loading) return <div className="p-8 text-neutral-400">Loading trust scores...</div>;

  return (
    <div>
      <PageHeader
        title="Trust & Risk"
        description="Track how doctor and hospital trust evolves, and surface behavioral patterns before they become incidents."
      />

      <div className="trust-top-grid" style={{ marginBottom: 'var(--space-5)' }}>
        <AnalyticsPanel title="Trust Leaderboard" subtitle="Lowest trust scores first. Click a row to see their 7-day trend.">
          <div>
            {sortedByRisk.length === 0 ? <div className="text-neutral-500 text-sm">No trust scores available</div> : sortedByRisk.map((doc) => (
              <TrustCard
                key={doc.user_id}
                name={doc.user_id}
                role="Doctor"
                hospital={doc.hospital_id || 'Unknown'}
                score={doc.score}
                riskLevel={doc.risk_level}
                delta={doc.score === 100 ? 0 : -5} // Mocking delta for visual
              />
            ))}
          </div>
        </AnalyticsPanel>

        <AnalyticsPanel title="Trust Distribution" subtitle="Doctors grouped by risk tier.">
          <ChartContainer height={220}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distribution} dataKey="value" nameKey="name"
                  innerRadius={56} outerRadius={84} paddingAngle={3} isAnimationActive={false}
                >
                  {distribution.map((entry) => <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />)}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </ChartContainer>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
            {distribution.map((entry) => (
              <div key={entry.name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 8, height: 8, borderRadius: '50%', background: RISK_COLORS[entry.name] }} />
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-secondary)' }}>{entry.name} ({entry.value})</span>
              </div>
            ))}
          </div>
        </AnalyticsPanel>
      </div>

      <div className="trust-bottom-grid">
        <AnalyticsPanel title="Risk Analysis" subtitle="Where risk is concentrated right now.">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <RiskRow label="Excessive record viewing"    value={42} tone="warning" />
            <RiskRow label="Emergency override misuse"   value={28} tone="danger" />
            <RiskRow label="Abnormal downloads"          value={18} tone="warning" />
            <RiskRow label="Repeated off-hours access"   value={12} tone="info" />
          </div>
        </AnalyticsPanel>

        <AnalyticsPanel title="Historical Trends" subtitle="Platform-wide average trust score, last 7 days.">
          <ChartContainer height={220}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="day" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} domain={[70, 100]} />
                <Tooltip content={<CustomTooltip />} />
                <Line type="monotone" dataKey="trust" stroke="var(--color-primary)" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </ChartContainer>
        </AnalyticsPanel>
      </div>

      <style>{`
        .trust-top-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: var(--space-5); }
        .trust-bottom-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-5); }
        @media (max-width: 900px) {
          .trust-top-grid, .trust-bottom-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

function RiskRow({ label, value, tone }) {
  const color = { danger: 'var(--color-danger)', warning: 'var(--color-warning)', info: 'var(--color-primary)' }[tone];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
      <span style={{ flex: '0 0 200px', fontSize: 'var(--text-sm)', color: 'var(--color-text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</span>
      <div style={{ flex: 1, height: 8, borderRadius: 'var(--radius-full)', background: 'var(--color-border)', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${value}%`, background: color, borderRadius: 'var(--radius-full)' }} />
      </div>
      <span className="tabular" style={{ fontSize: 'var(--text-sm)', fontWeight: 650, color: 'var(--color-text-primary)', width: 36, textAlign: 'right' }}>{value}%</span>
    </div>
  );
}
