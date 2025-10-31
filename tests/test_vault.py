"""
test_vault.py - Mocks and tests for vault integration (Ansible Python API)
"""
import pytest
import vault

class DummyVaultLib:
    def __init__(self, should_fail=False, decrypted_data=b"data"):
        self.should_fail = should_fail
        self.decrypted_data = decrypted_data
    def decrypt(self, encrypted_data):
        if self.should_fail:
            raise Exception("fail")
        return self.decrypted_data
    def encrypt(self, data, secret):
        if self.should_fail:
            raise Exception("fail")
        return b"encrypted"

def test_vault_decrypt_success(monkeypatch):
    import tempfile
    import os
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    monkeypatch.setattr(vault, "VaultLib", lambda *a, **k: DummyVaultLib())
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = os.path.join(tmpdir, "dummy.vault")
        with open(vault_path, "wb") as f:
            f.write(b"dummy")
        result = vault.vault_decrypt(vault_path=vault_path)
        assert result == b"data"

def test_vault_decrypt_failure(monkeypatch):
    import tempfile
    import os
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    monkeypatch.setattr(vault, "VaultLib", lambda *a, **k: DummyVaultLib(should_fail=True))
    with tempfile.TemporaryDirectory() as tmpdir:
        vault_path = os.path.join(tmpdir, "dummy.vault")
        with open(vault_path, "wb") as f:
            f.write(b"dummy")
        try:
            vault.vault_decrypt(vault_path=vault_path)
        except vault.VaultError as e:
            assert "fail" in str(e)
        else:
            assert False, "VaultError not raised"

def test_export_db_to_vault_subprocess_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router")
    class FailingProc:
        def run(self, *a, **k):
            return DummyProc(returncode=1, stderr=b"encryption failed")
    monkeypatch.setattr(stordb, "subprocess", FailingProc())
    vault_file = tmp_path / "vault.ansible"
    stordb.export_db_to_vault(str(vault_file))
    # Should not raise, but print error and not create vault file
    assert not vault_file.exists()
def test_import_db_from_vault_subprocess_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    class FailingProc:
        def run(self, *a, **k):
            return DummyProc(returncode=1, stderr=b"decryption failed")
    monkeypatch.setattr(stordb, "subprocess", FailingProc())
    vault_file = tmp_path / "vault.ansible"
    vault_file.write_text("dummy")
    stordb.import_db_from_vault(str(vault_file))
def test_import_db_from_vault_missing_file(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    vault_file = tmp_path / "missing.ansible"
    try:
        stordb.import_db_from_vault(str(vault_file))
    except Exception as e:
        assert "No such file" in str(e) or "not found" in str(e)
def test_import_db_from_vault_corrupt_json(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    class CorruptProc:
        def run(self, *a, **k):
            return DummyProc(stdout=b"not a json", returncode=0)
    monkeypatch.setattr(stordb, "subprocess", CorruptProc())
    vault_file = tmp_path / "vault.ansible"
    vault_file.write_text("dummy")
    stordb.import_db_from_vault(str(vault_file))
import tempfile
import os
import stordb
class DummyProc:
    def __init__(self, returncode=0, stdout=b"[{}]", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
    def run(self, *args, **kwargs):
        return self
def test_export_db_to_vault(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    stordb.add_secret("00:11:22:33:44:55", "Router", "Alice", "Main router")
    class DummyProc:
        def run(self, *a, **k):
            # Simulate vault file creation
            for arg in a[0]:
                if isinstance(arg, str) and arg.endswith(".ansible"):
                    open(arg, "w").write("dummy vault content")
            return self
    monkeypatch.setattr(stordb, "subprocess", DummyProc())
    vault_file = tmp_path / "vault.ansible"
    stordb.export_db_to_vault(str(vault_file))
    assert vault_file.exists()
def test_import_db_from_vault(monkeypatch, tmp_path):
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    monkeypatch.setattr(stordb, "subprocess", DummyProc(stdout=b"[]"))
    vault_file = tmp_path / "vault.ansible"
    vault_file.write_text("dummy")
    stordb.import_db_from_vault(str(vault_file))
"""
test_vault.py - Mocks and tests for vault integration
"""
import pytest
import vault

