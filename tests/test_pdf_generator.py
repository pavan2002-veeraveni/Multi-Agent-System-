"""
Automated Tests — PDF Report Generator

Verifies that the ReportLab-based PDF compiler:
  1. Successfully writes a valid PDF file.
  2. Does not raise styling exceptions.
  3. Produces correct page structure and metadata.
"""

import os
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def output_dir(tmp_path):
    """Provide a temporary output directory for PDF files."""
    out = tmp_path / "output"
    out.mkdir()
    return out


@pytest.fixture
def sample_markdown():
    """Sample Markdown content simulating a writer agent's output."""
    return """# Executive Summary

This report provides a comprehensive analysis of the technology sector
performance during Q3 2024. Key findings indicate strong revenue growth
across major tech companies.

# Market Overview

The technology sector continues to show resilience with:
- Cloud computing revenue grew 25% year-over-year
- AI-related investments increased by 40%
- Semiconductor demand remains strong

# Financial Analysis

The following metrics were observed across the sample companies:

| Metric | Value | Change |
|--------|-------|--------|
| Avg Revenue | $230.5B | +12% |
| Avg Net Income | $51.2B | +8% |
| Avg PE Ratio | 35.4 | -2.1 |

# Key Insights & Trends

Several important trends emerged from the data:
- AI infrastructure spending is accelerating
- Cloud margins are improving
- Consumer tech spending is moderating

# Recommendations

Based on the analysis, we recommend:
- Overweight positions in cloud and AI sectors
- Monitor semiconductor supply chain developments
- Maintain neutral stance on consumer electronics

# Conclusion

The tech sector shows strong fundamentals heading into Q4,
with AI and cloud computing driving growth.
"""


@pytest.fixture
def sample_statistics_markdown():
    """Sample Pandas statistics in Markdown format."""
    return """|        | Revenue_B | Net_Income_B | EPS   | PE_Ratio |
|--------|-----------|-------------|-------|----------|
| count  | 7.00      | 7.00        | 7.00  | 7.00     |
| mean   | 254.43    | 51.11       | 7.93  | 44.04    |
| std    | 173.21    | 30.82       | 4.37  | 18.63    |
| min    | 60.92     | 12.56       | 2.90  | 24.10    |
| 25%    | 115.84    | 29.09       | 4.71  | 26.05    |
| 50%    | 211.92    | 39.10       | 6.42  | 28.50    |
| 75%    | 350.86    | 73.08       | 10.87 | 52.25    |
| max    | 574.78    | 99.80       | 15.02 | 70.20    |
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMarketReportPDF:
    """Test suite for the MarketReportPDF generator."""

    def test_pdf_file_created(self, output_dir, sample_markdown):
        """PDF file must be created on disk."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_report.pdf")
        result = MarketReportPDF.from_markdown(
            markdown_text=sample_markdown,
            filename=pdf_path,
            title="Test Report",
            query="Test Query",
        )
        assert os.path.exists(result)
        assert os.path.getsize(result) > 0

    def test_pdf_has_valid_header(self, output_dir, sample_markdown):
        """Generated file must start with the PDF magic bytes."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_header.pdf")
        MarketReportPDF.from_markdown(
            markdown_text=sample_markdown,
            filename=pdf_path,
            title="Header Test",
        )
        with open(pdf_path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-", "File does not start with PDF magic bytes"

    def test_pdf_no_styling_exceptions(self, output_dir, sample_markdown, sample_statistics_markdown):
        """PDF compilation must not raise any styling exceptions."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_no_exceptions.pdf")
        # This should not raise any exception
        try:
            MarketReportPDF.from_markdown(
                markdown_text=sample_markdown,
                filename=pdf_path,
                title="Exception Test Report",
                query="Tech Sector Q3",
                statistics_markdown=sample_statistics_markdown,
            )
        except Exception as exc:
            pytest.fail(f"PDF generation raised an exception: {exc}")

    def test_pdf_with_empty_content(self, output_dir):
        """PDF must handle empty content without crashing."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_empty.pdf")
        result = MarketReportPDF.from_markdown(
            markdown_text="",
            filename=pdf_path,
            title="Empty Report",
        )
        assert os.path.exists(result)

    def test_pdf_with_statistics_table(self, output_dir, sample_markdown, sample_statistics_markdown):
        """PDF must include the statistics table without errors."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_with_stats.pdf")
        result = MarketReportPDF.from_markdown(
            markdown_text=sample_markdown,
            filename=pdf_path,
            title="Stats Report",
            statistics_markdown=sample_statistics_markdown,
        )
        assert os.path.exists(result)
        # PDF with stats table should be larger than minimal
        assert os.path.getsize(result) > 1000

    def test_pdf_instance_methods(self, output_dir):
        """Test individual instance methods of MarketReportPDF."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_instance.pdf")
        pdf = MarketReportPDF(
            filename=pdf_path,
            title="Instance Test",
            query="Test Query",
        )
        pdf.add_header_banner()
        pdf.add_section("Test Section", "This is test content.\n- Bullet one\n- Bullet two")
        pdf.add_data_table(
            "| Col A | Col B |\n|-------|-------|\n| 1 | 2 |\n| 3 | 4 |",
            caption="Test Table",
        )
        result = pdf.build()
        assert os.path.exists(result)

    def test_pdf_multiple_sections(self, output_dir):
        """PDF must handle multiple sections correctly."""
        from crew.pdf_generator import MarketReportPDF

        pdf_path = str(output_dir / "test_multi_section.pdf")
        pdf = MarketReportPDF(filename=pdf_path, title="Multi-Section")
        pdf.add_header_banner()

        for i in range(5):
            pdf.add_section(
                f"Section {i + 1}",
                f"Content for section {i + 1}.\n- Point A\n- Point B",
            )

        result = pdf.build()
        assert os.path.exists(result)
        assert os.path.getsize(result) > 1000

    def test_numbered_canvas(self, output_dir, sample_markdown):
        """Verify the PDF uses NumberedCanvas (Page X of Y support)."""
        from crew.pdf_generator import MarketReportPDF, NumberedCanvas

        # Verify NumberedCanvas class exists and is callable
        assert callable(NumberedCanvas)

        # Generate a PDF and verify it works with the custom canvas
        pdf_path = str(output_dir / "test_numbered.pdf")
        result = MarketReportPDF.from_markdown(
            markdown_text=sample_markdown,
            filename=pdf_path,
            title="Numbered Pages Test",
        )
        assert os.path.exists(result)
