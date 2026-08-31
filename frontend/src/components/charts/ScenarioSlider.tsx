import React from 'react';
import { motion } from 'framer-motion';
import { Activity, TrendingDown, Zap, ArrowRight } from 'lucide-react';
import { useStore } from '../../store/useStore';

export const ScenarioSlider: React.FC = () => {
  const { currentScenario, setCurrentScenario } = useStore();

  const scenarios = [
    {
      id: 'base',
      name: 'Base Scenario',
      tagline: 'Current Economic Trajectory',
      rateShock: '0 bps',
      unemployment: '4.2%',
      hpi: '+1.5%',
      icon: Activity,
      color: 'brass',
    },
    {
      id: 'adverse_credit',
      name: 'Adverse Credit',
      tagline: 'Stagflation & Housing Downturn',
      rateShock: '+225 bps',
      unemployment: '8.5%',
      hpi: '-8.0%',
      icon: TrendingDown,
      color: 'rust',
    },
    {
      id: 'high_prepayment',
      name: 'High Prepayment',
      tagline: 'Rapid Rate Cuts & Refi Wave',
      rateShock: '-250 bps',
      unemployment: '3.5%',
      hpi: '+5.0%',
      icon: Zap,
      color: 'teal',
    },
  ] as const;

  return (
    <div className="observatory-panel p-5">
      <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
        <div>
          <span className="engraved-label">Macroeconomic Stress Testing Engine</span>
          <h3 className="font-display text-lg text-paper-100 font-medium">Scenario Morph Controller</h3>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-brass-500/10 text-brass-400 border border-brass-500/30">
          Monte Carlo: 1,000 Draws/Qtr
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {scenarios.map((sc) => {
          const isSelected = currentScenario === sc.id;
          const Icon = sc.icon;

          return (
            <button
              key={sc.id}
              onClick={() => setCurrentScenario(sc.id)}
              className={`text-left p-4 rounded-lg border transition-all relative overflow-hidden flex flex-col justify-between ${
                isSelected
                  ? 'bg-ink-800/90 border-brass-500 shadow-brass-glow'
                  : 'bg-ink-950/60 border-brass-500/20 hover:border-brass-500/50 hover:bg-ink-900/60'
              }`}
            >
              {isSelected && (
                <motion.div
                  layoutId="scenario-active-indicator"
                  className="absolute inset-0 border-2 border-brass-400 rounded-lg pointer-events-none"
                  transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                />
              )}

              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`p-2 rounded ${isSelected ? 'bg-brass-500/20 text-brass-300' : 'bg-ink-900 text-paper-300'}`}>
                    <Icon className="w-4 h-4" />
                  </span>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-brass-400 font-semibold">
                    {sc.id.replace('_', ' ')}
                  </span>
                </div>
                <h4 className="font-display text-base font-semibold text-paper-100">{sc.name}</h4>
                <p className="text-xs text-paper-300 mt-0.5">{sc.tagline}</p>
              </div>

              {/* Stress Factors */}
              <div className="mt-4 pt-3 border-t border-brass-500/10 grid grid-cols-3 gap-1 font-mono text-[11px]">
                <div>
                  <span className="text-[9px] text-paper-300 block">RATE</span>
                  <span className="font-bold text-paper-100">{sc.rateShock}</span>
                </div>
                <div>
                  <span className="text-[9px] text-paper-300 block">UNEMP</span>
                  <span className="font-bold text-paper-100">{sc.unemployment}</span>
                </div>
                <div>
                  <span className="text-[9px] text-paper-300 block">HPI</span>
                  <span className={`font-bold ${sc.hpi.startsWith('-') ? 'text-signal-rust' : 'text-signal-teal'}`}>
                    {sc.hpi}
                  </span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
