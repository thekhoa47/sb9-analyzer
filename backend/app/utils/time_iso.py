from datetime import datetime, timezone, timedelta

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def hours_ago_iso(h: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=h)).isoformat()
