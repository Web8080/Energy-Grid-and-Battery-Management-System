"""
Local Schedule Validation

Validation utilities for device-side schedule validation.
Simplified version of cloud validation for local use.
"""

from typing import List, Optional, Tuple


def validate_schedule_locally(
    schedule: List[dict]
) -> Tuple[bool, List[str]]:
    """
    Validate schedule locally on device.
    
    Args:
        schedule: List of schedule entries
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(schedule, list):
        return False, ["Schedule must be a list"]
    
    if len(schedule) == 0:
        return False, ["Schedule cannot be empty"]
    
    for i, entry in enumerate(schedule):
        if not isinstance(entry, dict):
            errors.append(f"Entry {i}: must be a dictionary")
            continue
        
        required_fields = ["start_time", "end_time", "mode", "rate_kw"]
        for field in required_fields:
            if field not in entry:
                errors.append(f"Entry {i}: missing field {field}")
        
        if "mode" in entry:
            mode = entry["mode"]
            if mode not in [1, 2]:
                errors.append(f"Entry {i}: mode must be 1 or 2 (got {mode})")
        
        if "rate_kw" in entry:
            rate = entry["rate_kw"]
            if not isinstance(rate, (int, float)) or rate < 0 or rate > 1000:
                errors.append(
                    f"Entry {i}: rate_kw must be between 0 and 1000 (got {rate})"
                )
    
    return len(errors) == 0, errors
