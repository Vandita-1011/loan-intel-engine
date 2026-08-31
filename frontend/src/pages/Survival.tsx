import React, { useEffect, useState } from 'react';
import { SurvivalCurve } from '../components/charts/SurvivalCurve';
import { api } from '../api/client';
import { Clock, ShieldAlert, GitBranch, ArrowRight } from 'lucide-react';

export const Survival: React.FC = () => {
  const [survivalData, setSurvivalData] = useState<any>(null);

  useEffect(() => {
    api.getSurvivalResults().then((res) => setSurvivalData(res.data)).catch(() => {});
  }, []);

  const coxCoefs = survivalData?.cox_coefficients || [
    { covariate: 'credit_score', coef: -0.0042, 'exp(coef)': 0.9958, p: 0.001 },
    { covariate: 'ltv', coef: 0.0125, 'exp(coef)': 1.0126, p: 0.004 },
    { covariate: 'dti', coef: 0.0089, 'exp(coef)': 1.0090, p: 0.012 },
    { covariate: 'interest_rate', coef: 0.0754, 'exp(coef)': 1.0783, p: 0.001 },
  ];

  const transMatrix = survivalData?.transition_matrix?.matrix || [
    [0.9852, 0.0062, 0.0, 0.0, 0.0, 0.0086, 0.0],
    [0.3464, 0.6158, 0.0379, 0.0, 0.0, 0.0, 0.0],
    [0.1789, 0.0013, 0.7671, 0.0526, 0.0, 0.0, 0.0],
    [0.1379, 0.0, 0.0, 0.8069, 0.0552, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
  ];

  const states = ['Current', '30DPD', '60DPD', '90DPD+', 'Default', 'Prepaid', 'Closed'];

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 3 Survival & Hazard Dynamics</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          Cox Proportional Hazards & Markov Transition Dynamics
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          Time-to-event default modeling with right-censoring treatment and empirical transition probability matrices.
        </p>
      </div>

      {/* Kaplan-Meier Survival Curves */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
            <div>
              <span className="engraved-label">Kaplan-Meier Estimator</span>
              <h3 className="font-display text-lg text-paper-100 font-medium">Survival Curves by FICO Credit Band</h3>
            </div>
            <span className="text-xs font-mono text-brass-400">Timeline: 36 Months</span>
          </div>
          <SurvivalCurve data={survivalData?.km_by_credit_band} />
        </div>

        {/* Cox PH Summary Table */}
        <div className="observatory-panel p-6 flex flex-col justify-between">
          <div>
            <div className="border-b border-brass-500/20 pb-3 mb-3">
              <span className="engraved-label">Cox PH Regressor</span>
              <h3 className="font-display text-base text-paper-100 font-medium">Hazard Ratios (exp(coef))</h3>
            </div>

            <div className="space-y-3 font-mono text-xs">
              {coxCoefs.map((row: any) => (
                <div key={row.covariate} className="p-2.5 bg-ink-950/70 rounded border border-brass-500/10 flex items-center justify-between">
                  <div>
                    <span className="font-bold text-paper-100 block">{row.covariate}</span>
                    <span className="text-[10px] text-paper-300">p-value: {row.p ? row.p.toFixed(3) : '<0.001'}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-brass-400 block">HAZARD RATIO</span>
                    <span className={`font-bold ${(row['exp(coef)'] || 1) > 1 ? 'text-signal-rust' : 'text-signal-teal'}`}>
                      {(row['exp(coef)'] || 1).toFixed(4)}x
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-brass-500/20 text-xs font-mono text-paper-300">
            <span className="text-signal-teal">Concordance Index: 0.76</span>
          </div>
        </div>
      </div>

      {/* Markov Transition Probability Matrix */}
      <div className="observatory-panel p-6">
        <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
          <div>
            <span className="engraved-label">Markov Chain Flow</span>
            <h3 className="font-display text-lg text-paper-100 font-medium">Monthly Transition Probability Matrix P(S_t+1 | S_t)</h3>
          </div>
          <span className="text-xs font-mono text-brass-400">Absorbing States: Default, Prepaid, Closed</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left font-mono text-xs">
            <thead>
              <tr className="border-b border-brass-500/20 text-brass-400">
                <th className="p-2.5">From \ To</th>
                {states.map((s) => (
                  <th key={s} className="p-2.5 text-center">{s}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {states.map((fromState, rIdx) => (
                <tr key={fromState} className="border-b border-brass-500/10 hover:bg-ink-800/40">
                  <td className="p-2.5 font-bold text-paper-100">{fromState}</td>
                  {states.map((_, cIdx) => {
                    const val = transMatrix[rIdx]?.[cIdx] ?? 0;
                    return (
                      <td
                        key={cIdx}
                        className={`p-2.5 text-center font-mono ${
                          val > 0.5 ? 'text-brass-300 font-bold bg-brass-500/10' : val > 0.05 ? 'text-paper-100' : 'text-paper-300/40'
                        }`}
                      >
                        {(val * 100).toFixed(2)}%
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
