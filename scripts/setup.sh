#!/bin/bash

set -e

echo "========================================="
echo "Energy Grid & Battery Management Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Error: python3 is required but not installed.${NC}" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Error: docker-compose is required but not installed.${NC}" >&2; exit 1; }
echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update .env with your PostgreSQL password and SECRET_KEY${NC}"
    echo ""
fi

# Check if DATABASE_URL needs updating
if grep -q "YOUR_POSTGRES_PASSWORD" .env; then
    echo -e "${YELLOW}⚠️  Please update DATABASE_URL in .env with your PostgreSQL password${NC}"
    echo ""
fi

# Start infrastructure
echo "Starting infrastructure services..."
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
echo -e "${GREEN}✓ Infrastructure services started${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5
until docker exec energy-grid-postgres pg_isready -U user > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
echo ""

# Create database if it doesn't exist
echo "Creating database if needed..."
docker exec -i energy-grid-postgres psql -U user -c "CREATE DATABASE energy_grid;" 2>/dev/null || echo "Database already exists"
echo -e "${GREEN}✓ Database ready${NC}"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run migrations
echo "Running database migrations..."
cd cloud_backend
alembic upgrade head
cd ..
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

echo "========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your PostgreSQL password"
echo "2. Start the API server:"
echo "   cd cloud_backend"
echo "   source ../venv/bin/activate"
echo "   uvicorn api.main:app --reload"
echo ""
echo "3. Access the API:"
echo "   - Health: http://localhost:8000/health"
echo "   - Docs: http://localhost:8000/api/docs"
echo ""
echo "4. Start Grafana (optional):"
echo "   docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d"
echo "   Access: http://localhost:3000 (admin/admin)"
echo ""
