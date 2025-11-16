"""
Security Monitoring and Logging Utility

This module provides comprehensive security monitoring, logging,
and threat detection for the RiceGuard application.
"""

import logging
import time
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from functools import wraps
from fastapi import Request, HTTPException
import ipaddress

# Configure security logger
security_logger = logging.getLogger("riceguard.security")

@dataclass
class SecurityEvent:
    """Structure for security events"""
    event_type: str
    timestamp: datetime
    ip_address: str
    user_agent: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    severity: str = "medium"  # low, medium, high, critical

class SecurityMonitor:
    """Security monitoring and threat detection system"""

    def __init__(self):
        self.failed_logins = defaultdict(list)  # IP -> list of timestamps
        self.suspicious_activities = defaultdict(int)  # IP -> count
        self.blocked_ips = set()
        self.rate_limits = defaultdict(lambda: deque())  # IP -> deque of timestamps
        self.events_log = deque(maxlen=1000)  # Keep last 1000 events

        # Load configuration from environment
        self.max_login_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
        self.lockout_duration = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")) * 60
        self.rate_limit_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.rate_limit_window = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.enable_logging = os.getenv("ENABLE_SECURITY_LOGGING", "true").lower() == "true"

        security_logger.info("Security monitoring initialized")

    def log_security_event(self, event: SecurityEvent) -> None:
        """Log a security event"""
        if not self.enable_logging:
            return

        # Add to events log
        self.events_log.append(event)

        # Log with structured format
        log_data = {
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "ip_address": event.ip_address,
            "user_agent": event.user_agent,
            "user_id": event.user_id,
            "severity": event.severity,
            "details": event.details
        }

        # Log based on severity
        if event.severity == "critical":
            security_logger.critical(f"SECURITY EVENT: {json.dumps(log_data)}")
        elif event.severity == "high":
            security_logger.error(f"SECURITY EVENT: {json.dumps(log_data)}")
        elif event.severity == "medium":
            security_logger.warning(f"SECURITY EVENT: {json.dumps(log_data)}")
        else:
            security_logger.info(f"SECURITY EVENT: {json.dumps(log_data)}")

    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is currently blocked"""
        return ip_address in self.blocked_ips

    def is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP has exceeded rate limits"""
        now = time.time()
        request_times = self.rate_limits[ip_address]

        # Remove old requests outside the window
        while request_times and request_times[0] < now - self.rate_limit_window:
            request_times.popleft()

        # Check if exceeded limit
        return len(request_times) >= self.rate_limit_requests

    def record_request(self, ip_address: str) -> None:
        """Record a request for rate limiting"""
        self.rate_limits[ip_address].append(time.time())

    def record_failed_login(self, ip_address: str, user_agent: str, email: Optional[str] = None) -> bool:
        """Record a failed login attempt and check for lockout"""
        now = datetime.now(timezone.utc)
        self.failed_logins[ip_address].append(now)

        # Clean old attempts
        cutoff_time = now.timestamp() - self.lockout_duration
        self.failed_logins[ip_address] = [
            attempt for attempt in self.failed_logins[ip_address]
            if attempt.timestamp() > cutoff_time
        ]

        # Check if should be blocked
        if len(self.failed_logins[ip_address]) >= self.max_login_attempts:
            self.blocked_ips.add(ip_address)

            event = SecurityEvent(
                event_type="login_brute_force_detected",
                timestamp=now,
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    "failed_attempts": len(self.failed_logins[ip_address]),
                    "email": email,
                    "action": "ip_blocked"
                },
                severity="high"
            )
            self.log_security_event(event)
            return True

        # Log the failed attempt
        event = SecurityEvent(
            event_type="failed_login",
            timestamp=now,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "failed_attempts": len(self.failed_logins[ip_address]),
                "email": email
            },
            severity="medium"
        )
        self.log_security_event(event)
        return False

    def record_successful_login(self, ip_address: str, user_id: str, user_agent: str) -> None:
        """Record a successful login"""
        # Clear failed attempts for this IP
        if ip_address in self.failed_logins:
            del self.failed_logins[ip_address]

        # Remove from blocked IPs if present
        self.blocked_ips.discard(ip_address)

        event = SecurityEvent(
            event_type="successful_login",
            timestamp=datetime.now(timezone.utc),
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            severity="low"
        )
        self.log_security_event(event)

    def detect_suspicious_patterns(self, request: Request) -> List[str]:
        """Detect suspicious request patterns"""
        suspicious_indicators = []

        # Check user agent
        user_agent = request.headers.get("user-agent", "")
        if not user_agent or len(user_agent) < 10:
            suspicious_indicators.append("missing_or_short_user_agent")

        # Check for suspicious headers
        suspicious_headers = ["x-forwarded-for", "x-real-ip"]
        for header in suspicious_headers:
            if header in request.headers:
                suspicious_indicators.append(f"suspicious_header_{header}")

        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB
            suspicious_indicators.append("large_request_body")

        return suspicious_indicators

    def validate_ip_address(self, ip_address: str) -> bool:
        """Validate IP address format"""
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client IP
        if hasattr(request, 'client') and request.client:
            return request.client.host

        return "unknown"

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security monitoring summary"""
        now = datetime.now(timezone.utc)
        last_hour = now.timestamp() - 3600

        recent_events = [
            event for event in self.events_log
            if event.timestamp.timestamp() > last_hour
        ]

        return {
            "timestamp": now.isoformat(),
            "blocked_ips_count": len(self.blocked_ips),
            "failed_login_attempts": sum(len(attempts) for attempts in self.failed_logins.values()),
            "recent_events_count": len(recent_events),
            "events_by_severity": {
                severity: sum(1 for event in recent_events if event.severity == severity)
                for severity in ["low", "medium", "high", "critical"]
            },
            "top_suspicious_ips": [
                ip for ip, count in self.suspicious_activities.most_common(10)
            ]
        }

# Global security monitor instance
security_monitor = SecurityMonitor()

def security_monitoring_decorator(event_type: str, severity: str = "medium"):
    """Decorator to add security monitoring to functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                # Log successful execution
                if request:
                    event = SecurityEvent(
                        event_type=f"{event_type}_success",
                        timestamp=datetime.now(timezone.utc),
                        ip_address=security_monitor.get_client_ip(request),
                        user_agent=request.headers.get("user-agent", ""),
                        details={
                            "execution_time": time.time() - start_time,
                            "function": func.__name__
                        },
                        severity=severity
                    )
                    security_monitor.log_security_event(event)

                return result

            except Exception as e:
                # Log failed execution
                if request:
                    event = SecurityEvent(
                        event_type=f"{event_type}_failure",
                        timestamp=datetime.now(timezone.utc),
                        ip_address=security_monitor.get_client_ip(request),
                        user_agent=request.headers.get("user-agent", ""),
                        details={
                            "execution_time": time.time() - start_time,
                            "function": func.__name__,
                            "error": str(e)
                        },
                        severity="high" if isinstance(e, HTTPException) and e.status_code >= 500 else "medium"
                    )
                    security_monitor.log_security_event(event)

                raise

        return wrapper
    return decorator

# Export functions for use in other modules
def log_security_event(event_type: str, request: Request, details: Dict = None, severity: str = "medium"):
    """Convenience function to log security events"""
    event = SecurityEvent(
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        ip_address=security_monitor.get_client_ip(request),
        user_agent=request.headers.get("user-agent", ""),
        details=details,
        severity=severity
    )
    security_monitor.log_security_event(event)

def is_ip_safe(ip_address: str) -> bool:
    """Check if IP is safe (not blocked or rate limited)"""
    return not (security_monitor.is_ip_blocked(ip_address) or security_monitor.is_rate_limited(ip_address))