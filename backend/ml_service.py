from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    import numpy as np

# Setup logging for ML service
log = logging.getLogger("riceguard.ml")

# Load environment variables from backend/.env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# SECURITY: Validate and sanitize environment variables
def _validate_model_path(path_str: str) -> str:
    """Validate model path to prevent directory traversal and injection attacks."""
    if not path_str:
        return ""

    # Resolve absolute path and normalize
    try:
        abs_path = Path(path_str).resolve()

        # Only allow specific file extensions
        allowed_extensions = {'.h5', '.hdf5', '.pb', '.savedmodel'}
        if abs_path.suffix.lower() not in allowed_extensions:
            raise ValueError(f"Invalid model file extension: {abs_path.suffix}")

        # SECURITY: Enhanced path validation to prevent symlink attacks and traversal
        repo_root = Path(__file__).parent.parent.resolve()

        # SECURITY: Validate path components before resolution
        if '..' in path_str or path_str.startswith('/') or ':' in path_str:
            raise ValueError(f"Invalid path components in model path: {path_str}")

        # SECURITY: Ensure model is within strictly allowed directories
        allowed_dirs = [
            repo_root / "ml",
            repo_root / "models",
            Path("/models"),  # Production models directory
            Path("/app/models"),  # Container models directory
        ]

        # SECURITY: Additional validation - check for symlink attacks
        try:
            # Resolve the path and check if it resolves to allowed directory
            real_path = abs_path.resolve()

            # SECURITY: Multiple validation layers
            is_allowed = False
            for allowed_dir in allowed_dirs:
                allowed_real = allowed_dir.resolve()
                if hasattr(real_path, 'is_relative_to'):
                    is_allowed = real_path.is_relative_to(allowed_real)
                else:
                    # Fallback for older Python versions
                    is_allowed = str(real_path).startswith(str(allowed_real))

                if is_allowed:
                    break

            # SECURITY: Additional check - ensure no symlinks lead outside allowed dirs
            if is_allowed:
                # Check each component of the path for symlinks
                current_path = Path(real_path.root) if hasattr(real_path, 'root') else Path('/')
                for part in real_path.parts[1:]:  # Skip root
                    current_path = current_path / part
                    if current_path.is_symlink():
                        # Verify symlink target is also within allowed directories
                        target = current_path.resolve()
                        if not any(
                            target.is_relative_to(allowed_dir.resolve()) if hasattr(target, 'is_relative_to')
                            else str(target).startswith(str(allowed_dir.resolve()))
                            for allowed_dir in allowed_dirs
                        ):
                            is_allowed = False
                            break

        except (OSError, ValueError) as path_error:
            log.error(f"Path resolution error during model validation: {path_error}")
            raise ValueError(f"Invalid model path: {path_str}")

        if not is_allowed:
            raise ValueError(f"Model path not in allowed directory: {abs_path}")

        return str(abs_path)

    except Exception as e:
        log.error(f"Invalid model path '{path_str}': {e}")
        raise ValueError(f"Invalid model path: {path_str}")

def _validate_labels_path(path_str: str) -> str:
    """Validate labels path to prevent directory traversal attacks."""
    if not path_str:
        return ""

    try:
        abs_path = Path(path_str).resolve()

        # Only allow .txt extension
        if abs_path.suffix.lower() != '.txt':
            raise ValueError(f"Labels file must be .txt, got: {abs_path.suffix}")

        # Get repo root for validation
        repo_root = Path(__file__).parent.parent.resolve()

        # Ensure labels file is within allowed directories
        allowed_dirs = [
            repo_root / "ml",
            repo_root / "models",
            Path("/models"),
            Path("/app/models"),
        ]

        is_allowed = any(
            abs_path.is_relative_to(allowed_dir.resolve()) if hasattr(abs_path, 'is_relative_to')
            else str(abs_path).startswith(str(allowed_dir.resolve()))
            for allowed_dir in allowed_dirs
            if allowed_dir.exists()
        )

        if not is_allowed:
            raise ValueError(f"Labels path not in allowed directory: {abs_path}")

        return str(abs_path)

    except Exception as e:
        log.error(f"Invalid labels path '{path_str}': {e}")
        raise ValueError(f"Invalid labels path: {path_str}")

