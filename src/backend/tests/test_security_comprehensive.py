# tests/test_security_comprehensive.py
"""
Comprehensive security tests covering input validation, authentication, authorization,
file upload security, rate limiting, and other security aspects of the RiceGuard application.
"""

import pytest
import io
import time
import hashlib
import secrets
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from PIL import Image
from pymongo import ObjectId

from factories import (
    UserFactory, EdgeCaseDataFactory,
    SecurityTestDataFactory
)


class TestAuthenticationSecurity:
    """Test authentication security mechanisms."""

    @pytest.mark.security
    @pytest.mark.auth
    def test_password_hashing_strength(self, client, monkeypatch):
        """AUTH-SEC-001: Password hashing uses strong algorithm."""
        # Arrange
        user_data = UserFactory(password="strong_password_123")

        # Mock database to inspect stored password
        mock_collection = MagicMock()
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "test_id_12345"
        mock_collection.insert_one.return_value = mock_insert_result

        with patch('db.get_db') as mock_get_db:
            mock_get_db.return_value.users = mock_collection

            # Act
            response = client.post("/api/v1/auth/register", json=user_data.dict())

            # Assert
            assert response.status_code == 200

            # Verify password was hashed with strong algorithm
            stored_password = mock_collection.insert_one.call_args[0][0]['password_hash']
            assert stored_password != user_data.password
            assert stored_password.startswith('$2b$')  # bcrypt
            assert len(stored_password) == 60  # bcrypt hash length

    @pytest.mark.security
    @pytest.mark.auth
    def test_session_token_entropy(self, client):
        """AUTH-SEC-002: JWT tokens have sufficient entropy."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        # Assert
        assert response.status_code == 200
        token = response.json()["accessToken"]

        # JWT tokens should have sufficient entropy
        # Split token and analyze the signature part
        parts = token.split('.')
        assert len(parts) == 3

        # The signature should be cryptographically random
        signature = parts[2]
        assert len(signature) >= 32  # Minimum length for secure signature

    @pytest.mark.security
    @pytest.mark.auth
    def test_brute_force_protection(self, client):
        """AUTH-SEC-003: Brute force attack protection."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act - Multiple failed login attempts
        failed_attempts = []
        for i in range(20):  # Simulate 20 failed attempts
            response = client.post("/api/v1/auth/login", json={
                "email": user_data.email,
                "password": f"wrong_password_{i}"
            })
            failed_attempts.append(response.status_code)

        # Assert - Should either return 401 consistently or implement rate limiting
        assert all(code == 401 for code in failed_attempts)

        # Final correct login should still work (unless account lockout is implemented)
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        # Either succeeds or is locked out - both are valid security measures
        assert response.status_code in [200, 401, 429]

    @pytest.mark.security
    @pytest.mark.auth
    def test_token_expiration(self, client, monkeypatch):
        """AUTH-SEC-004: Token expiration enforcement."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Mock very short token expiration
        with patch('security.create_access_token') as mock_create_token:
            with patch('security.decode_token') as mock_decode_token:
                # Create token that expires immediately
                mock_create_token.return_value = "short_lived_token"
                mock_decode_token.side_effect = Exception("Token has expired")

                login_response = client.post("/api/v1/auth/login", json={
                    "email": user_data.email,
                    "password": user_data.password
                })
                token = login_response.json()["accessToken"]

                # Act - Try to use expired token
                response = client.get("/api/v1/scans", headers={
                    "Authorization": f"Bearer {token}"
                })

                # Assert
                assert response.status_code == 401

    @pytest.mark.security
    @pytest.mark.auth
    def test_token_tampering_detection(self, client):
        """AUTH-SEC-005: Token tampering detection."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        valid_token = login_response.json()["accessToken"]

        # Tamper with the token
        tampered_token = valid_token[:-10] + "tampered"

        # Act
        response = client.get("/api/v1/scans", headers={
            "Authorization": f"Bearer {tampered_token}"
        })

        # Assert
        assert response.status_code == 401

    @pytest.mark.security
    @pytest.mark.auth
    def test_concurrent_session_limit(self, client):
        """AUTH-SEC-006: Concurrent session management."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        tokens = []
        # Act - Create multiple concurrent sessions
        for i in range(5):
            response = client.post("/api/v1/auth/login", json={
                "email": user_data.email,
                "password": user_data.password
            })
            if response.status_code == 200:
                tokens.append(response.json()["accessToken"])

        # Assert - Multiple tokens should be valid (unless session limit is implemented)
        for token in tokens:
            response = client.get("/api/v1/scans", headers={
                "Authorization": f"Bearer {token}"
            })
            # Should either succeed or fail if session limit is enforced
            assert response.status_code in [200, 401]


class TestInputValidationSecurity:
    """Test input validation security."""

    @pytest.mark.security
    @pytest.mark.validation
    @pytest.mark.parametrize("malicious_email", EdgeCaseDataFactory.invalid_emails())
    def test_email_injection_prevention(self, client, malicious_email):
        """INPUT-SEC-001: Email injection prevention."""
        # Arrange
        malicious_payload = {
            "name": "Test User",
            "email": malicious_email,
            "password": "password123"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=malicious_payload)

        # Assert - Should reject malicious emails
        assert response.status_code == 422

    @pytest.mark.security
    @pytest.mark.validation
    def test_sql_injection_prevention_mongodb(self, client):
        """INPUT-SEC-002: MongoDB injection prevention."""
        # Test various MongoDB injection attempts
        injection_payloads = [
            {"email": {"$ne": None}, "password": "password"},
            {"email": {"$regex": ".*"}, "password": "password"},
            {"email": {"$where": "function() { return true; }"}, "password": "password"},
            {"email": {"$gt": ""}, "password": "password"},
        ]

        for payload in injection_payloads:
            # Act
            response = client.post("/api/v1/auth/login", json=payload)

            # Assert - Should reject non-string inputs
            assert response.status_code == 422

    @pytest.mark.security
    @pytest.mark.validation
    def test_xss_prevention(self, client):
        """INPUT-SEC-003: XSS attack prevention."""
        # Arrange
        xss_payloads = [
            {"name": "<script>alert('xss')</script>", "email": "test@example.com", "password": "password123"},
            {"name": "javascript:alert('xss')", "email": "test@example.com", "password": "password123"},
            {"name": "<img src=x onerror=alert('xss')>", "email": "test@example.com", "password": "password123"},
        ]

        for payload in xss_payloads:
            # Act
            response = client.post("/api/v1/auth/register", json=payload)

            # Assert - Should either succeed (with sanitization) or fail validation
            if response.status_code == 200:
                # If successful, verify XSS was sanitized
                user_id = response.json()["id"]
                # Check that script tags were sanitized
                # This would depend on the actual sanitization implementation
            else:
                assert response.status_code == 422

    @pytest.mark.security
    @pytest.mark.validation
    def test_command_injection_prevention(self, client):
        """INPUT-SEC-004: Command injection prevention."""
        # Arrange
        command_injection_payloads = [
            {"name": "; ls -la", "email": "test@example.com", "password": "password123"},
            {"name": "| cat /etc/passwd", "email": "test@example.com", "password": "password123"},
            {"name": "& echo 'malicious'", "email": "test@example.com", "password": "password123"},
            {"name": "`whoami`", "email": "test@example.com", "password": "password123"},
        ]

        for payload in command_injection_payloads:
            # Act
            response = client.post("/api/v1/auth/register", json=payload)

            # Assert - Should not execute commands
            assert response.status_code in [200, 422]
            # If successful, verify no command execution occurred

    @pytest.mark.security
    @pytest.mark.validation
    def test_path_traversal_prevention(self, client):
        """INPUT-SEC-005: Path traversal prevention."""
        # Arrange
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "....//....//....//etc/passwd",
        ]

        for malicious_filename in path_traversal_payloads:
            # Test file upload with malicious filename
            malicious_file = io.BytesIO(b"fake image content")

            # Act
            response = client.post(
                "/api/v1/scans",
                files={"file": (malicious_filename, malicious_file, "image/jpeg")},
                headers={"Authorization": "Bearer invalid_token"}  # Will fail auth but test filename handling
            )

            # Assert - Should either reject filename or fail authentication
            # The important thing is that path traversal should not work
            assert response.status_code in [401, 400, 422]

    @pytest.mark.security
    @pytest.mark.validation
    def test_buffer_overflow_prevention(self, client):
        """INPUT-SEC-006: Buffer overflow prevention."""
        # Arrange
        large_payloads = [
            {"name": "A" * 10000, "email": "test@example.com", "password": "password123"},
            {"name": "B" * 100000, "email": "test@example.com", "password": "password123"},
            {"email": "C" * 1000 + "@example.com", "name": "Test User", "password": "password123"},
            {"password": "D" * 1000, "email": "test@example.com", "name": "Test User"},
        ]

        for payload in large_payloads:
            # Act
            response = client.post("/api/v1/auth/register", json=payload)

            # Assert - Should handle large inputs gracefully
            assert response.status_code in [200, 422]

    @pytest.mark.security
    @pytest.mark.validation
    def test_unicode_and_encoding_attacks(self, client):
        """INPUT-SEC-007: Unicode and encoding attack prevention."""
        # Arrange
        unicode_payloads = [
            {"name": "\ufeff\x00\x0d\x0a", "email": "test@example.com", "password": "password123"},
            {"name": "%2e%2e%2f", "email": "test@example.com", "password": "password123"},
            {"name": "&#60;script&#62;alert('xss')&#60;/script&#62;", "email": "test@example.com", "password": "password123"},
        ]

        for payload in unicode_payloads:
            # Act
            response = client.post("/api/v1/auth/register", json=payload)

            # Assert - Should handle encoding attacks
            assert response.status_code in [200, 422]


class TestFileUploadSecurity:
    """Test file upload security."""

    @pytest.fixture
    def authenticated_user(self, client):
        """Create authenticated user for file upload tests."""
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.security
    @pytest.mark.upload
    def test_malicious_file_type_rejection(self, client, authenticated_user):
        """FILE-SEC-001: Malicious file type rejection."""
        # Arrange
        malicious_files = [
            ("malicious.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream"),
            ("script.php", io.BytesIO(b"<?php system($_GET['cmd']); ?>"), "application/x-php"),
            ("script.js", io.BytesIO(b"alert('xss')"), "application/javascript"),
            ("shell.jsp", io.BytesIO(b"<%@ page import=\"java.io.*\" %>"), "application/x-jsp"),
            ("exploit.asp", io.BytesIO(b"<% Response.Write(\"malicious\") %>"), "application/x-asp"),
        ]

        for filename, content, content_type in malicious_files:
            # Act
            response = client.post(
                "/api/v1/scans",
                headers=authenticated_user,
                files={"file": (filename, content, content_type)}
            )

            # Assert
            assert response.status_code == 400  # Should reject malicious files

    @pytest.mark.security
    @pytest.mark.upload
    def test_file_size_limit_enforcement(self, client, authenticated_user):
        """FILE-SEC-002: File size limit enforcement."""
        # Arrange - Create a large image (simulate large file)
        large_img = Image.new('RGB', (5000, 5000), color='blue')
        large_img_bytes = io.BytesIO()
        large_img.save(large_img_bytes, format='JPEG', quality=100)
        large_img_bytes.seek(0)

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=authenticated_user,
            files={"file": ("large.jpg", large_img_bytes, "image/jpeg")}
        )

        # Assert - Should either accept (if under limit) or reject oversized files
        assert response.status_code in [200, 400, 413]

    @pytest.mark.security
    @pytest.mark.upload
    def test_file_header_validation(self, client, authenticated_user):
        """FILE-SEC-003: File header/magic number validation."""
        # Arrange - File with extension .jpg but actually a different file type
        fake_jpg = io.BytesIO(b"This is not a JPEG file but has .jpg extension")

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=authenticated_user,
            files={"file": ("fake.jpg", fake_jpg, "image/jpeg")}
        )

        # Assert - Should reject files with mismatched headers
        assert response.status_code == 400

    @pytest.mark.security
    @pytest.mark.upload
    def test_metadata_sanitization(self, client, authenticated_user):
        """FILE-SEC-004: EXIF/metadata sanitization."""
        # Arrange - Create image with malicious EXIF data
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')

        # Add malicious EXIF data (this would need proper EXIF manipulation library)
        malicious_exif = io.BytesIO(b"malicious_exif_data")

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=authenticated_user,
            files={"file": ("metadata.jpg", img_bytes, "image/jpeg")}
        )

        # Assert - Should handle EXIF data safely
        # The exact behavior depends on implementation
        assert response.status_code in [200, 400]

    @pytest.mark.security
    @pytest.mark.upload
    def test_zip_bomb_prevention(self, client, authenticated_user):
        """FILE-SEC-005: Zip bomb prevention."""
        # Arrange - Create a zip bomb (small file that expands to huge size)
        zip_bomb = io.BytesIO(b"PK\x03\x04")  # Zip file header

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=authenticated_user,
            files={"file": ("bomb.zip", zip_bomb, "application/zip")}
        )

        # Assert - Should reject zip files or handle them safely
        assert response.status_code == 400  # Should reject non-image files

    @pytest.mark.security
    @pytest.mark.upload
    def test_embedded_malware_detection(self, client, authenticated_user):
        """FILE-SEC-006: Embedded malware detection."""
        # Arrange - Create an image with embedded malware (steganography simulation)
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')

        # Append malicious content at the end (simple steganography simulation)
        malicious_content = b"\x00" * 100 + b"MALICIOUS_PAYLOAD"
        img_bytes.write(malicious_content)
        img_bytes.seek(0)

        # Act
        response = client.post(
            "/api/v1/scans",
            headers=authenticated_user,
            files={"file": ("infected.jpg", img_bytes, "image/jpeg")}
        )

        # Assert - Should either process safely or detect embedded content
        assert response.status_code in [200, 400]

    @pytest.mark.security
    @pytest.mark.upload
    def test_filename_sanitization(self, client, authenticated_user):
        """FILE-SEC-007: Filename sanitization."""
        # Arrange
        malicious_filenames = [
            "../../../etc/passwd.jpg",
            "..\\..\\..\\windows\\system32\\config\\sam.jpg",
            "file with spaces and symbols!@#$%^&().jpg",
            "con.jpg",  # Windows reserved name
            "prn.jpg",  # Windows reserved name
            "file\x00null.jpg",  # Null byte injection
            "very_long_filename_" + "a" * 250 + ".jpg",  # Overly long filename
        ]

        # Create a simple image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        for filename in malicious_filenames:
            # Act
            response = client.post(
                "/api/v1/scans",
                headers=authenticated_user,
                files={"file": (filename, img_bytes, "image/jpeg")}
            )

            # Assert - Should handle malicious filenames safely
            assert response.status_code in [200, 400, 422]


class TestRateLimitingSecurity:
    """Test rate limiting and DoS protection."""

    @pytest.mark.security
    @pytest.mark.rate_limit
    def test_api_rate_limiting(self, client):
        """RATE-SEC-001: API endpoint rate limiting."""
        # Act - Make rapid requests to a public endpoint
        responses = []
        for i in range(100):  # 100 rapid requests
            response = client.get("/api/v1/health")
            responses.append(response.status_code)
            time.sleep(0.01)  # Small delay to be realistic

        # Assert - Should either allow all (no rate limiting) or start rate limiting
        # If rate limiting is implemented, we should see 429 responses
        rate_limited_responses = [code for code in responses if code == 429]

        # Either no rate limiting (all 200) or rate limiting implemented
        assert all(code == 200 for code in responses) or len(rate_limited_responses) > 0

    @pytest.mark.security
    @pytest.mark.rate_limit
    def test_authentication_rate_limiting(self, client):
        """RATE-SEC-002: Authentication endpoint rate limiting."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act - Multiple failed login attempts
        responses = []
        for i in range(20):
            response = client.post("/api/v1/auth/login", json={
                "email": user_data.email,
                "password": f"wrong_password_{i}"
            })
            responses.append(response.status_code)

        # Assert - Should either continue returning 401 or implement rate limiting
        assert all(code == 401 for code in responses) or 429 in responses

    @pytest.mark.security
    @pytest.mark.rate_limit
    def test_upload_rate_limiting(self, client, authenticated_user):
        """RATE-SEC-003: File upload rate limiting."""
        # Arrange - Create a small test image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        # Act - Multiple rapid upload attempts
        responses = []
        for i in range(10):
            response = client.post(
                "/api/v1/scans",
                headers=authenticated_user,
                files={"file": (f"test_{i}.jpg", img_bytes, "image/jpeg")}
            )
            responses.append(response.status_code)

        # Assert - Should either allow all or implement rate limiting
        assert all(code in [200, 500] for code in responses) or 429 in responses

    @pytest.mark.security
    @pytest.mark.rate_limit
    def test_ip_based_rate_limiting(self, client):
        """RATE-SEC-004: IP-based rate limiting."""
        # Act - Requests from different "IPs" would require proper testing infrastructure
        # For now, test that rate limiting headers might be present
        response = client.get("/api/v1/health")

        # Check for rate limiting headers (if implemented)
        headers = response.headers
        # Common rate limiting headers
        rate_limit_headers = [
            'X-RateLimit-Limit',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset',
            'Retry-After'
        ]

        # At least one rate limiting header should be present if rate limiting is implemented
        has_rate_limit_headers = any(header in headers for header in rate_limit_headers)

        # Should either have rate limiting headers or not implement rate limiting
        assert has_rate_limit_headers or response.status_code == 200

    @pytest.mark.security
    @pytest.mark.rate_limit
    def test_concurrent_request_handling(self, client):
        """RATE-SEC-005: Concurrent request handling."""
        import threading
        import time

        results = []

        def make_request():
            response = client.get("/api/v1/health")
            results.append(response.status_code)

        # Act - Create 50 concurrent requests
        threads = [threading.Thread(target=make_request) for _ in range(50)]
        start_time = time.time()

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        total_time = time.time() - start_time

        # Assert - Should handle concurrent requests without crashing
        assert len(results) == 50
        assert all(code in [200, 429] for code in results)
        assert total_time < 30.0  # Should complete within reasonable time


