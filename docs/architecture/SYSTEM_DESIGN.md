# System Design: Autonomous Energy Grid & Smart Battery Management

## Problem Statement

Build a production-grade AI-enabled platform that optimizes energy distribution across a regional smart grid, integrates thousands of Raspberry Pi-based smart batteries that can charge or discharge at specific intervals, supports participation in energy trading markets, and ensures reliability, scalability, security, observability, traceability, and actionable analytics.

## Architectural Exploration

### Architecture 1: Monolithic Cloud with Direct Device Communication

#### Components and Responsibilities

- **Monolithic API Service**: Single application handling schedule distribution, device management, ML inference, and analytics
- **PostgreSQL Database**: Stores schedules, device metadata, execution logs, and analytics data
- **Device Fleet**: Raspberry Pi devices with direct HTTP polling to cloud API
- **Monitoring Service**: Integrated metrics collection and alerting

#### Data Flow

**Read Path:**
- Devices poll `/get-schedule/{device_id}` endpoint every 5 minutes
- API queries PostgreSQL for device schedule
- Returns JSON schedule payload

**Write Path:**
- Schedule ingestion writes directly to PostgreSQL
- Device acknowledgements write to PostgreSQL execution_logs table
- ML predictions write optimized schedules to PostgreSQL

#### Scaling Characteristics

- **Horizontal Scaling**: Limited by database connection pool (typically 100-200 connections per instance)
- **Vertical Scaling**: Single instance can handle ~500-1000 concurrent device connections
- **Bottlenecks**: Database becomes bottleneck at ~10,000 devices; API instance memory/CPU limits
- **Independent Scaling**: Cannot scale API independently from database load

#### Failure Modes

- **API Failure**: All devices lose schedule access; no graceful degradation
- **Database Failure**: Complete system outage; no read replicas for failover
- **Network Partition**: Devices cannot reach cloud; no local caching or fallback schedules
- **Partial Failure**: One device failure affects others if database locks occur

#### Operational Burden

- **Infrastructure**: Single application server, database server, basic monitoring
- **Monitoring**: Application logs, database metrics, basic health checks
- **Deployment**: Single Docker container deployment; simple but risky (all-or-nothing)
- **Debugging**: Centralized logs but difficult to trace individual device flows
- **Maintenance**: Low complexity but high blast radius for changes
- **Team Expertise**: Standard web development skills sufficient

#### Tradeoffs

- **Gains**: Simple architecture, easy to understand, low initial complexity, fast development
- **Losses**: Poor scalability beyond 1000 devices, single point of failure, difficult to optimize individual components
- **Harder later**: Adding message queues, microservices, or advanced features requires major refactoring
- **Impossible later**: Cannot scale beyond database connection limits without complete redesign

#### Liability Points

- Becomes a liability at ~5,000 devices due to connection pool exhaustion
- Cannot handle traffic spikes during schedule updates
- Database becomes bottleneck preventing horizontal scaling
- Single deployment unit creates high-risk releases

---

### Architecture 2: Event-Driven Microservices with Message Queue

#### Components and Responsibilities

- **Schedule API Service**: REST API for schedule ingestion and device queries
- **Device Command Service**: Processes device acknowledgements and status updates
- **ML Optimization Service**: Runs predictions and generates optimized schedules
- **Message Queue (RabbitMQ/AWS SQS)**: Decouples services and devices
- **PostgreSQL**: Primary database for schedules and metadata
- **Time-Series Database (InfluxDB)**: Stores execution logs and metrics
- **Device Fleet**: Raspberry Pi devices communicate via MQTT or HTTP with message queue
- **Observability Stack**: Prometheus, Grafana, ELK for metrics, logs, traces

#### Data Flow

**Read Path:**
- Devices publish MQTT messages to `devices/{device_id}/schedule/request` topic
- Schedule API Service consumes requests, queries PostgreSQL, publishes to `devices/{device_id}/schedule/response`
- Devices subscribe to response topic and receive schedules

**Write Path:**
- Schedule ingestion API writes to PostgreSQL and publishes to `schedules/updated` topic
- ML Service consumes schedule updates, generates predictions, writes optimized schedules
- Device acknowledgements published to `devices/{device_id}/execution/ack` topic
- Command Service consumes acks, validates, writes to InfluxDB and PostgreSQL

#### Scaling Characteristics

- **Horizontal Scaling**: Each service scales independently; message queue handles 100K+ messages/sec
- **Vertical Scaling**: Individual services can scale vertically as needed
- **Bottlenecks**: Message queue throughput (mitigated by partitioning), database write capacity
- **Independent Scaling**: Schedule API, ML Service, Command Service scale independently based on load

