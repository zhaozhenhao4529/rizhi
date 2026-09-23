"""天气服务 - Open-Meteo 免费 API（无需 Key）+ 穿衣建议"""
import time
import requests

# 常用城市坐标（避免额外地理编码请求）
CITIES = {
    "北京": (39.9042, 116.4074), "上海": (31.2304, 121.4737),
    "杭州": (30.2741, 120.1551), "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579), "南京": (32.0603, 118.7969),
    "武汉": (30.5928, 114.3055), "成都": (30.5728, 104.0668),
    "西安": (34.3416, 108.9398), "长沙": (28.2282, 112.9388),
    "重庆": (29.5630, 106.5516), "天津": (39.3434, 117.3616),
    "苏州": (31.2989, 120.5853), "青岛": (36.0671, 120.3826),
    "郑州": (34.7466, 113.6254), "合肥": (31.8206, 117.2272),
    "济南": (36.6512, 117.1201), "福州": (26.0745, 119.2965),
    "厦门": (24.4798, 118.0894), "昆明": (24.8801, 102.8329),
    "沈阳": (41.8057, 123.4315), "大连": (38.9140, 121.6147),
    "哈尔滨": (45.8038, 126.5349), "长春": (43.8171, 125.3235),
    "石家庄": (38.0428, 114.5149), "太原": (37.8706, 112.5489),
    "南昌": (28.6820, 115.8579), "贵阳": (26.6470, 106.6302),
    "兰州": (36.0611, 103.8343), "乌鲁木齐": (43.8256, 87.6168),
}

# WMO 天气代码 → (中文描述, 图标)
WMO_CODES = {
    0: ("晴", "☀️"), 1: ("大部晴朗", "🌤️"), 2: ("局部多云", "⛅"), 3: ("阴", "☁️"),
    45: ("雾", "🌫️"), 48: ("冻雾", "🌫️"),
    51: ("毛毛雨", "🌦️"), 53: ("毛毛雨", "🌦️"), 55: ("浓毛毛雨", "🌧️"),
    56: ("冻毛毛雨", "🌧️"), 57: ("冻毛毛雨", "🌧️"),
    61: ("小雨", "🌧️"), 63: ("中雨", "🌧️"), 65: ("大雨", "🌧️"),
    66: ("冻雨", "🌧️"), 67: ("冻雨", "🌧️"),
    71: ("小雪", "🌨️"), 73: ("中雪", "❄️"), 75: ("大雪", "❄️"), 77: ("雪粒", "❄️"),
    80: ("阵雨", "🌦️"), 81: ("强阵雨", "🌧️"), 82: ("暴雨", "⛈️"),
    85: ("阵雪", "🌨️"), 86: ("强阵雪", "❄️"),
    95: ("雷暴", "⛈️"), 96: ("雷暴伴冰雹", "⛈️"), 99: ("雷暴伴冰雹", "⛈️"),
}

_cache = {"data": None, "city": None, "ts": 0}
CACHE_TTL = 1800  # 30 分钟缓存


def _geocode(city: str):
    """城市名 → 坐标，先查内置表，再走 Open-Meteo 地理编码"""
    if city in CITIES:
        return CITIES[city]
    for name, coord in CITIES.items():
        if city and (city in name or name in city):
            return coord
    try:
        resp = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "zh"},
            timeout=8,
        )
        results = resp.json().get("results", [])
        if results:
            return results[0]["latitude"], results[0]["longitude"]
    except Exception as e:
        print(f"[weather] 地理编码失败: {e}")
    return None


def get_weather(city: str = "北京") -> dict:
    global _cache
    now = time.time()
    if _cache["data"] and _cache["city"] == city and now - _cache["ts"] < CACHE_TTL:
        return _cache["data"]

    coord = _geocode(city)
    if not coord:
        return _fallback_weather(city)
    lat, lon = coord
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone": "Asia/Shanghai", "forecast_days": 1,
            },
            timeout=10,
        )
        data = resp.json()
        cur = data["current"]
        daily = data["daily"]
        code = cur.get("weather_code", 0)
        desc, icon = WMO_CODES.get(code, ("多云", "🌥️"))
        temp = cur["temperature_2m"]
        result = {
            "city": city,
            "temperature": temp,
            "feels_like": cur.get("apparent_temperature", temp),
            "temp_max": daily["temperature_2m_max"][0],
            "temp_min": daily["temperature_2m_min"][0],
            "humidity": cur.get("relative_humidity_2m"),
            "wind_speed": cur.get("wind_speed_10m"),
            "description": desc,
            "icon": icon,
            "advice": _dress_advice(temp, code),
            "source": "open-meteo",
        }
        _cache = {"data": result, "city": city, "ts": now}
        return result
    except Exception as e:
        print(f"[weather] 获取失败: {e}")
        return _fallback_weather(city)


def _dress_advice(temp: float, code: int) -> str:
    rainy = code in {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82, 95, 96, 99}
    snowy = code in {71, 73, 75, 77, 85, 86}
    if temp >= 30:
        base = "酷热难耐，短袖短裤安排上，注意防晒补水"
    elif temp >= 26:
        base = "天气偏热，T恤+薄裤正合适"
    elif temp >= 20:
        base = "舒适宜人的温度，单穿长袖或薄外套都可以"
    elif temp >= 15:
        base = "微凉，建议带一件薄外套或针织开衫"
    elif temp >= 10:
        base = "明显转凉，毛衣+外套的组合该出场了"
    elif temp >= 5:
        base = "寒意十足，呢子大衣或厚外套安排上"
    else:
        base = "严寒天气，羽绒服+围巾，注意保暖"
    if rainy:
        base += "；有雨，记得带伞，鞋子选防水的"
    elif snowy:
        base += "；有雪，穿防滑保暖的靴子"
    return base


def _fallback_weather(city: str) -> dict:
    """离线兜底数据"""
    return {
        "city": city, "temperature": 22, "feels_like": 22,
        "temp_max": 26, "temp_min": 17, "humidity": 55, "wind_speed": 8,
        "description": "多云", "icon": "⛅",
        "advice": "舒适宜人的温度，单穿长袖或薄外套都可以",
        "source": "fallback",
    }
