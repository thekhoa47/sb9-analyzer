export type MaskResult = {
  id: string;
  address: string;
  city: string;
  state: string;
  zip: string;
  beds: number;
  baths: number;
  year_built: number;
  living_area: number;
  lot_area: number;
  image_url: string;
  parcel_stats: string;
};

export type AnalyzeResult = MaskResult & {
  predicted_label: 'YES' | 'NO';
};
