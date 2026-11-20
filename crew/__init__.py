"""
Multi-Agent Market Research & Report Generator - CrewAI Package

This package contains the CrewAI agent definitions, task configurations,
custom tools, PDF report generator, and execution benchmarking utilities.
"""

import os
import sys

# Ensure local writable appdata for CrewAI token manager in all environments
if sys.platform == "win32":
    local_app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".localappdata"))
    try:
        current_lad = os.environ.get("LOCALAPPDATA", "")
        test_dir = os.path.join(current_lad, "crewai_write_test")
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
    except Exception:
        os.environ["LOCALAPPDATA"] = local_app_dir
        os.makedirs(local_app_dir, exist_ok=True)

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")

from crew.agents import create_agents
from crew.tasks import create_tasks
from crew.crew import MarketResearchCrew
from crew.pdf_generator import MarketReportPDF
from crew.benchmarks import BenchmarkTracker

__all__ = [
    "create_agents",
    "create_tasks",
    "MarketResearchCrew",
    "MarketReportPDF",
    "BenchmarkTracker",
]
