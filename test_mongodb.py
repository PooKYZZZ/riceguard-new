#!/usr/bin/env python3
"""
MongoDB Connection Test Script for RiceGuard
Tests MongoDB Atlas connection before starting the application
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "src" / "backend"
sys.path.insert(0, str(backend_path))

def test_mongo_connection():
    """Test MongoDB connection with detailed error reporting."""
    print("=" * 70)
    print("RiceGuard MongoDB Connection Test")
    print("=" * 70)
    print()
    
    try:
        print("Step 1: Loading environment configuration...")
        from settings import MONGO_URI, DB_NAME
        
        # Mask password in URI for display
        display_uri = MONGO_URI
        if '@' in MONGO_URI:
            parts = MONGO_URI.split('@')
            if '://' in parts[0]:
                auth_part = parts[0].split('://')[1]
                if ':' in auth_part:
                    username = auth_part.split(':')[0]
                    display_uri = MONGO_URI.replace(auth_part, f"{username}:****")
        
        print(f"   ✅ Environment loaded successfully")
        print(f"   📍 MongoDB URI: {display_uri}")
        print(f"   📊 Database Name: {DB_NAME}")
        print()
        
        print("Step 2: Validating MongoDB URI format...")
        if MONGO_URI.startswith('mongodb+srv://'):
            print("   ✅ Using MongoDB Atlas (mongodb+srv://)")
        elif MONGO_URI.startswith('mongodb://'):
            if 'localhost' in MONGO_URI or '127.0.0.1' in MONGO_URI:
                print("   ❌ ERROR: localhost MongoDB detected!")
                print("   💡 RiceGuard requires MongoDB Atlas cloud database")
                print("   📖 See MONGODB_SETUP.md for setup instructions")
                return False
            print("   ⚠️  Using standard MongoDB connection (not Atlas)")
        else:
            print("   ❌ ERROR: Invalid MongoDB URI format")
            return False
        print()
        
        print("Step 3: Connecting to MongoDB Atlas...")
        print("   ⏳ This may take 10-15 seconds...")
        from db import get_client
        
        client = get_client()
        print("   ✅ MongoDB client created successfully")
        print()
        
        print("Step 4: Testing database operations...")
        db = client[DB_NAME]
        
        # Test ping
        admin_db = client.admin
        result = admin_db.command('ping', maxTimeMS=5000)
        print(f"   ✅ Ping successful: {result}")
        
        # Get server info
        server_info = admin_db.command('serverStatus', maxTimeMS=10000)
        print(f"   ✅ MongoDB version: {server_info.get('version', 'unknown')}")
        print(f"   ✅ Uptime: {server_info.get('uptime', 0)} seconds")
        print()
        
        print("Step 5: Checking database collections...")
        collections = db.list_collection_names()
        print(f"   ✅ Found {len(collections)} collections")
        if collections:
            for coll in collections:
                count = db[coll].count_documents({})
                print(f"      - {coll}: {count} documents")
        else:
            print("      - No collections yet (this is normal for new database)")
        print()
        
        print("=" * 70)
        print("✅ SUCCESS: MongoDB Atlas connection is working perfectly!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run: python start.py")
        print("  2. Access backend: http://127.0.0.1:8000")
        print("  3. Access frontend: http://localhost:3000")
        print()
        return True
        
    except ValueError as e:
        print()
        print("=" * 70)
        print("❌ CONFIGURATION ERROR")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("💡 Solution:")
        print("   1. Open src/backend/.env file")
        print("   2. Update MONGO_URI with your MongoDB Atlas credentials")
        print("   3. See MONGODB_SETUP.md for detailed setup guide")
        print()
        return False
        
    except ImportError as e:
        print()
        print("=" * 70)
        print("❌ IMPORT ERROR")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("💡 Solution:")
        print("   1. Install required packages: pip install pymongo python-dotenv certifi")
        print("   2. Or run: pip install -r src/backend/requirements.txt")
        print()
        return False
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ CONNECTION ERROR")
        print("=" * 70)
        print()
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print()
        print("💡 Common solutions:")
        print("   1. Check MongoDB Atlas IP whitelist (allow 0.0.0.0/0 for development)")
        print("   2. Verify username and password are correct in MONGO_URI")
        print("   3. Ensure cluster is running (not paused)")
        print("   4. Check network connectivity")
        print("   5. See MONGODB_SETUP.md for detailed troubleshooting")
        print()
        return False

if __name__ == "__main__":
    success = test_mongo_connection()
    sys.exit(0 if success else 1)
