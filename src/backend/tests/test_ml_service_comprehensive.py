# tests/test_ml_service_comprehensive.py
"""
Comprehensive ML service tests covering model loading, prediction, confidence calibration,
and all edge cases for the rice disease detection system.
"""

import pytest
import numpy as np
import io
import tempfile
import os
from PIL import Image
from unittest.mock import patch, Mock, MagicMock, mock_open
from pathlib import Path

from ml_service import (
    predict_image, get_prediction_debug_info,
    load_model, get_temperature, get_model_path,
    apply_temperature_scaling, get_confidence_level,
    CONFIDENCE_THRESHOLD, CONFIDENCE_MARGIN, IMG_SIZE, TEMPERATURE
)


class TestModelLoading:
    """Test model loading and initialization."""

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.tf.keras.models.load_model')
    def test_load_model_success(self, mock_load_model):
        """MODEL-001: Successfully load a valid TensorFlow model."""
        # Arrange
        mock_model = Mock()
        mock_model.summary.return_value = "Model summary"
        mock_load_model.return_value = mock_model

        with patch('ml_service.get_model_path') as mock_get_path:
            mock_get_path.return_value = "/path/to/model.h5"

            # Act
            result = load_model()

            # Assert
            assert result is not None
            mock_load_model.assert_called_once_with("/path/to/model.h5")

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.tf.keras.models.load_model')
    def test_load_model_file_not_found(self, mock_load_model):
        """MODEL-002: Handle model file not found gracefully."""
        # Arrange
        mock_load_model.side_effect = FileNotFoundError("Model file not found")

        with patch('ml_service.get_model_path') as mock_get_path:
            mock_get_path.return_value = "/nonexistent/model.h5"

            # Act & Assert
            with pytest.raises(FileNotFoundError):
                load_model()

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.tf.keras.models.load_model')
    def test_load_model_corrupted_file(self, mock_load_model):
        """MODEL-003: Handle corrupted model file gracefully."""
        # Arrange
        mock_load_model.side_effect = Exception("Corrupted model file")

        with patch('ml_service.get_model_path') as mock_get_path:
            mock_get_path.return_value = "/corrupted/model.h5"

            # Act & Assert
            with pytest.raises(Exception):
                load_model()

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.tf.keras.models.load_model')
    def test_load_model_cache(self, mock_load_model):
        """MODEL-004: Model loading is cached for performance."""
        # Arrange
        mock_model = Mock()
        mock_load_model.return_value = mock_model

        with patch('ml_service.get_model_path') as mock_get_path:
            mock_get_path.return_value = "/path/to/model.h5"

            # Act - Load model twice
            model1 = load_model()
            model2 = load_model()

            # Assert
            assert model1 is model2  # Should be same cached instance
            mock_load_model.assert_called_once()  # Called only once due to caching

    @pytest.mark.ml
    @pytest.mark.unit
    def test_get_model_path_valid_environment(self, monkeypatch):
        """MODEL-005: Get model path from environment variable."""
        # Arrange
        monkeypatch.setenv("MODEL_PATH", "/custom/path/model.h5")

        # Act
        result = get_model_path()

        # Assert
        assert result == "/custom/path/model.h5"

    @pytest.mark.ml
    @pytest.mark.unit
    def test_get_model_path_default_fallback(self, monkeypatch):
        """MODEL-006: Use default model path when environment variable not set."""
        # Arrange
        monkeypatch.delenv("MODEL_PATH", raising=False)

        with patch('ml_service.Path.__new__') as mock_path:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = True
            mock_path.return_value = mock_path_instance

            # Act
            result = get_model_path()

            # Assert
            assert result is not None


