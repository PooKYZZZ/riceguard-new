#!/usr/bin/env python3
"""
RiceGuard Mobile App Setup Script
Sets up React Native/Expo mobile app development environment
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Project paths
REPO_ROOT = Path(__file__).parent.parent
MOBILE_DIR = REPO_ROOT / "mobileapp" / "riceguard"

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

def check_mobile_directory():
    """Check if mobile app directory exists"""
    print_status("Checking mobile app directory...")

    if MOBILE_DIR.exists():
        print_success(f"Mobile app directory found: {MOBILE_DIR}")
        return True
    else:
        print_warning(f"Mobile app directory not found: {MOBILE_DIR}")
        return False

def install_expo_cli():
    """Install Expo CLI globally"""
    print_status("Installing Expo CLI...")

    try:
        # Install Expo CLI
        subprocess.run(
            ["npm", "install", "-g", "expo-cli"],
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Expo CLI installed globally")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install Expo CLI: {e}")
        return False

def install_mobile_dependencies():
    """Install mobile app dependencies"""
    print_status("Installing mobile app dependencies...")

    if not MOBILE_DIR.exists():
        print_error("Mobile app directory not found")
        return False

    # Check if package.json exists
    package_json = MOBILE_DIR / "package.json"
    if not package_json.exists():
        print_error("package.json not found in mobile app directory")
        return False

    try:
        # Install dependencies
        subprocess.run(
            ["npm", "install"],
            cwd=MOBILE_DIR,
            check=True,
            capture_output=True,
            text=True
        )
        print_success("Mobile dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install mobile dependencies: {e}")
        return False

def create_mobile_env_file():
    """Create mobile app environment file"""
    print_status("Creating mobile environment configuration...")

    if not MOBILE_DIR.exists():
        print_error("Mobile app directory not found")
        return False

    mobile_env = MOBILE_DIR / ".env"
    mobile_env_example = MOBILE_DIR / ".env.example"

    # Create .env.example if it doesn't exist
    if not mobile_env_example.exists():
        env_content = """# Mobile App Environment Configuration
# Copy this file to .env and update values

# API Configuration
# Use your PC's IP address for mobile development
# Format: http://YOUR_PC_IP:8000/api/v1
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1

# App Configuration
EXPO_PUBLIC_APP_NAME=RiceGuard
EXPO_PUBLIC_APP_VERSION=1.0.0

# Development Configuration
EXPO_PUBLIC_DEBUG=true
EXPO_PUBLIC_LOG_LEVEL=debug

# Feature Flags
EXPO_PUBLIC_ENABLE_ANALYTICS=false
EXPO_PUBLIC_ENABLE_CRASH_REPORTING=false

# Build Configuration
EXPO_PUBLIC_ENVIRONMENT=development
"""

        try:
            with open(mobile_env_example, "w") as f:
                f.write(env_content)
            print_success(f"Created {mobile_env_example}")
        except Exception as e:
            print_error(f"Failed to create .env.example: {e}")
            return False

    # Create .env file from example if it doesn't exist
    if not mobile_env.exists():
        try:
            import shutil
            shutil.copy(mobile_env_example, mobile_env)
            print_success(f"Created {mobile_env} from example")
        except Exception as e:
            print_error(f"Failed to create .env: {e}")
            return False
    else:
        print_success(f"{mobile_env} already exists")

    return True

def setup_mobile_model():
    """Setup mobile TensorFlow Lite model"""
    print_status("Setting up mobile ML model...")

    ml_dir = REPO_ROOT / "ml"
    mobile_assets = MOBILE_DIR / "assets"

    # Create assets directory if it doesn't exist
    mobile_assets.mkdir(exist_ok=True)

    # Copy TensorFlow Lite model if it exists
    tflite_model = ml_dir / "model.tflite"
    if tflite_model.exists():
        try:
            import shutil
            shutil.copy(tflite_model, mobile_assets / "model.tflite")
            print_success("Copied TensorFlow Lite model to mobile assets")
        except Exception as e:
            print_error(f"Failed to copy TFLite model: {e}")
            return False
    else:
        print_warning("TensorFlow Lite model not found. Run convert-to-tflite.py first")

    # Copy labels file if it exists
    labels_file = ml_dir / "labels.txt"
    if labels_file.exists():
        try:
            import shutil
            shutil.copy(labels_file, mobile_assets / "labels.txt")
            print_success("Copied labels file to mobile assets")
        except Exception as e:
            print_error(f"Failed to copy labels file: {e}")
            return False
    else:
        print_warning("Labels file not found")

    return True

def create_mobile_start_script():
    """Create mobile app start script"""
    print_status("Creating mobile start script...")

    if not MOBILE_DIR.exists():
        print_error("Mobile app directory not found")
        return False

    start_script = MOBILE_DIR / "start-mobile.sh"
    script_content = """#!/bin/bash
# RiceGuard Mobile App Development Starter

# Get local IP address
get_local_ip() {
    if command -v ipconfig &> /dev/null; then
        # Windows
        ipconfig | grep "IPv4" | awk '{print $14}' | head -1
    elif command -v ifconfig &> /dev/null; then
        # macOS/Linux
        ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1
    else
        echo "127.0.0.1"
    fi
}

