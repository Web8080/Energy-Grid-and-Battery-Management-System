# Use Cases: Energy Grid & Smart Battery Management System

## Overview

This document outlines the primary use cases for the Energy Grid & Smart Battery Management System, designed from the perspectives of Project Manager, ML Engineer, Full Stack Engineer, Systems Engineer/Architect, and Security Specialist.

---

## User Roles

### 1. System Administrator (Admin)
- Full system access
- User management
- System configuration
- Audit log access

### 2. Grid Operator (Operator)
- Schedule management
- Device monitoring
- Analytics access
- Alert management

### 3. Energy Trader (Operator)
- Schedule optimization
- Trading performance analysis
- Cost/revenue tracking
- Market integration

### 4. Viewer (Viewer)
- Read-only access
- Dashboard viewing
- Report access
- Historical data viewing

### 5. Device (Device)
- Schedule retrieval
- Command execution
- Status reporting
- Acknowledgement sending

---

## Use Case 1: User Authentication and Authorization

**Actor**: All users  
**Precondition**: User has valid account  
**Postcondition**: User authenticated, session established

### Flow:
1. User navigates to login page
2. User enters username and password
3. System validates credentials
4. System generates JWT access token (7-day expiration) and refresh token (30-day expiration)
5. User receives tokens
6. User uses access token for API requests
7. When access token expires, user uses refresh token to get new tokens

### Security Considerations:
- Rate limiting on login endpoint (5 attempts per 15 minutes)
- Password hashing with bcrypt
- JWT tokens with expiration
- Refresh token rotation
- Failed login attempt logging

### Admin Use Case:
- Admin can create new users
- Admin can assign roles
- Admin can deactivate users
- Admin can view all users

---

## Use Case 2: Schedule Management

**Actor**: Grid Operator, Energy Trader  
**Precondition**: User authenticated, operator role  
**Postcondition**: Schedule created/updated for device

### Flow:
1. Operator logs into system
2. Operator navigates to schedule management
3. Operator selects device or device group
4. Operator creates/edits schedule with:
   - Start/end times (ISO8601)
   - Mode (1=discharge, 2=charge)
   - Rate (kW)
5. System validates schedule:
   - No overlapping intervals
   - Valid mode values
   - Rate within device limits
   - Sequential timestamps
6. System stores schedule in database
7. System distributes schedule to device via MQTT
8. Device receives and stores schedule locally
9. System logs schedule creation

### ML Integration:
- Operator can request ML optimization
- ML service generates optimized schedule
- Operator reviews and approves optimized schedule
- Optimized schedule distributed to device

### Security:
- Authentication required
- Operator role required
- Input sanitization
- Audit logging

---

## Use Case 3: Device Monitoring and Control

**Actor**: Grid Operator, System Administrator  
**Precondition**: User authenticated, operator/admin role  
**Postcondition**: Device status visible, commands executed

### Flow:
1. Operator navigates to device dashboard
2. System displays:
   - Device online/offline status
   - Current schedule execution
   - Battery charge level
   - Recent command execution history
   - Error logs
3. Operator filters by:
   - Device ID
   - Status (online/offline)
   - Location
   - Last seen time
4. Operator selects device for details
5. System shows:
   - Device metadata
   - Current schedule
   - Execution history
   - Health metrics
6. Operator can:
   - View execution logs
   - Trigger manual command
   - Update device status
   - View alerts

### Real-time Updates:
- WebSocket connection for live updates
- Device status updates every 5 minutes
- Command execution updates immediately
- Alert notifications in real-time

---

## Use Case 4: ML-Powered Schedule Optimization

**Actor**: Energy Trader, Grid Operator  
**Precondition**: User authenticated, ML service available  
**Postcondition**: Optimized schedule generated

### Flow:
1. Trader selects device(s) for optimization
2. Trader specifies optimization objective:
   - Minimize cost
   - Maximize revenue
   - Grid stabilization
3. Trader selects time period (e.g., next 24 hours)
4. System collects:
   - Historical energy prices
   - Historical demand patterns
   - Device usage history
   - Weather data (if available)
5. ML service:
   - Computes features
   - Runs prediction model
   - Generates optimized schedule
6. System displays:
   - Optimized schedule
   - Predicted savings/revenue
   - Model confidence
   - Comparison with current schedule
7. Trader reviews optimization
8. Trader approves or modifies schedule
9. Approved schedule distributed to device

### ML Engineer Perspective:
- Model version tracking
- Feature drift monitoring
- Prediction accuracy tracking
- A/B testing between models
- Model retraining triggers

---

## Use Case 5: Analytics and Reporting

**Actor**: All authenticated users (role-based access)  
**Precondition**: User authenticated  
**Postcondition**: Analytics data displayed/reported

### Flow:
1. User navigates to analytics dashboard
2. User selects:
   - Time period (day/week/month)
   - Device(s) or device group
   - Metrics to display
3. System queries:
   - Execution logs
   - Energy usage data
   - Cost/revenue data
   - Device health metrics
4. System aggregates data
5. System displays:
   - Charts and graphs
   - Summary statistics
   - Trends and patterns
   - Anomalies
6. User can:
   - Export data (CSV/JSON/PDF)
   - Schedule reports
   - Set up alerts
   - Share dashboards

### Admin Analytics:
- User activity logs
- System performance metrics
- Security event logs
- Cost analysis

---

## Use Case 6: Alert Management

**Actor**: Grid Operator, System Administrator  
**Precondition**: User authenticated, operator/admin role  
**Postcondition**: Alerts configured and monitored

