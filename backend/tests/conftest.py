"""测试环境：环境变量先行（SQLite 内存 + 临时相册/缓存目录），再导入应用。

唯一测试接缝 = 后端 HTTP API（spec Testing Decisions）；
测试库 SQLite 内存，毫秒级零依赖。
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

_PHOTOS = tempfile.mkdtemp(prefix="uj_photos_")
_CACHE = tempfile.mkdtemp(prefix="uj_cache_")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("PHOTOS_DIR", _PHOTOS)
os.environ.setdefault("CACHE_DIR", _CACHE)
os.environ.setdefault("ADMIN_PASSWORD", "test-admin")  # 测试环境默认开启管理端鉴权

sys.path.insert(0, str(BACKEND))

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import get_settings
from app.db import Base, SessionLocal, engine
from app.main import app
from app.seed import seed_cities

Image.MAX_IMAGE_PIXELS = None


@pytest.fixture()
def db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session = SessionLocal()
    seed_cities(session)
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db) -> TestClient:
    c = TestClient(app)
    r = c.post("/api/v1/admin/login", json={"password": os.environ["ADMIN_PASSWORD"]})
    assert r.status_code == 200, "测试 client 应以默认管理密码登录"
    return c


@pytest.fixture()
def anon_client(db) -> TestClient:
    """未登录客户端（验证 401 路径）。"""
    return TestClient(app)


@pytest.fixture()
def photos_root() -> Path:
    """每个测试独立的相册 + 缓存目录（Settings 缓存随环境切换重建）。"""
    old_photos, old_cache = os.environ["PHOTOS_DIR"], os.environ["CACHE_DIR"]
    new_photos = tempfile.mkdtemp(prefix="uj_photos_")
    new_cache = tempfile.mkdtemp(prefix="uj_cache_")
    os.environ["PHOTOS_DIR"], os.environ["CACHE_DIR"] = new_photos, new_cache
    get_settings.cache_clear()
    root = Path(new_photos)
    root.mkdir(parents=True, exist_ok=True)
    yield root
    os.environ["PHOTOS_DIR"], os.environ["CACHE_DIR"] = old_photos, old_cache
    get_settings.cache_clear()


# ---------- 图片工厂 ----------

def make_jpeg(path: Path, size=(1200, 800), color=(200, 100, 50), orientation: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.new("RGB", size, color)
    kwargs = {}
    if orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = orientation  # Orientation tag
        kwargs["exif"] = exif
    im.save(path, "JPEG", **kwargs)


def make_heic(path: Path, size=(900, 600), color=(10, 120, 180)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, format="HEIF")


# ---------- API 数据工厂 ----------

CITY_CODES = {
    "昆明市": "530100",
    "大理白族自治州": "532900",
    "丽江市": "530700",
    "杭州市": "330100",
    "北京市": "110000",  # 省级行政区划码（city 表 level=1 行）
    "北京市市级": "110100",  # 合成的直辖市市级条目
    "青岛市": "370200",
}


def create_member(client, name, nickname=None, is_child=False) -> dict:
    r = client.post("/api/v1/admin/members", json={"name": name, "nickname": nickname, "is_child": is_child})
    assert r.status_code == 201, r.text
    return r.json()


def create_tag(client, name) -> dict:
    r = client.post("/api/v1/admin/tags", json={"name": name})
    assert r.status_code == 201, r.text
    return r.json()


def trip_payload(**overrides) -> dict:
    payload = {
        "title": "云南环线：从滇池到玉龙",
        "start_date": "2024-05-01",
        "end_date": "2024-05-07",
        "summary": "七天一千二百公里。",
        "content": "<p>出发前一晚……</p>",
        "status": "published",
        "cities": [
            {"city_code": CITY_CODES["昆明市"]},
            {"city_code": CITY_CODES["大理白族自治州"]},
            {"city_code": CITY_CODES["丽江市"]},
        ],
        "attractions": [
            {"name": "滇池 · 海埂大坝", "city_code": CITY_CODES["昆明市"], "album_rel_path": "2024云南/昆明滇池", "note": "海鸥落在手腕上啄食。"},
            {"name": "洱海", "city_code": CITY_CODES["大理白族自治州"], "album_rel_path": "2024云南/大理洱海", "lng": 100.18, "lat": 25.75, "note": "S 湾的日落持续了四十分钟。"},
        ],
        "days": [
            {"date": "2024-05-01", "title": "海埂大坝喂红嘴鸥", "note": "晚宿翠湖旁"},
            {"date": "2024-05-02", "title": "西山 → 动车赴大理"},
        ],
        "member_ids": [],
        "tag_ids": [],
    }
    payload.update(overrides)
    return payload


def create_trip(client, **overrides) -> dict:
    r = client.post("/api/v1/admin/trips", json=trip_payload(**overrides))
    assert r.status_code == 201, r.text
    return r.json()
