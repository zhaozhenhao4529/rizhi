"""SQLite 数据访问层 - 日知"""
import sqlite3
import json
import os
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wardrobe.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS clothes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    subcategory TEXT DEFAULT '',
    colors TEXT DEFAULT '[]',
    style_tags TEXT DEFAULT '[]',
    season TEXT DEFAULT '[]',
    warmth_level INTEGER DEFAULT 3,
    formality INTEGER DEFAULT 2,
    description TEXT DEFAULT '',
    image_path TEXT DEFAULT '',
    wear_count INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS outfits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    occasion TEXT DEFAULT '日常',
    item_ids TEXT DEFAULT '[]',
    title TEXT DEFAULT '',
    reasoning TEXT DEFAULT '',
    weather TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS moments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    scene TEXT DEFAULT '生活碎片',
    image_path TEXT DEFAULT '',
    summary TEXT DEFAULT '',
    insights TEXT DEFAULT '[]',
    edge_color TEXT DEFAULT '',
    edge_hex TEXT DEFAULT '',
    ai_powered INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

JSON_FIELDS = {"colors", "style_tags", "season", "item_ids", "weather", "insights"}


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row):
    d = dict(row)
    for f in JSON_FIELDS:
        if f in d and isinstance(d[f], str):
            try:
                d[f] = json.loads(d[f])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ---------------- 衣物 ----------------

def add_clothing(item: dict) -> dict:
    fields = ["name", "category", "subcategory", "colors", "style_tags",
              "season", "warmth_level", "formality", "description", "image_path"]
    values = []
    for f in fields:
        v = item.get(f)
        if f in JSON_FIELDS and not isinstance(v, str):
            v = json.dumps(v if v is not None else [], ensure_ascii=False)
        values.append(v)
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO clothes ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            values,
        )
        row = conn.execute("SELECT * FROM clothes WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)


def list_clothes(category: str = None) -> list:
    with get_conn() as conn:
        if category and category != "全部":
            rows = conn.execute(
                "SELECT * FROM clothes WHERE category = ? ORDER BY created_at DESC", (category,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM clothes ORDER BY created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]


def get_clothing(item_id: int) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM clothes WHERE id = ?", (item_id,)).fetchone()
        return _row_to_dict(row) if row else None


def delete_clothing(item_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM clothes WHERE id = ?", (item_id,))
        return cur.rowcount > 0


def increment_wear_count(item_ids: list):
    with get_conn() as conn:
        for iid in item_ids:
            conn.execute("UPDATE clothes SET wear_count = wear_count + 1 WHERE id = ?", (iid,))


def decrement_wear_count(item_ids: list):
    with get_conn() as conn:
        for iid in item_ids:
            conn.execute(
                "UPDATE clothes SET wear_count = MAX(wear_count - 1, 0) WHERE id = ?",
                (iid,),
            )


def delete_outfits_on_date(date: str) -> list:
    outfits = get_outfit_on_date(date)
    item_ids = []
    for outfit in outfits:
        item_ids.extend(outfit.get("item_ids") or [])
    with get_conn() as conn:
        conn.execute("DELETE FROM outfits WHERE date = ?", (date,))
    return item_ids


def delete_moments_on_date(date: str) -> list:
    moments = list_moments(date)
    with get_conn() as conn:
        conn.execute("DELETE FROM moments WHERE date = ?", (date,))
    return moments


# ---------------- 穿搭记录 ----------------

def add_outfit(outfit: dict) -> dict:
    fields = ["date", "occasion", "item_ids", "title", "reasoning", "weather"]
    values = []
    for f in fields:
        v = outfit.get(f)
        if f in JSON_FIELDS and not isinstance(v, str):
            v = json.dumps(v if v is not None else ([] if f == "item_ids" else {}), ensure_ascii=False)
        values.append(v)
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO outfits ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            values,
        )
        row = conn.execute("SELECT * FROM outfits WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)


def list_outfits(month: str = None) -> list:
    with get_conn() as conn:
        if month:
            rows = conn.execute(
                "SELECT * FROM outfits WHERE date LIKE ? ORDER BY date DESC, created_at DESC", (f"{month}%",)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM outfits ORDER BY date DESC, created_at DESC").fetchall()
        return [_row_to_dict(r) for r in rows]


def get_outfit_on_date(date: str) -> list:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM outfits WHERE date = ? ORDER BY created_at DESC", (date,)
        ).fetchall()
        return [_row_to_dict(r) for r in rows]


# ---------------- 生活碎片 ----------------

def add_moment(moment: dict) -> dict:
    fields = ["date", "scene", "image_path", "summary", "insights", "edge_color", "edge_hex", "ai_powered"]
    values = []
    for f in fields:
        v = moment.get(f)
        if f in JSON_FIELDS and not isinstance(v, str):
            v = json.dumps(v if v is not None else [], ensure_ascii=False)
        if f == "ai_powered":
            v = 1 if v else 0
        values.append(v)
    with get_conn() as conn:
        cur = conn.execute(
            f"INSERT INTO moments ({', '.join(fields)}) VALUES ({', '.join(['?'] * len(fields))})",
            values,
        )
        row = conn.execute("SELECT * FROM moments WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _row_to_dict(row)


def list_moments(date: str = None) -> list:
    with get_conn() as conn:
        if date:
            rows = conn.execute(
                "SELECT * FROM moments WHERE date = ? ORDER BY created_at ASC", (date,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM moments ORDER BY created_at DESC").fetchall()
        items = [_row_to_dict(r) for r in rows]
        for item in items:
            item["ai_powered"] = bool(item.get("ai_powered"))
        return items


def delete_moment(moment_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM moments WHERE id = ?", (moment_id,))
        return cur.rowcount > 0
