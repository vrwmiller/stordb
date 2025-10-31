import os
import sys
import json
import logging
import sqlite3
import subprocess
import shutil
import datetime
from typing import Optional, Dict, Any


def export_db_to_vault(vault_file: str):
    """Export all secrets to a JSON file and encrypt it with Ansible vault."""
    import tempfile

    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            export_db_to_json(tmp.name)
            tmp.flush()
            password = os.getenv("VAULT_PASSWORD")
            if not password:
                import getpass

                password = getpass.getpass("Vault password: ")
            proc = subprocess.run(
                [
                    "ansible-vault",
                    "encrypt",
                    tmp.name,
                    "--output",
                    vault_file,
                    "--vault-password-file",
                    "-",
                ],
                input=password.encode(),
                capture_output=True,
            )
            if proc.returncode != 0:
                logger.error(f"Vault encryption failed: {proc.stderr.decode().strip()}")
                print("Error: Vault encryption failed. See log for details.")
                os.unlink(tmp.name)
                return
        os.unlink(tmp.name)
        logger.info(
            f"Exported and encrypted database to {vault_file}. No secrets or passwords logged."
        )
        print("Exported and encrypted database to {}.".format(vault_file))
    except Exception as e:
        logger.error(f"Vault export error: {e}")
        print("Error: Vault export failed. See log for details.")


def import_db_from_vault(vault_file: str):
    """Decrypt an Ansible vault file and import its contents into the database."""
    import tempfile

    try:
        password = os.getenv("VAULT_PASSWORD")
        if not password:
            import getpass

            password = getpass.getpass("Vault password: ")
        with tempfile.NamedTemporaryFile("w", delete=False) as tmp:
            proc = subprocess.run(
                ["ansible-vault", "view", vault_file, "--vault-password-file", "-"],
                input=password.encode(),
                capture_output=True,
            )
            if proc.returncode != 0:
                logger.error(f"Vault decryption failed: {proc.stderr.decode().strip()}")
                print("Error: Vault decryption failed. See log for details.")
                os.unlink(tmp.name)
                return
            tmp.write(proc.stdout.decode())
            tmp.flush()
            init_db()
            import_db_from_json(tmp.name)
        os.unlink(tmp.name)
        logger.info(f"Decrypted and imported database from {vault_file}.")
        print("Decrypted and imported database from {}.".format(vault_file))
    except Exception as e:
        logger.error(f"Vault import error: {e}")
        print("Error: Vault import failed. See log for details.")


"""
stordb.py - Secure Hardware & Secrets Database
"""


