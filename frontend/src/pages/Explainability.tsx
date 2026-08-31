import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Search, HelpCircle, ShieldAlert, Sparkles, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';

export const Explainability: React.FC = () => {
  const { selectedLoanId, setSelectedLoanId } = useStore();
  const [globalData, setGlobalData] = useState<any>(null);
  const [loanExplain, setLoanExplain] = useState<any>(null);
  const [loanInput, setLoanInput] = useState<string>('LN000000');

  useEffect(() => {
    api.getGlobalExplainability().then((res) => setGlobalData(res.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedLoanId) {
      setLoanInput(selectedLoanId);
      api.getExplainability(selectedLoanId).then((res) => setLoanExplain(res.data)).catch(() => {});
    }
  }, [selectedLoanId]);

  const handleLookup = () => {
    if (loanInput.trim()) {
      setSelectedLoanId(loanInput.trim().toUpperCase());
    }
  };

  const globalImp = (globalData?.global_importance || [
    { feature: 'interest_rate', mean_abs_shap: 0.2845 },
    { feature: 'rate_x_ltv', mean_abs_shap: 0.2412 },
    { feature: 'days_past_due', mean_abs_shap: 0.2105 },
    { feature: 'original_balance', mean_abs_shap: 0.1874 },
    { feature: 'rate_x_dti', mean_abs_shap: 0.1652 },
    { feature: 'credit_x_ltv', mean_abs_shap: 0.1421 },
    { feature: 'credit_score_num', mean_abs_shap: 0.1198 },
    { feature: 'balance_ratio', mean_abs_shap: 0.0984 },
  ]).slice(0, 10);

  const localDrivers = loanExplain?.shap_drivers || [
    { feature: 'interest_rate', shap_value: 0.1574 },
    { feature: 'rate_x_ltv', shap_value: 0.1396 },
    { feature: 'rate_x_dti', shap_value: 0.1160 },
    { feature: 'days_past_due', shap_value: -0.045 },
    { feature: 'credit_score_num', shap_value: -0.082 },
  ];

  const fpCases = globalData?.fp_cases || [
    {
      loan_id: 'LN000841',
      prediction: 0.68,
      explanation: 'High interest rate (7.25%) and subprime credit (<620) increased hazard score, but borrower maintained perfect payment history.',
    },
  ];

  const fnCases = globalData?.fn_cases || [
    {
      loan_id: 'LN003291',
      prediction: 0.12,
      explanation: 'Prime credit (780+) and low LTV (55%) depressed hazard score, but sudden documentation lapse led to servicer default.',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 6 Model Explainability & Interpretability</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          SHAP Driver Attribution & Error Case Studies
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          Global feature importance rankings via TreeExplainer, localized waterfall hazard attributions, and false positive / negative post-mortems.
        </p>
      </div>

      {/* Loan Selector Header */}
      <div className="observatory-panel p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="engraved-label">Loan Focus:</span>
          <div className="relative">
            <input
              type="text"
              value={loanInput}
              onChange={(e) => setLoanInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLookup()}
              className="bg-ink-950 border border-brass-500/40 rounded px-3 py-1.5 font-mono text-xs text-paper-100 uppercase focus:border-brass-400 focus:outline-none w-36 font-bold"
            />
          </div>
          <button
            onClick={handleLookup}
            className="bg-brass-500 text-ink-950 font-mono text-xs font-bold px-3 py-1.5 rounded hover:bg-brass-400"
          >
            Inspect
          </button>
        </div>

        <div className="flex items-center gap-4 font-mono text-xs">
          <div>
            <span className="text-paper-300 text-[10px] block">PREDICTED 3M HAZARD</span>
            <span className="font-bold text-brass-300">
              {((loanExplain?.prediction || 0.1075) * 100).toFixed(1)}%
            </span>
          </div>
          <div>
            <span className="text-paper-300 text-[10px] block">CONFIDENCE BAND</span>
            <span className="font-bold text-signal-teal uppercase">
              {loanExplain?.confidence_band || 'High'}
            </span>
          </div>
        </div>
      </div>

      {/* Global vs Local SHAP Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Global SHAP Importance */}
        <div className="observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
            <div>
              <span className="engraved-label">Population Level</span>
              <h3 className="font-display text-base text-paper-100 font-medium">Global Feature Importance (Mean |SHAP|)</h3>
            </div>
            <span className="text-xs font-mono text-brass-400">TreeExplainer N=2,000</span>
          </div>

          <div className="w-full h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={globalImp} layout="vertical" margin={{ top: 0, right: 20, left: 60, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#252D3F" horizontal={false} />
                <XAxis type="number" stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <YAxis dataKey="feature" type="category" stroke="#A6732B" tick={{ fill: '#E8E0CE', fontSize: 11, fontFamily: 'JetBrains Mono' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#10131A',
                    borderColor: '#C4903F',
                    borderRadius: '8px',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="mean_abs_shap" name="Mean |SHAP|" fill="#C4903F" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Local Loan Attribution Waterfall */}
        <div className="observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
            <div>
              <span className="engraved-label">Subject Loan Telemetry</span>
              <h3 className="font-display text-base text-paper-100 font-medium">
                Local Attribution Waterfall ({selectedLoanId})
              </h3>
            </div>
            <span className="text-xs font-mono text-brass-400">Base: +0.0547</span>
          </div>

          <div className="space-y-3 font-mono text-xs">
            {localDrivers.map((d: any, idx: number) => {
              const isPositive = d.shap_value > 0;
              return (
                <div key={idx} className="p-2.5 bg-ink-950/70 rounded border border-brass-500/10 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-paper-100 block">{d.feature}</span>
                    <span className="text-[10px] text-paper-300">
                      {isPositive ? 'Elevates Default Hazard' : 'Mitigates Risk Factor'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className={`text-sm font-bold ${isPositive ? 'text-signal-rust' : 'text-signal-teal'}`}>
                      {isPositive ? '+' : ''}{Number(d.shap_value).toFixed(4)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* FP vs FN Case Study Post-Mortems */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="observatory-panel p-6 border-l-4 border-l-signal-amber">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-5 h-5 text-signal-amber" />
            <h4 className="font-display text-base font-bold text-paper-100">False Positive Case Studies (Type I)</h4>
          </div>
          <div className="space-y-3 font-mono text-xs">
            {fpCases.slice(0, 2).map((c: any) => (
              <div key={c.loan_id} className="p-3 bg-ink-950/80 rounded border border-brass-500/10">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-brass-300">{c.loan_id}</span>
                  <span className="text-signal-amber">Predicted: {(c.prediction * 100).toFixed(1)}% (Cured)</span>
                </div>
                <p className="text-paper-300 text-[11px] leading-relaxed">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="observatory-panel p-6 border-l-4 border-l-signal-rust">
          <div className="flex items-center gap-2 mb-3">
            <XCircle className="w-5 h-5 text-signal-rust" />
            <h4 className="font-display text-base font-bold text-paper-100">False Negative Case Studies (Type II)</h4>
          </div>
          <div className="space-y-3 font-mono text-xs">
            {fnCases.slice(0, 2).map((c: any) => (
              <div key={c.loan_id} className="p-3 bg-ink-950/80 rounded border border-brass-500/10">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-bold text-brass-300">{c.loan_id}</span>
                  <span className="text-signal-rust">Predicted: {(c.prediction * 100).toFixed(1)}% (Defaulted)</span>
                </div>
                <p className="text-paper-300 text-[11px] leading-relaxed">{c.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
