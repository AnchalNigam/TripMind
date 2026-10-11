export interface AgentTraceStep {
  step_number: number;
  thought: string;
  tool_name?: string;
  tool_input?: Record<string, any>;
  observation?: string;
}

export interface AccommodationItem {
  name: string;
  region: string;
  rating: number;
  price_per_night_inr: number;
  heating_verified: boolean;
  amenities: string[];
  couple_suitability: string;
  address_or_area: string;
}

export interface ActivityItem {
  name: string;
  region: string;
  category: string;
  is_adventure: boolean;
  estimated_duration_hours: number;
  cost_inr: number;
  description: string;
  best_time_of_day: string;
}

export interface RouteResult {
  origin: string;
  destination: string;
  mode: string;
  distance_km: number;
  estimated_duration_hours: number;
  estimated_cost_inr: number;
  road_condition: string;
  requires_special_vehicle: boolean;
  advisory: string;
}

export interface BudgetItem {
  category: string;
  amount_inr: number;
  notes: string;
}

export interface BudgetBreakdownResult {
  items: BudgetItem[];
  subtotal_inr: number;
  tax_gst_inr: number;
  buffer_inr: number;
  total_estimated_inr: number;
  budget_cap_inr: number;
  remaining_headroom_inr: number;
  is_within_budget: boolean;
  audit_notes: string;
}

export interface DayPlan {
  day_number: number;
  title: string;
  region: string;
  stay: AccommodationItem;
  activities: ActivityItem[];
  transit?: RouteResult;
  daily_cost_inr: number;
  pace_notes: string;
}

export interface TripPlanResponse {
  trip_title: string;
  destination: string;
  month: string;
  duration_days: number;
  duration_nights: number;
  traveler_profile: string;
  days: DayPlan[];
  budget_summary: BudgetBreakdownResult;
  constraints_verified: Record<string, boolean>;
  agent_reasoning_summary: string;
  execution_trace: AgentTraceStep[];
}