def setup_logger(debug=False):
    logger = logging.getLogger("stordb")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()
    if debug:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler("stordb.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logger(debug=False)

SCHEMA = """
CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT,
    device_name TEXT,
    owner TEXT,
    notes TEXT,
    secret_type TEXT,
    secret_value TEXT
);
"""


def get_db_connection(db_path: str = None):
    """Get a SQLite database connection."""
    try:
        if db_path is None:
            db_path = os.getenv("STORDB_DB_PATH", "stordb.sqlite3")
        return sqlite3.connect(db_path)
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        print(f"Error: Could not connect to database: {e}")
        raise


def init_db(db_path: str = None):
    """Initialize the database schema if not present."""
    conn = get_db_connection(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    conn.close()


def validate_json_input(data):
    """Validate imported JSON data for required fields."""
    if not isinstance(data, list):
        raise ValueError("JSON input must be a list of records.")
    required = {"mac_address", "device_name", "owner"}
    for i, entry in enumerate(data):
        missing = required - set(entry.keys())
        if missing:
            raise ValueError(
                f"Record {i} missing required fields: {', '.join(missing)}"
            )


def usage():
    print(
        """
Usage: stordb.py [OPTIONS]

Options:
    --init                       Initialize the database
    --add MAC NAME OWNER NOTES   Add a new device
    --lookup MAC                 Lookup device by MAC address
    --delete ID                  Delete device by ID
    --update ID FIELD=VALUE      Update device field
    --import-json FILE           Import devices/secrets from a JSON file
    --debug                      Enable debug output to STDOUT
    -h, --help                   Show this help message
    --backup-db [PATH]           Backup the database to PATH (or timestamped file)
    --restore-db PATH            Restore the database from backup file PATH
"""
    )
def backup_db(backup_path: str = None, db_path: str = None):
    """Backup the SQLite database to a file (default: timestamped in current dir)."""
    if db_path is None:
        db_path = os.getenv("STORDB_DB_PATH", "stordb.sqlite3")
    if not os.path.exists(db_path):
        logger.error(f"Backup failed: database file {db_path} does not exist.")
        print(f"Error: Database file {db_path} does not exist.")
        return
    if backup_path is None:
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{db_path}.backup_{ts}"
    try:
        shutil.copy2(db_path, backup_path)
        logger.info(f"DB BACKUP: {db_path} -> {backup_path}")
        print(f"Database backed up to {backup_path}.")
    except Exception as e:
        logger.error(f"DB BACKUP ERROR: {e}")
        print(f"Error: Could not backup database: {e}")

def restore_db(backup_path: str, db_path: str = None):
    """Restore the SQLite database from a backup file."""
    if db_path is None:
        db_path = os.getenv("STORDB_DB_PATH", "stordb.sqlite3")
    if not os.path.exists(backup_path):
        logger.error(f"Restore failed: backup file {backup_path} does not exist.")
        print(f"Error: Backup file {backup_path} does not exist.")
        return
    try:
        shutil.copy2(backup_path, db_path)
        logger.info(f"DB RESTORE: {backup_path} -> {db_path}")
        print(f"Database restored from {backup_path} to {db_path}.")
    except Exception as e:
        logger.error(f"DB RESTORE ERROR: {e}")
        print(f"Error: Could not restore database: {e}")


def setup_logger(debug=False):
    logger = logging.getLogger("stordb")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.handlers.clear()
    if debug:
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler("stordb.log")
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def add_secret(
    mac_address: str,
    device_name: str,
    owner: str,
    notes: str = "",
    secret_type: str = "mac",
    secret_value: str = "",
    db_path: str = None,
):
    # Validate required fields
    if not mac_address:
        logger.warning("Add secret failed: mac_address is required")
        raise ValueError("mac_address is required")
    if not device_name:
        logger.warning("Add secret failed: device_name is required")
        raise ValueError("device_name is required")
    if not owner:
        logger.warning("Add secret failed: owner is required")
        raise ValueError("owner is required")
    try:
        conn = get_db_connection(db_path)
        conn.execute(
            "INSERT INTO secrets (mac_address, device_name, owner, notes, secret_type, secret_value) VALUES (?, ?, ?, ?, ?, ?)",
            (mac_address, device_name, owner, notes, secret_type, secret_value),
        )
        conn.commit()
        conn.close()
        logger.info(
            f"DB TRANSACTION: add_secret device_name='{device_name}', owner='{owner}', secret_type='{secret_type}', mac_address='[REDACTED]', secret_value='[REDACTED]', id=[auto]"
        )
    except Exception as e:
        logger.error(f"DB TRANSACTION ERROR: add_secret device_name='{device_name}', owner='{owner}', error={e}")
        print(f"Error: Could not add secret: {e}")
        raise


def lookup_secret(
    mac_address: Optional[str] = None,
    device_name: Optional[str] = None,
    db_path: str = None,
) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    if mac_address:
        cursor.execute("SELECT * FROM secrets WHERE mac_address = ?", (mac_address,))
    elif device_name:
        cursor.execute("SELECT * FROM secrets WHERE device_name = ?", (device_name,))
    else:
        conn.close()
        return None
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(zip([d[0] for d in cursor.description], row))
    return None


def lookup_secrets_by_field(field: str, value: str, db_path: str = None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    query = f"SELECT * FROM secrets WHERE {field} = ?"
    cursor.execute(query, (value,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for row in rows:
        results.append(dict(zip([d[0] for d in cursor.description], row)))
    return results


def update_secret(id: int, updates: Dict[str, Any], db_path: str = None):
    try:
        conn = get_db_connection(db_path)
        fields = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [id]
        conn.execute(f"UPDATE secrets SET {fields} WHERE id = ?", values)
        conn.commit()
        conn.close()
        safe_updates = {k: ("[REDACTED]" if k in ("secret_value", "mac_address") else v) for k, v in updates.items()}
        logger.info(f"DB TRANSACTION: update_secret id={id}, updates={safe_updates}")
    except Exception as e:
        logger.error(f"DB TRANSACTION ERROR: update_secret id={id}, error={e}")
        print(f"Error: Could not update secret: {e}")
        raise


def delete_secret(id: int, db_path: str = None):
    try:
        conn = get_db_connection(db_path)
        conn.execute("DELETE FROM secrets WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        logger.info(f"DB TRANSACTION: delete_secret id={id}")
    except Exception as e:
        logger.error(f"DB TRANSACTION ERROR: delete_secret id={id}, error={e}")
        print(f"Error: Could not delete secret: {e}")
        raise


def import_json(json_file: str, db_path: str = None):
    logger.info(f"UI ACTION: import_json requested from {json_file}")
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"JSON load error in {json_file}: {e}")
        print(f"Error: Could not load JSON in {json_file}: {e}")
        return
    try:
        validate_json_input(data)
    except Exception as e:
        logger.error(f"JSON validation failed: {e}")
        print(f"Error: {e}")
        return
    count = 0
    for entry in data:
        try:
            mac = entry.get("mac_address", "")
            name = entry.get("device_name", "")
            owner = entry.get("owner", "")
            notes = entry.get("notes", "")
            secret_type = entry.get("secret_type", "mac")
            secret_value = entry.get("secret_value", "")
            add_secret(mac, name, owner, notes, secret_type, secret_value, db_path=db_path)
            count += 1
        except Exception as e:
            logger.error(f"DB TRANSACTION ERROR: import_json record device_name='{name}', owner='{owner}', error={e}")
            print(f"Error: Could not import record: {e}")
    logger.info(f"DB TRANSACTION: import_json imported {count} records from {json_file}")
    print(f"Imported {count} records from {json_file}.")


def export_db_to_json(json_file: str, db_path: str = None):
    """Export all secrets from the database to a JSON file."""
    logger.info(f"UI ACTION: export_db_to_json requested to {json_file}")
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM secrets")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in rows]
        conn.close()
        with open(json_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"DB TRANSACTION: export_db_to_json exported {len(data)} records to {json_file}")
        print(f"Exported {len(data)} records to {json_file}.")
    except Exception as e:
        logger.error(f"DB TRANSACTION ERROR: export_db_to_json to {json_file}, error={e}")
        print(f"Error: Could not export to JSON: {e}")
        raise


def import_db_from_json(json_file: str, db_path: str = None):
    """Import secrets from a JSON file into the database."""
    logger.info(f"UI ACTION: import_db_from_json requested from {json_file}")
    try:
        with open(json_file, "r") as f:
            data = json.load(f)
        validate_json_input(data)
        conn = get_db_connection(db_path)
        for entry in data:
            try:
                mac = entry.get("mac_address", "")
                name = entry.get("device_name", "")
                owner = entry.get("owner", "")
                notes = entry.get("notes", "")
                secret_type = entry.get("secret_type", "mac")
                secret_value = entry.get("secret_value", "")
                conn.execute(
                    "INSERT INTO secrets (mac_address, device_name, owner, notes, secret_type, secret_value) VALUES (?, ?, ?, ?, ?, ?)",
                    (mac, name, owner, notes, secret_type, secret_value),
                )
            except Exception as e:
                logger.error(f"DB TRANSACTION ERROR: import_db_from_json record device_name='{name}', owner='{owner}', error={e}")
                print(f"Error: Could not import record: {e}")
        conn.commit()
        conn.close()
        logger.info(f"DB TRANSACTION: import_db_from_json imported {len(data)} records from {json_file}")
        print(f"Imported {len(data)} records from {json_file}.")
    except Exception as e:
        logger.error(f"DB TRANSACTION ERROR: import_db_from_json from {json_file}, error={e}")
        print(f"Error: Could not import from JSON: {e}")
        raise


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="stordb: Secure Hardware & Secrets Database"
    )
    parser.add_argument("--init", action="store_true", help="Initialize the database")
    parser.add_argument(
        "--add",
        nargs=4,
        metavar=("MAC", "NAME", "OWNER", "NOTES"),
        help="Add a new device",
    )
    parser.add_argument("--lookup", metavar="MAC", help="Lookup device by MAC address")
    parser.add_argument("--owner", metavar="OWNER", help="Lookup device(s) by owner")
    parser.add_argument(
        "--device", metavar="NAME", help="Lookup device(s) by device name"
    )
    parser.add_argument("--delete", metavar="ID", type=int, help="Delete device by ID")
    parser.add_argument(
        "--update", nargs=2, metavar=("ID", "FIELD=VALUE"), help="Update device field"
    )
    parser.add_argument(
        "--import-json", metavar="FILE", help="Import devices/secrets from a JSON file"
    )
    parser.add_argument(
        "--export-json", metavar="FILE", help="Export all secrets to a JSON file"
    )
    parser.add_argument(
        "--import-db-json",
        metavar="FILE",
        help="Import secrets from a JSON file into the database (overwrites existing)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug output to STDOUT"
    )
    parser.add_argument(
        "--export-vault",
        metavar="VAULT_FILE",
        help="Export all secrets to an Ansible vault-encrypted file",
    )
    parser.add_argument(
        "--import-vault",
        metavar="VAULT_FILE",
        help="Import secrets from an Ansible vault-encrypted file",
    )
    parser.add_argument(
        "--backup-db",
        nargs="?",
        metavar="PATH",
        help="Backup the database to PATH (or timestamped file)",
    )
    parser.add_argument(
        "--restore-db",
        metavar="PATH",
        help="Restore the database from backup file PATH",
    )
    args = parser.parse_args()

    global logger
    logger = setup_logger(debug=args.debug)
    logger.info(f"UI ACTION: CLI started with args: {sys.argv[1:]}")

    if args.init:
        logger.info("UI ACTION: --init requested")
        init_db()
        logger.info("DB TRANSACTION: Database initialized.")
        print(json.dumps({"status": "Database initialized."}, indent=2))
    elif args.backup_db is not None:
        logger.info(f"UI ACTION: --backup-db requested to {args.backup_db}")
        backup_db(args.backup_db)
    elif args.restore_db:
        logger.info(f"UI ACTION: --restore-db requested from {args.restore_db}")
        restore_db(args.restore_db)
    elif args.add:
        mac, name, owner, notes = args.add
        logger.info(f"UI ACTION: --add requested for device_name={name}, owner={owner}")
        add_secret(mac, name, owner, notes)
        print(json.dumps({"status": f"Added device {name}."}, indent=2))
    elif args.lookup or args.owner or args.device:
        logger.info(f"UI ACTION: --lookup/--owner/--device requested")
        results = []
        if args.lookup:
            res = lookup_secret(mac_address=args.lookup)
            if res:
                results.append(res)
        if args.owner:
            results += lookup_secrets_by_field("owner", args.owner)
        if args.device:
            results += lookup_secrets_by_field("device_name", args.device)
        seen = set()
        deduped = []
        for r in results:
            if r and r.get("id") not in seen:
                deduped.append(dict(r))
                seen.add(r.get("id"))
        if deduped:
            print(json.dumps(deduped, indent=2))
        else:
            print(json.dumps({"status": "Not found."}, indent=2))
    elif args.delete:
        logger.info(f"UI ACTION: --delete requested for id={args.delete}")
        delete_secret(args.delete)
        print(json.dumps({"status": f"Deleted device with ID {args.delete}."}, indent=2))
    elif args.update:
        id, fieldval = args.update
        field, val = fieldval.split("=", 1)
        logger.info(f"UI ACTION: --update requested for id={id}, field={field}")
        update_secret(int(id), {field: val})
        print(json.dumps({"status": f"Updated device {id}: {field} -> {val}"}, indent=2))
    elif args.import_json:
        logger.info(f"UI ACTION: --import-json requested from {args.import_json}")
        import_json(args.import_json)
        print(json.dumps({"status": f"Imported from {args.import_json}"}, indent=2))
    elif args.export_json:
        logger.info(f"UI ACTION: --export-json requested to {args.export_json}")
        export_db_to_json(args.export_json)
    elif args.import_db_json:
        logger.info(f"UI ACTION: --import-db-json requested from {args.import_db_json}")
        init_db()  # Ensure DB exists and is empty
        import_db_from_json(args.import_db_json)
    elif args.export_vault:
        logger.info(f"UI ACTION: --export-vault requested to {args.export_vault}")
        export_db_to_vault(args.export_vault)
    elif args.import_vault:
        logger.info(f"UI ACTION: --import-vault requested from {args.import_vault}")
        import_db_from_vault(args.import_vault)
    else:
        usage()


if __name__ == "__main__":
    main()
