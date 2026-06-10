import uuid
from pathlib import Path

import aiosqlite

from config import get_settings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_db_path() -> str:
    raw = get_settings().db_path
    p = Path(raw)
    if p.is_absolute():
        return str(p)
    return str((_PROJECT_ROOT / p).resolve())


DB_PATH = _resolve_db_path()


async def get_db_connection() -> aiosqlite.Connection:
    conn = await aiosqlite.connect(DB_PATH)
    conn.row_factory = aiosqlite.Row
    return conn


async def get_customer(customer_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_order(order_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE order_id = ?", (order_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_orders_for_customer(customer_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM orders WHERE customer_id = ?", (customer_id,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def get_refund_history(customer_id: str, days: int = 90) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT * FROM refund_requests
            WHERE customer_id = ?
              AND requested_at >= datetime('now', '-' || ? || ' days')
              AND status IN ('approved', 'escalated_human')
            ORDER BY requested_at DESC
            """,
            (customer_id, days),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def check_duplicate_refund(order_id: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM refund_requests WHERE order_id = ? AND status != 'pending'",
            (order_id,),
        ) as cur:
            row = await cur.fetchone()
            return bool(row[0] > 0)


async def create_refund_request(
    order_id: str,
    customer_id: str,
    reason: str,
    status: str,
    resolution: str,
    resolved_by: str = "nova-ai",
) -> str:
    request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO refund_requests
              (request_id, order_id, customer_id, reason, requested_at,
               status, resolution, resolved_by, resolved_at)
            VALUES (?, ?, ?, ?, datetime('now'), ?, ?, ?, datetime('now'))
            """,
            (request_id, order_id, customer_id, reason, status, resolution, resolved_by),
        )
        await db.commit()
    return request_id


async def get_all_refund_requests() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT rr.*, o.product_name, o.amount_usd, c.name AS customer_name
            FROM refund_requests rr
            JOIN orders o ON rr.order_id = o.order_id
            JOIN customers c ON rr.customer_id = c.customer_id
            ORDER BY rr.requested_at DESC
            """
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