# Set environment variables
LOCAL_IP=$(get_local_ip)
export EXPO_PUBLIC_API_BASE_URL="http://${LOCAL_IP}:8000/api/v1"
export REACT_NATIVE_PACKAGER_HOSTNAME="${LOCAL_IP}"

echo "📱 Starting RiceGuard Mobile App"
echo "🌐 Local IP: ${LOCAL_IP}"
echo "🔗 API URL: ${EXPO_PUBLIC_API_BASE_URL}"
echo ""

# Start Expo
npx expo start --lan --clear
"""

    try:
        with open(start_script, "w") as f:
            f.write(script_content)

        # Make script executable
        start_script.chmod(0o755)
        print_success(f"Created {start_script}")
        return True
    except Exception as e:
        print_error(f"Failed to create start script: {e}")
        return False

def create_mobile_instructions():
    """Create mobile development instructions"""
    print_status("Creating mobile development instructions...")

    if not MOBILE_DIR.exists():
        print_error("Mobile app directory not found")
        return False

    instructions_file = MOBILE_DIR / "MOBILE_SETUP.md"
    instructions_content = """# RiceGuard Mobile App Setup Instructions

## Prerequisites

- Node.js 18+ installed
- Expo CLI installed globally
- Physical mobile device (recommended) or emulator
- RiceGuard backend running on your network

## Setup Steps

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Copy `.env.example` to `.env` and update the API URL:
```bash
cp .env.example .env
```

Update `EXPO_PUBLIC_API_BASE_URL` with your PC's IP address.

### 3. Start Backend
Make sure the RiceGuard backend is running:
```bash
# From project root
python start-dev.py --backend-only
```

### 4. Start Mobile Development Server
```bash
# Using the helper script
./start-mobile.sh

# Or manually
export EXPO_PUBLIC_API_BASE_URL="http://YOUR_PC_IP:8000/api/v1"
export REACT_NATIVE_PACKAGER_HOSTNAME="YOUR_PC_IP"
npx expo start --lan --clear
```

### 5. Run on Device

#### Physical Device (Recommended)
1. Install Expo Go on your phone
2. Scan the QR code shown in the terminal
3. The app should connect to your backend

#### Android Emulator
1. Start Android Studio and create an emulator
2. Run: `npx expo start --android`
3. Use API URL: `http://10.0.2.2:8000/api/v1`

#### iOS Simulator
1. Start Xcode and open simulator
2. Run: `npx expo start --ios`
3. Use API URL: `http://127.0.0.1:8000/api/v1`

## Troubleshooting

### Device Cannot Reach Backend
1. Ensure backend runs with `--host 0.0.0.0`
2. Check firewall settings for port 8000
3. Verify your PC's IP address
4. Try using `--tunnel` mode

### Metro Bundler Issues
```bash
# Clear cache
npx expo start --clear

# Reset everything
npx expo start -c
```

### Network Issues
- Disable VPN temporarily
- Ensure you're on the same network as your PC
- Check router firewall settings

## Development Tips

- Use Chrome DevTools for debugging
- Shake device to open developer menu
- Check Expo Go logs for network errors
- Test on both Android and iOS if possible

## Build for Production

When ready to build for app stores:
```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Build for Android
eas build --platform android

# Build for iOS
eas build --platform ios
```
"""

    try:
        with open(instructions_file, "w") as f:
            f.write(instructions_content)
        print_success(f"Created {instructions_file}")
        return True
    except Exception as e:
        print_error(f"Failed to create instructions: {e}")
        return False

def main():
    """Main mobile setup function"""
    print(f"{Colors.HEADER}{Colors.BOLD}📱 RiceGuard Mobile App Setup{Colors.ENDC}")
    print("Configuring React Native/Expo mobile development environment")
    print("=" * 60)

    # Check if mobile directory exists
    if not check_mobile_directory():
        print_warning("Mobile app is optional. Skipping mobile setup.")
        return True

    # Setup steps
    setup_steps = [
        ("Installing Expo CLI", install_expo_cli),
        ("Installing mobile dependencies", install_mobile_dependencies),
        ("Creating environment configuration", create_mobile_env_file),
        ("Setting up mobile ML model", setup_mobile_model),
        ("Creating mobile start script", create_mobile_start_script),
        ("Creating setup instructions", create_mobile_instructions),
    ]

    for step_name, step_func in setup_steps:
        print(f"\n{step_name}...")
        if not step_func():
            print_error(f"Failed to complete {step_name.lower()}")
            return False

    print("\n" + "=" * 60)
    print("🎉 Mobile app setup completed successfully!")
    print("\nNext steps:")
    print("1. Configure mobile/.env (copy from .env.example)")
    print("2. Update EXPO_PUBLIC_API_BASE_URL with your PC IP")
    print("3. Start backend: python start-dev.py --backend-only")
    print("4. Start mobile app: cd mobileapp/riceguard && ./start-mobile.sh")
    print("5. Scan QR code with Expo Go on your phone")
    print("\n📚 Read mobileapp/riceguard/MOBILE_SETUP.md for detailed instructions")
    print("=" * 60)

    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup cancelled by user{Colors.ENDC}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
        sys.exit(1)