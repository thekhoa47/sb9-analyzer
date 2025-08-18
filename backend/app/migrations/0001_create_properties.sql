CREATE TABLE IF NOT EXISTS properties (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  address          text        NOT NULL,
  city             text,
  state            char(2) CHECK (state ~ '^[A-Z]{2}$'),
  zip              char(5) CHECK (zip ~ '^[0-9]{5}$'),
  parcel_geom      geometry(Polygon, 4326),
  parcel_centroid  geometry(Point,   4326),
  beds             integer,
  baths            numeric(3,1) CHECK (baths >= 0),  -- allows 1.5, 2.5, etc.
  year_built       integer CHECK (year_built BETWEEN 1800 AND 2100),
  living_area      integer CHECK (living_area >= 0),
  lot_area         integer CHECK (lot_area >= 0),
  image_url        text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_properties_addr
  ON properties (lower(address), lower(city), lower(state), zip);

CREATE INDEX IF NOT EXISTS idx_properties_centroid
  ON properties USING GIST (parcel_centroid);

CREATE INDEX IF NOT EXISTS idx_properties_geom
  ON properties USING GIST (parcel_geom);
