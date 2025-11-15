#!/usr/bin/env python3
"""
Temperature Calibration Script for RiceGuard ML Model

This script calibrates the model's confidence using temperature scaling.
It finds the optimal temperature T that minimizes negative log-likelihood
on a validation set of predictions and calculates Expected Calibration Error (ECE).

Usage:
    python backend/temperature_calibrate.py --data-dir ml/val_images/
    python backend/temperature_calibrate.py --logits-file ml/val_logits.npy --apply
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent))
from ml_service import get_model, get_labels, _preprocess, IMG_SIZE

# Setup logging
log = logging.getLogger("temperature_calibrate")
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def softmax(x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    """Apply softmax with temperature scaling."""
    x_scaled = x / temperature
    exp_x = np.exp(x_scaled - np.max(x_scaled))
    return exp_x / np.sum(exp_x)


def nll_loss(probs: np.ndarray, true_labels: np.ndarray) -> float:
    """Calculate negative log-likelihood loss."""
    # Avoid log(0) by clipping
    eps = 1e-12
    probs = np.clip(probs, eps, 1.0 - eps)

    # Calculate NLL for each sample
    nll = -np.log(probs[np.arange(len(true_labels)), true_labels])
    return np.mean(nll)


def expected_calibration_error(probs: np.ndarray, true_labels: np.ndarray, n_bins: int = 10) -> float:
    """Calculate Expected Calibration Error (ECE)."""
    # Get confidence (max probability) and predictions
    confidences = np.max(probs, axis=1)
    predictions = np.argmax(probs, axis=1)
    accuracies = (predictions == true_labels).astype(float)

    # Create bins
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find samples in this bin
        in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
        prop_in_bin = in_bin.mean()

        if prop_in_bin > 0:
            # Calculate accuracy and confidence in this bin
            accuracy_in_bin = accuracies[in_bin].mean()
            avg_confidence_in_bin = confidences[in_bin].mean()

            # Add weighted contribution to ECE
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return ece


def collect_logits_from_images(image_dir: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Collect model logits from validation images."""
    log.info(f"Collecting logits from images in {image_dir}...")

    model = get_model()
    labels = get_labels()
    all_logits = []
    all_labels = []

    # Map folder names to label indices
    label_to_idx = {label: idx for idx, label in enumerate(labels)}

    image_files = []
    for label_dir in image_dir.iterdir():
        if not label_dir.is_dir():
            continue

        label_name = label_dir.name.lower().replace(' ', '_').replace('-', '_')
        if label_name not in label_to_idx:
            log.warning(f"Label '{label_name}' not found in model labels. Skipping.")
            continue

        label_idx = label_to_idx[label_name]

        for img_file in label_dir.glob('*.*'):
            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                image_files.append((img_file, label_idx))

    if not image_files:
        raise ValueError(f"No valid images found in {image_dir}")

    log.info(f"Found {len(image_files)} validation images")

    for img_path, label_idx in image_files:
        try:
            # Preprocess and get logits
            tensor = _preprocess(str(img_path))
            logits = model.predict(tensor, verbose=0)[0]  # Raw logits

            all_logits.append(logits)
            all_labels.append(label_idx)

            if len(all_logits) % 10 == 0:
                log.info(f"Processed {len(all_logits)} images...")

        except Exception as e:
            log.error(f"Error processing {img_path}: {e}")
            continue

    if not all_logits:
        raise ValueError("No valid logits collected")

    return np.array(all_logits), np.array(all_labels)


def load_saved_logits(logits_file: Path, labels_file: Optional[Path] = None) -> Tuple[np.ndarray, np.ndarray]:
    """Load pre-saved logits from file."""
    if not logits_file.exists():
        raise FileNotFoundError(f"Logits file not found: {logits_file}")

    # If only logits file provided, try to find corresponding labels file
    if labels_file is None:
        labels_file = logits_file.parent / logits_file.name.replace('_logits', '_labels')

    if not labels_file.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_file}")

    log.info(f"Loading saved logits from {logits_file}")
    logits = np.load(logits_file)
    labels = np.load(labels_file)

    return logits, labels


def find_optimal_temperature(logits: np.ndarray, true_labels: np.ndarray) -> Tuple[float, float, float]:
    """Find optimal temperature using grid search and optimization. Returns (temp, ece_before, ece_after)."""
    log.info("Finding optimal temperature...")

    # Calculate ECE before calibration (temperature=1.0)
    probs_before = np.array([softmax(logits[i], 1.0) for i in range(len(logits))])
    ece_before = expected_calibration_error(probs_before, true_labels)
    log.info(f"ECE before calibration: {ece_before:.4f}")

    # Grid search first with tighter range for better calibration
    temperatures = np.linspace(0.05, 3.0, 60)  # More focused range
    best_temp = 1.0
    best_nll = float('inf')

    for temp in temperatures:
        probs = np.array([softmax(logits[i], temp) for i in range(len(logits))])
        nll = nll_loss(probs, true_labels)

        if nll < best_nll:
            best_nll = nll
            best_temp = temp

    log.info(f"Grid search best temperature: {best_temp:.3f} (NLL: {best_nll:.4f})")

    # Fine-tune with SciPy if available
    try:
        from scipy.optimize import minimize_scalar

        def objective(temp):
            probs = np.array([softmax(logits[i], temp) for i in range(len(logits))])
            return nll_loss(probs, true_labels)

        result = minimize_scalar(objective, bounds=(0.05, 3.0), method='bounded')
        if result.success and result.fun < best_nll:
            best_temp = result.x
            best_nll = result.fun
            log.info(f"SciPy optimized temperature: {best_temp:.3f} (NLL: {best_nll:.4f})")
    except ImportError:
        log.info("SciPy not available, using grid search result")

    # Calculate ECE after calibration
    probs_after = np.array([softmax(logits[i], best_temp) for i in range(len(logits))])
    ece_after = expected_calibration_error(probs_after, true_labels)
    log.info(f"ECE after calibration: {ece_after:.4f}")

    improvement = ece_before - ece_after
    if improvement > 0:
        log.info(f"ECE improvement: {improvement:.4f} ({improvement/ece_before*100:.1f}% reduction)")
    else:
        log.warning(f"ECE worsened by: {abs(improvement):.4f}")

    return best_temp, ece_before, ece_after


