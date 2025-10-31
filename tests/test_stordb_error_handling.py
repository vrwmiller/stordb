"""
test_stordb_error_handling.py - Tests for error handling in stordb.py
"""
import os
import pytest
import stordb
import sqlite3
import json

def test_get_db_connection_error(monkeypatch):
    # Simulate sqlite3.connect raising an error
    monkeypatch.setattr(sqlite3, "connect", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("fail connect")))
    with pytest.raises(sqlite3.OperationalError):
        stordb.get_db_connection("/tmp/doesnotexist.sqlite")

def test_add_secret_db_error(monkeypatch):
    # Simulate db connection error
    monkeypatch.setattr(stordb, "get_db_connection", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("fail add")))
    with pytest.raises(sqlite3.OperationalError):
        stordb.add_secret("mac", "dev", "owner")

def test_update_secret_db_error(monkeypatch):
    monkeypatch.setattr(stordb, "get_db_connection", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("fail update")))
    with pytest.raises(sqlite3.OperationalError):
        stordb.update_secret(1, {"owner": "Bob"})

def test_delete_secret_db_error(monkeypatch):
    monkeypatch.setattr(stordb, "get_db_connection", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("fail delete")))
    with pytest.raises(sqlite3.OperationalError):
        stordb.delete_secret(1)

def test_import_json_load_error(tmp_path, monkeypatch):
    # Simulate file not found
    bad_file = tmp_path / "missing.json"
    stordb.import_json(str(bad_file))  # Should print error and not raise

def test_import_json_record_error(tmp_path, monkeypatch):
    # Simulate error in add_secret for a record
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    monkeypatch.setattr(stordb, "add_secret", lambda *a, **k: (_ for _ in ()).throw(ValueError("fail record")))
    data = [{"mac_address": "mac", "device_name": "dev", "owner": "owner"}]
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps(data))
    stordb.import_json(str(json_file))  # Should print error and not raise

def test_export_db_to_json_error(monkeypatch):
    # Simulate open() raising error
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("fail open")))
    with pytest.raises(OSError):
        stordb.export_db_to_json("/tmp/fail.json")

def test_import_db_from_json_error(monkeypatch):
    # Simulate open() raising error
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("fail open")))
    with pytest.raises(OSError):
        stordb.import_db_from_json("/tmp/fail.json")

def test_import_db_from_json_record_error(tmp_path, monkeypatch):
    # Simulate error in record import
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    monkeypatch.setattr(stordb, "get_db_connection", lambda *a, **k: (_ for _ in ()).throw(sqlite3.OperationalError("fail import")))
    data = [{"mac_address": "mac", "device_name": "dev", "owner": "owner"}]
    json_file = tmp_path / "data.json"
    json_file.write_text(json.dumps(data))
    with pytest.raises(sqlite3.OperationalError):
        stordb.import_db_from_json(str(json_file))
