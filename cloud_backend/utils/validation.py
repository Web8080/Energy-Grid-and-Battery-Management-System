"""
Schedule Validation Utilities

Validates battery schedule entries to ensure they meet all constraints
before distribution to devices. This prevents invalid schedules from
causing device errors or safety issues.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ScheduleValidationError(Exception):
    """Raised when schedule validation fails."""
    pass


class ScheduleValidator:
    """
    Validates battery schedule entries according to system constraints.
    
    Ensures schedules are safe, consistent, and executable by devices.
    """
    
    MIN_RATE_KW = 0.0
    MAX_RATE_KW = 1000.0
    VALID_MODES = {1, 2}  # 1 = discharge, 2 = charge
    MIN_INTERVAL_MINUTES = 1
    MAX_INTERVAL_HOURS = 24
    
    def __init__(
        self,
        min_rate_kw: float = MIN_RATE_KW,
        max_rate_kw: float = MAX_RATE_KW,
        valid_modes: set = None
    ):
        """
        Initialize validator with constraints.
        
        Args:
            min_rate_kw: Minimum allowed rate in kW
            max_rate_kw: Maximum allowed rate in kW
            valid_modes: Set of valid mode values (default: {1, 2})
        """
        self.min_rate_kw = min_rate_kw
        self.max_rate_kw = max_rate_kw
        self.valid_modes = valid_modes or self.VALID_MODES
    
    def validate_schedule_entry(
        self, 
        entry: Dict, 
        index: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a single schedule entry.
        
        Args:
            entry: Schedule entry dictionary
            index: Optional index for error reporting
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        prefix = f"Entry {index}: " if index is not None else ""
        
        if not isinstance(entry, dict):
            return False, f"{prefix}Entry must be a dictionary"
        
        required_fields = ["start_time", "end_time", "mode", "rate_kw"]
        for field in required_fields:
            if field not in entry:
                return False, f"{prefix}Missing required field: {field}"
        
        start_time = entry.get("start_time")
        end_time = entry.get("end_time")
        mode = entry.get("mode")
        rate_kw = entry.get("rate_kw")
        
        valid, error = self._validate_timestamps(start_time, end_time, prefix)
        if not valid:
            return False, error
        
        valid, error = self._validate_mode(mode, prefix)
        if not valid:
            return False, error
        
        valid, error = self._validate_rate(rate_kw, prefix)
        if not valid:
            return False, error
        
        return True, None
    
    def validate_schedule(
        self, 
        schedule: List[Dict],
        device_id: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate an entire schedule (list of entries).
        
        Args:
            schedule: List of schedule entry dictionaries
            device_id: Optional device ID for error reporting
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        prefix = f"Device {device_id}: " if device_id else ""
        
        if not isinstance(schedule, list):
            return False, [f"{prefix}Schedule must be a list"]
        
        if len(schedule) == 0:
            return False, [f"{prefix}Schedule cannot be empty"]
        
        parsed_times = []
        
        for i, entry in enumerate(schedule):
            valid, error = self.validate_schedule_entry(entry, index=i)
            if not valid:
                errors.append(error)
                continue
            
            try:
                start_time = self._parse_timestamp(entry["start_time"])
                end_time = self._parse_timestamp(entry["end_time"])
                parsed_times.append((start_time, end_time, i))
            except ValueError as e:
                errors.append(f"Entry {i}: Invalid timestamp format - {e}")
        
        if errors:
            return False, errors
        
        overlap_errors = self._check_overlaps(parsed_times, prefix)
        errors.extend(overlap_errors)
        
        sequential_errors = self._check_sequential(parsed_times, prefix)
        errors.extend(sequential_errors)
        
        return len(errors) == 0, errors
    
    def _validate_timestamps(
        self, 
        start_time: str, 
        end_time: str, 
        prefix: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """Validate timestamp format and ordering."""
        try:
            start_dt = self._parse_timestamp(start_time)
            end_dt = self._parse_timestamp(end_time)
        except ValueError as e:
            return False, f"{prefix}Invalid timestamp format: {e}"
        
        if start_dt >= end_dt:
            return False, f"{prefix}start_time must be before end_time"
        
        duration_minutes = (end_dt - start_dt).total_seconds() / 60
        if duration_minutes < self.MIN_INTERVAL_MINUTES:
            return False, (
                f"{prefix}Interval too short: "
                f"minimum {self.MIN_INTERVAL_MINUTES} minutes"
            )
        
        duration_hours = duration_minutes / 60
        if duration_hours > self.MAX_INTERVAL_HOURS:
            return False, (
                f"{prefix}Interval too long: "
                f"maximum {self.MAX_INTERVAL_HOURS} hours"
            )
        
        return True, None
    
    def _validate_mode(self, mode: int, prefix: str = "") -> Tuple[bool, Optional[str]]:
        """Validate mode value."""
        if not isinstance(mode, int):
            return False, f"{prefix}mode must be an integer"
        
        if mode not in self.valid_modes:
            valid_str = ", ".join(str(m) for m in sorted(self.valid_modes))
            return False, (
                f"{prefix}mode must be one of: {valid_str} "
                f"(got {mode})"
            )
        
        return True, None
    
    def _validate_rate(
        self, 
        rate_kw: float, 
        prefix: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """Validate rate_kw value."""
        try:
            rate = float(rate_kw)
        except (ValueError, TypeError):
            return False, f"{prefix}rate_kw must be a number"
        
        if rate < self.min_rate_kw:
            return False, (
                f"{prefix}rate_kw must be >= {self.min_rate_kw} "
                f"(got {rate})"
            )
        
        if rate > self.max_rate_kw:
            return False, (
                f"{prefix}rate_kw must be <= {self.max_rate_kw} "
                f"(got {rate})"
            )
        
        return True, None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse ISO8601 timestamp string.
        
        Supports formats:
        - 2025-12-25T00:00:00Z
        - 2025-12-25T00:00:00+00:00
        - 2025-12-25T00:00:00
        """
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S.%f"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse timestamp: {timestamp_str}")
    
    def _check_overlaps(
        self, 
        parsed_times: List[Tuple[datetime, datetime, int]], 
        prefix: str = ""
    ) -> List[str]:
        """Check for overlapping time intervals."""
        errors = []
        sorted_times = sorted(parsed_times, key=lambda x: x[0])
        
        for i in range(len(sorted_times) - 1):
            _, end1, idx1 = sorted_times[i]
            start2, _, idx2 = sorted_times[i + 1]
            
            if end1 > start2:
                errors.append(
                    f"{prefix}Entries {idx1} and {idx2} overlap: "
                    f"{end1} > {start2}"
                )
        
        return errors
    
    def _check_sequential(
        self, 
        parsed_times: List[Tuple[datetime, datetime, int]], 
        prefix: str = ""
    ) -> List[str]:
        """
        Check that intervals are sequential (end of one = start of next).
        
        Note: This is a warning, not an error, as gaps may be intentional.
        """
        warnings = []
        sorted_times = sorted(parsed_times, key=lambda x: x[0])
        
        for i in range(len(sorted_times) - 1):
            _, end1, idx1 = sorted_times[i]
            start2, _, idx2 = sorted_times[i + 1]
            
            if end1 != start2:
                gap_seconds = (start2 - end1).total_seconds()
                if gap_seconds > 0:
                    warnings.append(
                        f"{prefix}Gap between entries {idx1} and {idx2}: "
                        f"{gap_seconds} seconds"
                    )
                else:
                    warnings.append(
                        f"{prefix}Overlap between entries {idx1} and {idx2}: "
                        f"{(end1 - start2).total_seconds()} seconds"
                    )
        
        return warnings
    
    def clean_schedule(
        self, 
        schedule: List[Dict],
        device_id: Optional[str] = None
    ) -> Tuple[List[Dict], List[str]]:
        """
        Clean and validate schedule, returning valid entries and warnings.
        
        Args:
            schedule: List of schedule entries
            device_id: Optional device ID
        
        Returns:
            Tuple of (cleaned_schedule, warnings)
        """
        warnings = []
        cleaned = []
        
        for i, entry in enumerate(schedule):
            valid, error = self.validate_schedule_entry(entry, index=i)
            
            if valid:
                cleaned.append(entry)
            else:
                warnings.append(f"Entry {i} invalid: {error}")
                logger.warning(
                    f"Invalid schedule entry {i} for device {device_id}: {error}"
                )
        
        if cleaned:
            valid, errors = self.validate_schedule(cleaned, device_id)
            if not valid:
                warnings.extend(errors)
        
        return cleaned, warnings


