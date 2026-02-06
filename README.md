# Autonomous Energy Grid & Smart Battery Management System

## Purpose and Product Context

This system is a production-grade AI-enabled platform that optimizes energy distribution across a regional smart grid by integrating and managing thousands of Raspberry Pi-based smart batteries. The platform enables these batteries to participate in energy trading markets by following optimized charge/discharge schedules, while maintaining real-time observability, fault tolerance, and actionable analytics.

**Primary Use Case**: Grid operators and energy traders need to remotely control and optimize thousands of distributed battery systems to stabilize the grid, participate in energy markets, and maximize revenue while ensuring reliability and compliance.

**Problem Solved**: Traditional battery management systems lack the scalability, observability, and AI-driven optimization needed to manage large fleets of distributed energy storage devices participating in dynamic energy markets.

**Key Value Proposition**:
- Reliable remote control of 10,000+ battery devices
- AI-driven schedule optimization reducing energy costs by >10%
- Real-time observability and analytics for operational decision-making
- Automated CI/CD and model deployment for rapid iteration
- Production-grade reliability (>99.9% uptime) and fault tolerance

## Architecture Overview

The system follows a **Hybrid Modular Monolith with Message Queue Integration** architecture, balancing scalability with operational simplicity.

### Core Components

**Cloud Backend (Modular Monolith)**:
- Schedule Module: REST API for schedule ingestion and distribution
- Device Module: Device registration, status tracking, acknowledgement processing
- ML Module: Schedule optimization predictions and model serving
- Analytics Module: Aggregation queries and report generation

**Message Queue (RabbitMQ)**:
- Decouples cloud backend from device fleet
- Handles schedule distribution via MQTT topics
- Processes device acknowledgements asynchronously
- Supports 100K+ messages/second throughput

**Database Layer**:
- PostgreSQL: Primary database for schedules, devices, execution logs
- Read Replicas: Scale read queries horizontally
- Redis Cache: Schedule and device status caching (5-minute TTL)
- InfluxDB/Prometheus: Time-series metrics and execution logs

**Device Fleet (Raspberry Pi)**:
- Execution daemon with MQTT client
- Local SQLite for schedule persistence
- Command execution at scheduled intervals
- Health monitoring and acknowledgement publishing

**Observability Stack**:
- Prometheus: Metrics collection and storage
- Grafana: Metrics visualization and dashboards
- Structured Logging: JSON logs with correlation IDs
- Distributed Tracing: OpenTelemetry/Jaeger for request tracing

**Analytics & Dashboard**:
- React/Grafana frontend for real-time monitoring
- REST API backend for analytics queries
- WebSocket server for real-time updates
- Historical analytics and reporting

### Data Flow

**Schedule Distribution**:
```
External Schedule Source → Schedule Ingestion API → PostgreSQL → 
Redis Cache → RabbitMQ → Device (MQTT) → Local SQLite → Command Execution
```

**Device Acknowledgement**:
```
Device Execution → Acknowledgement → RabbitMQ → Device Module → 
PostgreSQL + InfluxDB → Analytics Aggregation → Dashboard Updates
```

### Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Pydantic
- **Message Queue**: RabbitMQ with MQTT plugin
- **Database**: PostgreSQL 15+, Redis 7+, InfluxDB 2.x
- **ML**: scikit-learn, pandas, numpy
- **Observability**: Prometheus, Grafana, OpenTelemetry
- **Frontend**: React 18+ or Grafana dashboards
- **Infrastructure**: Docker, Kubernetes, GitHub Actions
- **Device**: Python 3.11+ on Raspberry Pi OS

## Key Workflows

### Schedule Distribution Workflow

1. External system or ML optimization service creates battery schedule
2. Schedule ingested via REST API (`POST /schedules`)
3. Schedule validated (mode, rate_kw, time intervals, conflicts)
4. Schedule stored in PostgreSQL and cached in Redis
5. Schedule update published to RabbitMQ `schedule.updates` topic
6. ML module consumes update and generates optimized schedule (optional)
7. Optimized schedule stored and published to device-specific MQTT topic
8. Device receives schedule via MQTT subscription
9. Device validates and stores schedule locally in SQLite
10. Device executes commands at scheduled intervals

### Command Execution Workflow

