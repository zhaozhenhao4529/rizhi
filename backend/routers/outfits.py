"""穿搭推荐、穿它打卡、日历记录。"""
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ..database import get_conn, now_str, row_to_item, row_to_outfit
from ..schemas import RecommendRequest, WearRequest
from ..services import ai_service, weather_service

router = APIRouter(prefix="/api/outfits", tags=["outfits"])


def _load_items_by_ids(conn, ids):
    if not ids:
        return []
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"SELECT * FROM clothing_items WHERE id IN ({marks})", list(ids)).fetchall()
    by_id = {r["id"]: row_to_item(r) for r in rows}
    return [by_id[i] for i in ids if i in by_id]


@router.post("/recommend")
async def recommend(payload: RecommendRequest):
    weather = await weather_service.get_weather(payload.city)
    with get_conn() as conn:
        items = [row_to_item(r) for r in
                 conn.execute("SELECT * FROM clothing_items").fetchall()]
    result = ai_service.recommend_outfits(items, weather, payload.occasion)

    saved = []
    with get_conn() as conn:
        for o in result.get("outfits", []):
            cur = conn.execute(
                """INSERT INTO outfits (title, occasion, weather_json, item_ids,
                                        reasoning, created_at)
                   VALUES (?,?,?,?,?,?)""",
                (o["title"], payload.occasion, json.dumps(weather, ensure_ascii=False),
                 json.dumps(o["item_ids"]), o["reasoning"], now_str()),
            )
            o["id"] = cur.lastrowid
            o["items"] = _load_items_by_ids(conn, o["item_ids"])
            saved.append(o)
    return {"weather": weather, "occasion": payload.occasion,
            "outfits": saved, "tip": result.get("tip", ""),
            "ai_mode": result.get("ai_mode", "")}


@router.get("/history")
def outfit_history(limit: int = 20):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM outfits ORDER BY created_at DESC LIMIT ?",
            (limit,)).fetchall()
        result = []
        for r in rows:
            o = row_to_outfit(r)
            o["items"] = _load_items_by_ids(conn, o["item_ids"])
            result.append(o)
        return result


@router.post("/wear")
def wear_today(payload: WearRequest):
    date = payload.date or datetime.now().strftime("%Y-%m-%d")
    item_ids = payload.item_ids
    if payload.outfit_id and not item_ids:
        with get_conn() as conn:
            row = conn.execute("SELECT item_ids FROM outfits WHERE id=?",
                               (payload.outfit_id,)).fetchone()
            if row:
                item_ids = json.loads(row["item_ids"])
    if not item_ids:
        raise HTTPException(400, "没有记录任何衣物")
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO wear_records (date, outfit_id, item_ids, occasion, note, created_at)
               VALUES (?,?,?,?,?,?)""",
            (date, payload.outfit_id, json.dumps(item_ids),
             payload.occasion, payload.note, now_str()),
        )
        marks = ",".join("?" * len(item_ids))
        conn.execute(
            f"UPDATE clothing_items SET wear_count = wear_count + 1 WHERE id IN ({marks})",
            list(item_ids))
    return {"ok": True, "date": date}


@router.get("/calendar")
def calendar(month: str = None):
    """月历数据：month 格式 2026-09，默认当月。"""
    month = month or datetime.now().strftime("%Y-%m")
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM wear_records WHERE date LIKE ? ORDER BY date",
            (f"{month}-%",)).fetchall()
        days = {}
        for r in rows:
            d = dict(r)
            d["item_ids"] = json.loads(d["item_ids"])
            d["items"] = _load_items_by_ids(conn, d["item_ids"])
            days.setdefault(d["date"], []).append(d)
        return {"month": month, "days": days}
