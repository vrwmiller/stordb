"""
test_stordb.py - Initial tests for stordb
"""
import os
import tempfile
import sqlite3
import pytest
import stordb

def test_init_db(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    assert db_path.exists()
    # Check table exists
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='secrets'")
    assert cursor.fetchone() is not None
    conn.close()

def test_add_and_lookup(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router")
    result = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    assert result is not None
    assert result["device_name"] == "Router"
    assert result["owner"] == "Alice"

def test_update_and_delete(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router")
    result = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    id = result["id"]
    stordb.update_secret(id, {"owner": "Bob"})
    updated = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    assert updated["owner"] == "Bob"
    stordb.delete_secret(id)
    deleted = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    assert deleted is None
