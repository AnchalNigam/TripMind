import { useState } from 'react';
import { TripPlanResponse } from './types';
import { TraceViewer } from './components/TraceViewer';
import { ItineraryView } from './components/ItineraryView';
import { BudgetWidget } from './components/BudgetWidget';
import {
  Compass,
  Sparkles,
  Database,
  Brain,
  Calendar,
  Coins,
  Send,
  Loader2,
  ExternalLink,
} from 'lucide-react';

const PRESET_QUERIES = [
  {
    label: '❄️ 5-Day Kashmir Winter',
    query:
      "I want to visit Kashmir in December for 5 days. I'm going with my wife. We don't want a hectic trip. We love scenic places and food, but aren't interested in adventure activities. Budget around ₹80k excluding flights.",
  },
  {
    label: '🏖️ 4-Day Goa Beach',
    query:
      'I want to visit Goa in November for 4 days with friends. Relaxing beach trip, seafood, no water sports adventure. Budget ₹40k.',
  },
  {
    label: '🦏 2-Day Assam Food & River',
    query:
      'I want to go to Assam for 2 days. Relaxing trip, good local food, no adventure sports. Budget around ₹35k. I am in Delhi.',
  },
];

export function App() {
  const [query, setQuery] = useState(PRESET_QUERIES[0].query);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [plan, setPlan] = useState<TripPlanResponse | null>(null);
  const [provider, setProvider] = useState<'mock' | 'gemini' | 'groq'>('mock');
  const [activeTab, setActiveTab] = useState<'itinerary' | 'trace' | 'budget'>('itinerary');

  const handlePlan = async (queryText: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/planner/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_query: queryText,
          preferred_provider: provider,
        }),
      });

      if (!response.ok) {
        let msg = `Server responded with HTTP ${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) msg = errorData.detail;
        } catch (_) {}
        throw new Error(msg);
      }

      const data: TripPlanResponse = await response.json();
      setPlan(data);
      setActiveTab('itinerary');
    } catch (err: any) {
      const msg = err.message || 'Failed to generate itinerary';
      if (msg.includes('500') || msg.includes('Failed to fetch')) {
        setError(`${msg} — Please check that your FastAPI backend is running on port 8000 (\`uvicorn tripmind.api.app:app --port 8000\`) and PostgreSQL is active.`);
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <span className="text-3xl">🏔️</span>
            <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-2">
              TripMind <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 font-mono font-bold border border-indigo-500/30">V1 ReAct Engine</span>
            </h1>
          </div>
          <p className="text-sm text-slate-400">
            Autonomous Adaptive Trip Planning across the 7 progressive levels of Agentic AI.
          </p>
        </div>

        {/* Status Indicators */}
        <div className="flex flex-wrap items-center gap-2.5 text-xs font-mono">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-semibold">
            <Database className="w-3.5 h-3.5" />
            <span>PostgreSQL 16 (Port 5433)</span>
          </div>
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-semibold">
            <Compass className="w-3.5 h-3.5" />
            <span>Live OSRM Routing</span>
          </div>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            <span>Swagger API</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </header>

      {/* Query Section */}
      <section className="bg-slate-900 border border-slate-800 rounded-3xl p-6 shadow-2xl space-y-4">
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Enter Natural Language Travel Goal & Constraints</span>
          </label>
          <div className="relative">
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe your trip, constraints, budget, and travel companions..."
              className="w-full bg-slate-950 border border-slate-800 rounded-2xl px-4 py-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm leading-relaxed"
            />
            <button
              onClick={() => handlePlan(query)}
              disabled={loading || !query.trim()}
              className="absolute right-3 bottom-4 px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-sm flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all duration-150"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Agent Planning...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Execute ReAct Loop</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Controls: Provider Selector + Quick Benchmarks */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-semibold flex items-center gap-1">
              <Brain className="w-3.5 h-3.5 text-indigo-400" />
              <span>LLM Engine:</span>
            </span>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as 'mock' | 'gemini' | 'groq')}
              className="bg-slate-950 border border-slate-700 hover:border-slate-600 text-xs rounded-xl px-3 py-1.5 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium cursor-pointer"
            >
              <option value="mock">⚡ Mock Replay (Instant, Deterministic)</option>
              <option value="gemini">✨ Google Gemini 2.0 (Live AI)</option>
              <option value="groq">⚡ Groq Llama 3.3 70B (Live AI)</option>
            </select>
          </div>

          {/* Preset Chips */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-slate-400 font-medium">Test Queries:</span>
            {PRESET_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQuery(preset.query);
                  handlePlan(preset.query);
                }}
                className="px-2.5 py-1 text-xs rounded-full bg-slate-800/90 hover:bg-slate-700 text-slate-300 border border-slate-700/60 transition-colors font-medium"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Loading state indicator */}
      {loading && (
        <div className="p-12 text-center bg-slate-900/60 border border-slate-800 rounded-3xl space-y-3 animate-pulse">
          <Brain className="w-10 h-10 text-indigo-400 mx-auto animate-bounce" />
          <h3 className="text-lg font-bold text-slate-200">Autonomous ReAct Loop in Progress</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Deliberating over seasonal accessibility, invoking transit routing, querying PostgreSQL for stays, and auditing budget constraints...
          </p>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-2xl text-sm">
          {error}
        </div>
      )}

      {/* Results Section */}
      {plan && !loading && (
        <div className="space-y-6">
          {/* Trip Summary Card */}
          <div className="bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-slate-800 rounded-3xl p-6 shadow-xl space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-2xl font-black text-white">{plan.trip_title}</h2>
              <span className="px-3 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-bold border border-indigo-500/30">
                {plan.duration_days} Days / {plan.duration_nights} Nights
              </span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">
              {plan.agent_reasoning_summary}
            </p>
          </div>

          {/* Navigation Tabs */}
          <div className="flex border-b border-slate-800 gap-2">
            <button
              onClick={() => setActiveTab('itinerary')}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
                activeTab === 'itinerary'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Calendar className="w-4 h-4" />
              <span>Verified Itinerary</span>
            </button>
            <button
              onClick={() => setActiveTab('trace')}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
                activeTab === 'trace'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Brain className="w-4 h-4" />
              <span>ReAct Cognitive Trace ({plan.execution_trace.length})</span>
            </button>
            <button
              onClick={() => setActiveTab('budget')}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
                activeTab === 'budget'
                  ? 'border-indigo-500 text-indigo-400'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              <Coins className="w-4 h-4" />
              <span>Budget Audit (₹{plan.budget_summary.total_estimated_inr.toLocaleString()})</span>
            </button>
          </div>

          {/* Tab Content */}
          <div>
            {activeTab === 'itinerary' && <ItineraryView days={plan.days} />}
            {activeTab === 'trace' && <TraceViewer trace={plan.execution_trace} />}
            {activeTab === 'budget' && (
              <BudgetWidget
                budget={plan.budget_summary}
                constraintsVerified={plan.constraints_verified}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
