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

interface CalibrationPlotProps {
  calibration?: {
    fraction_positive: number[];
    mean_predicted: number[];
  };
}

export const CalibrationPlot: React.FC<CalibrationPlotProps> = ({ calibration }) => {
  const chartData = React.useMemo(() => {
    if (!calibration || !calibration.mean_predicted) return [];
    return calibration.mean_predicted.map((pred, idx) => ({
      predicted: (pred * 100).toFixed(1),
      actual: ((calibration.fraction_positive[idx] || 0) * 100).toFixed(1),
      perfect: (pred * 100).toFixed(1),
    }));
  }, [calibration]);

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#252D3F" />
          <XAxis
            dataKey="predicted"
            stroke="#A6732B"
            unit="%"
            tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
            label={{ value: 'Mean Predicted Probability', position: 'insideBottom', offset: -5, fill: '#E0B979', fontSize: 11 }}
          />
          <YAxis
            stroke="#A6732B"
            unit="%"
            domain={[0, 100]}
            tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }}
            label={{ value: 'Empirical Positive Fraction', angle: -90, position: 'insideLeft', fill: '#E0B979', fontSize: 11 }}
          />
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
          <Line
            type="monotone"
            dataKey="actual"
            name="Calibrated LightGBM (Isotonic)"
            stroke="#C4903F"
            strokeWidth={3}
            dot={{ r: 4, fill: '#C4903F' }}
          />
          <Line
            type="monotone"
            dataKey="perfect"
            name="Ideal Calibration (y=x)"
            stroke="#3E8E82"
            strokeWidth={1.5}
            strokeDasharray="4 4"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
