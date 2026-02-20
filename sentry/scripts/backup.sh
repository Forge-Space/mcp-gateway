#!/bin/bash

# Sentry Backup Script
# Creates a complete backup of Sentry data and configuration

set -e

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="sentry_backup_${TIMESTAMP}.tar.gz"

echo "🔄 Creating Sentry backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Docker volumes
echo "📦 Backing up Docker volumes..."

# PostgreSQL data
echo "  - PostgreSQL data..."
docker run --rm \
    -v sentry_postgres_data:/data \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf /backup/postgres_data_${TIMESTAMP}.tar.gz -C /data .

# Redis data
echo "  - Redis data..."
docker run --rm \
    -v sentry_redis_data:/data \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf /backup/redis_data_${TIMESTAMP}.tar.gz -C /data .

# Sentry files
echo "  - Sentry files..."
docker run --rm \
    -v sentry_sentry_data:/data \
    -v "$(pwd)/$BACKUP_DIR":/backup \
    alpine tar czf /backup/sentry_data_${TIMESTAMP}.tar.gz -C /data .

# Backup configuration files
echo "📝 Backing up configuration..."
cp .env "${BACKUP_DIR}/env_${TIMESTAMP}"
cp docker-compose.yml "${BACKUP_DIR}/docker-compose_${TIMESTAMP}.yml"
cp nginx.conf "${BACKUP_DIR}/nginx_${TIMESTAMP}.conf" 2>/dev/null || true

# Create combined backup
echo "🗜️  Creating combined backup archive..."
cd "$BACKUP_DIR"
tar czf "${BACKUP_FILE}" \
    postgres_data_${TIMESTAMP}.tar.gz \
    redis_data_${TIMESTAMP}.tar.gz \
    sentry_data_${TIMESTAMP}.tar.gz \
    env_${TIMESTAMP} \
    docker-compose_${TIMESTAMP}.yml \
    nginx_${TIMESTAMP}.conf

# Cleanup individual files
rm postgres_data_${TIMESTAMP}.tar.gz \
   redis_data_${TIMESTAMP}.tar.gz \
   sentry_data_${TIMESTAMP}.tar.gz \
   env_${TIMESTAMP} \
   docker-compose_${TIMESTAMP}.yml \
   nginx_${TIMESTAMP}.conf

cd ..

echo "✅ Backup complete: ${BACKUP_DIR}/${BACKUP_FILE}"
echo "📊 Backup size: $(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)"

# Cleanup old backups (keep last 7 days)
echo "🧹 Cleaning up old backups..."
find "$BACKUP_DIR" -name "sentry_backup_*.tar.gz" -mtime +7 -delete

echo "🎉 Backup process completed successfully!"