"""AI 服务：衣物识别 / 穿搭推荐 / 购物建议。

双模式：
- 真实模式：走 OpenAI 兼容接口（默认阿里云百炼 DashScope，Qwen-VL + Qwen）
- Mock 模式：无 API Key 时自动启用。识别用 Pillow 做真实主色提取，
  推荐用内置规则引擎（温度/场合/色彩搭配规则），保证离线也能完整演示。
"""
import base64
import io
import json
import random
import re

from PIL import Image

from ..config import (AI_API_KEY, AI_BASE_URL, AI_MOCK, TEXT_MODEL,
                      VISION_MODEL)

# ---------------- 颜色体系 ----------------
COLOR_PALETTE = {
    "黑色": "#1a1a1a", "白色": "#f5f5f5", "灰色": "#8c8c8c",
    "米色": "#e8dcc4", "卡其色": "#b8a06e", "棕色": "#7a5230",
    "藏青色": "#22304a", "牛仔蓝": "#4a6fa5", "天蓝色": "#87ceeb",
    "红色": "#c0392b", "粉色": "#f2b8c6", "酒红色": "#722f37",
    "绿色": "#4a7c59", "军绿色": "#5b6248", "黄色": "#e8c547",
    "橙色": "#d97b29", "紫色": "#7d5ba6", "条纹": "#8899aa",
    "花色": "#a08090", "其他": "#999999",
}
NEUTRAL_COLORS = {"黑色", "白色", "灰色", "米色", "卡其色", "藏青色", "牛仔蓝", "棕色"}

CATEGORIES = ["上装", "下装", "外套", "连衣裙", "鞋子", "配饰"]
SEASONS = ["春", "夏", "秋", "冬", "四季"]
STYLE_TAG_POOL = ["简约", "休闲", "运动", "正式", "甜美", "街头", "复古", "学院"]

OCCASION_STYLE = {
    "日常上课": ["休闲", "简约", "学院", "街头"],
    "约会": ["甜美", "简约", "复古", "休闲"],
    "运动健身": ["运动"],
    "面试答辩": ["正式", "简约"],
    "聚会出游": ["街头", "休闲", "甜美", "复古"],
    "宅家休息": ["休闲", "简约", "运动"],
}


# ---------------- 工具函数 ----------------
def _client():
    from openai import OpenAI
    return OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL, timeout=60)


def _extract_json(text: str):
    """从模型输出中提取 JSON（容忍 markdown 代码块包裹）。"""
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if m:
        text = m.group(1)
    start = text.find("{")
    if start == -1:
        start = text.find("[")
    if start == -1:
        raise ValueError(f"模型输出无 JSON: {text[:200]}")
    # 找到与之匹配的结尾
    opener = text[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    for i in range(start, len(text)):
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError(f"JSON 不完整: {text[:200]}")


def dominant_color(image_path: str):
    """用 Pillow 提取图片主色调，映射到最近的颜色名。返回 (颜色名, hex)。"""
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((80, 80))
        # 简单量化取主色
        q = img.quantize(colors=3, method=Image.MEDIANCUT)
        palette = q.getpalette()
        counts = sorted(q.getcolors(), reverse=True)
        r, g, b = palette[counts[0][1] * 3: counts[0][1] * 3 + 3]
        hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)
        # 找最近的颜色名
        def dist(c_hex):
            cr, cg, cb = int(c_hex[1:3], 16), int(c_hex[3:5], 16), int(c_hex[5:7], 16)
            return (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2
        name = min(COLOR_PALETTE, key=lambda n: dist(COLOR_PALETTE[n]))
        return name, hex_code
    except Exception:
        return "其他", "#999999"


def image_to_base64(image_path: str, max_side=768) -> str:
    img = Image.open(image_path).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=82)
    return base64.b64encode(buf.getvalue()).decode()


# ---------------- 1. 衣物识别 ----------------
RECOGNIZE_PROMPT = """你是专业的服装识别助手。请识别图片中的主要衣物，严格返回如下 JSON（不要多余文字）：
{
  "name": "衣物名称，如：白色纯棉T恤",
  "category": "必须是以下之一：上装/下装/外套/连衣裙/鞋子/配饰",
  "color": "主颜色中文名，从：黑色/白色/灰色/米色/卡其色/棕色/藏青色/牛仔蓝/天蓝色/红色/粉色/酒红色/绿色/军绿色/黄色/橙色/紫色/条纹/花色 中选最接近的",
  "style_tags": ["从：简约/休闲/运动/正式/甜美/街头/复古/学院 中选1-3个"],
  "season": "春/夏/秋/冬/四季 之一",
  "warmth": 1到5的整数，1最清凉5最保暖,
  "description": "一句话中文描述这件衣物的款式特点"
}"""


