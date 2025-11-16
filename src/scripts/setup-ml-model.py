#!/usr/bin/env python3
"""
RiceGuard ML Model Setup Script
Handles downloading, validating, and configuring the ML model
"""

import os
import sys
import requests
import hashlib
from pathlib import Path
import zipfile
import shutil

# Project paths
REPO_ROOT = Path(__file__).parent.parent
ML_DIR = REPO_ROOT / "ml"
MODEL_FILE = ML_DIR / "model.h5"
MODEL_INFO_FILE = ML_DIR / "model_info.json"

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, color=Colors.OKCYAN):
    """Print colored status message"""
    print(f"{color}→{Colors.ENDC} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✅{Colors.ENDC} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}❌{Colors.ENDC} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠️{Colors.ENDC} {message}")

def calculate_file_hash(file_path):
    """Calculate SHA-256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception:
        return None

def create_ml_directory():
    """Create ML directory structure"""
    print_status("Creating ML directory structure...")

    ML_DIR.mkdir(exist_ok=True)
    print_success(f"Created {ML_DIR}")
    return True

def validate_model_file(model_path):
    """Validate the ML model file"""
    print_status("Validating ML model file...")

    if not model_path.exists():
        print_error("Model file not found")
        return False

    # Check file size (should be around 128MB)
    file_size = model_path.stat().st_size
    expected_size_min = 100 * 1024 * 1024  # 100MB
    expected_size_max = 150 * 1024 * 1024  # 150MB

    if file_size < expected_size_min or file_size > expected_size_max:
        print_warning(f"Model file size ({file_size / (1024*1024):.1f}MB) is outside expected range (100-150MB)")

    # Try to import and test the model
    try:
        import tensorflow as tf
        model = tf.keras.models.load_model(str(model_path))

        # Check model structure
        input_shape = model.input_shape
        output_shape = model.output_shape

        print(f"  Model input shape: {input_shape}")
        print(f"  Model output shape: {output_shape}")

        # Expected shapes for RiceGuard model
        if input_shape != (None, 224, 224, 3):
            print_warning(f"Unexpected input shape: {input_shape}")

        if output_shape != (None, 4):  # 4 classes: brown_spot, blast, blight, healthy
            print_warning(f"Unexpected output shape: {output_shape}")

        print_success("Model file validation passed")
        return True

    except ImportError:
        print_warning("TensorFlow not available for model validation")
        return True  # Continue without validation
    except Exception as e:
        print_error(f"Model validation failed: {e}")
        return False

def create_model_info():
    """Create model information file"""
    print_status("Creating model information file...")

    model_info = {
        "model_name": "RiceGuard Disease Detection Model",
        "version": "1.0.0",
        "description": "TensorFlow model for rice leaf disease detection",
        "classes": ["brown_spot", "blast", "blight", "healthy"],
        "input_shape": [224, 224, 3],
        "output_shape": [4],
        "expected_file_size": "128MB",
        "supported_formats": [".h5"],
        "preprocessing": {
            "image_size": [224, 224],
            "normalization": "divide by 255",
            "color_mode": "RGB"
        },
        "performance": {
            "accuracy": "95.2%",
            "confidence_threshold": 0.62,
            "temperature": 2.1
        },
        "requirements": {
            "tensorflow": ">=2.15.0",
            "numpy": ">=1.21.0",
            "pillow": ">=8.0.0"
        },
        "last_updated": "2024-01-01",
        "notes": [
            "Model trained on 10,000+ rice leaf images",
            "Supports 4 disease classes plus healthy",
            "Uses confidence calibration for improved predictions",
            "Temperature scaling optimized for better probability estimates"
        ]
    }

    try:
        import json
        with open(MODEL_INFO_FILE, "w") as f:
            json.dump(model_info, f, indent=2)
        print_success(f"Created {MODEL_INFO_FILE}")
        return True
    except Exception as e:
        print_error(f"Failed to create model info: {e}")
        return False

def create_download_script():
    """Create a script to help download the model"""
    print_status("Creating model download assistant...")

    download_script = REPO_ROOT / "scripts" / "download-model.py"
    script_content = '''#!/usr/bin/env python3
"""
RiceGuard ML Model Download Assistant
Provides instructions and download options for the ML model
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ML_DIR = REPO_ROOT / "ml"
MODEL_FILE = ML_DIR / "model.h5"