def save_calibration_results(temperature: float, ece_before: float, ece_after: float, output_file: Path):
    """Save calibration results to file."""
    results = {
        "temperature": float(temperature),
        "ece_before": float(ece_before),
        "ece_after": float(ece_after),
        "ece_improvement": float(ece_before - ece_after),
        "calibration_date": str(Path().absolute()),
        "instructions": "Add TEMPERATURE=<value> to your .env file",
        "recommended_env_update": f"TEMPERATURE={temperature:.3f}"
    }

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    log.info(f"Calibration results saved to {output_file}")


def update_env_file(temperature: float, env_file: Path = Path('.env'), create_backup: bool = True):
    """Update temperature in .env file with backup."""
    if env_file.exists():
        if create_backup:
            backup_file = env_file.with_suffix('.env.bak')
            env_file.rename(backup_file)
            log.info(f"Created backup: {backup_file}")
            # Restore the original for editing
            backup_file.rename(env_file)

        env_content = env_file.read_text()
        lines = env_content.split('\n')
        updated = False

        for i, line in enumerate(lines):
            if line.startswith('TEMPERATURE='):
                lines[i] = f'TEMPERATURE={temperature:.3f}'
                updated = True
                log.info(f"Updated existing TEMPERATURE setting")
                break

        if not updated:
            lines.append(f'TEMPERATURE={temperature:.3f}')
            log.info(f"Added new TEMPERATURE setting")

        env_content = '\n'.join(lines)
        env_file.write_text(env_content)
        log.info(f"Updated TEMPERATURE in {env_file} to {temperature:.3f}")
    else:
        log.warning(f"Environment file {env_file} not found")


def main():
    parser = argparse.ArgumentParser(description="Calibrate model temperature")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--data-dir', type=Path, help='Directory with validation images')
    group.add_argument('--logits-file', type=Path, help='File with saved logits (.npy)')
    group.add_argument('--create-sample', action='store_true',
                      help='Create sample validation set structure')

    parser.add_argument('--labels-file', type=Path, help='Labels file corresponding to logits file')
    parser.add_argument('--output', type=Path, default='.env.calibrated',
                       help='Output file for calibration results (default: .env.calibrated)')
    parser.add_argument('--apply', action='store_true',
                       help='Apply the calibration by updating the .env file')
    parser.add_argument('--env-file', type=Path, default=Path('.env'),
                       help='Environment file to update (default: .env)')

    args = parser.parse_args()

    if args.create_sample:
        # Create sample directory structure
        sample_dir = Path('../ml/val_images')  # Go up from backend to root
        sample_dir.mkdir(exist_ok=True, parents=True)

        labels = get_labels()
        for label in labels:
            (sample_dir / label).mkdir(exist_ok=True)

        print(f"Created sample validation directory structure: {sample_dir}")
        print("Please add validation images to subdirectories and re-run this script")
        return

    try:
        # Collect validation data
        if args.data_dir:
            logits, true_labels = collect_logits_from_images(args.data_dir)
        else:
            logits, true_labels = load_saved_logits(args.logits_file, args.labels_file)

        # Find optimal temperature with ECE calculation
        optimal_temp, ece_before, ece_after = find_optimal_temperature(logits, true_labels)

        # Save results
        save_calibration_results(optimal_temp, ece_before, ece_after, args.output)

        # Update .env if requested
        if args.apply:
            update_env_file(optimal_temp, args.env_file, create_backup=True)

            # Also update backend/.env if it exists
            backend_env = args.env_file.parent / 'backend' / args.env_file.name
            if backend_env.exists():
                update_env_file(optimal_temp, backend_env, create_backup=False)

        log.info("\nCalibration complete!")
        log.info(f"Optimal temperature: {optimal_temp:.3f}")
        log.info(f"ECE before: {ece_before:.4f}")
        log.info(f"ECE after: {ece_after:.4f}")
        log.info(f"Add this to your .env: TEMPERATURE={optimal_temp:.3f}")

        if not args.apply:
            log.info(f"Run with --apply flag to update your .env file automatically")

    except Exception as e:
        log.error(f"Error during calibration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()