### Flow:
1. Operator navigates to alert management
2. Operator views active alerts:
   - Device offline alerts
   - Command execution failures
   - High latency alerts
   - ML model drift alerts
3. Operator filters alerts by:
   - Severity (critical/warning/info)
   - Device
   - Alert type
   - Time range
4. Operator acknowledges alerts
5. Operator configures alert rules:
   - Threshold values
   - Notification channels
   - Escalation policies
6. System sends notifications:
   - Email
   - Slack
   - PagerDuty
   - SMS (for critical)

---

## Use Case 7: Admin User Management

**Actor**: System Administrator  
**Precondition**: Admin authenticated  
**Postcondition**: User created/updated/deactivated

### Flow:
1. Admin navigates to user management
2. Admin views user list with filters:
   - Role
   - Status (active/inactive)
   - Last login
3. Admin creates new user:
   - Email address
   - Username
   - Password (temporary, must change)
   - Role assignment
4. System sends welcome email with credentials
5. Admin updates user:
   - Role changes
   - Status changes
   - Password reset
6. Admin deactivates user:
   - Immediate access revocation
   - Data preservation
   - Audit log entry

### Security:
- Admin-only access
- Audit logging for all changes
- Password complexity requirements
- Account lockout after failed attempts

---

## Use Case 8: Device Registration and Onboarding

**Actor**: System Administrator, Device  
**Precondition**: Admin authenticated or device certificate valid  
**Postcondition**: Device registered and active

### Flow:
1. Admin registers new device:
   - Device ID (unique)
   - Location
   - Battery capacity
   - Max charge/discharge rates
2. System creates device record
3. System generates device certificate (mTLS)
4. System provisions device:
   - Certificate installation
   - Initial configuration
   - Default schedule (if any)
5. Device connects to system:
   - mTLS handshake
   - Device authentication
   - Schedule request
6. System validates device certificate
7. System distributes schedule
8. Device begins operation

---

## Use Case 9: Schedule Execution and Acknowledgement

**Actor**: Device  
**Precondition**: Device authenticated, schedule received  
**Postcondition**: Command executed, acknowledgement sent

### Flow:
1. Device daemon checks current time
2. Device matches time to schedule entry
3. Device validates schedule entry
4. Device executes command:
   - Mode 1: Discharge at specified rate
   - Mode 2: Charge at specified rate
5. Device records execution:
   - Success/failure
   - Actual rate achieved
   - Timestamp
   - Error message (if failed)
6. Device sends acknowledgement to cloud
7. Cloud processes acknowledgement:
   - Validates device
   - Stores execution log
   - Updates metrics
   - Triggers alerts if failed
8. Cloud updates dashboard in real-time

---

## Use Case 10: System Health Monitoring

**Actor**: System Administrator  
**Precondition**: Admin authenticated  
**Postcondition**: System health status visible

### Flow:
1. Admin navigates to system health dashboard
2. System displays:
   - API health status
   - Database connection status
   - Message queue status
   - Redis cache status
   - ML service status
3. System shows metrics:
   - Request rates
   - Error rates
   - Latency percentiles
   - Resource utilization
4. Admin views:
   - Recent errors
   - Performance trends
   - Capacity planning data
5. Admin can:
   - Restart services
   - Scale resources
   - View logs
   - Export metrics

---

## Use Case 11: Compliance and Audit Reporting

**Actor**: System Administrator, Compliance Officer  
**Precondition**: Admin authenticated  
**Postcondition**: Audit report generated

### Flow:
1. Admin navigates to audit logs
2. Admin filters by:
   - User
   - Action type
   - Time range
   - Resource
3. System displays audit trail:
   - User actions
   - Data modifications
   - Authentication events
   - System changes
4. Admin exports audit report:
   - CSV format
   - PDF format
   - JSON format
5. Report includes:
   - Timestamp
   - User ID
   - Action
   - Resource
   - Result
   - IP address

---

## Use Case 12: Disaster Recovery and Failover

**Actor**: System (Automatic), System Administrator  
**Precondition**: System monitoring active  
**Postcondition**: System recovered or failed over

### Flow:
1. System detects component failure:
   - Database unavailable
   - API instance down
   - Message queue failure
2. System triggers alerts
3. Automatic failover:
   - Database: Switch to read replica
   - API: Load balancer routes away
   - Message queue: Cluster failover
4. System continues operating (degraded mode)
5. Admin receives notification
6. Admin investigates and resolves
7. System recovers automatically
8. Buffered operations processed

---

## Integration Use Cases

### External Schedule Source Integration
- Webhook receives schedule updates
- Webhook signature verified
- Schedule validated and stored
- Distributed to devices

### Energy Market Integration
- Market prices fetched periodically
- Prices stored in database
- ML models use prices for optimization
- Schedules adjusted based on market conditions

### SCADA System Integration
- Grid status data received
- Battery schedules adjusted for grid stability
- Real-time coordination with grid operator

---

## Non-Functional Requirements

### Performance
- API response time <200ms (P95)
- Schedule distribution <5 seconds
- Dashboard updates <30 seconds
- Supports 10,000+ concurrent devices

### Security
- All endpoints authenticated
- Role-based access control
- Input sanitization
- Rate limiting
- Audit logging

### Reliability
- 99.9% uptime
- Automatic failover
- Data durability
- Zero data loss for critical operations

### Scalability
- Horizontal scaling
- Auto-scaling based on load
- Database read replicas
- Caching layer

---

**Document Version**: 1.0  
**Last Updated**: February 6, 2026  
**Next Review**: March 6, 2026
