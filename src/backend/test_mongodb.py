#!/usr/bin/env python3
"""
MongoDB Atlas Connection Test Script
Tests the database connection using the current .env configuration
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

try:
    from pymongo import MongoClient
    from pymongo.server_api import ServerApi
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    print("Testing MongoDB Atlas Connection...")
    print("=" * 50)
    
    # Get configuration
    mongo_uri = os.getenv('MONGO_URI')
    db_name = os.getenv('DB_NAME')
    
    if not mongo_uri:
        print("ERROR: MONGO_URI not found in .env file")
        sys.exit(1)
        
    if not db_name:
        print("ERROR: DB_NAME not found in .env file")
        sys.exit(1)
    
    print(f"MongoDB URI: {mongo_uri.replace('Dikoalam1991!', '***')}")
    print(f"Database Name: {db_name}")
    print()
    
    # Test connection
    print("Attempting to connect...")
    client = MongoClient(mongo_uri, server_api=ServerApi('1'))
    
    # Ping the server
    try:
        client.admin.command('ping')
        print("SUCCESS: MongoDB Atlas connection successful!")
        
        # Test database access
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"Database '{db_name}' is accessible")
        print(f"Existing collections: {collections if collections else 'None (new database)'}")
        
        # Test write operation
        test_collection = db.connection_test
        test_doc = {"test": "connection", "timestamp": "now"}
        result = test_collection.insert_one(test_doc)
        test_collection.delete_one({"_id": result.inserted_id})
        print("SUCCESS: Read/Write operations working correctly")
        
    except Exception as e:
        print(f"ERROR: Connection failed: {str(e)}")
        print("\nCommon fixes:")
        print("1. Check if REPLACE_CLUSTER is replaced with actual cluster name")
        print("2. Verify username and password are correct")
        print("3. Ensure your IP is whitelisted in MongoDB Atlas")
        print("4. Check if cluster is running")
        sys.exit(1)
        
    finally:
        client.close()
        print("Connection closed")
        
except ImportError as e:
    print(f"ERROR: Missing required package: {e}")
    print("Run: pip install pymongo python-dotenv")
    sys.exit(1)
    
except Exception as e:
    print(f"ERROR: Unexpected error: {e}")
    sys.exit(1)

print("\nMongoDB Atlas configuration is correct!")