# Multi-Agent Market Research with CrewAI
- **Repository**: [Insert URL]

## Installation
1. Configure `.env` file (`TAVILY_API_KEY`, `OPENAI_API_KEY`).
2. Install dependencies: `pip install -r requirements.txt`
3. Run main app: `python main.py`
4. Run tests: `pytest`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                 Manager LLM (GPT-4o)            │
│            Hierarchical Process Control          │
├────────────┬────────────────┬────────────────────┤
│            │                │                    │
│  ┌─────────▼──────┐ ┌──────▼───────┐ ┌──────────▼─────┐
│  │ Lead Researcher │ │ Data Analyst │ │ Content Writer │
│  │   Agent         │ │   Agent      │ │   Agent        │
│  └─────────┬──────┘ └──────┬───────┘ └──────────┬─────┘
│            │                │                    │
│  ┌─────────▼──────┐ ┌──────▼───────┐            │
│  │ Web Scraper    │ │ Financial    │            │
│  │ Tool (Tavily/  │ │ Metrics Tool │            │
│  │ SerperDev)     │ │ (Pandas)     │            │
│  └────────────────┘ └──────────────┘            │
│                                                  │
├──────────────────────────────────────────────────┤
│           Post-Processing Pipeline               │
│  ┌─────────────┐  ┌──────────┐  ┌────────────┐  │
│  │ Markdown    │→ │ ReportLab│→ │ PDF Report │  │
│  │ Report      │  │ Compiler │  │ (A4)       │  │
│  └─────────────┘  └──────────┘  └────────────┘  │
└──────────────────────────────────────────────────┘
```

## 📋 Features

- **Hierarchical Agent Orchestration**: Three specialized agents managed by a supervisor LLM via `Process.hierarchical`
- **Custom Web Scraping Tools**: Integrates with Tavily and SerperDev APIs for real-time market data collection
- **Pandas Data Analysis**: Statistical processing with `describe()`, computing mean, std, min, max, and percentiles
- **Professional PDF Reports**: ReportLab-powered A4 documents with headers, tables, and "Page X of Y" numbering
- **Execution Benchmarking**: JSON-logged timing metrics and task routing history
- **Automated Test Suite**: pytest coverage for financial tools and PDF generation

## 📂 Project Structure

```
Multi_agent/
├── main.py                      # Entry point with CLI interface
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── benchmarks.json              # Execution benchmarks (generated)
│
├── crew/                        # CrewAI package
│   ├── __init__.py              # Package exports
│   ├── agents.py                # Agent definitions (Researcher, Analyst, Writer)
│   ├── tasks.py                 # Task definitions (Research, Analysis, Report)
│   ├── tools.py                 # Custom tools (@tool decorated)
│   ├── crew.py                  # MarketResearchCrew orchestrator
│   ├── pdf_generator.py         # ReportLab PDF compiler
│   └── benchmarks.py            # Execution timing & analytics
│
├── tests/                       # Automated test suite
│   ├── __init__.py
│   ├── test_financial_tools.py  # Pandas analysis verification
│   └── test_pdf_generator.py    # PDF layout validation
│
├── data/                        # Input data
│   └── sample_metrics.csv       # Sample financial metrics dataset
│
├── output/                      # Generated reports (runtime)
│   ├── market_report.md         # Markdown report
│   └── market_report.pdf        # Compiled PDF report
│
└── sample_outputs/              # Sample generated outputs
    ├── market_report.md
    └── market_report.pdf
```

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Multi_agent
```

### 2. Create a Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and set the following keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | Powers the manager LLM and all agents |
| `TAVILY_API_KEY` | ⚡ Recommended | Primary web search API |
| `SERPER_API_KEY` | 🔄 Fallback | Alternative search API (if Tavily unavailable) |
| `MANAGER_LLM_MODEL` | ❌ Optional | Override default model (default: `gpt-4o`) |

## 🌐 REST API Endpoints & Server

The application provides both a CLI interface and a production **FastAPI REST API**.

### Starting the API Server

```bash
python api.py
# or using uvicorn directly:
uvicorn api:app --host 0.0.0.0 --port 8000
```

