# backend/tests/test_fc_login.py
def test_FC_LOGIN_001_empty_fields_returns_422(client):
    r = client.post("/api/v1/auth/login", json={})
    assert r.status_code == 422
    # message corresponds to "Email and password are required."
    data = r.json()
    assert "detail" in data


def test_FC_LOGIN_002_invalid_email_returns_422(client):
    """
    Enter an invalid email format and any password.
    Expected: 422 Unprocessable Entity due to invalid email format.
    """
    payload = {"email": "invalid-email", "password": "12345678"}
    r = client.post("/api/v1/auth/login", json=payload)
    assert r.status_code == 422
    data = r.json()
    assert "detail" in data


def test_FC_LOGIN_003_valid_login_returns_access_token(client):
    """
    Enter valid email + password.
    Expected: 200 OK, token returned.
    """
    # 1. Register a valid user
    reg = client.post(
        "/api/v1/auth/register",
        json={"name": "TestUser", "email": "user@test.com", "password": "secret12"},
    )
    assert reg.status_code == 200

    # 2. Try logging in with same credentials
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "user@test.com", "password": "secret12"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "accessToken" in data
    assert data["user"]["email"] == "user@test.com"