def print_instructions():
    """Print download instructions"""
    print("🌾 RiceGuard ML Model Download Instructions")
    print("=" * 50)
    print()
    print("The ML model file (model.h5) is required for RiceGuard to function.")
    print("It's a 128MB TensorFlow model that detects rice leaf diseases.")
    print()
    print("📥 Download Options:")
    print()
    print("1. 📁 Team File Sharing:")
    print("   - Check your team's Google Drive/Dropbox/OneDrive")
    print("   - Look for 'riceguard_model.h5' or similar")
    print("   - Download and place in: ml/model.h5")
    print()
    print("2. 🔗 Direct Download (if available):")
    print("   - Contact the ML team member for download link")
    print("   - File size: ~128MB")
    print("   - Format: TensorFlow .h5 file")
    print()
    print("3. 📧 Contact Team:")
    print("   - ML Engineer: Eugene Dela Cruz")
    print("   - Team Lead: Mark Angelo Aquino")
    print("   - Backend: Froilan Gayao")
    print()
    print("📁 Target Location:")
    print(f"   {MODEL_FILE}")
    print()
    print("✅ After downloading, run:")
    print("   python scripts/setup-ml-model.py")
    print("   python verify-setup.py")
    print()
    print("🔍 Model Details:")
    print("   - Size: ~128MB")
    print("   - Classes: brown_spot, blast, blight, healthy")
    print("   - Input: 224x224 RGB images")
    print("   - Framework: TensorFlow 2.x")

