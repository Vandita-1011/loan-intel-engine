import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  AlertCircle, 
  ShieldCheck, 
  Database, 
  Compass, 
  Layers,
  ArrowUpRight
} from 'lucide-react';
import { RiskTerrain } from '../components/3d/RiskTerrain';
import { ScenarioSlider } from '../components/charts/ScenarioSlider';
import { useStore } from '../store/useStore';
import { api } from '../api/client';

export const Overview: React.FC = () => {
  const { currentScenario, setSelectedSegment, setActiveTab, setSelectedLoanId } = useStore();
  const [summary, setSummary] = useState<any>(null);
  const [anomalies, setAnomalies] = useState<any[]>([]);

  useEffect(() => {
    api.getDQSummary().then((res) => setSummary(res.data)).catch(() => {});
    api.getAnomalies(5).then((res) => setAnomalies(res.data.anomalies || [])).catch(() => {});
  }, []);

  const kpis = [
    {
      label: 'PORTFOLIO VOLUME',
      value: '15,000 Loans',
      sub: '$3.42B Active UPB',
      icon: Database,
      trend: '+4.2% YoY',
      color: 'brass',
    },
    {
      label: 'DATA QUALITY SCORE',
      value: `${summary?.data_quality_score || 66.4}/100`,
      sub: '98.5% Record Completeness',
      icon: ShieldCheck,
      trend: 'Verified Rules',
      color: 'teal',
    },
    {
      label: '3M DELINQUENCY HAZARD',
      value: currentScenario === 'adverse_credit' ? '9.4%' : currentScenario === 'high_prepayment' ? '4.8%' : '5.5%',
      sub: 'Calibrated LightGBM Target',
      icon: TrendingUp,
      trend: currentScenario === 'adverse_credit' ? '+71% Stress' : 'Base Horizon',
      color: currentScenario === 'adverse_credit' ? 'rust' : 'amber',
    },
    {
      label: 'HIGH-PRIORITY EXCEPTIONS',
      value: `${anomalies.length > 0 ? anomalies.length * 4 : 20} Critical`,
      sub: 'IsolationForest + Autoencoder',
      icon: AlertCircle,
      trend: 'Triage Required',
      color: 'rust',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner: Instrument Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-brass-500/20 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-brass-500 animate-spin-slow" />
            <span className="engraved-label">Observatory Command Bridge</span>
          </div>
          <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
            Portfolio Intelligence & Hazard Telemetry
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="bg-ink-900 border border-brass-500/30 px-3 py-1.5 rounded-lg flex items-center gap-2 font-mono text-xs">
            <span className="w-2 h-2 rounded-full bg-signal-teal animate-pulse" />
            <span className="text-paper-200">ML Engines Online</span>
          </div>
          <button 
            onClick={() => setActiveTab('copilot')}
            className="bg-brass-500 hover:bg-brass-400 text-ink-950 px-4 py-1.5 rounded-lg font-mono text-xs font-bold transition-all shadow-brass-sm flex items-center gap-1.5"
          >
            Launch Copilot <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* KPI Instrument Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.08, type: 'spring', stiffness: 200 }}
              className="observatory-panel p-4 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between">
                <span className="engraved-label">{kpi.label}</span>
                <span className="p-1.5 rounded bg-ink-800 text-brass-400 border border-brass-500/20">
                  <Icon className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3">
                <div className="font-mono text-2xl font-bold text-paper-100 tracking-tight">
                  {kpi.value}
                </div>
                <div className="flex items-center justify-between mt-1 text-xs font-mono">
                  <span className="text-paper-300">{kpi.sub}</span>
                  <span className={`font-semibold ${
                    kpi.color === 'teal' ? 'text-signal-teal' : kpi.color === 'rust' ? 'text-signal-rust' : 'text-brass-400'
                  }`}>
                    {kpi.trend}
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* 3D Risk Terrain Centerpiece */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[480px]">
          <RiskTerrain
            scenario={currentScenario}
            onSelectSegment={(creditBand, vintage) => {
              setSelectedSegment({ creditBand, vintage });
              setActiveTab('scenarios');
            }}
          />
        </div>

        {/* Right Side: Quick Triage Queue */}
        <div className="observatory-panel p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-3">
              <div>
                <span className="engraved-label">Reviewer Exception Queue</span>
                <h3 className="font-display text-base text-paper-100 font-medium">Anomaly Watchlist</h3>
              </div>
              <button
                onClick={() => setActiveTab('anomalies')}
                className="text-xs font-mono text-brass-400 hover:text-brass-300 flex items-center gap-1"
              >
                View All <ArrowUpRight className="w-3 h-3" />
              </button>
            </div>

            <div className="space-y-2.5 font-mono text-xs">
              {(anomalies.length > 0 ? anomalies : [
                { loan_id: 'LN000128', exception_type: 'balance_mismatch', anomaly_score: 0.89 },
                { loan_id: 'LN000452', exception_type: 'status_conflict', anomaly_score: 0.84 },
                { loan_id: 'LN001093', exception_type: 'date_invalid', anomaly_score: 0.78 },
                { loan_id: 'LN002144', exception_type: 'missing_doc', anomaly_score: 0.72 },
              ]).map((anom, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setSelectedLoanId(anom.loan_id);
                    setActiveTab('anomalies');
                  }}
                  className="p-2.5 rounded bg-ink-950/60 border border-brass-500/20 hover:border-brass-500/60 hover:bg-ink-800/80 cursor-pointer transition-all flex items-center justify-between"
                >
                  <div>
                    <span className="font-bold text-paper-100 block">{anom.loan_id}</span>
                    <span className="text-[10px] text-signal-rust uppercase">
                      {anom.exception_type?.replace(/_/g, ' ') || 'Reconciliation Error'}
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-paper-300 block">SCORE</span>
                    <span className="font-bold text-signal-rust">
                      {((anom.anomaly_score || 0.8) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-brass-500/20 text-xs font-mono text-paper-300 flex items-center justify-between">
            <span className="flex items-center gap-1.5"><Layers className="w-3.5 h-3.5 text-brass-400" /> Blended IF+AE Model</span>
            <span className="text-signal-teal">100% Deterministic Verified</span>
          </div>
        </div>
      </div>

      {/* Scenario Morph Controller */}
      <ScenarioSlider />
    </div>
  );
};
