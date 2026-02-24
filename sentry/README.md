# Sentry Self-Hosted Setup

Self-hosted Sentry instance for the UIForge ecosystem with cost-effective monitoring and error tracking.

## 🚀 Quick Start

```bash
# Clone and setup
cd /path/to/mcp-gateway/sentry
./setup.sh
```

## 📋 Services

- **PostgreSQL**: Primary database for Sentry data
- **Redis**: Caching and session management
- **Web**: Sentry web interface
- **Worker**: Background task processing
- **Cron**: Periodic maintenance tasks
- **Nginx**: Reverse proxy (production mode)

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Required
SENTRY_DB_PASSWORD=your_secure_password
SENTRY_SECRET_KEY=your_long_random_key
SENTRY_ADMIN_EMAIL=admin@yourdomain.com

# Optional (for email alerts)
SENTRY_EMAIL_HOST=smtp.gmail.com
SENTRY_EMAIL_USER=your_email@gmail.com
SENTRY_EMAIL_PASSWORD=your_app_password
```

### SSL Configuration (Production)

1. Place SSL certificates in `ssl/` directory:
   - `ssl/cert.pem` - SSL certificate
   - `ssl/key.pem` - Private key

2. Enable production profile:
```bash
docker-compose --profile production up -d
```

## 📊 Access

- **Web Interface**: http://localhost:9000
- **Default Credentials**: admin@localhost / admin123

## 🎯 Project Setup

Create projects for each UIForge application:

1. **mcp-gateway** (Python)
2. **uiforge-mcp** (Node.js)
3. **uiforge-webapp** (Next.js)
4. **forge-patterns** (Development)

## 🔧 Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Update Sentry
docker-compose pull && docker-compose up -d

# Backup data
./scripts/backup.sh

# Restore data
./scripts/restore.sh
```

## 📈 Monitoring

### Health Checks
- Web interface: http://localhost:9000/_health/
- Database: PostgreSQL health checks
- Redis: Ping health checks

### Performance Monitoring
- Monitor resource usage with `docker stats`
- Check log volumes with `docker volume ls`
- Track database size with PostgreSQL queries

## 🔒 Security

- Internal network isolation
- Rate limiting via Nginx
- Security headers configured
- No public registration (admin-only setup)
- SSL/TLS encryption in production

## 💾 Backup Strategy

### Automated Backups
```bash
# Daily backup script
0 2 * * * /path/to/mcp-gateway/sentry/scripts/backup.sh
```

### Manual Backup
```bash
./scripts/backup.sh
```

### Restore
```bash
./scripts/restore.sh backup_file.tar.gz
```

## 🚨 Troubleshooting

### Common Issues

1. **Services not starting**
   ```bash
   docker-compose logs web
   docker-compose logs postgres
   ```

2. **Database connection errors**
   - Check `.env` file configuration
   - Verify PostgreSQL container health

3. **High memory usage**
   - Reduce `SENTRY_WEB_CONCURRENCY`
   - Optimize `SENTRY_DB_POOL_SIZE`

### Performance Tuning

1. **Database Optimization**
   ```sql
   -- In PostgreSQL
   ALTER SYSTEM SET shared_buffers = '256MB';
   ALTER SYSTEM SET effective_cache_size = '1GB';
   ```

2. **Redis Optimization**
   ```bash
   # In docker-compose.yml redis command
   redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
   ```

## 📞 Support

For issues with Sentry itself:
- [Sentry Documentation](https://docs.sentry.io/)
- [Sentry GitHub](https://github.com/getsentry/sentry)

For UIForge-specific issues:
- Check project documentation
- Review integration guides
- Monitor logs for error patterns
