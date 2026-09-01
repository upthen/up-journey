#!/usr/bin/env bash
# 数据库备份：在 NAS 部署目录执行（cron 每日凌晨或手动）。
# mysqldump 导出 → gzip → 保留最近 N 份。
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/volume1/docker/up-journey/backups}"
KEEP="${KEEP:-14}"
cd "$(dirname "$0")"

mkdir -p "${BACKUP_DIR}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${BACKUP_DIR}/upjourney-${STAMP}.sql.gz"

docker compose exec -T mysql sh -c \
  'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines upjourney' | gzip > "${OUT}"

echo "✅ 备份完成：${OUT}"
ls -1t "${BACKUP_DIR}"/upjourney-*.sql.gz | tail -n +"$((KEEP + 1))" | xargs -r rm -f
echo "   保留最近 ${KEEP} 份"
