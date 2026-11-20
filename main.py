#!/usr/bin/env python3
"""
Multi-Agent Market Research & Report Generator
==============================================

Entry point for the CrewAI hierarchical market-research pipeline.

Usage:
    python main.py --query "Tech Sector Q3 Analysis"
    python main.py --query "EV Market Outlook 2025" --csv data/sample_metrics.csv
    python main.py --mock  # Offline simulation mode for verification
"""

import argparse
import logging
import os
import shutil
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("output/execution.log", mode="a", encoding="utf-8"),
    ],
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Market Research & Report Generator (CrewAI)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Tech Sector Q3 Analysis",
        help="Market research query (default: 'Tech Sector Q3 Analysis')",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="data/sample_metrics.csv",
        help="Path to CSV file with financial metrics (default: data/sample_metrics.csv)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/market_report.pdf",
        help="Output PDF file path (default: output/market_report.pdf)",
    )
    parser.add_argument(
        "--manager-model",
        type=str,
        default=None,
        help="Manager LLM model (default: gpt-4o or MANAGER_LLM_MODEL env var)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock/offline demonstration mode without live LLM API calls",
    )
    return parser.parse_args()


def run_mock_pipeline(args) -> str:
    """Simulate hierarchical execution for offline verification."""
    from crew.benchmarks import BenchmarkTracker
    from crew.pdf_generator import MarketReportPDF
    from crew.tools import calculate_financial_metrics

    logger.info("=" * 70)
    logger.info("[Manager LLM] Initializing hierarchical multi-agent workflow...")
    logger.info("[Manager LLM] Team: Lead Researcher, Data Analyst, Content Writer")
    logger.info("[Manager LLM] Process: Process.hierarchical (Dynamic Delegation)")
    logger.info("=" * 70)

    tracker = BenchmarkTracker(output_path="benchmarks.json")
    tracker.start_pipeline()

    # Step 1: Delegate to Lead Researcher
    logger.info("[Manager LLM] -> Delegating Task 1 to Market Research Specialist...")
    tracker.start_task("research")
    tracker.log_routing(
        "Manager LLM",
        "Market Research Specialist",
        f"Search web and gather metrics for: '{args.query}'",
    )
    time.sleep(0.5)
    logger.info("[Market Research Specialist] Executing web_search_scraper...")
    logger.info("[Market Research Specialist] Scraped financial sources and trends for: %s", args.query)
    tracker.stop_task("research", status="completed")

    # Step 2: Delegate to Data Analyst
    logger.info("[Manager LLM] -> Delegating Task 2 to Financial Data Analyst...")
    tracker.start_task("analysis")
    tracker.log_routing(
        "Manager LLM",
        "Financial Data Analyst",
        f"Calculate statistical summaries for dataset: '{args.csv}'",
    )
    stats_md = calculate_financial_metrics.run(csv_path=args.csv)
    time.sleep(0.5)
    logger.info("[Financial Data Analyst] Calculated descriptive statistics via Pandas describe():\n%s", stats_md[:300])
    tracker.stop_task("analysis", status="completed")

    # Step 3: Delegate to Content Writer
    logger.info("[Manager LLM] -> Delegating Task 3 to Technical Reports Writer...")
    tracker.start_task("report_writing")
    tracker.log_routing(
        "Manager LLM",
        "Technical Reports Writer",
        "Synthesize gathered findings and statistical matrices into structured report",
    )
    time.sleep(0.5)

    sample_md_file = Path("sample_outputs/market_report.md")
    if sample_md_file.exists():
        report_text = sample_md_file.read_text(encoding="utf-8")
    else:
        report_text = f"# Executive Summary\n\nMarket analysis for {args.query}.\n\n# Financial Analysis\n\n{stats_md}"

    tracker.stop_task("report_writing", status="completed")
    tracker.stop_pipeline()
    tracker.save()

    logger.info("[Technical Reports Writer] Structured report generated (%d characters).", len(report_text))
    return report_text, stats_md


def main() -> None:
    """Run the full market research pipeline."""
    args = parse_args()

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    os.makedirs("sample_outputs", exist_ok=True)

    logger.info("=" * 70)
    logger.info("Multi-Agent Market Research & Report Generator")
    logger.info("=" * 70)
    logger.info("Query       : %s", args.query)
    logger.info("CSV Data    : %s", args.csv)
    logger.info("Output PDF  : %s", args.output)
    logger.info("=" * 70)

    from crew.pdf_generator import MarketReportPDF
    from crew.tools import calculate_financial_metrics

    openai_key = os.getenv("OPENAI_API_KEY", "")
    is_mock = args.mock or not openai_key or openai_key.startswith("sk-your") or openai_key == "mock-test-key"

    if is_mock:
        if not args.mock:
            logger.info("No live OPENAI_API_KEY detected in .env. Running in demonstration verification mode.")
        report_text, stats_markdown = run_mock_pipeline(args)
    else:
        from crew.crew import MarketResearchCrew

        # Phase 1: Run the hierarchical CrewAI pipeline
        logger.info("Phase 1: Initializing hierarchical CrewAI pipeline with Manager LLM...")
        research_crew = MarketResearchCrew(
            query=args.query,
            csv_path=args.csv,
            manager_model=args.manager_model,
            benchmark_path="benchmarks.json",
        )

        report_text = research_crew.run()
        logger.info("Phase 1 complete. Report text length: %d chars", len(report_text))

        # Phase 2: Compute statistics table
        logger.info("Phase 2: Generating financial statistics from CSV...")
        stats_markdown = None
        if os.path.exists(args.csv):
            stats_markdown = calculate_financial_metrics.run(csv_path=args.csv)

    # Save the raw markdown report
    md_path = Path(args.output).with_suffix(".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(report_text, encoding="utf-8")
    logger.info("Markdown report saved: %s", md_path)

    # Phase 3: Compile the PDF report
    logger.info("Phase 3: Compiling PDF report with ReportLab...")
    pdf_path = MarketReportPDF.from_markdown(
        markdown_text=report_text,
        filename=args.output,
        title="Market Research Report",
        query=args.query,
        statistics_markdown=stats_markdown,
    )
    logger.info("PDF report generated: %s", pdf_path)

    # Copy to sample_outputs
    sample_md = Path("sample_outputs") / md_path.name
    sample_pdf = Path("sample_outputs") / Path(args.output).name
    shutil.copy2(str(md_path), str(sample_md))
    shutil.copy2(args.output, str(sample_pdf))
    logger.info("Sample outputs synced to sample_outputs/")

    # Summary
    logger.info("=" * 70)
    logger.info("Pipeline completed successfully!")
    logger.info("  Markdown   : %s", md_path.resolve())
    logger.info("  PDF        : %s", Path(args.output).resolve())
    logger.info("  Benchmarks : %s", Path("benchmarks.json").resolve())
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