#### Failure Modes

- **Service Failure**: Other services continue operating; message queue buffers messages
- **Message Queue Failure**: System degrades but can fall back to direct HTTP polling
- **Database Failure**: Read replicas available; write operations queued in message queue
- **Partial Failure**: Individual device failures isolated; no cascading failures

#### Operational Burden

- **Infrastructure**: Multiple services, message queue cluster, primary DB, time-series DB, observability stack
- **Monitoring**: Distributed tracing, service-level metrics, message queue depth, database replication lag
- **Deployment**: Kubernetes or container orchestration required; service mesh for inter-service communication
- **Debugging**: Distributed tracing essential; correlation IDs across services
- **Maintenance**: Higher complexity but lower blast radius per service
- **Team Expertise**: Requires distributed systems knowledge, message queue operations, service mesh

#### Tradeoffs

- **Gains**: Excellent scalability (10K+ devices), fault isolation, independent deployment, technology flexibility per service
- **Losses**: Higher operational complexity, more infrastructure to manage, distributed debugging challenges, eventual consistency complexities
- **Harder later**: Adding new services requires message queue integration; service mesh configuration complexity
- **Impossible later**: Cannot simplify to monolithic without losing scale benefits

#### Liability Points

- Becomes a liability for small deployments (<100 devices) due to operational overhead
- Requires skilled DevOps team for production operations
- Message queue becomes critical dependency; failure impacts entire system
- Distributed tracing and debugging require specialized tooling and expertise

---

### Architecture 3: Hybrid Modular Monolith with Message Queue Integration

#### Components and Responsibilities

- **Modular Monolith API**: Single deployable unit with internal modules (Schedule, Device, ML, Analytics)
- **Message Queue (RabbitMQ)**: Handles device communication and async processing
- **PostgreSQL**: Primary database with read replicas
- **Redis Cache**: Caches frequently accessed schedules and device status
- **Time-Series Database (Prometheus/InfluxDB)**: Metrics and execution logs
- **Device Fleet**: Raspberry Pi devices use MQTT for schedules, HTTP for acks
- **Observability**: Prometheus + Grafana for metrics, structured logging

#### Data Flow

**Read Path:**
- Devices publish MQTT requests; API module handles via message queue consumer
- Schedule module queries PostgreSQL (with Redis cache layer)
- Response published via MQTT to device topic

**Write Path:**
- Schedule ingestion writes to PostgreSQL, invalidates Redis cache, publishes to queue
- ML module consumes schedule updates, generates predictions asynchronously
- Device acks processed by Device module, written to time-series DB and PostgreSQL

#### Scaling Characteristics

- **Horizontal Scaling**: Multiple monolith instances behind load balancer; shared message queue and database
- **Vertical Scaling**: Single instance handles 2000-3000 devices with proper resource allocation
- **Bottlenecks**: Database connections (mitigated by connection pooling and read replicas), message queue throughput
- **Independent Scaling**: Cannot scale ML module independently; all modules scale together

#### Failure Modes

- **Instance Failure**: Other instances continue; load balancer routes traffic away
- **Message Queue Failure**: Can fall back to direct HTTP polling mode
- **Database Failure**: Read replicas available; writes queued in message queue
- **Partial Failure**: Module failures affect entire instance but not other instances

#### Operational Burden

- **Infrastructure**: Multiple API instances, message queue, database cluster, cache, time-series DB
- **Monitoring**: Application metrics, message queue depth, cache hit rates, database performance
- **Deployment**: Single container deployment but multiple instances; simpler than microservices
- **Debugging**: Centralized logs per instance; easier than fully distributed but requires correlation IDs
- **Maintenance**: Moderate complexity; module changes require full deployment but testing is simpler
- **Team Expertise**: Standard backend development with message queue experience

#### Tradeoffs

- **Gains**: Good scalability (5K-10K devices), simpler than microservices, message queue decoupling, easier debugging than full microservices
- **Losses**: Cannot scale ML independently, larger deployment units, shared resource constraints
- **Harder later**: Splitting into microservices requires significant refactoring; adding new modules increases complexity
- **Impossible later**: Cannot achieve microservice-level independent scaling without architectural change

#### Liability Points

- Becomes a liability at very large scale (>15K devices) where independent ML scaling is critical
- Module coupling can create deployment bottlenecks
- Shared resources (memory, CPU) limit optimization of individual modules

---

## Comparison Summary

