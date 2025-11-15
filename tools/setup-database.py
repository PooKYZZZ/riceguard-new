#!/usr/bin/env python3
"""
RiceGuard Database Setup and Seeding Script
Automatically configures MongoDB Atlas and seeds with initial data
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime
import pymongo
from pymongo import MongoClient
from dotenv import load_dotenv

# Add backend to path for imports
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def load_environment():
    """Load environment variables from .env file"""
    env_file = backend_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        return True
    else:
        print("❌ Backend .env file not found. Please create it from .env.example")
        return False

def test_database_connection():
    """Test MongoDB Atlas connection"""
    try:
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME")

        if not mongo_uri or not db_name:
            print("❌ MONGO_URI or DB_NAME not found in environment variables")
            return False

        print(f"🔗 Testing connection to MongoDB Atlas...")
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)

        # Test the connection
        client.server_info()
        db = client[db_name]

        print(f"✅ Successfully connected to database: {db_name}")
        return True, client, db

    except pymongo.errors.ServerSelectionTimeoutError:
        print("❌ Connection timeout. Check your internet connection and MongoDB URI.")
        return False
    except pymongo.errors.ConfigurationError:
        print("❌ Invalid MongoDB URI format. Please check your connection string.")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def create_indexes(db):
    """Create necessary database indexes for performance"""
    print("🔧 Creating database indexes...")

    try:
        # Users collection indexes
        db.users.create_index("email", unique=True)
        print("  ✅ Created unique index on users.email")

        # Scans collection indexes
        db.scans.create_index("userId")
        db.scans.create_index([("userId", 1), ("createdAt", -1)])
        db.scans.create_index("createdAt")
        print("  ✅ Created indexes on scans collection")

        # Recommendations collection indexes
        db.recommendations.create_index("diseaseKey", unique=True)
        print("  ✅ Created unique index on recommendations.diseaseKey")

        print("✅ All database indexes created successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")
        return False

def seed_recommendations(db):
    """Seed disease recommendations data"""
    print("🌱 Seeding disease recommendations...")

    recommendations = [
        {
            "_id": "brown_spot",
            "diseaseKey": "brown_spot",
            "diseaseName": "Brown Spot",
            "scientificName": "Cochliobolus miyabeanus",
            "description": "Brown spot is a fungal disease that causes small, circular, brown spots on rice leaves.",
            "symptoms": [
                "Small, circular to oval brown spots on leaves",
                "Spots have gray centers and dark brown margins",
                "Lesions may coalesce in severe infections",
                "Reduced photosynthesis and plant vigor"
            ],
            "causes": [
                "Fungal pathogen Cochliobolus miyabeanus",
                "High humidity and moderate temperatures",
                "Excessive nitrogen fertilization",
                "Poor drainage and waterlogged conditions"
            ],
            "treatment": [
                "Use resistant rice varieties",
                "Apply fungicides (e.g., propiconazole, tebuconazole)",
                "Balance fertilizer application",
                "Ensure proper field drainage",
                "Practice crop rotation"
            ],
            "prevention": [
                "Use certified disease-free seeds",
                "Maintain proper plant spacing",
                "Avoid excessive nitrogen fertilization",
                "Ensure good water management",
                "Monitor fields regularly for early detection"
            ],
            "severity": "moderate",
            "impact": "yield_loss_moderate"
        },
        {
            "_id": "blast",
            "diseaseKey": "blast",
            "diseaseName": "Rice Blast",
            "scientificName": "Magnaporthe oryzae",
            "description": "Rice blast is one of the most destructive diseases of rice worldwide, affecting leaves, nodes, and panicles.",
            "symptoms": [
                "Diamond-shaped lesions with gray centers and brown margins",
                "Lesions may enlarge and coalesce",
                "Neck blast can cause panicle breakage",
                "White to gray fungal growth in humid conditions"
            ],
            "causes": [
                "Fungal pathogen Magnaporthe oryzae",
                "High humidity (above 90%)",
                "Temperature range of 25-28°C",
                "Excessive nitrogen fertilization"
            ],
            "treatment": [
                "Apply systemic fungicides (e.g., tricyclazole, azoxystrobin)",
                "Use resistant varieties",
                "Adjust planting density",
                "Balance fertilizer application"
            ],
            "prevention": [
                "Plant resistant varieties",
                "Avoid excessive nitrogen",
                "Ensure proper field drainage",
                "Practice crop rotation",
                "Remove infected plant debris"
            ],
            "severity": "high",
            "impact": "yield_loss_severe"
        },
        {
            "_id": "blight",
            "diseaseKey": "blight",
            "diseaseName": "Bacterial Blight",
            "scientificName": "Xanthomonas oryzae pv. oryzae",
            "description": "Bacterial blight is a serious bacterial disease that causes yellowing and drying of rice leaves.",
            "symptoms": [
                "Yellow to white lesions along leaf margins",
                "Wavy, translucent lesions that turn white",
                "Lesions may extend to entire leaf blade",
                "Kresek phase: seedling wilting and death"
            ],
            "causes": [
                "Bacterial pathogen Xanthomonas oryzae",
                "High humidity and temperature",
                "Rain and wind dispersal",
                "Contaminated seeds and equipment"
            ],
            "treatment": [
                "Use resistant varieties",
                "Apply bactericides (e.g., copper-based compounds)",
                "Balanced fertilizer application",
                "Proper water management"
            ],
            "prevention": [
                "Use certified disease-free seeds",
                "Seed treatment with hot water or chemicals",
                "Remove infected plants",
                "Sanitize farm equipment",
                "Avoid excessive nitrogen fertilization"
            ],
            "severity": "moderate_to_high",
            "impact": "yield_loss_moderate_to_severe"
        },
        {
            "_id": "healthy",
            "diseaseKey": "healthy",
            "diseaseName": "Healthy",
            "scientificName": "Oryza sativa",
            "description": "Healthy rice plant with no disease symptoms.",
            "symptoms": [
                "Green, uniform leaf color",
                "No lesions or spots",
                "Normal plant growth and development",
                "Good tillering and vigor"
            ],
            "causes": [
                "Proper crop management",
                "Balanced nutrition",
                "Adequate water management",
                "Disease-resistant varieties"
            ],
            "treatment": [
                "Continue good agricultural practices",
                "Regular monitoring",
                "Balanced fertilizer application",
                "Proper irrigation management"
            ],
            "prevention": [
                "Use quality seeds",
                "Proper field preparation",
                "Balanced fertilization",
                "Timely weed control",
                "Regular field scouting"
            ],
            "severity": "none",
            "impact": "optimal_yield"
        }
    ]

    try:
        # Clear existing recommendations
        db.recommendations.delete_many({})

        # Insert new recommendations
        result = db.recommendations.insert_many(recommendations)
        print(f"  ✅ Seeded {len(result.inserted_ids)} disease recommendations")
        return True

    except Exception as e:
        print(f"❌ Failed to seed recommendations: {e}")
        return False

def create_test_user(db):
    """Create a test user for development"""
    print("👤 Creating test user...")

    try:
        # Check if test user already exists
        existing_user = db.users.find_one({"email": "test@riceguard.com"})
        if existing_user:
            print("  ℹ️ Test user already exists")
            return True

        # Import password hashing from backend
        try:
            from security import hash_password
            hashed_password = hash_password("test123")
        except ImportError:
            # Fallback if backend modules not available
            import hashlib
            hashed_password = hashlib.sha256("test123".encode()).hexdigest()

        test_user = {
            "email": "test@riceguard.com",
            "password": hashed_password,
            "fullName": "Test User",
            "createdAt": datetime.utcnow(),
            "isActive": True,
            "role": "user"
        }

        result = db.users.insert_one(test_user)
        print(f"  ✅ Created test user with ID: {result.inserted_id}")
        print(f"  📧 Email: test@riceguard.com")
        print(f"  🔑 Password: test123")
        return True

    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False

def create_database_info(db):
    """Create database information document"""
    print("📋 Creating database information...")

    try:
        db_info = {
            "_id": "database_info",
            "version": "1.0.0",
            "createdAt": datetime.utcnow(),
            "lastUpdated": datetime.utcnow(),
            "description": "RiceGuard MongoDB Atlas Database",
            "collections": {
                "users": "User accounts and authentication",
                "scans": "Disease scan records and predictions",
                "recommendations": "Disease treatment recommendations"
            },
            "setup_completed": True
        }

        # Use replace_one with upsert
        db.database_info.replace_one(
            {"_id": "database_info"},
            db_info,
            upsert=True
        )
        print("  ✅ Database information created")
        return True

    except Exception as e:
        print(f"❌ Failed to create database info: {e}")
        return False

def verify_setup(db):
    """Verify that database setup was successful"""
    print("🔍 Verifying database setup...")

    try:
        # Check collections
        collections = db.list_collection_names()
        expected_collections = ["users", "scans", "recommendations", "database_info"]

        for collection in expected_collections:
            if collection in collections:
                count = db[collection].count_documents({})
                print(f"  ✅ {collection}: {count} documents")
            else:
                print(f"  ❌ {collection}: not found")
                return False

        # Check indexes
        indexes = db.users.list_indexes()
        print(f"  ✅ Users collection has {len(list(indexes))} indexes")

        print("✅ Database setup verification completed successfully")
        return True

    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False

def main():
    """Main database setup function"""
    print("🗄️ RiceGuard Database Setup")
    print("=" * 40)

    # Load environment variables
    if not load_environment():
        return False

    # Test database connection
    connection_result = test_database_connection()
    if not connection_result:
        return False

    # Unpack connection result
    if isinstance(connection_result, tuple):
        success, client, db = connection_result
    else:
        return False

    try:
        # Setup steps
        setup_steps = [
            ("Creating indexes", lambda: create_indexes(db)),
            ("Seeding recommendations", lambda: seed_recommendations(db)),
            ("Creating test user", lambda: create_test_user(db)),
            ("Creating database info", lambda: create_database_info(db)),
            ("Verifying setup", lambda: verify_setup(db))
        ]

        for step_name, step_func in setup_steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"❌ Failed to complete {step_name.lower()}")
                return False

        print("\n" + "=" * 40)
        print("🎉 Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Start the backend server: cd backend && python -m uvicorn main:app --reload")
        print("2. Access API documentation: http://127.0.0.1:8000/docs")
        print("3. Test with test user: test@riceguard.com / test123")
        print("=" * 40)

        return True

    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Database setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)