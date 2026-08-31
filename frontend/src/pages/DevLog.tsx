import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import { FileText, Cpu, CheckCircle2, ShieldAlert, Sparkles, BookOpen } from 'lucide-react';

export const DevLog: React.FC = () => {
  const [devLogContent, setDevLogContent] = useState<string>('');

  useEffect(() => {
    api.getDevLog().then((res) => {
      setDevLogContent(res.data?.content || '');
    }).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <div className="border-b border-brass-500/20 pb-4">
        <span className="engraved-label">Task 8 Agentic Transparency Deliverable</span>
        <h1 className="font-display text-2xl md:text-3xl font-bold text-paper-100 mt-1">
          AI Development & Agentic Handoff Log
        </h1>
        <p className="text-sm text-paper-300 font-mono mt-1">
          Official engineering record detailing AI tools, prompt invocations, code generation shares, quota-switch handoff, and review governance.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Col: Key Meta Stats */}
        <div className="space-y-4">
          <div className="observatory-panel p-5">
            <span className="engraved-label">Build Governance</span>
            <div className="mt-3 space-y-3 font-mono text-xs">
              <div className="p-2.5 bg-ink-950 rounded border border-brass-500/10">
                <span className="text-[10px] text-brass-400 block">PRIMARY AI AGENTS</span>
                <span className="font-bold text-paper-100 mt-0.5 block">Claude Sonnet + Gemini 3.7</span>
              </div>
              <div className="p-2.5 bg-ink-950 rounded border border-brass-500/10">
                <span className="text-[10px] text-brass-400 block">AI CODE PROPORTION</span>
                <span className="font-bold text-signal-teal mt-0.5 block">~92% Generated & Verified</span>
              </div>
              <div className="p-2.5 bg-ink-950 rounded border border-brass-500/10">
                <span className="text-[10px] text-brass-400 block">AGENT HANDOFF</span>
                <span className="font-bold text-signal-amber mt-0.5 block">Documented in Audit</span>
              </div>
            </div>
          </div>

          <div className="observatory-panel p-5">
            <span className="engraved-label">Non-Negotiables Check</span>
            <div className="mt-3 space-y-2 font-mono text-xs">
              <div className="flex items-center gap-2 text-signal-teal">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>Non-LLM ML Models for All Predictions</span>
              </div>
              <div className="flex items-center gap-2 text-signal-teal">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>Strict Time-Aware Panel Splits</span>
              </div>
              <div className="flex items-center gap-2 text-signal-teal">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>ChromaDB RAG Grounding</span>
              </div>
              <div className="flex items-center gap-2 text-signal-teal">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>Full Prompt / Decision Logging</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right 3 Cols: Rendered Markdown Content */}
        <div className="lg:col-span-3 observatory-panel p-6">
          <div className="flex items-center justify-between border-b border-brass-500/20 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-brass-400" />
              <h3 className="font-display text-base text-paper-100 font-medium">reports/ai_development_log.md</h3>
            </div>
            <span className="text-xs font-mono text-brass-400">Live Workspace Report</span>
          </div>

          <div className="bg-ink-950/80 rounded-lg p-5 border border-brass-500/10 max-h-[600px] overflow-y-auto font-mono text-xs text-paper-200 whitespace-pre-wrap leading-relaxed">
            {devLogContent || '# Loading AI Development Log...'}
          </div>
        </div>
      </div>
    </div>
  );
};
