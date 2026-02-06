"""
Schedule Ingestion Service

Fetches battery schedules from external REST API, validates JSON structure,
and stores schedules in the database for distribution to devices.

This module handles the data ingestion pipeline stage, ensuring schedules
are fetched reliably, validated, and persisted for later distribution.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class ScheduleIngestionService:
    """
    Service for ingesting battery schedules from external APIs.
    
    Handles fetching, validation, and storage of schedules with
    retry logic, error handling, and logging for reproducibility.
    """
    
    def __init__(
        self,
        api_base_url: str,
        api_key: Optional[str] = None,
        db_path: str = "schedules.db",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize the schedule ingestion service.
        
        Args:
            api_base_url: Base URL of the external schedule API
            api_key: API key for authentication (optional)
            db_path: Path to SQLite database for local storage
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.api_key = api_key
        self.db_path = db_path
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.session = self._create_session()
        self._init_database()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        if self.api_key:
            session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        session.headers.update({"Content-Type": "application/json"})
        
        return session
    
    def _init_database(self):
        """Initialize SQLite database for schedule storage."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingested_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                schedule_data TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source_url TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_device_id 
            ON ingested_schedules(device_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_fetched_at 
            ON ingested_schedules(fetched_at)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized at {self.db_path}")
    
    def fetch_schedule(self, device_id: str, date: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch schedule for a specific device from external API.
        
        Args:
            device_id: Unique device identifier
            date: Date in YYYY-MM-DD format (defaults to tomorrow)
        
        Returns:
            Schedule dictionary or None if fetch failed
        """
        if date is None:
            from datetime import timedelta
            tomorrow = datetime.now() + timedelta(days=1)
            date = tomorrow.strftime("%Y-%m-%d")
        
        endpoint = f"/schedules/{device_id}"
        url = urljoin(self.api_base_url, endpoint)
        params = {"date": date}
        
        try:
            logger.info(f"Fetching schedule for device {device_id} on {date}")
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            schedule_data = response.json()
            
            if not self._validate_json_structure(schedule_data):
                raise ValueError("Invalid JSON structure received")
            
            self._store_schedule(device_id, schedule_data, url)
            
            logger.info(f"Successfully fetched schedule for device {device_id}")
            return schedule_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch schedule for {device_id}: {e}")
            self._store_schedule_error(device_id, str(e), url)
            return None
        
        except ValueError as e:
            logger.error(f"Invalid schedule data for {device_id}: {e}")
            self._store_schedule_error(device_id, str(e), url)
            return None
    
    def fetch_bulk_schedules(
        self, 
        device_ids: List[str], 
        date: Optional[str] = None
    ) -> Dict[str, Optional[Dict]]:
        """
        Fetch schedules for multiple devices.
        
        Args:
            device_ids: List of device identifiers
            date: Date in YYYY-MM-DD format
        
        Returns:
            Dictionary mapping device_id to schedule or None
        """
        results = {}
        
        for device_id in device_ids:
            schedule = self.fetch_schedule(device_id, date)
            results[device_id] = schedule
        
        success_count = sum(1 for s in results.values() if s is not None)
        logger.info(
            f"Bulk fetch completed: {success_count}/{len(device_ids)} successful"
        )
        
        return results
    
    def _validate_json_structure(self, data: Dict) -> bool:
        """
        Validate that JSON has expected structure.
        
        Args:
            data: JSON data to validate
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.warning("Schedule data is not a dictionary")
            return False
        
        if "device_id" not in data:
            logger.warning("Schedule missing device_id field")
            return False
        
        if "schedule" not in data:
            logger.warning("Schedule missing schedule array")
            return False
        
        if not isinstance(data["schedule"], list):
            logger.warning("Schedule field is not a list")
            return False
        
        for entry in data["schedule"]:
            if not isinstance(entry, dict):
                logger.warning("Schedule entry is not a dictionary")
                return False
            
            required_fields = ["start_time", "end_time", "mode", "rate_kw"]
            for field in required_fields:
                if field not in entry:
                    logger.warning(f"Schedule entry missing required field: {field}")
                    return False
        
        return True
    
    def _store_schedule(
        self, 
        device_id: str, 
        schedule_data: Dict, 
        source_url: str
    ):
        """Store fetched schedule in local database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO ingested_schedules 
                (device_id, schedule_data, source_url, status)
                VALUES (?, ?, ?, ?)
            """, (
                device_id,
                json.dumps(schedule_data),
                source_url,
                "success"
            ))
            
            conn.commit()
            logger.debug(f"Stored schedule for {device_id} in database")
            
        except sqlite3.Error as e:
            logger.error(f"Database error storing schedule for {device_id}: {e}")
            conn.rollback()
        
        finally:
            conn.close()
    
    def _store_schedule_error(
        self, 
        device_id: str, 
        error_message: str, 
        source_url: str
    ):
        """Store error information for failed schedule fetch."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO ingested_schedules 
                (device_id, schedule_data, source_url, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                device_id,
                json.dumps({}),
                source_url,
                "error",
                error_message
            ))
            
            conn.commit()
            logger.debug(f"Stored error for {device_id} in database")
            
        except sqlite3.Error as e:
            logger.error(f"Database error storing error for {device_id}: {e}")
            conn.rollback()
        
        finally:
            conn.close()
    
    def get_ingestion_history(
        self, 
        device_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve ingestion history from local database.
        
        Args:
            device_id: Filter by device ID (optional)
            limit: Maximum number of records to return
        
        Returns:
            List of ingestion records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        try:
            if device_id:
                cursor.execute("""
                    SELECT * FROM ingested_schedules
                    WHERE device_id = ?
                    ORDER BY fetched_at DESC
                    LIMIT ?
                """, (device_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM ingested_schedules
                    ORDER BY fetched_at DESC
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()


def main():
    """Example usage of the schedule ingestion service."""
    import os
    
    api_url = os.getenv("SCHEDULE_API_URL", "https://api.example.com")
    api_key = os.getenv("SCHEDULE_API_KEY")
    
    service = ScheduleIngestionService(
        api_base_url=api_url,
        api_key=api_key,
        db_path="schedules_ingestion.db"
    )
    
    device_id = "RPI-001"
    schedule = service.fetch_schedule(device_id)
    
    if schedule:
        print(f"Fetched schedule for {device_id}:")
        print(json.dumps(schedule, indent=2))
    else:
        print(f"Failed to fetch schedule for {device_id}")
    
    history = service.get_ingestion_history(device_id, limit=10)
    print(f"\nIngestion history: {len(history)} records")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
