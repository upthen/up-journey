# up-journey

家庭旅游记录应用：管理端录入旅行记录，展示端以 v4 流程式体验（全屏地图即首页）呈现家庭足迹。
需求见 `.scratch/v1/spec.md`，架构见 `docs/`，展示端像素蓝本见 `docs/prototype/v4/`（ADR-0001）。

## 目录

```
backend/    FastAPI + SQLAlchemy 2.0 + Pydantic v2 · Alembic · pytest
frontend/   Vue 3 + TS + Vite 单 SPA（展示端 + /admin 管理端）
deploy/     docker-compose（nginx + api + mysql）· 发布/备份脚本
docs/       架构 / 数据库 / 部署文档 · 高保真原型
```

## 本地开发

```bash
# 1) 后端（uv，Python 3.12）
cd backend
uv sync
cp ../deploy/.env.example .env          # 按需修改
DATABASE_URL=sqlite:///./data/upjourney.db uv run alembic upgrade head
uv run python scripts/seed_demo.py      # 可选：演示数据 + 相册样例
uv run uvicorn app.main:app --reload    # :8000

# 2) 前端（Node 22）
cd frontend
npm install
npm run dev                             # :5173，/api 代理到 :8000
```

MySQL 本地跑法：`docker compose -f deploy/docker-compose.dev.yml up -d`（127.0.0.1:33061）。

## 测试

```bash
cd backend && uv run pytest          # 88 个 API 测试（SQLite 内存，唯一测试接缝）
cd frontend && npm run typecheck     # vue-tsc
```

## 部署到绿联 NAS

见 `docs/deployment.md` 与 `deploy/deploy.sh`（构建 arm64 镜像 → scp → compose up → 冒烟）。
**公网暴露前必须启用鉴权**（代码已留接缝：`app/routers/admin.py: require_admin`）。

## 图片主权

唯一数据源 = NAS 共享相册（只读挂载）。应用按需生成缩略图/大图缓存，原图永不改动；
所有图片路径钉死在挂载根内，目录穿越一律 403。
