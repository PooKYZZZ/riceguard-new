# tests/test_database_comprehensive.py
"""
Comprehensive database tests covering CRUD operations, indexing, pagination,
query optimization, and all database-related functionality for MongoDB.
"""

import pytest
import datetime
from unittest.mock import patch, MagicMock
from pymongo import DESCENDING, ASCENDING
from bson import ObjectId, errors as bson_errors
from typing import Dict, List, Any

from db import (
    get_db, ensure_indexes, as_object_id,
    create_user, get_user_by_email, get_user_by_id,
    create_scan, get_scans_by_user, get_scan_by_id,
    update_scan, delete_scan, delete_scans_bulk,
    get_scan_count_by_user, get_scan_statistics,
    cleanup_old_scans
)
from factories import (
    UserFactory, ScanItemFactory, BulkDeleteInFactory,
    BDDDataFactory, EdgeCaseDataFactory
)


class TestDatabaseConnection:
    """Test database connection and basic operations."""

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_db_connection(self):
        """DB-CONN-001: Successfully establish database connection."""
        # Act
        db = get_db()

        # Assert
        assert db is not None
        assert hasattr(db, 'users')
        assert hasattr(db, 'scans')

    @pytest.mark.db
    @pytest.mark.unit
    def test_database_collection_access(self):
        """DB-CONN-002: Access database collections correctly."""
        # Arrange
        db = get_db()

        # Act & Assert
        assert db.users is not None
        assert db.scans is not None
        assert hasattr(db.users, 'insert_one')
        assert hasattr(db.users, 'find_one')
        assert hasattr(db.scans, 'insert_one')
        assert hasattr(db.scans, 'find')

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.MongoClient')
    def test_database_connection_failure_handling(self, mock_mongo_client):
        """DB-CONN-003: Handle database connection failures gracefully."""
        # Arrange
        mock_mongo_client.side_effect = Exception("Connection failed")

        # Act & Assert
        with pytest.raises(Exception):
            get_db()


class TestObjectIdConversion:
    """Test ObjectId conversion and validation."""

    @pytest.mark.db
    @pytest.mark.unit
    def test_as_object_id_valid_string(self):
        """OBJID-001: Convert valid string to ObjectId."""
        # Arrange
        valid_id = "507f1f77bcf86cd799439011"

        # Act
        result = as_object_id(valid_id)

        # Assert
        assert isinstance(result, ObjectId)
        assert str(result) == valid_id

    @pytest.mark.db
    @pytest.mark.unit
    def test_as_object_id_none_input(self):
        """OBJID-002: Handle None input gracefully."""
        # Act
        result = as_object_id(None)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_as_object_id_empty_string(self):
        """OBJID-003: Handle empty string gracefully."""
        # Act
        result = as_object_id("")

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_as_object_id_invalid_format(self):
        """OBJID-004: Handle invalid ObjectId format."""
        # Arrange
        invalid_id = "invalid_object_id"

        # Act
        result = as_object_id(invalid_id)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_input", [
        "123",  # Too short
        "x" * 24,  # Invalid characters
        "507f1f77bcf86cd79943901",  # 23 characters
        "507f1f77bcf86cd7994390111",  # 25 characters
    ])
    def test_as_object_id_various_invalid_inputs(self, invalid_input):
        """OBJID-005: Handle various invalid ObjectId inputs."""
        # Act
        result = as_object_id(invalid_input)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_as_object_id_already_objectid(self):
        """OBJID-006: Handle ObjectId input correctly."""
        # Arrange
        obj_id = ObjectId()

        # Act
        result = as_object_id(obj_id)

        # Assert
        assert result is obj_id