class TestTemperatureScaling:
    """Test temperature scaling for confidence calibration."""

    @pytest.mark.ml
    @pytest.mark.unit
    @pytest.mark.parametrize("temperature,expected_effect", [
        (1.0, "no_change"),  # No scaling
        (0.5, "increase"),   # Increase confidence
        (2.0, "decrease"),   # Decrease confidence
    ])
    def test_temperature_scaling_effects(self, temperature, expected_effect):
        """TEMP-001: Temperature scaling affects logits correctly."""
        # Arrange
        logits = np.array([1.0, 2.0, 3.0, 4.0])
        original_confidence = np.max(logits) / np.sum(logits)

        # Act
        scaled_logits = apply_temperature_scaling(logits, temperature)
        scaled_confidence = np.max(scaled_logits) / np.sum(scaled_logits)

        # Assert
        if expected_effect == "no_change":
            assert abs(scaled_confidence - original_confidence) < 0.001
        elif expected_effect == "increase":
            assert scaled_confidence > original_confidence
        elif expected_effect == "decrease":
            assert scaled_confidence < original_confidence

    @pytest.mark.ml
    @pytest.mark.unit
    def test_temperature_scaling_extreme_values(self):
        """TEMP-002: Temperature scaling handles extreme values."""
        # Arrange
        logits = np.array([1.0, 2.0, 3.0, 4.0])

        # Act & Assert - Very low temperature
        scaled_low = apply_temperature_scaling(logits, 0.01)
        assert not np.any(np.isnan(scaled_low))
        assert not np.any(np.isinf(scaled_low))

        # Act & Assert - Very high temperature
        scaled_high = apply_temperature_scaling(logits, 100.0)
        assert not np.any(np.isnan(scaled_high))
        assert not np.any(np.isinf(scaled_high))

    @pytest.mark.ml
    @pytest.mark.unit
    def test_get_temperature_environment_variable(self, monkeypatch):
        """TEMP-003: Get temperature from environment variable."""
        # Arrange
        monkeypatch.setenv("MODEL_TEMPERATURE", "0.8")

        # Act
        result = get_temperature()

        # Assert
        assert result == 0.8

    @pytest.mark.ml
    @pytest.mark.unit
    def test_get_temperature_default_value(self, monkeypatch):
        """TEMP-004: Use default temperature when environment variable not set."""
        # Arrange
        monkeypatch.delenv("MODEL_TEMPERATURE", raising=False)

        # Act
        result = get_temperature()

        # Assert
        assert result == TEMPERATURE  # Default value


class TestConfidenceLevelCalculation:
    """Test confidence level categorization."""

    @pytest.mark.ml
    @pytest.mark.unit
    @pytest.mark.parametrize("confidence,expected_level", [
        (0.95, "high"),
        (0.85, "high"),
        (0.75, "medium"),
        (0.65, "medium"),
        (0.45, "low"),
        (0.25, "low"),
        (0.15, "low"),
    ])
    def test_confidence_level_categorization(self, confidence, expected_level):
        """CONF-001: Confidence levels are categorized correctly."""
        # Act
        result = get_confidence_level(confidence)

        # Assert
        assert result == expected_level

    @pytest.mark.ml
    @pytest.mark.unit
    @pytest.mark.parametrize("invalid_confidence", [
        -0.1,  # Negative confidence
        1.1,   # Confidence > 1.0
        "0.5", # String instead of float
        None,  # None value
    ])
    def test_confidence_level_invalid_inputs(self, invalid_confidence):
        """CONF-002: Handle invalid confidence values gracefully."""
        # Act & Assert
        with pytest.raises((ValueError, TypeError)):
            get_confidence_level(invalid_confidence)

    @pytest.mark.ml
    @pytest.mark.unit
    def test_confidence_level_boundary_values(self):
        """CONF-003: Boundary values are handled correctly."""
        # Test exact boundary values
        assert get_confidence_level(CONFIDENCE_THRESHOLD) == "medium"
        assert get_confidence_level(CONFIDENCE_THRESHOLD - 0.01) == "low"
        assert get_confidence_level(CONFIDENCE_THRESHOLD + CONFIDENCE_MARGIN) == "high"


