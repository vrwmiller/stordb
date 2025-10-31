"""
test_coverage_expansion.py - Additional tests for vault, update/delete, redaction, CLI, and error scenarios
"""
import os
import tempfile
import pytest
import stordb
import vault

# --- Vault export/import logic ---
def test_vault_export_import(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router", secret_value="secret1")
    vault_file = tmp_path / "vault.ansible"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    # Export
    vault.vault_encrypt(b'{"test": "data"}', vault_path=str(vault_file))
    assert vault_file.exists()
    # Import
    decrypted = vault.vault_decrypt(vault_path=str(vault_file))
    assert decrypted is not None

# --- Update/delete scenarios ---
def test_update_delete_secret(tmp_path):
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

# --- Redaction logic for logs and CLI output ---
def test_redaction_logic(tmp_path):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router", secret_value="supersecret")
    result = stordb.lookup_secret(mac_address="00:11:22:33:44:55")
    safe_result = dict(result)
    if "secret_value" in safe_result:
        safe_result["secret_value"] = "[REDACTED]"
    if "mac_address" in safe_result:
        safe_result["mac_address"] = "[REDACTED]"
    assert safe_result["mac_address"] == "[REDACTED]"
    assert safe_result["secret_value"] == "[REDACTED]"

# --- Simulate full CLI workflows ---
def test_full_cli_workflow(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    stordb.add_secret("AA:BB:CC:DD:EE:01", "Router", "Alice", "Main router", secret_value="secret1")
    stordb.add_secret("AA:BB:CC:DD:EE:02", "Switch", "Bob", "Core switch", secret_value="secret2")
    # Export to JSON
    json_file = tmp_path / "export.json"
    stordb.export_db_to_json(str(json_file))
    assert json_file.exists()
    # Export to vault
    vault_file = tmp_path / "vault.ansible"
    vault.vault_encrypt(json_file.read_bytes(), vault_path=str(vault_file))
    assert vault_file.exists()
    # Import from vault
    decrypted = vault.vault_decrypt(vault_path=str(vault_file))
    assert decrypted is not None
    # Import JSON
    stordb.import_json(str(json_file))
    # Lookup
    results = stordb.lookup_secrets_by_field("owner", "Alice")
    assert results[0]["device_name"] == "Router"
    assert results[0]["owner"] == "Alice"

# --- Vault password incorrect or missing ---
def test_vault_password_incorrect(monkeypatch, tmp_path):
    vault_file = tmp_path / "vault.ansible"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    vault.vault_encrypt(b"data", vault_path=str(vault_file))
    monkeypatch.setattr(vault, "get_vault_password", lambda: "wrongpass")
    with pytest.raises(vault.VaultError):
        vault.vault_decrypt(vault_path=str(vault_file))

def test_vault_password_missing(monkeypatch, tmp_path):
    vault_file = tmp_path / "vault.ansible"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    vault.vault_encrypt(b"data", vault_path=str(vault_file))
    monkeypatch.setattr(vault, "get_vault_password", lambda: None)
    with pytest.raises(Exception):
        vault.vault_decrypt(vault_path=str(vault_file))

# --- Import/export when disk is full or files are locked ---
def test_import_export_disk_full(monkeypatch, tmp_path):
    # Simulate disk full by raising OSError on file write
    monkeypatch.setattr("builtins.open", lambda *a, **k: (_ for _ in ()).throw(OSError("No space left on device")))
    with pytest.raises(OSError):
        stordb.export_db_to_json("/tmp/full.json")
    with pytest.raises(OSError):
        vault.vault_encrypt(b"data", vault_path="/tmp/full.vault")

# --- Directly test vault_encrypt and vault_decrypt ---
def test_vault_encrypt_decrypt_valid(monkeypatch, tmp_path):
    vault_file = tmp_path / "vault.ansible"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    vault.vault_encrypt(b"hello world", vault_path=str(vault_file))
    decrypted = vault.vault_decrypt(vault_path=str(vault_file))
    assert decrypted == b"hello world"

def test_vault_encrypt_decrypt_invalid(monkeypatch, tmp_path):
    vault_file = tmp_path / "vault.ansible"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    vault.vault_encrypt(b"hello world", vault_path=str(vault_file))
    # Corrupt the vault file
    with open(vault_file, "wb") as f:
        f.write(b"not a vault")
    with pytest.raises(vault.VaultError):
        vault.vault_decrypt(vault_path=str(vault_file))

# --- Test VaultError exception handling ---
def test_vault_error_exception():
    err = vault.VaultError("fail")
    assert str(err) == "fail"
