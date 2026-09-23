"""衣物管理：上传、AI 识别、CRUD、筛选。"""
import json
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import UPLOAD_DIR
from ..database import get_conn, now_str, row_to_item
from ..schemas import ClothingConfirm, ClothingUpdate
from ..services import ai_service

router = APIRouter(prefix="/api/clothing", tags=["clothing"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/upload")
async def upload_and_recognize(file: UploadFile = File(...)):
    """上传图片 → 保存 → AI 识别，返回识别结果供用户确认。"""
    ext = ("." + file.filename.rsplit(".", 1)[-1].lower()) if "." in file.filename else ".jpg"
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "仅支持 jpg/png/webp 图片")
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    path = UPLOAD_DIR / filename
    content = await file.read()
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(400, "图片不能超过 15MB")
    path.write_bytes(content)

    recognized = ai_service.recognize_clothing(str(path))
    recognized["image_path"] = f"/uploads/{filename}"
    return recognized


@router.post("")
def create_item(payload: ClothingConfirm):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO clothing_items
               (name, category, color, color_hex, style_tags, season, warmth,
                image_path, description, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (payload.name, payload.category, payload.color, payload.color_hex,
             json.dumps(payload.style_tags, ensure_ascii=False), payload.season,
             payload.warmth, payload.image_path, payload.description, now_str()),
        )
        row = conn.execute("SELECT * FROM clothing_items WHERE id=?",
                           (cur.lastrowid,)).fetchone()
        return row_to_item(row)


@router.get("")
def list_items(category: str = None, season: str = None):
    sql, params = "SELECT * FROM clothing_items", []
    conds = []
    if category:
        conds.append("category=?"); params.append(category)
    if season:
        conds.append("(season=? OR season='四季')"); params.append(season)
    if conds:
        sql += " WHERE " + " AND ".join(conds)
    sql += " ORDER BY created_at DESC"
    with get_conn() as conn:
        return [row_to_item(r) for r in conn.execute(sql, params).fetchall()]


@router.put("/{item_id}")
def update_item(item_id: int, payload: ClothingUpdate):
    fields, params = [], []
    for k, v in payload.dict(exclude_none=True).items():
        if k == "style_tags":
            v = json.dumps(v, ensure_ascii=False)
        fields.append(f"{k}=?"); params.append(v)
    if not fields:
        raise HTTPException(400, "没有要更新的字段")
    params.append(item_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE clothing_items SET {', '.join(fields)} WHERE id=?", params)
        row = conn.execute("SELECT * FROM clothing_items WHERE id=?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(404, "衣物不存在")
        return row_to_item(row)


@router.delete("/{item_id}")
def delete_item(item_id: int):
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM clothing_items WHERE id=?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "衣物不存在")
        return {"ok": True}
