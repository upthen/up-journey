"""相册目录浏览（管理端选图器）。"""

from tests.conftest import make_jpeg


def test_album_root_lists(client, photos_root):
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "a.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "b.jpg")
    make_jpeg(photos_root / "2023青岛" / "c.jpg")
    (photos_root / "2024云南" / "notes.txt").write_text("忽略非图片")

    r = client.get("/api/v1/admin/album")
    assert r.status_code == 200
    data = r.json()
    assert data["current"] == ""
    assert data["parent"] is None
    assert [d["name"] for d in data["dirs"]] == ["2023青岛", "2024云南"]
    assert data["photos"] == []  # 根下没有直接图片


def test_album_subdir_lists_photos_sorted(client, photos_root):
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "b.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "a.jpg")
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "sub" / "c.jpg")

    r = client.get("/api/v1/admin/album", params={"path": "2024云南/大理洱海"})
    data = r.json()
    assert data["current"] == "2024云南/大理洱海"
    assert data["parent"] == "2024云南"
    assert data["photos"] == ["2024云南/大理洱海/a.jpg", "2024云南/大理洱海/b.jpg"]
    assert [d["name"] for d in data["dirs"]] == ["sub"]


def test_album_parent_of_first_level_is_root(client, photos_root):
    make_jpeg(photos_root / "2024云南" / "a.jpg")
    data = client.get("/api/v1/admin/album", params={"path": "2024云南"}).json()
    assert data["parent"] == ""


def test_album_traversal_403(client):
    for evil in ("../", "..", "a/../../.."):
        r = client.get("/api/v1/admin/album", params={"path": evil})
        assert r.status_code == 403, evil
    r = client.get("/api/v1/admin/album?path=..%2F")
    assert r.status_code == 403


def test_album_missing_dir_404(client):
    assert client.get("/api/v1/admin/album", params={"path": "不存在"}).status_code == 404


def test_album_hidden_files_skipped(client, photos_root):
    (photos_root / "album").mkdir(parents=True)
    (photos_root / "album" / ".DS_Store").write_text("x")
    (photos_root / ".hidden").mkdir()
    make_jpeg(photos_root / "album" / "v.jpg")
    data = client.get("/api/v1/admin/album", params={"path": "album"}).json()
    assert data["photos"] == ["album/v.jpg"]
    assert data["dirs"] == []
