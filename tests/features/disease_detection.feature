# =============================================================================
# RiceGuard Disease Detection BDD Scenarios
# =============================================================================
Feature: Rice Leaf Disease Detection
  As a rice farmer
  I want to upload images of rice leaves for disease analysis
  So that I can quickly identify and treat plant diseases

  Background:
    Given the RiceGuard application is running
    And I am successfully authenticated
    And the ML model is loaded and ready
    And the image upload system is functional

  Scenario: Successful Disease Detection - High Confidence
    Given I am on the scan page
    And I have a clear image of a diseased rice leaf
    When I upload the image "bacterial_leaf_blight_sample.jpg"
    And the image processing completes
    Then the system should detect "bacterial_leaf_blight" with confidence > 0.80
    And I should see the disease prediction results
    And I should receive treatment recommendations
    And the scan should be saved to my history

  Scenario: Disease Detection with Low Confidence
    Given I am on the scan page
    And I have a blurry or poor quality rice leaf image
    When I upload the image "uncertain_sample.jpg"
    And the image processing completes
    Then the system should return "uncertain" with confidence < 0.45
    And I should see a message about low confidence detection
    And I should be prompted to upload a clearer image
    And the scan should still be saved to my history

  Scenario: Disease Detection with Similar Diseases
    Given I am on the scan page
    And I have an image of rice leaf blast
    When I upload the image "leaf_blast_sample.jpg"
    And the image processing completes
    Then the system should detect "leaf_blast" as primary prediction
    And I should see alternative disease suggestions
    And I should see confidence scores for similar diseases
    And recommendations should address both possible diseases

  Scenario: Upload Invalid File Type
    Given I am on the scan page
    When I try to upload a file "document.pdf" (non-image)
    Then I should see an error message "Invalid file type"
    And the upload should be rejected
    And no scan should be created

  Scenario: Upload Oversized Image
    Given I am on the scan page
    When I try to upload an image larger than 8MB
    Then I should see an error message about file size limit
    And the upload should be rejected
    And no scan should be created

  Scenario: Upload Corrupted Image
    Given I am on the scan page
    When I try to upload a corrupted image file
    Then the system should detect the corruption
    And I should see an error message "Invalid or corrupted image"
    And no scan should be created

  Scenario: Successful Healthy Plant Detection
    Given I am on the scan page
    And I have a clear image of a healthy rice leaf
    When I upload the image "healthy_leaf_sample.jpg"
    And the image processing completes
    Then the system should detect "healthy" with high confidence > 0.85
    And I should see a confirmation that the plant is healthy
    And I should receive general plant care tips

  Scenario: Batch Disease Detection
    Given I am on the scan page
    And I have multiple rice leaf images to analyze
    When I upload 5 images in sequence
    Then each image should be processed independently
    And I should receive individual results for each image
    And all scans should be saved to my history
    And the processing should complete within reasonable time

  Scenario: Model Failure Handling
    Given the ML model encounters an error during processing
    When I upload an image for analysis
    Then the system should handle the error gracefully
    And I should see a user-friendly error message
    And the technical error should be logged
    And I should be able to try again

  Scenario: Cross-Platform Detection Consistency
    Given I upload an image through the web application
    And the system detects "bacterial_leaf_blight" with 0.87 confidence
    When I upload the same image through the mobile app
    Then I should receive the same disease detection
    And the confidence score should be identical
    And the processing time should be similar

  Scenario: Offline Detection Capability
    Given I have a poor internet connection
    And I am using the mobile app
    When I upload an image for analysis
    Then the app should attempt processing with available connectivity
    If connectivity fails:
      Then the app should store the image locally
      And I should see a message about offline processing
      And the image should be processed when connectivity is restored

  Scenario: Real-time Processing Feedback
    Given I am uploading a large image file
    When the upload begins
    Then I should see a progress indicator
    And I should see processing status updates
    And the UI should remain responsive
    And I should be able to cancel the operation if needed

  Scenario: Disease Detection with Annotations
    Given I am on the scan page
    And I upload an image of a diseased rice leaf
    When I add notes "Found in paddy field sector 3 after heavy rainfall"
    And the processing completes
    Then the system should detect the disease
    And my notes should be saved with the scan
    And I should be able to view my notes in the history

  Scenario: Confidence Calibration Validation
    Given I am testing system accuracy
    When I upload 100 validated test images
    Then the system's confidence scores should be well-calibrated
    And high confidence predictions (>0.80) should be >95% accurate
    And low confidence predictions (<0.50) should be marked as uncertain
    And the overall accuracy should meet quality standards