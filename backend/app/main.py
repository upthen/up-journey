"""FastAPI 入口。开发：uvicorn app.main:app --reload；容器：由 deploy 启动。"""

from fastapi import FastAPI

from .routers import admin, public


def create_app() -> FastAPI:
    app = FastAPI(title="up-journey API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
    app.include_router(public.router)
    app.include_router(admin.router)
    return app


app = create_app()
