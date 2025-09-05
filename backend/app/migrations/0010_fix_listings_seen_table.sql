ALTER TABLE listings_seen
  ALTER COLUMN listing_key TYPE text;

-- allow NULL and remove default so inserts can omit or set NULL
ALTER TABLE listings_seen
  ALTER COLUMN updated_at DROP NOT NULL,
  ALTER COLUMN updated_at DROP DEFAULT;

-- keep the trigger that sets updated_at=now() on UPDATE
-- if you dropped it earlier, recreate it:
CREATE OR REPLACE FUNCTION set_timestamp() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_listings_seen_updated_at') THEN
    CREATE TRIGGER trg_listings_seen_updated_at
    BEFORE UPDATE ON listings_seen
    FOR EACH ROW EXECUTE FUNCTION set_timestamp();
  END IF;
END$$;
