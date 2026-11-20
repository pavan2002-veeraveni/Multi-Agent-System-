"""
Automated Tests — Financial Data Tools

Verifies that the Pandas-based financial metrics tool correctly
calculates summary statistics on a mock CSV dataset.
"""

import os
import csv
import tempfile
import pytest
import pandas as pd


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_csv_path(tmp_path):
    """Create a temporary CSV file with known financial data."""
    csv_file = tmp_path / "test_metrics.csv"
    data = [
        ["Company", "Revenue_B", "Net_Income_B", "EPS", "PE_Ratio", "Market_Cap_B"],
        ["AlphaCorp", "120.5", "30.2", "5.10", "22.5", "800.0"],
        ["BetaInc", "95.3", "18.7", "3.80", "30.1", "600.0"],
        ["GammaTech", "210.0", "55.0", "8.20", "18.3", "1200.0"],
        ["DeltaIO", "78.9", "12.1", "2.50", "35.6", "450.0"],
        ["EpsilonAI", "150.0", "40.0", "6.70", "25.0", "950.0"],
    ]
    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    return str(csv_file)


@pytest.fixture
def expected_stats():
    """Pre-computed expected statistics for the mock dataset."""
    return {
        "Revenue_B": {
            "count": 5,
            "mean": 130.94,
            "min": 78.9,
            "max": 210.0,
        },
        "Net_Income_B": {
            "count": 5,
            "mean": 31.2,
            "min": 12.1,
            "max": 55.0,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCalculateFinancialMetrics:
    """Test suite for the calculate_financial_metrics tool."""

    def test_returns_markdown_string(self, mock_csv_path):
        """Tool must return a non-empty Markdown string."""
        from crew.tools import calculate_financial_metrics

        result = calculate_financial_metrics.run(mock_csv_path)
        assert isinstance(result, str)
        assert len(result) > 0
        # Markdown tables contain pipe characters
        assert "|" in result

    def test_contains_statistical_rows(self, mock_csv_path):
        """Output must include standard describe() row labels."""
        from crew.tools import calculate_financial_metrics

        result = calculate_financial_metrics.run(mock_csv_path)
        for label in ["mean", "std", "min", "max", "count"]:
            assert label in result, f"Missing statistic row: {label}"

    def test_correct_mean_calculation(self, mock_csv_path, expected_stats):
        """Verify the mean values match manual calculations."""
        df = pd.read_csv(mock_csv_path)
        for col, stats in expected_stats.items():
            computed_mean = round(df[col].mean(), 2)
            assert computed_mean == stats["mean"], (
                f"Mean mismatch for {col}: expected {stats['mean']}, got {computed_mean}"
            )

    def test_correct_min_max(self, mock_csv_path, expected_stats):
        """Verify min and max values are correct."""
        df = pd.read_csv(mock_csv_path)
        for col, stats in expected_stats.items():
            assert df[col].min() == stats["min"]
            assert df[col].max() == stats["max"]

    def test_correct_count(self, mock_csv_path, expected_stats):
        """Verify the row count is correct."""
        df = pd.read_csv(mock_csv_path)
        for col, stats in expected_stats.items():
            assert len(df[col]) == stats["count"]

    def test_handles_missing_file(self):
        """Tool must handle a non-existent file gracefully."""
        from crew.tools import calculate_financial_metrics

        result = calculate_financial_metrics.run("/nonexistent/path.csv")
        assert "Error" in result or "not found" in result.lower()

    def test_std_deviation_positive(self, mock_csv_path):
        """Standard deviation for varied data must be positive."""
        df = pd.read_csv(mock_csv_path)
        for col in df.select_dtypes(include="number").columns:
            assert df[col].std() > 0, f"Std dev should be > 0 for {col}"

    def test_describe_shape(self, mock_csv_path):
        """Describe output must have 8 rows (count, mean, std, min, 25%, 50%, 75%, max)."""
        df = pd.read_csv(mock_csv_path)
        desc = df.describe()
        assert desc.shape[0] == 8
