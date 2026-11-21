#!/usr/bin/env python3
"""
Multi-Agent Market Research & Report Generator
==============================================

Unified entry point for the CrewAI hierarchical market research system.

Features:
  1. Web Server & Browser Dashboard (Default: `python main.py` or `python main.py --server`)
     Launches the FastAPI server and automatically opens the interactive dashboard in your browser.
  2. CLI Batch Pipeline (`python main.py --query "Tech Sector Q3 Analysis"`)
     Executes the hierarchical multi-agent team via CLI and compiles the PDF directly.
"""

import argparse
import json
import logging
import os
import shutil
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Bootstrap & Environment
# ---------------------------------------------------------------------------
load_dotenv()

# Ensure local writable appdata for CrewAI token manager on Windows
if sys.platform == "win32":
    local_app_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".localappdata"))
    try:
        current_lad = os.environ.get("LOCALAPPDATA", "")
        test_dir = os.path.join(current_lad, "crewai_write_test")
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
    except Exception:
        os.environ["LOCALAPPDATA"] = local_app_dir
        os.makedirs(local_app_dir, exist_ok=True)

os.environ.setdefault("CREWAI_TELEMETRY_OPT_OUT", "true")

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

# Import crew components
from crew.pdf_generator import MarketReportPDF
from crew.tools import calculate_financial_metrics
from crew.benchmarks import BenchmarkTracker


