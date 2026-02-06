"""
Input Sanitization Utilities

Sanitizes and validates user inputs to prevent injection attacks,
XSS, and other security vulnerabilities.
"""

import html
import logging
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize a string input.
    
    Args:
        value: Input string
        max_length: Optional maximum length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)
    
    sanitized = value.strip()
    
    sanitized = html.escape(sanitized)
    
    dangerous_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"data:text/html",
        r"vbscript:",
    ]
    
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_email(email: str) -> str:
    """
    Sanitize and validate email address.
    
    Args:
        email: Email address
    
    Returns:
        Sanitized email
    
    Raises:
        ValueError: If email is invalid
    """
    email = email.strip().lower()
    
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    if not re.match(email_pattern, email):
        raise ValueError("Invalid email format")
    
    return email


def sanitize_url(url: str, allowed_schemes: List[str] = None) -> str:
    """
    Sanitize and validate URL.
    
    Args:
        url: URL string
        allowed_schemes: List of allowed URL schemes (default: http, https)
    
    Returns:
        Sanitized URL
    
    Raises:
        ValueError: If URL is invalid or uses disallowed scheme
    """
    if allowed_schemes is None:
        allowed_schemes = ["http", "https"]
    
    try:
        parsed = urlparse(url)
        
        if parsed.scheme not in allowed_schemes:
            raise ValueError(f"URL scheme not allowed: {parsed.scheme}")
        
        return url
    
    except Exception as e:
        raise ValueError(f"Invalid URL: {e}")


def sanitize_device_id(device_id: str) -> str:
    """
    Sanitize device ID to prevent injection.
    
    Args:
        device_id: Device identifier
    
    Returns:
        Sanitized device ID
    """
    if not isinstance(device_id, str):
        device_id = str(device_id)
    
    device_id = device_id.strip()
    
    if not re.match(r"^[A-Z0-9_-]+$", device_id):
        raise ValueError("Invalid device ID format")
    
    if len(device_id) > 100:
        raise ValueError("Device ID too long")
    
    return device_id


def sanitize_json_input(data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
    """
    Recursively sanitize JSON input data.
    
    Args:
        data: JSON-serializable data
    
    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        return {k: sanitize_json_input(v) for k, v in data.items()}
    
    elif isinstance(data, list):
        return [sanitize_json_input(item) for item in data]
    
    elif isinstance(data, str):
        return sanitize_string(data)
    
    else:
        return data


def validate_schedule_entry_input(entry: Dict) -> Dict:
    """
    Validate and sanitize schedule entry input.
    
    Args:
        entry: Schedule entry dictionary
    
    Returns:
        Sanitized schedule entry
    
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(entry, dict):
        raise ValueError("Schedule entry must be a dictionary")
    
    required_fields = ["start_time", "end_time", "mode", "rate_kw"]
    
    for field in required_fields:
        if field not in entry:
            raise ValueError(f"Missing required field: {field}")
    
    sanitized = {
        "start_time": sanitize_string(entry["start_time"], max_length=50),
        "end_time": sanitize_string(entry["end_time"], max_length=50),
        "mode": int(entry["mode"]) if isinstance(entry["mode"], (int, str)) else None,
        "rate_kw": float(entry["rate_kw"]) if isinstance(entry["rate_kw"], (int, float, str)) else None
    }
    
    if sanitized["mode"] not in [1, 2]:
        raise ValueError("Mode must be 1 or 2")
    
    if not (0 <= sanitized["rate_kw"] <= 1000):
        raise ValueError("rate_kw must be between 0 and 1000")
    
    return sanitized
