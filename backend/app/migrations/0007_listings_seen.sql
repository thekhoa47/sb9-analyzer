CREATE TABLE IF NOT EXISTS listings_seen (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_key      varchar(64) NOT NULL,
  first_seen_at    timestamptz NOT NULL DEFAULT now(),
  saved_search_id  uuid NOT NULL REFERENCES saved_searches(id) ON DELETE CASCADE,

  CONSTRAINT uq_listings_seen_key_search UNIQUE (listing_key, saved_search_id)
);

CREATE INDEX IF NOT EXISTS ix_listings_seen_listing_key
  ON listings_seen (listing_key);
