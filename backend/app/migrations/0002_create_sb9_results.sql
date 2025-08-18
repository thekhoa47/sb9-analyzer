DO $$ BEGIN
  CREATE TYPE sb9_label AS ENUM ('YES','NO','UNCERTAIN');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS sb9_results (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id      uuid NOT NULL REFERENCES properties(id) ON DELETE CASCADE UNIQUE,
  predicted_label  sb9_label NOT NULL,
  human_label      sb9_label,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz
);

CREATE INDEX IF NOT EXISTS idx_sb9_results_predicted
  ON sb9_results (predicted_label);

CREATE INDEX IF NOT EXISTS idx_sb9_results_human
  ON sb9_results (human_label);

CREATE INDEX IF NOT EXISTS idx_sb9_results_created
  ON sb9_results (property_id, created_at DESC);