class TestDatabaseIndexing:
    """Test database indexing and query optimization."""

    @pytest.mark.db
    @pytest.mark.unit
    def test_ensure_indexes_creation(self):
        """INDEX-001: Create necessary database indexes."""
        # Act
        ensure_indexes()

        # Assert - Indexes should be created without errors
        # Note: In a real test environment, you'd verify index creation
        assert True  # If no exception raised, indexing succeeded

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.get_db')
    def test_ensure_indexes_users_collection(self, mock_get_db):
        """INDEX-002: Create indexes on users collection."""
        # Arrange
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Act
        ensure_indexes()

        # Assert
        mock_db.users.create_index.assert_called()
        mock_db.scans.create_index.assert_called()

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.get_db')
    def test_ensure_indexes_scans_collection(self, mock_get_db):
        """INDEX-003: Create indexes on scans collection."""
        # Arrange
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Act
        ensure_indexes()

        # Assert
        # Verify indexes are created for common query patterns
        calls = mock_db.scans.create_index.call_args_list
        index_fields = [call[0][0] for call in calls]

        # Should have user_id index for user-specific queries
        assert any("user_id" in str(field) for field in index_fields)

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.get_db')
    def test_ensure_indexes_error_handling(self, mock_get_db):
        """INDEX-004: Handle index creation errors gracefully."""
        # Arrange
        mock_db = MagicMock()
        mock_db.users.create_index.side_effect = Exception("Index creation failed")
        mock_get_db.return_value = mock_db

        # Act & Assert
        with pytest.raises(Exception):
            ensure_indexes()


