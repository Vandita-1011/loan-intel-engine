import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface SurvivalCurveProps {
  data?: Record<string, { time: number[]; survival: number[] }>;
}

export const SurvivalCurve: React.FC<SurvivalCurveProps> = ({ data }) => {
  // Transform Kaplan-Meier dataset into Recharts tabular structure
  const chartData = React.useMemo(() => {
    if (!data) return [];
    const bands = Object.keys(data);
    if (bands.length === 0) return [];

    const maxMonths = 36;
    const rows = [];
    for (let t = 1; t <= maxMonths; t++) {
      const row: any = { month: `M${t}` };
      bands.forEach((band) => {
        const timeArr = data[band]?.time || [];
        const survArr = data[band]?.survival || [];
        // find closest time index
        let closestIdx = 0;
        for (let i = 0; i < timeArr.length; i++) {
          if (timeArr[i] <= t) closestIdx = i;
        }
        row[band] = (survArr[closestIdx] !== undefined ? survArr[closestIdx] * 100 : 100).toFixed(1);
      });
      rows.push(row);
    }
    return rows;
  }, [data]);

  const colors = ['#B4482E', '#D9A441', '#E0B979', '#C4903F', '#3E8E82', '#68D391'];

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#252D3F" />
          <XAxis dataKey="month" stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
          <YAxis stroke="#A6732B" unit="%" domain={[70, 100]} tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
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
          {Object.keys(data || {}).map((band, idx) => (
            <Line
              key={band}
              type="monotone"
              dataKey={band}
              name={band}
              stroke={colors[idx % colors.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
