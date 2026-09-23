"""Pydantic 请求/响应模型。"""
from typing import List, Optional
from pydantic import BaseModel


class ClothingConfirm(BaseModel):
    """上传识别后，用户确认/修改的衣物信息。"""
    name: str
    category: str
    color: str
    color_hex: str = "#999999"
    style_tags: List[str] = []
    season: str = "四季"
    warmth: int = 3
    image_path: str
    description: str = ""


class ClothingUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    color: Optional[str] = None
    color_hex: Optional[str] = None
    style_tags: Optional[List[str]] = None
    season: Optional[str] = None
    warmth: Optional[int] = None
    description: Optional[str] = None


class RecommendRequest(BaseModel):
    occasion: str = "日常上课"
    city: Optional[str] = None       # 为空用默认城市
    date: Optional[str] = None       # 预留：为未来某天推荐


class WearRequest(BaseModel):
    outfit_id: Optional[int] = None
    item_ids: List[int] = []
    occasion: str = ""
    note: str = ""
    date: Optional[str] = None       # 默认今天
