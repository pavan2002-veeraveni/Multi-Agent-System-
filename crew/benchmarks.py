"""
Execution Benchmarking & Analytics

Captures and logs execution metrics for each agent task, including
timing data and task routing history. Writes results to benchmarks.json.
"""

import json
import time
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BenchmarkTracker:
    """Tracks execution timing and task delegation for the CrewAI pipeline."""

    def __init__(self, output_path: str = "benchmarks.json"):
        self.output_path = Path(output_path)
        self.records: list[dict[str, Any]] = []
        self.routing_history: list[dict[str, str]] = []
        self._active_timers: dict[str, float] = {}
        self.pipeline_start: float | None = None
        self.pipeline_end: float | None = None

    def start_pipeline(self) -> None:
        """Mark the start of the full pipeline execution."""
        self.pipeline_start = time.time()
        logger.info("Pipeline execution started at %s", datetime.now(timezone.utc).isoformat())

    def stop_pipeline(self) -> None:
        """Mark the end of the full pipeline execution."""
        self.pipeline_end = time.time()
        logger.info("Pipeline execution completed at %s", datetime.now(timezone.utc).isoformat())

    def start_task(self, task_name: str) -> None:
        """Begin timing a named task."""
        self._active_timers[task_name] = time.time()
        self.records.append({
            "task": task_name,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "status": "running",
        })
        logger.info("Task started: %s", task_name)

    def stop_task(self, task_name: str, status: str = "completed") -> None:
        """Stop timing a named task and record duration."""
        start = self._active_timers.pop(task_name, None)
        if start is None:
            logger.warning("No active timer found for task: %s", task_name)
            return

        elapsed = round(time.time() - start, 3)

        # Update the matching record
        for record in reversed(self.records):
            if record["task"] == task_name and record["status"] == "running":
                record["duration_seconds"] = elapsed
                record["end_time"] = datetime.now(timezone.utc).isoformat()
                record["status"] = status
                break

        logger.info("Task completed: %s (%.3fs)", task_name, elapsed)

    def log_routing(self, from_agent: str, to_agent: str, task_description: str) -> None:
        """Record a task delegation event in the routing history."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": from_agent,
            "to": to_agent,
            "task": task_description,
        }
        self.routing_history.append(entry)
        logger.info("Task routed: %s -> %s (%s)", from_agent, to_agent, task_description)

    def task_callback(self, task_output) -> None:
        """
        CrewAI task callback handler.

        Called automatically by CrewAI after each task completes.
        Logs the task completion and records routing information.
        """
        task_desc = getattr(task_output, "description", "unknown_task")
        agent_name = getattr(task_output, "agent", "unknown_agent")

        # Log routing from manager to the executing agent
        self.log_routing("Manager LLM", str(agent_name), str(task_desc)[:100])

        # If we have an active timer for this description, stop it
        for timer_name in list(self._active_timers.keys()):
            if timer_name in str(task_desc):
                self.stop_task(timer_name)
                break

    def get_summary(self) -> dict[str, Any]:
        """Generate a summary of all benchmark data."""
        total_duration = None
        if self.pipeline_start and self.pipeline_end:
            total_duration = round(self.pipeline_end - self.pipeline_start, 3)

        return {
            "pipeline_total_seconds": total_duration,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "task_benchmarks": self.records,
            "routing_history": self.routing_history,
            "summary": {
                "total_tasks": len(self.records),
                "completed_tasks": sum(
                    1 for r in self.records if r.get("status") == "completed"
                ),
                "total_routing_events": len(self.routing_history),
            },
        }

    def save(self, filepath: str | None = None) -> str:
        """Persist benchmark data to a JSON file."""
        path = Path(filepath) if filepath else self.output_path
        data = self.get_summary()

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Benchmarks saved to %s", path)
        return str(path)
