"""
Test that Bandit security checks run and report issues for intentionally insecure code.
These tests do not validate Bandit itself, but ensure Bandit can be run and detects known issues.
"""
import subprocess
import sys
import os
import tempfile

def test_bandit_detects_insecure_code():
    # Create a temporary Python file with a known Bandit issue (use of exec)
    insecure_code = """
def run():
    exec("print('hello')")
"""
    import time
    temp_fd, temp_path = tempfile.mkstemp(suffix=".py")
    with os.fdopen(temp_fd, "w") as f:
        f.write(insecure_code)
        f.flush()
    print(f"Bandit test temp file path: {temp_path}")
    try:
        result = subprocess.run([
            'bandit', '-q', '-r', temp_path
        ], capture_output=True, text=True)
        # Bandit should report at least one issue
        if not ("exec_used" in result.stdout or "Use of exec detected" in result.stdout or "exec_used" in result.stderr or "Use of exec detected" in result.stderr):
            print(f"Bandit returncode: {result.returncode}")
            print(f"Bandit stdout: {result.stdout}")
            print(f"Bandit stderr: {result.stderr}")
        assert "exec_used" in result.stdout or "Use of exec detected" in result.stdout or "exec_used" in result.stderr or "Use of exec detected" in result.stderr
    finally:
        print(f"Temp file left for manual inspection: {temp_path}")
        # os.remove(temp_path)  # Commented out for debugging

def test_bandit_clean_code():
    # Create a temporary Python file with no Bandit issues
    clean_code = """
def run():
    print('hello')
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(clean_code)
        temp_path = f.name
    try:
        result = subprocess.run([
            sys.executable, '-m', 'bandit', '-q', '-r', temp_path
        ], capture_output=True, text=True)
        # Bandit should not report 'exec' issue
        assert "exec" not in result.stdout and "exec" not in result.stderr
    finally:
        os.remove(temp_path)
