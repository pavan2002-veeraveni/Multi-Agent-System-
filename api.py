"""
REST API Endpoints for Multi-Agent Market Research & Report Generator
=====================================================================

Provides a production FastAPI interface exposing HTTP endpoints to trigger
hierarchical market research workflows, retrieve generated reports, download
compiled PDFs, inspect execution benchmarks, and compute Pandas metrics.

Run server:
    python api.py
    # or: uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

# Ensure local writable appdata
if sys.platform == "win32":
    local_app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".localappdata"))
    os.environ.setdefault("LOCALAPPDATA", local_app_dir)
os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")

from crew.pdf_generator import MarketReportPDF
from crew.tools import calculate_financial_metrics
from crew.benchmarks import BenchmarkTracker

logger = logging.getLogger("api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Multi-Agent Market Research & Report Generator API",
    description="REST API for orchestrating CrewAI hierarchical agents, compiling ReportLab PDFs, and logging execution analytics.",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class ResearchRequest(BaseModel):
    query: str = Field(
        default="Tech Sector Q3 Analysis",
        description="The topic or industry sector for market research.",
        examples=["Tech Sector Q3 Analysis"],
    )
    csv_path: Optional[str] = Field(
        default="data/sample_metrics.csv",
        description="Relative or absolute path to corporate financial metrics CSV.",
        examples=["data/sample_metrics.csv"],
    )
    manager_model: Optional[str] = Field(
        default="gpt-4o",
        description="Manager LLM model identifier for hierarchical supervision.",
        examples=["gpt-4o"],
    )
    mock: Optional[bool] = Field(
        default=False,
        description="Force simulation mode for offline testing without live LLM calls.",
        examples=[False],
    )


class MetricsRequest(BaseModel):
    csv_path: str = Field(
        default="data/sample_metrics.csv",
        description="Path to CSV dataset for descriptive statistical parsing.",
        examples=["data/sample_metrics.csv"],
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["General"])
def root():
    """API overview and list of available endpoints."""
    return {
        "service": "Multi-Agent Market Research & Report Generator API",
        "version": "1.0.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "POST /api/research": "Run hierarchical market research pipeline",
            "GET  /api/reports/download": "Download compiled PDF market report",
            "GET  /api/reports/markdown": "View generated Markdown report",
            "GET  /api/benchmarks": "Retrieve task execution benchmarks and routing history",
            "POST /api/metrics/calculate": "Compute Pandas summary statistics on CSV dataset",
            "GET  /health": "Health check endpoint",
        },
    }


@app.get("/health", tags=["General"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "multi-agent-crewai"}


@app.post("/api/research", tags=["Research & Reports"])
def run_research(request: ResearchRequest):
    """
    Execute the multi-agent market research pipeline for a given query.

    **Inputs:**
    - `query`: Target sector or topic (e.g. 'Tech Sector Q3 Analysis')
    - `csv_path`: Path to corporate financial metrics CSV (default: 'data/sample_metrics.csv')
    - `manager_model`: LLM supervisor model (default: 'gpt-4o')
    - `mock`: Optional boolean to force offline demonstration mode

    **Outputs:**
    - Status message
    - Execution timings
    - Preview of generated report
    - Download links for PDF and Markdown deliverables
    """
    os.makedirs("output", exist_ok=True)
    os.makedirs("sample_outputs", exist_ok=True)

    openai_key = os.getenv("OPENAI_API_KEY", "")
    is_mock = request.mock or not openai_key or openai_key.startswith("sk-your") or openai_key == "mock-test-key"

    stats_markdown = None
    if os.path.exists(request.csv_path):
        stats_markdown = calculate_financial_metrics.run(csv_path=request.csv_path)

    tracker = BenchmarkTracker(output_path="benchmarks.json")
    tracker.start_pipeline()

    if is_mock:
        tracker.start_task("research")
        tracker.log_routing("Manager LLM", "Market Research Specialist", f"Web search for {request.query}")
        tracker.stop_task("research", "completed")

        tracker.start_task("analysis")
        tracker.log_routing("Manager LLM", "Financial Data Analyst", f"Parse dataset {request.csv_path}")
        tracker.stop_task("analysis", "completed")

        tracker.start_task("report_writing")
        tracker.log_routing("Manager LLM", "Technical Reports Writer", "Synthesize report")

        # Load standard high-quality report template
        sample_file = Path("sample_outputs/market_report.md")
        if sample_file.exists():
            report_text = sample_file.read_text(encoding="utf-8")
        else:
            report_text = f"# Executive Summary\n\nMarket analysis for {request.query}.\n\n# Financial Analysis\n\n{stats_markdown}"

        tracker.stop_task("report_writing", "completed")
        tracker.stop_pipeline()
        tracker.save()
    else:
        from crew.crew import MarketResearchCrew
        crew = MarketResearchCrew(
            query=request.query,
            csv_path=request.csv_path,
            manager_model=request.manager_model,
            benchmark_path="benchmarks.json",
        )
        report_text = crew.run()

    # Save outputs
    output_pdf = "output/market_report.pdf"
    output_md = "output/market_report.md"

    Path(output_md).write_text(report_text, encoding="utf-8")

    MarketReportPDF.from_markdown(
        markdown_text=report_text,
        filename=output_pdf,
        title="Market Research Report",
        query=request.query,
        statistics_markdown=stats_markdown,
    )

    benchmarks_data = tracker.get_summary()

    return {
        "status": "success",
        "query": request.query,
        "csv_path": request.csv_path,
        "mode": "simulation" if is_mock else "live_hierarchical",
        "output_files": {
            "pdf_url": "/api/reports/download",
            "markdown_url": "/api/reports/markdown",
            "pdf_path": os.path.abspath(output_pdf),
            "markdown_path": os.path.abspath(output_md),
        },
        "report_preview": report_text[:500] + "...",
        "benchmarks": benchmarks_data,
    }


@app.get("/api/reports/download", tags=["Research & Reports"])
def download_pdf_report():
    """Download the latest compiled A4 PDF market research report."""
    pdf_path = Path("output/market_report.pdf")
    if not pdf_path.exists():
        pdf_path = Path("sample_outputs/market_report.pdf")
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="No generated PDF report found. Run /api/research first.")

    return FileResponse(
        path=str(pdf_path),
        filename="market_report.pdf",
        media_type="application/pdf",
    )


@app.get("/api/reports/markdown", tags=["Research & Reports"])
def get_markdown_report():
    """Retrieve the raw Markdown content of the generated market research report."""
    md_path = Path("output/market_report.md")
    if not md_path.exists():
        md_path = Path("sample_outputs/market_report.md")
    if not md_path.exists():
        raise HTTPException(status_code=404, detail="No markdown report found. Run /api/research first.")

    return PlainTextResponse(content=md_path.read_text(encoding="utf-8"))


@app.get("/api/benchmarks", tags=["Benchmarking & Analytics"])
def get_benchmarks():
    """Retrieve the latest task execution benchmarks and agent routing history."""
    benchmarks_path = Path("benchmarks.json")
    if not benchmarks_path.exists():
        raise HTTPException(status_code=404, detail="No benchmarks.json found. Run /api/research first.")

    with open(benchmarks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.post("/api/metrics/calculate", tags=["Data Analysis"])
def compute_metrics(request: MetricsRequest):
    """
    Parse a CSV dataset with Pandas and compute descriptive summary statistics
    (count, mean, std, min, 25%, 50%, 75%, max) formatted as a Markdown table.

    **Input:**
    - `csv_path`: Path to the CSV file (e.g. 'data/sample_metrics.csv')

    **Output:**
    - Formatted Markdown table containing descriptive statistics
    """
    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail=f"CSV file not found: {request.csv_path}")

    markdown_table = calculate_financial_metrics.run(csv_path=request.csv_path)
    return {
        "status": "success",
        "csv_path": request.csv_path,
        "statistics_markdown": markdown_table,
    }


# ---------------------------------------------------------------------------
# Server Starter
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=False)
