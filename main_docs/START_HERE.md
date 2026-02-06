# 🚀 START HERE - Energy Grid & Battery Management System

## Quick Setup (5 Minutes)

### 1. Update Environment Variables

**File Location**: `.env` (in project root)

**Required Updates**:
1. **DATABASE_URL**: Replace `YOUR_POSTGRES_PASSWORD` with your PostgreSQL password
   ```bash
   DATABASE_URL=postgresql://user:your_password_here@localhost:5432/energy_grid
   ```

2. **SECRET_KEY**: Already generated, but verify it's set
   ```bash
   SECRET_KEY=befYVjnnfX4l_20hokyNrYYNEq3PZz0hubL-_REwwV0
   ```

### 2. Push to GitHub (Do This First!)

Run these commands in your terminal:

```bash
cd /Users/user/AI_Autonomous_Engergy_grid_and_smart_battery_management_systems

# Initialize git (if needed)
git init

# Add remote
git remote add origin https://github.com/Web8080/Energy-Grid-and-Battery-Management-System.git

# Stage all files (sensitive files auto-excluded)
git add .

# Commit
git commit -m "Initial commit: Energy Grid & Battery Management System"

# Push
git branch -M main
git push -u origin main
```

**Note**: The `.env` file and sensitive files are automatically excluded by `.gitignore`

### 3. Start Infrastructure

**Option A: Automated Setup Script**
```bash
./scripts/setup.sh
```

**Option B: Manual Setup**
```bash
# Start services
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d

# Create database (if using local PostgreSQL)
psql -U user -h localhost -c "CREATE DATABASE energy_grid;"

# Run migrations
cd cloud_backend
alembic upgrade head
cd ..
```

### 4. Start API Server

```bash
# Activate virtual environment
source venv/bin/activate  # or: venv\Scripts\activate on Windows

# Start API
cd cloud_backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Available at**: http://localhost:8000
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/api/docs (if DEBUG=true)

### 5. Start Dashboard (Grafana)

```bash
docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d
```

**Access Grafana**: http://localhost:3000
- Username: `admin`
- Password: `admin` (change on first login)

### 6. Test Device Daemon (Simulation)

```bash
export DEVICE_ID=RPI-001
export API_BASE_URL=http://localhost:8000
export MQTT_BROKER=localhost

cd device_fleet/daemon
python battery_daemon.py
```

## 📋 Environment Variables Needed

### Required from You:
1. **PostgreSQL Password** → Update `DATABASE_URL` in `.env`
2. **SECRET_KEY** → Already generated (can keep or regenerate)

### Optional:
- `CORS_ORIGINS` → Add your frontend URLs
- `API_KEY` → For external integrations
- `MQTT_USERNAME`/`MQTT_PASSWORD` → If MQTT requires auth

## 📚 Documentation Files

- `QUICK_START.md` - Detailed step-by-step guide
- `ENVIRONMENT_SETUP.md` - Environment variable reference
- `GIT_SETUP.md` - Git repository setup instructions
- `DASHBOARD_SETUP.md` - Dashboard hosting options (Vercel/AWS)
- `SETUP_GUIDE.md` - Comprehensive setup guide

## 🎯 Dashboard Hosting Recommendation

**For React Dashboard**: Use **Vercel** (recommended)
- Free tier available
- Perfect for React apps
- Easy deployment
- See `DASHBOARD_SETUP.md` for details

**For Monitoring**: Use **Grafana** (already configured)
- Runs locally via Docker
- Access: http://localhost:3000

## ✅ Verification

Test the setup:

```bash
# Health check
curl http://localhost:8000/health

# Should return: {"status":"healthy","timestamp":"...","service":"energy-grid-api"}
```

## 🔒 Security Notes

- ✅ `.env` file is excluded from Git
- ✅ Sensitive files are in `.gitignore`
- ✅ Never commit secrets or API keys
- ✅ Use different secrets for production

## 🆘 Troubleshooting

**Database Connection Failed**:
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify password in `.env` matches your PostgreSQL password

**Port Already in Use**:
- Check: `lsof -i :8000`
- Change port in `.env`: `API_PORT=8001`

**Need Help?** Check the detailed guides in the project root.

---

**Ready to start?** Follow steps 1-6 above! 🚀
