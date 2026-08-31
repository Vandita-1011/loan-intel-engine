import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface DriftChartProps {
  driftData?: Record<string, { psi: number; ks_statistic: number; ks_pvalue: number }>;
}

export const DriftChart: React.FC<DriftChartProps> = ({ driftData }) => {
  const chartData = React.useMemo(() => {
    if (!driftData) return [];
    return Object.entries(driftData).map(([feature, stats]) => ({
      feature: feature.replace(/_/g, ' '),
      psi: Number(stats.psi.toFixed(4)),
      ks: Number(stats.ks_statistic.toFixed(4)),
      status: stats.psi < 0.1 ? 'Stable' : stats.psi < 0.25 ? 'Moderate' : 'Severe',
    }));
  }, [driftData]);

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#252D3F" />
          <XAxis dataKey="feature" stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
          <YAxis stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#10131A',
              borderColor: '#C4903F',
              borderRadius: '8px',
              fontFamily: 'JetBrains Mono',
              fontSize: '12px',
            }}
          />
          <Legend wrapperStyle={{ fontFamily: 'JetBrains Mono', fontSize: '11px', color: '#E8E0CE' }} />
          <Bar dataKey="psi" name="Population Stability Index (PSI)" fill="#C4903F" radius={[4, 4, 0, 0]} />
          <Bar dataKey="ks" name="Kolmogorov-Smirnov (KS Stat)" fill="#3E8E82" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
