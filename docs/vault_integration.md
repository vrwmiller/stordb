# Ansible Vault Integration for stordb

## Overview
stordb supports secure export and import of the secrets database using Ansible vault encryption (AES256). This ensures all secrets are protected at rest and only accessible with the correct vault password.

## Exporting the Database to a Vault File
To export all secrets and encrypt them with Ansible vault:

```bash
python stordb.py --export-vault vault.ansible
```
You will be prompted for the vault password if `VAULT_PASSWORD` is not set in your environment.

## Importing the Database from a Vault File
To decrypt a vault file and import its contents into the database:

```bash
python stordb.py --import-vault vault.ansible
```
You will be prompted for the vault password if `VAULT_PASSWORD` is not set.

## How It Works
- The database is exported to a temporary JSON file.
- The JSON file is encrypted using the `ansible-vault` CLI.
- For import, the vault file is decrypted to a temporary JSON file and loaded into the database.
- Temporary files are securely deleted after use.

## Security Notes
- Plaintext secrets are only present in memory and secure temporary files during export/import.
- Never store or log vault passwords or decrypted secrets.
- Only `mac_address` and `secret_value` fields are redacted in logs and CLI output; owner and device name are shown for usability.
- All vault operations include robust error handling for subprocess failures and corrupt files.
- Always use strong vault passwords and restrict access to vault files.

## CLI Options
- `--export-vault VAULT_FILE`: Export and encrypt secrets to a vault file.
- `--import-vault VAULT_FILE`: Decrypt and import secrets from a vault file.

## See Also
- [`stordb.py`](../stordb.py): Main CLI and database logic
- [`vault.py`](../vault.py): Vault helper functions
- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/user_guide/vault.html)
