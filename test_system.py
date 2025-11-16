#!/usr/bin/env python3
"""
RiceGuard System Connectivity Test Script

This script tests all major components of the RiceGuard system to ensure
everything is properly configured and working.
"""

import os
import sys
import requests
import json
from pathlib import Path

def test_mongodb_connection():
    """Test MongoDB connection"""
    print("🔍 Testing MongoDB connection...")

    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "src" / "backend"
        sys.path.insert(0, str(backend_path))

        from dotenv import load_dotenv
        from pymongo import MongoClient

        # Load environment variables
        load_dotenv(backend_path / ".env")

        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            print("❌ MONGO_URI not found in environment")
            return False

        print(f"   Connecting to: {mongo_uri[:50]}...")

        # Test connection
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')

        # Get database info
        db_name = mongo_uri.split('/')[-1].split('?')[0]
        db = client[db_name]
        collections = db.list_collection_names()

        print(f"✅ MongoDB connection successful!")
        print(f"   Database: {db_name}")
        print(f"   Collections: {len(collections)}")
        client.close()
        return True

    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_backend_health():
    """Test backend health endpoint"""
    print("\n🔍 Testing backend health...")

    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend health check successful!")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            return True
        else:
            print(f"❌ Backend health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_frontend_running():
    """Test if frontend is accessible"""
    print("\n🔍 Testing frontend accessibility...")

    try:
        response = requests.get("http://localhost:3000", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is running!")
            print("   URL: http://localhost:3000")
            return True
        else:
            print(f"❌ Frontend returned HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not running on http://localhost:3000")
        return False
    except Exception as e:
        print(f"❌ Frontend check failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🔍 Testing API endpoints...")

    base_url = "http://localhost:8000/api/v1"

    # Test endpoints that don't require authentication
    endpoints = [
        "/health",
        "/recommendations/healthy"
    ]

    success_count = 0

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"   ✅ GET {endpoint}")
                success_count += 1
            else:
                print(f"   ❌ GET {endpoint} - HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ GET {endpoint} - {e}")

    print(f"\n   API Tests: {success_count}/{len(endpoints)} successful")
    return success_count == len(endpoints)

def check_environment_files():
    """Check if environment files are properly configured"""
    print("\n🔍 Checking environment configuration...")

    backend_env = Path(__file__).parent / "src" / "backend" / ".env"
    frontend_env = Path(__file__).parent / "src" / "frontend" / ".env"

    checks = []

    # Check backend .env
    if backend_env.exists():
        print("   ✅ Backend .env file exists")
        checks.append(True)

        # Check required variables
        with open(backend_env) as f:
            content = f.read()
            required_vars = ['MONGO_URI', 'JWT_SECRET']
            for var in required_vars:
                if f"{var}=" in content:
                    print(f"   ✅ {var} configured")
                else:
                    print(f"   ❌ {var} missing")
    else:
        print("   ❌ Backend .env file missing")
        checks.append(False)

    # Check frontend .env
    if frontend_env.exists():
        print("   ✅ Frontend .env file exists")
        checks.append(True)

        # Check API URL
        with open(frontend_env) as f:
            content = f.read()
            if "REACT_APP_API_URL=" in content:
                print("   ✅ REACT_APP_API_URL configured")
            else:
                print("   ❌ REACT_APP_API_URL missing")
    else:
        print("   ❌ Frontend .env file missing")
        checks.append(False)

    return all(checks)

def check_upload_directory():
    """Check if upload directory exists and is writable"""
    print("\n🔍 Checking upload directory...")

    upload_dir = Path(__file__).parent / "src" / "backend" / "uploads"

    if upload_dir.exists():
        print("   ✅ Upload directory exists")

        # Test write permissions
        test_file = upload_dir / "test_write.tmp"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print("   ✅ Upload directory is writable")
            return True
        except Exception as e:
            print(f"   ❌ Upload directory not writable: {e}")
            return False
    else:
        print("   ❌ Upload directory missing")
        return False

def main():
    """Run all tests"""
    print("🚀 RiceGuard System Connectivity Test")
    print("=" * 50)

    tests = [
        ("Environment Configuration", check_environment_files),
        ("Upload Directory", check_upload_directory),
        ("MongoDB Connection", test_mongodb_connection),
        ("Backend Health", test_backend_health),
        ("Frontend Running", test_frontend_running),
        ("API Endpoints", test_api_endpoints),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 All tests passed! The RiceGuard system is ready to use.")
        print("\nNext steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Register a new account")
        print("3. Try uploading an image for analysis")
    else:
        print(f"\n⚠️  {len(results) - passed} test(s) failed.")
        print("Please review the errors above and fix the issues.")

        if not any("MongoDB" in name and not result for name, result in results):
            print("\n💡 Tip: The system is configured to use local MongoDB.")
            print("   Make sure MongoDB is running on your system.")

        if not any("Backend" in name and not result for name, result in results):
            print("\n💡 Tip: Start the backend with:")
            print("   cd src/backend && python main.py")

        if not any("Frontend" in name and not result for name, result in results):
            print("\n💡 Tip: Start the frontend with:")
            print("   cd src/frontend && npm start")

if __name__ == "__main__":
    main()