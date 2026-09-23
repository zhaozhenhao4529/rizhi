"""AI 服务层 - 通义千问 Qwen-VL 衣物识别 + Qwen 搭配推荐
优先调用阿里云百炼（DashScope）OpenAI 兼容接口；
未配置 DASHSCOPE_API_KEY 或调用失败时，自动降级为本地规则引擎，保证演示永不中断。
"""
import os
import json
import base64
import random
import re

DASHSCOPE_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE = os.environ.get(
    "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
VL_MODEL = os.environ.get("VL_MODEL", "qwen-vl-plus")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen-plus")

CATEGORIES = ["上装", "下装", "外套", "连衣裙", "鞋子", "配饰"]

RECOGNIZE_PROMPT = """你是一位专业的时尚造型师。请识别图片中的这件衣物，严格以 JSON 格式返回（不要输出任何其他文字）：
{
  "name": "简短中文名称，如：奶白色针织开衫",
  "category": "必须是以下之一：上装、下装、外套、连衣裙、鞋子、配饰",
  "subcategory": "具体品类，如：T恤、衬衫、卫衣、牛仔裤、半裙、运动鞋",
  "colors": ["主要颜色，1-2个，中文"],
  "style_tags": ["风格标签，从：休闲、正式、运动、街头、甜美、简约、复古、学院 中选1-3个"],
  "season": ["适合季节，从：春、夏、秋、冬 中选，可多选"],
  "warmth_level": "1-5的整数，1最薄5最保暖",
  "formality": "1-5的整数，1最休闲5最正式",
  "description": "一句话时尚点评，20字以内"
}"""

RECOMMEND_PROMPT = """你是一位专业AI穿搭造型师。根据用户的衣橱清单、天气和场合，设计搭配方案。

【天气】{weather_desc}
【场合】{occasion}
【衣橱清单】（JSON数组，每件含 id/name/category/colors/style_tags/warmth_level(1-5)/formality(1-5)）
{wardrobe_json}

要求：
1. 给出 3 套完整搭配，每套通常包含：上装+下装+鞋子（天冷加外套，连衣裙可替代上装+下装，可选配饰）
2. 只能从衣橱清单中选择，使用真实存在的 id
3. 考虑温度（保暖度匹配）、场合（正式度匹配）、颜色协调
4. 严格返回 JSON（不要输出其他文字）：
{{
  "outfits": [
    {{
      "title": "搭配名称，如：奶油系学院风",
      "item_ids": [衣物id数组],
      "reasoning": "搭配逻辑讲解：为什么适合这个天气和场合，颜色/风格如何协调，80字以内",
      "tip": "一条实用小贴士，如配饰或穿法建议，30字以内"
    }}
  ]
}}"""

DIAGNOSIS_PROMPT = """你是一位衣橱管理顾问。分析用户的衣橱构成，找出穿搭缺口。

【衣橱清单】（JSON数组）
{wardrobe_json}

【统计】共 {total} 件；各类别数量：{category_stats}

要求：严格返回 JSON（不要输出其他文字）：
{{
  "summary": "衣橱整体风格诊断，60字以内",
  "strengths": ["衣橱优势，2-3条，每条15字以内"],
  "gaps": [
    {{
      "missing": "缺少的单品，如：正式场合西装外套",
      "reason": "为什么需要它，30字以内",
      "search_keyword": "电商平台搜索关键词，如：女 西装外套 通勤 简约",
      "priority": "高/中/低"
    }}
  ],
  "advice": "一句购买原则建议，40字以内"
}}
缺口按重要性给出3-5条。"""


# ---------------- Qwen 调用 ----------------

def _get_client():
    from openai import OpenAI
    return OpenAI(api_key=DASHSCOPE_KEY, base_url=DASHSCOPE_BASE, timeout=60)


def _extract_json(text: str) -> dict:
    """从模型输出中稳健提取 JSON"""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start:end + 1]
    return json.loads(text)


