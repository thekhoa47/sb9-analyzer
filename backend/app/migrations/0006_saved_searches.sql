CREATE TABLE IF NOT EXISTS saved_searches (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name           varchar(100) NOT NULL,

  city           varchar(80)  NOT NULL,
  radius_miles   integer      NOT NULL DEFAULT 10,
  beds_min       integer      NOT NULL DEFAULT 3,
  baths_min      integer      NOT NULL DEFAULT 2,
  max_price      integer,

  criteria_json  jsonb,
  cursor_iso     varchar(40),

  client_id      uuid REFERENCES clients(id) ON DELETE SET NULL,

  created_at     timestamptz NOT NULL DEFAULT now(),
  updated_at     timestamptz
);
