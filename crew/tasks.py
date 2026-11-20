"""
CrewAI Task Definitions

Defines the three core tasks for the market research pipeline:
  1. Research Task   – data gathering and web scraping
  2. Analysis Task   – statistical processing with Pandas
  3. Report Task     – structured report writing
"""

import logging
from crewai import Task, Agent

logger = logging.getLogger(__name__)


def create_tasks(
    query: str,
    csv_path: str = "data/sample_metrics.csv",
) -> list[Task]:
    """
    Create the ordered list of tasks for the hierarchical crew.

    In hierarchical mode, tasks are NOT pre-assigned to agents.
    The manager LLM decides which agent handles which task.

    Args:
        query:    The market research query (e.g. 'Tech Sector Q3 Analysis').
        csv_path: Path to the CSV file containing financial metrics.

    Returns:
        Ordered list of Task objects.
    """
    # ----- Task 1: Market Research & Data Collection -----
    research_task = Task(
        description=(
            f"Conduct comprehensive market research on the following topic:\n\n"
            f"**Query:** {query}\n\n"
            f"Your objectives:\n"
            f"1. Search the web for the latest financial data, market trends, "
            f"   and company performance metrics related to '{query}'.\n"
            f"2. Identify at least 3-5 key data points including revenue figures, "
            f"   growth rates, market share, and competitive landscape.\n"
            f"3. Gather information from reputable financial sources.\n"
            f"4. Compile all raw findings into a structured summary.\n\n"
            f"Use the web_search_scraper tool to search and collect data."
        ),
        expected_output=(
            "A comprehensive research summary containing:\n"
            "- Key financial metrics found (revenue, growth, market cap, etc.)\n"
            "- Market trends and competitive landscape overview\n"
            "- Source URLs for data verification\n"
            "- Raw data points suitable for further analysis"
        ),
    )

    # ----- Task 2: Financial Data Analysis -----
    analysis_task = Task(
        description=(
            f"Analyze the financial dataset and research findings.\n\n"
            f"Your objectives:\n"
            f"1. Load and analyze the financial metrics from the CSV file at: "
            f"   '{csv_path}' using the calculate_financial_metrics tool.\n"
            f"2. Compute summary statistics (mean, min, max, standard deviation) "
            f"   for all numeric columns.\n"
            f"3. Identify key trends, outliers, and notable patterns in the data.\n"
            f"4. Cross-reference the statistical findings with the research data "
            f"   gathered in the previous task.\n"
            f"5. Verify numeric consistency and flag any discrepancies.\n\n"
            f"Use the calculate_financial_metrics tool with the path '{csv_path}'."
        ),
        expected_output=(
            "A detailed analytical report containing:\n"
            "- Markdown table of summary statistics (from Pandas describe())\n"
            "- Key insights and trend analysis\n"
            "- Notable outliers or anomalies\n"
            "- Data quality assessment\n"
            "- Cross-reference notes with research findings"
        ),
    )

    # ----- Task 3: Report Writing -----
    report_task = Task(
        description=(
            f"Write a comprehensive, professional market research report based on "
            f"the research findings and data analysis.\n\n"
            f"**Report Topic:** {query}\n\n"
            f"Your report MUST include the following sections:\n"
            f"1. **Executive Summary** – A concise overview of key findings.\n"
            f"2. **Methodology** – Brief description of data sources and methods.\n"
            f"3. **Market Overview** – Current state of the market based on research.\n"
            f"4. **Financial Analysis** – Detailed breakdown of the statistical "
            f"   findings, including the Pandas summary statistics table.\n"
            f"5. **Key Insights & Trends** – Major patterns and observations.\n"
            f"6. **Risk Factors** – Potential risks and market headwinds.\n"
            f"7. **Recommendations** – Actionable insights for stakeholders.\n"
            f"8. **Conclusion** – Summary of the overall assessment.\n\n"
            f"Format the report in Markdown with clear headers, bullet points, "
            f"and include any data tables from the analysis."
        ),
        expected_output=(
            "A complete, professionally formatted Markdown report with:\n"
            "- Executive Summary\n"
            "- Methodology section\n"
            "- Market Overview\n"
            "- Financial Analysis with data tables\n"
            "- Key Insights & Trends\n"
            "- Risk Factors\n"
            "- Recommendations\n"
            "- Conclusion\n"
            "The report should be publication-ready and data-driven."
        ),
        output_file="output/market_report.md",
    )

    tasks = [research_task, analysis_task, report_task]
    logger.info("Created %d tasks for query: '%s'", len(tasks), query)
    return tasks