def _recognize_with_qwen(image_bytes: bytes, mime: str) -> dict:
    client = _get_client()
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.chat.completions.create(
        model=VL_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": RECOGNIZE_PROMPT},
            ],
        }],
        temperature=0.3,
    )
    result = _extract_json(resp.choices[0].message.content)
    result["ai_powered"] = True
    return _normalize_recognition(result)


def _recommend_with_qwen(wardrobe: list, weather_desc: str, occasion: str) -> dict:
    client = _get_client()
    slim = [{
        "id": c["id"], "name": c["name"], "category": c["category"],
        "subcategory": c.get("subcategory", ""), "colors": c["colors"],
        "style_tags": c["style_tags"], "warmth_level": c["warmth_level"],
        "formality": c["formality"],
    } for c in wardrobe]
    prompt = RECOMMEND_PROMPT.format(
        weather_desc=weather_desc,
        occasion=occasion,
        wardrobe_json=json.dumps(slim, ensure_ascii=False, indent=1),
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    result = _extract_json(resp.choices[0].message.content)
    result["ai_powered"] = True
    return result


def _diagnose_with_qwen(wardrobe: list) -> dict:
    client = _get_client()
    slim = [{
        "name": c["name"], "category": c["category"], "subcategory": c.get("subcategory", ""),
        "colors": c["colors"], "style_tags": c["style_tags"], "formality": c["formality"],
    } for c in wardrobe]
    stats = {}
    for c in wardrobe:
        stats[c["category"]] = stats.get(c["category"], 0) + 1
    prompt = DIAGNOSIS_PROMPT.format(
        wardrobe_json=json.dumps(slim, ensure_ascii=False, indent=1),
        total=len(wardrobe),
        category_stats="、".join(f"{k}{v}件" for k, v in stats.items()),
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    result = _extract_json(resp.choices[0].message.content)
    result["ai_powered"] = True
    return result


# ---------------- 本地规则引擎（兜底，保证演示可用） ----------------

_MOCK_POOL = {
    "上装": [("基础款纯棉T恤", "T恤", ["白"], ["休闲", "简约"], ["春", "夏", "秋"], 2, 1),
             ("条纹海魂衫", "T恤", ["蓝", "白"], ["休闲", "学院"], ["春", "夏"], 2, 1),
             ("燕麦色针织毛衣", "毛衣", ["米"], ["简约", "温柔"], ["秋", "冬"], 4, 2),
             ("浅蓝牛津纺衬衫", "衬衫", ["浅蓝"], ["学院", "简约"], ["春", "秋"], 2, 3)],
    "下装": [("高腰直筒牛仔裤", "牛仔裤", ["蓝"], ["休闲", "街头"], ["春", "秋", "冬"], 3, 2),
             ("黑色西装阔腿裤", "休闲裤", ["黑"], ["简约", "正式"], ["春", "秋"], 2, 4),
             ("卡其色工装裤", "工装裤", ["卡其"], ["街头", "休闲"], ["春", "秋"], 3, 1)],
    "外套": [("复古牛仔外套", "牛仔外套", ["蓝"], ["街头", "复古"], ["春", "秋"], 3, 2),
             ("驼色呢子大衣", "大衣", ["驼"], ["简约", "正式"], ["冬"], 5, 4),
             ("奶白色针织开衫", "开衫", ["米白"], ["温柔", "学院"], ["春", "秋"], 3, 2)],
    "连衣裙": [("法式碎花茶歇裙", "连衣裙", ["米", "碎花"], ["甜美", "复古"], ["春", "夏"], 1, 3),
               ("黑色针织连衣裙", "连衣裙", ["黑"], ["简约", "正式"], ["秋", "冬"], 3, 4)],
    "鞋子": [("经典小白鞋", "运动鞋", ["白"], ["休闲", "简约"], ["春", "夏", "秋", "冬"], 2, 1),
             ("黑色切尔西短靴", "靴子", ["黑"], ["简约", "复古"], ["秋", "冬"], 3, 3),
             ("帆布鞋", "帆布鞋", ["米白"], ["学院", "休闲"], ["春", "夏", "秋"], 1, 1)],
    "配饰": [("焦糖色皮质托特包", "包", ["焦糖"], ["简约"], ["春", "夏", "秋", "冬"], 1, 3),
             ("米色贝雷帽", "帽子", ["米"], ["复古", "甜美"], ["秋", "冬"], 2, 2)],
}


def _normalize_recognition(r: dict) -> dict:
    cat = r.get("category", "上装")
    if cat not in CATEGORIES:
        cat = "上装"
    return {
        "name": str(r.get("name", "未命名衣物"))[:30],
        "category": cat,
        "subcategory": str(r.get("subcategory", ""))[:20],
        "colors": [str(c) for c in (r.get("colors") or ["白"])][:3],
        "style_tags": [str(t) for t in (r.get("style_tags") or ["休闲"])][:3],
        "season": [s for s in (r.get("season") or ["春", "秋"]) if s in "春夏秋冬"] or ["春", "秋"],
        "warmth_level": max(1, min(5, int(r.get("warmth_level", 3) or 3))),
        "formality": max(1, min(5, int(r.get("formality", 2) or 2))),
        "description": str(r.get("description", ""))[:60],
        "ai_powered": r.get("ai_powered", False),
    }


def _mock_recognize(filename: str = "") -> dict:
    """无 API Key 时的本地模拟识别：按文件名关键词 + 随机合理猜测"""
    fname = (filename or "").lower()
    cat = random.choice(list(_MOCK_POOL.keys()))
    kw_map = {"裤": "下装", "jean": "下装", "裙": "连衣裙", "dress": "连衣裙",
              "鞋": "鞋子", "shoe": "鞋子", "boot": "鞋子", "外套": "外套",
              "coat": "外套", "jacket": "外套", "包": "配饰", "bag": "配饰",
              "帽": "配饰", "衫": "上装", "t恤": "上装", "tshirt": "上装", "卫衣": "上装"}
    for kw, c in kw_map.items():
        if kw in fname:
            cat = c
            break
    item = random.choice(_MOCK_POOL[cat])
    return _normalize_recognition({
        "name": item[0], "category": cat, "subcategory": item[1],
        "colors": item[2], "style_tags": item[3], "season": item[4],
        "warmth_level": item[5], "formality": item[6],
        "description": "本地识别模式：接入 Qwen-VL 后可自动精确识别",
        "ai_powered": False,
    })


_OCCASION_FORMALITY = {
    "日常上课": (1, 3), "周末出游": (1, 3), "约会": (2, 4),
    "运动健身": (1, 1), "面试答辩": (4, 5), "聚会派对": (2, 4),
}


def _rule_recommend(wardrobe: list, weather: dict, occasion: str) -> dict:
    """本地规则搭配引擎：温度→保暖度，场合→正式度，品类组合"""
    temp = weather.get("temperature", 22)
    if temp >= 28:
        warmth_range = (1, 2)
    elif temp >= 20:
        warmth_range = (1, 3)
    elif temp >= 12:
        warmth_range = (2, 4)
    elif temp >= 5:
        warmth_range = (3, 5)
    else:
        warmth_range = (4, 5)

    fmin, fmax = _OCCASION_FORMALITY.get(occasion, (1, 3))

    def pick(category, prefer_warmth=None):
        cands = [c for c in wardrobe if c["category"] == category]
        if not cands:
            return None
        def score(c):
            s = 0
            w = c["warmth_level"]
            if warmth_range[0] <= w <= warmth_range[1]:
                s += 3
            if fmin <= c["formality"] <= fmax:
                s += 2
            if occasion == "运动健身" and "运动" in c["style_tags"]:
                s += 3
            s += random.uniform(0, 1.5)
            return s
        return max(cands, key=score)

    outfits = []
    used = set()
    for _ in range(3):
        items = []
        dress = pick("连衣裙")
        use_dress = dress is not None and random.random() < 0.3 and fmin >= 2
        if use_dress:
            items.append(dress)
        else:
            top, bottom = pick("上装"), pick("下装")
            if top:
                items.append(top)
            if bottom:
                items.append(bottom)
        if temp < 18:
            coat = pick("外套")
            if coat and coat["warmth_level"] <= warmth_range[1] + 1:
                items.append(coat)
        shoes = pick("鞋子")
        if shoes:
            items.append(shoes)
        if temp < 24 and random.random() < 0.4:
            acc = pick("配饰")
            if acc and not (temp >= 22 and acc.get("subcategory") == "帽子"):
                items.append(acc)

        ids = tuple(sorted(i["id"] for i in items))
        if len(items) >= 2 and ids not in used:
            used.add(ids)
            names = " + ".join(i["name"] for i in items)
            main_colors = []
            for i in items:
                main_colors.extend(i["colors"])
            if temp >= 28:
                feel = "天热，挑了更薄、更好活动的单品"
            elif temp >= 22:
                feel = "温度舒服，没有再加厚外套"
            elif temp >= 12:
                feel = "有点凉，保暖留在刚好够用"
            else:
                feel = "天冷，把保暖放在前面"
            outfits.append({
                "title": _gen_title(items, occasion),
                "item_ids": list(ids),
                "items": [{"id": i["id"], "name": i["name"], "category": i["category"],
                           "image_path": i["image_path"], "colors": i["colors"]} for i in items],
                "reasoning": f"{occasion}场合，气温约{temp:.0f}℃，{feel}：{names}。整体以{'、'.join(list(dict.fromkeys(main_colors))[:3])}色系为主。",
                "tip": random.choice([
                    "把上衣下摆塞进裤腰，比例更好看。",
                    "可以加一条细腰带强调腰线。",
                    "卷起袖口露出手腕，更显利落。",
                    "同色系袜子能拉长腿部线条。",
                ]),
            })
    return {"outfits": outfits, "ai_powered": False}


def _gen_title(items, occasion):
    tags = []
    for i in items:
        tags.extend(i.get("style_tags", []))
    tag = max(set(tags), key=tags.count) if tags else "休闲"
    return f"{tag}风 · {occasion}穿搭"


def _rule_diagnose(wardrobe: list) -> dict:
    stats = {}
    for c in wardrobe:
        stats[c["category"]] = stats.get(c["category"], 0) + 1
    gaps = []
    if stats.get("外套", 0) < 2:
        gaps.append({"missing": "百搭外套（如西装外套/大衣）", "reason": "外套数量偏少，换季和正式场合不够用",
                     "search_keyword": "西装外套 女 通勤 简约", "priority": "高"})
    if stats.get("鞋子", 0) < 3:
        gaps.append({"missing": "一双正式感单鞋/短靴", "reason": "鞋子选择少，难以应对面试答辩等场合",
                     "search_keyword": "切尔西短靴 百搭", "priority": "中"})
    formal = [c for c in wardrobe if c["formality"] >= 4]
    if len(formal) < 2:
        gaps.append({"missing": "正式场合单品（衬衫/西裤）", "reason": "正式度高的单品不足，面试答辩场景受限",
                     "search_keyword": "白衬衫 女 面试 通勤", "priority": "高"})
    if stats.get("配饰", 0) < 2:
        gaps.append({"missing": "点睛配饰（包/帽子/丝巾）", "reason": "配饰能让基础款搭配瞬间出彩",
                     "search_keyword": "托特包 女 百搭 通勤", "priority": "低"})
    if not gaps:
        gaps.append({"missing": "季节性流行单品", "reason": "衣橱结构完整，可补充当季流行元素保持新鲜感",
                     "search_keyword": "2026秋季流行 穿搭", "priority": "低"})
    return {
        "summary": f"衣橱共{len(wardrobe)}件单品，以休闲日常为主，基础款占比高，搭配自由度不错。",
        "strengths": ["基础款丰富，百搭实穿", "色系以中性色为主，容易组合"],
        "gaps": gaps[:5],
        "advice": "遵循「二八原则」：80%经典基础款 + 20%设计款，少买多搭。",
        "ai_powered": False,
    }


# ---------------- 日知：要带的东西 / 腕上一句话 / 随手一拍 / 一日页 ----------------

_GLANCE_LABEL = {
    "折叠伞": "带伞", "薄外套": "加外套", "围巾": "围巾", "防晒": "防晒",
    "简历": "带简历", "水杯": "水杯", "校园卡": "校园卡", "充电宝": "充电宝", "纸巾": "纸巾",
}
_OCCASION_SHORT = {
    "日常上课": "上课", "约会": "约会", "运动健身": "运动",
    "面试答辩": "面试", "周末出游": "出游", "聚会派对": "聚会",
}
_EDGE_PALETTE = {
    "黑色": "#1a1a1a", "白色": "#f4f1ea", "灰色": "#8c8c8c", "米色": "#e8dcc4",
    "卡其色": "#b8a06e", "棕色": "#7a5230", "藏青": "#22304a", "牛仔蓝": "#4a6fa5",
    "红色": "#c0392b", "粉色": "#f2b8c6", "绿色": "#4a7c59", "黄色": "#e8c547",
    "焦糖": "#b0703c", "燕麦": "#d9c7a7",
}

UNDERSTAND_PROMPT = """你是「日知」，一个理解用户今天生活的伙伴。用户拍了一张「{scene}」。
天气：{weather_desc}
衣橱里已有的单品（只能谈论这些，不要建议购买）：
{wardrobe_json}

请只根据画面和上面的事实，严格返回 JSON：
{{
  "summary": "一句话，40字以内，说明这一眼看见了什么、和今天有什么关系",
  "insights": [
    {{"text": "一条具体提醒，22字以内", "kind": "idle|missing|ready|notice"}}
  ]
}}
insights 给 2 到 4 条。kind：idle 闲置的已有衣物，missing 今天该带但可能没带，ready 已经具备，notice 普通提醒。
不要输出其他文字。"""


def _is_wet(weather: dict) -> bool:
    desc = weather.get("description") or ""
    return any(k in desc for k in ("雨", "雷", "雪"))


def suggest_brings(weather: dict, occasion: str) -> list:
    """根据天气和场合，给出今天出门要带的东西。只谈随身物品，不推销衣服。"""
    brings = []
    desc = weather.get("description") or ""
    temp = weather.get("temperature", 20) or 20
    if _is_wet(weather):
        label = "折叠伞" if "雪" not in desc else "防滑"
        why = f"今天{desc}，出门前放进包侧袋" if label == "折叠伞" else f"今天{desc}，鞋底要抓得住地"
        brings.append({"label": label if label != "防滑" else "防滑鞋", "why": why})
    if temp >= 28:
        brings.append({"label": "防晒", "why": "紫外线强，防晒和补水一起带"})
    elif temp < 8:
        brings.append({"label": "围巾", "why": "气温低，脖子先暖起来"})
    elif temp < 15:
        brings.append({"label": "薄外套", "why": "体感偏凉，带一件能随时穿脱的"})
    extra = {
        "面试答辩": ("简历", "纸质简历和学生证放在最外层"),
        "运动健身": ("水杯", "运动时别等口渴了再找水"),
        "日常上课": ("校园卡", "门禁和食堂都用得上"),
        "约会": ("充电宝", "晚上回来电量容易见底"),
        "周末出游": ("纸巾", "在外面待得久，随手能用上"),
        "聚会派对": ("充电宝", "晚上回来电量容易见底"),
    }.get(occasion)
    if extra:
        brings.append({"label": extra[0], "why": extra[1]})
    # 去重并最多三条
    seen = set()
    unique = []
    for b in brings:
        if b["label"] in seen:
            continue
        seen.add(b["label"])
        unique.append(b)
    return unique[:3]


def glance_line(brings: list, occasion: str, outfit_title: str = "") -> str:
    """腕上只留一句话：要带的、场合、今天这套的气质。"""
    parts = []
    if brings:
        label = brings[0]["label"]
        parts.append(_GLANCE_LABEL.get(label, label))
    parts.append(_OCCASION_SHORT.get(occasion, (occasion or "日常")[:2]))
    title = (outfit_title or "").split("·")[0].strip()
    if title:
        parts.append(title[:6])
    return " · ".join(parts)


def _edge_color(image_bytes: bytes):
    """端侧主色：只在本机用像素估算，不把原图交给模型也能给出色块。"""
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((48, 48))
        pixels = list(img.getdata())
        if not pixels:
            raise ValueError("empty")
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        hex_code = "#{:02x}{:02x}{:02x}".format(r, g, b)

        def dist(c_hex):
            cr, cg, cb = int(c_hex[1:3], 16), int(c_hex[3:5], 16), int(c_hex[5:7], 16)
            return (cr - r) ** 2 + (cg - g) ** 2 + (cb - b) ** 2

        name = min(_EDGE_PALETTE, key=lambda n: dist(_EDGE_PALETTE[n]))
        return name, hex_code
    except Exception:
        return "米色", "#e8dcc4"


def _weather_desc(weather: dict) -> str:
    return (f"{weather.get('city', '')}，{weather.get('description', '多云')}，"
            f"约 {weather.get('temperature', '')}℃")


def _rule_understand(scene: str, wardrobe: list, weather: dict, edge_name: str, edge_hex: str) -> dict:
    desc = weather.get("description") or "多云"
    temp = weather.get("temperature", 20) or 20
    rainy = _is_wet(weather)
    idle = [c for c in wardrobe if int(c.get("wear_count") or 0) == 0]
    worn = sorted(wardrobe, key=lambda c: int(c.get("wear_count") or 0), reverse=True)
    top_worn = worn[0] if worn and int(worn[0].get("wear_count") or 0) > 0 else None
    insights = []

    if scene == "衣柜":
        if idle:
            insights.append({"text": f"「{idle[0]['name']}」还没上过身", "kind": "idle"})
        if len(idle) > 1:
            insights.append({"text": f"「{idle[1]['name']}」也在等第一次穿着", "kind": "idle"})
        if top_worn:
            insights.append({
                "text": f"「{top_worn['name']}」穿过 {top_worn['wear_count']} 次，今天让它歇一歇",
                "kind": "notice",
            })
        coats = [c for c in wardrobe if c.get("category") == "外套"]
        if rainy and coats:
            insights.append({"text": f"有雨，外套先看「{coats[0]['name']}」", "kind": "ready"})
        elif rainy:
            insights.append({"text": "有雨，衣橱里还没有外套", "kind": "missing"})
        summary = f"衣柜这一眼的主色接近{edge_name}。对照的是你已有的 {len(wardrobe)} 件衣服。"
    elif scene == "书包":
        if rainy:
            insights.append({"text": "今天有雨，折叠伞放进夹层", "kind": "missing"})
        else:
            insights.append({"text": f"今天{desc}，不用为天气腾位置", "kind": "ready"})
        bags = [c for c in wardrobe if "包" in (c.get("name") or "") or c.get("subcategory") == "包"]
        if bags:
            insights.append({"text": f"通勤就用已有的「{bags[0]['name']}」", "kind": "ready"})
        insights.append({"text": "校园卡放最外层，进门不用翻包", "kind": "notice"})
        summary = f"书包画面主色接近{edge_name}。要带的东西按今天的{desc}来。"
    elif scene == "桌面":
        insights.append({"text": "穿什么回到出门卡点一次就行", "kind": "notice"})
        if idle:
            insights.append({"text": f"想换风格时，让「{idle[0]['name']}」上身", "kind": "idle"})
        if temp >= 26:
            insights.append({"text": "室内偏暖，厚衣服不必堆在椅背上", "kind": "ready"})
        summary = f"桌面主色接近{edge_name}。这一拍只记住和今天有关的那一句。"
    else:
        if rainy:
            insights.append({"text": "锁门前摸一下包侧袋，伞在不在", "kind": "missing"})
        if temp < 15:
            insights.append({"text": "门口偏凉，薄外套搭在臂上", "kind": "notice"})
        else:
            insights.append({"text": f"大约 {round(temp)}°C，不用在门口再加一层", "kind": "ready"})
        insights.append({"text": "看一眼腕上那句话，带齐再走", "kind": "ready"})
        summary = f"门口这一眼主色接近{edge_name}。出门前要核对的事收成一句。"

    return {
        "scene": scene,
        "summary": summary,
        "insights": insights[:4],
        "edge_color": edge_name,
        "edge_hex": edge_hex,
        "ai_powered": False,
    }


def _understand_with_qwen(image_bytes: bytes, mime: str, scene: str, wardrobe: list, weather: dict) -> dict:
    client = _get_client()
    slim = [{"name": c["name"], "category": c["category"], "wear_count": c.get("wear_count", 0)} for c in wardrobe[:30]]
    prompt = UNDERSTAND_PROMPT.format(
        scene=scene,
        weather_desc=_weather_desc(weather),
        wardrobe_json=json.dumps(slim, ensure_ascii=False),
    )
    b64 = base64.b64encode(image_bytes).decode()
    resp = client.chat.completions.create(
        model=VL_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }],
        temperature=0.4,
    )
    result = _extract_json(resp.choices[0].message.content)
    insights = []
    for item in result.get("insights") or []:
        kind = item.get("kind") if item.get("kind") in {"idle", "missing", "ready", "notice"} else "notice"
        text = str(item.get("text", "")).strip()
        if text:
            insights.append({"text": text[:40], "kind": kind})
    return {
        "scene": scene,
        "summary": str(result.get("summary", "")).strip()[:80],
        "insights": insights[:4],
        "ai_powered": True,
    }


