import axios from 'axios';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

export const api = {
  getHealth: () => apiClient.get('/health'),
  getLoanPrediction: (loanId: string) => apiClient.get(`/predictions/${loanId}`),
  listPredictions: (limit = 20, offset = 0) => apiClient.get(`/predictions/?limit=${limit}&offset=${offset}`),
  getAnomalies: (limit = 20) => apiClient.get(`/anomalies/?limit=${limit}`),
  getScenarioResults: () => apiClient.get('/scenario/results'),
  runScenario: (scenarioName: string) => apiClient.post('/scenario/run', { scenario_name: scenarioName }),
  getExplainability: (loanId: string) => apiClient.get(`/explain/${loanId}`),
  getGlobalExplainability: () => apiClient.get('/explain/global/summary'),
  askCopilot: (loanId: string, question: string) => apiClient.post('/copilot/ask', { loan_id: loanId, question }),
  getDevLog: () => apiClient.get('/devlog'),
  getReport: (name: string) => apiClient.get(`/reports/${name}`),
  getDQSummary: () => apiClient.get('/data/dq-summary'),
  getPredictionResults: () => apiClient.get('/data/prediction-results'),
  getSurvivalResults: () => apiClient.get('/data/survival-results'),
  getExplainabilityResults: () => apiClient.get('/data/explainability-results'),
  getAnomalyExamples: () => apiClient.get('/data/anomaly-examples'),
  getPromptLog: () => apiClient.get('/prompt-log'),
};