1. Device daemon checks current time against schedule
2. At scheduled interval (e.g., 00:00, 00:30), device validates schedule entry
3. Device executes charge (mode=2) or discharge (mode=1) command
4. Device records execution result (success/failure, actual rate, timestamp)
5. Device publishes acknowledgement to RabbitMQ `device.acks` topic
6. Cloud backend Device Module consumes acknowledgement
7. Acknowledgement validated and stored in PostgreSQL `execution_logs`
8. Metrics written to InfluxDB for observability
9. Analytics aggregation updates dashboard data
10. Alerts triggered if execution failed

### ML Optimization Workflow

1. Historical energy price and demand data collected
2. Features engineered (price trends, demand patterns, device history)
3. ML model trained on historical data
4. Model evaluated and validated
5. Model deployed to serving endpoint
6. Schedule update triggers ML prediction request
7. Features computed for prediction
8. Model generates optimized schedule
9. Optimized schedule stored and distributed to device
10. Model performance monitored (accuracy, latency, drift)

### Failure Recovery Workflow

1. System detects failure (API instance down, database unavailable, device offline)
2. Health checks fail, alerts triggered
3. Load balancer routes traffic away from failed instance
4. Message queue buffers messages during outages
5. Devices use cached schedules if cloud unavailable
6. Automatic instance replacement (Kubernetes)
7. Database failover to read replica if primary fails
8. System recovers and processes buffered messages
9. Monitoring confirms recovery
10. Post-mortem analysis and improvements

## Setup Instructions

### Prerequisites

**Required**:
- Python 3.11 or higher
- Docker and Docker Compose
- PostgreSQL 15+ (or use Docker image)
- RabbitMQ 3.12+ (or use Docker image)
- Redis 7+ (or use Docker image)

**Optional**:
- Node.js 18+ (for frontend development, if using React)
- Kubernetes cluster (for production deployment)

### Quick Setup

For the fastest setup, use the automated setup script:

```bash
./scripts/setup.sh
```

This script will:
1. Check prerequisites
2. Start infrastructure services
3. Create database
4. Install dependencies
5. Run migrations

### Manual Setup

For detailed manual setup instructions, see `main_docs/QUICK_START.md` or follow these steps:

1. **Clone the repository**:
```bash
git clone https://github.com/Web8080/Energy-Grid-and-Battery-Management-System.git
cd Energy-Grid-and-Battery-Management-System
```

2. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your PostgreSQL password and other settings
# See main_docs/ENVIRONMENT_SETUP.md for details
```

3. **Start infrastructure services**:
```bash
docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d
```

4. **Run database migrations**:
```bash
cd cloud_backend
alembic upgrade head
cd ..
```

5. **Start the backend API**:
```bash
source venv/bin/activate  # Create venv first if needed: python -m venv venv
pip install -r requirements.txt
cd cloud_backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Verify setup**:
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","timestamp":"...","service":"energy-grid-api"}
```

For complete setup instructions, troubleshooting, and configuration details, see the documentation in `main_docs/`.

### Production Deployment

See `docs/deployment/PRODUCTION_DEPLOYMENT.md` for detailed production deployment instructions using Kubernetes.

### Quick Start Guide

For a quick setup guide, see `main_docs/START_HERE.md` or `main_docs/QUICK_START.md`.

Additional documentation:
- `main_docs/ENVIRONMENT_SETUP.md` - Environment variable configuration
- `main_docs/DASHBOARD_SETUP.md` - Dashboard hosting and setup
- `main_docs/GIT_SETUP.md` - Git repository setup
- `main_docs/SETUP_GUIDE.md` - Comprehensive setup instructions

## Configuration

### Environment Variables

**Critical Configuration** (must be set before starting):

- `DATABASE_URL`: PostgreSQL connection string
  - Format: `postgresql://user:password@host:port/database`
  - Example: `postgresql://user:your_password@localhost:5432/energy_grid`
  - **Action Required**: Update with your PostgreSQL password in `.env`

- `SECRET_KEY`: JWT token signing key (32+ characters)
  - Generated automatically if not set (development only)
  - **Action Required**: Set a strong random key for production
  - Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

