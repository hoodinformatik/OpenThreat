#!/bin/bash

# OpenThreat Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 OpenThreat Production Deployment"
echo "===================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ Error: .env file not found${NC}"
    echo "Please create .env file from .env.example"
    exit 1
fi

# Load environment variables
source .env

# Check required variables
required_vars=("DATABASE_URL" "POSTGRES_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${RED}❌ Error: $var is not set in .env${NC}"
        exit 1
    fi
done

echo -e "${GREEN}✓${NC} Environment variables loaded"

# Pull latest code
echo ""
echo "📥 Pulling latest code..."
git pull origin main

# Build images
echo ""
echo "🔨 Building Docker images..."
docker compose build --no-cache backend frontend celery-worker celery-beat

# Stop old containers
echo ""
echo "🛑 Stopping old containers..."
docker compose down

# Start database and wait
echo ""
echo "🗄️  Starting database..."
docker compose up -d postgres redis
sleep 10

# Run migrations
echo ""
echo "📊 Running database migrations..."
docker compose run --rm backend alembic upgrade head

# Start all services
echo ""
echo "🚀 Starting all services..."
docker compose up -d

# Wait for Celery to be ready and trigger initial news fetch
echo ""
echo "📰 Triggering initial news fetch..."
sleep 5
docker compose exec -T celery-worker python -c "from backend.tasks.news_tasks import fetch_news_articles_task; fetch_news_articles_task.delay()" || echo -e "${YELLOW}⚠️ News fetch trigger failed - will run on schedule${NC}"

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 15

# Health check
echo ""
echo "🏥 Running health checks..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker compose logs backend
    exit 1
fi

if curl -f http://localhost > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend is healthy"
else
    echo -e "${RED}❌ Frontend health check failed${NC}"
    docker compose logs frontend
    exit 1
fi

# Check Celery services
if docker compose ps celery-worker | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Celery worker is running"
else
    echo -e "${YELLOW}⚠️ Celery worker may not be running${NC}"
fi

if docker compose ps celery-beat | grep -q "Up"; then
    echo -e "${GREEN}✓${NC} Celery beat scheduler is running"
else
    echo -e "${YELLOW}⚠️ Celery beat scheduler may not be running${NC}"
fi

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

# Show logs
echo ""
echo "📝 Recent logs:"
docker compose logs --tail=20

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost"
echo "   API:      http://localhost/api/v1"
echo "   Docs:     http://localhost/api/v1/docs"
echo "   Health:   http://localhost/health"
echo ""
echo "📊 Monitoring:"
echo "   docker compose logs -f"
echo "   docker compose ps"
echo ""
echo "🛑 To stop:"
echo "   docker compose down"
