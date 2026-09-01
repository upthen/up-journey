# up-journey 架构设计

> 2026-09-01 技术方案访谈定稿。配套文档：[database.md](./database.md)、[deployment.md](./deployment.md)。

## 总体拓扑

```
┌────────────────────── 绿联 DH4300 Plus（ARM64 · UGOS Pro · 192.168.1.18）──────────────────────┐
│  docker-compose（deploy/）                                                                     │
│                                                                                                │
│  ┌──────────────────┐    /api 反代     ┌──────────────────┐          ┌──────────────────┐     │
│  │ nginx            │ ───────────────▶ │ api              │ ───────▶ │ mysql            │     │
│  │ · 前端静态 dist   │                  │ FastAPI+uvicorn  │  3306    │ MySQL 8 utf8mb4  │     │
│  │ · SPA 回落规则    │                  │ · Alembic 迁移    │ (内部)   │ volume: mysql_data│   │
│  │ · gzip/静态缓存   │                  │ · 图片管线        │          └──────────────────┘     │
│  └──────────────────┘                  └───────┬──────────┘                                     │
│        ▲ 对外 :8100                             │                                                │
│        │                              ro 挂载 /photos ──▶ 宿主机共享相册目录（唯一数据源，只读）      │
│     局域网浏览器                       rw 挂载 /cache ──▶ 缩略图缓存卷（应用私有）                   │
└────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 仓库布局

```
backend/    FastAPI 应用、Alembic 迁移、pytest 测试
frontend/   Vue 3 + TS + Vite 单 SPA（展示端 + /admin）
deploy/     docker-compose.yml、nginx.conf、Dockerfile ×2、deploy.sh、db-backup.sh、.env.example
docs/       架构 / DDL / 部署文档、prototype 高保真原型
```

## API 设计

- REST，统一前缀 `/api/v1`；统一错误结构 `{ "detail": "..." }`。
- **展示端（公开）**：
  - `GET /api/v1/stats` — 数字统计（年数/省/市/景点/国家/次数/天数/带娃次数）
  - `GET /api/v1/trips?year=&tag=` — 已发布旅行卡片列表
  - `GET /api/v1/trips/{slug}` — 旅行详情（含正文、图库目录、天程）
  - `GET /api/v1/footprints` — 足迹地图数据（省份清单、城市坐标、各旅行路线、时间轴数据）
  - `GET /api/v1/photos/{size}?path=` — 图片服务（size = thumb | full）
  - `GET /api/v1/meta` — 成员/标签/站点配置
- **管理端（`/api/v1/admin/*`，挂空的鉴权依赖——未来启用"管理员密码"只改这一个依赖）**：
  - trips / members / tags 的 CRUD
  - `GET /api/v1/admin/album?path=` — 相册目录浏览（列子目录与图片，供选图器）
  - `POST /api/v1/admin/photos/pick-cover` 语义并入 trip 更新（cover_photo 存相册相对路径）
- 前端 axios 轻封装 composable；跨页共享状态（站点配置）用 Pinia。

## 图片管线

1. 请求 `GET /photos/thumb?path=2024云南/大理洱海/IMG_1234.HEIC`。
2. 校验解析后的绝对路径必须落在 `/photos` 挂载根内，否则 403。
3. 缓存键 = 原始相对路径 + 文件 mtime + size 档位，命中 `/cache` 直接返回。
4. 未命中则 Pillow 打开原图：EXIF 转正 → HEIC 转 JPEG → resize（thumb 400px / full 1600px 长边）→ 写缓存 → 返回。
5. 原图永远只读；相册内容增删实时生效（无同步任务，请求时扫描）。

## 安全边界

- v1 无鉴权（纯局域网）。所有 admin API 收敛在独立路由依赖下；前端预留路由守卫位。
- 部署文档显著警示：**挂公网前必须启用"访客密码 + 管理员密码"开关**。
- 富文本：展示端 `v-html` 前必过 DOMPurify 白名单；图片路径服务端二次校验。

## 关键技术选型一览

| 层 | 选型 |
|---|---|
| 前端框架 | Vue 3 + TypeScript + Vite，单 SPA |
| UI 组件 | Element Plus（管理端）；展示端 Tailwind 自定义排版 |
| 地图 | ECharts 按需引入 + 中国 GeoJSON 随包（离线） |
| 富文本 | WangEditor 5（管理端）+ DOMPurify（展示端） |
| 后端 | FastAPI + SQLAlchemy 2.0 + Pydantic v2（容器内 Python 3.12） |
| 迁移 | Alembic（第一天启用，城市字典走种子迁移） |
| 数据库 | MySQL 8 / utf8mb4 / InnoDB |
| 字体 | 思源宋体 self-host 子集化 woff2（标题+数字），正文系统无衬线 |
| 镜像 | 全部 linux/arm64，多阶段构建 |

## 测试接缝

唯一接缝 = 后端 HTTP API（pytest + TestClient + SQLite 内存库）；部署脚本对真 MySQL 冒烟。详见 spec 的 Testing Decisions。
