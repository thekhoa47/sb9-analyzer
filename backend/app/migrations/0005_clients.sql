CREATE TABLE IF NOT EXISTS clients (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name             varchar(120) NOT NULL,
  email            varchar(255),
  phone            varchar(32),
  messenger_psid   varchar(64),

  sms_opt_in       boolean NOT NULL DEFAULT true,
  email_opt_in     boolean NOT NULL DEFAULT true,
  messenger_opt_in boolean NOT NULL DEFAULT false,

  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz,

  CONSTRAINT ck_clients_name_not_empty CHECK (name <> '')
);
