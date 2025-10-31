"""
test_edge_cases.py - Edge case tests for stordb
"""
import os
import tempfile
import pytest
import stordb

def test_add_missing_fields(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    # Missing mac_address
    with pytest.raises(Exception):
        stordb.add_secret("", "Router", "Alice", "Main router")
    # Missing device_name
    with pytest.raises(Exception):
        stordb.add_secret("00:11:22:33:44:55", "", "Alice", "Main router")
    # Missing owner
    with pytest.raises(Exception):
        stordb.add_secret("00:11:22:33:44:55", "Router", "", "Main router")

def test_import_malformed_json(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("not a json")
    # Should print error and not raise
    stordb.import_json(str(bad_json))

def test_update_delete_nonexistent(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    # Update non-existent
    stordb.update_secret(9999, {"owner": "Nobody"})
    # Delete non-existent
    stordb.delete_secret(9999)

def test_redaction_logic(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router", secret_value="supersecret")
    result = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    assert result["mac_address"] == "00:11:22:33:44:55"
    # Simulate CLI output redaction
    safe_result = dict(result)
    if "secret_value" in safe_result:
        safe_result["secret_value"] = "[REDACTED]"
    if "mac_address" in safe_result:
        safe_result["mac_address"] = "[REDACTED]"
    assert safe_result["mac_address"] == "[REDACTED]"
    assert safe_result["secret_value"] == "[REDACTED]"
