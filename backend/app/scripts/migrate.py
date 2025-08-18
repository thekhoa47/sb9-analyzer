import os, glob, pathlib
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

ENV_PATH = pathlib.Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH) # loads backend/.env

engine = create_engine(os.environ["DATABASE_URL"], future=True)

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[1] / "migrations"

def ensure_table(conn):
    conn.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
          version     text PRIMARY KEY,
          applied_at  timestamptz NOT NULL DEFAULT now()
        );
    """)

def applied_versions(conn):
    rows = conn.execute(text("SELECT version FROM schema_migrations")).fetchall()
    return {r[0] for r in rows}

def apply_sql_file(conn, path: pathlib.Path):
    sql = path.read_text()
    # Use driver-level execution to allow multiple statements per file.
    conn.exec_driver_sql(sql)

def main():
    files = sorted(glob.glob(str(MIGRATIONS_DIR / "*.sql")))
    if not files:
        print(f"No .sql files found in {MIGRATIONS_DIR}")
        return

    with engine.begin() as conn:
        ensure_table(conn)
        done = applied_versions(conn)

        for path_str in files:
            path = pathlib.Path(path_str)
            version = path.stem  # e.g. "0001_init"
            if version in done:
                continue
            print(f"→ Applying {version} ...")
            apply_sql_file(conn, path)
            conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:v)"),
                {"v": version},
            )
            print(f"✓ {version} applied")

if __name__ == "__main__":
    main()
