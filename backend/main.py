"""日知 - FastAPI 主应用
手机懂今天：出门卡、随手一拍、一日页。
"""
import io
import os
import uuid
import shutil
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

import database as db
import ai_service
import weather as weather_service

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="日知 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 生产模式：托管前端构建产物
DIST_DIR = os.path.join(BASE_DIR, "..", "frontend", "dist")


# ---------------- 请求模型 ----------------

class RecommendReq(BaseModel):
    occasion: str = "日常上课"
    city: str = "北京"
    date: str = ""


class OutfitSaveReq(BaseModel):
    date: str
    occasion: str = "日常"
    item_ids: list[int]
    title: str = ""
    reasoning: str = ""
    weather: dict = {}


class MomentSaveReq(BaseModel):
    date: str
    scene: str = "门口"
    image_path: str = ""
    summary: str = ""
    insights: list = []
    edge_color: str = ""
    edge_hex: str = ""
    ai_powered: bool = False


# ---------------- 系统 ----------------

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "日知",
        "ai": ai_service.ai_status(),
        "time": datetime.now().isoformat(),
    }


# ---------------- 天气 ----------------

@app.get("/api/weather")
def get_weather(city: str = "北京"):
    return weather_service.get_weather(city)


# ---------------- 衣物 ----------------

@app.get("/api/clothes")
def list_clothes(category: str = None):
    return {"items": db.list_clothes(category)}


@app.post("/api/clothes/recognize")
async def recognize(image: UploadFile = File(...)):
    """上传图片 → AI 识别（不落库，返回识别结果供用户确认）"""
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "图片不能超过 10MB")
    result = ai_service.recognize_clothing(
        content, image.filename or "", image.content_type or "image/jpeg"
    )
    # 暂存图片，保存衣物时引用
    ext = os.path.splitext(image.filename or "img.jpg")[1] or ".jpg"
    tmp_name = f"tmp_{uuid.uuid4().hex[:12]}{ext}"
    with open(os.path.join(UPLOAD_DIR, tmp_name), "wb") as f:
        f.write(content)
    result["temp_image"] = f"/uploads/{tmp_name}"
    return result


@app.post("/api/clothes")
def create_clothing(item: dict):
    if not item.get("name") or not item.get("category"):
        raise HTTPException(400, "名称和品类不能为空")
    # 把暂存图转正
    image_path = item.get("image_path", "")
    if image_path.startswith("/uploads/tmp_"):
        old = os.path.join(UPLOAD_DIR, os.path.basename(image_path))
        new_name = os.path.basename(image_path).replace("tmp_", "", 1)
        new = os.path.join(UPLOAD_DIR, new_name)
        if os.path.exists(old):
            shutil.move(old, new)
        image_path = f"/uploads/{new_name}"
    item["image_path"] = image_path
    saved = db.add_clothing(item)
    return saved


@app.get("/api/clothes/{item_id}")
def get_clothing(item_id: int):
    item = db.get_clothing(item_id)
    if not item:
        raise HTTPException(404, "衣物不存在")
    return item


@app.delete("/api/clothes/{item_id}")
def delete_clothing(item_id: int):
    item = db.get_clothing(item_id)
    if not item:
        raise HTTPException(404, "衣物不存在")
    db.delete_clothing(item_id)
    # 清理图片
    if item.get("image_path", "").startswith("/uploads/"):
        p = os.path.join(UPLOAD_DIR, os.path.basename(item["image_path"]))
        if os.path.exists(p):
            os.remove(p)
    return {"ok": True}


# ---------------- 搭配推荐 ----------------

@app.post("/api/recommend")
def recommend(req: RecommendReq):
    wardrobe = db.list_clothes()
    if len(wardrobe) < 2:
        raise HTTPException(400, "衣橱里至少需要 2 件衣物才能生成搭配，先去录入几件吧")
    w = weather_service.get_weather(req.city)
    result = ai_service.recommend_outfits(wardrobe, w, req.occasion)
    result["weather"] = w
    result["occasion"] = req.occasion
    brings = ai_service.suggest_brings(w, req.occasion)
    title = ""
    if result.get("outfits"):
        title = result["outfits"][0].get("title") or ""
    result["brings"] = brings
    result["glance"] = ai_service.glance_line(brings, req.occasion, title)
    return result


