import React from 'react';
import { BudgetBreakdownResult } from '../types';
import { ShieldCheck, AlertCircle, Coins, CheckCircle2 } from 'lucide-react';

interface BudgetWidgetProps {
  budget: BudgetBreakdownResult;
  constraintsVerified: Record<string, boolean>;
}

export const BudgetWidget: React.FC<BudgetWidgetProps> = ({ budget, constraintsVerified }) => {
  const percentUsed = Math.min(100, Math.round((budget.total_estimated_inr / budget.budget_cap_inr) * 100));

  return (
    <div className="space-y-6">
      {/* Progress Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Coins className="w-5 h-5 text-amber-400" />
            <h3 className="font-semibold text-lg text-slate-100">Deterministic Financial Audit</h3>
          </div>
          <div className="flex items-center gap-2">
            {budget.is_within_budget ? (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-bold text-xs rounded-full">
                <ShieldCheck className="w-4 h-4" /> Budget Compliant
              </span>
            ) : (
              <span className="flex items-center gap-1.5 px-3 py-1 bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold text-xs rounded-full">
                <AlertCircle className="w-4 h-4" /> Cap Exceeded
              </span>
            )}
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs font-semibold text-slate-300">
            <span>Total Estimated: ₹{budget.total_estimated_inr.toLocaleString()}</span>
            <span>Budget Cap: ₹{budget.budget_cap_inr.toLocaleString()}</span>
          </div>
          <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-500 ${
                budget.is_within_budget ? 'bg-gradient-to-r from-emerald-500 to-cyan-400' : 'bg-rose-500'
              }`}
              style={{ width: `${percentUsed}%` }}
            />
          </div>
          <div className="flex justify-between text-[11px] text-slate-400">
            <span>{percentUsed}% Utilized</span>
            <span className="text-emerald-400 font-bold">
              Remaining Headroom: ₹{budget.remaining_headroom_inr.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Audit Notes */}
        <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/60 text-xs text-slate-300">
          <strong>Audit Status:</strong> {budget.audit_notes}
        </div>
      </div>

      {/* Itemized Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h4 className="font-semibold text-sm uppercase tracking-wider text-slate-400">Itemized Cost Breakdown</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5">Category</th>
                <th className="py-2.5 text-right">Amount</th>
                <th className="py-2.5 pl-4">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 text-xs">
              {budget.items.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-800/20">
                  <td className="py-2.5 font-medium text-slate-200">{item.category}</td>
                  <td className="py-2.5 text-right font-mono font-bold text-slate-100">
                    ₹{item.amount_inr.toLocaleString()}
                  </td>
                  <td className="py-2.5 pl-4 text-slate-400">{item.notes}</td>
                </tr>
              ))}
              <tr className="border-t-2 border-slate-800 font-semibold">
                <td className="py-3 text-slate-200">Subtotal</td>
                <td className="py-3 text-right font-mono text-slate-100">₹{budget.subtotal_inr.toLocaleString()}</td>
                <td className="py-3 pl-4 text-slate-400">Direct Travel & Stay Services</td>
              </tr>
              <tr>
                <td className="py-2 text-slate-400">GST (5%)</td>
                <td className="py-2 text-right font-mono text-slate-300">₹{budget.tax_gst_inr.toLocaleString()}</td>
                <td className="py-2 pl-4 text-slate-400">Mandatory Tourism & Hospitality Tax</td>
              </tr>
              <tr>
                <td className="py-2 text-slate-400">Contingency Cushion</td>
                <td className="py-2 text-right font-mono text-slate-300">₹{budget.buffer_inr.toLocaleString()}</td>
                <td className="py-2 pl-4 text-slate-400">10% Seasonal Weather Reserve</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Constraints Checklist */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
        <h4 className="font-semibold text-sm uppercase tracking-wider text-slate-400">
          Zero-Math Intuitive Constraint Verification
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {Object.entries(constraintsVerified).map(([key, val]) => (
            <div
              key={key}
              className="flex items-center gap-2 p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs"
            >
              <CheckCircle2 className={`w-4 h-4 ${val ? 'text-emerald-400' : 'text-rose-400'}`} />
              <span className="font-medium text-slate-200 capitalize">
                {key.replace(/_/g, ' ')}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
