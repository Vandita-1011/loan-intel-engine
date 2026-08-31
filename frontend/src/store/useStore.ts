import { create } from 'zustand';

export type ActiveTab = 
  | 'landing'
  | 'overview' 
  | 'data-intelligence' 
  | 'prediction' 
  | 'survival' 
  | 'anomalies' 
  | 'scenarios' 
  | 'explainability' 
  | 'copilot' 
  | 'devlog';

export interface AppState {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
  selectedLoanId: string;
  setSelectedLoanId: (loanId: string) => void;
  currentScenario: 'base' | 'adverse_credit' | 'high_prepayment';
  setCurrentScenario: (scenario: 'base' | 'adverse_credit' | 'high_prepayment') => void;
  selectedSegment: { creditBand: string; vintage: string } | null;
  setSelectedSegment: (seg: { creditBand: string; vintage: string } | null) => void;
}

export const useStore = create<AppState>((set) => ({
  activeTab: 'landing',
  setActiveTab: (activeTab) => set({ activeTab }),
  selectedLoanId: 'LN000000',
  setSelectedLoanId: (selectedLoanId) => set({ selectedLoanId }),
  currentScenario: 'base',
  setCurrentScenario: (currentScenario) => set({ currentScenario }),
  selectedSegment: null,
  setSelectedSegment: (selectedSegment) => set({ selectedSegment }),
}));
