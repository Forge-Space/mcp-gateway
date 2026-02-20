#!/bin/bash

# Sentry Setup Script
# This script sets up a self-hosted Sentry instance

set -e

echo "🚀 Setting up Sentry for UIForge Ecosystem..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Create sentry directory if it doesn't exist
SENTRY_DIR="$(dirname "$0")"
cd "$SENTRY_DIR"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration before continuing!"
    echo "   Required fields: SENTRY_DB_PASSWORD, SENTRY_SECRET_KEY"
    echo ""
    read -p "Press Enter to continue after editing .env file..."
fi

# Generate secure values if not set
if grep -q "your_secure_postgres_password_here" .env; then
    echo "🔐 Generating secure passwords and keys..."
    
    # Generate random passwords
    DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SECRET_KEY=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-50)
    SSO_KEY=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    SSO_SECRET=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    
    # Update .env file
    sed -i.bak "s/your_secure_postgres_password_here/$DB_PASSWORD/" .env
    sed -i.bak "s/your_super_long_random_secret_key_at_least_32_characters/$SECRET_KEY/" .env
    sed -i.bak "s/your_sso_key_here/$SSO_KEY/" .env
    sed -i.bak "s/your_sso_secret_here/$SSO_SECRET/" .env
    
    echo "✅ Generated secure configuration"
fi

# Create Docker volumes
echo "📦 Creating Docker volumes..."
docker volume create sentry_postgres_data 2>/dev/null || true
docker volume create sentry_redis_data 2>/dev/null || true
docker volume create sentry_sentry_data 2>/dev/null || true

# Start Sentry services
echo "🚀 Starting Sentry services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🔍 Checking service health..."
for i in {1..10}; do
    if curl -f http://localhost:9000/_health/ > /dev/null 2>&1; then
        echo "✅ Sentry is ready!"
        break
    else
        echo "⏳ Waiting for Sentry... ($i/10)"
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo "❌ Sentry failed to start. Check logs:"
        docker-compose logs web
        exit 1
    fi
done

# Create initial organization and projects
echo "🏗️  Setting up Sentry organization..."
docker-compose exec web sentry createuser \
    --superuser \
    --email "${SENTRY_ADMIN_EMAIL:-admin@localhost}" \
    --password admin123 \
    --no-input || true

echo ""
echo "🎉 Sentry setup complete!"
echo ""
echo "📍 Access Sentry at: http://localhost:9000"
echo "🔑 Default credentials: admin@localhost / admin123"
echo ""
echo "📝 Next steps:"
echo "1. Log in to Sentry and change the default password"
echo "2. Create projects for each application:"
echo "   - mcp-gateway (Python)"
echo "   - uiforge-mcp (Node.js)"
echo "   - uiforge-webapp (Next.js)"
echo "   - forge-patterns (Development)"
echo "3. Get DSN URLs for each project"
echo "4. Update application environment variables with SENTRY_DSN"
echo ""
echo "🔧 Management commands:"
echo "  Start:  docker-compose up -d"
echo "  Stop:   docker-compose down"
echo "  Logs:   docker-compose logs -f"
echo "  Update: docker-compose pull && docker-compose up -d"
echo ""