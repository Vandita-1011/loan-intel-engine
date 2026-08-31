import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Compass, 
  Activity, 
  Database, 
  Target, 
  GitBranch, 
  AlertTriangle, 
  Layers, 
  Sparkles, 
  Bot, 
  FileText,
  ShieldCheck,
  Radio
} from 'lucide-react';
import { useStore, ActiveTab } from './store/useStore';
import { Landing } from './pages/Landing';
import { Overview } from './pages/Overview';
import { DataIntelligence } from './pages/DataIntelligence';
import { Prediction } from './pages/Prediction';
import { Survival } from './pages/Survival';
import { Anomalies } from './pages/Anomalies';
import { Scenarios } from './pages/Scenarios';
import { Explainability } from './pages/Explainability';
import { Copilot } from './pages/Copilot';
import { DevLog } from './pages/DevLog';

export const App: React.FC = () => {
  const { activeTab, setActiveTab, selectedLoanId } = useStore();

  if (activeTab === 'landing') {
    return <Landing />;
  }

  const navigationItems: Array<{ id: ActiveTab; label: string; icon: React.ComponentType<{ className?: string }>; tooltip: string }> = [
    { id: 'overview', label: 'Overview', icon: Compass, tooltip: 'Portfolio overview summarizing predictions, anomalies, and stress tests.' },
    { id: 'data-intelligence', label: 'Data Intelligence', icon: Database, tooltip: 'Audits data quality score, missingness, and cross-field contradictions.' },
    { id: 'prediction', label: 'Prediction', icon: Target, tooltip: 'Calibrated delinquency and default predictions via scikit-learn models.' },
    { id: 'survival', label: 'Survival & Hazards', icon: GitBranch, tooltip: 'Cox hazard curves and state transition matrices.' },
    { id: 'anomalies', label: 'Anomaly Triage', icon: AlertTriangle, tooltip: 'IsolationForest & PyTorch autoencoder anomaly scoring.' },
    { id: 'scenarios', label: 'Stress Scenarios', icon: Layers, tooltip: 'Monte Carlo cashflow and default projections under stress.' },
    { id: 'explainability', label: 'SHAP Explainability', icon: Sparkles, tooltip: 'Global & local SHAP attributions explaining model features.' },
    { id: 'copilot', label: 'AI Copilot', icon: Bot, tooltip: 'Grounded RAG assistant for loan reviews and safety rules.' },
    { id: 'devlog', label: 'Dev Log', icon: FileText, tooltip: 'Official build governance audit trail.' },
  ];

  return (
    <div className="min-h-screen bg-ink-950 text-paper-100 flex flex-col font-body selection:bg-brass-500 selection:text-ink-950">
      {/* Top Observatory Instrument Navigation Header */}
      <header className="sticky top-0 z-50 bg-ink-950/95 backdrop-blur-md border-b border-brass-500/20 px-4 lg:px-8 py-3">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Logo & Identity */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-ink-900 border border-brass-500/40 flex items-center justify-center shadow-brass-sm">
              <Compass className="w-5 h-5 text-brass-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-lg text-paper-100 tracking-tight">
                  THE OBSERVATORY
                </span>
                <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-brass-500/15 text-brass-400 border border-brass-500/30">
                  v1.0 ML Engine
                </span>
              </div>
              <p className="text-[11px] text-paper-300 font-mono">
                Loan Performance Intelligence & Risk Architecture
              </p>
            </div>
          </div>

          {/* Real-time Status */}
          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="hidden sm:flex items-center gap-2 bg-ink-900/80 px-3 py-1.5 rounded border border-brass-500/20">
              <Radio className="w-3.5 h-3.5 text-signal-teal animate-pulse" />
              <span className="text-paper-300">Active Loan:</span>
              <span className="font-bold text-brass-300">{selectedLoanId || 'LN000000'}</span>
            </div>
            <div className="flex items-center gap-2 bg-ink-900/80 px-3 py-1.5 rounded border border-brass-500/20">
              <span className="w-2 h-2 rounded-full bg-signal-teal" />
              <span className="text-paper-200">7 ML Models Loaded</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="max-w-7xl mx-auto mt-3 pt-2 border-t border-brass-500/10 flex items-center gap-1 overflow-x-auto">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                title={item.tooltip}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-mono font-medium transition-all whitespace-nowrap relative ${
                  isActive
                    ? 'text-ink-950 font-bold bg-brass-500 shadow-brass-sm'
                    : 'text-paper-300 hover:text-paper-100 hover:bg-ink-900/60'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-ink-950' : 'text-brass-400'}`} />
                {item.label}
              </button>
            );
          })}
        </nav>
      </header>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 lg:p-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === 'overview' && <Overview />}
            {activeTab === 'data-intelligence' && <DataIntelligence />}
            {activeTab === 'prediction' && <Prediction />}
            {activeTab === 'survival' && <Survival />}
            {activeTab === 'anomalies' && <Anomalies />}
            {activeTab === 'scenarios' && <Scenarios />}
            {activeTab === 'explainability' && <Explainability />}
            {activeTab === 'copilot' && <Copilot />}
            {activeTab === 'devlog' && <DevLog />}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="border-t border-brass-500/20 bg-ink-950 px-4 py-4 text-center font-mono text-xs text-paper-300">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Intain Campus FinTech Challenge 2026 — AI Track</span>
          <span className="text-brass-400">Grounded Non-LLM ML + RAG Assisted Workflow</span>
          <span>Status: Verified Runnable Prototype</span>
        </div>
      </footer>
    </div>
  );
};
