"""
test_logging.py - Tests for logging in stordb.py and vault.py
"""
import os
import logging
import tempfile
import stordb
import vault
import pytest

def read_log(log_path):
    with open(log_path, "r") as f:
        return f.read()

def test_stordb_add_secret_logs(tmp_path, monkeypatch):
    log_path = tmp_path / "stordb.log"
    monkeypatch.setenv("STORDB_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(stordb, "logger", logging.getLogger("stordb_test"))
    stordb.logger.handlers.clear()
    handler = logging.FileHandler(str(log_path))
    stordb.logger.addHandler(handler)
    stordb.logger.setLevel(logging.INFO)
    stordb.init_db()
    stordb.add_secret("mac1", "dev1", "owner1")
    handler.flush()
    log_content = read_log(log_path)
    assert "DB TRANSACTION: add_secret" in log_content
    assert "device_name='dev1'" in log_content
    assert "owner='owner1'" in log_content
    assert "[REDACTED]" in log_content
    assert "mac1" not in log_content

def test_stordb_update_secret_logs(tmp_path, monkeypatch):
    log_path = tmp_path / "stordb.log"
    monkeypatch.setenv("STORDB_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(stordb, "logger", logging.getLogger("stordb_test"))
    stordb.logger.handlers.clear()
    handler = logging.FileHandler(str(log_path))
    stordb.logger.addHandler(handler)
    stordb.logger.setLevel(logging.INFO)
    stordb.init_db()
    stordb.add_secret("mac2", "dev2", "owner2")
    stordb.update_secret(1, {"owner": "newowner", "secret_value": "supersecret"})
    handler.flush()
    log_content = read_log(log_path)
    assert "DB TRANSACTION: update_secret" in log_content
    assert "id=1" in log_content
    assert "[REDACTED]" in log_content
    assert "supersecret" not in log_content

def test_stordb_delete_secret_logs(tmp_path, monkeypatch):
    log_path = tmp_path / "stordb.log"
    monkeypatch.setenv("STORDB_DB_PATH", str(tmp_path / "test.sqlite"))
    monkeypatch.setattr(stordb, "logger", logging.getLogger("stordb_test"))
    stordb.logger.handlers.clear()
    handler = logging.FileHandler(str(log_path))
    stordb.logger.addHandler(handler)
    stordb.logger.setLevel(logging.INFO)
    stordb.init_db()
    stordb.add_secret("mac3", "dev3", "owner3")
    stordb.delete_secret(1)
    handler.flush()
    log_content = read_log(log_path)
    assert "DB TRANSACTION: delete_secret" in log_content
    assert "id=1" in log_content
    assert "mac3" not in log_content

def test_vault_encrypt_decrypt_logs(tmp_path, monkeypatch):
    log_path = tmp_path / "vault.log"
    monkeypatch.setenv("VAULT_PASSWORD", "testpass")
    monkeypatch.setattr(vault, "vault_logger", logging.getLogger("vault_test"))
    vault.vault_logger.handlers.clear()
    handler = logging.FileHandler(str(log_path))
    vault.vault_logger.addHandler(handler)
    vault.vault_logger.setLevel(logging.INFO)
    data = b"secretdata"
    vault_path = tmp_path / "vault.ansible"
    vault.vault_encrypt(data, str(vault_path))
    handler.flush()
    log_content = read_log(log_path)
    assert "Vault encrypt requested" in log_content
    assert "Vault encryption complete" in log_content
    assert "secretdata" not in log_content
    # Decrypt
    vault.vault_decrypt(str(vault_path))
    handler.flush()
    log_content = read_log(log_path)
    assert "Vault decrypt requested" in log_content
    assert "Vault decryption complete" in log_content
    assert "secretdata" not in log_content
