# backend/seed.py
# Seed initial recommendation documents into MongoDB.

from datetime import datetime, timezone
from typing import Dict, Any
from db import get_db, ensure_indexes

# --- canonical keys must match ml_service / labels.txt EXACTLY ---
DEFAULT_RECOS: Dict[str, Dict[str, Any]] = {
    "bacterial_leaf_blight": {
        "title": "Bacterial Leaf Blight — Management",
        "steps": [
            "Use clean, certified seed and remove volunteer rice plants and weeds",
            "Improve field sanitation and water management; avoid standing water for long periods",
            "Avoid excessive nitrogen during early growth; prefer split applications",
        ],
        "version": "1.1",
    },
    "brown_spot": {
        "title": "Brown Spot — Management",
        "steps": [
            "Remove severely infected leaves and crop residues after harvest",
            "Ensure proper field drainage and avoid water stress",
            "Apply balanced fertilizer (add potassium; avoid excess nitrogen)",
        ],
        "version": "1.1",
    },
    "healthy": {
        "title": "Healthy — No Action Needed",
        "steps": [
            "Maintain good field hygiene and monitor crops regularly",
            "Follow balanced fertilization and proper spacing to sustain plant vigor",
        ],
        "version": "1.1",
    },
    "leaf_blast": {
        "title": "Leaf Blast — Management",
        "steps": [
            "Plant resistant or tolerant varieties when available",
            "Avoid late planting; synchronize planting to reduce inoculum pressure",
            "Improve airflow with proper spacing; avoid dense planting and excessive nitrogen",
        ],
        "version": "1.1",
    },
    "leaf_scald": {
        "title": "Leaf Scald — Management",
        "steps": [
            "Use balanced fertilization and avoid excess nitrogen",
            "Manage irrigation to reduce stress; maintain good drainage and avoid prolonged leaf wetness",
            "Remove crop debris after harvest; practice crop rotation if feasible",
        ],
        "version": "1.1",
    },
    "narrow_brown_spot": {
        "title": "Narrow Brown Spot — Management",
        "steps": [
            "Plant resistant varieties if available and use clean seed",
            "Improve field airflow with proper spacing; reduce canopy humidity",
            "Apply balanced fertilizer, emphasizing potassium; avoid excess nitrogen",
        ],
        "version": "1.1",
    },
}

# Optional migration from old keys used in earlier versions of the backend.
# If you had documents with 'blast' or 'blight', we upgrade them to the new keys.
ALIASES = {
    "blast": "leaf_blast",
    "blight": "bacterial_leaf_blight",
}


def seed_recommendations() -> None:
    """Insert default recommendation docs if they don't exist; migrate old keys."""
    ensure_indexes()
    db = get_db()
    coll = db.recommendations

    # --- migrate old keys to new canonical keys (best effort, safe if none exist) ---
    for old_key, new_key in ALIASES.items():
        # Only attempt migration if there is no canonical doc yet
        if coll.count_documents({"diseaseKey": new_key}) == 0:
            # Move first matching doc (if any) to the new key
            doc = coll.find_one({"diseaseKey": old_key})
            if doc:
                coll.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"diseaseKey": new_key, "updatedAt": datetime.now(timezone.utc)}},
                )

    # --- upsert canonical recommendations ---
    inserted = 0
    for key, val in DEFAULT_RECOS.items():
        res = coll.update_one(
            {"diseaseKey": key},
            {
                "$setOnInsert": {
                    "diseaseKey": key,
                    "title": val["title"],
                    "steps": val["steps"],
                    "version": val["version"],
                    "updatedAt": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        if res.upserted_id is not None:
            inserted += 1

    total = coll.count_documents({})
    print(f"[seed] recommendations upsert complete (inserted {inserted}, total {total}).")


if __name__ == "__main__":
    seed_recommendations()
