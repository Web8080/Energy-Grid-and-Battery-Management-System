"""
Battery Execution Daemon

Raspberry Pi daemon that polls for schedules, validates them, executes
charge/discharge commands at scheduled intervals, and sends acknowledgements.

This daemon runs continuously on each Raspberry Pi device, managing
local schedule execution and communication with the cloud backend.
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import paho.mqtt.client as mqtt

from device_fleet.utils.schedule_executor import ScheduleExecutor
from device_fleet.utils.validation import validate_schedule_locally

logger = logging.getLogger(__name__)


class BatteryDaemon:
    """
    Main daemon class for battery schedule execution.
    
    Handles schedule retrieval, local storage, command execution,
    and acknowledgement publishing.
    """
    
    def __init__(
        self,
        device_id: str,
        api_base_url: str,
        mqtt_broker: str = "localhost",
        mqtt_port: int = 1883,
        poll_interval: int = 300,
        db_path: str = "/var/lib/battery-daemon/schedules.db"
    ):
        """
        Initialize the battery daemon.
        
        Args:
            device_id: Unique device identifier
            api_base_url: Cloud backend API base URL
            mqtt_broker: MQTT broker hostname
            mqtt_port: MQTT broker port
            poll_interval: Schedule polling interval in seconds
            db_path: Path to local SQLite database
        """
        self.device_id = device_id
        self.api_base_url = api_base_url.rstrip('/')
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.poll_interval = poll_interval
        self.db_path = db_path
        
        self.current_schedule: Optional[List[Dict]] = None
        self.executor = ScheduleExecutor(device_id)
        self.mqtt_client = None
        self.running = False
        
        self._init_database()
        self._init_mqtt()
    
    def _init_database(self):
        """Initialize local SQLite database for schedule storage."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                schedule_data TEXT NOT NULL,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                schedule_entry_index INTEGER,
                execution_time TIMESTAMP,
                status TEXT,
                actual_rate_kw REAL,
                error_message TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def _init_mqtt(self):
        """Initialize MQTT client for schedule reception."""
        self.mqtt_client = mqtt.Client(client_id=self.device_id)
        
        self.mqtt_client.on_connect = self._on_mqtt_connect
        self.mqtt_client.on_message = self._on_mqtt_message
        self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """Handle MQTT connection."""
        if rc == 0:
            logger.info("Connected to MQTT broker")
            topic = f"devices/{self.device_id}/schedule/response"
            client.subscribe(topic)
            logger.info(f"Subscribed to topic: {topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode())
            logger.info(f"Received schedule via MQTT: {payload.get('device_id')}")
            
            if payload.get("device_id") == self.device_id:
                schedule = payload.get("schedule", [])
                self._process_schedule(schedule)
        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}", exc_info=True)
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        logger.warning(f"Disconnected from MQTT broker: {rc}")
    
    async def start(self):
        """Start the daemon."""
        logger.info(f"Starting battery daemon for device {self.device_id}")
        
        self.running = True
        
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
        
        await self._load_cached_schedule()
        
        tasks = [
            asyncio.create_task(self._poll_schedules()),
            asyncio.create_task(self._execute_schedule_loop()),
            asyncio.create_task(self._health_check_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the daemon."""
        logger.info("Stopping battery daemon")
        self.running = False
        
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
    
    async def _poll_schedules(self):
        """Periodically poll cloud API for schedules."""
        while self.running:
            try:
                await self._fetch_schedule()
            except Exception as e:
                logger.error(f"Error polling schedule: {e}", exc_info=True)
            
            await asyncio.sleep(self.poll_interval)
    
    async def _fetch_schedule(self):
        """Fetch schedule from cloud API."""
        url = f"{self.api_base_url}/schedules/{self.device_id}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.json()
                        schedule = data.get("schedule", [])
                        
                        if schedule:
                            self._process_schedule(schedule)
                    elif response.status == 404:
                        logger.warning(f"No schedule found for device {self.device_id}")
                    else:
                        logger.error(f"Failed to fetch schedule: {response.status}")
        
        except asyncio.TimeoutError:
            logger.warning("Schedule fetch timeout, using cached schedule")
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}", exc_info=True)
    
    def _process_schedule(self, schedule: List[Dict]):
        """
        Process and store received schedule.
        
        Args:
            schedule: List of schedule entries
        """
        is_valid, errors = validate_schedule_locally(schedule)
        
        if not is_valid:
            logger.error(f"Invalid schedule received: {errors}")
            return
        
        self.current_schedule = schedule
        self._store_schedule(schedule)
        
        logger.info(f"Schedule processed: {len(schedule)} entries")
    
    def _store_schedule(self, schedule: List[Dict]):
        """Store schedule in local database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE schedules SET status = 'inactive'
                WHERE device_id = ? AND status = 'active'
            """, (self.device_id,))
            
            cursor.execute("""
                INSERT INTO schedules (device_id, schedule_data, status)
                VALUES (?, ?, ?)
            """, (
                self.device_id,
                json.dumps(schedule),
                "active"
            ))
            
            conn.commit()
            logger.debug("Schedule stored in local database")
        
        except sqlite3.Error as e:
            logger.error(f"Database error storing schedule: {e}")
            conn.rollback()
        
        finally:
            conn.close()
    
    async def _load_cached_schedule(self):
        """Load cached schedule from local database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT schedule_data FROM schedules
                WHERE device_id = ? AND status = 'active'
                ORDER BY received_at DESC
                LIMIT 1
            """, (self.device_id,))
            
            row = cursor.fetchone()
            if row:
                schedule = json.loads(row["schedule_data"])
                self.current_schedule = schedule
                logger.info(f"Loaded cached schedule: {len(schedule)} entries")
        
        finally:
            conn.close()
    
    async def _execute_schedule_loop(self):
        """Main loop for executing scheduled commands."""
        while self.running:
            if self.current_schedule:
                await self._check_and_execute()
            
            await asyncio.sleep(30)
    
    async def _check_and_execute(self):
        """Check current time against schedule and execute if needed."""
        if not self.current_schedule:
            return
        
        now = datetime.utcnow()
        
        for i, entry in enumerate(self.current_schedule):
            start_time = datetime.fromisoformat(
                entry["start_time"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                entry["end_time"].replace("Z", "+00:00")
            )
            
            if start_time <= now < end_time:
                await self._execute_entry(i, entry)
                break
    
    async def _execute_entry(self, index: int, entry: Dict):
        """Execute a schedule entry."""
        mode = entry["mode"]
        rate_kw = entry["rate_kw"]
        
        logger.info(
            f"Executing schedule entry {index}: mode={mode}, rate={rate_kw}kW"
        )
        
        try:
            success, actual_rate = await self.executor.execute_command(
                mode=mode,
                rate_kw=rate_kw
            )
            
            if success:
                await self._send_acknowledgement(
                    index=index,
                    status="success",
                    actual_rate_kw=actual_rate
                )
            else:
                await self._send_acknowledgement(
                    index=index,
                    status="failed",
                    error_message="Command execution failed"
                )
        
        except Exception as e:
            logger.error(f"Error executing entry {index}: {e}", exc_info=True)
            await self._send_acknowledgement(
                index=index,
                status="failed",
                error_message=str(e)
            )
    
    async def _send_acknowledgement(
        self,
        index: int,
        status: str,
        actual_rate_kw: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Send execution acknowledgement to cloud backend."""
        ack = {
            "device_id": self.device_id,
            "schedule_entry_index": index,
            "execution_time": datetime.utcnow().isoformat() + "Z",
            "status": status,
            "actual_rate_kw": actual_rate_kw,
            "error_message": error_message
        }
        
        try:
            url = f"{self.api_base_url}/devices/{self.device_id}/acknowledgements"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=ack,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 202:
                        logger.debug(f"Acknowledgement sent for entry {index}")
                    else:
                        logger.warning(
                            f"Failed to send acknowledgement: {response.status}"
                        )
        
        except Exception as e:
            logger.error(f"Error sending acknowledgement: {e}", exc_info=True)
    
    async def _health_check_loop(self):
        """Periodic health check and status reporting."""
        while self.running:
            await asyncio.sleep(300)
            
            logger.debug(
                f"Health check: device={self.device_id}, "
                f"schedule_active={self.current_schedule is not None}"
            )


def main():
    """Main entry point for the daemon."""
    import os
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("/var/log/battery-daemon.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    device_id = os.getenv("DEVICE_ID", "RPI-001")
    api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    mqtt_broker = os.getenv("MQTT_BROKER", "localhost")
    
    daemon = BatteryDaemon(
        device_id=device_id,
        api_base_url=api_url,
        mqtt_broker=mqtt_broker
    )
    
    try:
        asyncio.run(daemon.start())
    except KeyboardInterrupt:
        logger.info("Daemon stopped by user")


if __name__ == "__main__":
    main()
