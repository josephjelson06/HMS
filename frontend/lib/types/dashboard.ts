export type RecentHotel = {
  id: string;
  name: string;
  status: string;
  created_at?: string | null;
};

export type AdminDashboardSummary = {
  total_hotels: number;
  active_hotels: number;
  active_subscriptions: number;
  open_helpdesk_tickets: number;
  monthly_revenue_cents: number;
  outstanding_balance_cents: number;
  new_hotels_last_30_days: number;
  recent_hotels: RecentHotel[];
};

export type RecentIncident = {
  id: string;
  title: string;
  status: string;
  severity: string;
  occurred_at?: string | null;
};

export type HotelDashboardSummary = {
  total_guests: number;
  active_guests: number;
  total_rooms: number;
  occupied_rooms: number;
  occupancy_rate: number;
  open_incidents: number;
  open_helpdesk_tickets: number;
  active_kiosks: number;
  outstanding_balance_cents: number;
  recent_incidents: RecentIncident[];
};