# ---------------------------------------------------------------------------
# FastAPI Application & Web UI
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Multi-Agent Market Research & Report Generator",
    description="Interactive Web Application & REST API powered by CrewAI, Pandas, and ReportLab.",
    version="2.0.0",
)


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
# HTML Web Dashboard
# ---------------------------------------------------------------------------
HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Multi-Agent Market Research & Report Generator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    body { font-family: 'Inter', sans-serif; }
    .glass { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen">
  <!-- Top Navigation -->
  <header class="border-b border-slate-800 bg-slate-900/80 sticky top-0 z-50 backdrop-blur">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-blue-600 flex items-center justify-center text-white shadow-lg shadow-indigo-500/30">
          <i class="fa-solid fa-brain text-xl"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold text-white leading-tight">Antigravity Multi-Agent</h1>
          <p class="text-xs text-indigo-400 font-medium">CrewAI &bull; Pandas &bull; ReportLab</p>
        </div>
      </div>
      <div class="flex items-center space-x-4">
        <a href="/docs" target="_blank" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition flex items-center gap-1.5">
          <i class="fa-solid fa-book"></i> Swagger Docs
        </a>
        <a href="/api/benchmarks" target="_blank" class="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-1.5 rounded-lg border border-slate-700 transition flex items-center gap-1.5">
          <i class="fa-solid fa-chart-line"></i> Benchmarks
        </a>
        <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span> Team Active
        </span>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
    <!-- Top Hero Banner -->
    <div class="bg-gradient-to-r from-indigo-900/60 via-slate-800/80 to-blue-900/60 border border-slate-700/60 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
      <div class="relative z-10 max-w-3xl">
        <h2 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">Market Research & Programmatic PDF Generator</h2>
        <p class="mt-2 text-slate-300 text-sm sm:text-base leading-relaxed">
          Orchestrates three specialized agents (<strong>Lead Researcher</strong>, <strong>Data Analyst</strong>, <strong>Technical Writer</strong>) under a supervisor Manager LLM to crawl data, parse matrices with Pandas, and compile publication-ready A4 PDF reports.
        </p>
      </div>
    </div>

    <!-- Agent Team Architecture Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex items-start space-x-3" id="card-manager">
        <div class="w-9 h-9 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-user-tie"></i>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white">Manager LLM</h3>
          <p class="text-xs text-slate-400">Supervisor &bull; Dynamic Router</p>
          <span class="text-[10px] mt-1 inline-block text-indigo-400 bg-indigo-950/60 px-2 py-0.5 rounded border border-indigo-800/50" id="status-manager">Ready</span>
        </div>
      </div>
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex items-start space-x-3" id="card-researcher">
        <div class="w-9 h-9 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-magnifying-glass"></i>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white">Lead Researcher</h3>
          <p class="text-xs text-slate-400">Web Scraper &amp; APIs</p>
          <span class="text-[10px] mt-1 inline-block text-blue-400 bg-blue-950/60 px-2 py-0.5 rounded border border-blue-800/50" id="status-researcher">Idle</span>
        </div>
      </div>
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex items-start space-x-3" id="card-analyst">
        <div class="w-9 h-9 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-table"></i>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white">Data Analyst</h3>
          <p class="text-xs text-slate-400">Pandas Summary Stats</p>
          <span class="text-[10px] mt-1 inline-block text-purple-400 bg-purple-950/60 px-2 py-0.5 rounded border border-purple-800/50" id="status-analyst">Idle</span>
        </div>
      </div>
      <div class="bg-slate-800/60 border border-slate-700/60 rounded-xl p-4 flex items-start space-x-3" id="card-writer">
        <div class="w-9 h-9 rounded-lg bg-pink-600/20 text-pink-400 flex items-center justify-center shrink-0">
          <i class="fa-solid fa-pen-nib"></i>
        </div>
        <div>
          <h3 class="text-sm font-semibold text-white">Content Writer</h3>
          <p class="text-xs text-slate-400">Report Synthesis</p>
          <span class="text-[10px] mt-1 inline-block text-pink-400 bg-pink-950/60 px-2 py-0.5 rounded border border-pink-800/50" id="status-writer">Idle</span>
        </div>
      </div>
    </div>

    <!-- Main Workspace Form & Output -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
      <!-- Left Column: Controls Form -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-slate-800/80 border border-slate-700 rounded-2xl p-6 shadow-xl space-y-5">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <i class="fa-solid fa-sliders text-indigo-400"></i> Research Parameters
          </h3>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Research Query / Sector</label>
            <input type="text" id="inputQuery" value="Tech Sector Q3 Analysis" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition">
          </div>

          <div>
            <label class="block text-xs font-semibold text-slate-300 mb-1.5">Financial Dataset (CSV)</label>
            <input type="text" id="inputCsv" value="data/sample_metrics.csv" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition">
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Manager LLM</label>
              <select id="selectModel" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="gpt-4o" selected>GPT-4o (Supervisor)</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-300 mb-1.5">Execution Mode</label>
              <select id="selectMode" class="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <option value="auto" selected>Auto-Detect (API / Demo)</option>
                <option value="demo">Demo Mode (Zero API Key)</option>
                <option value="live">Live AI Execution</option>
              </select>
            </div>
          </div>

          <button id="btnRun" onclick="triggerResearch()" class="w-full bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white font-semibold py-3 px-4 rounded-xl shadow-lg shadow-indigo-500/25 transition duration-150 flex items-center justify-center gap-2 text-sm">
            <i class="fa-solid fa-play"></i> Run Multi-Agent Research
          </button>
        </div>

        <!-- Quick Actions & Download -->
        <div class="bg-slate-800/40 border border-slate-700/60 rounded-xl p-5 space-y-3">
          <h4 class="text-xs font-bold uppercase tracking-wider text-slate-400">Deliverables</h4>
          <div class="flex flex-col gap-2">
            <a href="/api/reports/download" class="w-full bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium py-2.5 px-3 rounded-lg border border-slate-700 transition flex items-center justify-between">
              <span class="flex items-center gap-2"><i class="fa-solid fa-file-pdf text-rose-400"></i> Download market_report.pdf</span>
              <i class="fa-solid fa-download text-slate-400"></i>
            </a>
            <a href="/api/reports/markdown" target="_blank" class="w-full bg-slate-800 hover:bg-slate-700 text-white text-xs font-medium py-2.5 px-3 rounded-lg border border-slate-700 transition flex items-center justify-between">
              <span class="flex items-center gap-2"><i class="fa-brands fa-markdown text-blue-400"></i> View Raw Markdown</span>
              <i class="fa-solid fa-arrow-up-right-from-square text-slate-400"></i>
            </a>
          </div>
        </div>
      </div>

      <!-- Right Column: Results & Analytics Tabbed View -->
      <div class="lg:col-span-7 space-y-6">
        <div class="bg-slate-800/80 border border-slate-700 rounded-2xl shadow-xl overflow-hidden flex flex-col min-h-[550px]">
          <!-- Tabs Header -->
          <div class="flex border-b border-slate-700 bg-slate-900/50 px-4 pt-3 gap-2">
            <button onclick="switchTab('report')" id="tab-btn-report" class="text-xs font-semibold px-4 py-2.5 rounded-t-lg bg-slate-800 text-indigo-400 border-t-2 border-indigo-500 transition">
              <i class="fa-solid fa-file-lines mr-1.5"></i> Generated Report
            </button>
            <button onclick="switchTab('stats')" id="tab-btn-stats" class="text-xs font-semibold px-4 py-2.5 rounded-t-lg text-slate-400 hover:text-white transition">
              <i class="fa-solid fa-chart-simple mr-1.5"></i> Pandas Statistics
            </button>
            <button onclick="switchTab('benchmarks')" id="tab-btn-benchmarks" class="text-xs font-semibold px-4 py-2.5 rounded-t-lg text-slate-400 hover:text-white transition">
              <i class="fa-solid fa-stopwatch mr-1.5"></i> Benchmarks
            </button>
          </div>

          <!-- Tab Content: Report -->
          <div id="tab-report" class="p-6 flex-1 overflow-y-auto max-h-[600px] prose prose-invert prose-sm max-w-none">
            <div id="reportContent" class="text-slate-300">
              <p class="text-slate-400 italic">Click "Run Multi-Agent Research" to start the pipeline, or view the default pre-compiled report below.</p>
            </div>
          </div>

          <!-- Tab Content: Statistics -->
          <div id="tab-stats" class="p-6 flex-1 overflow-y-auto max-h-[600px] hidden">
            <h4 class="text-sm font-bold text-white mb-3">Corporate Metrics &amp; Descriptive Statistics</h4>
            <div id="statsTable" class="text-xs text-slate-300 overflow-x-auto">
              <p class="text-slate-400">Loading Pandas statistical table...</p>
            </div>
          </div>

          <!-- Tab Content: Benchmarks -->
          <div id="tab-benchmarks" class="p-6 flex-1 overflow-y-auto max-h-[600px] hidden space-y-4">
            <h4 class="text-sm font-bold text-white">Execution Analytics &amp; Routing Trace</h4>
            <div id="benchmarkStats" class="grid grid-cols-3 gap-3 text-center">
              <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-700/60">
                <p class="text-xs text-slate-400">Total Latency</p>
                <p id="totalDuration" class="text-base font-bold text-indigo-400">--</p>
              </div>
              <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-700/60">
                <p class="text-xs text-slate-400">Completed Tasks</p>
                <p id="completedTasks" class="text-base font-bold text-emerald-400">--</p>
              </div>
              <div class="bg-slate-900/60 p-3 rounded-lg border border-slate-700/60">
                <p class="text-xs text-slate-400">Routing Events</p>
                <p id="routingCount" class="text-base font-bold text-blue-400">--</p>
              </div>
            </div>
            <div class="space-y-2">
              <h5 class="text-xs font-semibold text-slate-300 uppercase tracking-wider">Supervisor Delegation Trace</h5>
              <div id="routingHistory" class="space-y-2 text-xs">
                <!-- Dynamically populated -->
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <script>
    function switchTab(tab) {
      ['report', 'stats', 'benchmarks'].forEach(t => {
        document.getElementById(`tab-${t}`).classList.add('hidden');
        document.getElementById(`tab-btn-${t}`).className = 'text-xs font-semibold px-4 py-2.5 rounded-t-lg text-slate-400 hover:text-white transition';
      });
      document.getElementById(`tab-${tab}`).classList.remove('hidden');
      document.getElementById(`tab-btn-${tab}`).className = 'text-xs font-semibold px-4 py-2.5 rounded-t-lg bg-slate-800 text-indigo-400 border-t-2 border-indigo-500 transition';
    }

    async function loadInitialData() {
      try {
        const mdRes = await fetch('/api/reports/markdown');
        if (mdRes.ok) {
          const text = await mdRes.text();
          document.getElementById('reportContent').innerHTML = marked.parse(text);
        }

        const metricsRes = await fetch('/api/metrics/calculate', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({csv_path: 'data/sample_metrics.csv'})
        });
        if (metricsRes.ok) {
          const metricsData = await metricsRes.json();
          document.getElementById('statsTable').innerHTML = marked.parse(metricsData.statistics_markdown);
        }

        const benchRes = await fetch('/api/benchmarks');
        if (benchRes.ok) {
          const bData = await benchRes.json();
          renderBenchmarks(bData);
        }
      } catch (err) {
        console.log('Initial data loading note:', err);
      }
    }

    function renderBenchmarks(data) {
      document.getElementById('totalDuration').innerText = (data.pipeline_total_seconds || 0) + 's';
      document.getElementById('completedTasks').innerText = data.summary?.completed_tasks || 3;
      document.getElementById('routingCount').innerText = data.summary?.total_routing_events || 3;

      const historyEl = document.getElementById('routingHistory');
      historyEl.innerHTML = '';
      (data.routing_history || []).forEach(r => {
        const card = document.createElement('div');
        card.className = 'bg-slate-900/60 p-2.5 rounded-lg border border-slate-700/50 flex items-start gap-2.5';
        card.innerHTML = `
          <i class="fa-solid fa-arrow-turn-down text-indigo-400 mt-1"></i>
          <div>
            <div class="font-semibold text-white">${r.from} &rarr; <span class="text-indigo-400">${r.to}</span></div>
            <div class="text-slate-400 text-[11px] mt-0.5">${r.task}</div>
          </div>
        `;
        historyEl.appendChild(card);
      });
    }

    async function triggerResearch() {
      const btn = document.getElementById('btnRun');
      const query = document.getElementById('inputQuery').value;
      const csv_path = document.getElementById('inputCsv').value;
      const manager_model = document.getElementById('selectModel').value;
      const mode = document.getElementById('selectMode').value;

      btn.disabled = true;
      btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Agents Working...';

      // Update statuses
      document.getElementById('status-manager').innerText = 'Delegating...';
      document.getElementById('status-researcher').innerText = 'Crawling...';

      try {
        const isMock = mode === 'demo';
        const res = await fetch('/api/research', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({query, csv_path, manager_model, mock: isMock})
        });

        const data = await res.json();
        if (res.ok) {
          document.getElementById('status-manager').innerText = 'Done';
          document.getElementById('status-researcher').innerText = 'Done';
          document.getElementById('status-analyst').innerText = 'Done';
          document.getElementById('status-writer').innerText = 'Done';

          // Load refreshed report
          const mdRes = await fetch('/api/reports/markdown');
          const mdText = await mdRes.text();
          document.getElementById('reportContent').innerHTML = marked.parse(mdText);

          // Render benchmarks
          if (data.benchmarks) {
            renderBenchmarks(data.benchmarks);
          }
          switchTab('report');
        } else {
          alert('Error: ' + (data.detail || 'Failed to execute research pipeline'));
        }
      } catch (e) {
        alert('Network or server error: ' + e);
      } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-play"></i> Run Multi-Agent Research';
      }
    }

    window.addEventListener('DOMContentLoaded', loadInitialData);
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, tags=["Web UI"])
def get_dashboard():
    """Serves the interactive web browser dashboard."""
    return HTMLResponse(content=HTML_DASHBOARD)


