"""
vault.py - Ansible vault integration for stordb
"""

import os
import logging
from typing import Optional
from ansible.parsing.vault import VaultLib, VaultSecret
from ansible.constants import DEFAULT_VAULT_ID_MATCH

VAULT_PATH = os.getenv("STORDB_VAULT_PATH", "vault.ansible")
VAULT_PASSWORD = os.getenv("VAULT_PASSWORD")

# Setup logger for vault operations
vault_logger = logging.getLogger("vault")
vault_logger.setLevel(logging.INFO)
if not vault_logger.handlers:
    handler = logging.FileHandler("vault.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    vault_logger.addHandler(handler)

class VaultError(Exception):
    pass

def get_vault_password() -> str:
    if VAULT_PASSWORD:
        vault_logger.info("Vault password retrieved from environment variable.")
        return VAULT_PASSWORD
    import getpass
    vault_logger.info("Vault password requested interactively.")
    return getpass.getpass("Vault password: ")

def vault_encrypt(data: bytes, vault_path: str = VAULT_PATH) -> None:
    vault_logger.info(f"Vault encrypt requested for data of length {len(data)} to {vault_path}")
    password = get_vault_password()
    secret = VaultSecret(password.encode())
    vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, secret)])
    encrypted = vault.encrypt(data, secret)
    with open(vault_path, "wb") as f:
        f.write(encrypted)
    vault_logger.info(f"Vault encryption complete for {vault_path}. No secrets logged.")

def vault_decrypt(vault_path: str = VAULT_PATH) -> Optional[bytes]:
    vault_logger.info(f"Vault decrypt requested for {vault_path}")
    password = get_vault_password()
    secret = VaultSecret(password.encode())
    vault = VaultLib([(DEFAULT_VAULT_ID_MATCH, secret)])
    with open(vault_path, "rb") as f:
        encrypted_data = f.read()
    try:
        decrypted = vault.decrypt(encrypted_data)
        vault_logger.info(f"Vault decryption complete for {vault_path}. No secrets logged.")
        return decrypted
    except Exception as e:
        vault_logger.error(f"Vault decryption error for {vault_path}: {e}")
        raise VaultError(str(e))