| Aspect | Monolithic Cloud | Event-Driven Microservices | Hybrid Modular Monolith |
|--------|------------------|----------------------------|-------------------------|
| **Complexity** | Low | High | Medium |
| **Scalability** | Low (1K devices) | Very High (10K+ devices) | High (5K-10K devices) |
| **Operational Overhead** | Low | High | Medium |
| **Development Speed** | Fast | Slower (coordination) | Medium |
| **Failure Resilience** | Low (single point) | High (isolated failures) | Medium (instance-level) |
| **Technology Flexibility** | Low | High | Medium |
| **Debugging Difficulty** | Low | High | Medium |
| **Initial Cost** | Low | High | Medium |
| **Team Expertise Required** | Standard | Advanced | Intermediate |

## Recommendation

**Chosen Approach:** Hybrid Modular Monolith with Message Queue Integration (Architecture 3)

**Justification:**

1. **Scale Requirements**: Target scale of 10 → 10,000 devices fits well within this architecture's capabilities (5K-10K comfortable range)

2. **Operational Balance**: Provides message queue decoupling and scalability benefits without the full complexity of microservices, reducing operational burden for initial deployment

3. **Development Velocity**: Faster initial development than microservices while maintaining ability to scale horizontally

4. **Fault Tolerance**: Message queue provides buffering and decoupling; multiple instances provide redundancy; read replicas handle database failures

5. **Cost Efficiency**: Lower infrastructure costs than full microservices while achieving necessary scale

6. **Team Capabilities**: Requires intermediate distributed systems knowledge, which is more accessible than full microservices expertise

**Acknowledged Tradeoffs:**

- ML module cannot scale independently; if ML inference becomes bottleneck, will need to extract to separate service
- Module coupling means changes to one module require full deployment; mitigated by careful module boundaries
- Shared resources limit per-module optimization; acceptable for target scale

**Migration Triggers:**

- Device count exceeds 15,000 requiring independent ML scaling
- ML inference latency becomes critical requiring dedicated ML infrastructure
- Need for service-specific technology choices (e.g., Python for ML, Go for API) requiring microservices split
- Team grows large enough to support microservices operational model

---

## Detailed Architecture

### Core Components

#### 1. Cloud Backend (Modular Monolith)

**Schedule Module:**
- REST API endpoints for schedule ingestion (`POST /schedules`)
- Schedule retrieval (`GET /schedules/{device_id}`)
- Schedule validation and conflict detection
- Database operations for schedule CRUD

**Device Module:**
- Device registration and metadata management
- Device status tracking (online/offline, health)
- Acknowledgement processing from devices
- Device command history

**ML Module:**
- Schedule optimization predictions
- Model serving endpoint (`POST /ml/optimize`)
- Feature engineering for predictions
- Model version management

**Analytics Module:**
- Aggregation queries for dashboards
- Historical data analysis
- Report generation
- Data export functionality

#### 2. Message Queue (RabbitMQ)

**Topics/Queues:**
- `schedule.requests`: Device schedule requests
- `schedule.responses.{device_id}`: Schedule responses per device
- `device.acks`: Device execution acknowledgements
- `schedule.updates`: Schedule change notifications
- `ml.predictions`: ML optimization results

**Configuration:**
- Durable queues for reliability
- Message TTL for stale message cleanup
- Dead letter queues for failed processing
- Clustering for high availability

#### 3. Database Layer

**PostgreSQL (Primary):**
- `devices`: Device metadata and configuration
- `schedules`: Schedule definitions and assignments
- `execution_logs`: Device command execution records
- `ml_models`: Model metadata and versions
- `analytics_aggregates`: Pre-computed analytics data

**Read Replicas:**
- 2-3 read replicas for query scaling
- Automatic failover via connection pool
- Read-only queries routed to replicas

**Redis Cache:**
- Schedule cache (TTL: 5 minutes)
- Device status cache (TTL: 1 minute)
- Rate limiting counters
- Session state (if needed)

**Time-Series Database (InfluxDB/Prometheus):**
- Device execution metrics (latency, success/failure)
- System performance metrics
- ML model performance metrics
- Energy usage and trading metrics

#### 4. Device Fleet (Raspberry Pi)

**Execution Daemon:**
- MQTT client for schedule reception
- Schedule validation and conflict detection
- Command execution at scheduled intervals
- Acknowledgement publishing
- Health monitoring and reporting

**Local Storage:**
- SQLite database for schedule persistence
- Execution logs for debugging
- Fallback schedule support

#### 5. Observability Stack

**Metrics (Prometheus):**
- API request rates and latencies
- Device online/offline counts
- Command execution success/failure rates
- ML prediction latencies
- Database query performance
- Message queue depth and throughput