def validate_schedule_entry(entry: Dict) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate a single schedule entry.
    
    Args:
        entry: Schedule entry dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = ScheduleValidator()
    return validator.validate_schedule_entry(entry)


def validate_schedule(
    schedule: List[Dict], 
    device_id: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate an entire schedule.
    
    Args:
        schedule: List of schedule entries
        device_id: Optional device ID
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validator = ScheduleValidator()
    return validator.validate_schedule(schedule, device_id)


def main():
    """Example usage of validation functions."""
    validator = ScheduleValidator()
    
    valid_schedule = [
        {
            "start_time": "2025-12-25T00:00:00Z",
            "end_time": "2025-12-25T00:30:00Z",
            "mode": 1,
            "rate_kw": 100
        },
        {
            "start_time": "2025-12-25T00:30:00Z",
            "end_time": "2025-12-25T01:00:00Z",
            "mode": 2,
            "rate_kw": 50
        }
    ]
    
    is_valid, errors = validator.validate_schedule(valid_schedule, "RPI-001")
    print(f"Valid schedule: {is_valid}")
    if errors:
        print(f"Errors: {errors}")
    
    invalid_schedule = [
        {
            "start_time": "2025-12-25T00:00:00Z",
            "end_time": "2025-12-25T00:30:00Z",
            "mode": 3,
            "rate_kw": 100
        }
    ]
    
    is_valid, errors = validator.validate_schedule(invalid_schedule, "RPI-002")
    print(f"\nInvalid schedule: {is_valid}")
    if errors:
        print(f"Errors: {errors}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    main()
