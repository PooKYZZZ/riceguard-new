# =============================================================================
# RiceGuard User Authentication BDD Scenarios
# =============================================================================
Feature: User Authentication
  As a rice farmer or agricultural worker
  I want to securely register, login, and manage my account
  So that I can access the rice disease detection services

  Background:
    Given the RiceGuard application is running
    And the authentication system is available
    And the database is clean

  Scenario: Successful User Registration
    Given I am a new user without an account
    When I navigate to the registration page
    And I enter a valid email "farmer@riceguard.com"
    And I enter a strong password "RiceGuard2023!"
    And I confirm the password "RiceGuard2023!"
    And I submit the registration form
    Then I should see a success message "Account created successfully"
    And my account should be created in the database
    And I should be redirected to the login page

  Scenario: Registration with Weak Password
    Given I am a new user without an account
    When I navigate to the registration page
    And I enter a valid email "farmer@riceguard.com"
    And I enter a weak password "123"
    And I confirm the password "123"
    And I submit the registration form
    Then I should see an error message "Password must be at least 8 characters"
    And my account should not be created

  Scenario: Registration with Invalid Email
    Given I am a new user without an account
    When I navigate to the registration page
    And I enter an invalid email "invalid-email"
    And I enter a valid password "RiceGuard2023!"
    And I confirm the password "RiceGuard2023!"
    And I submit the registration form
    Then I should see an error message "Please enter a valid email address"
    And my account should not be created

  Scenario: Registration with Duplicate Email
    Given I am an existing user with email "existing@riceguard.com"
    And I have successfully registered before
    When I navigate to the registration page
    And I enter the existing email "existing@riceguard.com"
    And I enter a valid password "RiceGuard2023!"
    And I confirm the password "RiceGuard2023!"
    And I submit the registration form
    Then I should see an error message "Email already registered"
    And no new account should be created

  Scenario: Successful Login
    Given I am a registered user with email "farmer@riceguard.com"
    And I have a valid password "RiceGuard2023!"
    When I navigate to the login page
    And I enter my email "farmer@riceguard.com"
    And I enter my password "RiceGuard2023!"
    And I submit the login form
    Then I should be successfully authenticated
    And I should receive a JWT access token
    And I should be redirected to the scan page
    And my token should be stored securely

  Scenario: Login with Invalid Credentials
    Given I am a registered user with email "farmer@riceguard.com"
    When I navigate to the login page
    And I enter my email "farmer@riceguard.com"
    And I enter an incorrect password "wrongpassword"
    And I submit the login form
    Then I should see an error message "Invalid email or password"
    And I should not receive an access token
    And I should remain on the login page

  Scenario: Login with Non-existent Account
    When I navigate to the login page
    And I enter a non-existent email "nonexistent@riceguard.com"
    And I enter any password "anypassword"
    And I submit the login form
    Then I should see an error message "Invalid email or password"
    And I should not receive an access token
    And I should remain on the login page

  Scenario: Account Lockout After Multiple Failed Attempts
    Given I am a registered user with email "farmer@riceguard.com"
    And I attempt to login with wrong password 5 times
    When I try to login again on the 6th attempt
    Then I should see an error message "Account temporarily locked"
    And I should be unable to login for 30 minutes
    And the lockout should be recorded in security logs

  Scenario: Secure Logout
    Given I am successfully logged in
    And I have a valid access token
    When I click the logout button
    Then my access token should be invalidated
    And I should be redirected to the landing page
    And my secure storage should be cleared

  Scenario: Session Timeout
    Given I am successfully logged in
    And my session has expired after 6 hours
    When I try to access a protected endpoint
    Then I should receive a 401 Unauthorized error
    And I should be redirected to the login page
    And my local token should be cleared

  Scenario: Cross-Platform Authentication Consistency
    Given I register an account through the web application
    When I try to login with the same credentials on the mobile app
    Then I should be successfully authenticated on mobile
    And my user data should be consistent across platforms
    And my scan history should be synchronized

  Scenario: Password Security Requirements
    Given I am registering a new account
    When I try to register with password "password123" (no special character)
    Then I should see an error about missing special character
    When I try to register with password "PASSWORD123" (no lowercase)
    Then I should see an error about missing lowercase letter
    When I try to register with password "password123" (no uppercase)
    Then I should see an error about missing uppercase letter
    When I try to register with password "Password!" (no digit)
    Then I should see an error about missing digit
    When I register with password "RiceGuard2023!" (meets all requirements)
    Then my registration should be successful