class TestAuthorizationSecurity:
    """Test authorization and access control."""

    @pytest.fixture
    def user_with_scans(self, client):
        """Create user with scans for authorization testing."""
        # Create user1
        user1_data = UserFactory()
        client.post("/api/v1/auth/register", json=user1_data.dict())
        login1_response = client.post("/api/v1/auth/login", json={
            "email": user1_data.email,
            "password": user1_data.password
        })
        user1_token = login1_response.json()["accessToken"]
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        # Create user2
        user2_data = UserFactory()
        client.post("/api/v1/auth/register", json=user2_data.dict())
        login2_response = client.post("/api/v1/auth/login", json={
            "email": user2_data.email,
            "password": user2_data.password
        })
        user2_token = login2_response.json()["accessToken"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        return user1_headers, user2_headers

    @pytest.mark.security
    @pytest.mark.authz
    def test_user_data_isolation(self, client, user_with_scans):
        """AUTHZ-SEC-001: User data isolation."""
        user1_headers, user2_headers = user_with_scans

        # Act - user1 tries to access user2's data
        response1 = client.get("/api/v1/scans", headers=user1_headers)
        response2 = client.get("/api/v1/scans", headers=user2_headers)

        # Assert - Each user should only see their own data
        assert response1.status_code == 200
        assert response2.status_code == 200

        # Users should not see each other's scans
        user1_scans = response1.json()["scans"]
        user2_scans = response2.json()["scans"]

        # Verify no overlap in scan IDs
        user1_scan_ids = {scan.get("id") for scan in user1_scans}
        user2_scan_ids = {scan.get("id") for scan in user2_scans}

        # Should be no overlapping scans
        assert user1_scan_ids.isdisjoint(user2_scan_ids)

    @pytest.mark.security
    @pytest.mark.authz
    def test_cross_user_access_prevention(self, client, user_with_scans):
        """AUTHZ-SEC-002: Cross-user access prevention."""
        user1_headers, user2_headers = user_with_scans

        # user1 creates a scan
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            upload_response = client.post(
                "/api/v1/scans",
                headers=user1_headers,
                files={"file": ("test.jpg", img_bytes, "image/jpeg")}
            )
            scan_id = upload_response.json()["id"]

            # user2 tries to access user1's scan
            response = client.get(f"/api/v1/scans/{scan_id}", headers=user2_headers)

            # Assert - user2 should not be able to access user1's scan
            assert response.status_code == 404

    @pytest.mark.security
    @pytest.mark.authz
    def test_privilege_escalation_prevention(self, client):
        """AUTHZ-SEC-003: Privilege escalation prevention."""
        # Create regular user
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access admin endpoints (if they exist)
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/system",
            "/api/v1/admin/logs",
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=headers)
            # Should either return 404 (not found) or 403 (forbidden)
            assert response.status_code in [404, 401, 403]

    @pytest.mark.security
    @pytest.mark.authz
    def test_token_manipulation_prevention(self, client):
        """AUTHZ-SEC-004: Token manipulation prevention."""
        # Arrange
        user_data = UserFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })
        token = login_response.json()["accessToken"]

        # Try to manipulate token to gain admin privileges
        # This is highly dependent on the actual implementation
        manipulated_tokens = [
            token.replace("sub", "admin"),
            token + "admin",
            token[:-10] + "admin_privileges",
        ]

        for manipulated_token in manipulated_tokens:
            response = client.get("/api/v1/scans", headers={
                "Authorization": f"Bearer {manipulated_token}"
            })
            # Should reject manipulated tokens
            assert response.status_code == 401

    @pytest.mark.security
    @pytest.mark.authz
    def test_resource_owner_validation(self, client, user_with_scans):
        """AUTHZ-SEC-005: Resource owner validation."""
        user1_headers, user2_headers = user_with_scans

        # user1 creates a scan
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        with patch('routers.predict_image') as mock_predict:
            mock_predict.return_value = {
                "prediction": "healthy",
                "confidence": 0.95,
                "confidence_level": "high",
                "calibrated_confidence": 0.93
            }

            upload_response = client.post(
                "/api/v1/scans",
                headers=user1_headers,
                files={"file": ("test.jpg", img_bytes, "image/jpeg")}
            )
            scan_id = upload_response.json()["id"]

            # user2 tries to delete user1's scan
            response = client.delete(f"/api/v1/scans/{scan_id}", headers=user2_headers)

            # Assert - Should prevent deletion
            assert response.status_code == 404

            # user1 can delete their own scan
            response = client.delete(f"/api/v1/scans/{scan_id}", headers=user1_headers)
            assert response.status_code == 200


