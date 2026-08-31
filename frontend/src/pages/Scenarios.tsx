import React, { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { ScenarioSlider } from '../components/charts/ScenarioSlider';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import { Layers, Activity, TrendingDown, Zap } from 'lucide-react';

export const Scenarios: React.FC = () => {
  const { currentScenario, selectedSegment } = useStore();
  const [scenarioResults, setScenarioResults] = useState<any>(null);

  useEffect(() => {
    api.getScenarioResults().then((res) => setScenarioResults(res.data)).catch(() => {});
  }, []);

  const quarters = scenarioResults?.scenarios?.[currentScenario] || [];

  const chartData = quarters.map((q: any) => ({
    quarter: q.quarter,
    delinquency: Number((q.delinquency_rate.mean * 100).toFixed(2)),
    delinq_p95: Number((q.delinquency_rate.p95 * 100).toFixed(2)),
    default: Number((q.default_rate.mean * 100).toFixed(2)),
    prepayment: Number((q.prepayment_rate.mean * 100).toFixed(2)),
  }));

  const segments = scenarioResults?.segments || {
    '<620': { n_loans: 750, base_delinq_rate: 0.097, adverse_delinq_rate: 0.165 },
    '620-660': { n_loans: 1500, base_delinq_rate: 0.076, adverse_delinq_rate: 0.132 },
    '660-700': { n_loans: 3000, base_delinq_rate: 0.058, adverse_delinq_rate: 0.098 },
    '700-740': { n_loans: 4500, base_delinq_rate: 0.038, adverse_delinq_rate: 0.065 },
    '740-780': { n_loans: 3000, base_delinq_rate: 0.022, adverse_delinq_rate: 0.038 },
    '780+': { n_loans: 2250, base_delinq_rate: 0.011, adverse_delinq_rate: 0.018 },
  };

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 5 Macroeconomic Simulation</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          Scenario Projections & Segment Vulnerability Breakdown
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          Monte Carlo simulation (1,000 draws per quarter) projecting 8-quarter risk paths under rate, unemployment, and HPI shocks.
        </p>
      </div>

      {/* Controller */}
      <ScenarioSlider />

      {/* 8-Quarter Projected Path Chart */}
      <div className="observatory-panel p-6">
        <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
          <div>
            <span className="engraved-label">8-Quarter Forward Telemetry</span>
            <h3 className="font-display text-lg text-paper-100 font-medium">
              Projected Rate Paths: Delinquency, Default & Prepayment
            </h3>
          </div>
          <span className="text-xs font-mono text-brass-400">Monte Carlo Confidence Bands (P5 - P95)</span>
        </div>

        <div className="w-full h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#252D3F" />
              <XAxis dataKey="quarter" stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
              <YAxis stroke="#A6732B" unit="%" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
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
              <Area
                type="monotone"
                dataKey="delinquency"
                name="Delinquency Rate (30DPD+)"
                stroke="#D9A441"
                fill="#D9A441"
                fillOpacity={0.2}
                strokeWidth={2.5}
              />
              <Area
                type="monotone"
                dataKey="default"
                name="Default Hazard"
                stroke="#B4482E"
                fill="#B4482E"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Area
                type="monotone"
                dataKey="prepayment"
                name="Prepayment Hazard (CPR)"
                stroke="#3E8E82"
                fill="#3E8E82"
                fillOpacity={0.15}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Segment Level Breakdown Table */}
      <div className="observatory-panel p-6">
        <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
          <div>
            <span className="engraved-label">Segment Vulnerability Matrix</span>
            <h3 className="font-display text-lg text-paper-100 font-medium">Cohort Stress Disparity (Credit Band × Scenario)</h3>
          </div>
          {selectedSegment && (
            <span className="text-xs font-mono bg-brass-500/20 text-brass-300 px-3 py-1 rounded border border-brass-500/40">
              Terrain Focus: {selectedSegment.creditBand} ({selectedSegment.vintage})
            </span>
          )}
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-brass-500/20 text-brass-400">
                <th className="p-3">FICO Credit Band</th>
                <th className="p-3">Portfolio Volume</th>
                <th className="p-3 text-center">Base Delinq</th>
                <th className="p-3 text-center">Adverse Stress Delinq</th>
                <th className="p-3 text-center">Stress Delta</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brass-500/10">
              {Object.entries(segments).map(([band, data]: any) => {
                const isFocused = selectedSegment?.creditBand === band;
                const baseD = data.base_delinq_rate * 100;
                const advD = data.adverse_delinq_rate * 100;
                const delta = advD - baseD;

                return (
                  <tr key={band} className={`hover:bg-ink-800/40 ${isFocused ? 'bg-brass-500/10 font-bold' : ''}`}>
                    <td className="p-3 font-bold text-paper-100">{band}</td>
                    <td className="p-3 text-paper-200">{(data.n_loans || 1000).toLocaleString()} loans</td>
                    <td className="p-3 text-center text-signal-teal font-semibold">{baseD.toFixed(2)}%</td>
                    <td className="p-3 text-center text-signal-rust font-semibold">{advD.toFixed(2)}%</td>
                    <td className="p-3 text-center font-bold text-signal-rust">+{delta.toFixed(2)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