Interactive Swagger documentation is available at `http://localhost:8000/docs`.

### Available Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API status and directory of available endpoints |
| `GET` | `/health` | Service health status |
| `POST` | `/api/research` | Trigger the multi-agent market research & PDF generation pipeline |
| `GET` | `/api/reports/download` | Download the compiled A4 PDF report (`market_report.pdf`) |
| `GET` | `/api/reports/markdown` | View the generated Markdown report (`market_report.md`) |
| `GET` | `/api/benchmarks` | Retrieve task latency benchmarks and routing history (`benchmarks.json`) |
| `POST` | `/api/metrics/calculate` | Compute Pandas descriptive statistics on a CSV dataset |

---

## 💻 Usage

### Run the Main Application

```bash
python main.py --query "Tech Sector Q3 Analysis"
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--query` | `"Tech Sector Q3 Analysis"` | Market research query topic |
| `--csv` | `data/sample_metrics.csv` | Path to financial metrics CSV |
| `--output` | `output/market_report.pdf` | Output PDF report path |
| `--manager-model` | `gpt-4o` | Manager LLM model name |

### Example Commands

```bash
# Default tech sector analysis
python main.py --query "Tech Sector Q3 Analysis"

# Custom query with different CSV data
python main.py --query "EV Market Outlook 2025" --csv data/ev_metrics.csv

# Specify output location
python main.py --query "AI Industry Report" --output reports/ai_analysis.pdf
```

## 🧪 Running Tests

Execute the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run specific test modules:

```bash
# Test financial tools only
pytest tests/test_financial_tools.py -v

# Test PDF generator only
pytest tests/test_pdf_generator.py -v
```

### Test Coverage

| Test Module | Tests | Description |
|-------------|-------|-------------|
| `test_financial_tools.py` | 8 | Pandas analysis, statistics validation, error handling |
| `test_pdf_generator.py` | 8 | PDF creation, styling, tables, page numbering |

## 🔄 Verification Workflows

### Test Case 1: Hierarchical Process Execution

```bash
python main.py --query "Tech Sector Q3 Analysis"
```
- ✅ Console logs show manager LLM initializing the workflow
- ✅ Tasks are delegated dynamically by the manager
- ✅ Log trace shows Researcher → Analyst → Writer delegation

### Test Case 2: Data Aggregation & PDF Generation

After running Test Case 1:
- ✅ Check `output/` directory for `market_report.pdf`
- ✅ PDF contains styled header banner with metadata
- ✅ PDF contains structured data tables with Pandas metrics
- ✅ PDF contains correct page numbers (Page X of Y)

### Test Case 3: Automated Test Suite

```bash
pytest
```
- ✅ All tests pass
- ✅ No exceptions logged

## 📊 Execution Benchmarks

After each run, execution metrics are logged to `benchmarks.json`:

```json
{
  "pipeline_total_seconds": 45.23,
  "task_benchmarks": [
    {"task": "research", "duration_seconds": 15.1, "status": "completed"},
    {"task": "analysis", "duration_seconds": 8.4, "status": "completed"},
    {"task": "report_writing", "duration_seconds": 12.7, "status": "completed"}
  ],
  "routing_history": [
    {"from": "Manager LLM", "to": "Market Research Specialist", "task": "..."},
    {"from": "Manager LLM", "to": "Financial Data Analyst", "task": "..."},
    {"from": "Manager LLM", "to": "Technical Reports Writer", "task": "..."}
  ]
}
```

## 🛠️ Technology Stack

| Technology | Purpose |
|-----------|---------|
| **Python 3.10+** | Core language |
| **CrewAI** | Multi-agent orchestration framework |
| **Pandas** | Financial data analysis and statistics |
| **ReportLab** | Programmatic PDF report generation |
| **Tavily / SerperDev** | Web search API integration |
| **BeautifulSoup4** | HTML parsing and web scraping |
| **python-dotenv** | Environment variable management |
| **pytest** | Automated testing framework |

## 📄 License

This project is provided for assessment and educational purposes.
