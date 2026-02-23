"""
MLflow backtest exporter.

Orchestrates the extraction of backtest data from a pysystemtrade System
object and logs it to an MLflow tracking server.

If MLflow is not configured in private_config.yaml, all export functions
are silently no-ops.
"""

import os
import shutil
import tempfile
from datetime import datetime
from typing import Dict, Optional

from sysmlflow.config import MLflowConfig
from sysmlflow.extractors import (
    extract_instrument_metrics,
    extract_parameters,
    extract_portfolio_metrics,
    extract_rule_metrics,
    extract_timeseries,
)
from sysmlflow.utils import dataframe_to_temp_csv

try:
    import mlflow

    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class MLflowBacktestExporter:
    """Exports pysystemtrade backtest results to MLflow.

    Usage:
        exporter = MLflowBacktestExporter()  # reads from private_config.yaml
        run_id = exporter.export(system, run_name="my_backtest")

    If MLflow is not configured or not installed, all methods are silent no-ops.
    """

    def __init__(self, config: Optional[MLflowConfig] = None):
        if config is None:
            config = MLflowConfig.from_private_config()

        self._config = config
        self._enabled = config is not None and MLFLOW_AVAILABLE

        if self._enabled:
            mlflow.set_tracking_uri(config.tracking_uri)

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def config(self) -> Optional[MLflowConfig]:
        return self._config

    def export(
        self,
        system,
        run_name: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Export a completed backtest to MLflow.

        Args:
            system: A pysystemtrade System object that has been run.
            run_name: Optional name for the MLflow run. Defaults to a
                      timestamped name.
            tags: Optional dict of additional tags for the run.

        Returns:
            The MLflow run_id, or None if MLflow is not enabled.
        """
        if not self._enabled:
            return None

        if run_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"backtest_{timestamp}"

        mlflow.set_experiment(self._config.experiment_name)

        with mlflow.start_run(run_name=run_name) as run:
            run_id = run.info.run_id

            # ── Tags ──
            run_tags = {
                "framework": "pysystemtrade",
                "export_timestamp": datetime.now().isoformat(),
            }
            try:
                instruments = system.get_instrument_list()
                run_tags["instrument_count"] = str(len(instruments))
            except Exception:
                pass
            try:
                rules = system.rules.trading_rules()
                run_tags["rule_count"] = str(len(rules))
            except Exception:
                pass
            if tags:
                run_tags.update(tags)
            mlflow.set_tags(run_tags)

            # ── Parameters ──
            self._log_parameters(system)

            # ── Metrics ──
            self._log_metrics(system)

            # ── Artifacts (timeseries CSVs) ──
            self._log_artifacts(system)

            # ── Config YAML artifact ──
            self._log_config_artifact(system)

        return run_id

    def _log_parameters(self, system):
        """Log system configuration as MLflow parameters."""
        params = extract_parameters(system)
        if not params:
            return

        # MLflow has a limit of 100 params per batch call
        param_items = list(params.items())
        batch_size = 100
        for i in range(0, len(param_items), batch_size):
            batch = dict(param_items[i : i + batch_size])
            try:
                mlflow.log_params(batch)
            except Exception:
                # Log individually if batch fails
                for key, value in batch.items():
                    try:
                        mlflow.log_param(key, value)
                    except Exception:
                        pass

    def _log_metrics(self, system):
        """Log all performance metrics to MLflow."""
        all_metrics: Dict[str, float] = {}

        # Portfolio-level
        all_metrics.update(extract_portfolio_metrics(system))

        # Per-instrument
        all_metrics.update(extract_instrument_metrics(system))

        # Per-rule
        all_metrics.update(extract_rule_metrics(system))

        if not all_metrics:
            return

        # MLflow batch metric logging
        try:
            mlflow.log_metrics(all_metrics)
        except Exception:
            # Fall back to individual logging
            for key, value in all_metrics.items():
                try:
                    mlflow.log_metric(key, value)
                except Exception:
                    pass

    def _log_artifacts(self, system):
        """Log timeseries data as CSV artifacts."""
        timeseries = extract_timeseries(system)
        if not timeseries:
            return

        temp_dirs = []
        try:
            for name, df in timeseries.items():
                csv_path = dataframe_to_temp_csv(df, name)
                temp_dirs.append(os.path.dirname(csv_path))
                try:
                    mlflow.log_artifact(csv_path, artifact_path="timeseries")
                except Exception:
                    pass
        finally:
            # Cleanup temp files
            for temp_dir in temp_dirs:
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass

    def _log_config_artifact(self, system):
        """Log the system config as a YAML artifact."""
        try:
            import yaml

            config_dict = system.config.as_dict()
            temp_dir = tempfile.mkdtemp(prefix="sysmlflow_config_")
            config_path = os.path.join(temp_dir, "system_config.yaml")

            with open(config_path, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False)

            mlflow.log_artifact(config_path, artifact_path="config")
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


def export_backtest_to_mlflow(
    system,
    run_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    config: Optional[MLflowConfig] = None,
) -> Optional[str]:
    """Convenience function to export a backtest to MLflow in one call.

    Reads MLflow configuration from private_config.yaml. If MLflow is not
    configured, silently returns None.

    Args:
        system: A pysystemtrade System object that has been run.
        run_name: Optional name for the MLflow run.
        tags: Optional dict of additional tags.
        config: Optional MLflowConfig override (for testing).

    Returns:
        The MLflow run_id, or None if MLflow is not enabled.

    Example:
        from systems.provided.futures_chapter15.basesystem import futures_system
        from sysmlflow import export_backtest_to_mlflow

        system = futures_system()
        run_id = export_backtest_to_mlflow(system, run_name="chapter15_test")
    """
    exporter = MLflowBacktestExporter(config=config)
    return exporter.export(system, run_name=run_name, tags=tags)
