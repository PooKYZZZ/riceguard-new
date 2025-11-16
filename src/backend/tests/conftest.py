# tests/conftest.py
import os
import sys
import shutil
import tempfile
import pytest
import mongomock
from fastapi.testclient import TestClient


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app          # now resolvable
import db as dbmod

# Keep uploads small & isolated for tests (set BEFORE TestClient/app init)
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="uploads_")
os.environ["MAX_UPLOAD_MB"] = "2"  # 2MB limit for tests

@pytest.fixture(scope="session", autouse=True)
def _mock_db():
    """Replace get_db() with an in-memory Mongo client BEFORE app lifespan runs."""
    client = mongomock.MongoClient()
    testdb = client["test_db"]
    dbmod.get_db = lambda: testdb
    # Create indexes just like the app does
    import db as _db
    _db.ensure_indexes()
    yield
    client.close()

@pytest.fixture(scope="session")
def client(_mock_db):  # depend on _mock_db to guarantee order
    return TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def _cleanup_uploads():
    yield
    shutil.rmtree(os.environ["UPLOAD_DIR"], ignore_errors=True)
