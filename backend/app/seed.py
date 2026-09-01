"""城市字典种子：city 表（Alembic 种子迁移与测试 fixture 共用）。"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import City

CITY_DATA_FILE = Path(__file__).parent / "city_data.json"


def city_rows() -> list[dict]:
    """解析后的城市字典行（测试断言坐标也用它）。"""
    return json.loads(CITY_DATA_FILE.read_text(encoding="utf-8"))


def seed_cities(db: Session) -> int:
    """幂等导入城市字典，返回导入行数。"""
    rows = city_rows()
    existing = set(db.scalars(select(City.code)))
    fresh = [City(**r) for r in rows if r["code"] not in existing]
    db.add_all(fresh)
    db.flush()
    return len(fresh)
