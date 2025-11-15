# backend/db.py
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from bson import ObjectId
from settings import MONGO_URI, DB_NAME
import certifi

_client: MongoClient | None = None

def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(
            MONGO_URI,
            uuidRepresentation="standard",
            tls=True,                         
            tlsCAFile=certifi.where(),        
            serverSelectionTimeoutMS=8000,    
        )
    return _client

def get_db():
    return get_client()[DB_NAME]

def ensure_indexes():
    db = get_db()
    db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")
    db.scans.create_index([("userId", ASCENDING), ("createdAt", DESCENDING)], name="user_createdAt")

def as_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise ValueError("Invalid ObjectId format")

def close_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None