**Required Services**:
- `REDIS_URL`: Redis connection (default: `redis://localhost:6379/0`)
- `RABBITMQ_URL`: RabbitMQ connection (default: `amqp://guest:guest@localhost:5672/`)

**Security Configuration**:
- `CORS_ORIGINS`: Allowed frontend origins (comma-separated, no wildcard in production)
- `API_KEY`: API key for external integrations (optional)

**Optional Configuration**:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARN, ERROR) - default: INFO
- `ENVIRONMENT`: Environment name (development, staging, production) - default: development
- `DEBUG`: Debug mode (false in production, true for development)
- `CACHE_TTL`: Cache TTL in seconds - default: 300
- `MQTT_BROKER_HOST`: MQTT broker hostname - default: localhost
- `MQTT_BROKER_PORT`: MQTT broker port - default: 1883

**Complete Reference**: See `main_docs/ENVIRONMENT_SETUP.md` for all environment variables and configuration options.

### Configuration Files

**Application Configuration**:
- `cloud_backend/config/settings.py`: Centralized settings management
- `cloud_backend/config/database.py`: Database connection and pooling configuration

**Infrastructure Configuration**:
- `infrastructure/docker/`: Docker Compose files for local development
- `infrastructure/kubernetes/`: Kubernetes manifests for production deployment

**Observability Configuration**:
- `observability/metrics/prometheus.yml`: Prometheus scraping configuration
- `observability/metrics/grafana/`: Grafana dashboard definitions

**Message Queue Configuration**:
- RabbitMQ queues, exchanges, and routing keys defined in `cloud_backend/services/message_queue.py`
- MQTT topics configured for device communication

## Failure Modes

### Database Failure

**Symptoms**: API returns 500 errors, schedule queries fail, device acknowledgements not processed.

**Causes**: Primary database instance failure, network partition, connection pool exhaustion.

**Recovery**:
1. Automatic failover to read replica for read queries
2. Write operations queued in message queue
3. Database instance automatically replaced (Kubernetes)
4. Buffered writes processed after recovery

**Prevention**: Read replicas, connection pooling, health checks, automatic instance replacement.

### Message Queue Failure

**Symptoms**: Devices cannot receive schedules, acknowledgements not processed, message queue depth increases.

**Causes**: RabbitMQ node failure, network issues, queue overflow.

**Recovery**:
1. Fallback to direct HTTP polling for devices
2. RabbitMQ cluster automatic failover
3. Message persistence ensures no data loss
4. Buffered messages processed after recovery

**Prevention**: RabbitMQ clustering, mirrored queues, message persistence, health monitoring.

### API Instance Failure

**Symptoms**: 502/503 errors, devices cannot reach API, health checks fail.

**Causes**: Application crash, out of memory, high CPU usage, deployment issues.

**Recovery**:
1. Load balancer routes traffic away from failed instance
2. Kubernetes automatically replaces failed pod
3. New instance starts and joins cluster
4. Health checks confirm recovery

**Prevention**: Resource limits, health checks, auto-scaling, graceful shutdowns.

### Device Network Partition

**Symptoms**: Device offline status, no acknowledgements received, schedules not delivered.

**Causes**: Network connectivity issues, device power failure, firewall blocking.

**Recovery**:
1. Device uses cached schedule locally
2. Device retries connection with exponential backoff
3. Device sends buffered acknowledgements on reconnection
4. Cloud backend processes delayed acknowledgements

**Prevention**: Local schedule caching, retry logic, health monitoring, network redundancy.

### ML Model Degradation

**Symptoms**: Prediction accuracy decreases, optimization results worsen, model drift alerts.

**Causes**: Data distribution shift, feature drift, model staleness.

**Recovery**:
1. Automatic model performance monitoring detects degradation
2. Fallback to rule-based schedules
3. Model retrained on recent data
4. New model version deployed via A/B testing
5. Old model rolled back if new model performs worse

**Prevention**: Model monitoring, feature drift detection, regular retraining, A/B testing.

## Debugging Tips

### Enable Debug Logging

Set `LOG_LEVEL=DEBUG` in environment variables or `cloud_backend/config/settings.py`:

```python
LOG_LEVEL = "DEBUG"
```

### Check API Health

```bash
curl http://localhost:8000/health
curl http://localhost:8000/metrics  # Prometheus metrics
```

