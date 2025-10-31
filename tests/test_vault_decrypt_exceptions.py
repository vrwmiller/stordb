"""
test_vault_decrypt_exceptions.py - Test exception handling in vault_decrypt for multiple error types
"""
import pytest
import vault

class DummyVaultLib:
    def __init__(self, exc):
        self.exc = exc
    def decrypt(self, encrypted_data):
        raise self.exc

def test_vault_decrypt_value_error(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    monkeypatch.setattr(vault, "VaultLib", lambda *a, **k: DummyVaultLib(ValueError("bad value")))
    vault_file = tmp_path / "dummy.vault"
    vault_file.write_bytes(b"dummy")
    with pytest.raises(vault.VaultError) as excinfo:
        vault.vault_decrypt(vault_path=str(vault_file))
    assert "bad value" in str(excinfo.value)

def test_vault_decrypt_type_error(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    monkeypatch.setattr(vault, "VaultLib", lambda *a, **k: DummyVaultLib(TypeError("wrong type")))
    vault_file = tmp_path / "dummy.vault"
    vault_file.write_bytes(b"dummy")
    with pytest.raises(vault.VaultError) as excinfo:
        vault.vault_decrypt(vault_path=str(vault_file))
    assert "wrong type" in str(excinfo.value)

def test_vault_decrypt_runtime_error(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    monkeypatch.setattr(vault, "VaultLib", lambda *a, **k: DummyVaultLib(RuntimeError("runtime fail")))
    vault_file = tmp_path / "dummy.vault"
    vault_file.write_bytes(b"dummy")
    with pytest.raises(vault.VaultError) as excinfo:
        vault.vault_decrypt(vault_path=str(vault_file))
    assert "runtime fail" in str(excinfo.value)