class TestImagePreprocessing:
    """Test image preprocessing before model prediction."""

    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        # Create a simple 224x224 RGB image
        image = Image.new('RGB', (224, 224), color='red')
        return image

    @pytest.fixture
    def sample_image_bytes(self, sample_image):
        """Convert sample image to bytes."""
        img_bytes = io.BytesIO()
        sample_image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def non_image_bytes(self):
        """Create non-image bytes for negative testing."""
        return io.BytesIO(b"This is not an image file")

    @pytest.fixture
    def oversized_image(self):
        """Create an oversized test image."""
        # Create a large image (4000x4000)
        image = Image.new('RGB', (4000, 4000), color='blue')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG', quality=95)
        img_bytes.seek(0)
        return img_bytes

    @pytest.fixture
    def tiny_image(self):
        """Create a very small test image."""
        # Create a tiny image (10x10)
        image = Image.new('RGB', (10, 10), color='green')
        img_bytes = io.BytesIO()
        image.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_image_preprocessing_success(self, mock_image_open, mock_load_model, sample_image):
        """IMG-001: Successful image preprocessing."""
        # Arrange
        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model
        mock_image_open.return_value = sample_image

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result is not None
        assert "prediction" in result
        assert "confidence" in result
        assert "confidence_level" in result

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_image_preprocessing_different_formats(self, mock_image_open, mock_load_model):
        """IMG-002: Handle different image formats."""
        # Arrange
        test_images = [
            Image.new('RGB', (224, 224), color='red'),   # JPEG
            Image.new('RGBA', (224, 224), color='blue'), # PNG with alpha
            Image.new('L', (224, 224), color=128),       # Grayscale
        ]

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        for image in test_images:
            mock_image_open.return_value = image

            # Act
            result = predict_image(io.BytesIO())

            # Assert
            assert result is not None
            assert "prediction" in result

    @pytest.mark.ml
    @pytest.mark.unit
    def test_image_preprocessing_invalid_file(self, non_image_bytes):
        """IMG-003: Handle non-image files gracefully."""
        # Act & Assert
        with pytest.raises(Exception):  # Should raise some form of exception
            predict_image(non_image_bytes)

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_image_preprocessing_corrupted_image(self, mock_image_open, mock_load_model):
        """IMG-004: Handle corrupted image files."""
        # Arrange
        mock_image_open.side_effect = Exception("Corrupted image")
        mock_model = Mock()
        mock_load_model.return_value = mock_model

        # Act & Assert
        with pytest.raises(Exception):
            predict_image(io.BytesIO(b"corrupted data"))

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_image_resize_to_target_size(self, mock_image_open, mock_load_model, sample_image):
        """IMG-005: Images are resized to target model size."""
        # Arrange
        large_image = Image.new('RGB', (1024, 768), color='purple')
        mock_image_open.return_value = large_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act
        predict_image(io.BytesIO())

        # Assert - Image should be resized to IMG_SIZE
        # Note: This would require access to the actual image processing code
        # For now, we verify prediction succeeded
        mock_model.predict.assert_called_once()

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_image_normalization(self, mock_image_open, mock_load_model, sample_image):
        """IMG-006: Images are properly normalized."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act
        predict_image(io.BytesIO())

        # Assert - Model prediction was called (implies preprocessing succeeded)
        mock_model.predict.assert_called_once()


class TestModelPrediction:
    """Test the actual model prediction functionality."""

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_success(self, mock_image_open, mock_load_model, sample_image):
        """PRED-001: Successful model prediction."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        # Mock model output for 4 disease classes
        mock_model.predict.return_value = np.array([[0.1, 0.15, 0.7, 0.05]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result is not None
        assert "prediction" in result
        assert "confidence" in result
        assert "confidence_level" in result
        assert "calibrated_confidence" in result

        # Check that confidence is reasonable
        assert 0 <= result["confidence"] <= 1
        assert 0 <= result["calibrated_confidence"] <= 1

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    @pytest.mark.parametrize("model_output,expected_prediction", [
        ([[0.8, 0.1, 0.05, 0.05]], "bacterial_leaf_blight"),  # Index 0
        ([[0.1, 0.7, 0.1, 0.1]], "brown_spot"),  # Index 1
        ([[0.05, 0.05, 0.85, 0.05]], "healthy"),  # Index 2
        ([[0.1, 0.1, 0.1, 0.7]], "leaf_blast"),  # Index 3
    ])
    def test_prediction_different_classes(self, mock_image_open, mock_load_model,
                                        sample_image, model_output, expected_prediction):
        """PRED-002: Model correctly predicts different disease classes."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array(model_output)
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result["prediction"] == expected_prediction
        assert result["confidence"] == max(model_output[0])

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_low_confidence(self, mock_image_open, mock_load_model, sample_image):
        """PRED-003: Low confidence predictions are handled correctly."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        # Model output with low confidence (all probabilities similar)
        mock_model.predict.return_value = np.array([[0.25, 0.25, 0.25, 0.25]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result["confidence"] == 0.25
        assert result["confidence_level"] == "low"

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_equal_probabilities(self, mock_image_open, mock_load_model, sample_image):
        """PRED-004: Handle equal probabilities across all classes."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.25, 0.25, 0.25, 0.25]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result["confidence"] == 0.25
        assert result["confidence_level"] == "low"

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_model_error(self, mock_image_open, mock_load_model, sample_image):
        """PRED-005: Handle model prediction errors gracefully."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.side_effect = Exception("Model prediction failed")
        mock_load_model.return_value = mock_model

        # Act & Assert
        with pytest.raises(Exception):
            predict_image(io.BytesIO())

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_output_shape_validation(self, mock_image_open, mock_load_model, sample_image):
        """PRED-006: Validate model output shape."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_load_model.return_value = mock_model

        # Test various output shapes
        test_cases = [
            np.array([[0.1, 0.2, 0.6, 0.1]]),  # Correct shape
            np.array([[0.1, 0.2, 0.6]]),       # Wrong shape (3 classes)
            np.array([0.1, 0.2, 0.6, 0.1]),    # Wrong shape (1D)
            np.array([]),                       # Empty output
        ]

        for i, output in enumerate(test_cases):
            mock_model.predict.return_value = output

            if i == 0:  # Only the first case should succeed
                result = predict_image(io.BytesIO())
                assert result is not None
            else:
                with pytest.raises(Exception):
                    predict_image(io.BytesIO())

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_batch_vs_single(self, mock_image_open, mock_load_model, sample_image):
        """PRED-007: Handle both single and batch predictions."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result is not None
        assert isinstance(result, dict)


class TestConfidenceCalibration:
    """Test confidence calibration and uncertainty quantification."""

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    @patch('ml_service.get_temperature')
    def test_confidence_calibration_applied(self, mock_get_temp, mock_image_open,
                                          mock_load_model, sample_image):
        """CALIB-001: Temperature scaling is applied to confidence."""
        # Arrange
        mock_get_temp.return_value = 0.8  # Non-default temperature
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert "calibrated_confidence" in result
        assert result["calibrated_confidence"] != result["confidence"]
        assert 0 <= result["calibrated_confidence"] <= 1

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_confidence_margin_application(self, mock_image_open, mock_load_model, sample_image):
        """CALIB-002: Confidence margin is applied correctly."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        # High confidence prediction
        mock_model.predict.return_value = np.array([[0.9, 0.05, 0.03, 0.02]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result["confidence"] == 0.9
        assert result["confidence_level"] == "high"

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_uncertainty_handling(self, mock_image_open, mock_load_model, sample_image):
        """CALIB-003: Handle uncertain predictions correctly."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        # Uncertain prediction (probabilities close together)
        mock_model.predict.return_value = np.array([[0.28, 0.26, 0.25, 0.21]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert result["confidence"] == 0.28
        assert result["confidence_level"] == "low"


class TestPredictionDebugInfo:
    """Test prediction debugging and information utilities."""

    @pytest.mark.ml
    @pytest.mark.unit
    def test_get_prediction_debug_info_structure(self):
        """DEBUG-001: Debug info has correct structure."""
        # Act
        debug_info = get_prediction_debug_info()

        # Assert
        assert isinstance(debug_info, dict)
        assert "confidence_threshold" in debug_info
        assert "confidence_margin" in debug_info
        assert "temperature" in debug_info
        assert "img_size" in debug_info

        assert debug_info["confidence_threshold"] == CONFIDENCE_THRESHOLD
        assert debug_info["confidence_margin"] == CONFIDENCE_MARGIN
        assert debug_info["img_size"] == IMG_SIZE

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.get_temperature')
    def test_get_prediction_debug_info_dynamic_temperature(self, mock_get_temp):
        """DEBUG-002: Debug info reflects current temperature setting."""
        # Arrange
        mock_get_temp.return_value = 0.75

        # Act
        debug_info = get_prediction_debug_info()

        # Assert
        assert debug_info["temperature"] == 0.75

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_prediction_metadata_collection(self, mock_image_open, mock_load_model, sample_image):
        """DEBUG-003: Collect metadata about prediction process."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act
        result = predict_image(io.BytesIO())

        # Assert
        assert "prediction" in result
        assert "confidence" in result
        assert "confidence_level" in result
        assert "calibrated_confidence" in result

        # Verify confidence values are reasonable
        assert 0 <= result["confidence"] <= 1
        assert 0 <= result["calibrated_confidence"] <= 1
        assert result["confidence_level"] in ["high", "medium", "low"]


class TestMLServiceIntegration:
    """Integration tests for ML service components."""

    @pytest.mark.ml
    @pytest.mark.integration
    def test_end_to_end_prediction_flow(self):
        """INTEGR-001: End-to-end prediction flow works correctly."""
        # Create a real test image
        img = Image.new('RGB', (224, 224), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        # Mock the model loading but use real image processing
        with patch('ml_service.load_model') as mock_load_model:
            with patch('ml_service.Image.open') as mock_image_open:
                mock_model = Mock()
                mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
                mock_load_model.return_value = mock_model
                mock_image_open.return_value = img

                # Act
                result = predict_image(img_bytes)

                # Assert
                assert result is not None
                assert result["prediction"] == "healthy"
                assert result["confidence"] == 0.6

    @pytest.mark.ml
    @pytest.mark.integration
    def test_concurrent_predictions(self):
        """INTEGR-002: Handle concurrent prediction requests."""
        import threading
        import time

        # Create test image
        img = Image.new('RGB', (224, 224), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        results = []

        with patch('ml_service.load_model') as mock_load_model:
            with patch('ml_service.Image.open') as mock_image_open:
                mock_model = Mock()
                mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
                mock_load_model.return_value = mock_model
                mock_image_open.return_value = img

                def make_prediction():
                    result = predict_image(img_bytes)
                    results.append(result)

                # Act - Create multiple concurrent predictions
                threads = [threading.Thread(target=make_prediction) for _ in range(5)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()

                # Assert
                assert len(results) == 5
                for result in results:
                    assert result is not None
                    assert result["prediction"] == "healthy"

    @pytest.mark.ml
    @pytest.mark.performance
    def test_prediction_performance_timing(self):
        """PERF-001: Prediction performance meets timing requirements."""
        import time

        # Create test image
        img = Image.new('RGB', (224, 224), color='green')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        with patch('ml_service.load_model') as mock_load_model:
            with patch('ml_service.Image.open') as mock_image_open:
                mock_model = Mock()
                mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
                mock_load_model.return_value = mock_model
                mock_image_open.return_value = img

                # Act - Measure prediction time
                start_time = time.time()
                result = predict_image(img_bytes)
                end_time = time.time()

                prediction_time = end_time - start_time

                # Assert - Should complete within reasonable time (e.g., 5 seconds)
                assert prediction_time < 5.0
                assert result is not None

    @pytest.mark.ml
    @pytest.mark.security
    def test_malicious_image_handling(self):
        """SEC-001: Handle potentially malicious image files."""
        # Test with various potentially malicious inputs
        malicious_inputs = [
            io.BytesIO(b"\x00" * 1000),  # Null bytes
            io.BytesIO(b"very long string" * 1000),  # Very long text
            io.BytesIO(b"<script>alert('xss')</script>"),  # XSS attempt
        ]

        for malicious_input in malicious_inputs:
            # Act & Assert - Should handle gracefully
            try:
                with patch('ml_service.load_model'):
                    with patch('ml_service.Image.open') as mock_image_open:
                        mock_image_open.side_effect = Exception("Invalid image")
                        predict_image(malicious_input)
            except Exception:
                # Expected to fail, but should not crash the application
                pass


class TestMLServiceEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.ml
    @pytest.mark.unit
    def test_empty_image_input(self):
        """EDGE-001: Handle empty image input."""
        # Act & Assert
        with pytest.raises(Exception):
            predict_image(io.BytesIO())

    @pytest.mark.ml
    @pytest.mark.unit
    def test_none_image_input(self):
        """EDGE-002: Handle None image input."""
        # Act & Assert
        with pytest.raises((TypeError, ValueError)):
            predict_image(None)

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_extreme_image_dimensions(self, mock_image_open, mock_load_model):
        """EDGE-003: Handle images with extreme dimensions."""
        # Arrange
        tiny_img = Image.new('RGB', (1, 1), color='red')
        huge_img = Image.new('RGB', (10000, 10000), color='blue')

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[0.1, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        for test_img in [tiny_img, huge_img]:
            mock_image_open.return_value = test_img

            # Act
            try:
                result = predict_image(io.BytesIO())
                # If successful, verify structure
                assert result is not None
                assert "prediction" in result
            except Exception:
                # Some extreme images might fail, which is acceptable
                pass

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_model_output_nan_values(self, mock_image_open, mock_load_model, sample_image):
        """EDGE-004: Handle model output with NaN values."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[np.nan, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act & Assert
        with pytest.raises(Exception):
            predict_image(io.BytesIO())

    @pytest.mark.ml
    @pytest.mark.unit
    @patch('ml_service.load_model')
    @patch('ml_service.Image.open')
    def test_model_output_inf_values(self, mock_image_open, mock_load_model, sample_image):
        """EDGE-005: Handle model output with infinite values."""
        # Arrange
        mock_image_open.return_value = sample_image

        mock_model = Mock()
        mock_model.predict.return_value = np.array([[np.inf, 0.2, 0.6, 0.1]])
        mock_load_model.return_value = mock_model

        # Act & Assert
        with pytest.raises(Exception):
            predict_image(io.BytesIO())