type PropertyOut = {
  id: string;
  address: string;
  city: string | null;
  state: string | null;
  zip: string | null;
  beds: number | null;
  baths: number | null;
  year_built: number | null;
  living_area: number | null;
  lot_area: number | null;
  image_url: string;
  created_at: string;
  updated_at: string | null;
};

type Sb9ResultsOut = {
  id: string;
  property_id: string;
  predicted_label: string;
  human_label: string | null;
  created_at: string;
  updated_at: string | null;
};

export type ResultWithProperty = Sb9ResultsOut & {
  property: PropertyOut;
};

export type ResultsPage = {
  total: number;
  page: number;
  size: number;
  items: ResultWithProperty[];
};