**Logging (Structured JSON):**
- Application logs with correlation IDs
- Device execution logs
- ML training and inference logs
- Error logs with stack traces

**Tracing (OpenTelemetry/Jaeger):**
- End-to-end request tracing
- Cross-service trace correlation
- Database query tracing
- Message queue operation tracing

**Alerting:**
- PagerDuty/Slack integration
- Alert rules for critical metrics
- Escalation policies

#### 6. Analytics & Dashboard

**Backend API:**
- REST endpoints for dashboard data
- Real-time WebSocket for live updates
- Aggregation queries optimized for dashboard needs
- Export functionality (CSV, JSON)

**Frontend (React/Grafana):**
- Real-time device monitoring dashboard
- Command execution success/failure visualization
- ML model performance metrics
- Energy usage and trading analytics
- Alert management interface

**Data Pipeline:**
- ETL jobs for analytics aggregation
- Scheduled reports generation
- Data retention policies

### Data Flow Diagrams

#### Schedule Distribution Flow

```
External Schedule Source
    |
    v
Schedule Ingestion API (POST /schedules)
    |
    v
PostgreSQL (schedules table)
    |
    v
Redis Cache Invalidation
    |
    v
RabbitMQ (schedule.updates topic)
    |
    v
ML Module (consumes updates)
    |
    v
ML Optimization Service
    |
    v
PostgreSQL (optimized schedules)
    |
    v
RabbitMQ (schedule.responses.{device_id})
    |
    v
Device (MQTT subscription)
    |
    v
Local SQLite Storage
    |
    v
Command Execution
```

#### Device Acknowledgement Flow

```
Device Execution
    |
    v
Acknowledgement Generation
    |
    v
RabbitMQ (device.acks topic)
    |
    v
Device Module (consumes acks)
    |
    v
Validation & Processing
    |
    v
PostgreSQL (execution_logs)
    |
    v
InfluxDB (metrics)
    |
    v
Analytics Aggregation
    |
    v
Dashboard Updates
```

### Security Architecture

#### Authentication & Authorization

- **Device Authentication**: Certificate-based mutual TLS (mTLS) for device-to-cloud communication
- **API Authentication**: JWT tokens for external API access
- **Internal Service Auth**: Service-to-service authentication via API keys or mTLS

#### Data Encryption

- **In Transit**: TLS 1.3 for all external communication
- **At Rest**: Database encryption at rest, encrypted backups
- **Secrets Management**: HashiCorp Vault or AWS Secrets Manager for API keys, DB credentials

#### Network Security

- **VPC/Network Isolation**: Private subnets for backend services
- **Firewall Rules**: Restrictive ingress/egress rules
- **DDoS Protection**: Cloud provider DDoS mitigation

#### Device Security

- **Secure Boot**: Verified boot process on Raspberry Pi
- **OTA Updates**: Signed firmware updates
- **Local Security**: Encrypted local storage, secure credential storage

### Scalability Design

#### Horizontal Scaling Strategy

1. **API Instances**: Auto-scale based on CPU (70% threshold) and request queue depth
2. **Message Queue**: RabbitMQ clustering with mirrored queues
3. **Database**: Read replicas auto-scaled based on read query latency
4. **Cache**: Redis cluster mode for distributed caching

#### Vertical Scaling Strategy

1. **Database**: Vertical scaling for write-heavy workloads
2. **ML Module**: GPU instances for model inference if needed
3. **Message Queue**: Larger instances for higher throughput

#### Partitioning Strategy

1. **Device Partitioning**: Partition devices by geographic region or device group
2. **Schedule Partitioning**: Partition schedules by time windows
3. **Message Queue Partitioning**: Partition topics by device_id hash

### Failure Modes and Mitigation

#### Database Failure

- **Mitigation**: Read replicas for read operations, message queue buffers writes
- **Recovery**: Automatic failover to replica, manual promotion if needed
- **Data Loss Risk**: Low (replication lag < 1 second)

#### Message Queue Failure

- **Mitigation**: RabbitMQ clustering with automatic failover
- **Fallback**: Direct HTTP polling mode for devices
- **Recovery**: Queue replication and message persistence

#### API Instance Failure

- **Mitigation**: Multiple instances behind load balancer, health checks
- **Recovery**: Automatic instance replacement, traffic routing
- **Data Loss Risk**: None (stateless API)

#### Device Network Partition

- **Mitigation**: Local schedule caching, fallback schedules
- **Recovery**: Automatic reconnection with exponential backoff
- **Data Loss Risk**: Low (local persistence)

#### ML Service Failure

- **Mitigation**: Fallback to rule-based schedules, circuit breaker pattern
- **Recovery**: Automatic service restart, model rollback
- **Data Loss Risk**: None (schedules still served from database)

