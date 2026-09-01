"""图片管线：EXIF 转正、HEIC 转码、两档缩放、缓存、目录穿越拦截、原图只读。"""

import hashlib

from PIL import Image
from tests.conftest import make_heic, make_jpeg


def _img_size(body: bytes):
    import io

    with Image.open(io.BytesIO(body)) as im:
        return im.size


def test_photo_traversal_blocked(client):
    """目录穿越一律 403（architecture.md：解析后必须落在挂载根内）。"""
    for evil in (
        "../secret.jpg",
        "a/../../secret.jpg",
        "..\\..\\secret.jpg",
        "/etc/passwd",
        "a/./b.jpg",
        "a//b.jpg",
        "..",
        "photos/../../x.jpg",
    ):
        r = client.get("/api/v1/photos/thumb", params={"path": evil})
        assert r.status_code == 403, evil


def test_photo_url_encoded_traversal_blocked(client):
    """%2e%2e 形式的穿越在 HTTP 层解码后同样被拦截。"""
    r = client.get("/api/v1/photos/thumb?path=%2e%2e/x.jpg")
    assert r.status_code == 403
    r = client.get("/api/v1/photos/thumb?path=a/%2e%2e/%2e%2e/x.jpg")
    assert r.status_code == 403


def test_photo_missing_404(client):
    r = client.get("/api/v1/photos/thumb", params={"path": "不存在/x.jpg"})
    assert r.status_code == 404


def test_photo_bad_size_400(client):
    r = client.get("/api/v1/photos/huge", params={"path": "x.jpg"})
    assert r.status_code == 400


def test_photo_missing_param_422(client):
    assert client.get("/api/v1/photos/thumb").status_code == 422


def test_photo_unsupported_extension_404(client, photos_root):
    (photos_root / "notes.txt").write_text("not an image")
    r = client.get("/api/v1/photos/thumb", params={"path": "notes.txt"})
    assert r.status_code == 404


def test_thumb_and_full_sizes(client, photos_root):
    make_jpeg(photos_root / "album" / "big.jpg", size=(2400, 1600))

    thumb = client.get("/api/v1/photos/thumb", params={"path": "album/big.jpg"})
    assert thumb.status_code == 200
    assert thumb.headers["content-type"] == "image/jpeg"
    w, h = _img_size(thumb.content)
    assert max(w, h) == 400  # 长边 400

    full = client.get("/api/v1/photos/full", params={"path": "album/big.jpg"})
    w, h = _img_size(full.content)
    assert max(w, h) == 1600  # 长边 1600


def test_small_image_not_upscaled(client, photos_root):
    make_jpeg(photos_root / "small.jpg", size=(300, 200))
    r = client.get("/api/v1/photos/full", params={"path": "small.jpg"})
    assert _img_size(r.content) == (300, 200)


def test_exif_orientation_applied(client, photos_root):
    """EXIF Orientation=6（旋转 90°）自动转正：横存竖显。"""
    make_jpeg(photos_root / "rotated.jpg", size=(1200, 800), orientation=6)
    r = client.get("/api/v1/photos/full", params={"path": "rotated.jpg"})
    w, h = _img_size(r.content)
    assert (w, h) == (800, 1200)  # 已转正，而非文件里的 1200x800


def test_heic_transcoded_to_jpeg(client, photos_root):
    make_heic(photos_root / "heic" / "IMG_1234.HEIC", size=(900, 600))
    r = client.get("/api/v1/photos/thumb", params={"path": "heic/IMG_1234.HEIC"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"  # 非 Safari 也能看
    w, h = _img_size(r.content)
    assert (w, h) == (400, 267)


def test_original_never_modified(client, photos_root):
    src = photos_root / "album" / "orig.jpg"
    make_jpeg(src, size=(2400, 1600))
    before = hashlib.sha1(src.read_bytes()).hexdigest()

    client.get("/api/v1/photos/thumb", params={"path": "album/orig.jpg"})
    client.get("/api/v1/photos/full", params={"path": "album/orig.jpg"})

    assert hashlib.sha1(src.read_bytes()).hexdigest() == before


def test_cache_hit_skips_pillow(client, photos_root, monkeypatch):
    """第二次请求必须命中缓存：让 Pillow 一被调用就炸。"""
    make_jpeg(photos_root / "cached.jpg", size=(1200, 800))
    first = client.get("/api/v1/photos/thumb", params={"path": "cached.jpg"})
    assert first.status_code == 200

    import app.services.photos as svc

    class Boom:
        @staticmethod
        def open(*a, **k):
            raise AssertionError("第二次请求不应再碰原图")

    monkeypatch.setattr(svc, "Image", Boom)
    second = client.get("/api/v1/photos/thumb", params={"path": "cached.jpg"})
    assert second.status_code == 200
    assert second.content == first.content


def test_cache_invalidated_when_album_file_changes(client, photos_root):
    """缓存键含 mtime：相册图片被替换后实时换新。"""
    src = photos_root / "live.jpg"
    make_jpeg(src, size=(1200, 800), color=(255, 0, 0))
    first = client.get("/api/v1/photos/thumb", params={"path": "live.jpg"})
    assert first.status_code == 200

    make_jpeg(src, size=(1200, 800), color=(0, 0, 255))  # mtime 变化
    second = client.get("/api/v1/photos/thumb", params={"path": "live.jpg"})
    assert second.content != first.content


def test_unicode_path_roundtrip(client, photos_root):
    """中文相册目录（NAS 共享相册的真实形态）。"""
    make_jpeg(photos_root / "2024云南" / "大理洱海" / "日落.jpg", size=(900, 600))
    r = client.get("/api/v1/photos/thumb", params={"path": "2024云南/大理洱海/日落.jpg"})
    assert r.status_code == 200
    assert max(_img_size(r.content)) == 400
