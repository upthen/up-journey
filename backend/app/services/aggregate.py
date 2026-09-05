"""聚合服务：统计口径（docs/database.md）、足迹地图数据、旅行序列化。"""

import re
from datetime import date
from urllib.parse import unquote

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..models import Attraction, City, FamilyMember, Tag, Trip, TripCity
from ..schemas import (
    AbroadTripOut,
    AttractionOut,
    DayOut,
    FootprintsOut,
    GalleryGroupOut,
    MemberOut,
    RouteOut,
    SpotOut,
    StatsOut,
    TagOut,
    TimelineYearOut,
    TripCardOut,
    TripCityOut,
    TripDetailOut,
)
from ..utils import city_display, city_short
from .photos import scan_album


def _trip_days_count(trip: Trip) -> int:
    return (trip.end_date - trip.start_date).days + 1


def member_out(m: FamilyMember) -> MemberOut:
    return MemberOut.model_validate(m, from_attributes=True)


def tag_out(t: Tag) -> TagOut:
    return TagOut.model_validate(t, from_attributes=True)


def filter_trips(trips: list[Trip], year: int | None, tag: str | None) -> list[Trip]:
    """公开/管理列表共用的年份 + 标签过滤。"""
    if year is not None:
        trips = [t for t in trips if t.start_date.year == year]
    if tag is not None:
        trips = [t for t in trips if any(tg.name == tag for tg in t.tags)]
    return trips


def _resolved(own: float | None, fallback: float | None) -> float | None:
    """坐标回退：精调坐标优先，否则（城市中心等）回退值。"""
    return own if own is not None else fallback


_CONTENT_IMG_RE = re.compile(r"photos/(?:thumb|full)\?path=([^\"'\s>&]+)")


def _first_content_photo(content: str | None) -> str | None:
    """正文 HTML 里插入的第一张相册图（「相册插图」写入的 /photos/{size}?path= 链接）。"""
    if not content:
        return None
    m = _CONTENT_IMG_RE.search(content)
    return unquote(m.group(1)) if m else None


def _fallback_cover(trip: Trip) -> str | None:
    """卡片封面兜底：未手动选封面时，取第一个配置了相册的景点的首图，否则取正文首图。"""
    for a in trip.attractions:
        if a.album_rel_path:
            photos = scan_album(a.album_rel_path)
            if photos:
                return photos[0]
    return _first_content_photo(trip.content)


def trip_card(trip: Trip) -> TripCardOut:
    return TripCardOut(
        id=trip.id,
        slug=trip.slug,
        title=trip.title,
        start_date=trip.start_date,
        end_date=trip.end_date,
        year=trip.start_date.year,
        days_count=_trip_days_count(trip),
        summary=trip.summary,
        cover_photo=trip.cover_photo or _fallback_cover(trip),
        country=trip.country,
        status=trip.status,
        tags=[tag_out(t) for t in trip.tags],
        members=[member_out(m) for m in trip.members],
        route=[tc_display(tc) for tc in trip.cities],
        trip_days=[DayOut(day_index=d.day_index, date=d.date, title=d.title, note=d.note) for d in trip.days],
    )


def tc_display(tc: TripCity) -> str:
    if tc.city:
        return city_short(tc.city.name)
    return tc.city_name or "?"


def attraction_out(a: Attraction) -> AttractionOut:
    resolved_lng = _resolved(a.lng, a.city.lng if a.city else None)
    resolved_lat = _resolved(a.lat, a.city.lat if a.city else None)
    return AttractionOut(
        id=a.id,
        name=a.name,
        city_code=a.city_code,
        city_display=city_display(a.city.province_name, a.city.name) if a.city else None,
        album_rel_path=a.album_rel_path,
        lng=a.lng,
        lat=a.lat,
        resolved_lng=resolved_lng,
        resolved_lat=resolved_lat,
        note=a.note,
    )


def trip_detail(trip: Trip) -> TripDetailOut:
    settings = get_settings()
    gallery: list[GalleryGroupOut] = []
    photo_total = 0
    seen_dirs: set[str] = set()
    for a in trip.attractions:
        if a.album_rel_path and a.album_rel_path not in seen_dirs:
            seen_dirs.add(a.album_rel_path)
            photos = scan_album(a.album_rel_path, settings)
            gallery.append(
                GalleryGroupOut(attraction=a.name, album_dir=a.album_rel_path, count=len(photos), photos=photos)
            )
            photo_total += len(photos)
    card = trip_card(trip)
    detail = TripDetailOut(
        **card.model_dump(),
        content=trip.content,
        attractions=[attraction_out(a) for a in trip.attractions],
        cities=[
            TripCityOut(
                city_code=tc.city_code,
                city_name=tc.city_name,
                lng=_resolved(tc.lng, tc.city.lng if tc.city else None),
                lat=_resolved(tc.lat, tc.city.lat if tc.city else None),
                sort_order=tc.sort_order,
                display=tc_display(tc),
            )
            for tc in trip.cities
        ],
        gallery=gallery,
        photo_count=photo_total,
    )
    return detail


