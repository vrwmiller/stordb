"""
run_tests.py - Script to run all tests for stordb
"""
import pytest
import sys

if __name__ == "__main__":
    sys.exit(pytest.main(["tests"]))
