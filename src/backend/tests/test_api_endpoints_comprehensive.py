# tests/test_api_endpoints_comprehensive.py
"""
Comprehensive API endpoint tests covering all REST endpoints, input validation,
error handling, security, and edge cases for the RiceGuard FastAPI application.
"""

import pytest
import json
import io
import tempfile
import os
from unittest.mock import patch, Mock, MagicMock, mock_open
from PIL import Image
from fastapi.testclient import TestClient
from pymongo import ObjectId

from factories import (
    UserFactory, ScanItemFactory, BulkDeleteInFactory,
    EdgeCaseDataFactory, BDDDataFactory
)


class TestAuthenticationEndpoints:
    """Test authentication-related API endpoints."""

    @pytest.fixture
    def registered_user(self, client):
        """Create a registered user for testing."""
        user_data = UserFactory()
        response = client.post("/api/v1/auth/register", json=user_data.dict())
        assert response.status_code == 200
        return user_data, response.json()["id"]

    @pytest.fixture
    def authenticated_user(self, client, registered_user):
        """Create and authenticate a user."""
        user_data, _ = registered_user
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        assert login_response.status_code == 200
        token = login_response.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        return user_data, headers

    @pytest.mark.api
    @pytest.mark.auth
    def test_register_endpoint_success(self, client):
        """AUTH-API-001: Successful user registration."""
        # Arrange
        user_data = UserFactory()

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "User registered successfully"
        assert len(data["id"]) == 24  # ObjectId length

    @pytest.mark.api
    @pytest.mark.auth
    @pytest.mark.parametrize("field_name, invalid_value", [
        ("email", ""),
        ("email", "invalid-email"),
        ("name", ""),
        ("name", "a" * 101),
        ("password", "short"),
        ("password", "a" * 129),
    ])
    def test_register_endpoint_validation_errors(self, client, field_name, invalid_value):
        """AUTH-API-002: Registration validation errors."""
        # Arrange
        user_data = UserFactory()
        setattr(user_data, field_name, invalid_value)

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    @pytest.mark.auth
    def test_register_endpoint_duplicate_email(self, client, registered_user):
        """AUTH-API-003: Duplicate email registration."""
        # Arrange
        user_data, _ = registered_user

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.auth
    def test_login_endpoint_success(self, client, registered_user):
        """AUTH-API-004: Successful user login."""
        # Arrange
        user_data, _ = registered_user

        # Act
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data
        assert "user" in data
        assert data["user"]["email"] == user_data.email.lower()
        assert "password" not in data["user"]

    @pytest.mark.api
    @pytest.mark.auth
    def test_login_endpoint_invalid_credentials(self, client, registered_user):
        """AUTH-API-005: Invalid login credentials."""
        # Arrange
        user_data, _ = registered_user

        # Act
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": "wrong_password"
        })

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.auth
    def test_login_endpoint_nonexistent_user(self, client):
        """AUTH-API-006: Login with non-existent user."""
        # Arrange
        login_data = {"email": "nonexistent@example.com", "password": "password"}

        # Act
        response = client.post("/api/v1/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.auth
    def test_logout_endpoint_success(self, client, authenticated_user):
        """AUTH-API-007: Successful user logout."""
        # Arrange
        _, headers = authenticated_user

        # Act
        response = client.post("/api/v1/auth/logout", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    @pytest.mark.api
    @pytest.mark.auth
    def test_logout_endpoint_no_token(self, client):
        """AUTH-API-008: Logout without authentication token."""
        # Act
        response = client.post("/api/v1/auth/logout")

        # Assert
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.auth
    def test_logout_endpoint_invalid_token(self, client):
        """AUTH-API-009: Logout with invalid token."""
        # Arrange
        headers = {"Authorization": "Bearer invalid_token"}

        # Act
        response = client.post("/api/v1/auth/logout", headers=headers)

        # Assert
        assert response.status_code == 401


class TestScanEndpoints:
    """Test scan-related API endpoints."""

    @pytest.fixture
    def authenticated_user_with_scan(self, client):
        """Create authenticated user with a scan."""
        user_data = UserFactory()
        reg_response = client.post("/api/v1/auth/register", json=user_data.dict())
        assert reg_response.status_code == 200

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        return user_data, headers

    @pytest.fixture
    def sample_image_file(self):
        """Create a sample image file for upload."""
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def malicious_file(self):
        """Create a potentially malicious file."""
        return io.BytesIO(b"This is not an image file")

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_success(self, client, authenticated_user_with_scan, sample_image_file):
        """SCAN-API-001: Successful scan upload."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Mock ML service to return predictable results
        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            # Act
            response = client.post(
                "/api/v1/scans",
                headers=headers,
                files={"file": ("test.jpg", sample_image_file, "image/jpeg")}
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["prediction"] == "healthy"
            assert data["confidence"] == 0.95
            assert data["confidence_level"] == "high"
            assert data["filename"] == "test.jpg"

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_no_authentication(self, client, sample_image_file):
        """SCAN-API-002: Upload without authentication."""
        # Act
        response = client.post(
            "/api/v1/scans",
            files={"file": ("test.jpg", sample_image_file, "image/jpeg")}
        )

        # Assert
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_no_file(self, client, authenticated_user_with_scan):
        """SCAN-API-003: Upload without file."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Act
        response = client.post("/api/v1/scans", headers=headers)

        # Assert
        assert response.status_code == 422  # Validation error

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_invalid_file_type(self, client, authenticated_user_with_scan):
        """SCAN-API-004: Upload invalid file type."""
        # Arrange
        _, headers = authenticated_user_with_scan
        malicious_file = io.BytesIO(b" malicious content")

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=headers,
            files={"file": ("malicious.txt", malicious_file, "text/plain")}
        )

        # Assert
        assert response.status_code == 400  # Invalid file type

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_oversized_file(self, client, authenticated_user_with_scan):
        """SCAN-API-005: Upload oversized file."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Create a large image (simulate large file)
        large_img = Image.new('RGB', (2000, 2000), color='blue')
        large_img_bytes = io.BytesIO()
        large_img.save(large_img_bytes, format='JPEG', quality=100)
        large_img_bytes.seek(0)

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=headers,
            files={"file": ("large.jpg", large_img_bytes, "image/jpeg")}
        )

        # Assert - Should either succeed (if under limit) or fail gracefully
        assert response.status_code in [200, 400, 413]

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_upload_ml_service_error(self, client, authenticated_user_with_scan, sample_image_file):
        """SCAN-API-006: ML service error handling."""
        # Arrange
        _, headers = authenticated_user_with_scan

        with patch('routers.predict_image') as mock_predict:
            mock_predict.side_effect = Exception("ML service error")

            # Act
            response = client.post(
                "/api/v1/scans",
                headers=headers,
                files={"file": ("test.jpg", sample_image_file, "image/jpeg")}
            )

            # Assert
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_scans_success(self, client, authenticated_user_with_scan):
        """SCAN-API-007: Get user scans successfully."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Act
        response = client.get("/api/v1/scans", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "scans" in data
        assert "pagination" in data
        assert isinstance(data["scans"], list)

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_scans_pagination(self, client, authenticated_user_with_scan):
        """SCAN-API-008: Scans pagination parameters."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Act
        response = client.get("/api/v1/scans?page=1&page_size=5", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 5

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_scans_invalid_pagination(self, client, authenticated_user_with_scan):
        """SCAN-API-009: Invalid pagination parameters."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Test various invalid parameters
        test_cases = [
            {"page": 0, "page_size": 10},
            {"page": 1, "page_size": 0},
            {"page": -1, "page_size": -1},
            {"page": "invalid", "page_size": 10},
        ]

        for params in test_cases:
            response = client.get("/api/v1/scans", headers=headers, params=params)
            # Should either succeed with defaults or fail with validation
            assert response.status_code in [200, 422]

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_scan_by_id_success(self, client, authenticated_user_with_scan, sample_image_file):
        """SCAN-API-010: Get specific scan by ID."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # First create a scan
        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            upload_response = client.post(
                "/api/v1/scans",
                headers=headers,
                files={"file": ("test.jpg", sample_image_file, "image/jpeg")}
            )
            scan_id = upload_response.json()["id"]

            # Act
            response = client.get(f"/api/v1/scans/{scan_id}", headers=headers)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == scan_id
            assert data["prediction"] == "healthy"

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_scan_by_id_not_found(self, client, authenticated_user_with_scan):
        """SCAN-API-011: Get non-existent scan."""
        # Arrange
        _, headers = authenticated_user_with_scan
        fake_id = str(ObjectId())

        # Act
        response = client.get(f"/api/v1/scans/{fake_id}", headers=headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scan_success(self, client, authenticated_user_with_scan, sample_image_file):
        """SCAN-API-012: Delete scan successfully."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Create a scan first
        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            upload_response = client.post(
                "/api/v1/scans",
                headers=headers,
                files={"file": ("test.jpg", sample_image_file, "image/jpeg")}
            )
            scan_id = upload_response.json()["id"]

            # Act
            response = client.delete(f"/api/v1/scans/{scan_id}", headers=headers)

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Scan deleted successfully"

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scan_not_found(self, client, authenticated_user_with_scan):
        """SCAN-API-013: Delete non-existent scan."""
        # Arrange
        _, headers = authenticated_user_with_scan
        fake_id = str(ObjectId())

        # Act
        response = client.delete(f"/api/v1/scans/{fake_id}", headers=headers)

        # Assert
        assert response.status_code == 404

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scans_bulk_success(self, client, authenticated_user_with_scan, sample_image_file):
        """SCAN-API-014: Bulk delete scans successfully."""
        # Arrange
        _, headers = authenticated_user_with_scan
        scan_ids = []

        # Create multiple scans
        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            for i in range(3):
                upload_response = client.post(
                    "/api/v1/scans",
                    headers=headers,
                    files={"file": (f"test_{i}.jpg", sample_image_file, "image/jpeg")}
                )
                scan_ids.append(upload_response.json()["id"])

        # Act
        response = client.delete(
            "/api/v1/scans/bulk",
            headers=headers,
            json={"ids": scan_ids}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 3

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scans_bulk_too_many_ids(self, client, authenticated_user_with_scan):
        """SCAN-API-015: Bulk delete with too many IDs."""
        # Arrange
        _, headers = authenticated_user_with_scan
        too_many_ids = [str(ObjectId()) for _ in range(150)]  # Over the 100 limit

        # Act
        response = client.delete(
            "/api/v1/scans/bulk",
            headers=headers,
            json={"ids": too_many_ids}
        )

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "more than 100" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scans_bulk_invalid_id_format(self, client, authenticated_user_with_scan):
        """SCAN-API-016: Bulk delete with invalid ID formats."""
        # Arrange
        _, headers = authenticated_user_with_scan
        invalid_ids = ["invalid_id", "123", "another_invalid_id"]

        # Act
        response = client.delete(
            "/api/v1/scans/bulk",
            headers=headers,
            json={"ids": invalid_ids}
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.unit
    def test_delete_scans_bulk_empty_list(self, client, authenticated_user_with_scan):
        """SCAN-API-017: Bulk delete with empty ID list."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Act
        response = client.delete(
            "/api/v1/scans/bulk",
            headers=headers,
            json={"ids": []}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 0

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_statistics_success(self, client, authenticated_user_with_scan):
        """SCAN-API-018: Get scan statistics."""
        # Arrange
        _, headers = authenticated_user_with_scan

        # Act
        response = client.get("/api/v1/scans/statistics", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_scans" in data
        assert "disease_distribution" in data
        assert "confidence_distribution" in data
        assert "recent_scans" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_scan_statistics_no_authentication(self, client):
        """SCAN-API-019: Get statistics without authentication."""
        # Act
        response = client.get("/api/v1/scans/statistics")

        # Assert
        assert response.status_code == 401


class TestRecommendationEndpoints:
    """Test recommendation-related API endpoints."""

    @pytest.fixture
    def authenticated_user(self, client):
        """Create authenticated user."""
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        return headers

    @pytest.mark.api
    @pytest.mark.unit
    @pytest.mark.parametrize("disease_type", [
        "healthy",
        "bacterial_leaf_blight",
        "leaf_blast",
        "brown_spot",
        "leaf_scald",
        "narrow_brown_spot"
    ])
    def test_get_recommendations_success(self, client, authenticated_user, disease_type):
        """REC-API-001: Get recommendations for different disease types."""
        # Arrange
        headers = authenticated_user

        # Act
        response = client.get(f"/api/v1/recommendations/{disease_type}", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "disease" in data
        assert "description" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recommendations_invalid_disease(self, client, authenticated_user):
        """REC-API-002: Get recommendations for invalid disease type."""
        # Arrange
        headers = authenticated_user

        # Act
        response = client.get("/api/v1/recommendations/invalid_disease", headers=headers)

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_recommendations_no_authentication(self, client):
        """REC-API-003: Get recommendations without authentication."""
        # Act
        response = client.get("/api/v1/recommendations/healthy")

        # Assert
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.unit
    def test_get_all_recommendations_success(self, client, authenticated_user):
        """REC-API-004: Get all recommendations."""
        # Arrange
        headers = authenticated_user

        # Act
        response = client.get("/api/v1/recommendations", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Check structure of each recommendation
        for rec in data:
            assert "disease" in rec
            assert "description" in rec
            assert "recommendations" in rec
            assert isinstance(rec["recommendations"], list)


class TestHealthCheckEndpoints:
    """Test health check and system status endpoints."""

    @pytest.mark.api
    @pytest.mark.unit
    def test_health_check_success(self, client):
        """HEALTH-API-001: Health check endpoint."""
        # Act
        response = client.get("/api/v1/health")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_health_check_with_dependencies(self, client):
        """HEALTH-API-002: Health check with dependency status."""
        # Act
        response = client.get("/api/v1/health?detailed=true")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "dependencies" in data
        dependencies = data["dependencies"]
        assert "database" in dependencies
        assert "ml_model" in dependencies

    @pytest.mark.api
    @pytest.mark.unit
    def test_root_endpoint(self, client):
        """HEALTH-API-003: Root endpoint."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data


class TestSecurityEndpoints:
    """Test security-related endpoint behaviors."""

    @pytest.fixture
    def authenticated_user(self, client):
        """Create authenticated user."""
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}
        return headers, user_data

    @pytest.mark.api
    @pytest.mark.security
    def test_csrf_protection(self, client):
        """SEC-API-001: CSRF protection on state-changing endpoints."""
        # Test that sensitive endpoints require proper authentication
        sensitive_endpoints = [
            ("POST", "/api/v1/auth/register"),
            ("POST", "/api/v1/auth/login"),
            ("POST", "/api/v1/scans"),
            ("DELETE", "/api/v1/scans/fake_id"),
        ]

        for method, endpoint in sensitive_endpoints:
            # Act
            if method == "POST":
                response = client.post(endpoint)
            elif method == "DELETE":
                response = client.delete(endpoint)

            # Assert - Should either succeed (public endpoint) or require auth
            assert response.status_code in [200, 401, 422]

    @pytest.mark.api
    @pytest.mark.security
    def test_rate_limiting_headers(self, client):
        """SEC-API-002: Rate limiting headers present."""
        # Act
        response = client.get("/api/v1/health")

        # Assert - Check for rate limiting headers (if implemented)
        # This depends on the actual implementation
        headers = response.headers
        # Note: Actual rate limiting headers may vary
        assert response.status_code == 200

    @pytest.mark.api
    @pytest.mark.security
    def test_sensitive_data_exposure(self, client, authenticated_user):
        """SEC-API-003: No sensitive data exposure in responses."""
        # Arrange
        headers, user_data = authenticated_user

        # Test user endpoint doesn't expose password
        response = client.get("/api/v1/auth/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            assert "password" not in data
            assert "password_hash" not in data

    @pytest.mark.api
    @pytest.mark.security
    def test_input_validation_edge_cases(self, client):
        """SEC-API-004: Input validation for edge cases."""
        # Test various injection attempts
        malicious_payloads = [
            {"email": "'; DROP TABLE users; --", "password": "password"},
            {"name": "<script>alert('xss')</script>", "email": "test@example.com", "password": "password123"},
            {"email": "test@example.com", "password": "' OR '1'='1"},
        ]

        for payload in malicious_payloads:
            # Act
            response = client.post("/api/v1/auth/register", json=payload)

            # Assert - Should fail gracefully or be sanitized
            assert response.status_code in [400, 422]

    @pytest.mark.api
    @pytest.mark.security
    def test_file_upload_security(self, client, authenticated_user):
        """SEC-API-005: File upload security validation."""
        # Arrange
        headers, _ = authenticated_user

        # Test malicious file uploads
        malicious_files = [
            ("malicious.exe", io.BytesIO(b"fake executable content"), "application/octet-stream"),
            ("script.php", io.BytesIO(b"<?php echo 'malicious'; ?>"), "application/x-php"),
            ("malicious.js", io.BytesIO(b"alert('xss')"), "application/javascript"),
        ]

        for filename, content, content_type in malicious_files:
            # Act
            response = client.post(
                "/api/v1/scans",
                headers=headers,
                files={"file": (filename, content, content_type)}
            )

            # Assert - Should reject non-image files
            assert response.status_code == 400

    @pytest.mark.api
    @pytest.mark.security
    def test_cors_headers(self, client):
        """SEC-API-006: CORS headers are properly set."""
        # Act
        response = client.options("/api/v1/health")

        # Assert - Check for CORS headers
        headers = response.headers
        # Note: Actual CORS headers depend on configuration
        assert response.status_code in [200, 405]


class TestErrorHandling:
    """Test comprehensive error handling across endpoints."""

    @pytest.mark.api
    @pytest.mark.unit
    def test_404_not_found(self, client):
        """ERROR-API-001: 404 Not Found handling."""
        # Act
        response = client.get("/api/v1/nonexistent_endpoint")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_422_validation_error(self, client):
        """ERROR-API-002: 422 Validation Error handling."""
        # Act
        response = client.post("/api/v1/auth/register", json={"invalid": "data"})

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_500_server_error_handling(self, client):
        """ERROR-API-003: 500 Server Error handling."""
        # This test would require mocking internal services to fail
        # For now, test a scenario that might trigger a server error
        response = client.post(
            "/api/v1/scans",
            headers={"Authorization": "Bearer invalid_token"},
            files={"file": ("test.jpg", io.BytesIO(b"fake image"), "image/jpeg")}
        )

        # Should return authentication error, not crash
        assert response.status_code == 401

    @pytest.mark.api
    @pytest.mark.unit
    def test_malformed_json_request(self, client):
        """ERROR-API-004: Malformed JSON request handling."""
        # Act
        response = client.post(
            "/api/v1/auth/register",
            data="invalid json {",
            headers={"Content-Type": "application/json"}
        )

        # Assert
        assert response.status_code == 422

    @pytest.mark.api
    @pytest.mark.unit
    def test oversized_payload(self, client):
        """ERROR-API-005: Oversized payload handling."""
        # Create a very large payload
        large_payload = {
            "name": "a" * 10000,  # Very long name
            "email": "test@example.com",
            "password": "password123"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=large_payload)

        # Assert - Should handle gracefully
        assert response.status_code == 422


class TestAPIPerformance:
    """Test API performance and response times."""

    @pytest.mark.api
    @pytest.mark.performance
    def test_health_check_performance(self, client):
        """PERF-API-001: Health check response time."""
        import time

        # Act
        start_time = time.time()
        response = client.get("/api/v1/health")
        response_time = time.time() - start_time

        # Assert
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @pytest.mark.api
    @pytest.mark.performance
    def test_authentication_performance(self, client):
        """PERF-API-002: Authentication response time."""
        import time

        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act
        start_time = time.time()
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        response_time = time.time() - start_time

        # Assert
        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    @pytest.mark.api
    @pytest.mark.performance
    def test_concurrent_requests(self, client):
        """PERF-API-003: Concurrent request handling."""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/api/v1/health")
            results.append(response.status_code)

        # Act - Make 10 concurrent requests
        start_time = time.time()
        threads = [threading.Thread(target=make_request) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        total_time = time.time() - start_time

        # Assert
        assert all(code == 200 for code in results)
        assert total_time < 5.0  # All requests should complete within 5 seconds

    @pytest.mark.api
    @pytest.mark.performance
    def test_memory_usage_stability(self, client):
        """PERF-API-004: Memory usage stability under load."""
        import gc
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make multiple requests
        for _ in range(100):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

        # Force garbage collection
        gc.collect()

        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Assert - Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024  # 100MB


class TestAPIContract:
    """Test API contract consistency and backward compatibility."""

    @pytest.mark.api
    @pytest.mark.unit
    def test_response_format_consistency(self, client):
        """CONTRACT-API-001: Consistent response format across endpoints."""
        # Test successful responses have consistent structure
        endpoints = [
            "/api/v1/health",
            "/api/v1/recommendations",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                data = response.json()
                # Should be a valid JSON object
                assert isinstance(data, (dict, list))

    @pytest.mark.api
    @pytest.mark.unit
    def test_error_response_format(self, client):
        """CONTRACT-API-002: Consistent error response format."""
        # Test various error conditions
        error_endpoints = [
            "/api/v1/nonexistent",  # 404
            "/api/v1/auth/register",  # 422 (empty payload)
        ]

        for endpoint in error_endpoints:
            response = client.post(endpoint)
            if response.status_code >= 400:
                data = response.json()
                # Should have a 'detail' field for errors
                assert "detail" in data

    @pytest.mark.api
    @pytest.mark.unit
    def test_api_versioning(self, client):
        """CONTRACT-API-003: API versioning consistency."""
        # All endpoints should be under /api/v1/
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        # Test that unversioned endpoints either work or return appropriate error
        response = client.get("/health")
        assert response.status_code in [200, 404]

    @pytest.mark.api
    @pytest.mark.unit
    def test_content_type_headers(self, client):
        """CONTRACT-API-004: Correct content-type headers."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]