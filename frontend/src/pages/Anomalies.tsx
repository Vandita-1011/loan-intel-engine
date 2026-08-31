import React, { useEffect, useState } from 'react';
import { LoanPassportCard3D } from '../components/3d/LoanPassportCard3D';
import { api } from '../api/client';
import { useStore } from '../store/useStore';
import { AlertCircle, Filter, Search, CheckCircle, ShieldAlert } from 'lucide-react';

export const Anomalies: React.FC = () => {
  const { selectedLoanId, setSelectedLoanId } = useStore();
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [selectedLoanData, setSelectedLoanData] = useState<any>(null);
  const [predictionData, setPredictionData] = useState<any>(null);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    api.getAnomalyExamples().then((res) => {
      setAnomalies(res.data || []);
      if (res.data && res.data.length > 0 && !selectedLoanId) {
        setSelectedLoanId(res.data[0].loan_id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (selectedLoanId) {
      api.getLoanPrediction(selectedLoanId).then((res) => {
        setPredictionData(res.data);
      }).catch(() => {});

      // Lookup anomaly in list
      const matched = anomalies.find((a) => a.loan_id === selectedLoanId);
      if (matched) {
        setSelectedLoanData({
          loan_id: matched.loan_id,
          original_balance: matched.current_balance ? matched.current_balance * 1.1 : 350000,
          current_balance: matched.current_balance,
          credit_score_band: '620-660',
          ltv_band: '80-90%',
          dti_band: '40-45%',
          state: 'TX',
          loan_purpose: 'Purchase',
          interest_rate: 6.125,
          current_status: matched.current_status,
          days_past_due: matched.days_past_due,
        });
      }
    }
  }, [selectedLoanId, anomalies]);

  const filtered = anomalies.filter((a) => {
    const matchesFilter = filterType === 'all' || a.exception_type === filterType;
    const matchesSearch = !searchQuery || a.loan_id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const selectedAnomaly = anomalies.find((a) => a.loan_id === selectedLoanId) || anomalies[0];

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 4 Anomaly & Exception Engine</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          Reviewer Triage Queue & 3D Loan Passports
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          IsolationForest + Autoencoder blended anomaly scoring with deterministic validation rule violation diagnostics.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Triage List with Filters */}
        <div className="lg:col-span-2 space-y-4">
          <div className="observatory-panel p-4 flex flex-col md:flex-row gap-3 items-center justify-between">
            <div className="relative w-full md:w-64">
              <Search className="w-4 h-4 text-brass-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search Loan ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-ink-950 border border-brass-500/30 rounded pl-9 pr-3 py-1.5 font-mono text-xs text-paper-100 placeholder-paper-300/50 focus:border-brass-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto font-mono text-xs">
              <span className="text-brass-400 text-[10px] mr-1 uppercase">Filter:</span>
              {['all', 'missing_doc', 'balance_mismatch', 'status_conflict', 'date_invalid'].map((ft) => (
                <button
                  key={ft}
                  onClick={() => setFilterType(ft)}
                  className={`px-2.5 py-1 rounded capitalize border transition-all ${
                    filterType === ft
                      ? 'bg-brass-500 text-ink-950 font-bold border-brass-400'
                      : 'bg-ink-950 text-paper-300 border-brass-500/20 hover:border-brass-500/40'
                  }`}
                >
                  {ft.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Anomaly Table */}
          <div className="observatory-panel overflow-hidden">
            <div className="max-h-[500px] overflow-y-auto">
              <table className="w-full text-left font-mono text-xs">
                <thead className="sticky top-0 bg-ink-900 border-b border-brass-500/30 text-brass-400">
                  <tr>
                    <th className="p-3">Loan ID</th>
                    <th className="p-3">Exception Category</th>
                    <th className="p-3 text-center">Anomaly Index</th>
                    <th className="p-3">Status / DPD</th>
                    <th className="p-3">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-brass-500/10">
                  {filtered.map((item) => {
                    const isSelected = item.loan_id === selectedLoanId;
                    return (
                      <tr
                        key={item.loan_id}
                        onClick={() => setSelectedLoanId(item.loan_id)}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'bg-brass-500/15 border-l-4 border-l-brass-500' : 'hover:bg-ink-800/50'
                        }`}
                      >
                        <td className="p-3 font-bold text-paper-100">{item.loan_id}</td>
                        <td className="p-3">
                          <span className="px-2 py-0.5 rounded bg-signal-rust/15 text-signal-rust uppercase text-[10px] font-semibold">
                            {item.exception_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td className="p-3 text-center font-bold text-signal-rust">
                          {(item.anomaly_score * 100).toFixed(1)}%
                        </td>
                        <td className="p-3 text-paper-200">
                          {item.current_status} ({item.days_past_due} DPD)
                        </td>
                        <td className="p-3 text-paper-300 text-[11px] truncate max-w-xs">
                          {item.recommended_action}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Col: 3D Loan Passport Flip Card */}
        <div className="flex flex-col items-center justify-start">
          <div className="mb-2 text-center">
            <span className="engraved-label">3D Passport Inspector</span>
            <p className="text-xs text-paper-300 font-mono">Click card to rotate between Ledger & Telemetry</p>
          </div>

          <LoanPassportCard3D
            loan={selectedLoanData || { loan_id: selectedLoanId || 'LN000128' }}
            prediction={predictionData}
            anomaly={selectedAnomaly}
          />
        </div>
      </div>
    </div>
  );
};