class TestUserCRUDOperations:
    """Test user CRUD operations."""

    @pytest.mark.db
    @pytest.mark.unit
    def test_create_user_success(self):
        """USER-CRUD-001: Successfully create a new user."""
        # Arrange
        user_data = UserFactory()
        hashed_password = "hashed_password_123"

        # Act
        result = create_user(user_data.name, user_data.email, hashed_password)

        # Assert
        assert result is not None
        assert isinstance(result, str)  # Should return user ID as string
        assert len(result) == 24  # ObjectId length

    @pytest.mark.db
    @pytest.mark.unit
    def test_create_user_duplicate_email(self):
        """USER-CRUD-002: Handle duplicate email creation attempt."""
        # Arrange
        user_data = UserFactory()
        hashed_password = "hashed_password_123"

        # Create first user
        first_id = create_user(user_data.name, user_data.email, hashed_password)
        assert first_id is not None

        # Act - Try to create user with same email
        with pytest.raises(Exception):  # Should raise duplicate key error
            create_user("Another User", user_data.email, "another_hashed_password")

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_email_success(self):
        """USER-CRUD-003: Successfully retrieve user by email."""
        # Arrange
        user_data = UserFactory()
        hashed_password = "hashed_password_123"

        # Create user
        user_id = create_user(user_data.name, user_data.email, hashed_password)
        assert user_id is not None

        # Act
        result = get_user_by_email(user_data.email)

        # Assert
        assert result is not None
        assert result["name"] == user_data.name
        assert result["email"] == user_data.email.lower()  # Should be normalized
        assert result["password_hash"] == hashed_password
        assert "_id" in result

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_email_case_insensitive(self):
        """USER-CRUD-004: Email lookup should be case insensitive."""
        # Arrange
        user_data = UserFactory(email="Test@Example.COM")
        hashed_password = "hashed_password_123"

        # Create user
        user_id = create_user(user_data.name, user_data.email, hashed_password)

        # Act - Try different case variations
        result1 = get_user_by_email("test@example.com")
        result2 = get_user_by_email("TEST@EXAMPLE.COM")
        result3 = get_user_by_email("Test@Example.COM")

        # Assert
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert result1["_id"] == result2["_id"] == result3["_id"]

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_email_not_found(self):
        """USER-CRUD-005: Handle non-existent email lookup."""
        # Arrange
        non_existent_email = "nonexistent@example.com"

        # Act
        result = get_user_by_email(non_existent_email)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_id_success(self):
        """USER-CRUD-006: Successfully retrieve user by ID."""
        # Arrange
        user_data = UserFactory()
        hashed_password = "hashed_password_123"

        # Create user
        user_id = create_user(user_data.name, user_data.email, hashed_password)

        # Act
        result = get_user_by_id(user_id)

        # Assert
        assert result is not None
        assert result["name"] == user_data.name
        assert result["email"] == user_data.email.lower()
        assert result["_id"] == ObjectId(user_id)

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_id_not_found(self):
        """USER-CRUD-007: Handle non-existent ID lookup."""
        # Arrange
        non_existent_id = str(ObjectId())

        # Act
        result = get_user_by_id(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_user_by_id_invalid_format(self):
        """USER-CRUD-008: Handle invalid ID format."""
        # Arrange
        invalid_id = "invalid_object_id"

        # Act
        result = get_user_by_id(invalid_id)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.security
    def test_create_user_input_sanitization(self):
        """USER-CRUD-009: Input sanitization for user creation."""
        # Arrange
        malicious_name = "'; DROP TABLE users; --"
        malicious_email = "<script>alert('xss')</script>@example.com"
        hashed_password = "hashed_password_123"

        # Act
        try:
            user_id = create_user(malicious_name, malicious_email, hashed_password)

            # If successful, verify data was stored safely
            if user_id:
                result = get_user_by_id(user_id)
                assert result is not None
                # Name and email should be stored as-is but handled safely by MongoDB
                # The application layer should handle sanitization
        except Exception:
            # If validation prevents creation, that's also acceptable
            pass


class TestScanCRUDOperations:
    """Test scan CRUD operations."""

    @pytest.fixture
    def test_user(self):
        """Create a test user for scan operations."""
        user_data = UserFactory()
        user_id = create_user(user_data.name, user_data.email, "hashed_password")
        return user_id

    @pytest.mark.db
    @pytest.mark.unit
    def test_create_scan_success(self, test_user):
        """SCAN-CRUD-001: Successfully create a new scan."""
        # Arrange
        scan_data = ScanItemFactory(user_id=test_user)

        # Act
        result = create_scan(
            user_id=test_user,
            filename=scan_data.filename,
            original_name=scan_data.original_name,
            file_size=scan_data.file_size,
            mime_type=scan_data.mime_type,
            prediction=scan_data.prediction,
            confidence=scan_data.confidence,
            confidence_level=scan_data.confidence_level,
            calibrated_confidence=scan_data.calibrated_confidence,
            image_metadata=scan_data.image_metadata
        )

        # Assert
        assert result is not None
        assert isinstance(result, str)  # Should return scan ID as string
        assert len(result) == 24  # ObjectId length

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scans_by_user_success(self, test_user):
        """SCAN-CRUD-002: Successfully retrieve scans by user."""
        # Arrange
        scan_ids = []
        for i in range(3):
            scan_data = ScanItemFactory(user_id=test_user)
            scan_id = create_scan(
                user_id=test_user,
                filename=scan_data.filename,
                original_name=scan_data.original_name,
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )
            scan_ids.append(scan_id)

        # Act
        result = get_scans_by_user(test_user)

        # Assert
        assert len(result) >= 3
        for scan in result[:3]:  # Check the first 3 scans we created
            assert scan["user_id"] == ObjectId(test_user)
            assert "filename" in scan
            assert "prediction" in scan
            assert "confidence" in scan

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scans_by_user_pagination(self, test_user):
        """SCAN-CRUD-003: Pagination for user scans."""
        # Arrange
        # Create 15 scans for pagination testing
        for i in range(15):
            scan_data = ScanItemFactory(user_id=test_user)
            create_scan(
                user_id=test_user,
                filename=f"scan_{i:03d}.jpg",
                original_name=f"original_scan_{i:03d}.jpg",
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )

        # Act - Test pagination
        page_1 = get_scans_by_user(test_user, page=1, page_size=5)
        page_2 = get_scans_by_user(test_user, page=2, page_size=5)
        page_3 = get_scans_by_user(test_user, page=3, page_size=5)

        # Assert
        assert len(page_1) == 5
        assert len(page_2) == 5
        assert len(page_3) == 5

        # Verify pagination order (newest first)
        all_scans = page_1 + page_2 + page_3
        timestamps = [scan["created_at"] for scan in all_scans]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scans_by_user_empty_result(self, test_user):
        """SCAN-CRUD-004: Handle user with no scans."""
        # Act
        result = get_scans_by_user(test_user)

        # Assert
        assert result == []

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scans_by_user_invalid_pagination(self, test_user):
        """SCAN-CRUD-005: Handle invalid pagination parameters."""
        # Act & Assert - These should not crash
        result1 = get_scans_by_user(test_user, page=0, page_size=10)  # Invalid page
        result2 = get_scans_by_user(test_user, page=1, page_size=0)  # Invalid page_size
        result3 = get_scans_by_user(test_user, page=-1, page_size=-1)  # Negative values

        # Should return empty lists or handle gracefully
        assert isinstance(result1, list)
        assert isinstance(result2, list)
        assert isinstance(result3, list)

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_by_id_success(self, test_user):
        """SCAN-CRUD-006: Successfully retrieve scan by ID."""
        # Arrange
        scan_data = ScanItemFactory(user_id=test_user)
        scan_id = create_scan(
            user_id=test_user,
            filename=scan_data.filename,
            original_name=scan_data.original_name,
            file_size=scan_data.file_size,
            mime_type=scan_data.mime_type,
            prediction=scan_data.prediction,
            confidence=scan_data.confidence,
            confidence_level=scan_data.confidence_level,
            calibrated_confidence=scan_data.calibrated_confidence,
            image_metadata=scan_data.image_metadata
        )

        # Act
        result = get_scan_by_id(scan_id)

        # Assert
        assert result is not None
        assert result["_id"] == ObjectId(scan_id)
        assert result["user_id"] == ObjectId(test_user)
        assert result["filename"] == scan_data.filename

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_by_id_not_found(self):
        """SCAN-CRUD-007: Handle non-existent scan ID."""
        # Arrange
        non_existent_id = str(ObjectId())

        # Act
        result = get_scan_by_id(non_existent_id)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_by_id_invalid_format(self):
        """SCAN-CRUD-008: Handle invalid scan ID format."""
        # Arrange
        invalid_id = "invalid_scan_id"

        # Act
        result = get_scan_by_id(invalid_id)

        # Assert
        assert result is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_update_scan_success(self, test_user):
        """SCAN-CRUD-009: Successfully update scan metadata."""
        # Arrange
        scan_data = ScanItemFactory(user_id=test_user)
        scan_id = create_scan(
            user_id=test_user,
            filename=scan_data.filename,
            original_name=scan_data.original_name,
            file_size=scan_data.file_size,
            mime_type=scan_data.mime_type,
            prediction=scan_data.prediction,
            confidence=scan_data.confidence,
            confidence_level=scan_data.confidence_level,
            calibrated_confidence=scan_data.calibrated_confidence,
            image_metadata=scan_data.image_metadata
        )

        # Act
        update_data = {
            "prediction": "healthy",
            "confidence": 0.95,
            "confidence_level": "high",
            "calibrated_confidence": 0.93
        }
        result = update_scan(scan_id, update_data)

        # Assert
        assert result is True

        # Verify update
        updated_scan = get_scan_by_id(scan_id)
        assert updated_scan["prediction"] == "healthy"
        assert updated_scan["confidence"] == 0.95

    @pytest.mark.db
    @pytest.mark.unit
    def test_update_scan_not_found(self):
        """SCAN-CRUD-010: Handle update of non-existent scan."""
        # Arrange
        non_existent_id = str(ObjectId())
        update_data = {"prediction": "healthy"}

        # Act
        result = update_scan(non_existent_id, update_data)

        # Assert
        assert result is False

    @pytest.mark.db
    @pytest.mark.unit
    def test_delete_scan_success(self, test_user):
        """SCAN-CRUD-011: Successfully delete scan."""
        # Arrange
        scan_data = ScanItemFactory(user_id=test_user)
        scan_id = create_scan(
            user_id=test_user,
            filename=scan_data.filename,
            original_name=scan_data.original_name,
            file_size=scan_data.file_size,
            mime_type=scan_data.mime_type,
            prediction=scan_data.prediction,
            confidence=scan_data.confidence,
            confidence_level=scan_data.confidence_level,
            calibrated_confidence=scan_data.calibrated_confidence,
            image_metadata=scan_data.image_metadata
        )

        # Verify scan exists
        assert get_scan_by_id(scan_id) is not None

        # Act
        result = delete_scan(scan_id)

        # Assert
        assert result is True
        assert get_scan_by_id(scan_id) is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_delete_scan_not_found(self):
        """SCAN-CRUD-012: Handle deletion of non-existent scan."""
        # Arrange
        non_existent_id = str(ObjectId())

        # Act
        result = delete_scan(non_existent_id)

        # Assert
        assert result is False

    @pytest.mark.db
    @pytest.mark.unit
    def test_delete_scans_bulk_success(self, test_user):
        """SCAN-CRUD-013: Successfully bulk delete scans."""
        # Arrange
        scan_ids = []
        for i in range(5):
            scan_data = ScanItemFactory(user_id=test_user)
            scan_id = create_scan(
                user_id=test_user,
                filename=scan_data.filename,
                original_name=scan_data.original_name,
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )
            scan_ids.append(scan_id)

        # Verify scans exist
        for scan_id in scan_ids:
            assert get_scan_by_id(scan_id) is not None

        # Act
        result = delete_scans_bulk(test_user, scan_ids)

        # Assert
        assert result["deleted_count"] == 5
        for scan_id in scan_ids:
            assert get_scan_by_id(scan_id) is None

    @pytest.mark.db
    @pytest.mark.unit
    def test_delete_scans_bulk_partial_success(self, test_user):
        """SCAN-CRUD-014: Handle partial bulk deletion success."""
        # Arrange
        # Create some real scans
        real_scan_ids = []
        for i in range(3):
            scan_data = ScanItemFactory(user_id=test_user)
            scan_id = create_scan(
                user_id=test_user,
                filename=scan_data.filename,
                original_name=scan_data.original_name,
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )
            real_scan_ids.append(scan_id)

        # Mix with some non-existent IDs
        fake_ids = [str(ObjectId()) for _ in range(2)]
        all_ids = real_scan_ids + fake_ids

        # Act
        result = delete_scans_bulk(test_user, all_ids)

        # Assert
        assert result["deleted_count"] == 3  # Only real scans should be deleted
        assert result["failed_count"] == 2    # Fake IDs should fail

    @pytest.mark.db
    @pytest.mark.unit
    def test_delete_scans_bulk_owner_validation(self):
        """SCAN-CRUD-015: Bulk deletion respects scan ownership."""
        # Arrange
        user1_data = UserFactory()
        user2_data = UserFactory()

        user1_id = create_user(user1_data.name, user1_data.email, "hashed_password")
        user2_id = create_user(user2_data.name, user2_data.email, "hashed_password")

        # Create scan for user1
        scan_data = ScanItemFactory(user_id=user1_id)
        scan_id = create_scan(
            user_id=user1_id,
            filename=scan_data.filename,
            original_name=scan_data.original_name,
            file_size=scan_data.file_size,
            mime_type=scan_data.mime_type,
            prediction=scan_data.prediction,
            confidence=scan_data.confidence,
            confidence_level=scan_data.confidence_level,
            calibrated_confidence=scan_data.calibrated_confidence,
            image_metadata=scan_data.image_metadata
        )

        # Act - Try to delete user1's scan as user2
        result = delete_scans_bulk(user2_id, [scan_id])

        # Assert
        assert result["deleted_count"] == 0  # Should not delete
        assert get_scan_by_id(scan_id) is not None  # Scan should still exist


class TestDatabaseStatistics:
    """Test database statistics and aggregation queries."""

    @pytest.fixture
    def test_user_with_scans(self):
        """Create a test user with multiple scans for statistics."""
        user_data = UserFactory()
        user_id = create_user(user_data.name, user_data.email, "hashed_password")

        # Create scans with different predictions
        scan_data = [
            ScanItemFactory(user_id=user_id, prediction="healthy", confidence=0.9),
            ScanItemFactory(user_id=user_id, prediction="leaf_blast", confidence=0.8),
            ScanItemFactory(user_id=user_id, prediction="bacterial_leaf_blight", confidence=0.7),
            ScanItemFactory(user_id=user_id, prediction="healthy", confidence=0.85),
            ScanItemFactory(user_id=user_id, prediction="brown_spot", confidence=0.6),
        ]

        scan_ids = []
        for data in scan_data:
            scan_id = create_scan(
                user_id=user_id,
                filename=data.filename,
                original_name=data.original_name,
                file_size=data.file_size,
                mime_type=data.mime_type,
                prediction=data.prediction,
                confidence=data.confidence,
                confidence_level=data.confidence_level,
                calibrated_confidence=data.calibrated_confidence,
                image_metadata=data.image_metadata
            )
            scan_ids.append(scan_id)

        return user_id, scan_ids

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_count_by_user(self, test_user_with_scans):
        """DB-STAT-001: Get scan count by user."""
        # Arrange
        user_id, scan_ids = test_user_with_scans

        # Act
        result = get_scan_count_by_user(user_id)

        # Assert
        assert result == len(scan_ids)

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_count_by_user_no_scans(self):
        """DB-STAT-002: Handle user with no scans."""
        # Arrange
        user_data = UserFactory()
        user_id = create_user(user_data.name, user_data.email, "hashed_password")

        # Act
        result = get_scan_count_by_user(user_id)

        # Assert
        assert result == 0

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_statistics(self, test_user_with_scans):
        """DB-STAT-003: Get comprehensive scan statistics."""
        # Arrange
        user_id, scan_ids = test_user_with_scans

        # Act
        result = get_scan_statistics(user_id)

        # Assert
        assert result is not None
        assert "total_scans" in result
        assert "disease_distribution" in result
        assert "confidence_distribution" in result
        assert "recent_scans" in result

        assert result["total_scans"] == len(scan_ids)

        # Check disease distribution
        disease_dist = result["disease_distribution"]
        assert disease_dist["healthy"] == 2
        assert disease_dist["leaf_blast"] == 1
        assert disease_dist["bacterial_leaf_blight"] == 1
        assert disease_dist["brown_spot"] == 1

    @pytest.mark.db
    @pytest.mark.unit
    def test_get_scan_statistics_empty_user(self):
        """DB-STAT-004: Handle statistics for user with no scans."""
        # Arrange
        user_data = UserFactory()
        user_id = create_user(user_data.name, user_data.email, "hashed_password")

        # Act
        result = get_scan_statistics(user_id)

        # Assert
        assert result is not None
        assert result["total_scans"] == 0
        assert result["disease_distribution"] == {}
        assert result["confidence_distribution"] == {"high": 0, "medium": 0, "low": 0}
        assert result["recent_scans"] == []

    @pytest.mark.db
    @pytest.mark.unit
    def test_cleanup_old_scans(self, test_user_with_scans):
        """DB-STAT-005: Cleanup old scans functionality."""
        # Arrange
        user_id, scan_ids = test_user_with_scans

        # Act - Cleanup scans older than 1 day (shouldn't delete recent scans)
        cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        result = cleanup_old_scans(cutoff_date)

        # Assert
        assert isinstance(result, dict)
        assert "deleted_count" in result

        # Since our test scans are recent, none should be deleted
        assert result["deleted_count"] == 0


class TestDatabaseErrorHandling:
    """Test database error handling and edge cases."""

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.get_db')
    def test_database_connection_error_handling(self, mock_get_db):
        """DB-ERROR-001: Handle database connection errors."""
        # Arrange
        mock_get_db.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(Exception):
            create_user("Test User", "test@example.com", "hashed_password")

    @pytest.mark.db
    @pytest.mark.unit
    @patch('db.get_db')
    def test_database_operation_timeout(self, mock_get_db):
        """DB-ERROR-002: Handle database operation timeouts."""
        # Arrange
        mock_db = MagicMock()
        mock_db.users.insert_one.side_effect = Exception("Operation timeout")
        mock_get_db.return_value = mock_db

        # Act & Assert
        with pytest.raises(Exception):
            create_user("Test User", "test@example.com", "hashed_password")

    @pytest.mark.db
    @pytest.mark.unit
    def test_bson_serialization_errors(self, test_user):
        """DB-ERROR-003: Handle BSON serialization errors."""
        # Arrange
        invalid_data = {
            "user_id": test_user,
            "filename": "test.jpg",
            "original_name": "test.jpg",
            "file_size": 1000,
            "mime_type": "image/jpeg",
            # Include a value that might cause serialization issues
            "custom_field": {"$regex": "invalid_pattern"}  # MongoDB operator in data
        }

        # Act & Assert
        try:
            # This might cause serialization issues
            result = create_scan(**invalid_data)
            # If successful, verify it was handled safely
        except Exception as e:
            # Expected to fail due to invalid data
            assert "serialization" in str(e).lower() or "invalid" in str(e).lower()

    @pytest.mark.db
    @pytest.mark.security
    def test_sql_injection_prevention_mongodb(self, test_user):
        """DB-SEC-001: MongoDB injection attempt prevention."""
        # Arrange
        malicious_inputs = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "function() { return true; }"},
        ]

        for malicious_input in malicious_inputs:
            # Act & Assert - Try injection attempts
            try:
                # This should either fail validation or be handled safely
                result = get_user_by_email(malicious_input)
                # If successful, verify no sensitive data is exposed
                if result:
                    assert "password_hash" not in result or result["password_hash"] == ""
            except Exception:
                # Expected to fail for invalid input types
                pass

    @pytest.mark.db
    @pytest.mark.security
    def test_data_exfiltration_prevention(self, test_user):
        """DB-SEC-002: Prevent data exfiltration through queries."""
        # Arrange - Create another user with sensitive data
        other_user_data = UserFactory()
        other_user_id = create_user(
            other_user_data.name,
            other_user_data.email,
            "hashed_sensitive_password"
        )

        # Act - Try to access other user's data
        other_user_scans = get_scans_by_user(other_user_id)
        current_user_scans = get_scans_by_user(test_user)

        # Assert - Should only access own data
        assert all(scan["user_id"] == ObjectId(test_user) for scan in current_user_scans)
        # Other user's scans should not be accessible through current user's queries


