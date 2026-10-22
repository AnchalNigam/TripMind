import React from 'react';
import { DayPlan } from '../types';
import { Hotel, Car, Compass, Flame, AlertTriangle, Clock } from 'lucide-react';

interface ItineraryViewProps {
  days: DayPlan[];
}

export const ItineraryView: React.FC<ItineraryViewProps> = ({ days }) => {
  return (
    <div className="space-y-6">
      {days.map((day) => (
        <div
          key={day.day_number}
          className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4 hover:border-slate-700 transition-colors"
        >
          {/* Day Header */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 bg-indigo-600 text-white font-bold rounded-lg text-sm">
                Day {day.day_number}
              </span>
              <h4 className="text-lg font-bold text-slate-100">{day.title}</h4>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs px-2.5 py-1 bg-slate-800 rounded-md text-slate-300 font-medium">
                📍 {day.region}
              </span>
              <span className="text-sm font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-md border border-emerald-500/20">
                ₹{day.daily_cost_inr.toLocaleString()}
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Stay Card */}
            {day.stay && (
              <div className={`border rounded-xl p-4 space-y-2 ${
                day.stay.price_per_night_inr > 0 ? 'bg-slate-950/70 border-slate-800/80' : 'bg-slate-950/40 border-slate-800/50 opacity-80'
              }`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
                    <Hotel className="w-4 h-4" />
                    <span>{day.stay.price_per_night_inr > 0 ? 'Accommodation' : 'Departure Checkout'}</span>
                  </div>
                  {day.stay.price_per_night_inr > 0 ? (
                    day.stay.heating_verified && (
                      <span className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400">
                        <Flame className="w-3 h-3" /> Heated Stay Verified
                      </span>
                    )
                  ) : (
                    <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
                      Checkout Day (No overnight stay)
                    </span>
                  )}
                </div>
                <div className="font-bold text-slate-200 text-base">{day.stay.name}</div>
                <div className="text-xs text-slate-400 leading-relaxed">{day.stay.couple_suitability}</div>
                <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                  <span>⭐ {day.stay.rating} / 5.0</span>
                  <span className="font-semibold text-slate-300">
                    {day.stay.price_per_night_inr > 0 
                      ? `₹${day.stay.price_per_night_inr.toLocaleString()} / night`
                      : '₹0 (Checkout Day)'
                    }
                  </span>
                </div>
              </div>
            )}

            {/* Transit Leg */}
            {day.transit && (
              <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-cyan-400 text-xs font-semibold uppercase tracking-wider">
                    <Car className="w-4 h-4" />
                    <span>Transit Leg ({day.transit.mode.toUpperCase()})</span>
                  </div>
                  <span className="text-xs font-bold text-slate-300">
                    {day.transit.distance_km} km (~{day.transit.estimated_duration_hours}h)
                  </span>
                </div>
                <div className="text-sm font-semibold text-slate-200">
                  {day.transit.origin} ➔ {day.transit.destination}
                </div>
                {day.transit.requires_special_vehicle && (
                  <div className="flex items-start gap-1.5 p-2 rounded bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                    <span>{day.transit.advisory}</span>
                  </div>
                )}
                {!day.transit.requires_special_vehicle && (
                  <div className="text-xs text-slate-400">{day.transit.advisory}</div>
                )}
                <div className="text-xs text-slate-400 pt-1">
                  Estimated Transit: <span className="font-semibold text-slate-300">₹{day.transit.estimated_cost_inr.toLocaleString()}</span>
                </div>
              </div>
            )}
          </div>

          {/* Activities */}
          {day.activities && day.activities.length > 0 && (
            <div className="space-y-2 pt-2">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <Compass className="w-4 h-4 text-emerald-400" />
                <span>Curated Experiences & Dining</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {day.activities.map((act, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-slate-950/50 border border-slate-800/60 rounded-xl space-y-1.5 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200 text-sm">{act.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-semibold">
                        {act.category === 'culinary' ? '🍽️ Culinary' : '🌄 Scenic'}
                      </span>
                    </div>
                    <p className="text-slate-400 leading-relaxed">{act.description}</p>
                    <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/40">
                      <span>⏰ {act.best_time_of_day}</span>
                      <span className="font-semibold text-slate-300">₹{act.cost_inr.toLocaleString()}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Pace Notes */}
          <div className="flex items-center gap-2 p-3 bg-slate-800/40 rounded-xl text-xs text-slate-300">
            <Clock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span><strong className="text-slate-200">Pace Advisory:</strong> {day.pace_notes}</span>
          </div>
        </div>
      ))}
    </div>
  );
};