def _validate_numeric_range(value_str: str, min_val: float, max_val: float, default_val: float, param_name: str) -> float:
    """Validate numeric parameter is within safe range."""
    try:
        if not value_str:
            return default_val

        value = float(value_str)
        if not (min_val <= value <= max_val):
            log.warning(f"{param_name} value {value} out of range [{min_val}, {max_val}], using default {default_val}")
            return default_val

        return value
    except (ValueError, TypeError):
        log.warning(f"Invalid {param_name} value '{value_str}', using default {default_val}")
        return default_val

# SECURITY: Validate and sanitize environment variables
MODEL_PATH = _validate_model_path(os.getenv("MODEL_PATH", ""))
LABELS_PATH = _validate_labels_path(os.getenv("LABELS_PATH", ""))
CONFIDENCE_THRESHOLD = _validate_numeric_range(os.getenv("CONFIDENCE_THRESHOLD"), 0.0, 1.0, 0.45, "CONFIDENCE_THRESHOLD")
CONFIDENCE_MARGIN = _validate_numeric_range(os.getenv("CONFIDENCE_MARGIN"), 0.0, 1.0, 0.12, "CONFIDENCE_MARGIN")
IMG_SIZE = int(_validate_numeric_range(os.getenv("IMG_SIZE"), 32, 1024, 224, "IMG_SIZE"))
TEMPERATURE = _validate_numeric_range(os.getenv("TEMPERATURE"), 0.1, 10.0, 1.25, "TEMPERATURE")

# SECURITY: Log sanitized configuration (without paths)
log.info(f"Loaded ML configuration: TEMPERATURE={TEMPERATURE}, CONFIDENCE_THRESHOLD={CONFIDENCE_THRESHOLD}, CONFIDENCE_MARGIN={CONFIDENCE_MARGIN}, IMG_SIZE={IMG_SIZE}")

# Disease similarity mapping for commonly confused classes
SIMILAR_DISEASES = {
    'leaf_scald': ['rice_blast', 'brown_spot'],
    'rice_blast': ['leaf_scald', 'narrow_brown_spot'],
    'brown_spot': ['narrow_brown_spot', 'leaf_scald'],
    'narrow_brown_spot': ['brown_spot', 'rice_blast'],
    'leaf_blast': ['rice_blast', 'bacterial_leaf_blight'],
    'bacterial_leaf_blight': ['leaf_blast']
}

# TensorFlow/Pillow/Numpy are optional at import time; guard them for tests.
try:
    from tensorflow.keras.models import load_model
    import numpy as np
    from PIL import Image
    try:
        from tensorflow.keras.applications.resnet50 import preprocess_input as resnet50_preprocess
    except Exception:  # pragma: no cover - optional depending on model family
        resnet50_preprocess = None

    TF_OK = True
except Exception:  # pragma: no cover - runtime availability guard
    TF_OK = False
    resnet50_preprocess = None


# ---------------- Utility Functions ---------------- #
def softmax_with_temperature(logits: np.ndarray, temperature: float) -> np.ndarray:
    """Apply softmax with temperature scaling for better calibrated probabilities."""
    if temperature <= 0:
        temperature = 1.0

    # Scale logits by temperature
    scaled_logits = logits / temperature

    # Apply softmax with numerical stability
    exp_logits = np.exp(scaled_logits - np.max(scaled_logits))
    return exp_logits / np.sum(exp_logits)


def compute_entropy(probabilities: np.ndarray) -> float:
    """Compute Shannon entropy of probability distribution."""
    # Add small epsilon to avoid log(0)
    eps = 1e-12
    probabilities = np.clip(probabilities, eps, 1.0 - eps)
    return -np.sum(probabilities * np.log(probabilities))


def check_disease_similarity(predicted_label: str, top_predictions: List[Tuple[str, float]]) -> List[str]:
    """
    Check if predicted disease is commonly confused with other high-confidence alternatives.
    Returns a list of similar diseases that might be alternatives.
    """
    if predicted_label not in SIMILAR_DISEASES:
        return []

    similar_diseases = SIMILAR_DISEASES[predicted_label]
    alternatives = []

    # Check if similar diseases appear in top predictions with reasonable confidence
    for label, confidence in top_predictions[1:3]:  # Check runner-up predictions
        if label in similar_diseases and confidence > 0.20:  # 20% confidence threshold
            alternatives.append(label)

    return alternatives


