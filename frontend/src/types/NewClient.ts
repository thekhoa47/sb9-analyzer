export type NewClient = {
  id: string;
  name: string;
  email: string | null;
  phone: string | null;
  messenger_psid: string | null;
  email_opt_in: boolean;
  sms_opt_in: boolean;
  messenger_opt_in: boolean;
  created_at: string;
  updated_at: string | null;
  listing_preferences: {
    id: string;
    client_id: string;
    name: string;
    city: string;
    radius_miles: number;
    beds_min: number;
    baths_min: number;
    max_price: number | null;
    criteria_json: string | null;
    cursor_iso: string | null;
    created_at: string;
    updated_at: string | null;
  }[];
};

export type PaginatedClients = {
  items: NewClient[];
  page: number;
  pages: number;
  size: number;
  total: number;
};
