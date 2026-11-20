"""
Automated Tests — Execution Benchmarks & Analytics

Verifies that the BenchmarkTracker:
  1. Tracks pipeline timing accurately.
  2. Tracks individual task timing and status.
  3. Records task routing delegation history.
  4. Saves valid, well-formed benchmarks.json output.
"""

import os
import json
import time
import pytest
from crew.benchmarks import BenchmarkTracker


@pytest.fixture
def temp_benchmark_path(tmp_path):
    """Temporary file path for benchmarking output."""
    return str(tmp_path / "test_benchmarks.json")


class TestBenchmarkTracker:
    """Test suite for BenchmarkTracker."""

    def test_pipeline_timing(self, temp_benchmark_path):
        """Pipeline start and stop must calculate valid elapsed time."""
        tracker = BenchmarkTracker(output_path=temp_benchmark_path)
        tracker.start_pipeline()
        time.sleep(0.05)
        tracker.stop_pipeline()

        summary = tracker.get_summary()
        assert summary["pipeline_total_seconds"] is not None
        assert summary["pipeline_total_seconds"] >= 0.04

    def test_task_lifecycle_timing(self, temp_benchmark_path):
        """Task start and stop must record duration and completion status."""
        tracker = BenchmarkTracker(output_path=temp_benchmark_path)
        tracker.start_task("research")
        time.sleep(0.05)
        tracker.stop_task("research", status="completed")

        summary = tracker.get_summary()
        tasks = summary["task_benchmarks"]
        assert len(tasks) == 1
        assert tasks[0]["task"] == "research"
        assert tasks[0]["status"] == "completed"
        assert tasks[0]["duration_seconds"] >= 0.04

    def test_routing_history_logging(self, temp_benchmark_path):
        """Routing entries must be recorded with timestamp, from, to, and task."""
        tracker = BenchmarkTracker(output_path=temp_benchmark_path)
        tracker.log_routing("Manager LLM", "Market Research Specialist", "Scrape Q3 Data")
        tracker.log_routing("Manager LLM", "Financial Data Analyst", "Run Pandas summary")

        summary = tracker.get_summary()
        history = summary["routing_history"]
        assert len(history) == 2
        assert history[0]["from"] == "Manager LLM"
        assert history[0]["to"] == "Market Research Specialist"
        assert history[1]["to"] == "Financial Data Analyst"

    def test_save_to_json(self, temp_benchmark_path):
        """Tracker must persist a valid JSON file matching schema requirements."""
        tracker = BenchmarkTracker(output_path=temp_benchmark_path)
        tracker.start_pipeline()
        tracker.start_task("data_analysis")
        tracker.stop_task("data_analysis")
        tracker.log_routing("Manager LLM", "Financial Data Analyst", "Analyze CSV")
        tracker.stop_pipeline()

        saved_path = tracker.save()
        assert os.path.exists(saved_path)

        with open(saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "pipeline_total_seconds" in data
        assert "task_benchmarks" in data
        assert "routing_history" in data
        assert "summary" in data
        assert data["summary"]["total_tasks"] == 1
        assert data["summary"]["total_routing_events"] == 1
