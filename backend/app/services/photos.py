"""图片管线：相册只读引用 + 两档 JPEG 缓存。

规则（architecture.md 图片管线节）：
1. 唯一数据源 = PHOTOS_DIR 挂载根；所有请求路径必须解析后落在根内，否则 403；
2. 缓存键 = 相对路径 + mtime_ns + 档位，命中直接返回（相册增删实时生效）；
3. 未命中：Pillow 打开 → EXIF 转正 → HEIC 转码 → 降采样（thumb 400 / full 1600 长边）→
   原子写缓存；原图永不改动。
"""

import hashlib
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from ..config import Settings, cache_root, get_settings, photos_root
from ..schemas import AlbumDirOut, AlbumOut

register_heif_opener()

ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tif", ".tiff"}
SIZES = ("thumb", "full")


class PhotoError(Exception):
    status_code = 400


class PhotoForbidden(PhotoError):
    status_code = 403


class PhotoNotFound(PhotoError):
    status_code = 404


def _validate_rel(rel: str) -> str:
    if not rel or "\x00" in rel:
        raise PhotoForbidden("非法图片路径")
    if rel.startswith(("/", "\\")) or len(rel) > 1 and rel[1] == ":":
        raise PhotoForbidden("非法图片路径")
    parts = rel.replace("\\", "/").split("/")
    if any(p in ("", ".", "..") for p in parts):
        raise PhotoForbidden("非法图片路径")
    return "/".join(parts)


def resolve_within(root: Path, rel: str) -> Path:
    """把相对路径钉死在 root 内，任何形式的穿越都拒绝。"""
    rel = _validate_rel(rel)
    resolved = (root / rel).resolve()
    root = root.resolve()
    if resolved != root and root not in resolved.parents:
        raise PhotoForbidden("路径超出相册根目录")
    return resolved


def list_album(rel: str, settings: Settings | None = None) -> AlbumOut:
    """相册目录浏览（管理端选图器）：列子目录与图片。"""
    settings = settings or get_settings()
    root = photos_root(settings)
    rel = "" if rel in (".", "") else _validate_rel(rel)
    cur = resolve_within(root, rel) if rel else root
    if not cur.exists() or not cur.is_dir():
        raise PhotoNotFound("目录不存在")
    dirs, photos = [], []
    for child in sorted(cur.iterdir(), key=lambda p: p.name):
        if child.name.startswith("."):
            continue
        if child.is_dir():
            relpath = child.relative_to(root).as_posix()
            dirs.append(AlbumDirOut(path=relpath, name=child.name))
        elif child.is_file() and child.suffix.lower() in ALLOWED_EXTS:
            photos.append(child.relative_to(root).as_posix())
    parent = os.path.dirname(rel) if rel else None  # 一级目录的 parent="" 表示根
    return AlbumOut(current=rel, parent=parent, dirs=dirs, photos=photos)


def scan_album(rel: str | None, settings: Settings | None = None) -> list[str]:
    """某相册子目录内的全部图片（相对根路径，按文件名排序）；无目录返回空。"""
    if not rel:
        return []
    settings = settings or get_settings()
    root = photos_root(settings)
    try:
        cur = resolve_within(root, rel)
    except PhotoError:
        return []
    if not cur.is_dir():
        return []
    out = [
        child.relative_to(root).as_posix()
        for child in sorted(cur.iterdir(), key=lambda p: p.name)
        if child.is_file() and not child.name.startswith(".") and child.suffix.lower() in ALLOWED_EXTS
    ]
    return out


def _cache_file(root: Path, key: str) -> Path:
    return root / key[:2] / f"{key}.jpg"


def get_photo(size: str, rel: str, settings: Settings | None = None) -> Path:
    """返回可直送的 JPEG 缓存文件路径（命中或现场生成）。"""
    settings = settings or get_settings()
    if size not in SIZES:
        raise PhotoError("size 必须是 thumb 或 full")
    limit = settings.thumb_size if size == "thumb" else settings.full_size

    root = photos_root(settings)
    src = resolve_within(root, rel)
    if not src.exists() or not src.is_file():
        raise PhotoNotFound("图片不存在")
    if src.suffix.lower() not in ALLOWED_EXTS:
        raise PhotoNotFound("不支持的图片格式")
    stat = src.stat()

    key_src = f"{rel}\0{stat.st_mtime_ns}\0{size}".encode("utf-8")
    key = hashlib.sha1(key_src).hexdigest()
    cached = _cache_file(cache_root(settings), key)
    if cached.exists():
        return cached

    cached.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        if max(im.size) > limit:  # 小图不放大，保持原尺寸
            im.thumbnail((limit, limit), Image.LANCZOS)
        # 原子写：先写临时文件再 rename，避免并发请求读到半张图
        fd, tmp = tempfile.mkstemp(dir=cached.parent, suffix=".tmp")
        try:
            im.save(tmp, format="JPEG", quality=settings.image_quality, progressive=True)
            os.close(fd)
            os.replace(tmp, cached)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    return cached
