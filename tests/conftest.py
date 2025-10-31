import os
import pytest
import vault

@pytest.fixture(autouse=True)
def patch_vault_password(monkeypatch):
    os.environ["VAULT_PASSWORD"] = "testpass"
    monkeypatch.setattr(vault, "get_vault_password", lambda: "testpass")
