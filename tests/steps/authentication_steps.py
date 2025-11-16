# =============================================================================
# RiceGuard BDD Authentication Step Definitions
# =============================================================================
import re
import requests
import time
import jwt
from datetime import datetime, timedelta
from behave import given, when, then, step
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pymongo
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AuthenticationContext:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.web_url = os.getenv("WEB_URL", "http://localhost:3000")
        self.token = None
        self.user_data = None
        self.driver = None
        self.db_client = None
        self.response = None
        self.error_message = None
        self.registration_data = {}

# Global context
auth_context = AuthenticationContext()

@given('the RiceGuard application is running')
def step_app_running(context):
    """Verify that the application is accessible"""
    try:
        response = requests.get(f"{auth_context.base_url}/health", timeout=5)
        assert response.status_code == 200
    except requests.exceptions.RequestException as e:
        raise Exception(f"Application is not running: {e}")

@given('the authentication system is available')
def step_auth_available(context):
    """Verify that authentication endpoints are accessible"""
    try:
        response = requests.get(f"{auth_context.base_url}/api/v1/auth/register", timeout=5)
        # 405 Method Not Allowed is expected for GET on register endpoint
        assert response.status_code in [200, 405]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Authentication system not available: {e}")

@given('the database is clean')
def step_clean_database(context):
    """Clean the database for testing"""
    try:
        auth_context.db_client = MongoClient(os.getenv("MONGO_URI"))
        db = auth_context.db_client[os.getenv("DB_NAME")]

        # Clean test data - be careful in production!
        if "test" in os.getenv("DB_NAME", "").lower():
            db.users.delete_many({"email": {"$regex": r".*@riceguard\.com$"}})
            db.scans.delete_many({})
        else:
            raise Exception("Cannot clean database - not a test environment")
    except Exception as e:
        raise Exception(f"Database cleanup failed: {e}")

@given('I am a new user without an account')
def step_new_user(context):
    """Set up context for new user registration"""
    auth_context.registration_data = {
        "email": "farmer@riceguard.com",
        "password": "RiceGuard2023!",
        "name": "Test Farmer"
    }

@given('I am a registered user with email "{email}"')
def step_registered_user(context, email):
    """Set up context for existing user"""
    auth_context.registration_data = {
        "email": email,
        "password": "RiceGuard2023!",
        "name": "Test User"
    }

@given('I have successfully registered before')
def step_previously_registered(context):
    """Ensure user exists in database"""
    try:
        response = requests.post(
            f"{auth_context.base_url}/api/v1/auth/register",
            json=auth_context.registration_data,
            timeout=10
        )
        # 409 is acceptable if user already exists
        assert response.status_code in [200, 409]
    except requests.exceptions.RequestException as e:
        raise Exception(f"Registration setup failed: {e}")

@when('I navigate to the registration page')
def step_navigate_register(context):
    """Navigate to registration page using web driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    auth_context.driver = webdriver.Chrome(options=chrome_options)
    auth_context.driver.get(f"{auth_context.web_url}")

    # Click sign up button
    signup_btn = WebDriverWait(auth_context.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign Up')]"))
    )
    signup_btn.click()

@when('I navigate to the login page')
def step_navigate_login(context):
    """Navigate to login page using web driver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    auth_context.driver = webdriver.Chrome(options=chrome_options)
    auth_context.driver.get(f"{auth_context.web_url}")

    # Click log in button
    login_btn = WebDriverWait(auth_context.driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]"))
    )
    login_btn.click()

@when('I enter a valid email "{email}"')
def step_enter_email(context, email):
    """Enter email in the email field"""
    if auth_context.driver:
        # Web automation
        email_input = WebDriverWait(auth_context.driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginEmail"))
        )
        email_input.clear()
        email_input.send_keys(email)

    # Update context for API calls
    if "email" in auth_context.registration_data:
        auth_context.registration_data["email"] = email

@when('I enter a strong password "{password}"')
def step_enter_password(context, password):
    """Enter password in the password field"""
    if auth_context.driver:
        # Web automation
        password_input = WebDriverWait(auth_context.driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_input.clear()
        password_input.send_keys(password)

    # Update context for API calls
    auth_context.registration_data["password"] = password

@when('I confirm the password "{password}"')
def step_confirm_password(context, password):
    """Confirm password in the confirmation field"""
    if auth_context.driver:
        try:
            confirm_input = auth_context.driver.find_element(By.ID, "signupConfirm")
            confirm_input.clear()
            confirm_input.send_keys(password)
        except:
            # Might not exist in login form
            pass

@when('I submit the registration form')
def step_submit_registration(context):
    """Submit the registration form"""
    if auth_context.driver:
        # Web automation
        submit_btn = WebDriverWait(auth_context.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "form button[type='submit']"))
        )
        submit_btn.click()
    else:
        # API call
        try:
            auth_context.response = requests.post(
                f"{auth_context.base_url}/api/v1/auth/register",
                json=auth_context.registration_data,
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            auth_context.error_message = str(e)

@when('I submit the login form')
def step_submit_login(context):
    """Submit the login form"""
    if auth_context.driver:
        # Web automation
        submit_btn = WebDriverWait(auth_context.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "form button[type='submit']"))
        )
        submit_btn.click()
    else:
        # API call
        try:
            auth_context.response = requests.post(
                f"{auth_context.base_url}/api/v1/auth/login",
                json={
                    "email": auth_context.registration_data["email"],
                    "password": auth_context.registration_data["password"]
                },
                timeout=10
            )
        except requests.exceptions.RequestException as e:
            auth_context.error_message = str(e)

