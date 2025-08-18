BEGIN;

DROP INDEX IF EXISTS ux_properties_addr;

-- Add a real UNIQUE constraint on the raw columns.
-- This enforces uniqueness for exact (case-sensitive) tuples.
ALTER TABLE properties
  ADD CONSTRAINT ux_properties_addr UNIQUE (address, city, state, zip);

COMMIT;