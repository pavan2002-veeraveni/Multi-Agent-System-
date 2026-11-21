# Multi-Agent Market Research & Report Generator
## Comprehensive System Architecture & Technical Documentation

---

## 1. Executive Summary & Project Overview

The **Multi-Agent Market Research & Report Generator** is an enterprise-grade artificial intelligence platform developed using **CrewAI**, **Pandas**, **ReportLab**, and **FastAPI**. The platform orchestrates a hierarchical team of specialized AI agents coordinated by an LLM supervisor. It automates the end-to-end market analysis lifecycle:
1. Crawling real-time industry trends and search metrics via search APIs and web scraping.
2. Computing descriptive statistical matrices (mean, dispersion, min/max, percentiles) across corporate datasets using Pandas.
3. Synthesizing quantitative data and qualitative market research into a cohesive technical report.
4. Programmatically compiling a publication-ready A4 PDF document with styled banners, tabular grids, and dynamic two-pass page numbering ("Page X of Y").
5. Logging execution latencies and task delegation routing histories for performance benchmarking.
6. Providing an interactive Web Browser Dashboard and OpenAPI REST API for user interaction.

---

## 2. High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   USER INTERFACES                                      │
│                                                                                        │
│     Web Browser Dashboard (HTML5 / Tailwind)      CLI Runner (python main.py --query)  │
│                http://127.0.0.1:8000                           Terminal                │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FASTAPI APPLICATION LAYER                                 │
│                                                                                        │
│   POST /api/research         POST /api/metrics/calculate       GET /api/reports/download│
│   GET  /api/benchmarks       GET  /api/reports/markdown        GET /docs (Swagger)     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       HIERARCHICAL CREWAI ORCHESTRATION LAYER                          │
│                                                                                        │
│                                Manager LLM (GPT-4o)                                    │
│                             Process: Process.hierarchical                              │
│                                           │                                            │
│            ┌──────────────────────────────┼──────────────────────────────┐             │
│            ▼                              ▼                              ▼             │
│   Lead Researcher Agent          Data Analyst Agent             Content Writer Agent   │
│ 'Market Research Specialist'   'Financial Data Analyst'      'Technical Reports Writer'│
│            │                              │                              │             │
│   ┌────────▼─────────┐           ┌────────▼─────────┐           ┌────────▼─────────┐   │
│   │web_search_scraper│           │calculate_        │           │Report Synthesis  │   │
│   │- Tavily Search   │           │financial_metrics │           │- Exec Summary    │   │
│   │- SerperDev Fallbk│           │- Pandas describe │           │- Market Dynamics │   │
│   │- BeautifulSoup   │           │- Statistical Grid│           │- Risk Factors    │   │
│   └──────────────────┘           └──────────────────┘           └──────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              OUTPUT & EXPORT SUBSYSTEMS                                │
│                                                                                        │
│     ReportLab PDF Compiler              Benchmark Tracker            Markdown Exporter │
│     (A4 & NumberedCanvas)               (benchmarks.json)            (market_report.md)│
│               │                                 │                            │         │
│               ▼                                 ▼                            ▼         │
│   output/market_report.pdf               benchmarks.json           output/market_report.md
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Hierarchical Multi-Agent Team Design

The multi-agent team is managed under `Process.hierarchical`. Tasks are not hardcoded to agents; instead, the **Manager LLM** dynamically evaluates task descriptions, assesses agent proficiencies, delegates work, and validates deliverables.

### Agent Roster

#### 1. Supervisor: Manager LLM
- **Engine:** Configured via `manager_llm` (defaults to `gpt-4o` or environment override `MANAGER_LLM_MODEL`).
- **Responsibility:** Evaluates user queries, plans execution steps, orchestrates delegation, traces routing history, and reviews completed deliverables.

#### 2. Lead Researcher Agent
- **Role:** `Market Research Specialist`
- **Goal:** `"Query search search networks, locate financial data, and scrape company metrics."`
- **Backstory:** A seasoned market research specialist with 15 years of experience identifying credible financial data sources and distinguishing signal from market noise.
- **Assigned Tools:** `web_search_scraper`

#### 3. Data Analyst Agent
- **Role:** `Financial Data Analyst`
- **Goal:** `"Parse data matrices using Pandas, compute averages, and verify numeric consistency."`
- **Backstory:** An expert quantitative analyst with a rigorous background in statistical modeling, trend detection, and financial ratio validation.
- **Assigned Tools:** `calculate_financial_metrics`

#### 4. Content Writer Agent
- **Role:** `Technical Reports Writer`
- **Goal:** `"Synthesize information, write sections, and structure copy."`
- **Backstory:** A financial journalist and technical copywriter who formats complex corporate datasets and qualitative insights into structured, publication-grade reports.
- **Assigned Tools:** None (receives outputs from Researcher and Analyst).

---

## 4. Custom Tools & Data Collection Pipeline

Tools are built using CrewAI's `@tool` decorator in `crew/tools.py`:

