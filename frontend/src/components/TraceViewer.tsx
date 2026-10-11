import React, { useState } from 'react';
import { AgentTraceStep } from '../types';
import { Brain, Terminal, Eye, ChevronDown, ChevronRight } from 'lucide-react';

interface TraceViewerProps {
  trace: AgentTraceStep[];
}

export const TraceViewer: React.FC<TraceViewerProps> = ({ trace }) => {
  const [expandedSteps, setExpandedSteps] = useState<Record<number, boolean>>({
    1: true,
    2: true,
  });

  const toggleStep = (stepNumber: number) => {
    setExpandedSteps((prev) => ({
      ...prev,
      [stepNumber]: !prev[stepNumber],
    }));
  };

  if (!trace || trace.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400">
        No execution trace recorded. Run an itinerary plan to inspect the ReAct loop.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-lg text-slate-200">ReAct Cognitive Trace (Explainability)</h3>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 font-mono">
          {trace.length} Iteration Cycles
        </span>
      </div>

      <div className="space-y-3">
        {trace.map((step) => {
          const isExpanded = expandedSteps[step.step_number] ?? false;

          return (
            <div
              key={step.step_number}
              className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden transition-all duration-150 hover:border-slate-700"
            >
              <button
                onClick={() => toggleStep(step.step_number)}
                className="w-full px-4 py-3 flex items-center justify-between bg-slate-900/80 hover:bg-slate-800/50 transition-colors text-left"
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-mono font-bold flex items-center justify-center">
                    {step.step_number}
                  </span>
                  <span className="font-medium text-slate-200 text-sm">
                    {step.tool_name ? `Turn ${step.step_number}: Action ➔ ${step.tool_name}` : `Turn ${step.step_number}: Deliberation`}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  {step.tool_name && (
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-mono">
                      {step.tool_name}
                    </span>
                  )}
                  {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>
              </button>

              {isExpanded && (
                <div className="p-4 space-y-3 border-t border-slate-800/80 bg-slate-950/60 font-sans">
                  {/* Thought */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-400">
                      <Brain className="w-3.5 h-3.5" />
                      <span>Agent Thought</span>
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed pl-5 italic border-l-2 border-amber-500/40">
                      "{step.thought}"
                    </p>
                  </div>

                  {/* Tool Call Action */}
                  {step.tool_name && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                        <Terminal className="w-3.5 h-3.5" />
                        <span>Tool Invoked: {step.tool_name}</span>
                      </div>
                      <div className="pl-5">
                        <pre className="text-xs font-mono bg-slate-900 p-2.5 rounded-lg border border-slate-800 text-cyan-300 overflow-x-auto">
                          {JSON.stringify(step.tool_input, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}

                  {/* Observation */}
                  {step.observation && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-400">
                        <Eye className="w-3.5 h-3.5" />
                        <span>Environmental Observation</span>
                      </div>
                      <div className="pl-5">
                        <div className="text-xs font-mono bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 text-slate-300 overflow-x-auto max-h-48 overflow-y-auto">
                          {step.observation}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
