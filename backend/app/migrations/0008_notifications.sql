CREATE TABLE IF NOT EXISTS notifications (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  channel          notification_channel NOT NULL,
  status           notification_status  NOT NULL DEFAULT 'sent',
  listing_key      varchar(64) NOT NULL,
  detail           text,

  sent_at          timestamptz NOT NULL DEFAULT now(),

  client_id        uuid REFERENCES clients(id) ON DELETE SET NULL,
  saved_search_id  uuid REFERENCES saved_searches(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS ix_notifications_listing_key
  ON notifications (listing_key);