### Tool 1: `web_search_scraper`
```python
@tool
def web_search_scraper(query: str) -> str:
    """Searches the web for market data using Tavily / SerperDev and scrapes page text."""
```
- **Primary Search:** Queries the **Tavily Search API** (`https://api.tavily.com/search`) with `search_depth="advanced"`.
- **Fallback Search:** If Tavily is unavailable or unconfigured, falls back to the **SerperDev Google Search API** (`https://google.serper.dev/search`).
- **DOM Parsing & Scraping:** Sends HTTP requests to the top 3 target URLs, strips `<script>`, `<style>`, `<nav>`, `<header>`, and `<footer>` elements using **BeautifulSoup4**, and extracts clean text snippets.

### Tool 2: `calculate_financial_metrics`
```python
@tool
def calculate_financial_metrics(csv_path: str) -> str:
    """Loads corporate metrics from CSV and returns summary statistics as Markdown."""
```
- **Input:** Path to financial CSV dataset (e.g. `data/sample_metrics.csv`).
- **Processing:** Ingests tabular data via `pandas.read_csv()`, filters numeric fields, and computes `df.describe()`.
- **Metrics Calculated:**
  - `count`: Sample observations
  - `mean`: Arithmetic average
  - `std`: Standard deviation (dispersion)
  - `min`: Minimum observed value
  - `25%`: First quartile
  - `50%`: Median
  - `75%`: Third quartile
  - `max`: Peak observed value
- **Output:** Clean Markdown-formatted statistical table via `summary.to_markdown()`.

---

## 5. Programmatic PDF Generation Engine

PDF compilation is handled in `crew/pdf_generator.py` via Python's **ReportLab** library.

### Layout & Typographic System
- **Geometry:** Standard International A4 Page Size ($210\text{ mm} \times 297\text{ mm}$).
- **Margins:** Top/Bottom $25\text{ mm}$, Left/Right $20\text{ mm}$.
- **Palette:**
  - Primary / Headers: Deep Indigo (`#1a237e`)
  - Subheadings: Slate Indigo (`#283593`)
  - Accents: Sky Blue (`#42a5f5`)
  - Alternating Rows: Light Lavender Tint (`#e8eaf6`)
  - Grid Rules: Muted Grey (`#c5cae9`)

### NumberedCanvas ("Page X of Y")
ReportLab builds documents in a single forward pass by default, making total page count determination non-trivial. The generator implements a two-pass `NumberedCanvas`:
```python
class NumberedCanvas(canvas.Canvas):
    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(num_pages)
            super().showPage()
        super().save()
```
- **Header:** Styled banner with title, search query, author, and generation timestamp.
- **Footer:** Automatic "Page X of Y" page counter aligned right, alongside confidentiality disclosures and divider rules.

---

## 6. Execution Benchmarking & Analytics Engine

Tracking is managed by `BenchmarkTracker` in `crew/benchmarks.py`. All events are recorded in real-time and written to `benchmarks.json`:

```json
{
  "pipeline_total_seconds": 32.5,
  "generated_at": "2026-11-21T06:05:43.348632+00:00",
  "task_benchmarks": [
    {
      "task": "research",
      "start_time": "2026-11-21T06:05:43.344499+00:00",
      "status": "completed",
      "duration_seconds": 14.82,
      "end_time": "2026-11-21T06:05:58.164499+00:00"
    },
    {
      "task": "analysis",
      "start_time": "2026-11-21T06:05:58.174553+00:00",
      "status": "completed",
      "duration_seconds": 6.45,
      "end_time": "2026-11-21T06:06:04.624553+00:00"
    },
    {
      "task": "report_writing",
      "start_time": "2026-11-21T06:06:04.634575+00:00",
      "status": "completed",
      "duration_seconds": 11.23,
      "end_time": "2026-11-21T06:06:15.864575+00:00"
    }
  ],
  "routing_history": [
    {
      "timestamp": "2026-11-21T06:05:43.344522+00:00",
      "from": "Manager LLM",
      "to": "Market Research Specialist",
      "task": "Search web and gather metrics for: 'Tech Sector Q3 Analysis'"
    },
    {
      "timestamp": "2026-11-21T06:05:58.174559+00:00",
      "from": "Manager LLM",
      "to": "Financial Data Analyst",
      "task": "Calculate statistical summaries for dataset: 'data/sample_metrics.csv'"
    },
    {
      "timestamp": "2026-11-21T06:06:04.634579+00:00",
      "from": "Manager LLM",
      "to": "Technical Reports Writer",
      "task": "Synthesize gathered findings and statistical matrices into structured report"
    }
  ],
  "summary": {
    "total_tasks": 3,
    "completed_tasks": 3,
    "total_routing_events": 3
  }
}
```

---

## 7. Project File & Directory Structure

