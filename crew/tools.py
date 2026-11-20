"""
Custom Data Collection & Financial Tools

Provides two @tool-decorated functions for the CrewAI agents:
  1. web_search_scraper  – searches via Tavily / SerperDev and scrapes page text.
  2. calculate_financial_metrics – loads a CSV into Pandas and returns summary stats.
"""

import os
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from crewai.tools import tool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool 1: Web Scraper integrating with Search APIs
# ---------------------------------------------------------------------------

@tool
def web_search_scraper(query: str) -> str:
    """
    Searches the web for market data and financial information using Tavily
    or SerperDev APIs, then scrapes raw text from the top results.

    Args:
        query: The search query string (e.g. 'Tech Sector Q3 2024 revenue').

    Returns:
        Concatenated text snippets scraped from the top search results.
    """
    urls: list[str] = []
    snippets: list[str] = []

    tavily_key = os.getenv("TAVILY_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")

    # ---- Tavily search ----
    if tavily_key:
        try:
            logger.info("Searching via Tavily API for: %s", query)
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": 5,
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for result in data.get("results", []):
                urls.append(result.get("url", ""))
                snippets.append(result.get("content", ""))
            logger.info("Tavily returned %d results", len(urls))
        except Exception as exc:
            logger.warning("Tavily search failed: %s", exc)

    # ---- SerperDev fallback ----
    if not urls and serper_key:
        try:
            logger.info("Searching via SerperDev API for: %s", query)
            resp = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": serper_key, "Content-Type": "application/json"},
                json={"q": query, "num": 5},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("organic", []):
                urls.append(item.get("link", ""))
                snippets.append(item.get("snippet", ""))
            logger.info("SerperDev returned %d results", len(urls))
        except Exception as exc:
            logger.warning("SerperDev search failed: %s", exc)

    # ---- Scrape raw page text from top URLs ----
    scraped_sections: list[str] = []
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    for idx, url in enumerate(urls[:3]):
        if not url:
            continue
        try:
            page = requests.get(url, headers=headers, timeout=15)
            page.raise_for_status()
            soup = BeautifulSoup(page.text, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            # Trim to first 2000 chars per page
            trimmed = text[:2000]
            scraped_sections.append(
                f"--- Source {idx + 1}: {url} ---\n{trimmed}"
            )
        except Exception as exc:
            logger.warning("Failed to scrape %s: %s", url, exc)
            # Fall back to snippet if scraping fails
            if idx < len(snippets) and snippets[idx]:
                scraped_sections.append(
                    f"--- Source {idx + 1}: {url} (snippet) ---\n{snippets[idx]}"
                )

    if not scraped_sections:
        # If no live data, provide informative message
        return (
            f"No live search results retrieved for query: '{query}'. "
            "Please verify that TAVILY_API_KEY or SERPER_API_KEY is set in .env. "
            "Proceeding with available data."
        )

    return "\n\n".join(scraped_sections)


# ---------------------------------------------------------------------------
# Tool 2: Financial Data Parser using Pandas
# ---------------------------------------------------------------------------

@tool
def calculate_financial_metrics(csv_path: str) -> str:
    """
    Loads corporate metrics from a CSV file and returns summary statistics
    as a formatted Markdown table.

    The tool calculates count, mean, std, min, 25%, 50%, 75%, and max
    for every numeric column in the dataset.

    Args:
        csv_path: Absolute or relative path to the CSV file containing
                  financial metrics (e.g. 'data/sample_metrics.csv').

    Returns:
        A Markdown-formatted table of descriptive statistics.
    """
    if not os.path.exists(csv_path):
        return f"Error: File not found at '{csv_path}'. Please provide a valid CSV path."

    try:
        df = pd.read_csv(csv_path)
        logger.info(
            "Loaded CSV with %d rows and %d columns: %s",
            len(df), len(df.columns), list(df.columns),
        )

        # Compute descriptive statistics for numeric columns
        summary = df.describe()

        # Round for readability
        summary = summary.round(2)

        # Convert to Markdown
        markdown_table = summary.to_markdown()

        # Also add column info
        col_info = "\n\n**Dataset Columns:** " + ", ".join(df.columns.tolist())
        row_info = f"\n**Total Records:** {len(df)}"

        return markdown_table + col_info + row_info

    except Exception as exc:
        logger.error("Failed to process CSV '%s': %s", csv_path, exc)
        return f"Error processing CSV file: {exc}"
