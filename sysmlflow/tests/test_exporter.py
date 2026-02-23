"""Tests for sysmlflow.exporter module using mocked MLflow."""

from unittest.mock import MagicMock, patch, ANY
import pytest

from sysmlflow.config import MLflowConfig
from sysmlflow.exporter import MLflowBacktestExporter, export_backtest_to_mlflow


@pytest.fixture
def mock_config():
    return MLflowConfig(
        tracking_uri="http://test-server:5000",
        experiment_name="test_experiment",
    )


@pytest.fixture
def mock_system():
    """Create a minimal mock system with the attributes the exporter needs."""
    system = MagicMock()

    # Mock instrument list
    system.get_instrument_list.return_value = ["SOFR", "SP500"]

    # Mock trading rules
    system.rules.trading_rules.return_value = {
        "ewmac2_8": MagicMock(),
        "ewmac8_32": MagicMock(),
    }

    # Mock config
    system.config.as_dict.return_value = {
        "percentage_vol_target": 16.0,
        "notional_trading_capital": 1000000,
    }

    # Mock accounts.portfolio()
    mock_portfolio = MagicMock()
    mock_portfolio.asset_columns = ["SOFR", "SP500"]
    mock_portfolio.percent = MagicMock()

    # All stat methods return 0.5
    for attr in [
        "sharpe",
        "sortino",
        "calmar",
        "ann_mean",
        "ann_std",
        "avg_drawdown",
        "worst_drawdown",
        "time_in_drawdown",
        "hitrate",
        "profitfactor",
        "gaintolossratio",
        "t_stat",
        "p_value",
        "skew",
        "min",
        "max",
        "median",
        "mean",
        "std",
        "avg_loss",
        "avg_gain",
    ]:
        getattr(mock_portfolio.percent, attr).return_value = 0.5
        getattr(mock_portfolio.percent.gross, attr).return_value = 0.6
        getattr(mock_portfolio.percent.costs, attr).return_value = 0.1

    system.accounts.portfolio.return_value = mock_portfolio
    system.accounts.total_portfolio_level_turnover.return_value = 5.0

    # Mock pandl_for_all_trading_rules
    mock_rules_pandl = MagicMock()
    mock_rules_pandl.asset_columns = ["ewmac2_8", "ewmac8_32"]
    system.accounts.pandl_for_all_trading_rules.return_value = mock_rules_pandl

    # Mock capital
    system.positionSize.get_notional_capital.return_value = 1000000

    return system


class TestMLflowBacktestExporter:
    @patch("sysmlflow.exporter.MLFLOW_AVAILABLE", True)
    @patch("sysmlflow.exporter.mlflow")
    def test_export_creates_run(self, mock_mlflow, mock_config, mock_system):
        exporter = MLflowBacktestExporter(config=mock_config)
        exporter.export(mock_system, run_name="test_run")

        mock_mlflow.set_tracking_uri.assert_called_once_with("http://test-server:5000")
        mock_mlflow.set_experiment.assert_called_once_with("test_experiment")
        mock_mlflow.start_run.assert_called_once()

    @patch("sysmlflow.exporter.MLFLOW_AVAILABLE", True)
    @patch("sysmlflow.exporter.mlflow")
    def test_export_logs_tags(self, mock_mlflow, mock_config, mock_system):
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value.info.run_id = "abc123"

        exporter = MLflowBacktestExporter(config=mock_config)
        exporter.export(mock_system, run_name="test_run")

        mock_mlflow.set_tags.assert_called_once()
        tags_arg = mock_mlflow.set_tags.call_args[0][0]
        assert tags_arg["framework"] == "pysystemtrade"
        assert "instrument_count" in tags_arg

    @patch("sysmlflow.exporter.MLFLOW_AVAILABLE", True)
    @patch("sysmlflow.exporter.mlflow")
    def test_export_logs_metrics(self, mock_mlflow, mock_config, mock_system):
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value.info.run_id = "abc123"

        exporter = MLflowBacktestExporter(config=mock_config)
        exporter.export(mock_system, run_name="test_run")

        mock_mlflow.log_metrics.assert_called()

    @patch("sysmlflow.exporter.MLFLOW_AVAILABLE", True)
    @patch("sysmlflow.exporter.mlflow")
    def test_export_returns_run_id(self, mock_mlflow, mock_config, mock_system):
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value.info.run_id = "abc123"

        exporter = MLflowBacktestExporter(config=mock_config)
        result = exporter.export(mock_system, run_name="test_run")
        assert result == "abc123"


class TestDisabledExporter:
    def test_no_config_returns_none(self, mock_system):
        exporter = MLflowBacktestExporter(config=None)
        assert exporter.enabled is False
        result = exporter.export(mock_system)
        assert result is None


class TestConvenienceFunction:
    @patch("sysmlflow.exporter.MLFLOW_AVAILABLE", True)
    @patch("sysmlflow.exporter.mlflow")
    def test_export_backtest_to_mlflow(self, mock_mlflow, mock_config, mock_system):
        mock_mlflow.start_run.return_value.__enter__ = MagicMock()
        mock_mlflow.start_run.return_value.__exit__ = MagicMock()
        mock_mlflow.start_run.return_value.__enter__.return_value.info.run_id = "def456"

        result = export_backtest_to_mlflow(
            mock_system,
            run_name="test",
            config=mock_config,
        )
        assert result == "def456"
