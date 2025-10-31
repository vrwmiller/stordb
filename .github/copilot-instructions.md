
# stordb Copilot Instructions

## Python Code Style & Linting
- Use 4 spaces per indentation level (never tabs).
- Keep all branches (if/elif/else) aligned inside functions.
- Place helper functions and classes at module level.
- Run a linter (flake8) and formatter (black) after major edits.
- Avoid mixing tabs and spaces; ensure PEP8 compliance unless exceptions are documented.
- Use descriptive names; single-letter names only for loop indices.
- Add docstrings to all public functions/classes.

## Project Conventions
- No emojis in code, docs, or comments.
- Python scripts use `.py` extension and 4-space indentation.
- Use docstrings and inline comments as needed.
- Manage dependencies with `requirements.txt`.
- Main script for user interaction: `stordb.py.
- The ansible vault is the stordb sqlite database.

## Secrets & Configuration
- Never hard-code vault passwords or sensitive data.
- Use environment variables for credentials (e.g., `VAULT_PASSWORD`).
- Read vault passwords from environment or prompt interactively; never log or store in plaintext.
- Error messages must not leak sensitive info or vault contents.
- Process encrypted data in memory only; do not create temp files.

## Key Workflows
**Run locally:**
```bash
python3 -m venv venv && source venv/bin/activate
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```
**Test the application:**
```bash
source venv/bin/activate
python run_tests.py
# Or run specific tests
python -m pytest tests/ -v
```

## GitHub CLI Issue Creation
- Always use `--body-file` with `gh issue create` to avoid quoting errors and preserve formatting.
- Example:
  1. Write issue body to a file (e.g., `issue.txt`).
  2. Run:
     ```bash
     gh issue create --title "Your Issue Title" --body-file issue.txt
     ```

## Performance & Efficiency
- Optimize memory usage for large vault files.
- Use efficient string operations for JSON parsing and pattern matching.
- Minimize file I/O; process data in memory when possible.
- Consider lazy loading for very large datasets.

## Security & Privacy
- Never write/store passwords or other secrets in repo, logs, or error messages.
- Mask/redact sensitive vault data before logging.
- Decrypted vault contents must only be processed in memory.
- Use secure practices for Ansible vault operations and credentials.
- Validate input and handle edge cases to prevent vulnerabilities.

## Testing & Mocks
- Isolate all Ansible vault operations behind interfaces for mocking in unit tests.
- Provide test fixtures for:
  - Mocked vault decryption
  - Sample CSV data (varied formats, edge cases)
  - Error conditions (file not found, decryption failures, malformed data)
- Write integration tests for full workflow (no real vault files required).
- Use deterministic test data and mock Ansible vault components for consistent results.
- Test edge cases: empty files, invalid CSV, special characters in data.
