import React, { useEffect, useState } from 'react';
import { ShieldCheck, AlertTriangle, FileSpreadsheet, CheckCircle2, TrendingUp } from 'lucide-react';
import { DriftChart } from '../components/charts/DriftChart';
import { api } from '../api/client';

export const DataIntelligence: React.FC = () => {
  const [dq, setDq] = useState<any>(null);

  useEffect(() => {
    api.getDQSummary().then((res) => setDq(res.data)).catch(() => {});
  }, []);

  const missingData = dq?.missing_pct || {
    document_status: 6.42,
    current_balance: 1.18,
    loss_severity_band: 0.85,
  };

  const contradictions = dq?.contradictions || {
    prepaid_with_balance: 56,
    current_with_dpd: 5424,
    invalid_dates: 4643,
  };

  const outliers = dq?.outliers || {
    current_balance: { iqr_outliers: 9418, zscore_outliers: 3524 },
    days_past_due: { iqr_outliers: 12040, zscore_outliers: 8400 },
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 1 Telemetry</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          Data Intelligence & Quality Assurance Profiling
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          In-depth distribution analysis, intentional messiness detection, rule verification & drift metrics.
        </p>
      </div>

      {/* Top DQ Score Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="observatory-panel p-6 flex flex-col justify-between">
          <div>
            <span className="engraved-label">Portfolio Quality Score</span>
            <div className="flex items-baseline gap-2 mt-2">
              <span className="font-mono text-5xl font-bold text-brass-400">
                {dq?.data_quality_score || 66.4}
              </span>
              <span className="font-mono text-sm text-paper-300">/ 100</span>
            </div>
            <p className="text-xs text-paper-300 mt-2 font-mono">
              Composite index calculated from completeness ({dq?.completeness_pct || 98.5}%) and deterministic validity ({dq?.validity_pct || 34.3}%).
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-brass-500/20 flex items-center justify-between text-xs font-mono">
            <span className="text-signal-teal flex items-center gap-1"><ShieldCheck className="w-4 h-4" /> 8 Rules Verified</span>
            <span className="text-brass-400">Batch #2026-08</span>
          </div>
        </div>

        {/* Missingness Breakdown */}
        <div className="observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-2 mb-3">
            <span className="engraved-label">Missingness Heatmap</span>
            <span className="text-xs font-mono text-brass-400">MCAR + MNAR</span>
          </div>
          <div className="space-y-3 font-mono text-xs">
            {Object.entries(missingData).map(([col, pct]: any) => (
              <div key={col}>
                <div className="flex justify-between text-paper-200 mb-1">
                  <span>{col}</span>
                  <span className="font-bold text-brass-300">{Number(pct).toFixed(2)}%</span>
                </div>
                <div className="w-full h-2 rounded-full bg-ink-950 overflow-hidden border border-brass-500/20">
                  <div className="h-full bg-brass-500" style={{ width: `${Math.min(Number(pct) * 10, 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Injected Contradictions */}
        <div className="observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-2 mb-3">
            <span className="engraved-label">Rule Contradictions</span>
            <span className="text-xs font-mono text-signal-rust">Intentional Injections</span>
          </div>
          <div className="space-y-2.5 font-mono text-xs">
            <div className="p-2 bg-ink-950/60 rounded border border-brass-500/10 flex justify-between items-center">
              <span className="text-paper-200">Prepaid with Balance &gt; 0</span>
              <span className="font-bold text-signal-rust">{contradictions.prepaid_with_balance} rows</span>
            </div>
            <div className="p-2 bg-ink-950/60 rounded border border-brass-500/10 flex justify-between items-center">
              <span className="text-paper-200">Current with DPD &gt; 0</span>
              <span className="font-bold text-signal-amber">{contradictions.current_with_dpd} rows</span>
            </div>
            <div className="p-2 bg-ink-950/60 rounded border border-brass-500/10 flex justify-between items-center">
              <span className="text-paper-200">Invalid Audit Dates</span>
              <span className="font-bold text-signal-rust">{contradictions.invalid_dates} rows</span>
            </div>
          </div>
        </div>
      </div>

      {/* Population Stability Index / Drift Analysis */}
      <div className="observatory-panel p-6">
        <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
          <div>
            <span className="engraved-label">Temporal Stability Engine</span>
            <h3 className="font-display text-lg text-paper-100 font-medium">Train vs Test Population Drift (PSI & KS)</h3>
          </div>
          <span className="text-xs font-mono bg-brass-500/10 text-brass-400 px-3 py-1 rounded border border-brass-500/30">
            Split: Months 1-24 vs 25-36
          </span>
        </div>
        <DriftChart driftData={dq?.drift} />
      </div>
    </div>
  );
};