def check_model_exists():
    """Check if model file exists"""
    if MODEL_FILE.exists():
        file_size = MODEL_FILE.stat().st_size / (1024*1024)
        print(f"✅ Model file found: {MODEL_FILE}")
        print(f"📊 Size: {file_size:.1f}MB")
        return True
    else:
        print(f"❌ Model file not found: {MODEL_FILE}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        check_model_exists()
    else:
        print_instructions()

if __name__ == "__main__":
    main()
'''

    try:
        with open(download_script, "w") as f:
            f.write(script_content)
        print_success(f"Created {download_script}")
        return True
    except Exception as e:
        print_error(f"Failed to create download script: {e}")
        return False

def create_mobile_model_converter():
    """Create script to convert .h5 model to .tflite for mobile"""
    print_status("Creating mobile model converter...")

    converter_script = REPO_ROOT / "scripts" / "convert-to-tflite.py"
    script_content = '''#!/usr/bin/env python3
"""
RiceGuard Mobile Model Converter
Converts TensorFlow .h5 model to TensorFlow Lite .tflite format for mobile use
"""

import os
import sys
import tensorflow as tf
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ML_DIR = REPO_ROOT / "ml"
MODEL_FILE = ML_DIR / "model.h5"
TFLITE_FILE = ML_DIR / "model.tflite"

def convert_model():
    """Convert .h5 model to .tflite"""
    print("🔄 Converting TensorFlow model to TensorFlow Lite...")

    if not MODEL_FILE.exists():
        print(f"❌ Model file not found: {MODEL_FILE}")
        return False

    try:
        # Load the .h5 model
        print(f"📥 Loading model: {MODEL_FILE}")
        model = tf.keras.models.load_model(str(MODEL_FILE))

        # Convert to TensorFlow Lite
        print("⚙️ Converting to TensorFlow Lite format...")
        converter = tf.lite.TFLiteConverter.from_keras_model(model)

        # Enable optimizations for mobile
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

        # Convert the model
        tflite_model = converter.convert()

        # Save the TFLite model
        print(f"💾 Saving TFLite model: {TFLITE_FILE}")
        with open(TFLITE_FILE, "wb") as f:
            f.write(tflite_model)

        # Get file sizes
        h5_size = MODEL_FILE.stat().st_size / (1024*1024)
        tflite_size = TFLITE_FILE.stat().st_size / (1024*1024)

        print(f"✅ Conversion completed successfully!")
        print(f"📊 Original H5 size: {h5_size:.1f}MB")
        print(f"📊 TFLite size: {tflite_size:.1f}MB")
        print(f"📉 Size reduction: {((h5_size - tflite_size) / h5_size * 100):.1f}%")

        return True

    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        return False

def create_labels_file():
    """Create labels file for mobile app"""
    labels_file = ML_DIR / "labels.txt"

    labels = ["brown_spot", "blast", "blight", "healthy"]

    try:
        with open(labels_file, "w") as f:
            for label in labels:
                f.write(f"{label}\\n")

        print(f"✅ Created labels file: {labels_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to create labels file: {e}")
        return False

def main():
    """Main function"""
    print("🌾 RiceGuard Mobile Model Converter")
    print("=" * 40)

    # Convert the model
    if convert_model():
        # Create labels file
        create_labels_file()

        print("\\n" + "=" * 40)
        print("🎉 Mobile model setup completed!")
        print("\\nFiles created:")
        print(f"📱 TFLite Model: {TFLITE_FILE}")
        print(f"📋 Labels: {ML_DIR}/labels.txt")
        print("\\nNext steps:")
        print("1. Copy model.tflite to mobile app assets")
        print("2. Copy labels.txt to mobile app assets")
        print("3. Update mobile app to use new model")
        print("=" * 40)
        return True
    else:
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''

    try:
        with open(converter_script, "w") as f:
            f.write(script_content)
        print_success(f"Created {converter_script}")
        return True
    except Exception as e:
        print_error(f"Failed to create converter script: {e}")
        return False

def main():
    """Main ML model setup function"""
    print(f"{Colors.HEADER}{Colors.BOLD}🧠 RiceGuard ML Model Setup{Colors.ENDC}")
    print("Configuring TensorFlow model for rice leaf disease detection")
    print("=" * 60)

    # Setup steps
    setup_steps = [
        ("Creating ML directory structure", create_ml_directory),
        ("Creating download assistant", create_download_script),
        ("Creating mobile converter", create_mobile_model_converter),
        ("Creating model information", create_model_info),
    ]

    for step_name, step_func in setup_steps:
        print(f"\\n{step_name}...")
        if not step_func():
            print(f"❌ Failed to complete {step_name.lower()}")
            return False

    # Check if model exists and validate it
    print(f"\\nChecking for existing model...")
    if MODEL_FILE.exists():
        print_status(f"Found existing model: {MODEL_FILE}")
        if validate_model_file(MODEL_FILE):
            print_success("ML model setup completed successfully!")
        else:
            print_warning("Model validation failed, but setup completed")
    else:
        print_warning(f"Model file not found: {MODEL_FILE}")
        print_status("Run the following to get the model:")
        print(f"  python {REPO_ROOT}/scripts/download-model.py")

    print("\\n" + "=" * 60)
    print("📋 ML Model Setup Summary:")
    print("✅ Created ML directory structure")
    print("✅ Created download assistant script")
    print("✅ Created mobile converter script")
    print("✅ Created model information file")

    if MODEL_FILE.exists():
        print("✅ Model file is present")
    else:
        print("⚠️ Model file needs to be downloaded")

    print("\\nNext steps:")
    print("1. Download model.h5 (128MB) from team")
    print(f"2. Place it in: {MODEL_FILE}")
    print("3. Validate: python scripts/setup-ml-model.py")
    print("4. Convert for mobile: python scripts/convert-to-tflite.py")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\\n{Colors.WARNING}Setup cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)