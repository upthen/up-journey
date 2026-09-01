"""ORM 模型，与 docs/database.md 的 DDL 蓝本一一对应。

与蓝本的两处刻意差异（迁移为准，蓝本亦注明）：
- status 用 VARCHAR + 应用层校验，避免 MySQL ENUM 与 SQLite 不兼容；
- family_member 增加 is_child：统计口径"带娃出行次数"需要知道成员是否孩子。
坐标列统一用 Float：float64 精度（约 15 位）远超 DECIMAL(9,6)，且 SQLite 无真 DECIMAL，
双方言行为一致。
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import LONGTEXT as MYSQL_LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

# 富文本正文在 MySQL 上用 LONGTEXT（DDL 蓝本），其余方言回退 TEXT
LongText = Text().with_variant(MYSQL_LONGTEXT, "mysql")


class City(Base):
    """城市字典：level 1 = 省级（含直辖市/港澳台），level 2 = 地级市。

    province_name 与前端中国 GeoJSON 的省份 name 严格一致（着色按名称匹配）。
    """

    __tablename__ = "city"

    code: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    province_code: Mapped[str] = mapped_column(String(12), nullable=False)
    province_name: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)


class FamilyMember(Base):
    __tablename__ = "family_member"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(32))
    is_child: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)


class Trip(Base):
    __tablename__ = "trip"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500))
    content: Mapped[str | None] = mapped_column(LongText)  # 富文本 HTML
    cover_photo: Mapped[str | None] = mapped_column(String(255))  # 相册相对路径
    country: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    members: Mapped[list[FamilyMember]] = relationship(
        secondary="trip_member", order_by=FamilyMember.id
    )
    tags: Mapped[list[Tag]] = relationship(secondary="trip_tag", order_by=Tag.id)
    cities: Mapped[list[TripCity]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripCity.sort_order",
    )
    days: Mapped[list[TripDay]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan",
        order_by="TripDay.day_index",
    )
    attractions: Mapped[list[Attraction]] = relationship(
        back_populates="trip", cascade="all, delete-orphan"
    )


class TripMember(Base):
    __tablename__ = "trip_member"

    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True
    )
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("family_member.id", ondelete="CASCADE"), primary_key=True
    )


class TripTag(Base):
    __tablename__ = "trip_tag"

    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True
    )


class TripCity(Base):
    """途经城市（有序）。境内 city_code 非空；境外 city_code 空用自由文本 + 可选坐标。"""

    __tablename__ = "trip_city"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trip.id", ondelete="CASCADE"), nullable=False
    )
    city_code: Mapped[str | None] = mapped_column(String(12), ForeignKey("city.code"))
    city_name: Mapped[str | None] = mapped_column(String(32))  # 境外城市名，如 京都
    lng: Mapped[float | None] = mapped_column(Float)
    lat: Mapped[float | None] = mapped_column(Float)
    sort_order: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)

    trip: Mapped[Trip] = relationship(back_populates="cities")
    city: Mapped[City | None] = relationship()

    __table_args__ = (Index("idx_trip_city", "trip_id", "sort_order"),)


class TripDay(Base):
    __tablename__ = "trip_day"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trip.id", ondelete="CASCADE"), nullable=False
    )
    day_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    title: Mapped[str | None] = mapped_column(String(128))
    note: Mapped[str | None] = mapped_column(String(500))

    trip: Mapped[Trip] = relationship(back_populates="days")

    __table_args__ = (Index("idx_trip_day", "trip_id", "day_index"),)


class Attraction(Base):
    __tablename__ = "attraction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trip_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("trip.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    city_code: Mapped[str | None] = mapped_column(String(12), ForeignKey("city.code"))
    album_rel_path: Mapped[str | None] = mapped_column(String(255))  # 相对 /photos 根
    lng: Mapped[float | None] = mapped_column(Float)  # 空 = 跟随城市中心
    lat: Mapped[float | None] = mapped_column(Float)
    note: Mapped[str | None] = mapped_column(String(255))  # 一句话回忆（故事面板 blurb）

    trip: Mapped[Trip] = relationship(back_populates="attractions")
    city: Mapped[City | None] = relationship()

    __table_args__ = (Index("idx_trip_attraction", "trip_id"),)
