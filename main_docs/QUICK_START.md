# Quick Start Guide

## Prerequisites Check

- ✅ Python 3.11+
- ✅ Docker & Docker Compose
- ✅ PostgreSQL (or use Docker)
- ✅ Git

## Step-by-Step Setup

### Step 1: Update .env File

**Location**: `/Users/user/AI_Autonomous_Engergy_grid_and_smart_battery_management_systems/.env`

**Required Updates**:
1. Replace `YOUR_POSTGRES_PASSWORD` in `DATABASE_URL` with your PostgreSQL password
2. Verify `SECRET_KEY` is set (already generated)

```bash
# Edit .env file
nano .env
# or
code .env
```

### Step 2: Push to GitHub (Manual)

Run these commands in your terminal:

```bash
cd /Users/user/AI_Autonomous_Engergy_grid_and_smart_battery_management_systems

# Initialize git (if needed)
git init

# Add remote
git remote add origin https://github.com/Web8080/Energy-Grid-and-Battery-Management-System.git

# Stage files
git add .

# Commit
git commit -m "Initial commit: Energy Grid & Battery Management System"

# Push
git branch -M main
git push -u origin main
```

See `GIT_SETUP.md` for detailed instructions.

### Step 3: Start Infrastructure

```bash
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)  
- RabbitMQ (port 5672, management UI: http://localhost:15672)

**Verify**:
```bash
docker ps
# Should show postgres, redis, rabbitmq containers running
```

### Step 4: Create Database

```bash
# Connect to PostgreSQL
psql -U user -h localhost

# Create database
CREATE DATABASE energy_grid;

# Exit
\q
```

**Note**: If using Docker PostgreSQL, the database is created automatically.

### Step 5: Run Database Migrations

```bash
cd cloud_backend
alembic upgrade head
```

This creates all required tables:
- `users`
- `devices`
- `schedules`

### Step 6: Start API Server

```bash
cd cloud_backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoints**:
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs (if DEBUG=true)
- Metrics: http://localhost:8000/metrics

### Step 7: Start Observability Stack (Optional)

```bash
docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d
```

**Access**:
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Step 8: Test Device Daemon (Simulation)

```bash
# Set environment variables
export DEVICE_ID=RPI-001
export API_BASE_URL=http://localhost:8000
export MQTT_BROKER=localhost

# Run daemon
cd device_fleet/daemon
python battery_daemon.py
```

## Verification

### Test API Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"...","service":"energy-grid-api"}
```

### Test Authentication
```bash
# Create a test user first (via API or database)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'
```

## Troubleshooting

### Database Connection Failed
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify DATABASE_URL in .env matches your setup
- Check password is correct

### Port Already in Use
- Check what's using the port: `lsof -i :8000`
- Change port in .env: `API_PORT=8001`

### Redis Connection Failed
- Verify Redis is running: `docker ps | grep redis`
- Test connection: `redis-cli ping`

## Next Steps

1. ✅ Create admin user
2. ✅ Configure device certificates
3. ✅ Set up monitoring alerts
4. ✅ Build React dashboard (optional)
5. ✅ Deploy to production

## Dashboard Access

**Grafana** (Monitoring):
- URL: http://localhost:3000
- Credentials: admin/admin

**React Dashboard** (Custom):
- Not yet built - see `DASHBOARD_SETUP.md` for options
- Recommended: Vercel for hosting

---

**Need Help?** Check:
- `SETUP_GUIDE.md` - Detailed setup instructions
- `ENVIRONMENT_SETUP.md` - Environment variable guide
- `DASHBOARD_SETUP.md` - Dashboard hosting options
- `GIT_SETUP.md` - Git repository setup
