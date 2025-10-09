from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from faker import Faker
from sqlalchemy import delete

import app.models as m  # ORM models package
from app.core.db import SessionLocal


# ---------- Config ----------
CHANNELS = ("EMAIL", "SMS")  # must match your DB enum values exactly


# ---------- Helpers ----------
def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SeedArgs:
    clients: int
    searches: int
    reset: bool


# ---------- DB ops (SYNC) ----------
def reset_tables(session) -> None:
    """Hard delete in FK-safe order (child -> parent)."""
    # If you don't have SavedSearchMatch, remove that line.
    session.execute(delete(m.SavedSearchField))
    try:
        session.execute(delete(m.SavedSearchMatch))
    except Exception:
        pass
    session.execute(delete(m.SavedSearch))
    session.execute(delete(m.ClientNotificationPreference))
    session.execute(delete(m.Client))
    session.commit()


# ---------- Factories ----------
def make_client(faker: Faker) -> m.Client:
    return m.Client(
        name=faker.name(),
        email="ng.thekhoa@gmai.com",
        phone="+14159363580",  # E.164 string
        address=faker.address().replace("\n", ", "),
        is_active=True,
        created_at=utcnow(),
    )


def make_client_prefs(*, client_id: UUID) -> list[m.ClientNotificationPreference]:
    return [
        m.ClientNotificationPreference(
            client_id=client_id, channel="EMAIL", enabled=True, created_at=utcnow()
        ),
        m.ClientNotificationPreference(
            client_id=client_id, channel="SMS", enabled=True, created_at=utcnow()
        ),
    ]


def make_saved_search(
    faker: Faker,
    *,
    client_id: UUID,
    client_name: str,
) -> m.SavedSearch:
    note = random.choice(
        [
            None,
            "Focus on ADU potential",
            "Must be new built or recently remodeled",
            "Must be single story, ranch-style house",
        ]
    )
    return m.SavedSearch(
        client_id=client_id,
        name=f"Search {client_name}",
        beds_min=2,
        baths_min=2,
        max_price=2_000_000,
        analysis_note=note,
        created_at=utcnow(),
    )


def make_saved_search_fields(
    faker: Faker, *, saved_search_id: UUID
) -> list[m.SavedSearchField]:
    possible_fields: list[tuple[str, str]] = [
        ("city", "Fullerton"),
        ("zip", "92835"),
        ("property_sub_type", "Single Family Residence"),
        ("within_radius", 10),
        ("garage_spaces", faker.random_int(min=1, max=2)),
        ("lot_size", 10_000),
        ("living_area", 2000),
    ]

    rows: list[m.SavedSearchField] = []
    for search_field, value in possible_fields:
        rows.append(
            m.SavedSearchField(
                saved_search_id=saved_search_id,
                search_field=search_field,
                value=str(value),
                created_at=utcnow(),
            )
        )
    return rows


# ---------- Seeder (SYNC) ----------
def seed(
    *,
    num_clients: int,
    num_searches: int,
    reset: bool,
) -> dict[str, int]:
    faker = Faker()

    created_clients = 0
    created_prefs = 0
    created_searches = 0
    created_fields = 0

    session = SessionLocal()
    try:
        if reset:
            print("Resetting tables…")
            reset_tables(session)

        # 1) Clients
        print("Creating clients…")
        clients: list[m.Client] = [make_client(faker) for _ in range(num_clients)]
        session.add_all(clients)
        session.flush()  # get client IDs
        created_clients += len(clients)

        # 2) Preferences per client
        print("Creating clients' preferences…")
        prefs: list[m.ClientNotificationPreference] = []
        for client in clients:
            prefs.extend(make_client_prefs(client_id=client.id))
        session.add_all(prefs)
        created_prefs += len(prefs)

        # 3) Saved searches
        print("Creating saved searches…")
        searches: list[m.SavedSearch] = []
        for index, client in enumerate(clients, start=1):
            for i in range(1, num_searches + 1):
                saved_search = make_saved_search(
                    faker, client_id=client.id, client_name=f"{client.name}-{index}-{i}"
                )
                session.add(saved_search)
                searches.append(saved_search)
        session.flush()  # get saved_search IDs
        created_searches += len(searches)

        # 4) Fields for each search
        print("Creating saved search fields…")
        fields: list[m.SavedSearchField] = []
        for search in searches:
            rows = make_saved_search_fields(faker, saved_search_id=search.id)
            session.add_all(rows)
            fields.extend(rows)
        created_fields += len(fields)

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {
        "clients": created_clients,
        "preferences": created_prefs,
        "saved_searches": created_searches,
        "saved_search_fields": created_fields,
    }


# ---------- CLI ----------
def parse_args() -> SeedArgs:
    p = argparse.ArgumentParser(
        description="Seed database with fake clients & searches."
    )
    p.add_argument(
        "--clients", type=int, default=1, help="Number of clients to create."
    )
    p.add_argument(
        "--searches", type=int, default=1, help="Number of searches per client."
    )
    p.add_argument(
        "--reset", action="store_true", help="Truncate/DELETE existing rows first."
    )
    ns = p.parse_args()
    return SeedArgs(ns.clients, ns.searches, ns.reset)


def main() -> None:
    args = parse_args()
    result = seed(
        num_clients=args.clients,
        num_searches=args.searches,
        reset=args.reset,
    )
    print("Seed complete:", result)


if __name__ == "__main__":
    main()