@app.get("/api/departure")
def departure(city: str = "北京", occasion: str = "日常上课", title: str = ""):
    """已确认穿着后，单独取天气、要带的东西和腕上一句话。"""
    w = weather_service.get_weather(city)
    brings = ai_service.suggest_brings(w, occasion)
    return {
        "weather": w,
        "brings": brings,
        "glance": ai_service.glance_line(brings, occasion, title),
        "occasion": occasion,
    }


# ---------------- 穿搭记录 ----------------

@app.post("/api/outfits")
def save_outfit(req: OutfitSaveReq):
    saved = db.add_outfit(req.dict())
    db.increment_wear_count(req.item_ids)
    return saved


@app.get("/api/outfits")
def list_outfits(month: str = None):
    outfits = db.list_outfits(month)
    # 附带衣物详情
    for o in outfits:
        o["items"] = [
            {"id": c["id"], "name": c["name"], "category": c["category"], "image_path": c["image_path"]}
            for iid in o.get("item_ids", []) if (c := db.get_clothing(iid))
        ]
    return {"items": outfits}


@app.get("/api/outfits/stats")
def outfit_stats(month: str = None):
    outfits = db.list_outfits(month)
    clothes = db.list_clothes()
    wear_sorted = sorted(clothes, key=lambda c: c.get("wear_count", 0), reverse=True)
    return {
        "total_outfits": len(outfits),
        "active_days": len({o["date"] for o in outfits}),
        "total_clothes": len(clothes),
        "top_items": [
            {"id": c["id"], "name": c["name"], "image_path": c["image_path"], "wear_count": c["wear_count"]}
            for c in wear_sorted[:5] if c.get("wear_count", 0) > 0
        ],
        "category_stats": _category_stats(clothes),
    }


def _category_stats(clothes):
    stats = {}
    for c in clothes:
        stats[c["category"]] = stats.get(c["category"], 0) + 1
    return stats


# ---------------- 随手一拍 / 一日页 ----------------

@app.post("/api/moments/understand")
async def understand_moment(
    image: UploadFile = File(...),
    scene: str = Form("门口"),
    city: str = Form("北京"),
):
    content = await image.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(413, "图片不能超过 10MB")
    wardrobe = db.list_clothes()
    w = weather_service.get_weather(city)
    result = ai_service.understand_moment(
        content, scene, wardrobe, w, image.content_type or "image/jpeg"
    )
    ext = os.path.splitext(image.filename or "img.jpg")[1] or ".jpg"
    if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    tmp_name = f"tmp_{uuid.uuid4().hex[:12]}{ext}"
    with open(os.path.join(UPLOAD_DIR, tmp_name), "wb") as f:
        f.write(content)
    result["temp_image"] = f"/uploads/{tmp_name}"
    result["weather"] = {"description": w.get("description"), "temperature": w.get("temperature")}
    return result


@app.post("/api/moments")
def save_moment(req: MomentSaveReq):
    image_path = req.image_path or ""
    if image_path.startswith("/uploads/tmp_"):
        old = os.path.join(UPLOAD_DIR, os.path.basename(image_path))
        new_name = os.path.basename(image_path).replace("tmp_", "", 1)
        new = os.path.join(UPLOAD_DIR, new_name)
        if os.path.exists(old):
            shutil.move(old, new)
        image_path = f"/uploads/{new_name}"
    saved = db.add_moment({**req.dict(), "image_path": image_path})
    return saved


@app.get("/api/moments")
def list_moments(date: str = None):
    return {"items": db.list_moments(date)}


@app.delete("/api/moments/{moment_id}")
def remove_moment(moment_id: int):
    moments = db.list_moments()
    target = next((m for m in moments if m["id"] == moment_id), None)
    if not target:
        raise HTTPException(404, "这一拍不存在")
    db.delete_moment(moment_id)
    if target.get("image_path", "").startswith("/uploads/"):
        p = os.path.join(UPLOAD_DIR, os.path.basename(target["image_path"]))
        if os.path.exists(p) and not os.path.basename(p).startswith("seed_"):
            os.remove(p)
    return {"ok": True}


