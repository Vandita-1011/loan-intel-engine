import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, CheckCircle2, AlertTriangle, ArrowRightLeft, Sparkles } from 'lucide-react';

interface LoanPassportProps {
  loan: {
    loan_id: string;
    original_balance?: number;
    credit_score_band?: string;
    ltv_band?: string;
    dti_band?: string;
    state?: string;
    loan_purpose?: string;
    interest_rate?: number;
    current_status?: string;
    days_past_due?: number;
  };
  prediction?: {
    prob_delinquency_3m?: number;
    prob_default_12m?: number;
    prob_prepayment_12m?: number;
    predicted_next_state?: string;
    confidence?: number;
    top_drivers?: Array<{ feature: string; shap_value: number }>;
  };
  anomaly?: {
    anomaly_score?: number;
    exception_type?: string;
    drivers?: string[];
    recommended_action?: string;
  };
}

export const LoanPassportCard3D: React.FC<LoanPassportProps> = ({ loan, prediction, anomaly }) => {
  const [isFlipped, setIsFlipped] = useState(false);

  const delinquency3m = prediction?.prob_delinquency_3m ?? 0.05;
  const default12m = prediction?.prob_default_12m ?? 0.02;
  const anomalyScore = anomaly?.anomaly_score ?? 0.12;

  const isHighRisk = delinquency3m > 0.35 || default12m > 0.15 || anomalyScore > 0.6;

  return (
    <div className="w-full max-w-md h-[440px] [perspective:1200px] select-none">
      <motion.div
        className="w-full h-full relative [transform-style:preserve-3d] transition-transform duration-700 cursor-pointer"
        animate={{ rotateY: isFlipped ? 180 : 0 }}
        onClick={() => setIsFlipped(!isFlipped)}
      >
        {/* FRONT SIDE: Engraved Passport Ledger */}
        <div className="absolute inset-0 [backface-visibility:hidden] rounded-xl bg-paper-100 text-ink-950 p-6 border-2 border-brass-500/60 shadow-xl flex flex-col justify-between overflow-hidden">
          {/* Background Blueprint Watermark */}
          <div className="absolute inset-0 bg-blueprint opacity-10 pointer-events-none" />

          <div>
            <div className="flex items-center justify-between border-b border-brass-500/30 pb-3">
              <div>
                <span className="text-[10px] font-mono tracking-widest text-brass-600 uppercase font-semibold">
                  Official Instrument Record
                </span>
                <h3 className="font-display text-xl font-bold text-ink-950 tracking-tight flex items-center gap-2">
                  {loan.loan_id}
                  {isHighRisk ? (
                    <span className="text-xs bg-signal-rust/15 text-signal-rust px-2 py-0.5 rounded font-mono font-normal">
                      WATCHLIST
                    </span>
                  ) : (
                    <span className="text-xs bg-signal-teal/15 text-signal-teal px-2 py-0.5 rounded font-mono font-normal">
                      STANDARD
                    </span>
                  )}
                </h3>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-brass-600 block text-[10px]">ORIGINAL PRINCIPAL</span>
                <span className="font-bold text-ink-950">
                  ${(loan.original_balance || 320000).toLocaleString()}
                </span>
              </div>
            </div>

            {/* Static Attributes Grid */}
            <div className="grid grid-cols-2 gap-3 mt-4 text-xs font-mono">
              <div className="p-2.5 bg-paper-200/70 rounded border border-brass-500/20">
                <span className="text-[10px] text-ink-800/70 block">CREDIT SCORE BAND</span>
                <span className="font-bold text-ink-950 text-sm">{loan.credit_score_band || '700-740'}</span>
              </div>
              <div className="p-2.5 bg-paper-200/70 rounded border border-brass-500/20">
                <span className="text-[10px] text-ink-800/70 block">LTV / DTI RATIOS</span>
                <span className="font-bold text-ink-950 text-sm">
                  {loan.ltv_band || '70-80%'} / {loan.dti_band || '30-40%'}
                </span>
              </div>
              <div className="p-2.5 bg-paper-200/70 rounded border border-brass-500/20">
                <span className="text-[10px] text-ink-800/70 block">PURPOSE / JURISDICTION</span>
                <span className="font-bold text-ink-950 text-sm">
                  {loan.loan_purpose || 'Purchase'} ({loan.state || 'CA'})
                </span>
              </div>
              <div className="p-2.5 bg-paper-200/70 rounded border border-brass-500/20">
                <span className="text-[10px] text-ink-800/70 block">NOTE RATE</span>
                <span className="font-bold text-ink-950 text-sm">{loan.interest_rate || 5.25}%</span>
              </div>
            </div>

            {/* Current Status Banner */}
            <div className="mt-4 p-3 bg-ink-950 text-paper-100 rounded-lg flex items-center justify-between">
              <div>
                <span className="text-[10px] text-brass-400 font-mono block">SERVICING PERFORMANCE</span>
                <span className="font-mono text-sm font-semibold">{loan.current_status || 'Current'} ({loan.days_past_due || 0} DPD)</span>
              </div>
              <div className="text-right font-mono text-xs">
                <span className="text-paper-300 text-[10px] block">ANOMALY INDEX</span>
                <span className={`font-bold ${anomalyScore > 0.5 ? 'text-signal-rust' : 'text-signal-teal'}`}>
                  {(anomalyScore * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Footer prompt */}
          <div className="pt-3 border-t border-brass-500/20 flex items-center justify-between text-xs font-mono text-brass-600">
            <span className="flex items-center gap-1">
              <Sparkles className="w-3.5 h-3.5" /> Click to Inspect ML Telemetry
            </span>
            <ArrowRightLeft className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* BACK SIDE: Calibrated ML Gauges & SHAP Drivers */}
        <div className="absolute inset-0 [transform:rotateY(180deg)] [backface-visibility:hidden] rounded-xl bg-ink-900 text-paper-100 p-6 border-2 border-brass-500/80 shadow-2xl flex flex-col justify-between overflow-hidden">
          <div>
            <div className="flex items-center justify-between border-b border-brass-500/30 pb-3">
              <div>
                <span className="text-[10px] font-mono tracking-widest text-brass-400 uppercase font-semibold">
                  Calibrated Machine Intelligence
                </span>
                <h3 className="font-display text-lg font-bold text-paper-100 flex items-center gap-2">
                  {loan.loan_id} Telemetry
                </h3>
              </div>
              <span className="text-xs font-mono bg-brass-500/20 text-brass-300 px-2 py-0.5 rounded border border-brass-500/30">
                Next: {prediction?.predicted_next_state || 'Current'}
              </span>
            </div>

            {/* Model Probability Gauges */}
            <div className="grid grid-cols-3 gap-2 mt-4 text-center font-mono">
              <div className="p-2 bg-ink-950/80 rounded border border-brass-500/20">
                <span className="text-[9px] text-paper-300 block">3M DELINQ</span>
                <span className="text-sm font-bold text-brass-300">{(delinquency3m * 100).toFixed(1)}%</span>
              </div>
              <div className="p-2 bg-ink-950/80 rounded border border-brass-500/20">
                <span className="text-[9px] text-paper-300 block">12M DEFAULT</span>
                <span className="text-sm font-bold text-signal-rust">{(default12m * 100).toFixed(1)}%</span>
              </div>
              <div className="p-2 bg-ink-950/80 rounded border border-brass-500/20">
                <span className="text-[9px] text-paper-300 block">12M PREPAY</span>
                <span className="text-sm font-bold text-signal-teal">
                  {((prediction?.prob_prepayment_12m ?? 0.15) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* SHAP Feature Drivers */}
            <div className="mt-4">
              <span className="text-[10px] font-mono tracking-wider text-brass-400 uppercase font-semibold block mb-1.5">
                Top SHAP Hazard Influencers
              </span>
              <div className="space-y-1.5 font-mono text-xs">
                {(prediction?.top_drivers?.slice(0, 3) || [
                  { feature: 'interest_rate', shap_value: 0.157 },
                  { feature: 'rate_x_ltv', shap_value: 0.139 },
                  { feature: 'days_past_due', shap_value: 0.098 },
                ]).map((driver, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-ink-950/50 p-1.5 rounded border border-brass-500/10">
                    <span className="text-paper-200 truncate">{driver.feature}</span>
                    <span className={`font-semibold ${driver.shap_value > 0 ? 'text-signal-rust' : 'text-signal-teal'}`}>
                      {driver.shap_value > 0 ? '+' : ''}{driver.shap_value.toFixed(3)}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Anomaly / Exception Alert */}
            {anomaly?.exception_type && anomaly.exception_type !== 'none' && (
              <div className="mt-3 p-2 bg-signal-rust/15 border border-signal-rust/40 rounded text-xs font-mono text-signal-rust flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold uppercase block">{anomaly.exception_type.replace('_', ' ')}</span>
                  <p className="text-[11px] text-paper-200">{anomaly.recommended_action || 'Reconciliation required'}</p>
                </div>
              </div>
            )}
          </div>

          <div className="pt-3 border-t border-brass-500/20 flex items-center justify-between text-xs font-mono text-brass-400">
            <span className="flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5" /> Recommendation — Not a Decision
            </span>
            <ArrowRightLeft className="w-3.5 h-3.5" />
          </div>
        </div>
      </motion.div>
    </div>
  );
};
