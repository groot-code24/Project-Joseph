import os
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SEED_SQL = SCRIPT_DIR / "seed.sql"


def resolve_db_path() -> Path:
    raw = os.environ.get("DB_PATH", "./data/novamart.db")
    p = Path(raw)
    if p.is_absolute():
        return p
    return (PROJECT_ROOT / p).resolve()


def main() -> int:
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        already_seeded = False
        try:
            cur.execute("SELECT COUNT(*) FROM customers")
            if cur.fetchone()[0] > 0:
                already_seeded = True
        except sqlite3.OperationalError:
            already_seeded = False

        if already_seeded:
            print("Database already seeded, skipping.")
            return 0

        seed_sql = SEED_SQL.read_text(encoding="utf-8")
        conn.executescript(seed_sql)
        conn.commit()

        counts = {}
        for table in ("customers", "orders", "refund_requests"):
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
    finally:
        conn.close()

    print("")
    print(f"✅ Database initialized: {db_path}")
    print("")
    print("Table          Rows")
    print("──────────     ────")
    print(f"customers      {counts['customers']:>4}")
    print(f"orders         {counts['orders']:>4}")
    print(f"refund_reqs    {counts['refund_requests']:>4}")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(main())
