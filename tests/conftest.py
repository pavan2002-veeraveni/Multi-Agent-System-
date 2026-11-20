"""Pytest configuration and global fixtures."""

import os
import sys

# Configure environment before any crewai imports
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
local_app_dir = os.path.join(workspace_root, ".localappdata")
os.makedirs(local_app_dir, exist_ok=True)

if sys.platform == "win32":
    try:
        current_lad = os.environ.get("LOCALAPPDATA", "")
        test_dir = os.path.join(current_lad, "crewai_write_test")
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
    except Exception:
        os.environ["LOCALAPPDATA"] = local_app_dir

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")
os.environ.setdefault("OPENAI_API_KEY", "mock-test-key")
