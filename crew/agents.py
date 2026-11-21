"""
CrewAI Agent Definitions

Defines three specialized agents for the hierarchical market research crew:
  1. Lead Researcher Agent  – searches and scrapes financial data
  2. Data Analyst Agent     – parses and analyses data with Pandas
  3. Content Writer Agent   – synthesizes findings into a structured report
"""

import logging
from crewai import Agent
from crew.tools import web_search_scraper, calculate_financial_metrics

logger = logging.getLogger(__name__)


def create_agents() -> dict[str, Agent]:
    """
    Instantiate and return the three specialized CrewAI agents.

    Returns:
        Dictionary mapping agent names to Agent instances.
    """
    # ----- Agent 1: Lead Researcher -----
    researcher = Agent(
        role="Market Research Specialist",
        goal=(
            "Query search search networks, locate financial data, and scrape company metrics."
        ),
        backstory=(
            "You are a seasoned market research specialist with 15 years of "
            "experience in financial analysis. You have deep expertise in "
            "identifying reliable data sources, extracting key financial metrics, "
            "and distinguishing credible information from noise. You are known "
            "for your thorough and methodical approach to data collection."
        ),
        tools=[web_search_scraper],
        verbose=True,
        allow_delegation=False,
    )

    # ----- Agent 2: Data Analyst -----
    analyst = Agent(
        role="Financial Data Analyst",
        goal=(
            "Parse data matrices using Pandas, compute averages, and verify numeric consistency."
        ),
        backstory=(
            "You are an expert quantitative analyst with a strong background "
            "in statistical analysis and financial modeling. You excel at "
            "processing large datasets, identifying trends, computing key "
            "financial ratios, and presenting data in clear tabular formats. "
            "You always validate your calculations for accuracy."
        ),
        tools=[calculate_financial_metrics],
        verbose=True,
        allow_delegation=False,
    )

    # ----- Agent 3: Content Writer -----
    writer = Agent(
        role="Technical Reports Writer",
        goal=(
            "Synthesize information, write sections, and structure copy."
        ),
        backstory=(
            "You are a professional technical writer specializing in financial "
            "reports and market analyses. You have written hundreds of research "
            "reports for Fortune 500 companies. Your writing is clear, concise, "
            "and always backed by data. You structure reports with executive "
            "summaries, methodology sections, findings, and recommendations."
        ),
        tools=[],
        verbose=True,
        allow_delegation=False,
    )

    agents = {
        "researcher": researcher,
        "analyst": analyst,
        "writer": writer,
    }

    logger.info(
        "Created %d agents: %s",
        len(agents),
        ", ".join(agents.keys()),
    )

    return agents
