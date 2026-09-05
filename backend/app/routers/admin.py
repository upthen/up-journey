"""管理端 API（`/api/v1/admin/*`）。

v1 局域网无鉴权：所有路由挂在 `require_admin` 依赖下，未来反代公网前
只需在该依赖里启用"管理员密码"校验（spec 安全节），架构不变。
"""

import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import BaseModel

from ..auth import clear_cookie, issue_cookie, verify_request
from ..config import get_settings
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..db import get_db
from ..models import Attraction, City, FamilyMember, Tag, Trip, TripCity, TripDay
from ..schemas import (
    AlbumOut,
    AttractionIn,
    CityOut,
    MemberIn,
    MemberOut,
    MemberPatch,
    TagIn,
    TagOut,
    TripCardOut,
    TripCityIn,
    TripDayIn,
    TripDetailOut,
    TripIn,
)
from ..services.aggregate import filter_trips, member_out, tag_out, trip_card, trip_detail, tc_display
from ..services.photos import PhotoError, list_album
from ..utils import slugify_title

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


async def require_admin(request: Request) -> None:
    """鉴权接缝的落地实现（architecture.md 安全边界节）：
    密码登录后凭 HttpOnly 签名 cookie 访问；未配置密码 = 管理端 503。
    """
    verify_request(request)


# ---------- 管理端会话 ----------

class LoginIn(BaseModel):
    password: str


@router.post("/login")
def admin_login(payload: LoginIn, response: Response) -> dict:
    if not get_settings().admin_password:
        raise HTTPException(status_code=503, detail="管理端密码未配置：在 .env 设置 ADMIN_PASSWORD 后重启")
    if not issue_cookie(response, payload.password):
        # 统一错误口径：不区分"密码错"与"未登录"，避免探测
        raise HTTPException(status_code=401, detail="密码不正确")
    return {"ok": True}


@router.post("/logout")
def admin_logout(response: Response) -> dict:
    clear_cookie(response)
    return {"ok": True}


@router.get("/session")
def admin_session(request: Request) -> dict:
    """前端路由守卫探测：200=已登录；401=未登录；503=未配置密码。"""
    verify_request(request)
    return {"ok": True}


# ---------- 家庭成员 ----------

@router.get("/members", response_model=list[MemberOut], dependencies=[Depends(require_admin)])
def list_members(db: Session = Depends(get_db)) -> list[MemberOut]:
    members = db.scalars(select(FamilyMember).order_by(FamilyMember.id)).all()
    return [member_out(m) for m in members]


@router.post("/members", response_model=MemberOut, status_code=201, dependencies=[Depends(require_admin)])
def create_member(payload: MemberIn, db: Session = Depends(get_db)) -> MemberOut:
    member = FamilyMember(name=payload.name, nickname=payload.nickname, is_child=payload.is_child)
    db.add(member)
    db.commit()
    return member_out(member)


