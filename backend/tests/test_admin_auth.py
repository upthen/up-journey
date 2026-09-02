"""管理端鉴权：登录 cookie、401/503、公开 API 不受影响。"""

import os

import pytest

from app.config import reset_settings_cache

from tests.conftest import CITY_CODES, create_trip


@pytest.fixture()
def admin_pw():
    """确保管理密码生效（与 conftest 默认一致），Settings 缓存重建。"""
    reset_settings_cache()
    yield os.environ["ADMIN_PASSWORD"]
    reset_settings_cache()


def _login(client, password):
    return client.post("/api/v1/admin/login", json={"password": password})


# ---------- 未配置密码：管理端 503，展示端不受影响 ----------

def test_admin_api_503_when_password_unconfigured(anon_client, monkeypatch):
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    reset_settings_cache()
    try:
        assert anon_client.get("/api/v1/admin/members").status_code == 503
        assert anon_client.post("/api/v1/admin/login", json={"password": "x"}).status_code == 503
        # 展示端照常
        assert anon_client.get("/api/v1/health").status_code == 200
        assert anon_client.get("/api/v1/trips").status_code == 200
    finally:
        monkeypatch.undo()
        reset_settings_cache()


# ---------- 登录与会话 ----------

def test_login_wrong_password_401(client, admin_pw):
    r = _login(client, "wrong")
    assert r.status_code == 401


def test_login_ok_sets_cookie_then_admin_apis_work(client, admin_pw):
    r = _login(client, admin_pw)
    assert r.status_code == 200
    assert "uj_admin" in r.cookies

    assert client.get("/api/v1/admin/members").status_code == 200
    assert client.get("/api/v1/admin/session").status_code == 200
    assert client.get("/api/v1/admin/cities", params={"level": 1}).status_code == 200


def test_admin_api_401_without_login(anon_client, admin_pw):
    assert anon_client.get("/api/v1/admin/members").status_code == 401
    assert anon_client.get("/api/v1/admin/session").status_code == 401
    r = anon_client.post(
        "/api/v1/admin/trips", json={"title": "x", "start_date": "2024-01-01", "end_date": "2024-01-01"}
    )
    assert r.status_code == 401


def test_forged_cookie_401(anon_client, admin_pw):
    anon_client.cookies.set("uj_admin", "deadbeef" * 8)
    assert anon_client.get("/api/v1/admin/members").status_code == 401


def test_password_change_invalidates_sessions(client, admin_pw, monkeypatch):
    _login(client, admin_pw)
    assert client.get("/api/v1/admin/session").status_code == 200
    monkeypatch.setenv("ADMIN_PASSWORD", "rotated-password")
    reset_settings_cache()
    assert client.get("/api/v1/admin/session").status_code == 401
    reset_settings_cache()


def test_logout_clears_session(client, admin_pw):
    _login(client, admin_pw)
    assert client.get("/api/v1/admin/session").status_code == 200
    assert client.post("/api/v1/admin/logout").status_code == 200
    assert client.get("/api/v1/admin/session").status_code == 401


# ---------- 展示端与图片服务永远不需要登录 ----------

def test_public_apis_unaffected_by_auth(client, anon_client, admin_pw, photos_root):
    from tests.conftest import make_jpeg

    make_jpeg(photos_root / "album" / "a.jpg")
    assert anon_client.get("/api/v1/health").status_code == 200
    assert anon_client.get("/api/v1/stats").status_code == 200
    assert anon_client.get("/api/v1/footprints").status_code == 200
    assert anon_client.get("/api/v1/photos/thumb", params={"path": "album/a.jpg"}).status_code == 200
    assert anon_client.get("/api/v1/admin/album").status_code == 401  # 相册浏览在 admin 下


def test_draft_still_hidden_after_auth_enabled(client, admin_pw):
    """鉴权开启后：登录的管理端能看到草稿，公开展示端仍然看不到。"""
    trip = create_trip(client, title="草稿", status="draft")
    admin_view = client.get("/api/v1/admin/trips", params={"status": "draft"}).json()
    assert [t["title"] for t in admin_view] == ["草稿"]
    public_view = client.get("/api/v1/trips").json()
    assert all(t["slug"] != trip["slug"] for t in public_view)
