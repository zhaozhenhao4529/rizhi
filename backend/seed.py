"""演示种子数据 - 生成示例衣物（SVG 占位图 + 合理属性）
运行: python3 seed.py
"""
import os
import database as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# (文件名, 名称, 品类, 子类, 颜色, 风格, 季节, 保暖, 正式, 描述, SVG主体色, SVG类型)
SEED_ITEMS = [
    ("seed_tee_white.svg", "基础款纯棉白T", "上装", "T恤", ["白"], ["休闲", "简约"], ["春", "夏", "秋"], 2, 1, "衣橱万能打底，怎么搭都不会错", "#F5F2EC", "tee"),
    ("seed_shirt_blue.svg", "浅蓝牛津纺衬衫", "上装", "衬衫", ["浅蓝"], ["学院", "简约"], ["春", "秋"], 2, 3, "清爽学院风，单穿内搭都出彩", "#A8C5E0", "shirt"),
    ("seed_sweater_oat.svg", "燕麦色针织毛衣", "上装", "毛衣", ["燕麦"], ["简约", "复古"], ["秋", "冬"], 4, 2, "软糯亲肤，秋冬氛围感担当", "#D9C7A7", "sweater"),
    ("seed_hoodie_gray.svg", "灰色连帽卫衣", "上装", "卫衣", ["灰"], ["休闲", "街头"], ["春", "秋", "冬"], 3, 1, "oversize版型，慵懒随性", "#B8B8BC", "hoodie"),
    ("seed_jeans.svg", "高腰直筒牛仔裤", "下装", "牛仔裤", ["牛仔蓝"], ["休闲", "街头"], ["春", "秋", "冬"], 3, 2, "显腿直的神裤，四季常青款", "#5B7BA6", "jeans"),
    ("seed_pants_black.svg", "黑色西装阔腿裤", "下装", "西裤", ["黑"], ["简约", "正式"], ["春", "秋"], 2, 4, "垂坠感满分，通勤答辩都能打", "#3A3A3E", "trousers"),
    ("seed_skirt.svg", "奶茶色百褶半裙", "下装", "半裙", ["奶茶"], ["甜美", "学院"], ["春", "夏", "秋"], 1, 3, "走路带风，温柔感拉满", "#D4B89A", "skirt"),
    ("seed_coat_denim.svg", "复古牛仔外套", "外套", "牛仔外套", ["牛仔蓝"], ["街头", "复古"], ["春", "秋"], 3, 2, "做旧水洗，叠穿神器", "#6B8CAE", "jacket"),
    ("seed_coat_camel.svg", "驼色呢子大衣", "外套", "大衣", ["驼"], ["简约", "正式"], ["冬"], 5, 4, "气场全开，冬日质感之选", "#B8956A", "coat"),
    ("seed_cardigan.svg", "奶白色针织开衫", "外套", "开衫", ["奶白"], ["甜美", "学院"], ["春", "秋"], 3, 2, "温柔百搭，空调房救星", "#EFE6D8", "cardigan"),
    ("seed_dress_floral.svg", "法式碎花茶歇裙", "连衣裙", "连衣裙", ["米白", "碎花"], ["甜美", "复古"], ["春", "夏"], 1, 3, "V领收腰，约会战袍", "#E8D5C4", "dress"),
    ("seed_dress_black.svg", "黑色针织连衣裙", "连衣裙", "连衣裙", ["黑"], ["简约", "正式"], ["秋", "冬"], 3, 4, "一裙搞定正式场合", "#2E2E32", "dress"),
    ("seed_shoes_white.svg", "经典小白鞋", "鞋子", "运动鞋", ["白"], ["休闲", "简约"], ["春", "夏", "秋", "冬"], 2, 1, "鞋柜C位，万物皆可搭", "#F0EDE6", "sneaker"),
    ("seed_boots.svg", "黑色切尔西短靴", "鞋子", "短靴", ["黑"], ["简约", "复古"], ["秋", "冬"], 3, 3, "修饰腿型，秋冬必备", "#35353A", "boots"),
    ("seed_bag.svg", "焦糖色皮质托特包", "配饰", "包", ["焦糖"], ["简约"], ["春", "夏", "秋", "冬"], 1, 3, "大容量通勤包，质感在线", "#B0703C", "bag"),
    ("seed_beret.svg", "米色羊毛贝雷帽", "配饰", "帽子", ["米"], ["复古", "甜美"], ["秋", "冬"], 2, 2, "法式氛围感点睛之笔", "#E0D3BC", "beret"),
]

