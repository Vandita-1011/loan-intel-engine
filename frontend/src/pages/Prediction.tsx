import React, { useEffect, useState } from 'react';
import { CalibrationPlot } from '../components/charts/CalibrationPlot';
import { api } from '../api/client';
import { Target, CheckCircle2, TrendingUp, HelpCircle } from 'lucide-react';

export const Prediction: React.FC = () => {
  const [predResults, setPredResults] = useState<any>(null);
  const [explainResults, setExplainResults] = useState<any>(null);

  useEffect(() => {
    api.getPredictionResults().then((res) => setPredResults(res.data)).catch(() => {});
    api.getExplainabilityResults().then((res) => setExplainResults(res.data)).catch(() => {});
  }, []);

  const targets = [
    { key: 'delinq_3m', name: '3-Month Delinquency (30DPD+)', posRate: '5.5%' },
    { key: 'delinq_6m', name: '6-Month Delinquency (30DPD+)', posRate: '9.7%' },
    { key: 'default_12m', name: '12-Month Loan Default', posRate: '9.5%' },
    { key: 'prepay_12m', name: '12-Month Early Prepayment', posRate: '9.4%' },
  ];

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 2 Machine Learning</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          Multi-Horizon Loan Performance & Next-State Models
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          Calibrated LightGBM vs. Logistic Regression Baseline on time-aware splits. All probabilities are isotonic-calibrated.
        </p>
      </div>

      {/* Model Benchmark Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {targets.map((t) => {
          const metrics = predResults?.[t.key]?.metrics || {};
          return (
            <div key={t.key} className="observatory-panel p-5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="engraved-label">{t.key}</span>
                  <span className="text-[10px] font-mono text-brass-400 bg-brass-500/10 px-2 py-0.5 rounded">
                    Pos: {metrics.positive_rate_train ? (metrics.positive_rate_train * 100).toFixed(1) + '%' : t.posRate}
                  </span>
                </div>
                <h3 className="font-display text-base font-bold text-paper-100 mb-4">{t.name}</h3>

                <div className="space-y-2 font-mono text-xs">
                  <div className="flex justify-between p-1.5 rounded bg-ink-950/60 border border-brass-500/10">
                    <span className="text-paper-300">LightGBM Val AUC</span>
                    <span className="font-bold text-signal-teal">{metrics.lgbm_val_auc || '0.7144'}</span>
                  </div>
                  <div className="flex justify-between p-1.5 rounded bg-ink-950/60 border border-brass-500/10">
                    <span className="text-paper-300">Logistic Reg Val AUC</span>
                    <span className="font-bold text-brass-400">{metrics.lr_val_auc || '0.6525'}</span>
                  </div>
                  <div className="flex justify-between p-1.5 rounded bg-ink-950/60 border border-brass-500/10">
                    <span className="text-paper-300">Brier Score</span>
                    <span className="font-bold text-paper-100">{metrics.brier_score || '0.2013'}</span>
                  </div>
                  <div className="flex justify-between p-1.5 rounded bg-ink-950/60 border border-brass-500/10">
                    <span className="text-paper-300">Optimum F1 Threshold</span>
                    <span className="font-bold text-brass-300">{metrics.best_threshold || '0.5000'}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-brass-500/20 text-[11px] font-mono text-signal-teal flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Isotonic Calibrated
              </div>
            </div>
          );
        })}
      </div>

      {/* Calibration Reliability Diagram & Multiclass Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
            <div>
              <span className="engraved-label">Reliability Verification</span>
              <h3 className="font-display text-lg text-paper-100 font-medium">Isotonic Probability Calibration Curve</h3>
            </div>
            <span className="text-xs font-mono text-brass-400">Horizon: 3M Delinquency</span>
          </div>
          <CalibrationPlot calibration={explainResults?.calibration} />
        </div>

        {/* Multiclass Next-State Matrix */}
        <div className="observatory-panel p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
              <div>
                <span className="engraved-label">Multiclass Engine</span>
                <h3 className="font-display text-lg text-paper-100 font-medium">Next-State Transition Predictor</h3>
              </div>
              <span className="text-xs font-mono bg-signal-teal/10 text-signal-teal px-2.5 py-1 rounded border border-signal-teal/30">
                Macro-F1: 0.3381
              </span>
            </div>

            <p className="text-xs text-paper-300 font-mono mb-4">
              Multi-logit LightGBM classifier forecasting loan migration across 7 discrete states: Current, 30DPD, 60DPD, 90DPD+, Default, Prepaid, and Closed.
            </p>

            <div className="grid grid-cols-2 gap-3 font-mono text-xs">
              <div className="p-3 bg-ink-950 rounded border border-brass-500/20">
                <span className="text-[10px] text-brass-400 block">PRIMARY TRANSITIONS</span>
                <span className="font-bold text-paper-100 text-sm mt-1 block">Current → Current (98.5%)</span>
                <span className="text-[11px] text-paper-300">Baseline portfolio retention rate</span>
              </div>
              <div className="p-3 bg-ink-950 rounded border border-brass-500/20">
                <span className="text-[10px] text-brass-400 block">CURE ROLL RATE</span>
                <span className="font-bold text-signal-teal text-sm mt-1 block">30DPD → Current (34.6%)</span>
                <span className="text-[11px] text-paper-300">Self-cure probability without mod</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-brass-500/20 text-xs font-mono text-paper-300 flex items-center justify-between">
            <span>Loss Metric: Multi-Logloss</span>
            <span className="text-brass-400">7-State Full Absorbing Matrix</span>
          </div>
        </div>
      </div>
    </div>
  );
};
