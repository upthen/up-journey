#!/usr/bin/env bash
# up-journey 发布脚本：Mac 本地构建 → 传 NAS → 拉起 → 冒烟。
# 前置：NAS 开启 SSH；部署目录已放好 .env（参考 .env.example）。
# 用法：./deploy.sh [默认 192.168.1.18]
set -euo pipefail

NAS_HOST="${1:-192.168.1.18}"
NAS_DIR="${NAS_DIR:-/volume1/docker/up-journey}"
cd "$(dirname "$0")/.."

echo "==> 1/5 构建镜像（linux/arm64）"
docker buildx build --platform linux/arm64 -f deploy/Dockerfile.frontend -t up-journey/nginx:latest --load ..
docker buildx build --platform linux/arm64 -f deploy/Dockerfile.backend -t up-journey/api:latest --load ../backend

echo "==> 2/5 导出镜像 tar"
mkdir -p /tmp/up-journey-release
docker save up-journey/nginx:latest | gzip > /tmp/up-journey-release/nginx.tar.gz
docker save up-journey/api:latest | gzip > /tmp/up-journey-release/api.tar.gz

echo "==> 3/5 传输到 ${NAS_HOST}:${NAS_DIR}"
ssh "root@${NAS_HOST}" "mkdir -p ${NAS_DIR}"
scp /tmp/up-journey-release/nginx.tar.gz /tmp/up-journey-release/api.tar.gz \
    deploy/docker-compose.yml "root@${NAS_HOST}:${NAS_DIR}/"

echo "==> 4/5 NAS 端加载并拉起"
ssh "root@${NAS_HOST}" "cd ${NAS_DIR} \
    && gunzip -c nginx.tar.gz | docker load \
    && gunzip -c api.tar.gz | docker load \
    && rm -f nginx.tar.gz api.tar.gz \
    && docker compose up -d --remove-orphans"

echo "==> 5/5 冒烟探活"
sleep 8
curl -fsS "http://${NAS_HOST}:8100/api/v1/health" && echo
curl -fsS "http://${NAS_HOST}:8100/api/v1/stats" && echo
echo "✅ 部署完成：http://${NAS_HOST}:8100"