def understand_moment(image_bytes: bytes, scene: str, wardrobe: list, weather: dict, mime: str = "image/jpeg") -> dict:
    if scene not in {"衣柜", "书包", "桌面", "门口"}:
        scene = "门口"
    edge_name, edge_hex = _edge_color(image_bytes)
    result = None
    if DASHSCOPE_KEY:
        try:
            result = _understand_with_qwen(image_bytes, mime, scene, wardrobe, weather)
        except Exception as e:
            print(f"[ai_service] Qwen-VL 理解失败，降级本地模式: {e}")
    if not result or not result.get("summary"):
        result = _rule_understand(scene, wardrobe, weather, edge_name, edge_hex)
    result["edge_color"] = edge_name
    result["edge_hex"] = edge_hex
    result["scene"] = scene
    return result


def compose_day(date: str, weather: dict, outfits: list, moments: list, wardrobe: list) -> dict:
    """一日页只复述今天确认过的穿着和拍过的画面。"""
    outfit = outfits[0] if outfits else None
    occasion = (outfit or {}).get("occasion") or "日常上课"
    title = (outfit or {}).get("title") or ""
    brings = suggest_brings(weather, occasion)
    glance = glance_line(brings, occasion, title)
    temp = weather.get("temperature", 20) or 20
    desc = weather.get("description") or "多云"
    beats = []

    if outfit:
        names = "、".join(i.get("name", "") for i in (outfit.get("items") or [])[:4] if i.get("name"))
        bring_txt = "、".join(b["label"] for b in brings) if brings else "不用额外多带"
        beats.append({
            "slot": "早晨",
            "title": title or "今天这套",
            "text": f"{desc}，大约 {round(temp)}°C。你定了这套：{names or '已选单品'}。出门带上{bring_txt}。",
        })
    else:
        beats.append({
            "slot": "早晨",
            "title": "出门卡还在等你",
            "text": "搭配可以生成。点一次「今天就穿这套」，这一页才会记下你的选择。",
        })

    if moments:
        for m in moments:
            beats.append({
                "slot": "白天",
                "title": f"拍了{m.get('scene') or '生活'}",
                "text": m.get("summary") or "",
                "image_path": m.get("image_path") or "",
                "insights": m.get("insights") or [],
                "edge_color": m.get("edge_color") or "",
                "edge_hex": m.get("edge_hex") or "",
                "moment_id": m.get("id"),
            })
    else:
        beats.append({
            "slot": "白天",
            "title": "还没有随手一拍",
            "text": "拍衣柜、书包、桌面或门口。日知只把和今天有关的几句记进来。",
        })

    idle = [c for c in wardrobe if int(c.get("wear_count") or 0) == 0]
    if outfit and idle:
        tomorrow = f"明天让「{idle[0]['name']}」上身，今天这套先歇一天。"
    elif outfit:
        tomorrow = "明天出门前再看一眼天气，腕上那句话会跟着变。"
    else:
        tomorrow = "先把今天这套定下来，明天的第一句才有对照。"
    if any("伞" in b["label"] for b in brings):
        tomorrow = "伞先留在包侧袋。" + tomorrow

    return {
        "date": date,
        "headline": glance if outfit else "今天还没被记住",
        "glance": glance if outfit else "",
        "tomorrow": tomorrow,
        "closing": "这一页来自你确认过的穿着和拍过的画面。",
        "beats": beats,
        "brings": brings,
        "occasion": occasion,
        "outfit": outfit,
        "has_outfit": bool(outfit),
        "moment_count": len(moments),
        "ai_powered": False,
    }


