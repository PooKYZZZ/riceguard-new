# backend/db.py
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError, ConfigurationError
from bson import ObjectId
from settings import MONGO_URI, DB_NAME
import certifi
import logging

# Setup logging for database operations
log = logging.getLogger("riceguard.db")

_client: MongoClient | None = None

def get_client() -> MongoClient:
    """Get MongoDB client with enhanced error handling and optimized connection pooling."""
    global _client
    if _client is None:
        try:
            log.info("Initializing MongoDB connection with enhanced pool configuration...")

            # Validate MongoDB URI format
            if not MONGO_URI.startswith(('mongodb://', 'mongodb+srv://')):
                raise ConfigurationError("Invalid MongoDB URI format")

            # Enhanced connection pool configuration with proper error handling
            _client = MongoClient(
                MONGO_URI,
                uuidRepresentation="standard",
                tls=True,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=8000,
                # SECURITY: Hardened connection pool configuration against DoS attacks
                maxPoolSize=10,                    # Further reduced to prevent resource exhaustion
                minPoolSize=1,                     # Minimal baseline to conserve resources
                maxIdleTimeMS=30000,              # Reduced to 30s to free connections faster
                waitQueueTimeoutMS=1500,          # Faster failure detection for DoS protection
                retryWrites=True,                 # Retry write operations on failure
                retryReads=True,                  # Retry read operations on failure
                connectTimeoutMS=12000,           # Increased to 12s for better reliability
                socketTimeoutMS=30000,            # Reduced to 30s for faster timeout detection
                # Enhanced monitoring and error handling
                appName="RiceGuard Backend v1.1", # Identify this application in MongoDB logs
                # Connection retry and resilience settings
                retryMultiple=True,               # Retry multiple times on transient errors
                # Additional performance optimizations
                compressors="zlib",               # Simplified compression for broader compatibility
                zlibCompressionLevel=3,          # Lower compression level for better performance
                # Heartbeat and health monitoring
                heartbeatFrequencyMS=10000,      # Monitor connection health every 10 seconds
                serverMonitoringMode='poll',     # Use polling for better reliability
            )

            # Enhanced connection testing with timeout protection
            import signal
            from contextlib import contextmanager

            @contextmanager
            def timeout_context(seconds):
                def timeout_handler(signum, frame):
                    raise TimeoutError("Connection test timed out")

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(seconds)
                try:
                    yield
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)

            try:
                # Test the connection with timeout protection
                with timeout_context(15):  # 15 second timeout for connection test
                    admin_db = _client.admin
                    server_info = admin_db.command('serverStatus', maxTimeMS=10000)

                log.info(f"✅ MongoDB connection established successfully to: {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else 'local'}")
                log.info(f"MongoDB version: {server_info.get('version', 'unknown')}")

                # Enhanced connection pool monitoring
                try:
                    pool_stats = _client.topology_description.pool_stats
                    if pool_stats:
                        log.info(f"Connection pool status: available={pool_stats.get('available', 0)}")
                except Exception as pool_error:
                    log.warning(f"Could not retrieve pool stats: {pool_error}")

                # Set up connection monitoring
                def monitor_connection_health():
                    try:
                        # Ping the database to ensure connection is alive
                        admin_db = _client.admin
                        admin_db.command('ping', maxTimeMS=5000)
                    except Exception as e:
                        log.warning(f"Connection health check failed: {e}")
                        # Don't raise here - let individual operations handle connection issues

                # Store monitor function for later use
                _client._health_monitor = monitor_connection_health

            except TimeoutError:
                log.error("❌ MongoDB connection test timed out")
                _client = None
                raise RuntimeError("MongoDB connection test timed out")

        except ServerSelectionTimeoutError as e:
            log.error(f"❌ MongoDB server selection timeout: {e}")
            log.error("Please check:")
            log.error("  - MongoDB server is running and accessible")
            log.error("  - Network connectivity to MongoDB")
            log.error("  - IP whitelist in MongoDB Atlas (if using Atlas)")
            log.error(f"  - Connection string: {MONGO_URI}")
            _client = None
            raise RuntimeError(f"MongoDB connection failed: {e}")

        except ConnectionFailure as e:
            log.error(f"❌ MongoDB connection failure: {e}")
            log.error("Please check:")
            log.error("  - MongoDB credentials are correct")
            log.error("  - Database name is correct")
            log.error("  - Network connectivity")
            _client = None
            raise RuntimeError(f"MongoDB connection failed: {e}")

        except ConfigurationError as e:
            log.error(f"❌ MongoDB configuration error: {e}")
            log.error("Please check:")
            log.error("  - MongoDB URI format is correct")
            log.error("  - All required connection parameters are provided")
            _client = None
            raise RuntimeError(f"MongoDB configuration error: {e}")

        except Exception as e:
            log.error(f"❌ Unexpected MongoDB error: {e}")
            _client = None
            raise RuntimeError(f"Unexpected database error: {e}")

    return _client

