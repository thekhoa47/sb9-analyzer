type LineStringGeometry = {
  type: 'LineString';
  coordinates: [number, number][];
};

type PolygonGeometry = {
    type: 'Polygon';
    coordinates:  [number, number][]
};

export type PropertyAnalysisOut = {
    id: string;
    property_id: string;
    sb9_possible: boolean;
    adu_possible: boolean;
    band_low: number | null;
    band_high: number | null;
    split_angle_degree: number | null;
    split_line_geometry: LineStringGeometry | null;
    image_url: string | null;
    created_at: string;
    updated_at: string | null;
}

type PropertyOut = {
  id: string;
  address_line1: string;
  address_line2: string | null;
  city: string;
  state: string;
  zip: string;
  bedrooms: number | null;
  bathrooms: number | null;
  year_built: number | null;
  house_geometry: PolygonGeometry | null;
  created_at: string;
  updated_at: string | null;
};

export type AnalyzedProperty = PropertyOut & {
  analysis: PropertyAnalysisOut;
};

export type AnalyzedPropertiesPage = {
  total: number;
  page: number;
  size: number;
  items: AnalyzedProperty[];
};