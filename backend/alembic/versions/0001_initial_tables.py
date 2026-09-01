"""initial tables

Revision ID: 0001
Revises:
Create Date: 2026-09-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

ContentHTML = sa.Text().with_variant(mysql.LONGTEXT(charset="utf8mb4"), "mysql")


def upgrade() -> None:
    op.create_table(
        "city",
        sa.Column("code", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("province_code", sa.String(12), nullable=False),
        sa.Column("province_name", sa.String(32), nullable=False),
        sa.Column("level", sa.SmallInteger, nullable=False),
        sa.Column("lng", sa.Float, nullable=False),
        sa.Column("lat", sa.Float, nullable=False),
    )
    op.create_index("idx_province", "city", ["province_code"])

    op.create_table(
        "family_member",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(32), nullable=False),
        sa.Column("nickname", sa.String(32)),
        sa.Column("is_child", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "tag",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(16), nullable=False, unique=True),
    )

    op.create_table(
        "trip",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("start_date", sa.Date, nullable=False),
        sa.Column("end_date", sa.Date, nullable=False),
        sa.Column("summary", sa.String(500)),
        sa.Column("content", ContentHTML),
        sa.Column("cover_photo", sa.String(255)),
        sa.Column("country", sa.String(32)),
        sa.Column("status", sa.String(16), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_status_date", "trip", ["status", "start_date"])

    op.create_table(
        "trip_member",
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("member_id", sa.Integer, sa.ForeignKey("family_member.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "trip_tag",
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trip.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer, sa.ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "trip_city",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trip.id", ondelete="CASCADE"), nullable=False),
        sa.Column("city_code", sa.String(12), sa.ForeignKey("city.code")),
        sa.Column("city_name", sa.String(32)),
        sa.Column("lng", sa.Float),
        sa.Column("lat", sa.Float),
        sa.Column("sort_order", sa.SmallInteger, nullable=False, server_default=sa.text("0")),
    )
    op.create_index("idx_trip_city", "trip_city", ["trip_id", "sort_order"])

    op.create_table(
        "trip_day",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trip.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_index", sa.SmallInteger, nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("title", sa.String(128)),
        sa.Column("note", sa.String(500)),
    )
    op.create_index("idx_trip_day", "trip_day", ["trip_id", "day_index"])

    op.create_table(
        "attraction",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("trip_id", sa.Integer, sa.ForeignKey("trip.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("city_code", sa.String(12), sa.ForeignKey("city.code")),
        sa.Column("album_rel_path", sa.String(255)),
        sa.Column("lng", sa.Float),
        sa.Column("lat", sa.Float),
        sa.Column("note", sa.String(255)),
    )
    op.create_index("idx_trip_attraction", "attraction", ["trip_id"])


def downgrade() -> None:
    op.drop_table("attraction")
    op.drop_table("trip_day")
    op.drop_table("trip_city")
    op.drop_table("trip_tag")
    op.drop_table("trip_member")
    op.drop_table("trip")
    op.drop_table("tag")
    op.drop_table("family_member")
    op.drop_table("city")
