import React from 'react';
import { LineChart, Line, ResponsiveContainer } from 'recharts';

/**
 * Sparkline
 *
 * A micro inline trend line — no axes, no tooltip, no labels.
 * Embeds cleanly inside list rows (TrustCard expand, etc.).
 *
 * Props:
 *   data  — Array<{ value: number }>
 *   tone  — 'success' | 'danger' | 'warning' | 'info' | 'neutral'
 *   width — number (default 80)
 *   height — number (default 32)
 */

const TONE_COLOR = {
  success: 'var(--color-success)',
  danger:  'var(--color-danger)',
  warning: 'var(--color-warning)',
  info:    'var(--color-primary)',
  neutral: 'var(--color-text-muted)',
};

export default function Sparkline({ data = [], tone = 'info', width = 80, height = 32 }) {
  if (!data.length) return null;

  const color = TONE_COLOR[tone] || TONE_COLOR.info;

  return (
    <div style={{ width, height, flexShrink: 0 }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
