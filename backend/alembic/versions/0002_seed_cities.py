"""seed city dictionary (34 省级 + 地级市，DataV 名称与 GeoJSON 对齐)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-02

数据由 backend/scripts/build_city_data.py 生成（app/city_data.json）；
迁移直接读该文件，保证开发/生产/NAS 三处种子一致。
"""
import json
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

CITY_DATA = Path(__file__).resolve().parents[2] / "app" / "city_data.json"


def upgrade() -> None:
    rows = json.loads(CITY_DATA.read_text(encoding="utf-8"))
    op.bulk_insert(
        sa.table(
            "city",
            sa.column("code", sa.String),
            sa.column("name", sa.String),
            sa.column("province_code", sa.String),
            sa.column("province_name", sa.String),
            sa.column("level", sa.Integer),
            sa.column("lng", sa.Float),
            sa.column("lat", sa.Float),
        ),
        rows,
    )


def downgrade() -> None:
    op.execute("DELETE FROM city")
