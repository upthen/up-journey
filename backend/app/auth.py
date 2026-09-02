"""管理端鉴权：密码登录 → HttpOnly 签名 cookie → require_admin 统一校验。

无状态令牌 = HMAC-SHA256(密码派生密钥, "uj-admin")：不落库、不改代码结构即可吊销
（改 ADMIN_PASSWORD 即全部会话失效）。展示端公开 API 完全不经过这里。
"""

import hashlib
import hmac

from fastapi import HTTPException, Request, Response, status

from .config import get_settings

COOKIE_NAME = "uj_admin"
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 天


def _secret() -> bytes:
    return hashlib.sha256(("uj-admin-v1:" + get_settings().admin_password).encode()).digest()


def _token() -> str:
    return hmac.new(_secret(), b"uj-admin-session", hashlib.sha256).hexdigest()


def check_password(password: str) -> bool:
    return hmac.compare_digest(password, get_settings().admin_password)


def issue_cookie(response: Response, password: str) -> bool:
    """密码正确则向响应挂会话 cookie；返回密码是否正确。"""
    if not check_password(password):
        return False
    response.set_cookie(
        COOKIE_NAME,
        _token(),
        max_age=SESSION_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return True


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE_NAME, path="/")


def verify_request(request: Request) -> None:
    """require_admin 的实现：v1 局域网模式（未配密码）历史行为是放行；
    配置了密码后无有效 cookie 一律 401。未配置密码时管理 API 返回 503，
    引导设置——公网部署忘配密码不允许静默裸奔。
    """
    settings = get_settings()
    if not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="管理端密码未配置：在 .env 设置 ADMIN_PASSWORD 后重启（公网暴露前必须配置）",
        )
    token = request.cookies.get(COOKIE_NAME, "")
    if not token or not hmac.compare_digest(token, _token()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或会话已失效")
