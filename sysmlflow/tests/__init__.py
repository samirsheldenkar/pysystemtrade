"""Tests for sysmlflow.extractors module."""

import pytest
import pandas as pd

from systems.provided.futures_chapter15.basesystem import futures_system
from sysmlflow.extractors import (
    extract_portfolio_metrics,
    extract_instrument_metrics,
    extract_rule_metrics,
    extract_parameters,
    extract_timeseries,
    PORTFOLIO_STAT_METHODS,
)
from sysmlflow.utils import (
    sanitise_metric_name,
    flatten_dict,
    safe_float,
    truncate_param_value,
)


@pytest.fixture(scope="module")
def backtest_system():
    """Create a futures system for testing. Cached for the module."""
    system = futures_system()
    # Trigger the portfolio calculation so it's cached
    _ = system.accounts.portfolio()
    return system


class TestUtils:
    def test_sanitise_metric_name_clean(self):
        assert sanitise_metric_name("sharpe") == "sharpe"

    def test_sanitise_metric_name_special_chars(self):
        result = sanitise_metric_name("portfolio (net) ~sharpe")
        assert "(" not in result
        assert ")" not in result
        assert "~" not in result

    def test_sanitise_metric_name_slashes_preserved(self):
        result = sanitise_metric_name("instrument/SOFR/sharpe")
        assert result == "instrument/SOFR/sharpe"

    def test_sanitise_metric_name_truncation(self):
        long_name = "a" * 300
        result = sanitise_metric_name(long_name)
        assert len(result) == 250

    def test_flatten_dict_simple(self):
        d = {"a": 1, "b": 2}
        assert flatten_dict(d) == {"a": 1, "b": 2}

    def test_flatten_dict_nested(self):
        d = {"a": {"b": 1, "c": 2}}
        result = flatten_dict(d)
        assert result == {"a/b": 1, "a/c": 2}

    def test_flatten_dict_deep(self):
        d = {"a": {"b": {"c": 3}}}
        result = flatten_dict(d)
        assert result == {"a/b/c": 3}

    def test_safe_float_valid(self):
        assert safe_float(3.14) == 3.14
        assert safe_float(42) == 42.0
        assert safe_float("2.5") == 2.5

    def test_safe_float_nan(self):
        assert safe_float(float("nan")) is None

    def test_safe_float_inf(self):
        assert safe_float(float("inf")) is None

    def test_safe_float_invalid(self):
        assert safe_float("not_a_number") is None
        assert safe_float(None) is None

    def test_truncate_param_value(self):
        short = "hello"
        assert truncate_param_value(short) == "hello"

        long_val = "x" * 600
        result = truncate_param_value(long_val)
        assert len(result) == 500
        assert result.endswith("...")


class TestPortfolioMetrics:
    def test_returns_dict(self, backtest_system):
        metrics = extract_portfolio_metrics(backtest_system)
        assert isinstance(metrics, dict)

    def test_has_key_metrics(self, backtest_system):
        metrics = extract_portfolio_metrics(backtest_system)
        assert "portfolio/net/sharpe" in metrics
        assert "portfolio/net/ann_mean" in metrics
        assert "portfolio/net/ann_std" in metrics

    def test_all_values_are_floats(self, backtest_system):
        metrics = extract_portfolio_metrics(backtest_system)
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is {type(value)}, expected float"

    def test_gross_metrics_present(self, backtest_system):
        metrics = extract_portfolio_metrics(backtest_system)
        assert "portfolio/gross/sharpe" in metrics

    def test_turnover_present(self, backtest_system):
        metrics = extract_portfolio_metrics(backtest_system)
        assert "portfolio/total_turnover" in metrics


class TestInstrumentMetrics:
    def test_returns_dict(self, backtest_system):
        metrics = extract_instrument_metrics(backtest_system)
        assert isinstance(metrics, dict)

    def test_has_instrument_keys(self, backtest_system):
        metrics = extract_instrument_metrics(backtest_system)
        # Should have at least one instrument
        assert len(metrics) > 0
        # Keys should follow the pattern instrument/{code}/{stat}
        for key in metrics:
            parts = key.split("/")
            assert parts[0] == "instrument"
            assert len(parts) == 3

    def test_all_values_are_floats(self, backtest_system):
        metrics = extract_instrument_metrics(backtest_system)
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is {type(value)}"


class TestRuleMetrics:
    def test_returns_dict(self, backtest_system):
        metrics = extract_rule_metrics(backtest_system)
        assert isinstance(metrics, dict)

    def test_has_rule_keys(self, backtest_system):
        metrics = extract_rule_metrics(backtest_system)
        assert len(metrics) > 0
        for key in metrics:
            parts = key.split("/")
            assert parts[0] == "rule"
            assert len(parts) == 3

    def test_all_values_are_floats(self, backtest_system):
        metrics = extract_rule_metrics(backtest_system)
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is {type(value)}"


class TestParameters:
    def test_returns_dict(self, backtest_system):
        params = extract_parameters(backtest_system)
        assert isinstance(params, dict)

    def test_has_instrument_count(self, backtest_system):
        params = extract_parameters(backtest_system)
        assert "instrument_count" in params

    def test_has_rule_count(self, backtest_system):
        params = extract_parameters(backtest_system)
        assert "rule_count" in params

    def test_all_values_are_strings(self, backtest_system):
        params = extract_parameters(backtest_system)
        for key, value in params.items():
            assert isinstance(value, str), f"{key} is {type(value)}"

    def test_values_not_too_long(self, backtest_system):
        params = extract_parameters(backtest_system)
        for key, value in params.items():
            assert len(value) <= 500, f"{key} value is {len(value)} chars"


class TestTimeseries:
    def test_returns_dict(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        assert isinstance(ts, dict)

    def test_has_portfolio_equity_curve(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        assert "portfolio_equity_curve" in ts
        assert isinstance(ts["portfolio_equity_curve"], pd.DataFrame)

    def test_has_daily_returns(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        assert "portfolio_daily_returns" in ts
        assert isinstance(ts["portfolio_daily_returns"], pd.DataFrame)

    def test_has_instrument_returns(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        assert "instrument_returns" in ts
        assert isinstance(ts["instrument_returns"], pd.DataFrame)

    def test_has_positions(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        assert "positions" in ts
        assert isinstance(ts["positions"], pd.DataFrame)

    def test_dataframes_have_data(self, backtest_system):
        ts = extract_timeseries(backtest_system)
        for name, df in ts.items():
            assert len(df) > 0, f"{name} is empty"
