# up-journey 部署方案（绿联 DH4300 Plus · ARM64 · UGOS Pro）

> 镜像全部 `linux/arm64`；Mac（Apple Silicon）本地构建与 NAS 同架构，零交叉编译。

## 容器编排（deploy/docker-compose.yml 蓝本）

| 服务 | 说明 |
|---|---|
| `nginx` | 对外 `:8100`；托管前端 dist；`/api` 反代 api；SPA 回落 `index.html`；gzip + 静态长缓存 |
| `api` | uvicorn；启动时自动 `alembic upgrade head`；挂载 `/photos`（**只读**）与 `/cache`（读写） |
| `mysql` | MySQL 8 utf8mb4；volume `mysql_data`；healthcheck；**不暴露端口** |

`.env` 变量（本地与 NAS 各一份）：

```bash
PHOTOS_HOST_DIR=/volume1/家庭相册        # 宿主机共享相册绝对路径（NAS 上按实际填）
MYSQL_ROOT_PASSWORD=*****
MYSQL_DATABASE=upjourney
MYSQL_USER=upjourney
MYSQL_PASSWORD=*****
```

## 发布流程（deploy/deploy.sh）

```
Mac 本地：
  docker buildx build  --platform linux/arm64  （frontend → nginx 镜像；backend → api 镜像）
  docker save 两个镜像 → tar
  scp tar + docker-compose.yml + .env → 192.168.1.18
  ssh 远程执行：docker load ×2 → docker compose up -d → 冒烟探活
冒烟：curl http://192.168.1.18:8100/api/v1/health 与 /api/v1/stats
```

- 前置条件：NAS 开启 SSH；Docker（UGOS Pro 容器工作台）；已建好共享相册目录。
- 首次部署：在 NAS 上建部署目录（如 `/volume1/docker/up-journey/`），放入 `.env`（相册路径、口令）。
- 升级 = 重跑 `deploy.sh`；数据库结构变更由 api 容器启动时自动迁移。

## 数据与备份

- `mysql_data`、`cache` 均为 docker volume（不碰共享相册）。
- `db-backup.sh`（cron 或手动）：`mysqldump` 导出到 NAS 指定备份目录，保留最近 N 份。
- **共享相册是图片唯一数据源，应用只读**——应用故障/误删不影响照片。

## ⚠️ 公网暴露前置条件（未来）

将 8100 反代到公网域名**之前**，必须：

1. 启用代码中预留的"访客密码 + 管理员密码"开关（架构已留接缝，无需改造）；
2. 配置 HTTPS（NAS 反代或域名服务商侧）；
3. MySQL 确认未映射到宿主机端口。

## 本地开发

- `docker compose -f deploy/docker-compose.dev.yml up -d`：只起 MySQL 8（Docker Desktop）。
- 后端：`uvicorn` 直跑（热重载），`.env` 指向 localhost MySQL。
- 前端：`vite dev`，proxy `/api` 到本地 uvicorn。