def recognize_clothing(image_path: str) -> dict:
    """识别衣物属性。Mock 模式下主色为真实提取，其余属性随机生成供用户修改。"""
    if not AI_MOCK:
        try:
            b64 = image_to_base64(image_path)
            resp = _client().chat.completions.create(
                model=VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": RECOGNIZE_PROMPT},
                        {"type": "image_url",
                         "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
                temperature=0.2,
            )
            data = _extract_json(resp.choices[0].message.content)
            data = _normalize_recognized(data)
            data["ai_mode"] = "qwen-vl"
            return data
        except Exception as e:
            print(f"[AI] 识别调用失败，降级 Mock: {e}")

    # ---- Mock：真实主色 + 合理随机 ----
    color_name, color_hex = dominant_color(image_path)
    category = random.choice(CATEGORIES)
    season_warmth = {"上装": (random.choice(["春", "夏", "四季"]), random.randint(1, 3)),
                     "下装": ("四季", random.randint(2, 3)),
                     "外套": (random.choice(["秋", "冬"]), random.randint(4, 5)),
                     "连衣裙": (random.choice(["夏", "春"]), random.randint(1, 2)),
                     "鞋子": ("四季", 3),
                     "配饰": ("四季", 1)}
    season, warmth = season_warmth[category]
    tags = random.sample(STYLE_TAG_POOL, k=random.randint(1, 2))
    name = f"{color_name}{random.choice(['休闲', '百搭', '基础款', ''])}{_category_noun(category)}"
    return {
        "name": name, "category": category, "color": color_name,
        "color_hex": color_hex, "style_tags": tags, "season": season,
        "warmth": warmth,
        "description": f"一件{color_name}的{_category_noun(category)}（离线识别模式，接入 Qwen-VL 后自动生成精准描述）",
        "ai_mode": "mock",
    }


def _category_noun(category):
    return {"上装": "上衣", "下装": "裤装", "外套": "外套",
            "连衣裙": "连衣裙", "鞋子": "鞋子", "配饰": "配饰"}[category]


def _normalize_recognized(data: dict) -> dict:
    """清洗模型输出，保证字段合法。"""
    cat = data.get("category", "上装")
    if cat not in CATEGORIES:
        cat = "上装"
    color = data.get("color", "其他")
    if color not in COLOR_PALETTE:
        color = "其他"
    tags = [t for t in (data.get("style_tags") or []) if t in STYLE_TAG_POOL][:3] or ["休闲"]
    season = data.get("season", "四季")
    if season not in SEASONS:
        season = "四季"
    try:
        warmth = max(1, min(5, int(data.get("warmth", 3))))
    except (TypeError, ValueError):
        warmth = 3
    return {
        "name": str(data.get("name", "未命名衣物"))[:30],
        "category": cat, "color": color,
        "color_hex": COLOR_PALETTE[color],
        "style_tags": tags, "season": season, "warmth": warmth,
        "description": str(data.get("description", ""))[:120],
    }


# ---------------- 2. 穿搭推荐 ----------------
def recommend_outfits(items: list, weather: dict, occasion: str) -> dict:
    """根据衣橱、天气、场合生成 2-3 套搭配。"""
    if len(items) < 2:
        return {"outfits": [], "tip": "衣橱里衣物太少啦，先上传几件衣服吧！"}

    if not AI_MOCK:
        try:
            return _recommend_by_llm(items, weather, occasion)
        except Exception as e:
            print(f"[AI] 推荐调用失败，降级规则引擎: {e}")

    return _recommend_by_rules(items, weather, occasion)


def _recommend_by_llm(items, weather, occasion) -> dict:
    catalog = [{
        "id": it["id"], "name": it["name"], "category": it["category"],
        "color": it["color"], "style_tags": it["style_tags"],
        "season": it["season"], "warmth": it["warmth"],
    } for it in items]
    prompt = f"""你是资深穿搭造型师。根据用户的衣橱、天气和场合，搭配出2-3套造型。

【天气】{weather.get('city', '')} {weather.get('description', '')}，气温 {weather.get('temp_min', '?')}~{weather.get('temp_max', '?')}°C
【场合】{occasion}
【衣橱】{json.dumps(catalog, ensure_ascii=False)}

要求：
1. 每套由衣橱中真实存在的衣物 id 组成，搭配要完整（通常含上装+下装+鞋子，连衣裙可替代上装+下装，天冷加外套）
2. 考虑温度（warmth 保暖度）与场合风格匹配
3. 颜色搭配协调
4. 严格返回 JSON：{{"outfits": [{{"title": "造型名称", "item_ids": [id...], "reasoning": "80字内中文搭配理由，说明为什么适合今天"}}], "tip": "一句今日穿搭小贴士"}}"""
    resp = _client().chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    data = _extract_json(resp.choices[0].message.content)
    valid_ids = {it["id"] for it in items}
    outfits = [o for o in data.get("outfits", [])
               if o.get("item_ids") and all(i in valid_ids for i in o["item_ids"])]
    if not outfits:
        raise ValueError("模型返回的搭配无效")
    return {"outfits": outfits[:3], "tip": data.get("tip", ""), "ai_mode": "qwen"}


def _recommend_by_rules(items, weather, occasion) -> dict:
    """规则引擎：温度分层 + 场合风格 + 色彩协调。"""
    t_max = weather.get("temp_max")
    t_min = weather.get("temp_min")
    t_avg = ((t_max or 20) + (t_min or 12)) / 2
    prefer_styles = OCCASION_STYLE.get(occasion, STYLE_TAG_POOL)

    def style_score(it):
        return 2 if set(it["style_tags"]) & set(prefer_styles) else 0

    def warmth_ok(it, lo, hi):
        return lo <= it["warmth"] <= hi

    # 按温度决定保暖度区间与是否需要外套
    if t_avg >= 26:
        w_lo, w_hi, need_coat = 1, 2, False
    elif t_avg >= 20:
        w_lo, w_hi, need_coat = 1, 3, False
    elif t_avg >= 12:
        w_lo, w_hi, need_coat = 2, 4, False
    elif t_avg >= 5:
        w_lo, w_hi, need_coat = 3, 5, True
    else:
        w_lo, w_hi, need_coat = 4, 5, True

    tops = [i for i in items if i["category"] == "上装" and warmth_ok(i, w_lo, w_hi)]
    bottoms = [i for i in items if i["category"] == "下装"]
    dresses = [i for i in items if i["category"] == "连衣裙" and warmth_ok(i, w_lo, w_hi)]
    shoes = [i for i in items if i["category"] == "鞋子"]
    coats = [i for i in items if i["category"] == "外套"]
    accs = [i for i in items if i["category"] == "配饰"]

    def color_harmony(group):
        colors = [g["color"] for g in group]
        vivid = [c for c in colors if c not in NEUTRAL_COLORS]
        return len(vivid) <= 1  # 彩色不超过一个，其余用中性色压住

    combos = []
    # 方案A：连衣裙路线
    for d in sorted(dresses, key=style_score, reverse=True)[:2]:
        for s in (sorted(shoes, key=style_score, reverse=True)[:2] or [None]):
            group = [d] + ([s] if s else [])
            if color_harmony(group):
                combos.append({"base": group, "kind": "dress"})
    # 方案B：上装+下装路线
    for t in sorted(tops, key=style_score, reverse=True)[:3]:
        for b in sorted(bottoms, key=style_score, reverse=True)[:3]:
            for s in (sorted(shoes, key=style_score, reverse=True)[:2] or [None]):
                group = [t, b] + ([s] if s else [])
                if color_harmony(group):
                    combos.append({"base": group, "kind": "set"})

    if not combos:  # 衣橱缺品类时放宽：有什么穿什么
        pool = sorted(items, key=style_score, reverse=True)[:3]
        combos = [{"base": pool, "kind": "set"}]

    random.shuffle(combos)
    picked = combos[:3]
    outfits = []
    for idx, c in enumerate(picked):
        group = list(c["base"])
        coat_added = None
        if need_coat and coats:
            coat_added = sorted(coats, key=style_score, reverse=True)[0]
            group.append(coat_added)
        if accs and random.random() < 0.5:
            group.append(random.choice(accs))
        names = "、".join(g["name"] for g in group)
        main_colors = [g["color"] for g in group]
        vivid = [c2 for c2 in main_colors if c2 not in NEUTRAL_COLORS]
        color_txt = (f"以{vivid[0]}为视觉亮点，其余用中性色过渡" if vivid
                     else "全身中性色系，简约耐看不出错")
        warmth_txt = ("保暖度充足，应对低温" if t_avg < 12 else
                      "轻薄透气，适合温暖天气" if t_avg >= 24 else "薄厚适中，早晚温差也不怕")
        style_hit = set()
        for g in group:
            style_hit |= set(g["style_tags"]) & set(prefer_styles)
        style_txt = f"整体{('、'.join(style_hit)) or '休闲'}风格，契合「{occasion}」场合"
        outfits.append({
            "title": f"Look {idx + 1} · {group[0]['color']}系{('裙装' if c['kind'] == 'dress' else '套装')}",
            "item_ids": [g["id"] for g in group],
            "reasoning": f"{names}。{color_txt}；{warmth_txt}；{style_txt}。",
        })
    tips = [
        "出门前记得看实时天气，温差大可以备一件薄外套。",
        "全身颜色不超过三种，是穿搭不出错的黄金法则。",
        "配饰是提升精致度性价比最高的单品。",
    ]
    return {"outfits": outfits, "tip": random.choice(tips), "ai_mode": "rules"}


# ---------------- 3. 购物建议 ----------------
def shopping_suggestions(items: list) -> dict:
    """分析衣橱缺口，给出购买建议。"""
    if not AI_MOCK:
        try:
            return _suggest_by_llm(items)
        except Exception as e:
            print(f"[AI] 购物建议调用失败，降级规则: {e}")
    return _suggest_by_rules(items)


def _suggest_by_llm(items) -> dict:
    stat = {}
    for it in items:
        stat[it["category"]] = stat.get(it["category"], 0) + 1
    catalog = [{"name": i["name"], "category": i["category"], "color": i["color"],
                "style_tags": i["style_tags"]} for i in items]
    prompt = f"""你是胶囊衣橱规划师。分析用户衣橱的短板，给出3-5条最值得购入的单品建议。

【衣橱品类统计】{json.dumps(stat, ensure_ascii=False)}
【衣物清单】{json.dumps(catalog[:40], ensure_ascii=False)}

严格返回 JSON：{{"analysis": "80字内衣橱整体分析", "suggestions": [{{"item": "建议购入的单品", "reason": "40字内理由", "priority": "高/中/低"}}]}}"""
    resp = _client().chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    data = _extract_json(resp.choices[0].message.content)
    data["ai_mode"] = "qwen"
    return data


def _suggest_by_rules(items) -> dict:
    stat = {}
    colors = set()
    for it in items:
        stat[it["category"]] = stat.get(it["category"], 0) + 1
        colors.add(it["color"])
    suggestions = []
    if stat.get("外套", 0) < 1:
        suggestions.append({"item": "一件百搭外套（牛仔/风衣/西装）",
                            "reason": "衣橱缺少外套，换季和早晚温差时没有搭配层次", "priority": "高"})
    if stat.get("鞋子", 0) < 2:
        suggestions.append({"item": "一双小白鞋 + 一双深色单鞋",
                            "reason": "鞋履是造型完成度的关键，至少需要两双应对不同场合", "priority": "高"})
    if stat.get("上装", 0) < 3:
        suggestions.append({"item": "基础款白T恤 / 衬衫",
                            "reason": "上装是搭配的核心，基础款能与任何下装组合", "priority": "中"})
    if stat.get("下装", 0) < 2:
        suggestions.append({"item": "高腰直筒裤（黑或牛仔蓝）",
                            "reason": "下装不足会限制搭配数量，直筒裤最不挑身材", "priority": "中"})
    if stat.get("配饰", 0) < 1:
        suggestions.append({"item": "简约项链或百搭包包",
                            "reason": "配饰能以最低成本提升整体精致感", "priority": "低"})
    if not (colors & NEUTRAL_COLORS):
        suggestions.append({"item": "中性色（黑/白/米）基础单品",
                            "reason": "衣橱缺少中性色锚点，彩色单品之间难以互相搭配", "priority": "中"})
    if not suggestions:
        suggestions.append({"item": "衣橱结构健康！可以考虑一件设计感单品",
                            "reason": "基础款齐全后，一件亮色或设计款能制造记忆点", "priority": "低"})
    total = len(items)
    analysis = (f"衣橱共 {total} 件单品，覆盖 {len(stat)} 个品类。"
                f"{'品类均衡，搭配空间大。' if len(stat) >= 4 else '品类覆盖不足，优先补齐缺口品类。'}"
                f"（离线分析模式，接入 Qwen 后生成更精准的个性化建议）")
    return {"analysis": analysis, "suggestions": suggestions[:5], "ai_mode": "rules"}
