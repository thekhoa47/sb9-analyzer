ALTER TABLE notifications
  ADD COLUMN IF NOT EXISTS created_at timestamptz NOT NULL DEFAULT now(),
  ADD COLUMN IF NOT EXISTS updated_at timestamptz;  -- nullable on purpose
  ALTER COLUMN listing_key TYPE text;
  ALTER COLUMN detail TYPE text;

-- Auto-bump updated_at on any UPDATE
CREATE OR REPLACE FUNCTION set_timestamp() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_notifications_updated_at') THEN
    CREATE TRIGGER trg_notifications_updated_at
    BEFORE UPDATE ON notifications
    FOR EACH ROW EXECUTE FUNCTION set_timestamp();
  END IF;
END$$;
