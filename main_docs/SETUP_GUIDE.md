# Setup Guide: Energy Grid & Battery Management System

## Quick Start

### 1. Environment Configuration

The `.env` file has been created. You need to update the following:

**REQUIRED - Update these values:**

1. **DATABASE_URL**: Replace `YOUR_POSTGRES_PASSWORD` with your PostgreSQL password
   ```bash
   DATABASE_URL=postgresql://user:your_actual_password@localhost:5432/energy_grid
   ```

2. **SECRET_KEY**: Replace with a strong random secret (32+ characters)
   - You can generate one using: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Or use: `openssl rand -hex 32`

**OPTIONAL - Configure these if needed:**

- `CORS_ORIGINS`: Add your frontend URLs (comma-separated)
- `API_KEY`: For external API integrations
- `MQTT_USERNAME`/`MQTT_PASSWORD`: If MQTT requires authentication

### 2. Start Infrastructure Services

```bash
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

This starts:
- PostgreSQL (port 5432)
- Redis (port 6379)
- RabbitMQ (port 5672, management UI on 15672)

### 3. Create Database and Run Migrations

**First, create the database:**
```bash
# Connect to PostgreSQL
psql -U user -h localhost

# Create database
CREATE DATABASE energy_grid;

# Exit
\q
```

**Then run migrations:**
```bash
cd cloud_backend
alembic upgrade head
```

### 4. Start the API Server

```bash
cd cloud_backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000
API docs (if DEBUG=true): http://localhost:8000/api/docs

### 5. Start Observability Stack (Optional)

```bash
docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 6. Test the Setup

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","timestamp":"...","service":"energy-grid-api"}
```

## Dashboard Setup

### Option 1: Grafana (Recommended for Monitoring)

Grafana is already configured and runs via Docker:
- Access: http://localhost:3000
- Default credentials: admin/admin
- Pre-configured dashboards for metrics visualization

### Option 2: React Dashboard (Custom Frontend)

**For local development:**
```bash
cd analytics/frontend
npm install
npm run dev
```

**For production hosting:**

**Vercel (Frontend only - recommended for React):**
- Best for static React apps
- Free tier available
- Easy deployment
- Connect to your API backend

**AWS (Full-stack):**
- Use AWS Amplify for React frontend
- Or EC2/ECS for full deployment
- Better for full-stack applications

**Recommendation**: Use Grafana for monitoring dashboards (already set up) and Vercel for custom React frontend if you build one.

## Device Daemon Simulation

To simulate the device daemon locally:

```bash
# Set device environment variables
export DEVICE_ID=RPI-001
export API_BASE_URL=http://localhost:8000
export MQTT_BROKER=localhost

# Run the daemon
cd device_fleet/daemon
python battery_daemon.py
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running: `docker ps`
- Check DATABASE_URL format in .env
- Ensure database exists: `psql -U user -h localhost -l`

### Port Conflicts
- Check if ports are in use: `lsof -i :8000`
- Update ports in .env if needed

### Redis Connection Issues
- Verify Redis is running: `docker ps | grep redis`
- Test connection: `redis-cli ping`

### RabbitMQ Issues
- Check RabbitMQ management UI: http://localhost:15672
- Default credentials: guest/guest

## Next Steps

1. Create an admin user (via API or database)
2. Configure device certificates for mTLS
3. Set up monitoring alerts
4. Deploy to production (see docs/deployment/)

---

**Note**: Never commit the `.env` file to Git. It's already in `.gitignore`.