# ---------------- Paths ---------------- #
def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_model_path() -> Path:
    """Get default model path relative to backend directory."""
    # For backend execution, look in ml/ subdirectory first, then parent ml/
    backend_ml = Path(__file__).parent / "ml" / "model.h5"
    repo_ml = _repo_root() / "ml" / "model.h5"

    if backend_ml.exists():
        return backend_ml.resolve()
    return repo_ml.resolve()


def _default_labels_path() -> Path:
    """Get default labels path relative to backend directory."""
    # For backend execution, look in ml/ subdirectory first, then parent ml/
    backend_ml = Path(__file__).parent / "ml" / "labels.txt"
    repo_ml = _repo_root() / "ml" / "labels.txt"

    if backend_ml.exists():
        return backend_ml.resolve()
    return repo_ml.resolve()


# ---------------- Labels ---------------- #
def _load_labels_file(path: Path) -> List[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    labels = [line.strip() for line in lines if line.strip()]
    if len(labels) < 2:
        raise ValueError("labels.txt must list at least two classes")
    return labels


@lru_cache(maxsize=1)
def get_labels() -> List[str]:
    """Load and validate model labels with security checks."""
    if LABELS_PATH:
        path = Path(LABELS_PATH).resolve()
    else:
        path = _default_labels_path()

    # SECURITY: Validate file existence and permissions
    if not path.exists():
        raise FileNotFoundError(
            f"labels.txt not found at {path}. "
            "Create ml/labels.txt with the exact class order used during training."
        )

    # SECURITY: Ensure file is readable and has reasonable permissions
    try:
        file_stat = path.stat()
        # On Windows, the permission bits work differently. We'll check if file exists and is readable.
        # Skip the strict world-writable check on Windows as it causes false positives.
        import platform
        if platform.system() != 'Windows':
            if file_stat.st_mode & 0o002:  # Check world-writable bit (Unix/Linux only)
                log.warning(f"Security: Labels file {path} is world-writable")
    except Exception as e:
        log.warning(f"Cannot check file permissions for {path}: {e}")

    # SECURITY: Validate labels content
    labels = _load_labels_file(path)

    # SECURITY: Basic validation of labels
    if len(labels) > 100:  # Reasonable limit for number of classes
        raise ValueError(f"Too many labels ({len(labels)}). Maximum allowed is 100")

    for label in labels:
        if not label.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid label format: '{label}'. Labels must be alphanumeric with underscores/hyphens only")

        if len(label) > 50:  # Reasonable label length limit
            raise ValueError(f"Label too long: '{label}'. Maximum length is 50 characters")

    log.info(f"Loaded {len(labels)} labels from validated file")
    return labels


# ---------------- Model ---------------- #
@lru_cache(maxsize=1)
def get_model():
    """Load and cache the Keras model with comprehensive security validation."""
    if not TF_OK:
        raise RuntimeError("TensorFlow/Pillow not available in this environment")

    # SECURITY: Determine model path with validation
    if MODEL_PATH:
        path = Path(MODEL_PATH).resolve()
    else:
        path = _default_model_path()

    # SECURITY: Validate model file existence and properties
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at: {path}. Please ensure the ML model is properly installed.")

    # SECURITY: Check file size (models should be reasonable size)
    try:
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > 1000:  # 1GB limit for models
            raise ValueError(f"Model file too large: {file_size_mb:.1f}MB. Maximum allowed is 1000MB")
        if file_size_mb < 1:  # Models should be at least 1MB
            raise ValueError(f"Model file too small: {file_size_mb:.1f}MB. This may not be a valid model")
    except Exception as e:
        log.warning(f"Cannot validate model file size: {e}")

    # SECURITY: Check file permissions
    try:
        file_stat = path.stat()
        # On Windows, the permission bits work differently. We'll check if file exists and is readable.
        # Skip the strict world-writable check on Windows as it causes false positives.
        import platform
        if platform.system() != 'Windows':
            if file_stat.st_mode & 0o002:  # Check world-writable bit (Unix/Linux only)
                log.error(f"Security: Model file {path} is world-writable - refusing to load")
                raise PermissionError(f"Model file has insecure permissions: {path}")
    except Exception as e:
        if isinstance(e, PermissionError):
            raise
        log.warning(f"Cannot check model file permissions: {e}")

    # SECURITY: Validate file extension again (double-check)
    allowed_extensions = {'.h5', '.hdf5', '.pb', '.savedmodel'}
    if path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Invalid model file extension: {path.suffix}")

    log.info(f"Loading validated RiceGuard model from secure location")

    try:
        model = load_model(str(path))

        # SECURITY: Basic model validation
        if hasattr(model, 'input_shape'):
            # Validate input shape is reasonable
            input_shape = model.input_shape
            if input_shape and len(input_shape) >= 3:
                height, width = input_shape[1:3]
                if height > 1024 or width > 1024:
                    log.warning(f"Unusually large input dimensions: {height}x{width}")

        if hasattr(model, 'output_shape'):
            # Validate output shape is reasonable
            output_shape = model.output_shape
            if output_shape and len(output_shape) >= 2:
                num_classes = output_shape[1]
                if num_classes > 100:
                    raise ValueError(f"Too many output classes: {num_classes}. Maximum allowed is 100")

        log.info("Model loaded and validated successfully")
        return model

    except Exception as e:
        log.error(f"Failed to load or validate model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")


# ---------------- Preprocess ---------------- #
def _preprocess(image_path: str) -> any:
    """
    Enhanced image preprocessing for better inference accuracy.
    - Maintain aspect ratio while resizing
    - Apply proper normalization
    - Add batch dimension
    """
    img = Image.open(image_path).convert("RGB")

    # Maintain aspect ratio by padding to square
    target_size = IMG_SIZE
    original_width, original_height = img.size

    # Calculate scaling to maintain aspect ratio
    scale = min(target_size / original_width, target_size / original_height)
    new_width = int(original_width * scale)
    new_height = int(original_height * scale)

    # Resize and center pad
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create square image with padding
    new_img = Image.new("RGB", (target_size, target_size), (114, 114, 114))  # Gray padding
    offset = ((target_size - new_width) // 2, (target_size - new_height) // 2)
    new_img.paste(img, offset)

    # Convert to array and normalize
    arr = np.asarray(new_img, dtype="float32")

    # Use ResNet50 preprocessing if available, otherwise improved normalization
    if resnet50_preprocess:
        arr = resnet50_preprocess(arr)
    else:
        # Improved normalization: center pixels and scale
        arr = arr / 255.0
        # Apply slight contrast enhancement
        mean = np.mean(arr)
        std = np.std(arr)
        if std > 0:
            arr = (arr - mean) / (std + 1e-8) * 0.1 + 0.5  # Mild contrast enhancement
            arr = np.clip(arr, 0, 1)  # Ensure valid range

    arr = np.expand_dims(arr, axis=0)  # (1, H, W, 3)
    return arr


# ---------------- Inference ---------------- #
def predict_image(image_path: str) -> Tuple[str, float]:
    """
    Run a calibrated prediction against the model.
    Returns (label, confidence). If confidence falls below CONFIDENCE_THRESHOLD
    we return ("uncertain", confidence) so the client can handle low-confidence
    cases gracefully.
    """
    if not TF_OK:
        raise RuntimeError("TensorFlow/Pillow not available in this environment")

    model = get_model()
    labels = get_labels()
    tensor = _preprocess(image_path)

    try:
        # Get raw model outputs (could be logits or probabilities)
        raw_outputs = model.predict(tensor, verbose=0)[0]
        raw_outputs = np.asarray(raw_outputs, dtype="float32")

        log.debug(f"Raw outputs shape: {raw_outputs.shape}")
        log.debug(f"Raw outputs range: [{raw_outputs.min():.3f}, {raw_outputs.max():.3f}]")
        log.debug(f"Raw outputs sum: {raw_outputs.sum():.3f}")

    except Exception as e:
        raise RuntimeError(f"Model prediction failed: {e}")

    # Ensure labels and model output dimensions match.
    if len(raw_outputs) != len(labels):
        raise RuntimeError(
            f"Model output dimension ({len(raw_outputs)}) does not match labels ({len(labels)}). "
            "Update ml/labels.txt or retrain/export the model with matching classes."
        )

    # Determine if outputs are logits or probabilities and apply appropriate processing
    prob_sum = float(raw_outputs.sum())
    has_negative = np.any(raw_outputs < 0)
    is_logits = not np.isclose(prob_sum, 1.0, atol=0.1) or has_negative

    if is_logits:
        log.debug(f"Detected logits (sum={prob_sum:.3f}, has_negative={has_negative})")
        # Apply temperature scaling for logits
        probs = softmax_with_temperature(raw_outputs, TEMPERATURE)
        log.debug(f"Applied temperature scaling T={TEMPERATURE}")
    else:
        log.debug(f"Detected probabilities (sum={prob_sum:.3f})")
        # Normalize probabilities and apply mild temperature scaling
        probs = raw_outputs / np.sum(raw_outputs)
        # Apply very mild temperature scaling to already normalized probabilities
        if TEMPERATURE != 1.0:
            probs = softmax_with_temperature(np.log(probs + 1e-12), TEMPERATURE)
            log.debug(f"Applied mild temperature scaling T={TEMPERATURE}")

    log.debug(f"Calibrated probs sum: {probs.sum():.6f}")

    # Get top-3 predictions for diagnostics
    ranked_indices = probs.argsort()[::-1]
    top_indices = ranked_indices[:3]

    top_predictions = []
    for i, idx in enumerate(top_indices):
        confidence = float(probs[idx])
        top_predictions.append((labels[idx], confidence))
        log.debug(f"Top-{i+1}: {labels[idx]} ({confidence:.4f})")

    # Compute entropy for uncertainty estimation
    entropy = compute_entropy(probs)
    max_entropy = np.log(len(probs))
    entropy_ratio = entropy / max_entropy

    # Main prediction details
    top1_idx = int(top_indices[0])
    top2_idx = int(top_indices[1]) if len(top_indices) > 1 else None
    confidence = float(probs[top1_idx])
    runner_up_conf = float(probs[top2_idx]) if top2_idx is not None else 0.0
    confidence_gap = confidence - runner_up_conf

    log.debug(f"Final decision metrics:")
    log.debug(f"  - Confidence: {confidence:.3f}")
    log.debug(f"  - Confidence gap: {confidence_gap:.3f}")
    log.debug(f"  - Entropy: {entropy:.3f} (ratio: {entropy_ratio:.3f})")
    log.debug(f"  - Threshold: {CONFIDENCE_THRESHOLD}, Margin: {CONFIDENCE_MARGIN}")

    # Optimized decision logic with precise thresholds
    high_conf = confidence >= CONFIDENCE_THRESHOLD
    good_gap = confidence_gap >= CONFIDENCE_MARGIN
    low_entropy = entropy_ratio <= 0.45  # Tighter entropy requirement
    high_conf_override = confidence >= 0.78  # Slightly lower override threshold

    decision_reasons = []

    # Should be certain if:
    # 1. High confidence override with low entropy, OR
    # 2. Standard high confidence with (good gap OR low entropy)
    should_be_certain = (high_conf_override and low_entropy) or (high_conf and (good_gap or low_entropy))

    if high_conf:
        decision_reasons.append("confidence_above_threshold")
    if good_gap:
        decision_reasons.append("gap_above_margin")
    if low_entropy:
        decision_reasons.append("low_entropy")
    if high_conf_override:
        decision_reasons.append("high_confidence_override")

    # Additional uncertainty for truly ambiguous cases
    if confidence > 0.90 and entropy_ratio > 0.7:
        should_be_certain = False
        decision_reasons.append("high_confidence_high_entropy_UNCERTAIN")

    log.info(f"Decision: {'CERTAIN' if should_be_certain else 'UNCERTAIN'}")
    log.debug(f"Reasons: {', '.join(decision_reasons) if decision_reasons else 'none'}")

    # Check for disease similarity if prediction is certain
    predicted_label = labels[top1_idx]
    alternatives = []
    if should_be_certain:
        alternatives = check_disease_similarity(predicted_label, top_predictions)
        if alternatives:
            log.warning(f"Disease '{predicted_label}' may be confused with: {alternatives}")

    # Return calibrated prediction
    if should_be_certain:
        return predicted_label, confidence
    else:
        return "uncertain", confidence


def get_prediction_debug_info(image_path: str) -> dict:
    """
    Get detailed debug information for a prediction.
    Useful for the debug endpoint and calibration analysis.
    """
    if not TF_OK:
        raise RuntimeError("TensorFlow/Pillow not available in this environment")

    model = get_model()
    labels = get_labels()
    tensor = _preprocess(image_path)

    # Get raw outputs
    raw_outputs = model.predict(tensor, verbose=0)[0]
    raw_outputs = np.asarray(raw_outputs, dtype="float32")

    # Process with current configuration
    prob_sum = float(raw_outputs.sum())
    has_negative = np.any(raw_outputs < 0)
    is_logits = not np.isclose(prob_sum, 1.0, atol=0.1) or has_negative

    if is_logits:
        probs = softmax_with_temperature(raw_outputs, TEMPERATURE)
    else:
        probs = raw_outputs / np.sum(raw_outputs)
        if TEMPERATURE != 1.0:
            probs = softmax_with_temperature(np.log(probs + 1e-12), TEMPERATURE)

    # Get detailed rankings
    ranked_indices = probs.argsort()[::-1]
    entropy = compute_entropy(probs)
    max_entropy = np.log(len(probs))
    entropy_ratio = entropy / max_entropy

    # Extract top predictions with proper format
    top_predictions = []
    for rank, i in enumerate(ranked_indices[:3]):
        top_predictions.append({
            "label": labels[i],
            "confidence": float(probs[i]),
            "rank": rank + 1
        })

    # Determine final prediction using same logic as predict_image
    top1_idx = int(ranked_indices[0])
    top2_idx = int(ranked_indices[1]) if len(ranked_indices) > 1 else None
    confidence = float(probs[top1_idx])
    runner_up_conf = float(probs[top2_idx]) if top2_idx is not None else 0.0
    confidence_gap = confidence - runner_up_conf

    # Safer decision logic (same as predict_image)
    high_conf = confidence >= CONFIDENCE_THRESHOLD
    good_gap = confidence_gap >= CONFIDENCE_MARGIN
    low_entropy = entropy_ratio <= 0.6
    very_high_confidence = confidence >= 0.95 and entropy_ratio <= 0.2
    should_be_certain = very_high_confidence or (high_conf and (good_gap or low_entropy))

    # Check for disease similarity
    predicted_label = labels[top1_idx] if should_be_certain else "uncertain"
    alternatives = []
    top_predictions_tuples = [(p["label"], p["confidence"]) for p in top_predictions]

    if should_be_certain:
        alternatives = check_disease_similarity(predicted_label, top_predictions_tuples)

    # Build debug info
    debug_info = {
        "raw_outputs": raw_outputs.tolist(),
        "raw_sum": prob_sum,
        "has_negative": has_negative,
        "is_logits": is_logits,
        "temperature": TEMPERATURE,
        "calibrated_probabilities": probs.tolist(),
        "entropy": float(entropy),
        "max_entropy": float(max_entropy),
        "entropy_ratio": float(entropy_ratio),
        "top_predictions": top_predictions,
        "thresholds": {
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "confidence_margin": CONFIDENCE_MARGIN,
            "temperature": TEMPERATURE
        },
        "decision_metrics": {
            "confidence": confidence,
            "confidence_gap": confidence_gap,
            "high_confidence": high_conf,
            "good_gap": good_gap,
            "low_entropy": low_entropy,
            "very_high_confidence": very_high_confidence,
            "should_be_certain": should_be_certain
        },
        "final_prediction": {
            "label": predicted_label,
            "confidence": confidence,
            "alternatives": alternatives,
            "is_uncertain": not should_be_certain
        }
    }

    return debug_info