### Observability Strategy

#### Metrics

- **Business Metrics**: Device uptime, command success rate, energy traded
- **Technical Metrics**: API latency, database query time, message queue depth
- **ML Metrics**: Prediction latency, model accuracy, feature drift

#### Logging

- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: DEBUG, INFO, WARN, ERROR with appropriate sampling
- **Log Aggregation**: Centralized log storage with search capabilities

#### Tracing

- **Distributed Tracing**: OpenTelemetry instrumentation
- **Trace Sampling**: 100% for errors, 1% for successful requests
- **Trace Retention**: 7 days for debugging

#### Alerting

- **Critical Alerts**: System outages, high error rates, data loss
- **Warning Alerts**: Performance degradation, capacity thresholds
- **Info Alerts**: Deployments, configuration changes

### Deployment Architecture

#### CI/CD Pipeline

1. **Source Control**: GitHub with branch protection
2. **Testing**: Unit tests, integration tests, E2E tests
3. **Build**: Docker image creation and registry push
4. **Deployment**: Kubernetes rolling updates with health checks
5. **Rollback**: Automatic rollback on health check failures

#### Environment Strategy

- **Development**: Single instance, local databases
- **Staging**: Scaled-down production replica
- **Production**: Full scale with redundancy

#### Configuration Management

- **Environment Variables**: Non-sensitive configuration
- **Secrets Management**: Vault for sensitive data
- **Feature Flags**: Gradual feature rollout

### Cost Optimization

#### Infrastructure Costs

- **Compute**: Auto-scaling to minimize idle resources
- **Database**: Reserved instances for predictable workloads
- **Storage**: Tiered storage with lifecycle policies
- **Network**: CDN for static assets, data transfer optimization

#### Operational Costs

- **Monitoring**: Log sampling to reduce storage costs
- **Backups**: Incremental backups with retention policies
- **Development**: Spot instances for non-production environments

### Compliance and Governance

#### Data Retention

- **Execution Logs**: 90 days in hot storage, 1 year in cold storage
- **Schedules**: 2 years retention
- **Metrics**: 30 days high resolution, 1 year aggregated

#### Audit Logging

- **API Access**: All API calls logged with user/device ID
- **Configuration Changes**: All config changes audited
- **Deployments**: Deployment history tracked

#### Regulatory Compliance

- **Energy Regulations**: Compliance with grid operator requirements
- **Data Privacy**: GDPR compliance for device data
- **Security Standards**: SOC 2, ISO 27001 alignment

---

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

- Basic API with schedule CRUD
- PostgreSQL database schema
- Simple device polling (HTTP)
- Basic logging and metrics
- Single instance deployment

### Phase 2: Message Queue Integration (Weeks 5-8)

- RabbitMQ setup and integration
- MQTT support for devices
- Async processing for acks
- Basic observability (Prometheus)

### Phase 3: ML Integration (Weeks 9-12)

- ML model training pipeline
- Model serving integration
- Feature store implementation
- Model monitoring

### Phase 4: Analytics & Dashboard (Weeks 13-16)

- Analytics backend API
- Dashboard frontend
- Real-time updates
- Reporting functionality

### Phase 5: Production Hardening (Weeks 17-20)

- Security hardening
- Performance optimization
- Failure mode testing
- Documentation completion

---

## Success Criteria

### Functional Requirements

- ✅ Schedule distribution to 10,000 devices with <5 second latency
- ✅ Command execution success rate >99.5%
- ✅ ML optimization reduces energy costs by >10%
- ✅ Dashboard updates within 30 seconds of events

### Non-Functional Requirements

- ✅ API availability >99.9% (excluding planned maintenance)
- ✅ P95 API latency <200ms
- ✅ Database query latency P95 <50ms
- ✅ Message queue throughput >10K messages/second
- ✅ Zero data loss for critical operations

### Operational Requirements

- ✅ Deployment time <30 minutes
- ✅ Rollback capability <5 minutes
- ✅ Incident detection <2 minutes
- ✅ Full observability for debugging

---

## Known Limitations and Future Work

### Current Limitations

1. ML module scales with API (cannot scale independently)
2. Single region deployment (no multi-region support)
3. Limited device firmware update capabilities
4. Basic analytics (no advanced ML-based anomaly detection)

### Future Enhancements

1. Extract ML service to independent microservice for independent scaling
2. Multi-region deployment for global device fleet
3. Advanced OTA update system with rollback
4. ML-based anomaly detection and predictive maintenance
5. Advanced energy trading optimization with real-time market integration