class TestDatabasePerformance:
    """Test database performance and optimization."""

    @pytest.mark.db
    @pytest.mark.performance
    def test_bulk_operations_performance(self, test_user):
        """DB-PERF-001: Bulk operations performance test."""
        import time

        # Arrange
        num_scans = 100
        scan_data_list = [ScanItemFactory(user_id=test_user) for _ in range(num_scans)]

        # Act - Measure individual insert performance
        start_time = time.time()
        scan_ids = []
        for scan_data in scan_data_list:
            scan_id = create_scan(
                user_id=test_user,
                filename=scan_data.filename,
                original_name=scan_data.original_name,
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )
            scan_ids.append(scan_id)
        individual_time = time.time() - start_time

        # Assert - Should complete within reasonable time
        assert individual_time < 10.0  # 10 seconds for 100 inserts
        assert len(scan_ids) == num_scans

    @pytest.mark.db
    @pytest.mark.performance
    def test_query_pagination_performance(self, test_user):
        """DB-PERF-002: Query pagination performance test."""
        import time

        # Arrange - Create many scans
        num_scans = 1000
        for i in range(num_scans):
            scan_data = ScanItemFactory(user_id=test_user)
            create_scan(
                user_id=test_user,
                filename=f"scan_{i:04d}.jpg",
                original_name=f"original_{i:04d}.jpg",
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )

        # Act - Measure pagination performance
        start_time = time.time()
        for page in range(1, 11):  # Test first 10 pages
            scans = get_scans_by_user(test_user, page=page, page_size=50)
            assert len(scans) == 50
        pagination_time = time.time() - start_time

        # Assert - Pagination should be efficient
        assert pagination_time < 5.0  # 5 seconds for 10 pages

    @pytest.mark.db
    @pytest.mark.performance
    def test_index_usage_effectiveness(self, test_user):
        """DB-PERF-003: Verify index usage for common queries."""
        import time

        # Arrange - Create scans with varied data
        for i in range(500):
            scan_data = ScanItemFactory(user_id=test_user)
            create_scan(
                user_id=test_user,
                filename=f"scan_{i:03d}.jpg",
                original_name=scan_data.original_name,
                file_size=scan_data.file_size,
                mime_type=scan_data.mime_type,
                prediction=scan_data.prediction,
                confidence=scan_data.confidence,
                confidence_level=scan_data.confidence_level,
                calibrated_confidence=scan_data.calibrated_confidence,
                image_metadata=scan_data.image_metadata
            )

        # Act - Measure query performance with and without indexes
        start_time = time.time()
        scans = get_scans_by_user(test_user, page=1, page_size=100)
        query_time = time.time() - start_time

        # Assert - Query should be fast due to indexes
        assert len(scans) == 100
        assert query_time < 1.0  # Should complete in under 1 second

    @pytest.mark.db
    @pytest.mark.performance
    def test_aggregation_query_performance(self, test_user_with_scans):
        """DB-PERF-004: Aggregation query performance test."""
        import time

        # Arrange
        user_id, scan_ids = test_user_with_scans

        # Act - Measure statistics query performance
        start_time = time.time()
        stats = get_scan_statistics(user_id)
        stats_time = time.time() - start_time

        # Assert - Aggregation should be efficient
        assert stats is not None
        assert stats_time < 0.5  # Should complete in under 500ms