### View Application Logs

```bash
# Docker logs
docker-compose logs -f cloud_backend

# Kubernetes logs
kubectl logs -f deployment/cloud-backend-api

# Local development
tail -f logs/app.log
```

### Database Debugging

```bash
# Connect to database
psql $DATABASE_URL

# Check schedule distribution
SELECT device_id, COUNT(*) FROM execution_logs GROUP BY device_id;

# Check recent failures
SELECT * FROM execution_logs WHERE status = 'failed' ORDER BY created_at DESC LIMIT 10;
```

### Message Queue Debugging

```bash
# RabbitMQ management UI
open http://localhost:15672

# Check queue depth
rabbitmqctl list_queues name messages

# Check consumer status
rabbitmqctl list_consumers
```

### Device Debugging

```bash
# SSH into device
ssh pi@device-ip

# Check daemon logs
tail -f /var/log/battery-daemon.log

# Check local schedule storage
sqlite3 /var/lib/battery-daemon/schedules.db "SELECT * FROM schedules;"

# Test MQTT connection
mosquitto_sub -h mqtt-broker -t "devices/+/schedule/response"
```

### Distributed Tracing

View traces in Jaeger UI (if configured):
```bash
open http://localhost:16686
```

Search for traces by device_id, correlation_id, or operation name.

### Common Issues

**Issue**: Schedules not reaching devices
- Check RabbitMQ connection and queue depth
- Verify MQTT topic subscriptions
- Check device network connectivity
- Review device daemon logs

**Issue**: High API latency
- Check database query performance
- Verify Redis cache hit rates
- Review message queue depth
- Check API instance resource usage

**Issue**: ML predictions inaccurate
- Check feature drift metrics
- Verify model version in use
- Review training data quality
- Check prediction latency (may indicate issues)

## Explicit Non-Goals

This system explicitly does NOT include:

- **Device Hardware Design**: Physical battery hardware, Raspberry Pi hardware modifications, or firmware development (assumes existing hardware)
- **Energy Market Integration**: Direct integration with energy trading market APIs (assumes external system provides schedules)
- **Customer-Facing Applications**: Mobile apps, customer portals, or billing systems (internal operations tool)
- **Multi-Tenant SaaS**: Single-tenant deployment only; no multi-tenant features
- **Physical Installation**: Battery installation, wiring, or physical maintenance
- **Payment Processing**: Billing, invoicing, or payment collection
- **Advanced ML Research**: Cutting-edge ML research; focuses on production ML operations

## Known Debt

### Technical Debt

1. **ML Module Scaling**: ML module currently scales with API instances; should be extracted to independent service for better scaling at >15K devices. **Impact**: Medium. **Planned**: Phase 6 (post-MVP).

2. **Single Region Deployment**: Currently single-region only; multi-region support needed for global device fleet. **Impact**: Low (current scale). **Planned**: Phase 7.

3. **Basic OTA Updates**: Device firmware update system is basic; needs advanced rollback and staged rollout. **Impact**: Medium. **Planned**: Phase 6.

4. **Analytics Aggregation**: Some analytics queries are slow (>5 seconds) for large date ranges; needs optimization or pre-aggregation. **Impact**: Low. **Planned**: Ongoing optimization.

### Performance Considerations

- Database query optimization needed for analytics queries on large datasets
- Message queue partitioning by device_id hash for better distribution
- Redis cache warming for frequently accessed schedules
- ML feature computation caching to reduce latency

### Architectural Limitations

- Modular monolith limits independent scaling of ML module (acceptable for current scale)
- Single message queue cluster (acceptable for current scale, will need partitioning at larger scale)
- Basic device firmware update capabilities (sufficient for MVP, needs enhancement)

### Future Enhancements

1. Extract ML service to independent microservice
2. Multi-region deployment with data replication
3. Advanced OTA update system with A/B testing
4. ML-based anomaly detection and predictive maintenance
5. Real-time energy market integration for dynamic optimization
6. Advanced analytics with ML-based insights

## Documentation

### Main Documentation

All setup and configuration guides are located in the `main_docs/` directory:

