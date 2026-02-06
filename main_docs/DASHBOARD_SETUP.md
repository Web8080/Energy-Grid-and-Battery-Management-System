# Dashboard Setup Guide

## Dashboard Options

Based on the system architecture, you have two dashboard options:

### Option 1: Grafana (Recommended for Monitoring) ✅

**Status**: Already configured and ready to use

**Setup**:
```bash
docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d
```

**Access**:
- URL: http://localhost:3000
- Default credentials: `admin` / `admin` (change on first login)

**Features**:
- Pre-configured Prometheus data source
- Metrics visualization
- Real-time monitoring dashboards
- Alert management
- Custom dashboard creation

**Best For**: System monitoring, metrics visualization, operational dashboards

---

### Option 2: React Dashboard (Custom Frontend)

**Status**: Backend API ready, frontend needs to be built

**Architecture**:
- Backend: FastAPI (already running)
- Frontend: React 18+ (needs to be created)
- Real-time: WebSocket support (already implemented)

**Hosting Options**:

#### A. Vercel (Recommended for React Frontend) ⭐

**Why Vercel**:
- ✅ Free tier available
- ✅ Easy deployment
- ✅ Automatic HTTPS
- ✅ Fast global CDN
- ✅ Perfect for React/Next.js apps
- ✅ Environment variables management
- ✅ Preview deployments

**Deployment Steps**:
1. Create React app in `analytics/frontend/`
2. Connect to Vercel:
   ```bash
   npm i -g vercel
   vercel login
   cd analytics/frontend
   vercel
   ```
3. Configure environment variables in Vercel dashboard:
   - `REACT_APP_API_URL=https://your-api-domain.com`
   - `REACT_APP_WS_URL=wss://your-api-domain.com`
4. Deploy: `vercel --prod`

**Cost**: Free for hobby projects, $20/month for teams

#### B. AWS (Full-Stack Deployment)

**Why AWS**:
- ✅ Full control over infrastructure
- ✅ Better for full-stack applications
- ✅ Scalable and reliable
- ✅ Integration with other AWS services

**Deployment Options**:
1. **AWS Amplify** (Easiest for React):
   ```bash
   # Install Amplify CLI
   npm install -g @aws-amplify/cli
   amplify init
   amplify add hosting
   amplify publish
   ```

2. **AWS EC2/ECS** (For full-stack):
   - Deploy both frontend and backend
   - Use Docker containers
   - Load balancer for scaling

**Cost**: Pay-as-you-go, ~$10-50/month for small deployments

#### C. Netlify (Alternative to Vercel)

**Why Netlify**:
- ✅ Similar to Vercel
- ✅ Good free tier
- ✅ Easy deployment

**Deployment**: Similar to Vercel

---

## System Requirements Analysis

Based on `docs/architecture/SYSTEM_DESIGN.md`:

### Current Architecture:
- **Backend**: FastAPI (Python) - needs server hosting
- **Frontend**: React (static files) - can be CDN-hosted
- **Database**: PostgreSQL - needs managed database
- **Cache**: Redis - needs managed cache
- **Message Queue**: RabbitMQ - needs server hosting
- **Observability**: Prometheus/Grafana - can be self-hosted or managed

### Recommended Hosting Strategy:

**Development**:
- ✅ Everything local via Docker Compose
- ✅ Grafana for monitoring dashboards

**Production**:

1. **Backend API**: 
   - AWS ECS/Fargate (containerized)
   - Or Railway/Render (simpler)
   - Or DigitalOcean App Platform

2. **Frontend Dashboard**:
   - **Vercel** (recommended) - best for React apps
   - Or AWS Amplify
   - Or Netlify

3. **Database**:
   - AWS RDS PostgreSQL
   - Or Railway PostgreSQL
   - Or Supabase

4. **Redis**:
   - AWS ElastiCache
   - Or Redis Cloud (free tier)

5. **RabbitMQ**:
   - AWS MQ
   - Or CloudAMQP (free tier)
   - Or self-hosted on EC2

6. **Monitoring**:
   - Grafana Cloud (free tier)
   - Or self-hosted Grafana

---

## Recommendation

**For Dashboard**: Use **Vercel** for React frontend
- Easiest setup
- Free tier sufficient for development
- Perfect for static React apps
- Connects easily to your API backend

**For Full System**: Use **AWS** or **Railway**
- AWS: More control, better for scale
- Railway: Simpler, good for MVP

---

## Next Steps

1. **For Grafana** (immediate):
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.observability.yml up -d
   ```
   Access: http://localhost:3000

2. **For React Dashboard** (future):
   - Create React app in `analytics/frontend/`
   - Connect to FastAPI backend
   - Deploy to Vercel when ready

---

**Current Status**: Grafana is ready to use. React dashboard needs to be built.
