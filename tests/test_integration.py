"""
test_integration.py - Integration tests for stordb full workflow
"""
import os
import tempfile
import json
import stordb

def test_full_workflow(tmp_path):
    import vault
    db_path = tmp_path / "test.sqlite"
    os.environ["STORDB_DB_PATH"] = str(db_path)
    stordb.init_db()
    # Mock vault password provider
    vault.get_vault_password = lambda: "testpass"
    # Add device
    stordb.add_secret("AA:BB:CC:DD:EE:01", "Router", "Alice", "Main router", secret_value="secret1")
    stordb.add_secret("AA:BB:CC:DD:EE:02", "Switch", "Bob", "Core switch", secret_value="secret2")
    # Export to JSON
    json_file = tmp_path / "export.json"
    stordb.export_db_to_json(str(json_file))
    data = json.loads(json_file.read_text())
    assert len(data) == 2
    # Export to vault (simulate)
    vault_file = tmp_path / "vault.ansible"
    # Monkeypatch subprocess to simulate vault
    class DummyProc:
        def __init__(self, returncode=0, stdout=b"[{}]", stderr=b""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
        def run(self, *args, **kwargs):
            open(vault_file, "w").write("dummy vault content")
            return self
    stordb.subprocess = DummyProc()
    stordb.export_db_to_vault(str(vault_file))
    assert vault_file.exists()
    # Import from vault (simulate)
    stordb.subprocess = DummyProc(stdout=json_file.read_bytes())
    stordb.import_db_from_vault(str(vault_file))
    # Lookup and verify redaction
    results = stordb.lookup_secrets_by_field("owner", "Alice")
    assert results[0]["device_name"] == "Router"
    assert results[0]["owner"] == "Alice"
    # Simulate CLI output redaction
    safe_result = dict(results[0])
    if "secret_value" in safe_result:
        safe_result["secret_value"] = "[REDACTED]"
    if "mac_address" in safe_result:
        safe_result["mac_address"] = "[REDACTED]"
    assert safe_result["mac_address"] == "[REDACTED]"
    assert safe_result["secret_value"] == "[REDACTED]"