def with_prev_next(db: Session, detail: TripDetailOut) -> TripDetailOut:
    """按时间倒序的已发布序列里，补上一篇/下一篇。"""
    rows = db.execute(
        select(Trip.slug, Trip.title, Trip.start_date)
        .where(Trip.status == "published")
        .order_by(Trip.start_date.desc(), Trip.id.desc())
    ).all()
    for i, row in enumerate(rows):
        if row.slug == detail.slug:
            newer = rows[i - 1] if i > 0 else None
            older = rows[i + 1] if i + 1 < len(rows) else None
            detail.prev = {"slug": older.slug, "title": older.title} if older else None
            detail.next = {"slug": newer.slug, "title": newer.title} if newer else None
            break
    return detail


def published_trips(db: Session) -> list[Trip]:
    return list(
        db.scalars(
            select(Trip)
            .where(Trip.status == "published")
            .options(
                selectinload(Trip.tags),
                selectinload(Trip.members),
                selectinload(Trip.cities).selectinload(TripCity.city),
                selectinload(Trip.days),
                selectinload(Trip.attractions),
            )
            .order_by(Trip.start_date.desc(), Trip.id.desc())
        ).all()
    )


def compute_stats(db: Session, today: date | None = None) -> StatsOut:
    """统计口径见 docs/database.md：只计已发布旅行。"""
    today = today or date.today()
    trips = published_trips(db)

    # 「走过的年头」= 首末行程年份闭区间跨度；用当前年计算会在数据停更后虚涨（#18）
    year_list = [t.start_date.year for t in trips]
    years = max(year_list) - min(year_list) + 1 if year_list else 0

    province_codes: set[str] = set()
    city_codes: set[str] = set()
    for t in trips:
        for tc in t.cities:
            if tc.city_code:
                province_codes.add(tc.city.province_code)
                city_codes.add(tc.city_code)

    spot_pairs: set[tuple[str, str]] = set()
    for t in trips:
        for a in t.attractions:
            if a.city_code:
                spot_pairs.add((a.city_code, a.name))

    countries = len({t.country for t in trips if t.country})
    if city_codes:  # 境内（去过任一字典城市）算中国 1 个
        countries += 1

    child_ids = set(db.scalars(select(FamilyMember.id).where(FamilyMember.is_child.is_(True))))
    with_kids = sum(1 for t in trips if child_ids & {m.id for m in t.members})

    return StatsOut(
        years=years,
        provinces=len(province_codes),
        cities=len(city_codes),
        attractions=len(spot_pairs),
        countries=countries,
        trips=len(trips),
        days=sum(_trip_days_count(t) for t in trips),
        with_kids=with_kids,
    )


def compute_footprints(db: Session) -> FootprintsOut:
    """足迹地图数据：省份到访热力、景点涟漪点（含年份/照片数/一句话回忆）、旅行路线、编年聚合。

    境外点不上中国地图（世界图层属 v2），故只聚合 city_code 非空的境内足迹。
    """
    settings = get_settings()
    trips = published_trips(db)

    province_hits: dict[str, set[int]] = {}
    province_year_hits: dict[int, dict[str, set[int]]] = {}
    for t in trips:
        for tc in t.cities:
            if tc.city_code and tc.city:
                province_hits.setdefault(tc.city.province_name, set()).add(t.id)
                province_year_hits.setdefault(t.start_date.year, {}).setdefault(tc.city.province_name, set()).add(t.id)

    spots: list[SpotOut] = []
    routes: list[RouteOut] = []
    trips_by_year: dict[int, int] = {}
    days_by_year: dict[int, int] = {}
    for t in trips:
        year = t.start_date.year
        trips_by_year[year] = trips_by_year.get(year, 0) + 1
        days_by_year[year] = days_by_year.get(year, 0) + _trip_days_count(t)

        domestic = [tc for tc in t.cities if tc.city_code and tc.city]
        if len(domestic) >= 2:
            routes.append(
                RouteOut(
                    year=year,
                    trip_slug=t.slug,
                    trip_title=t.title,
                    coords=[
                        [_resolved(tc.lng, tc.city.lng), _resolved(tc.lat, tc.city.lat)] for tc in domestic
                    ],
                )
            )
        for a in t.attractions:
            if not a.city_code or not a.city:
                continue
            photos = scan_album(a.album_rel_path, settings) if a.album_rel_path else []
            spots.append(
                SpotOut(
                    name=a.name,
                    year=year,
                    lng=_resolved(a.lng, a.city.lng),
                    lat=_resolved(a.lat, a.city.lat),
                    city=city_display(a.city.province_name, a.city.name),
                    photo_count=len(photos),
                    note=a.note,
                    trip_slug=t.slug,
                    trip_title=t.title,
                    photos=photos[:3],
                )
            )

    return FootprintsOut(
        years=sorted(trips_by_year, reverse=True),
        provinces={name: len(ids) for name, ids in province_hits.items()},
        provinces_by_year={
            year: {name: len(ids) for name, ids in by_prov.items()}
            for year, by_prov in province_year_hits.items()
        },
        spots=spots,
        routes=routes,
        timeline=[
            TimelineYearOut(year=y, trip_count=trips_by_year[y], total_days=days_by_year[y])
            for y in sorted(trips_by_year, reverse=True)
        ],
        abroad_trips=[
            AbroadTripOut(year=t.start_date.year, title=t.title, slug=t.slug, country=t.country)
            for t in trips
            if t.country
        ],
    )
