-- Add timestamps (idempotent)
ALTER TABLE listings_seen
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();

-- Optional: backfill created_at from first_seen_at if it's earlier
UPDATE listings_seen
SET created_at = first_seen_at
WHERE created_at > first_seen_at;

-- Ensure a trigger keeps updated_at fresh on UPDATE
CREATE OR REPLACE FUNCTION set_timestamp() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'trg_listings_seen_updated_at'
  ) THEN
    CREATE TRIGGER trg_listings_seen_updated_at
    BEFORE UPDATE ON listings_seen
    FOR EACH ROW
    EXECUTE FUNCTION set_timestamp();
  END IF;
END$$;
