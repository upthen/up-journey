"""Pydantic v2 schemas：管理端入参 + 展示端出参。"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


# ---------- 管理端入参 ----------

class MemberIn(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    nickname: str | None = Field(default=None, max_length=32)
    is_child: bool = False


class TagIn(BaseModel):
    name: str = Field(min_length=1, max_length=16)


class TripCityIn(BaseModel):
    """境内传 city_code；境外 city_code 为空、传 city_name（可选坐标）。"""

    city_code: str | None = None
    city_name: str | None = Field(default=None, max_length=32)
    lng: float | None = None
    lat: float | None = None

    @model_validator(mode="after")
    def check(self) -> "TripCityIn":
        if not self.city_code and not self.city_name:
            raise ValueError("境内城市须填 city_code，境外城市须填 city_name")
        if self.lng is not None and not -180 <= self.lng <= 180:
            raise ValueError("lng 超出范围")
        if self.lat is not None and not -90 <= self.lat <= 90:
            raise ValueError("lat 超出范围")
        return self


class AttractionIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    city_code: str | None = None
    album_rel_path: str | None = Field(default=None, max_length=255)
    lng: float | None = None
    lat: float | None = None
    note: str | None = Field(default=None, max_length=255)


class TripDayIn(BaseModel):
    day_index: int | None = None  # 缺省按数组顺序 1..n
    date: date
    title: str | None = Field(default=None, max_length=128)
    note: str | None = Field(default=None, max_length=500)


class TripIn(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    slug: str | None = Field(default=None, min_length=1, max_length=64)
    start_date: date
    end_date: date
    summary: str | None = Field(default=None, max_length=500)
    content: str | None = None
    cover_photo: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, max_length=32)
    status: Literal["draft", "published"] = "draft"
    cities: list[TripCityIn] = Field(default_factory=list)
    attractions: list[AttractionIn] = Field(default_factory=list)
    days: list[TripDayIn] = Field(default_factory=list)
    member_ids: list[int] = Field(default_factory=list)
    tag_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_dates(self) -> "TripIn":
        if self.end_date < self.start_date:
            raise ValueError("end_date 不能早于 start_date")
        return self


class MemberPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=32)
    nickname: str | None = Field(default=None, max_length=32)
    is_child: bool | None = None


# ---------- 出参 ----------

class MemberOut(BaseModel):
    id: int
    name: str
    nickname: str | None
    is_child: bool


class TagOut(BaseModel):
    id: int
    name: str


class CityOut(BaseModel):
    code: str
    name: str
    province_code: str
    province_name: str
    level: int
    lng: float
    lat: float


class TripCityOut(BaseModel):
    city_code: str | None
    city_name: str | None
    lng: float | None
    lat: float | None
    sort_order: int
    display: str  # 昆明 / 京都


class DayOut(BaseModel):
    day_index: int
    date: date
    title: str | None
    note: str | None


class AttractionOut(BaseModel):
    id: int
    name: str
    city_code: str | None
    city_display: str | None  # 云南 · 昆明（无城市关联时为 None）
    album_rel_path: str | None
    lng: float | None
    lat: float | None
    resolved_lng: float | None  = None  # 精调坐标或城市中心；无城市关联时 None
    resolved_lat: float | None = None
    note: str | None


class GalleryGroupOut(BaseModel):
    attraction: str
    album_dir: str
    count: int
    photos: list[str]


class TripCardOut(BaseModel):
    id: int
    slug: str
    title: str
    start_date: date
    end_date: date
    year: int
    days_count: int  # 行程天数（end-start+1）
    summary: str | None
    cover_photo: str | None
    country: str | None
    status: str
    tags: list[TagOut]
    members: list[MemberOut]
    route: list[str]  # 昆明 → 大理 / 京都（有序展示名）
    trip_days: list[DayOut]


class TripDetailOut(TripCardOut):
    content: str | None
    attractions: list[AttractionOut]
    cities: list[TripCityOut]
    gallery: list[GalleryGroupOut]
    photo_count: int
    prev: dict | None = None  # {slug, title}
    next: dict | None = None


class StatsOut(BaseModel):
    years: int  # 旅行年数 = 当前自然年 − 首次旅行年份
    provinces: int
    cities: int
    attractions: int
    countries: int
    trips: int
    days: int  # 累计旅行天数
    with_kids: int  # 带娃出行次数


class SpotOut(BaseModel):
    name: str
    year: int
    lng: float
    lat: float
    city: str  # 云南 · 昆明
    photo_count: int
    note: str | None
    trip_slug: str
    trip_title: str
    photos: list[str]  # 前 3 张（相册相对路径）


class RouteOut(BaseModel):
    year: int
    trip_slug: str
    trip_title: str
    coords: list[list[float]]


class TimelineYearOut(BaseModel):
    year: int
    trip_count: int
    total_days: int


class AbroadTripOut(BaseModel):
    year: int
    title: str
    slug: str
    country: str


class FootprintsOut(BaseModel):
    years: list[int]
    provinces: dict[str, int]  # GeoJSON 省份名 → 到访次数（trip 去重）
    provinces_by_year: dict[int, dict[str, int]] = {}  # 年份 → 省份 → 到访 trip 数（#16）
    spots: list[SpotOut]
    routes: list[RouteOut]
    timeline: list[TimelineYearOut]
    abroad_trips: list[AbroadTripOut] = []  # 境外行程：中国地图上没有点位，需要单独的入口（#16）


class MetaOut(BaseModel):
    members: list[MemberOut]
    tags: list[TagOut]


class AlbumDirOut(BaseModel):
    path: str  # 相对路径
    name: str


class AlbumOut(BaseModel):
    current: str
    parent: str | None
    dirs: list[AlbumDirOut]
    photos: list[str]  # 图片文件相对路径
