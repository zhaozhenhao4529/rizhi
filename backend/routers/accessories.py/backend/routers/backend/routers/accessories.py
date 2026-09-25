from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import os
import uuid
from datetime import datetime

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database import get_db

router = APIRouter(prefix="/accessories", tags=["accessories"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "accessories")
os.makedirs(UPLOAD_DIR, exist_ok=True)

STYLE_COMPATIBILITY = {
    "休闲": ["休闲", "街头", "百搭", "运动"],
    "街头": ["街头", "休闲", "百搭"],
    "轻熟": ["轻熟", "优雅", "百搭", "休闲"],
    "优雅": ["优雅", "正式", "轻熟", "百搭"],
    "正式": ["正式", "优雅", "百搭"],
    "运动": ["运动", "休闲", "百搭"],
}

MATERIAL_DIALOGUE = {
    "棉": ["金属", "帆布", "编织", "木质"],
    "麻": ["木质", "编织", "亚铜"],
    "牛仔": ["金属", "皮质", "帆布"],
    "真丝": ["珍珠", "金银", "宝石"],
    "羊毛": ["金银", "珍珠", "皮质"],
    "西装面料": ["金银", "珍珠", "腕表"],
    "尼龙": ["金属", "塑料"],
    "机能面料": ["金属链条", "科技感"],
}

OCCASION_RULES = {
    "面试": {"max_visual_weight": 1, "message": "面试场合配饰越低调越好，建议腕表或简约耳钉"},
    "答辩": {"max_visual_weight": 1, "message": "答辩需要专业感，避免配饰分散注意力"},
    "运动": {"max_visual_weight": 2, "message": "运动以安全舒适为主，建议运动手表或发带"},
    "约会": {"max_visual_weight": 3, "message": "约会可以增加一件「小心机」配饰，但只限一件"},
    "聚会": {"max_visual_weight": 3, "message": "聚会可以适当亮眼，选择一件视觉焦点配饰"},
    "日常上课": {"max_visual_weight": 2, "message": "日常以舒适为主，1-2件简约配饰即可"},
    "周末出游": {"max_visual_weight": 3, "message": "出游可以休闲随性，帆布包+帽子都很合适"},
}

def generate_suggestion(outfit_style, occasion, recommendations, forbidden, total_items):
    lines = [f"今天是**{outfit_style}**风格穿搭。"]
    if total_items == 0:
        lines.append("你还没有添加配饰，先去「我的配饰」页面添加几件吧！")
        return "\n\n".join(lines)
    
    occasion_info = OCCASION_RULES.get(occasion, {})
    if occasion_info.get("message"):
        lines.append(f"💡 {occasion_info['message']}")
    lines.append("")
    
    if recommendations:
        lines.append("**建议搭配：**")
        for rec in recommendations[:3]:
            lines.append(f"✅ {rec['name']} — {rec.get('reason', '风格呼应')}")
    
    if forbidden:
        lines.append("")
        lines.append("**不太建议：**")
        for f in forbidden[:2]:
            lines.append(f"❌ {f['name']} — {f.get('reason', '风格不搭')}")
    
    if not recommendations:
        lines.append("今天这身建议暂时不戴配饰，保持简约。")
    
    return "\n".join(lines)

def match_offline(accessories, outfit_style, outfit_materials, outfit_colors, occasion):
    occasion_rule = OCCASION_RULES.get(occasion, {})
    max_weight = occasion_rule.get("max_visual_weight", 3)
    
    outfit_materials_list = outfit_materials.split(",") if outfit_materials else ["棉"]
    compatible_materials = set()
    for m in outfit_materials_list:
        m = m.strip()
        for key, mats in MATERIAL_DIALOGUE.items():
            if key in m:
                compatible_materials.update(mats)
    if not compatible_materials:
        compatible_materials = {"金属", "百搭"}
    
    compatible_styles = STYLE_COMPATIBILITY.get(outfit_style, ["百搭"])
    
    recommendations = []
    forbidden = []
    
    for acc in accessories:
        score = 0
        reasons = []
        
        if acc["style"] in compatible_styles:
            score += 50
            reasons.append(f"{acc['style']}风格和穿搭统一")
        elif acc["style"] == "百搭":
            score += 30
            reasons.append("百搭款不容易出错")
        else:
            score -= 20
            reasons.append(f"{acc['style']}风格和{outfit_style}不搭")
        
        if acc["material"] in compatible_materials:
            score += 20
            reasons.append(f"{acc['material']}材质和面料呼应")
        
        if acc["visual_weight"] > max_weight:
            score = 0
            reasons.append(f"{occasion}场合不适合太夸张的配饰")
            forbidden.append({"id": acc["id"], "name": acc["name"], "reason": f"{occasion}场合建议低调", "score": score})
            continue
        
        outfit_colors_list = outfit_colors.split(",") if outfit_colors else []
        if len(outfit_colors_list) >= 3 and acc["visual_weight"] >= 2:
            score -= 10
            reasons.append("全身颜色较多，配饰建议低调")
        
        if score >= 40:
            recommendations.append({**acc, "score": score, "reason": "，".join(reasons[:2])})
        elif score <= 0:
            forbidden.append({**acc, "reason": "，".join(reasons[:2]), "score": score})
    
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    final_recommend = []
    total_weight = 0
    for rec in recommendations:
        if total_weight + rec["visual_weight"] <= 4:
            final_recommend.append(rec)
            total_weight += rec["visual_weight"]
        if len(final_recommend) >= 3:
            break
    
    return final_recommend, forbidden

@router.post("/upload")
async def upload_accessory(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: str = Form(...),
    style: str = Form("百搭"),
    material: str = Form("金属"),
    color: str = Form(""),
    visual_weight: int = Form(1)
):
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(400, "只支持 jpg/png/webp 格式")
    
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        INSERT INTO accessories (name, category, style, material, color, visual_weight, image_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, style, material, color, visual_weight, filename, datetime.now().isoformat()))
    db.commit()
    
    return {"id": cursor.lastrowid, "name": name, "category": category, "style": style, "material": material, "color": color, "visual_weight": visual_weight, "image_url": f"/uploads/accessories/{filename}"}

