"""天气、统计、购物建议。"""
from fastapi import APIRouter

from ..database import get_conn, row_to_item
from ..services import ai_service, weather_service

router = APIRouter(prefix="/api", tags=["misc"])


@router.get("/weather")
async def weather(city: str = None):
    return await weather_service.get_weather(city)


@router.get("/stats")
def stats():
    with get_conn() as conn:
        items = [row_to_item(r) for r in
                 conn.execute("SELECT * FROM clothing_items").fetchall()]
        total_wears = conn.execute("SELECT COUNT(*) c FROM wear_records").fetchone()["c"]
    by_cat, by_color = {}, {}
    for it in items:
        by_cat[it["category"]] = by_cat.get(it["category"], 0) + 1
        by_color[it["color"]] = by_color.get(it["color"], 0) + 1
    neglected = sorted([i for i in items if i["wear_count"] == 0],
                       key=lambda x: x["created_at"])[:6]
    return {
        "total_items": len(items),
        "total_wears": total_wears,
        "by_category": by_cat,
        "by_color": by_color,
        "neglected": neglected,
    }


@router.get("/shopping")
def shopping():
    with get_conn() as conn:
        items = [row_to_item(r) for r in
                 conn.execute("SELECT * FROM clothing_items").fetchall()]
    return ai_service.shopping_suggestions(items)