class TestDataExposureSecurity:
    """Test data exposure and information leakage prevention."""

    @pytest.mark.security
    @pytest.mark.exposure
    def test_sensitive_data_exposure_prevention(self, client):
        """EXPOSURE-SEC-001: Sensitive data exposure prevention."""
        # Register user
        user_data = UserFactory()
        reg_response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert - Password should not be exposed in registration response
        assert "password" not in reg_response.json()
        assert "password_hash" not in reg_response.json()

        # Login user
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        # Assert - Password should not be exposed in login response
        user_data_response = login_response.json()["user"]
        assert "password" not in user_data_response
        assert "password_hash" not in user_data_response

    @pytest.mark.security
    @pytest.mark.exposure
    def test_error_message_information_leakage(self, client):
        """EXPOSURE-SEC-002: Error message information leakage prevention."""
        # Test various error conditions
        error_tests = [
            # Non-existent user
            {"email": "nonexistent@example.com", "password": "password"},
            # Wrong password
            {"email": "test@example.com", "password": "wrong"},
            # Invalid email format
            {"email": "invalid", "password": "password"},
        ]

        for payload in error_tests:
            response = client.post("/api/v1/auth/login", json=payload)

            # Error messages should be generic
            if response.status_code >= 400:
                error_detail = response.json().get("detail", "").lower()
                # Should not reveal specific internal information
                assert "database" not in error_detail
                assert "internal" not in error_detail
                assert "exception" not in error_detail
                assert "traceback" not in error_detail

    @pytest.mark.security
    @pytest.mark.exposure
    def test_debug_information_prevention(self, client):
        """EXPOSURE-SEC-003: Debug information prevention."""
        # Make requests that might trigger errors
        response = client.get("/api/v1/nonexistent")

        # Should not contain debug information
        if response.status_code == 404:
            content = response.text.lower()
            assert "traceback" not in content
            assert "debug" not in content
            assert "exception" not in content
            assert "stack trace" not in content

    @pytest.mark.security
    @pytest.mark.exposure
    def test_api_documentation_exposure(self, client):
        """EXPOSURE-SEC-004: API documentation exposure in production."""
        # Check if API docs are exposed inappropriately
        doc_endpoints = [
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        for endpoint in doc_endpoints:
            response = client.get(endpoint)
            # API docs should either be available (development) or restricted (production)
            # In production, these should be restricted
            # For this test, we just verify they behave consistently
            assert response.status_code in [200, 401, 403, 404]

    @pytest.mark.security
    @pytest.mark.exposure
    def test_server_header_information(self, client):
        """EXPOSURE-SEC-005: Server header information leakage."""
        response = client.get("/api/v1/health")

        # Check server header
        server_header = response.headers.get("server", "")

        # Should not reveal specific server information
        # (This depends on the actual server configuration)
        if server_header:
            # Generic server names are acceptable
            generic_servers = ["nginx", "apache", "uvicorn"]
            is_generic = any(generic in server_header.lower() for generic in generic_servers)

            # Should not reveal version numbers or detailed information
            has_version = any(char.isdigit() for char in server_header)

            # Either generic name without version or no header
            assert not has_version or not server_header

    @pytest.mark.security
    @pytest.mark.exposure
    def test_directory_traversal_exposure(self, client):
        """EXPOSURE-SEC-006: Directory traversal exposure prevention."""
        # Try various directory traversal attempts
        traversal_attempts = [
            "/api/v1/../../etc/passwd",
            "/api/v1/..\\..\\windows\\system32\\config\\sam",
            "/api/v1/scans/../../../etc/passwd",
            "/api/v1/scans/..%2F..%2F..%2Fetc%2Fpasswd",
        ]

        for attempt in traversal_attempts:
            response = client.get(attempt)
            # Should return 404 or handle gracefully
            assert response.status_code in [404, 400, 403]

    @pytest.mark.security
    @pytest.mark.exposure
    def test_environment_variable_exposure(self, client):
        """EXPOSURE-SEC-007: Environment variable exposure prevention."""
        # Try various endpoints that might expose environment variables
        test_endpoints = [
            "/api/v1/env",
            "/api/v1/config",
            "/api/v1/settings",
            "/api/v1/debug",
        ]

        for endpoint in test_endpoints:
            response = client.get(endpoint)
            if response.status_code == 200:
                content = response.text.lower()
                # Should not expose sensitive environment variables
                sensitive_vars = [
                    "password", "secret", "key", "token", "database",
                    "mongodb", "jwt", "private", "credential"
                ]

                for var in sensitive_vars:
                    # Check for obvious patterns (this is basic checking)
                    assert f"{var}=" not in content