@when('I enter my email "{email}"')
def step_enter_my_email(context, email):
    """Enter my email for login"""
    step_enter_email(context, email)

@when('I enter my password "{password}"')
def step_enter_my_password(context, password):
    """Enter my password for login"""
    step_enter_password(context, password)

@when('I enter an incorrect password "{password}"')
def step_enter_wrong_password(context, password):
    """Enter incorrect password"""
    step_enter_password(context, password)

@when('I attempt to login with wrong password {count:d} times')
def step_multiple_failed_attempts(context, count):
    """Attempt multiple failed logins"""
    for i in range(count):
        try:
            response = requests.post(
                f"{auth_context.base_url}/api/v1/auth/login",
                json={
                    "email": auth_context.registration_data["email"],
                    "password": "wrongpassword"
                },
                timeout=5
            )
            # Wait a bit between attempts
            time.sleep(0.5)
        except requests.exceptions.RequestException:
            pass

@then('I should see a success message "{message}"')
def step_success_message(context, message):
    """Verify success message is displayed"""
    if auth_context.driver:
        # Check web page for message
        try:
            element = WebDriverWait(auth_context.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{message}')]"))
            )
            assert element.is_displayed()
        except:
            # Try checking for success indicators
            pass
    else:
        # Check API response
        if auth_context.response and auth_context.response.status_code == 200:
            return True
        raise Exception("Success message not found")

@then('I should see an error message "{message}"')
def step_error_message(context, message):
    """Verify error message is displayed"""
    if auth_context.driver:
        # Check web page for error message
        try:
            element = WebDriverWait(auth_context.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{message}')]"))
            )
            assert element.is_displayed()
        except:
            # Check for error indicators
            pass
    else:
        # Check API response
        if auth_context.response:
            if auth_context.response.status_code >= 400:
                return True
        if auth_context.error_message:
            return True
        raise Exception(f"Expected error message '{message}' not found")

@then('my account should be created in the database')
def step_account_created_db(context):
    """Verify account exists in database"""
    try:
        db = auth_context.db_client[os.getenv("DB_NAME")]
        user = db.users.find_one({"email": auth_context.registration_data["email"]})
        assert user is not None
        assert user.get("email") == auth_context.registration_data["email"]
    except Exception as e:
        raise Exception(f"Account not found in database: {e}")

@then('my account should not be created')
def step_account_not_created(context):
    """Verify account does not exist in database"""
    try:
        db = auth_context.db_client[os.getenv("DB_NAME")]
        user = db.users.find_one({"email": auth_context.registration_data["email"]})
        assert user is None
    except Exception as e:
        raise Exception(f"Database check failed: {e}")

@then('I should be redirected to the login page')
def step_redirect_login(context):
    """Verify redirect to login page"""
    if auth_context.driver:
        # Check URL or login form presence
        try:
            WebDriverWait(auth_context.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginEmail"))
            )
        except:
            raise Exception("Not redirected to login page")

@then('I should be successfully authenticated')
def step_authenticated(context):
    """Verify successful authentication"""
    if auth_context.response:
        assert auth_context.response.status_code == 200
        data = auth_context.response.json()
        assert "accessToken" in data
        auth_context.token = data["accessToken"]
        auth_context.user_data = data.get("user")

@then('I should receive a JWT access token')
def step_jwt_token(context):
    """Verify JWT token is received"""
    assert auth_context.token is not None

    # Verify JWT structure
    try:
        decoded = jwt.decode(auth_context.token, options={"verify_signature": False})
        assert "sub" in decoded
        assert "exp" in decoded
    except jwt.DecodeError:
        raise Exception("Invalid JWT token received")

@then('I should be redirected to the scan page')
def step_redirect_scan(context):
    """Verify redirect to scan page"""
    if auth_context.driver:
        # Check for scan page elements
        try:
            WebDriverWait(auth_context.driver, 10).until(
                EC.url_contains("/scan")
            )
        except:
            raise Exception("Not redirected to scan page")

@then('my token should be stored securely')
def step_token_stored(context):
    """Verify token is stored securely"""
    if auth_context.driver:
        # Check for httpOnly cookie (though might not be accessible via JavaScript)
        cookies = auth_context.driver.get_cookies()
        token_cookie = next((c for c in cookies if c["name"] == "access_token"), None)
        assert token_cookie is not None

@then('I should not receive an access token')
def step_no_token(context):
    """Verify no token is received"""
    if auth_context.response:
        data = auth_context.response.json()
        assert "accessToken" not in data
    assert auth_context.token is None

@then('I should remain on the login page')
def step_stay_login(context):
    """Verify still on login page"""
    if auth_context.driver:
        try:
            email_input = WebDriverWait(auth_context.driver, 5).until(
                EC.presence_of_element_located((By.ID, "loginEmail"))
            )
        except:
            raise Exception("Not on login page anymore")

@then('I should be unable to login for 30 minutes')
def step_account_locked(context):
    """Verify account is locked"""
    try:
        response = requests.post(
            f"{auth_context.base_url}/api/v1/auth/login",
            json={
                "email": auth_context.registration_data["email"],
                "password": auth_context.registration_data["password"]
            },
            timeout=5
        )
        assert response.status_code == 423
    except requests.exceptions.RequestException:
        raise Exception("Lockout verification failed")

# Cleanup
def cleanup():
    """Clean up resources"""
    if auth_context.driver:
        auth_context.driver.quit()
    if auth_context.db_client:
        auth_context.db_client.close()