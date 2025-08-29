-- Enable needed extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- CREATE EXTENSION IF NOT EXISTS postgis; -- if you want PostGIS here

-- Enums
DO $$ BEGIN
  CREATE TYPE notification_channel AS ENUM ('sms', 'email', 'messenger');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE notification_status AS ENUM ('sent', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE TYPE sb9_label AS ENUM ('YES','NO','UNCERTAIN');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