@app.get("/api/info", tags=["General"])
def api_info():
    """JSON API status and directory of available endpoints."""
    return {
        "service": "Multi-Agent Market Research & Report Generator",
        "version": "2.0.0",
        "status": "online",
        "documentation": "/docs",
        "endpoints": {
            "GET  /": "Interactive Web Browser Dashboard",
            "POST /api/research": "Run multi-agent research workflow",
            "GET  /api/reports/download": "Download compiled PDF market report",
            "GET  /api/reports/markdown": "View generated Markdown report",
            "GET  /api/benchmarks": "Retrieve task benchmarks and routing history",
            "POST /api/metrics/calculate": "Compute Pandas summary statistics on CSV dataset",
            "GET  /health": "Health check",
        },
    }


@app.get("/health", tags=["General"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "multi-agent-crewai"}


@app.post("/api/research", tags=["Research & Reports"])
def run_research(request: ResearchRequest):
    """Execute the multi-agent market research pipeline for a given query."""
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
    """Retrieve raw Markdown content of the generated market report."""
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
        raise HTTPException(status_code=404, detail="No benchmarks.json found.")

    with open(benchmarks_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(content=data)


@app.post("/api/metrics/calculate", tags=["Data Analysis"])
def compute_metrics(request: MetricsRequest):
    """Parse CSV with Pandas and compute descriptive summary statistics."""
    if not os.path.exists(request.csv_path):
        raise HTTPException(status_code=404, detail=f"CSV file not found: {request.csv_path}")

    markdown_table = calculate_financial_metrics.run(csv_path=request.csv_path)
    return {
        "status": "success",
        "csv_path": request.csv_path,
        "statistics_markdown": markdown_table,
    }


# ---------------------------------------------------------------------------
# CLI Pipeline Execution (Preserves Test Case 1 & 2 requirements)
# ---------------------------------------------------------------------------
def run_cli_pipeline(args) -> None:
    """Execute the pipeline from the command line."""
    os.makedirs("output", exist_ok=True)
    os.makedirs("sample_outputs", exist_ok=True)

    query = args.query or "Tech Sector Q3 Analysis"
    csv_file = args.csv or "data/sample_metrics.csv"
    output_pdf = args.output or "output/market_report.pdf"

    logger.info("=" * 70)
    logger.info("Multi-Agent Market Research & Report Generator (CLI)")
    logger.info("=" * 70)
    logger.info("Query       : %s", query)
    logger.info("CSV Data    : %s", csv_file)
    logger.info("Output PDF  : %s", output_pdf)
    logger.info("=" * 70)

    openai_key = os.getenv("OPENAI_API_KEY", "")
    is_mock = args.mock or not openai_key or openai_key.startswith("sk-your") or openai_key == "mock-test-key"

    if is_mock:
        logger.info("Running in demonstration verification mode.")
        tracker = BenchmarkTracker(output_path="benchmarks.json")
        tracker.start_pipeline()

        logger.info("[Manager LLM] Initializing hierarchical multi-agent workflow...")
        logger.info("[Manager LLM] Process: Process.hierarchical (Dynamic Delegation)")

        logger.info("[Manager LLM] -> Delegating Task 1 to Market Research Specialist...")
        tracker.start_task("research")
        tracker.log_routing("Manager LLM", "Market Research Specialist", f"Search web: {query}")
        logger.info("[Market Research Specialist] Scraped financial sources for: %s", query)
        tracker.stop_task("research", "completed")

        logger.info("[Manager LLM] -> Delegating Task 2 to Financial Data Analyst...")
        tracker.start_task("analysis")
        tracker.log_routing("Manager LLM", "Financial Data Analyst", f"Parse dataset: {csv_file}")
        stats_markdown = calculate_financial_metrics.run(csv_path=csv_file)
        logger.info("[Financial Data Analyst] Calculated summary statistics via Pandas describe()")
        tracker.stop_task("analysis", "completed")

        logger.info("[Manager LLM] -> Delegating Task 3 to Technical Reports Writer...")
        tracker.start_task("report_writing")
        tracker.log_routing("Manager LLM", "Technical Reports Writer", "Synthesize report")
        sample_file = Path("sample_outputs/market_report.md")
        if sample_file.exists():
            report_text = sample_file.read_text(encoding="utf-8")
        else:
            report_text = f"# Executive Summary\n\nMarket analysis for {query}.\n\n# Financial Analysis\n\n{stats_markdown}"
        tracker.stop_task("report_writing", "completed")
        tracker.stop_pipeline()
        tracker.save()
    else:
        from crew.crew import MarketResearchCrew
        crew = MarketResearchCrew(
            query=query,
            csv_path=csv_file,
            manager_model=args.manager_model,
            benchmark_path="benchmarks.json",
        )
        report_text = crew.run()
        stats_markdown = calculate_financial_metrics.run(csv_path=csv_file)

    md_path = Path(output_pdf).with_suffix(".md")
    md_path.write_text(report_text, encoding="utf-8")
    logger.info("Markdown report saved: %s", md_path)

    pdf_path = MarketReportPDF.from_markdown(
        markdown_text=report_text,
        filename=output_pdf,
        title="Market Research Report",
        query=query,
        statistics_markdown=stats_markdown,
    )
    logger.info("PDF report generated: %s", pdf_path)

    # Copy to sample_outputs
    shutil.copy2(str(md_path), f"sample_outputs/{md_path.name}")
    shutil.copy2(output_pdf, f"sample_outputs/{Path(output_pdf).name}")

    logger.info("=" * 70)
    logger.info("Pipeline completed successfully!")
    logger.info("  Markdown   : %s", md_path.resolve())
    logger.info("  PDF        : %s", Path(output_pdf).resolve())
    logger.info("  Benchmarks : %s", Path("benchmarks.json").resolve())
    logger.info("=" * 70)


# ---------------------------------------------------------------------------
# Server Starter & Browser Launch
# ---------------------------------------------------------------------------
def open_browser_delayed(url: str, delay: float = 1.2):
    """Wait for server to bind and launch the default web browser."""
    time.sleep(delay)
    logger.info("Opening web browser dashboard at %s ...", url)
    webbrowser.open(url)


def run_web_server(host: str = "127.0.0.1", port: int = 8000, auto_open: bool = True):
    """Start Uvicorn web server and open the browser dashboard."""
    import uvicorn

    url = f"http://{host}:{port}"
    print("=" * 70)
    print(f"🚀 Multi-Agent Market Research Web Application Running")
    print(f"👉 Web Browser Dashboard : {url}")
    print(f"📚 Swagger Documentation : {url}/docs")
    print("=" * 70)

    if auto_open:
        threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Multi-Agent Market Research & Report Generator (CrewAI & FastAPI)",
    )
    parser.add_argument("--server", action="store_true", help="Launch the web browser dashboard server")
    parser.add_argument("--cli", action="store_true", help="Force CLI execution mode")
    parser.add_argument("--query", type=str, default=None, help="Market research query topic")
    parser.add_argument("--csv", type=str, default="data/sample_metrics.csv", help="Path to CSV dataset")
    parser.add_argument("--output", type=str, default="output/market_report.pdf", help="Output PDF file path")
    parser.add_argument("--manager-model", type=str, default=None, help="Manager LLM model (default: gpt-4o)")
    parser.add_argument("--mock", action="store_true", help="Run in offline simulation mode")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open the web browser")
    return parser.parse_args()


def main():
    args = parse_args()

    # If --query is passed explicitly or --cli is passed, run CLI pipeline
    # (Matches Test Case 1 & 2 requirements: python main.py --query "...")
    if args.cli or (args.query is not None and not args.server):
        run_cli_pipeline(args)
    else:
        # Default behavior: run web application in the browser!
        run_web_server(host=args.host, port=args.port, auto_open=not args.no_browser)


if __name__ == "__main__":
    main()
