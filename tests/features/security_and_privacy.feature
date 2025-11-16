# =============================================================================
# RiceGuard Security and Privacy BDD Scenarios
# =============================================================================
Feature: Security and Privacy Protection
  As a user of the RiceGuard application
  I want my personal data and agricultural information to be secure
  So that my privacy is protected and my data is safe from unauthorized access

  Background:
    Given the RiceGuard application is running with security features enabled
    And all security middleware is active
    And the database encryption is configured
    And audit logging is enabled

  Scenario: Secure Password Storage
    Given I register a new account with password "RiceGuard2023!"
    When my account is created
    Then my password should be hashed using bcrypt with 12 rounds
    And the plain password should never be stored
    And the password hash should be salted uniquely
    And the hash should be stored securely in the database

  Scenario: JWT Token Security
    Given I successfully login to the application
    Then I should receive a JWT access token
    And the token should be signed with HS256 algorithm
    And the token should have a valid expiration time
    And the token should not contain sensitive data
    And the token should be stored securely (httpOnly cookie)

  Scenario: Session Management
    Given I am logged in with a valid session
    When my session expires after 6 hours
    Then the token should be automatically invalidated
    And I should be required to login again
    And the expired token should be rejected by the server
    And the session timeout should be enforced consistently

  Scenario: Rate Limiting Protection
    Given a malicious user attempts to brute force login
    When they make 100 login attempts in 1 minute
    Then the system should block further attempts after threshold
    And they should receive a 429 Too Many Requests error
    And the rate limit should be per IP address
    And the attack should be logged for security monitoring

  Scenario: Input Validation and Sanitization
    Given I am filling out any form in the application
    When I input malicious content "<script>alert('xss')</script>"
    Then the content should be sanitized or rejected
    And no XSS attacks should be possible
    And database injection should be prevented
    And the input validation should be consistent across all endpoints

  Scenario: File Upload Security
    Given I attempt to upload a malicious file "virus.exe"
    When the system processes the upload
    Then the file should be rejected based on extension
    And only allowed image types should be accepted
    And uploaded files should be scanned for malware
    And file paths should be validated to prevent directory traversal

  Scenario: Secure File Access Control
    Given I have uploaded scan images to my account
    When another user tries to access my images via URL
    Then they should be denied access with 403 error
    And they should not be able to guess file URLs
    And file access should require valid authentication
    And access attempts should be logged

  Scenario: Cross-Origin Resource Sharing (CORS)
    Given the API is configured with CORS
    When an unauthorized domain tries to access the API
    Then the request should be blocked
    And only whitelisted domains should have access
    And CORS headers should be properly configured
    And preflight requests should be handled correctly

  Scenario: Database Connection Security
    Given the application connects to MongoDB
    Then the connection should use TLS encryption
    And authentication should be required
    And connection strings should not be exposed
    And database credentials should be stored securely

  Scenario: Error Handling Without Information Leakage
    When an unexpected error occurs in the system
    Then the error response should not expose stack traces
    And database errors should not reveal schema information
    And system paths should not be exposed
    And generic error messages should be provided to users

  Scenario: HTTPS Enforcement
    Given the application is deployed in production
    Then all API endpoints should require HTTPS
    And HTTP requests should be redirected to HTTPS
    And secure cookies should be used
    And HSTS headers should be configured

  Scenario: Audit Logging
    Given I perform any action in the system
    Then my action should be logged with timestamp
    And my IP address should be recorded
    And the action type should be documented
    And failed authentication attempts should be logged
    And sensitive operations should trigger security alerts

  Scenario: Data Encryption at Rest
    Given sensitive data is stored in the database
    Then personal information should be encrypted
    And scan data should be protected
    And database backups should be encrypted
    And encryption keys should be managed securely

  Scenario: GDPR Compliance - Data Deletion
    Given I request to delete my account
    When the deletion is processed
    Then all my personal data should be removed
    And my scan history should be deleted
    And my uploaded images should be removed
    And I should receive confirmation of deletion
    And the deletion should be irreversible

  Scenario: API Key Security
    Given the application uses third-party APIs
    Then API keys should be stored securely
    And keys should not be exposed in client-side code
    And API calls should be rate limited
    And key rotation should be supported

  Scenario: Environment Variable Security
    Given the application is deployed
    Then sensitive configuration should use environment variables
    And .env files should not be committed to version control
    And production secrets should be different from development
    And default credentials should not be used in production

  Scenario: Session Hijacking Prevention
    Given I am logged into the application
    When I login from a new device or location
    Then existing sessions should be evaluated
    And suspicious activity should trigger re-authentication
    And session tokens should be bound to IP/user agent
    And concurrent sessions should be limited

  Scenario: Dependency Security Scanning
    Given the application has third-party dependencies
    Then dependencies should be regularly scanned for vulnerabilities
    And outdated packages should be updated
    And vulnerable dependencies should be replaced
    And security patches should be applied promptly