# ---------------- 对外接口 ----------------

def recognize_clothing(image_bytes: bytes, filename: str = "", mime: str = "image/jpeg") -> dict:
    if DASHSCOPE_KEY:
        try:
            return _recognize_with_qwen(image_bytes, mime)
        except Exception as e:
            print(f"[ai_service] Qwen-VL 识别失败，降级本地模式: {e}")
    return _mock_recognize(filename)


def recommend_outfits(wardrobe: list, weather: dict, occasion: str) -> dict:
    weather_desc = (f"{weather.get('city', '')}，{weather.get('description', '晴')}，"
                    f"气温 {weather.get('temp_min', '')}~{weather.get('temp_max', '')}℃，"
                    f"当前 {weather.get('temperature', '')}℃")
    if DASHSCOPE_KEY and len(wardrobe) >= 2:
        try:
            result = _recommend_with_qwen(wardrobe, weather_desc, occasion)
            # 补充 item 详情
            id_map = {c["id"]: c for c in wardrobe}
            for o in result.get("outfits", []):
                o["items"] = [
                    {"id": c["id"], "name": c["name"], "category": c["category"],
                     "image_path": c["image_path"], "colors": c["colors"]}
                    for iid in o.get("item_ids", []) if (c := id_map.get(iid))
                ]
                o["item_ids"] = [i["id"] for i in o["items"]]
            result["outfits"] = [o for o in result.get("outfits", []) if len(o.get("items", [])) >= 2]
            if result["outfits"]:
                return result
        except Exception as e:
            print(f"[ai_service] Qwen 推荐失败，降级本地模式: {e}")
    return _rule_recommend(wardrobe, weather, occasion)


def diagnose_wardrobe(wardrobe: list) -> dict:
    if DASHSCOPE_KEY and wardrobe:
        try:
            return _diagnose_with_qwen(wardrobe)
        except Exception as e:
            print(f"[ai_service] Qwen 诊断失败，降级本地模式: {e}")
    return _rule_diagnose(wardrobe)


def ai_status() -> dict:
    return {
        "qwen_enabled": bool(DASHSCOPE_KEY),
        "vl_model": VL_MODEL if DASHSCOPE_KEY else None,
        "llm_model": LLM_MODEL if DASHSCOPE_KEY else None,
        "mode": "Qwen 大模型驱动" if DASHSCOPE_KEY else "本地规则引擎（配置 DASHSCOPE_API_KEY 后升级为 Qwen 驱动）",
    }