```
Multi_agent/
│
├── main.py                      # Primary Entry Point (Web Browser Server & CLI)
├── api.py                       # FastAPI compatibility module
├── test_api.py                  # API endpoint verification script
├── requirements.txt             # Project dependencies (CrewAI, Pandas, ReportLab, etc.)
├── .env.example                 # Environment configuration template
├── .gitignore                   # Ignores runtime outputs, credentials, and caches
├── README.md                    # Project overview & quick start
├── PROJECT_DOCUMENTATION.md     # This comprehensive technical reference
├── benchmarks.json              # Runtime execution benchmarks & routing history
│
├── crew/                        # Core Multi-Agent Package
│   ├── __init__.py              # Package exports and platform path guards
│   ├── agents.py                # Specialized Agent definitions
│   ├── tasks.py                 # Hierarchical Task definitions
│   ├── tools.py                 # @tool definitions (Search scraper & Pandas metrics)
│   ├── crew.py                  # Hierarchical MarketResearchCrew orchestrator
│   ├── pdf_generator.py         # ReportLab A4 compiler with NumberedCanvas
│   └── benchmarks.py            # Latency and delegation history analytics
│
├── data/                        # Input Datasets
│   └── sample_metrics.csv       # Corporate financial metrics (Apple, Microsoft, NVIDIA, etc.)
│
├── output/                      # Runtime Outputs
│   ├── market_report.pdf        # Generated publication-ready PDF report
│   ├── market_report.md         # Generated Markdown report
│   └── execution.log            # Execution log file
│
├── sample_outputs/              # Reference Pre-Compiled Deliverables
│   ├── market_report.pdf        # Benchmark reference PDF
│   └── market_report.md         # Benchmark reference Markdown
│
└── tests/                       # Automated Test Suite (pytest)
    ├── __init__.py
    ├── conftest.py              # Test harness configuration
    ├── test_financial_tools.py  # Pandas summary statistics verification
    ├── test_pdf_generator.py    # ReportLab layout, styles, and canvas validation
    └── test_benchmarks.py       # BenchmarkTracker duration & routing tests
```

---

## 8. REST API Specification

| Method | Endpoint | Request Body | Response | Description |
|---|---|---|---|---|
| `GET` | `/` | None | HTML | Interactive Web Browser Dashboard |
| `GET` | `/api/info` | None | JSON | Directory of available endpoints |
| `GET` | `/health` | None | `{"status": "healthy"}` | Service health probe |
| `POST` | `/api/research` | `{"query": str, "csv_path": str, "mock": bool}` | JSON (status, file paths, preview, benchmarks) | Executes hierarchical research pipeline |
| `GET` | `/api/reports/download` | None | Binary PDF (`application/pdf`) | Downloads compiled `market_report.pdf` |
| `GET` | `/api/reports/markdown` | None | Plain Text (`text/plain`) | Retrieves raw Markdown report text |
| `GET` | `/api/benchmarks` | None | JSON | Returns `benchmarks.json` contents |
| `POST` | `/api/metrics/calculate`| `{"csv_path": str}` | JSON (`statistics_markdown`) | Runs Pandas `describe()` on CSV |
| `GET` | `/docs` | None | HTML (Swagger UI) | Interactive OpenAPI testing console |

---

## 9. Verification & Automated Testing Suite

The platform includes 20 comprehensive unit and integration tests executed via `pytest`:

```bash
pytest -v
```

### Test Coverage Breakdown

```
tests/test_benchmarks.py
  - test_pipeline_timing: Measures start/stop wall-clock pipeline duration
  - test_task_lifecycle_timing: Verifies task start, duration calculation, and status
  - test_routing_history_logging: Verifies delegation entries (from, to, task)
  - test_save_to_json: Validates JSON serialization matching benchmark schema

tests/test_financial_tools.py
  - test_returns_markdown_string: Confirms non-empty Markdown table output
  - test_contains_statistical_rows: Checks for count, mean, std, min, max rows
  - test_correct_mean_calculation: Mathematically compares calculated means against expected
  - test_correct_min_max: Verifies lower and upper bound precision
  - test_correct_count: Confirms exact sample observation counts
  - test_handles_missing_file: Validates graceful error handling for missing files
  - test_std_deviation_positive: Ensures dispersion $> 0$ for non-identical datasets
  - test_describe_shape: Verifies 8-row descriptive statistical structure

tests/test_pdf_generator.py
  - test_pdf_file_created: Validates physical file generation on disk
  - test_pdf_has_valid_header: Asserts `%PDF-` magic header bytes
  - test_pdf_no_styling_exceptions: Confirms complete build with zero styling errors
  - test_pdf_with_empty_content: Validates fallback handling for empty bodies
  - test_pdf_with_statistics_table: Verifies table grid layout rendering
  - test_pdf_instance_methods: Validates add_header_banner, add_section, add_data_table
  - test_pdf_multiple_sections: Verifies flow across multiple document sections
  - test_numbered_canvas: Tests two-pass canvas and "Page X of Y" formatting
```

---

## 10. How to Run the Application

### 1. Launch Interactive Web Browser Dashboard (Recommended)
```powershell
python main.py
```
*Starts the server at `http://127.0.0.1:8000` and automatically opens the dashboard in your default browser.*

### 2. Run CLI Batch Analysis (Assessment Test Case 1)
```powershell
python main.py --query "Tech Sector Q3 Analysis"
```

### 3. Run with Custom Topic and Dataset
```powershell
python main.py --query "EV Sector Outlook 2025" --csv "data/sample_metrics.csv" --output "output/ev_report.pdf"
```

### 4. Run Automated Test Suite
```powershell
pytest -v
```
