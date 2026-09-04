#!/usr/bin/env bash
# up-journey 发布脚本：Mac 本地构建 → 传 NAS → 拉起 → 冒烟。
#
# 基础镜像走 NAS 私有镜像库（192.168.1.18:5000，registry:2，数据落
# /volume1/docker/registry），构建不再依赖 Docker Hub 直连。
# 首次使用 / 私库缺镜像时先执行：./deploy.sh bootstrap
#
# 前置：NAS 开启 SSH；部署目录已放好 .env（参考 .env.example）。
# 用法：./deploy.sh [NAS地址，默认 192.168.1.18]
set -euo pipefail

NAS_HOST="${1:-192.168.1.18}"
NAS_DIR="${NAS_DIR:-/volume1/docker/up-journey}"
REGISTRY="${REGISTRY:-${NAS_HOST}:5000}"
# 私库中的基础镜像（deploy.sh bootstrap 负责从官方源经加速器灌入）
BASE_IMAGES=(
  "${REGISTRY}/library/node:22-alpine"
  "${REGISTRY}/library/nginx:1.27-alpine"
  "${REGISTRY}/library/python:3.12-slim-bookworm"
  "${REGISTRY}/astral-sh/uv:python3.12-bookworm-slim"
)
cd "$(dirname "$0")/.."

# 私库里的镜像清单
registry_catalog() {
  curl -fsS "http://${REGISTRY}/v2/_catalog?n=100" 2>/dev/null || echo '{}'
}
registry_has() { # $1=repo $2=tag
  local repos tags
  repos=$(registry_catalog | python3 -c "import json,sys; print(' '.join(json.load(sys.stdin).get('repositories', [])))" 2>/dev/null || true)
  [[ " $repos " == *" $1 "* ]] || return 1
  tags=$(curl -fsS "http://${REGISTRY}/v2/${1}/tags/list" 2>/dev/null \
    | python3 -c "import json,sys; print(' '.join(json.load(sys.stdin).get('tags') or []))" 2>/dev/null || true)
  [[ " $tags " == *" $2 "* ]]
}

if [[ "${1:-}" == "bootstrap" ]]; then
  echo "==> 灌基础镜像进私有库 ${REGISTRY}（经本机 Docker 加速器拉取官方源）"
  # 官方源 → 私库 的对应关系（library/ 前缀 = Docker 官方镜像的规范路径）
  pairUp() { # $1=官方引用 $2=私库引用
    local repo="${2#${REGISTRY}/}"; repo="${repo%:*}"
    if registry_has "$repo" "${2##*:}"; then
      echo "    已存在，跳过：${2}"
    else
      echo "    拉取 ${1} → 推送 ${2}"
      docker pull "$1"
      docker tag "$1" "$2"
      docker push "$2"
    fi
  }
  pairUp "node:22-alpine"                  "${REGISTRY}/library/node:22-alpine"
  pairUp "nginx:1.27-alpine"               "${REGISTRY}/library/nginx:1.27-alpine"
  pairUp "python:3.12-slim-bookworm"       "${REGISTRY}/library/python:3.12-slim-bookworm"
  pairUp "ghcr.io/astral-sh/uv:python3.12-bookworm-slim" "${REGISTRY}/astral-sh/uv:python3.12-bookworm-slim"
  echo "✅ bootstrap 完成：$(registry_catalog)"
  exit 0
fi

echo "==> 0/5 校验私有库基础镜像"
for img in "${BASE_IMAGES[@]}"; do
  repo="${img#${REGISTRY}/}"; repo="${repo%:*}"; tag="${img##*:}"
  if ! registry_has "$repo" "$tag"; then
    echo "❌ 私库缺 ${img}，请先执行 ./deploy.sh bootstrap" >&2
    exit 1
  fi
done
echo "    基础镜像齐全"

echo "==> 1/5 构建镜像（linux/arm64）"
docker buildx build --platform linux/arm64 -f deploy/Dockerfile.frontend \
  --build-arg REGISTRY="${REGISTRY}" -t up-journey/nginx:latest --load .
docker buildx build --platform linux/arm64 -f deploy/Dockerfile.backend \
  --build-arg REGISTRY="${REGISTRY}" --build-arg UV_IMAGE="${REGISTRY}/astral-sh/uv:python3.12-bookworm-slim" \
  -t up-journey/api:latest --load backend

echo "==> 2/5 导出镜像 tar"
mkdir -p /tmp/up-journey-release
docker save up-journey/nginx:latest | gzip > /tmp/up-journey-release/nginx.tar.gz
docker save up-journey/api:latest | gzip > /tmp/up-journey-release/api.tar.gz

NAS_USER="${NAS_USER:-15827773695}"
echo "==> 3/5 传输到 ${NAS_HOST}（用户 ${NAS_USER}，ssh 流式传输；UGOS 的 SFTP 子系统受限）"
ssh -o BatchMode=yes "15827773695@${NAS_HOST}" "mkdir -p ~/up-journey-release"
for f in nginx.tar.gz api.tar.gz; do
  cat "/tmp/up-journey-release/$f" | ssh -o BatchMode=yes "15827773695@${NAS_HOST}" "cat > ~/up-journey-release/$f"
done
cat deploy/docker-compose.yml | ssh -o BatchMode=yes "15827773695@${NAS_HOST}" "cat > ~/up-journey-release/docker-compose.yml"

echo "==> 4/5 NAS 端加载并拉起（docker 命令需 sudo，复用 nas 工具的认证）"
NAS_TOOL="${NAS_TOOL:-$HOME/.agents/skills/nas-docker/scripts/nas}"
if [ ! -x "$NAS_TOOL" ]; then
  echo "❌ 找不到 $NAS_TOOL（NAS 的 docker 命令需要 sudo；本机没有该工具时请手动执行 NAS 端步骤）" >&2
  exit 1
fi
"$NAS_TOOL" root <<EOF
set -e
mkdir -p ${NAS_DIR}
mv /home/${NAS_USER}/up-journey-release/* ${NAS_DIR}/
cd ${NAS_DIR}
gunzip -c nginx.tar.gz | docker load
gunzip -c api.tar.gz | docker load
rm -f nginx.tar.gz api.tar.gz
docker compose up -d --remove-orphans
EOF

echo "==> 5/5 冒烟探活"
sleep 8
curl -fsS "http://${NAS_HOST}:8100/api/v1/health" && echo
curl -fsS "http://${NAS_HOST}:8100/api/v1/stats" && echo
echo "✅ 部署完成：http://${NAS_HOST}:8100"