def _attach_outfit_items(outfits: list) -> list:
    for o in outfits:
        o["items"] = [
            {"id": c["id"], "name": c["name"], "category": c["category"], "image_path": c["image_path"]}
            for iid in o.get("item_ids", []) if (c := db.get_clothing(iid))
        ]
    return outfits


def _doorway_jpeg() -> bytes:
    """路演用的门口一瞥：真实像素，交给和随手一拍同一条理解链路。"""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (720, 540), (214, 196, 170))
    draw = ImageDraw.Draw(img)
    for y in range(540):
        shade = int(232 - y * 0.18)
        draw.line([(0, y), (720, y)], fill=(shade, shade - 12, shade - 28))
    draw.rectangle([250, 36, 470, 430], fill=(48, 44, 40))
    draw.rectangle([270, 64, 450, 392], fill=(236, 220, 196))
    draw.rectangle([0, 430, 720, 540], fill=(154, 126, 96))
    draw.ellipse([300, 250, 318, 268], fill=(196, 160, 96))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=86)
    return buf.getvalue()


def _drop_upload(image_path: str):
    if not image_path or not image_path.startswith("/uploads/"):
        return
    name = os.path.basename(image_path)
    if name.startswith("seed_"):
        return
    path = os.path.join(UPLOAD_DIR, name)
    if os.path.exists(path):
        os.remove(path)


@app.post("/api/day/rehearse")
def rehearse(city: str = "北京", occasion: str = "日常上课"):
    """按此刻天气重写今天：出门卡 + 门口一拍，直接收成一日页。"""
    date = datetime.now().strftime("%Y-%m-%d")
    db.decrement_wear_count(db.delete_outfits_on_date(date))
    for moment in db.delete_moments_on_date(date):
        _drop_upload(moment.get("image_path") or "")

    wardrobe = db.list_clothes()
    if len(wardrobe) < 2:
        raise HTTPException(400, "衣橱里至少需要 2 件衣物")
    weather = weather_service.get_weather(city)
    result = ai_service.recommend_outfits(wardrobe, weather, occasion)
    outfits = result.get("outfits") or []
    if not outfits:
        raise HTTPException(400, "今天没有拼出一套")
    outfit = outfits[0]
    db.add_outfit({
        "date": date,
        "occasion": occasion,
        "item_ids": outfit.get("item_ids") or [],
        "title": outfit.get("title") or "",
        "reasoning": outfit.get("reasoning") or "",
        "weather": weather,
    })
    db.increment_wear_count(outfit.get("item_ids") or [])

    image_bytes = _doorway_jpeg()
    understood = ai_service.understand_moment(image_bytes, "门口", db.list_clothes(), weather)
    filename = f"door_{uuid.uuid4().hex[:10]}.jpg"
    with open(os.path.join(UPLOAD_DIR, filename), "wb") as f:
        f.write(image_bytes)
    db.add_moment({
        "date": date,
        "scene": "门口",
        "image_path": f"/uploads/{filename}",
        "summary": understood.get("summary") or "",
        "insights": understood.get("insights") or [],
        "edge_color": understood.get("edge_color") or "",
        "edge_hex": understood.get("edge_hex") or "",
        "ai_powered": bool(understood.get("ai_powered")),
    })

    page = ai_service.compose_day(
        date, weather,
        _attach_outfit_items(db.get_outfit_on_date(date)),
        db.list_moments(date),
        db.list_clothes(),
    )
    page["weather"] = weather
    page["rehearsed"] = True
    return page


@app.get("/api/day")
def day_page(date: str = "", city: str = "北京"):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    outfits = _attach_outfit_items(db.get_outfit_on_date(date))
    moments = db.list_moments(date)
    weather = weather_service.get_weather(city)
    page = ai_service.compose_day(date, weather, outfits, moments, db.list_clothes())
    page["weather"] = weather
    return page


# ---------------- 衣橱诊断 ----------------

@app.post("/api/wardrobe/diagnosis")
def diagnose():
    wardrobe = db.list_clothes()
    if not wardrobe:
        raise HTTPException(400, "衣橱还是空的，先录入几件衣物吧")
    return ai_service.diagnose_wardrobe(wardrobe)


# ---------------- 生产模式托管前端 ----------------

if os.path.isdir(DIST_DIR):
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith(("api/", "uploads/")):
            raise HTTPException(404)
        file_path = os.path.join(DIST_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