SVG_TEMPLATES = {
    "tee": '<path d="M30 25 L15 35 L22 55 L32 50 L32 85 L68 85 L68 50 L78 55 L85 35 L70 25 Q50 38 30 25 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/>',
    "shirt": '<path d="M32 22 L18 32 L24 52 L33 48 L33 86 L67 86 L67 48 L76 52 L82 32 L68 22 L58 30 L50 26 L42 30 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="50" y1="28" x2="50" y2="86" stroke="#8a8378" stroke-width="1.5"/>',
    "sweater": '<path d="M30 28 L16 38 L23 58 L32 54 L32 86 L68 86 L68 54 L77 58 L84 38 L70 28 Q50 40 30 28 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="32" y1="45" x2="68" y2="45" stroke="#8a8378" stroke-width="1" opacity="0.5"/><line x1="32" y1="55" x2="68" y2="55" stroke="#8a8378" stroke-width="1" opacity="0.5"/>',
    "hoodie": '<path d="M30 30 L16 40 L23 60 L32 56 L32 86 L68 86 L68 56 L77 60 L84 40 L70 30 Q62 22 50 22 Q38 22 30 30 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><path d="M40 24 Q50 16 60 24 Q58 32 50 32 Q42 32 40 24 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/>',
    "jeans": '<path d="M32 15 L68 15 L70 50 L64 90 L54 90 L50 55 L46 90 L36 90 L30 50 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="32" y1="24" x2="68" y2="24" stroke="#8a8378" stroke-width="1.5"/>',
    "trousers": '<path d="M33 15 L67 15 L70 90 L56 90 L50 50 L44 90 L30 90 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/>',
    "skirt": '<path d="M35 20 L65 20 L78 85 L22 85 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="42" y1="22" x2="36" y2="83" stroke="#8a8378" stroke-width="1" opacity="0.5"/><line x1="50" y1="22" x2="50" y2="83" stroke="#8a8378" stroke-width="1" opacity="0.5"/><line x1="58" y1="22" x2="64" y2="83" stroke="#8a8378" stroke-width="1" opacity="0.5"/>',
    "jacket": '<path d="M30 24 L14 34 L21 56 L31 51 L31 84 L69 84 L69 51 L79 56 L86 34 L70 24 L58 32 L50 28 L42 32 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="50" y1="30" x2="50" y2="84" stroke="#8a8378" stroke-width="1.5"/>',
    "coat": '<path d="M32 20 L18 30 L24 50 L32 46 L30 92 L70 92 L68 46 L76 50 L82 30 L68 20 L56 28 L50 25 L44 28 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="50" y1="28" x2="50" y2="92" stroke="#8a8378" stroke-width="1.5"/>',
    "cardigan": '<path d="M32 26 L18 36 L25 56 L33 52 L33 84 L67 84 L67 52 L75 56 L82 36 L68 26 L50 34 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="50" y1="34" x2="50" y2="84" stroke="#8a8378" stroke-width="1.5"/>',
    "dress": '<path d="M38 15 L62 15 L66 35 L74 88 L26 88 L34 35 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><path d="M38 15 Q50 26 62 15" fill="none" stroke="#8a8378" stroke-width="1.5"/>',
    "sneaker": '<path d="M18 62 Q18 50 30 48 L48 46 Q66 46 74 52 Q84 58 84 66 L84 72 L18 72 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="18" y1="66" x2="84" y2="66" stroke="#8a8378" stroke-width="1.5"/>',
    "boots": '<path d="M34 20 L62 20 L62 55 Q74 58 74 68 L74 74 L22 74 L22 68 Q22 58 34 55 Z" fill="{c}" stroke="#8a8378" stroke-width="2"/><line x1="22" y1="68" x2="74" y2="68" stroke="#8a8378" stroke-width="1.5"/>',
    "bag": '<rect x="26" y="38" width="48" height="40" rx="6" fill="{c}" stroke="#8a8378" stroke-width="2"/><path d="M38 38 Q38 24 50 24 Q62 24 62 38" fill="none" stroke="#8a8378" stroke-width="2.5"/>',
    "beret": '<ellipse cx="50" cy="55" rx="32" ry="18" fill="{c}" stroke="#8a8378" stroke-width="2"/><circle cx="50" cy="38" r="4" fill="{c}" stroke="#8a8378" stroke-width="1.5"/>',
}


def make_svg(color: str, kind: str) -> str:
    body = SVG_TEMPLATES.get(kind, SVG_TEMPLATES["tee"]).format(c=color)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="12" fill="#faf6ef"/>
{body}
</svg>'''


def run():
    db.init_db()
    existing = db.list_clothes()
    if existing:
        print(f"衣橱已有 {len(existing)} 件衣物，跳过种子数据（如需重置请删除 wardrobe.db）")
        return
    for (fname, name, cat, sub, colors, tags, season, warmth, formality, desc, color, kind) in SEED_ITEMS:
        svg_path = os.path.join(UPLOAD_DIR, fname)
        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(make_svg(color, kind))
        db.add_clothing({
            "name": name, "category": cat, "subcategory": sub, "colors": colors,
            "style_tags": tags, "season": season, "warmth_level": warmth,
            "formality": formality, "description": desc, "image_path": f"/uploads/{fname}",
        })
        print(f"  ✓ {name}")
    print(f"\n种子数据完成：{len(SEED_ITEMS)} 件示例衣物已入库")


if __name__ == "__main__":
    run()
