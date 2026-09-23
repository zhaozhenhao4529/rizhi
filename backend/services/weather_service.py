"""天气服务：Open-Meteo（无需 key），失败时返回兜底数据。"""
import httpx

from ..config import DEFAULT_CITY

WMO_CODES = {
    0: ("晴", "☀️"), 1: ("大部晴朗", "🌤️"), 2: ("局部多云", "⛅"),
    3: ("阴", "☁️"), 45: ("雾", "🌫️"), 48: ("雾凇", "🌫️"),
    51: ("毛毛雨", "🌦️"), 53: ("毛毛雨", "🌦️"), 55: ("毛毛雨", "🌧️"),
    61: ("小雨", "🌧️"), 63: ("中雨", "🌧️"), 65: ("大雨", "🌧️"),
    66: ("冻雨", "🌧️"), 67: ("冻雨", "🌧️"),
    71: ("小雪", "🌨️"), 73: ("中雪", "🌨️"), 75: ("大雪", "❄️"),
    77: ("雪粒", "❄️"), 80: ("阵雨", "🌦️"), 81: ("阵雨", "🌧️"),
    82: ("暴雨", "⛈️"), 85: ("阵雪", "🌨️"), 86: ("阵雪", "❄️"),
    95: ("雷阵雨", "⛈️"), 96: ("雷阵雨伴冰雹", "⛈️"), 99: ("雷阵雨伴冰雹", "⛈️"),
}

_cache = {}


async def get_weather(city: str = None) -> dict:
    city = (city or DEFAULT_CITY).strip()
    if city in _cache:
        return _cache[city]
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            geo = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "language": "zh"},
            )
            results = geo.json().get("results")
            if not results:
                raise ValueError(f"找不到城市: {city}")
            lat, lon = results[0]["latitude"], results[0]["longitude"]
            real_name = results[0].get("name", city)

            fc = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,weather_code,relative_humidity_2m",
                    "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                    "timezone": "auto", "forecast_days": 1,
                },
            )
            data = fc.json()
            code = data["current"]["weather_code"]
            desc, icon = WMO_CODES.get(code, ("多云", "🌥️"))
            result = {
                "city": real_name,
                "temp": round(data["current"]["temperature_2m"]),
                "temp_max": round(data["daily"]["temperature_2m_max"][0]),
                "temp_min": round(data["daily"]["temperature_2m_min"][0]),
                "humidity": data["current"].get("relative_humidity_2m"),
                "description": desc, "icon": icon, "live": True,
            }
            _cache[city] = result
            return result
    except Exception as e:
        print(f"[天气] 获取失败，使用兜底数据: {e}")
        return {"city": city, "temp": 22, "temp_max": 26, "temp_min": 16,
                "humidity": 50, "description": "多云", "icon": "⛅", "live": False}
