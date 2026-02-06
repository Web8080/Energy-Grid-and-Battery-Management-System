# Environment Setup Instructions

## .env File Location

The main `.env` file is located at the project root:
```
/Users/user/AI_Autonomous_Engergy_grid_and_smart_battery_management_systems/.env
```

## Required Environment Variables

### 🔴 CRITICAL - Must Update Before Starting

1. **DATABASE_URL** - PostgreSQL connection string
   ```bash
   DATABASE_URL=postgresql://user:YOUR_POSTGRES_PASSWORD@localhost:5432/energy_grid
   ```
   **Action**: Replace `YOUR_POSTGRES_PASSWORD` with your actual PostgreSQL password

2. **SECRET_KEY** - JWT token signing key
   ```bash
   SECRET_KEY=befYVjnnfX4l_20hokyNrYYNEq3PZz0hubL-_REwwV0
   ```
   **Action**: A secure key has been generated. You can keep it or generate a new one:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

### 🟡 RECOMMENDED - Update for Your Setup

3. **CORS_ORIGINS** - Allowed frontend origins
   ```bash
   CORS_ORIGINS=http://localhost:3000,http://localhost:8000
   ```
   **Action**: Add your frontend URLs (comma-separated, no spaces)

### 🟢 OPTIONAL - Configure as Needed

4. **API_KEY** - For external API integrations
   ```bash
   API_KEY=your_api_key_here
   ```

5. **MQTT_USERNAME** / **MQTT_PASSWORD** - If MQTT requires auth
   ```bash
   MQTT_USERNAME=your_mqtt_username
   MQTT_PASSWORD=your_mqtt_password
   ```

## Quick Setup Steps

1. **Edit .env file**:
   ```bash
   nano .env
   # or
   code .env
   ```

2. **Update DATABASE_URL** with your PostgreSQL password

3. **Verify SECRET_KEY** is set (already generated)

4. **Save the file**

## Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | ✅ Yes | - | JWT signing key (32+ chars) |
| `REDIS_URL` | ✅ Yes | `redis://localhost:6379/0` | Redis connection |
| `RABBITMQ_URL` | ✅ Yes | `amqp://guest:guest@localhost:5672/` | RabbitMQ connection |
| `CORS_ORIGINS` | 🟡 Recommended | `http://localhost:3000,...` | Allowed origins |
| `API_KEY` | 🟢 Optional | - | External API key |
| `DEBUG` | 🟢 Optional | `false` | Debug mode (never `true` in production) |
| `LOG_LEVEL` | 🟢 Optional | `INFO` | Logging level |

## Security Notes

- ✅ `.env` file is in `.gitignore` - will NOT be committed to Git
- ✅ Never share your `.env` file
- ✅ Use different secrets for development and production
- ✅ Rotate `SECRET_KEY` periodically in production

## Next Steps

After updating `.env`:
1. Start infrastructure: `docker-compose -f infrastructure/docker/docker-compose.dev.yml up -d`
2. Run migrations: `cd cloud_backend && alembic upgrade head`
3. Start API: `uvicorn cloud_backend.api.main:app --reload`