- **Quick Start**: `main_docs/START_HERE.md` - Get started in 5 minutes
- **Setup Guide**: `main_docs/SETUP_GUIDE.md` - Comprehensive setup instructions
- **Environment Setup**: `main_docs/ENVIRONMENT_SETUP.md` - Environment variables reference
- **Dashboard Setup**: `main_docs/DASHBOARD_SETUP.md` - Dashboard hosting options
- **Git Setup**: `main_docs/GIT_SETUP.md` - Repository setup instructions
- **Project Summary**: `main_docs/PROJECT_SUMMARY.md` - Project overview and structure

### Architecture Documentation

Detailed architecture and design documents are in `docs/`:

- **System Design**: `docs/architecture/SYSTEM_DESIGN.md` - Complete architecture exploration
- **Requirements**: `docs/REQUIREMENTS.md` - Functional and non-functional requirements
- **Deliverables**: `docs/DELIVERABLES.md` - Project deliverables by phase
- **Use Cases**: `docs/USE_CASES.md` - Detailed use cases and workflows
- **Security Audit**: `docs/SECURITY_AUDIT.md` - Security vulnerabilities and fixes
- **Security Summary**: `docs/SECURITY_SUMMARY.md` - Security implementation summary

### API Documentation

- **OpenAPI Spec**: Available at `/api/openapi.json` when API is running
- **Interactive Docs**: Available at `/api/docs` when DEBUG mode is enabled
- **API Routes**: See `cloud_backend/api/routes/` for endpoint implementations

## Development Guidelines

This project follows production-grade system engineering practices. See `.cursor/rules/ENERGY_GRID_SYSTEM_RULES.md` for:

- Code organization patterns
- Error handling standards
- Security practices
- Testing requirements
- Deployment procedures
- Performance targets

### Key Principles

- **Reliability First**: System continues operating with component failures
- **Observability**: Comprehensive metrics, logs, and tracing
- **Security**: Defense in depth with multiple security layers
- **Scalability**: Designed to handle 10K+ devices
- **Maintainability**: Clear code structure and comprehensive documentation

## Contributing

### Development Workflow

1. Create feature branch from `main`
2. Follow code standards in `.cursor/rules/ENERGY_GRID_SYSTEM_RULES.md`
3. Write tests (>80% coverage required)
4. Update documentation
5. Submit pull request with description

### Code Standards

- Type hints required for all functions
- Async/await patterns for I/O operations
- Structured logging with correlation IDs
- Input validation on all endpoints
- Error handling with generic user messages
- Server-side detailed error logging

### Testing

- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`
- Run tests: `pytest tests/ -v --cov`

## Operational Runbooks

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/metrics
```

### Common Operations

**View Logs**:
```bash
# Docker containers
docker-compose logs -f [service-name]

# Application logs
tail -f logs/app.log
```

**Database Operations**:
```bash
# Run migrations
cd cloud_backend && alembic upgrade head

# Create migration
alembic revision --autogenerate -m "description"
```

**Restart Services**:
```bash
# Restart infrastructure
docker-compose -f infrastructure/docker/docker-compose.dev.yml restart

# Restart API (if running locally)
# Stop with Ctrl+C, then restart with uvicorn command
```

## Monitoring and Alerting

### Metrics Endpoints

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (admin/admin)
- API Metrics: `http://localhost:8000/metrics`

### Key Metrics to Monitor

- API request rate and latency (P95, P99)
- Database query performance
- Message queue depth
- Device online/offline status
- Command execution success rate
- ML model prediction latency

### Alert Thresholds

**Critical**:
- API error rate >1%
- Database connection failures
- Message queue depth >10K
- Device offline rate >5%

**Warning**:
- API latency P95 >200ms
- Database query time >100ms
- Cache hit rate <80%

## Troubleshooting

See the "Debugging Tips" section above for common issues and solutions. For detailed troubleshooting:

- Check application logs with correlation IDs
- Review Prometheus metrics for anomalies
- Check RabbitMQ management UI for queue issues
- Verify database connectivity and query performance
- Review device daemon logs for execution issues

## License

[Specify license]

## Support

For issues, questions, or contributions:
- Open an issue in the repository
- Contact the development team
- Review documentation in `main_docs/` and `docs/`

---

**Last Updated**: February 6, 2026  
**Version**: 1.0.0  
**Status**: Production-Ready
