import os
import logging
from typing import List

# NEW: load .env from the backend folder
from pathlib import Path                 # NEW
from dotenv import load_dotenv           # NEW
load_dotenv(dotenv_path=Path(__file__).with_name(".env"))  # NEW

MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME: str = os.getenv("DB_NAME", "riceguard_db")
# SECURITY: JWT secret must be at least 32 characters for security
JWT_SECRET: str = os.getenv("JWT_SECRET", "")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET environment variable must be at least 32 characters long for security")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
TOKEN_EXPIRE_HOURS: int = int(os.getenv("TOKEN_EXPIRE_HOURS", "6"))
UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "8"))

_default_origins = [
    "http://localhost:8081",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:19000",
    "http://127.0.0.1:19006",
    "http://localhost:19000",
    "http://localhost:19006",
]

def is_development() -> bool:
    """Check if we're in development mode."""
    env = os.getenv("ENVIRONMENT", "development").lower()
    return env in ["development", "dev", "local"]

def get_dynamic_origins() -> List[str]:
    """Get dynamic allowed origins with enhanced security validation and performance optimization."""
    origins = []

    # Security: validate and sanitize origins
    def is_valid_origin(origin: str) -> bool:
        """Enhanced validation that an origin is safe and properly formatted."""
        if not origin or len(origin) > 200:  # Reasonable length limit
            return False

        origin_lower = origin.lower()

        # SECURITY: Block dangerous and overly permissive patterns
        dangerous_patterns = [
            '*',                         # Wildcard origins are dangerous
            'file://',                   # Local file access
            'ftp://',                    # FTP protocol
            'javascript:',               # JavaScript protocol
            'data:',                     # Data URLs
            'chrome-extension://',       # Chrome extensions
            'moz-extension://',          # Firefox extensions
            'chrome-devtools://',        # Dev tools
            'chrome-error://',           # Chrome error pages
            'chrome-native://',          # Chrome native protocol
            'about:',                    # About pages
            'resource://',               # Resource protocol
            'ws://',                     # WebSocket (potentially unsafe)
            'wss://',                    # Secure WebSocket (potentially unsafe)
        ]
        if any(pattern in origin_lower for pattern in dangerous_patterns):
            logger.debug(f"Blocked dangerous origin pattern: {origin}")
            return False

        # Must start with http:// or https://
        if not origin.startswith(("http://", "https://")):
            logger.debug(f"Origin must be HTTP/HTTPS: {origin}")
            return False

        # Enhanced URL format validation
        try:
            from urllib.parse import urlparse
            import re

            parsed = urlparse(origin)
            if not parsed.netloc:
                logger.debug(f"Invalid network location: {origin}")
                return False

            # SECURITY: Enhanced hostname validation
            hostname = parsed.hostname
            if not hostname:
                logger.debug(f"No hostname found: {origin}")
                return False

            # Block invalid hostnames
            if hostname.startswith('.') or hostname.endswith('.'):
                logger.debug(f"Invalid hostname format: {hostname}")
                return False

            # SECURITY: Block localhost in production mode
            if not is_development():
                blocked_hosts = {
                    'localhost', '127.0.0.1', '0.0.0.0',
                    '::1', '[::1]', 'localhost.localdomain'
                }
                if hostname in blocked_hosts or hostname.startswith('127.') or hostname.startswith('192.168.') or hostname.startswith('10.'):
                    logger.debug(f"Blocked localhost/private IP in production: {hostname}")
                    return False

            # SECURITY: Development mode - only allow localhost and private IPs
            if is_development():
                # Allow localhost variations
                if hostname in {'localhost', '127.0.0.1', '0.0.0.0', '::1', '[::1]'}:
                    return True

                # Allow private IP ranges in development (with validation)
                import ipaddress
                try:
                    ip_obj = ipaddress.ip_address(hostname)
                    if ip_obj.is_private or ip_obj.is_loopback:
                        # Additional validation for port numbers
                        if parsed.port:
                            # Only allow common development ports
                            allowed_ports = {3000, 5173, 8080, 8081, 19000, 19006, 8000, 5000}
                            if parsed.port not in allowed_ports:
                                logger.debug(f"Port not in allowed development ports: {parsed.port}")
                                return False
                        return True
                    else:
                        logger.debug(f"Non-private IP in development: {hostname}")
                        return False
                except ValueError:
                    # Not an IP address, continue with hostname validation
                    pass

                # Allow specific development hostnames
                allowed_dev_hosts = {
                    'localhost.localdomain',
                    'local',
                    'dev.local',
                    'localhost.local',
                }
                if hostname in allowed_dev_hosts:
                    return True

                # Block non-local hostnames in development
                if '.' in hostname and not hostname.endswith('.local'):
                    logger.debug(f"External hostname blocked in development: {hostname}")
                    return False

            # SECURITY: Production mode - strict hostname validation
            if not is_development():
                # Only allow specific production domains
                production_origins = os.getenv("PRODUCTION_ORIGINS", "").split(",")
                production_origins = [origin.strip() for origin in production_origins if origin.strip()]

                if production_origins:
                    # Check if origin matches any allowed production origin
                    if origin not in production_origins:
                        logger.debug(f"Origin not in production allowlist: {origin}")
                        return False
                else:
                    # No production origins configured - block all non-localhost
                    logger.debug(f"No production origins configured, blocking: {origin}")
                    return False

            # Additional security: validate port ranges
            if parsed.port:
                # Block privileged ports and suspicious ports
                blocked_ports = {1, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 25, 37, 42, 43, 53, 77, 79, 87, 95, 101, 102, 103, 104, 109, 110, 111, 113, 115, 117, 119, 123, 135, 137, 139, 143, 161, 163, 179, 389, 427, 465, 512, 513, 514, 515, 526, 530, 531, 532, 540, 548, 554, 587, 631, 646, 873, 990, 993, 995}
                if parsed.port in blocked_ports:
                    logger.debug(f"Blocked port: {parsed.port}")
                    return False

                # Block ports commonly used for attacks
                if parsed.port > 65535:
                    logger.debug(f"Port out of valid range: {parsed.port}")
                    return False

            return True

        except Exception as e:
            logger.debug(f"Origin validation error: {origin} - {e}")
            return False

    # Start with configured origins (highest priority)
    configured_origins = os.getenv("ALLOWED_ORIGINS", "").split(",") if os.getenv("ALLOWED_ORIGINS") else []
    logger = logging.getLogger("riceguard.settings")

    # Process configured origins with security validation
    for origin in configured_origins:
        origin = origin.strip()
        if not is_valid_origin(origin):
            logger.warning(f"Skipping invalid configured origin: {origin}")
            continue

        # Handle dynamic IP patterns for mobile development (development only)
        if origin.startswith("http://LOCAL_IP:") and is_development():
            import socket
            try:
                # Get local IP addresses more reliably
                hostname = socket.gethostname()
                local_ips = set()

                # Add hostname resolution
                try:
                    local_ip = socket.gethostbyname(hostname)
                    if (not local_ip.startswith("127.") and
                        not local_ip.startswith("169.254.") and
                        not local_ip.startswith("::")):
                        local_ips.add(local_ip)
                except:
                    pass

                # Add common local IP ranges for development
                dev_ips = ["192.168.1.100", "192.168.0.100", "10.0.0.100"]
                local_ips.update(dev_ips)

                for ip in local_ips:
                    dynamic_origin = origin.replace("LOCAL_IP", ip)
                    if is_valid_origin(dynamic_origin):
                        origins.append(dynamic_origin)
                        logger.debug(f"Added dynamic origin: {dynamic_origin}")

            except Exception as e:
                logger.warning(f"Failed to process dynamic IP pattern: {e}")
        else:
            origins.append(origin)

    # Add development origins if in development mode
    if is_development():
        # Core development origins
        dev_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8081",
            "http://127.0.0.1:8081",
            "http://localhost:19000",
            "http://127.0.0.1:19000",
            "http://localhost:19006",
            "http://127.0.0.1:19006",
        ]

        # Enhanced mobile development origins with improved IP detection
        try:
            import socket
            import ipaddress

            detected_ips = set()

            # Method 1: Get hostname-based IPs (more reliable)
            try:
                hostname = socket.gethostname()
                hostname_ips = socket.gethostbyname_ex(hostname)

                # hostname[2] contains all IP addresses for the hostname
                for ip in hostname_ips[2]:
                    if ip and not ip.startswith('127.') and not ip.startswith('169.254.'):
                        detected_ips.add(ip)
                        logger.debug(f"Detected hostname IP: {ip}")
            except Exception as hostname_error:
                logger.debug(f"Hostname IP detection failed: {hostname_error}")

            # Method 2: Get all network interfaces (backup method)
            try:
                local_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
                for info in local_info:
                    ip = info[4][0]
                    # Validate IP address format and filter private ranges
                    try:
                        ip_obj = ipaddress.ip_address(ip)
                        if ip_obj.is_private and not ip_obj.is_loopback and not ip_obj.is_link_local:
                            detected_ips.add(str(ip_obj))
                            logger.debug(f"Detected interface IP: {ip}")
                    except ValueError:
                        continue  # Skip invalid IP addresses
            except Exception as interface_error:
                logger.debug(f"Interface IP detection failed: {interface_error}")

            # Method 3: Fallback to common development IP ranges if no IPs detected
            if not detected_ips:
                logger.debug("No IPs detected, using fallback development IPs")
                # Common private network development ranges (conservative approach)
                fallback_ips = [
                    "192.168.1.100", "192.168.0.100", "192.168.68.100",
                    "10.0.0.100", "172.16.0.100"
                ]
                detected_ips.update(fallback_ips)

            # Validate and add mobile origins for detected IPs
            mobile_ports = [8081, 19000, 19006, 3000]
            valid_mobile_origins = 0

            for ip in detected_ips:
                try:
                    # Additional validation: try to bind to the IP to ensure it's available
                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    test_sock.bind((ip, 0))  # Bind to port 0 for testing
                    test_sock.close()

                    # If binding succeeds, the IP is available
                    for port in mobile_ports:
                        mobile_origin = f"http://{ip}:{port}"
                        if is_valid_origin(mobile_origin):
                            dev_origins.append(mobile_origin)
                            valid_mobile_origins += 1
                            logger.debug(f"Added mobile origin: {mobile_origin}")

                except (OSError, socket.error) as bind_error:
                    # IP is not available, skip it
                    logger.debug(f"IP {ip} not available: {bind_error}")
                    continue
                except Exception as validation_error:
                    logger.debug(f"Failed to validate IP {ip}: {validation_error}")
                    continue

            if valid_mobile_origins > 0:
                logger.info(f"Added {valid_mobile_origins} valid mobile origins from {len(detected_ips)} detected IPs")
            else:
                logger.warning("No valid mobile origins detected, mobile development may not work")

        except Exception as e:
            logger.error(f"Mobile network detection failed: {e}")
            # Add fallback localhost origins for development
            fallback_dev_origins = [
                "http://localhost:8081",
                "http://127.0.0.1:8081",
                "http://localhost:19000",
                "http://127.0.0.1:19000",
                "http://localhost:19006",
                "http://127.0.0.1:19006"
            ]
            for fallback_origin in fallback_dev_origins:
                if is_valid_origin(fallback_origin):
                    dev_origins.append(fallback_origin)
            logger.info("Added fallback localhost origins for mobile development")

        # Add validated development origins
        for dev_origin in dev_origins:
            if is_valid_origin(dev_origin):
                origins.append(dev_origin)

    # Production origins (if specified)
    if not is_development():
        prod_origins = os.getenv("PRODUCTION_ORIGINS", "").split(",") if os.getenv("PRODUCTION_ORIGINS") else []
        for prod_origin in prod_origins:
            prod_origin = prod_origin.strip()
            if is_valid_origin(prod_origin):
                origins.append(prod_origin)

    # Remove duplicates while preserving order (optimized)
    seen = set()
    unique_origins = []
    for origin in origins:
        if origin not in seen:
            seen.add(origin)
            unique_origins.append(origin)

    # Security check: ensure we have at least some valid origins in development
    if is_development() and not unique_origins:
        logger.warning("No valid CORS origins detected, adding fallback development origins")
        unique_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173"
        ]

    # Log final origins for debugging (but not in production for security)
    if is_development():
        logger.info(f"✅ Dynamic CORS origins ({len(unique_origins)}): {unique_origins}")
    else:
        logger.info(f"✅ Production CORS origins configured: {len(unique_origins)} origins")

    return unique_origins

# Get dynamic origins
ALLOWED_ORIGINS: List[str] = get_dynamic_origins()
