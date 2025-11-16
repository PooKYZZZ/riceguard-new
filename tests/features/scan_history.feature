# =============================================================================
# RiceGuard Scan History Management BDD Scenarios
# =============================================================================
Feature: Scan History Management
  As a rice farmer
  I want to view and manage my disease detection history
  So that I can track disease patterns and treatment effectiveness

  Background:
    Given the RiceGuard application is running
    And I am successfully authenticated
    And I have performed multiple disease scans
    And my scan history contains various disease types

  Scenario: View Complete Scan History
    Given I have performed 15 scans in the past month
    When I navigate to the history page
    Then I should see all my 15 scans displayed
    And each scan should show date, disease type, and confidence
    And the scans should be ordered by most recent first
    And I should see pagination controls for large history sets

  Scenario: Filter History by Disease Type
    Given I have scans with different diseases: "bacterial_leaf_blight", "leaf_blast", "healthy"
    When I apply a filter for "bacterial_leaf_blight"
    Then I should only see scans detected as "bacterial_leaf_blight"
    And the filter should be clearly indicated
    And I should be able to clear the filter

  Scenario: Search Scan History by Date Range
    Given I have scans from the past 6 months
    When I specify a date range from "2024-01-01" to "2024-01-31"
    Then I should only see scans within January 2024
    And the date filter should be reflected in the UI
    And the total count should match filtered results

  Scenario: View Individual Scan Details
    Given I am viewing my scan history
    And I click on a specific scan from "2024-01-15"
    Then I should see the original uploaded image
    And I should see the disease prediction details
    And I should see the confidence score
    And I should see any notes I added during scanning
    And I should see treatment recommendations

  Scenario: Delete Single Scan
    Given I am viewing my scan history
    And I select a scan to delete
    When I confirm the deletion
    Then the scan should be removed from my history
    And the associated image file should be deleted
    And I should see a confirmation message
    And the scan count should decrease

  Scenario: Delete Multiple Scans
    Given I have selected 5 scans to delete
    When I confirm the bulk deletion
    Then all 5 scans should be removed from my history
    And all associated image files should be deleted
    And I should see a confirmation message with count
    And my storage quota should be updated

  Scenario: Export Scan History
    Given I want to export my scan data for analysis
    When I click the export button
    Then I should be able to choose export format (CSV, PDF)
    And I should receive a file with all my scan data
    And the export should include dates, diseases, confidence scores
    And the export should include my notes and images if requested

  Scenario: Sort Scan History
    Given I am viewing my scan history with multiple scans
    When I sort by confidence score (high to low)
    Then scans should be ordered by confidence descending
    When I sort by date (oldest first)
    Then scans should be ordered by date ascending
    And the current sort should be clearly indicated

  Scenario: View Disease Statistics
    Given I have 50 scans in my history
    When I view the statistics dashboard
    Then I should see a chart of disease frequency
    And I should see confidence score distribution
    And I should see scan count by month
    And I should see improvement trends over time

  Scenario: Add Notes to Existing Scan
    Given I am viewing details of a previous scan
    When I add a note "Applied copper fungicide, results in 5 days"
    And I save the note
    Then the note should be saved with the scan
    And I should see the updated note immediately
    And the note timestamp should be recorded

  Scenario: Share Scan Results
    Given I have a successful disease detection scan
    When I click the share button
    Then I should be able to share via email or messaging
    And the shared content should include disease info
    And the shared content should include treatment recommendations
    And the shared content should not include sensitive personal data

  Scenario: Offline History Access
    Given I have poor internet connectivity
    And I am using the mobile app
    When I navigate to my scan history
    Then I should see previously loaded scans
    And I should see an indicator for offline mode
    And I should be able to view cached scan details
    And new scans should sync when connectivity is restored

  Scenario: Large History Performance
    Given I have over 1000 scans in my history
    When I navigate to the history page
    Then the page should load within 3 seconds
    And scrolling should remain smooth
    And pagination should work efficiently
    And filters should apply quickly

  Scenario: Cross-Platform History Synchronization
    Given I add a new scan using the mobile app
    When I check my history on the web application
    Then the new scan should appear immediately
    And the scan details should be identical across platforms
    And the timestamps should be consistent

  Scenario: History Data Integrity
    Given I have been using the application for 6 months
    When I review my complete scan history
    Then no scans should be missing
    And no data should be corrupted
    And image links should be valid
    And all timestamps should be chronological