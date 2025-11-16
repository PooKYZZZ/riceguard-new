# Enhanced rate limiting middleware with comprehensive security features

import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

# Setup logger for rate limiting
logger = logging.getLogger("riceguard.rate_limiter")

class RateLimiter:
    """Enhanced rate limiting with multiple strategies and security features."""

    def __init__(self):
        # In-memory storage for rate limiting (in production, use Redis)
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, float] = {}  # IP -> unblock time
        self.suspicious_ips: Dict[str, int] = {}   # IP -> violation count

        # Rate limiting configuration
        self.rates = {
            # (requests, window_seconds, description)
            'login': {'requests': 5, 'window': 300, 'description': 'Login attempts'},
            'register': {'requests': 3, 'window': 300, 'description': 'Registration attempts'},
            'upload': {'requests': 20, 'window': 300, 'description': 'File uploads'},
            'scan': {'requests': 30, 'window': 300, 'description': 'Scan requests'},
            'general': {'requests': 100, 'window': 300, 'description': 'General requests'},
            'api': {'requests': 60, 'window': 60, 'description': 'API calls per minute'},
        }

        # Security thresholds
        self.max_violations = 10  # Block after 10 violations
        self.block_duration = 3600  # Block for 1 hour
        self.suspicious_threshold = 5  # Flag as suspicious after 5 violations

        # Cleanup interval (run cleanup every 5 minutes)
        self.last_cleanup = time.time()
        self.cleanup_interval = 300

    def get_client_ip(self, request: Request) -> str:
        """SECURITY: Enhanced client IP detection with validation against spoofing."""
        # SECURITY: Validate IP format before using
        def is_valid_ip(ip_str: str) -> bool:
            import ipaddress
            try:
                # Validate IP address format and ensure it's not private/internal for rate limiting
                ip_obj = ipaddress.ip_address(ip_str)
                # SECURITY: Allow any IP for rate limiting but validate format
                return True
            except ValueError:
                return False

        # SECURITY: Only trust forward headers if coming from trusted proxies
        trusted_proxies = ['127.0.0.1', '::1']  # Add your reverse proxy IPs here

        # Get direct connection IP (most reliable)
        direct_ip = request.client.host if request.client else "unknown"

        # SECURITY: Check if request comes from trusted proxy
        if direct_ip in trusted_proxies:
            # Check for forwarded headers (only from trusted proxies)
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for and is_valid_ip(forwarded_for.split(",")[0].strip()):
                return forwarded_for.split(",")[0].strip()

            real_ip = request.headers.get("X-Real-IP")
            if real_ip and is_valid_ip(real_ip.strip()):
                return real_ip.strip()

        # SECURITY: Fall back to direct connection IP
        if is_valid_ip(direct_ip):
            return direct_ip

        # SECURITY: Invalid IP - use safe fallback
        return "invalid_ip"

    def get_rate_key(self, request: Request, endpoint_type: str) -> str:
        """Generate rate limiting key for request."""
        ip = self.get_client_ip(request)

        # For authenticated requests, use user ID instead of IP
        auth_header = request.headers.get("Authorization")
        if auth_header and endpoint_type != 'login':
            # Extract user identifier from token (simplified)
            try:
                # In a real implementation, you'd decode the JWT here
                # For now, we'll use a combination of IP and auth header
                user_hash = hash(auth_header.split()[-1][:16]) if len(auth_header.split()) > 1 else 0
                return f"user:{user_hash}"
            except:
                pass

        return f"ip:{ip}"

    def is_blocked(self, request: Request) -> Tuple[bool, Optional[str]]:
        """Check if client is currently blocked."""
        ip = self.get_client_ip(request)

        # Check IP block list
        if ip in self.blocked_ips:
            unblock_time = self.blocked_ips[ip]
            if time.time() < unblock_time:
                remaining = int(unblock_time - time.time())
                return True, f"IP blocked for {remaining} seconds due to abuse"
            else:
                # Unblock expired block
                del self.blocked_ips[ip]
                if ip in self.suspicious_ips:
                    del self.suspicious_ips[ip]
                logger.info(f"Rate limit block expired for IP: {ip}")

        return False, None

    def check_rate(self, request: Request, endpoint_type: str = 'general') -> bool:
        """Check if request exceeds rate limit."""
        # Check for blocks first
        is_blocked, block_reason = self.is_blocked(request)
        if is_blocked:
            logger.warning(f"Blocked request from {self.get_client_ip(request)}: {block_reason}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=block_reason
            )

        rate_config = self.rates.get(endpoint_type, self.rates['general'])
        key = self.get_rate_key(request, endpoint_type)

        # Cleanup old entries periodically
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cleanup()
            self.last_cleanup = current_time

        # Remove old requests outside the window
        window_start = current_time - rate_config['window']
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]

        # Check rate limit
        request_count = len(self.requests[key])
        if request_count >= rate_config['requests']:
            ip = self.get_client_ip(request)

            # Check if this is a repeated violation
            violations = self.suspicious_ips.get(ip, 0) + 1
            self.suspicious_ips[ip] = violations

            # Log the violation
            logger.warning(
                f"Rate limit exceeded - IP: {ip}, "
                f"Endpoint: {endpoint_type}, "
                f"Requests: {request_count}/{rate_config['requests']}, "
                f"Violations: {violations}"
            )

            # Apply escalating penalties
            if violations >= self.max_violations:
                # Block the IP for extended period
                self.blocked_ips[ip] = current_time + self.block_duration
                logger.warning(f"IP {ip} blocked due to repeated violations: {violations}")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Blocked for {self.block_duration//3600} hours due to abuse."
                )

            # Raise rate limit exception with retry info
            retry_after = rate_config['window']
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {rate_config['description']}. "
                      f"Maximum {rate_config['requests']} requests per {rate_config['window']} seconds. "
                      f"Please wait {retry_after} seconds before trying again."
            )

        # Record this request
        self.requests[key].append(current_time)
        return True

    def cleanup(self):
        """Clean up old entries to prevent memory leaks."""
        current_time = time.time()

        # Clean up old request entries
        for key in list(self.requests.keys()):
            # Remove empty request lists
            if not self.requests[key]:
                del self.requests[key]
                continue

            # Find oldest request time
            oldest_time = min(self.requests[key])
            if current_time - oldest_time > 3600:  # Remove entries older than 1 hour
                self.requests[key] = [
                    req_time for req_time in self.requests[key]
                    if current_time - req_time < 3600
                ]

        # Clean up expired blocks
        for ip in list(self.blocked_ips.keys()):
            if current_time >= self.blocked_ips[ip]:
                del self.blocked_ips[ip]
                if ip in self.suspicious_ips:
                    del self.suspicious_ips[ip]

        # Clean up old suspicious IP entries
        for ip in list(self.suspicious_ips.keys()):
            if ip not in self.blocked_ips:
                # Reduce violation count over time
                if self.suspicious_ips[ip] > 0:
                    self.suspicious_ips[ip] = max(0, self.suspicious_ips[ip] - 1)

        logger.debug(f"Rate limiter cleanup completed. "
                    f"Active IPs: {len(self.requests)}, "
                    f"Blocked IPs: {len(self.blocked_ips)}, "
                    f"Suspicious IPs: {len(self.suspicious_ips)}")

    def get_stats(self) -> dict:
        """Get rate limiting statistics for monitoring."""
        current_time = time.time()

        # Count active requests in last hour
        active_requests = 0
        for requests in self.requests.values():
            active_requests += len([
                req_time for req_time in requests
                if current_time - req_time < 3600
            ])

        return {
            'active_tracked_ips': len(self.requests),
            'blocked_ips': len(self.blocked_ips),
            'suspicious_ips': len(self.suspicious_ips),
            'active_requests_last_hour': active_requests,
            'last_cleanup': self.last_cleanup
        }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(self, app, limiter: RateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request: Request, call_next):
        # Determine endpoint type based on path and method
        path = request.url.path.lower()
        method = request.method.upper()

        endpoint_type = 'general'

        # Classify endpoint types for different rate limits
        if '/auth/login' in path and method == 'POST':
            endpoint_type = 'login'
        elif '/auth/register' in path and method == 'POST':
            endpoint_type = 'register'
        elif '/scans' in path and method == 'POST':
            endpoint_type = 'upload'
        elif '/scans' in path:
            endpoint_type = 'scan'
        elif '/api/v1' in path:
            endpoint_type = 'api'

        # Apply rate limiting
        try:
            self.limiter.check_rate(request, endpoint_type)
        except HTTPException as e:
            # Log rate limit hits
            logger.warning(
                f"Rate limit hit - {method} {path} - "
                f"IP: {self.limiter.get_client_ip(request)} - "
                f"Reason: {e.detail}"
            )
            # BUGFIX: Return proper JSONResponse instead of re-raising
            # This prevents the exception from being converted to 500 error
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "message": e.detail,
                    "status_code": e.status_code,
                    "path": path
                },
                headers={
                    "Retry-After": str(self.limiter.rates[endpoint_type]['window'])
                }
            )

        # Continue with the request
        response = await call_next(request)

        # Add rate limit headers
        stats = self.limiter.get_stats()
        response.headers["X-RateLimit-Limit"] = str(self.limiter.rates[endpoint_type]['requests'])
        response.headers["X-RateLimit-Window"] = str(self.limiter.rates[endpoint_type]['window'])
        response.headers["X-RateLimit-Remaining"] = str(max(0,
            self.limiter.rates[endpoint_type]['requests'] -
            len(self.limiter.requests.get(self.limiter.get_rate_key(request, endpoint_type), []))
        ))

        return response


# Global rate limiter instance
rate_limiter = RateLimiter()