@router.get("/list")
async def list_accessories(category: Optional[str] = None):
    db = get_db()
    cursor = db.cursor()
    if category and category != "全部":
        cursor.execute("SELECT * FROM accessories WHERE category = ? ORDER BY created_at DESC", (category,))
    else:
        cursor.execute("SELECT * FROM accessories ORDER BY created_at DESC")
    
    items = cursor.fetchall()
    return {"items": [{"id": r["id"], "name": r["name"], "category": r["category"], "style": r["style"], "material": r["material"], "color": r["color"], "visual_weight": r["visual_weight"], "image_url": f"/uploads/accessories/{r['image_path']}", "created_at": r["created_at"]} for r in items]}

@router.delete("/{accessory_id}")
async def delete_accessory(accessory_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT image_path FROM accessories WHERE id = ?", (accessory_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, "配饰不存在")
    
    filepath = os.path.join(UPLOAD_DIR, row["image_path"])
    if os.path.exists(filepath):
        os.remove(filepath)
    
    cursor.execute("DELETE FROM accessories WHERE id = ?", (accessory_id,))
    db.commit()
    return {"success": True}

@router.post("/ai-match")
async def ai_match_accessories(outfit_name: str = Form(...), outfit_style: str = Form(...), outfit_materials: str = Form(""), outfit_colors: str = Form(""), occasion: str = Form("日常")):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM accessories ORDER BY created_at DESC")
    accessories_raw = cursor.fetchall()
    
    if not accessories_raw:
        return {"suggestion": "你还没有添加任何配饰哦，先去「我的配饰」页面添加几件吧！", "recommendations": [], "forbidden": [], "is_offline": True}
    
    accessories = [{"id": r["id"], "name": r["name"], "category": r["category"], "style": r["style"], "material": r["material"], "color": r["color"], "visual_weight": r["visual_weight"], "image_url": f"/uploads/accessories/{r['image_path']}"} for r in accessories_raw]
    
    recommendations, forbidden = match_offline(accessories, outfit_style, outfit_materials, outfit_colors, occasion)
    suggestion = generate_suggestion(outfit_style, occasion, recommendations, forbidden, len(accessories))
    
    return {"suggestion": suggestion, "recommendations": recommendations, "forbidden": forbidden, "occasion": occasion, "outfit": outfit_name, "is_offline": True, "match_count": len(recommendations)}
