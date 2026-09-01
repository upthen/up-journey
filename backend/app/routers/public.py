"""展示端公开 API。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import FamilyMember, Tag, Trip
from ..schemas import FootprintsOut, MetaOut, StatsOut, TripCardOut, TripDetailOut
from ..services.aggregate import (
    compute_footprints,
    compute_stats,
    filter_trips,
    member_out,
    published_trips,
    tag_out,
    trip_card,
    trip_detail,
    with_prev_next,
)
from ..services.photos import PhotoError, get_photo

router = APIRouter(prefix="/api/v1", tags=["public"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(select(1))
    return {"status": "ok"}


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)) -> StatsOut:
    return compute_stats(db)


@router.get("/trips", response_model=list[TripCardOut])
def list_trips(
    year: int | None = Query(default=None),
    tag: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[TripCardOut]:
    trips = filter_trips(published_trips(db), year, tag)
    return [trip_card(t) for t in trips]


@router.get("/trips/{slug}", response_model=TripDetailOut)
def get_trip(slug: str, db: Session = Depends(get_db)) -> TripDetailOut:
    trip = db.scalar(
        select(Trip).where(Trip.slug == slug, Trip.status == "published")
    )
    if trip is None:
        raise HTTPException(status_code=404, detail="游记不存在")
    detail = with_prev_next(db, trip_detail(trip))
    return detail


@router.get("/footprints", response_model=FootprintsOut)
def footprints(db: Session = Depends(get_db)) -> FootprintsOut:
    return compute_footprints(db)


@router.get("/meta", response_model=MetaOut)
def meta(db: Session = Depends(get_db)) -> MetaOut:
    members = db.scalars(select(FamilyMember).order_by(FamilyMember.id)).all()
    tags = db.scalars(select(Tag).order_by(Tag.id)).all()
    return MetaOut(
        members=[member_out(m) for m in members],
        tags=[tag_out(t) for t in tags],
    )


@router.get("/photos/{size}")
def photo(size: str, path: str = Query(...)) -> FileResponse:
    try:
        file = get_photo(size, path, get_settings())
    except PhotoError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e
    return FileResponse(
        file,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