@router.put("/members/{member_id}", response_model=MemberOut, dependencies=[Depends(require_admin)])
def update_member(member_id: int, payload: MemberPatch, db: Session = Depends(get_db)) -> MemberOut:
    member = db.get(FamilyMember, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    if payload.name is not None:
        member.name = payload.name
    if payload.nickname is not None:
        member.nickname = payload.nickname
    if payload.is_child is not None:
        member.is_child = payload.is_child
    db.commit()
    return member_out(member)


@router.delete("/members/{member_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_member(member_id: int, db: Session = Depends(get_db)) -> Response:
    member = db.get(FamilyMember, member_id)
    if member is None:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.delete(member)
    db.commit()
    return Response(status_code=204)


# ---------- 标签 ----------

@router.get("/tags", response_model=list[TagOut], dependencies=[Depends(require_admin)])
def list_tags(db: Session = Depends(get_db)) -> list[TagOut]:
    tags = db.scalars(select(Tag).order_by(Tag.id)).all()
    return [tag_out(t) for t in tags]


@router.post("/tags", response_model=TagOut, status_code=201, dependencies=[Depends(require_admin)])
def create_tag(payload: TagIn, db: Session = Depends(get_db)) -> TagOut:
    if db.scalar(select(Tag).where(Tag.name == payload.name)):
        raise HTTPException(status_code=409, detail="标签已存在")
    tag = Tag(name=payload.name)
    db.add(tag)
    db.commit()
    return tag_out(tag)


@router.put("/tags/{tag_id}", response_model=TagOut, dependencies=[Depends(require_admin)])
def update_tag(tag_id: int, payload: TagIn, db: Session = Depends(get_db)) -> TagOut:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    dup = db.scalar(select(Tag).where(Tag.name == payload.name, Tag.id != tag_id))
    if dup:
        raise HTTPException(status_code=409, detail="标签已存在")
    tag.name = payload.name
    db.commit()
    return TagOut(id=tag.id, name=tag.name)


@router.delete("/tags/{tag_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_tag(tag_id: int, db: Session = Depends(get_db)) -> Response:
    tag = db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    db.commit()
    return Response(status_code=204)


# ---------- 城市字典（级联选择数据源） ----------

@router.get("/cities", response_model=list[CityOut], dependencies=[Depends(require_admin)])
def list_cities(
    province: str | None = Query(default=None),  # 省级 code 过滤其下属市
    level: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[CityOut]:
    stmt = select(City).order_by(City.province_code, City.code)
    if province:
        stmt = stmt.where(City.province_code == province, City.level == 2)
    if level is not None:
        stmt = stmt.where(City.level == level)
    return [CityOut.model_validate(c, from_attributes=True) for c in db.scalars(stmt)]


# ---------- 相册浏览（选图器） ----------

@router.get("/album", response_model=AlbumOut, dependencies=[Depends(require_admin)])
def album(path: str = Query(default="")) -> AlbumOut:
    try:
        return list_album(path, get_settings())
    except PhotoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e


# ---------- 旅行 CRUD ----------

_SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def _unique_slug(db: Session, wished: str, exclude_id: int | None) -> str:
    base = wished
    n = 2
    while True:
        stmt = select(Trip.id).where(Trip.slug == base)
        if exclude_id is not None:
            stmt = stmt.where(Trip.id != exclude_id)
        if db.scalar(stmt) is None:
            return base
        base = f"{wished}-{n}"
        n += 1


def _load(db: Session, trip_id: int) -> Trip:
    trip = db.scalar(
        select(Trip)
        .options(
            selectinload(Trip.tags),
            selectinload(Trip.members),
            selectinload(Trip.cities).selectinload(TripCity.city),
            selectinload(Trip.days),
            selectinload(Trip.attractions),
        )
        .where(Trip.id == trip_id)
    )
    if trip is None:
        raise HTTPException(status_code=404, detail="旅行不存在")
    return trip


def _apply_cities(db: Session, trip: Trip, cities_in: list[TripCityIn]) -> None:
    for order, c in enumerate(cities_in):
        city = None
        if c.city_code:
            city = db.get(City, c.city_code)
            if city is None:
                raise HTTPException(status_code=422, detail=f"未知城市: {c.city_code}")
            if c.city_name:
                raise HTTPException(status_code=422, detail="境内城市只传 city_code")
        trip.cities.append(
            TripCity(
                city_code=c.city_code,
                city_name=c.city_name,
                lng=c.lng,
                lat=c.lat,
                sort_order=order,
            )
        )


def _apply_trip(db: Session, trip: Trip, payload: TripIn) -> None:
    trip.title = payload.title
    trip.start_date = payload.start_date
    trip.end_date = payload.end_date
    trip.summary = payload.summary
    trip.content = payload.content
    trip.cover_photo = payload.cover_photo
    trip.country = payload.country
    trip.status = payload.status

    if payload.slug is not None and payload.slug != trip.slug:
        if not _SLUG_RE.match(payload.slug):
            raise HTTPException(status_code=422, detail="slug 只能包含小写字母、数字和连字符")
        trip.slug = _unique_slug(db, payload.slug, trip.id)
    elif not trip.slug:  # 新建且未指定
        trip.slug = _unique_slug(db, slugify_title(payload.title), trip.id)

    # 嵌套集合整体替换
    trip.cities.clear()
    db.flush()
    _apply_cities(db, trip, payload.cities)

    trip.days.clear()
    db.flush()
    for i, d in enumerate(payload.days, start=1):
        trip.days.append(
            TripDay(day_index=d.day_index if d.day_index is not None else i, date=d.date, title=d.title, note=d.note)
        )

    trip.attractions.clear()
    db.flush()
    for a in payload.attractions:
        if a.city_code and db.get(City, a.city_code) is None:
            raise HTTPException(status_code=422, detail=f"未知景点城市: {a.city_code}")
        trip.attractions.append(
            Attraction(
                name=a.name,
                city_code=a.city_code,
                album_rel_path=a.album_rel_path,
                lng=a.lng,
                lat=a.lat,
                note=a.note,
            )
        )

    members = []
    for mid in dict.fromkeys(payload.member_ids):  # 去重保序
        m = db.get(FamilyMember, mid)
        if m is None:
            raise HTTPException(status_code=422, detail=f"未知成员: {mid}")
        members.append(m)
    trip.members = members

    tags = []
    for tid in dict.fromkeys(payload.tag_ids):
        t = db.get(Tag, tid)
        if t is None:
            raise HTTPException(status_code=422, detail=f"未知标签: {tid}")
        tags.append(t)
    trip.tags = tags


@router.get("/trips", response_model=list[TripCardOut], dependencies=[Depends(require_admin)])
def admin_list_trips(
    year: int | None = Query(default=None),
    tag: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TripCardOut]:
    stmt = (
        select(Trip)
        .options(
            selectinload(Trip.tags),
            selectinload(Trip.members),
            selectinload(Trip.cities).selectinload(TripCity.city),
            selectinload(Trip.days),
        )
        .order_by(Trip.start_date.desc(), Trip.id.desc())
    )
    if status_filter:
        stmt = stmt.where(Trip.status == status_filter)
    trips = db.scalars(stmt).unique().all()
    trips = filter_trips(trips, year, tag)
    if q:
        needle = q.strip().lower()
        trips = [
            t
            for t in trips
            if needle in t.title.lower()
            or needle in (t.summary or "").lower()
            or any(needle in (tc.city.name if tc.city else (tc.city_name or "")).lower() for tc in t.cities)
        ]
    return [trip_card(t) for t in trips]


@router.post("/trips", response_model=TripDetailOut, status_code=201, dependencies=[Depends(require_admin)])
def create_trip(payload: TripIn, db: Session = Depends(get_db)) -> TripDetailOut:
    # 双击/并发提交撞 slug：_unique_slug 是先查后插，窗口内互相看不见，
    # 且 _apply_trip 内部的 flush 就会抛 IntegrityError——try 必须包住整段（#15）。
    # 回滚后强制走自动生成（服务端按已提交态补 -2 后缀）重试一次。
    try:
        trip = Trip()
        _apply_trip(db, trip, payload)
        db.add(trip)
        db.commit()
    except IntegrityError:
        db.rollback()
        trip = Trip()
        _apply_trip(db, trip, payload.model_copy(update={"slug": None}))
        db.add(trip)
        db.commit()
    return trip_detail(_load(db, trip.id))


@router.get("/trips/{trip_id}", response_model=TripDetailOut, dependencies=[Depends(require_admin)])
def admin_get_trip(trip_id: int, db: Session = Depends(get_db)) -> TripDetailOut:
    return trip_detail(_load(db, trip_id))


@router.put("/trips/{trip_id}", response_model=TripDetailOut, dependencies=[Depends(require_admin)])
def update_trip(trip_id: int, payload: TripIn, db: Session = Depends(get_db)) -> TripDetailOut:
    trip = _load(db, trip_id)
    try:
        _apply_trip(db, trip, payload)
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="slug 已被其他旅行占用") from e
    return trip_detail(_load(db, trip.id))


@router.delete("/trips/{trip_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_trip(trip_id: int, db: Session = Depends(get_db)) -> Response:
    trip = _load(db, trip_id)
    db.delete(trip)
    db.commit()
    return Response(status_code=204)
