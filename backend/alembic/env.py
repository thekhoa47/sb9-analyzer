# alembic/env.py
from __future__ import annotations

import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# ----- make "app/..." importable -----
HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]  # adjust if your structure differs
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ----- logging from alembic.ini -----
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----- import settings (MUST be lightweight) -----
# should load .env internally (e.g., via Pydantic BaseSettings)
from app.core.config import settings  # noqa: E402

# ----- import Base metadata + register all models -----
from app.models.base import Base  # noqa: E402
import app.models.property  # noqa: F401,E402
import app.models.listing  # noqa: F401,E402
import app.models.property_analysis  # noqa: F401,E402
import app.models.client  # noqa: F401,E402
import app.models.saved_search  # noqa: F401,E402
import app.models.saved_search_field  # noqa: F401,E402
import app.models.saved_search_match  # noqa: F401,E402
import app.models.search_listing_analysis  # noqa: F401,E402
import app.models.client_notification_preference  # noqa: F401,E402
import app.models.sent_notification  # noqa: F401,E402

target_metadata = Base.metadata


def _get_db_url() -> str:
    """
    Resolution order:
      1) settings.DATABASE_URL_MIGRATIONS (Supabase direct: 5432, sslmode=require)
      2) `alembic -x dburl=...`
      3) alembic.ini -> sqlalchemy.url
      4) settings.DATABASE_URL (last resort; not ideal for DDL if it's pooled/6543)
    """
    # 1) from settings
    if getattr(settings, "DATABASE_URL_MIGRATIONS", None):
        return settings.DATABASE_URL_MIGRATIONS  # type: ignore[attr-defined]

    # 2) from -x dburl=...
    xargs = context.get_x_argument(as_dictionary=True)
    if xargs and "dburl" in xargs:
        return xargs["dburl"]

    # 3) from alembic.ini
    ini_url = config.get_main_option("sqlalchemy.url")
    if ini_url:
        return ini_url

    # 4) last resort
    if getattr(settings, "DATABASE_URL", None):
        return settings.DATABASE_URL  # type: ignore[attr-defined]

    raise RuntimeError(
        "No DB URL found. Provide settings.DATABASE_URL_MIGRATIONS, "
        "or pass -x dburl=..., or set sqlalchemy.url in alembic.ini."
    )


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in {
        "spatial_ref_sys",
        "geometry_columns",
        "geography_columns",
    }:
        return False
    return True


def run_migrations_offline() -> None:
    url = _get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _get_db_url()
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