def get_db():
    """Get database with enhanced connection health monitoring."""
    client = get_client()

    # Periodic health check
    try:
        if hasattr(client, '_health_monitor'):
            client._health_monitor()
    except Exception as e:
        log.warning(f"Database health check failed: {e}")
        # Continue with database operation - don't fail here

    return client[DB_NAME]

def ensure_indexes():
    """Create database indexes with enhanced error handling and logging."""
    try:
        db = get_db()
        log.info("Creating database indexes...")

        # User indexes
        try:
            db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
            log.info("✅ Created unique email index on users collection")
        except Exception as e:
            log.warning(f"Failed to create email index: {e}")

        # Scan indexes for performance
        try:
            db.scans.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)], name="user_createdAt")
            db.scans.create_index([("createdAt", DESCENDING)], name="created_at_desc")
            db.scans.create_index([("userId", ASCENDING)], name="user_id")
            log.info("✅ Created performance indexes on scans collection")
        except Exception as e:
            log.warning(f"Failed to create scan indexes: {e}")

        # Recommendation indexes
        try:
            db.recommendations.create_index([("diseaseKey", ASCENDING)], unique=True, name="uniq_disease_key")
            db.recommendations.create_index([("updatedAt", DESCENDING)], name="updated_at_desc")
            log.info("✅ Created indexes on recommendations collection")
        except Exception as e:
            log.warning(f"Failed to create recommendation indexes: {e}")

        # Additional performance indexes for common queries
        try:
            # Index for scan status queries
            db.scans.create_index([("userId", ASCENDING), ("status", ASCENDING)], name="user_status")
            # Index for disease prediction queries
            db.scans.create_index([("label", ASCENDING)], name="scan_label")
            # Index for confidence-based queries
            db.scans.create_index([("confidence", DESCENDING)], name="scan_confidence_desc")
            # Compound index for user activity tracking
            db.scans.create_index([("userId", ASCENDING), ("createdAt", DESCENDING), ("label", ASCENDING)], name="user_activity_index")
            # Index for file path lookups (used in static file serving)
            db.scans.create_index([("imageUrl", ASCENDING)], name="scan_imageUrl")
            # Index for model version tracking
            db.scans.create_index([("modelVersion", ASCENDING), ("createdAt", DESCENDING)], name="model_version_tracking")
            log.info("✅ Created additional performance indexes")
        except Exception as e:
            log.warning(f"Failed to create additional indexes: {e}")

        # Enhanced security and monitoring indexes
        try:
            # User activity monitoring indexes
            db.users.create_index([("lastLogin", DESCENDING)], name="user_last_login_desc")
            db.users.create_index([("createdAt", DESCENDING)], name="user_created_at_desc")
            db.users.create_index([("isActive", ASCENDING), ("createdAt", DESCENDING)], name="user_active_created")

            # Security monitoring indexes
            db.users.create_index([("failedLoginAttempts", DESCENDING), ("lastFailedLogin", DESCENDING)], name="security_failed_logins")
            db.users.create_index([("lockedUntil", ASCENDING)], name="security_locked_until")

            # Recommendation versioning and audit indexes
            db.recommendations.create_index([("version", DESCENDING), ("updatedAt", DESCENDING)], name="recommendation_version_audit")
            db.recommendations.create_index([("updatedAt", DESCENDING)], name="recommendations_updated_desc")

            # Specialized query optimization indexes
            db.scans.create_index([("userId", ASCENDING), ("confidence", DESCENDING)], name="user_confidence_index")
            db.scans.create_index([("label", ASCENDING), ("confidence", DESCENDING)], name="disease_confidence_index")
            db.scans.create_index([("modelVersion", ASCENDING), ("confidence", DESCENDING)], name="model_confidence_index")

            log.info("✅ Created security and monitoring indexes")
        except Exception as e:
            log.warning(f"Failed to create security indexes: {e}")

        log.info("✅ Database index creation completed")

    except Exception as e:
        log.error(f"❌ Failed to create database indexes: {e}")
        # Don't raise here - indexes are nice-to-have but not required for basic functionality

def as_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError("Invalid ObjectId format")

def close_client():
    """Close MongoDB connection with proper cleanup and logging."""
    global _client
    if _client is not None:
        try:
            log.info("Closing MongoDB connection...")
            _client.close()
            _client = None
            log.info("✅ MongoDB connection closed successfully")
        except Exception as e:
            log.warning(f"Error closing MongoDB connection: {e}")
            _client = None  # Force reset even on error
    else:
        log.debug("MongoDB client was already None")
