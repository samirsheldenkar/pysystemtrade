"""
MLflow connection configuration.

Reads MLflow settings from the existing pysystemtrade private_config.yaml.
If the mlflow section is not present, the module returns None to signal
that MLflow export should be silently skipped.

Expected private_config.yaml structure:
    mlflow:
      tracking_uri: "http://your-mlflow-server:5000"
      experiment_name: "pysystemtrade_backtests"   # optional
"""

from dataclasses import dataclass
from typing import Optional

from sysdata.config.private_config import get_private_config_as_dict

MLFLOW_CONFIG_KEY = "mlflow"
DEFAULT_EXPERIMENT_NAME = "pysystemtrade_backtests"


@dataclass(frozen=True)
class MLflowConfig:
    """Holds MLflow connection settings."""

    tracking_uri: str
    experiment_name: str

    @staticmethod
    def from_private_config() -> Optional["MLflowConfig"]:
        """Read MLflow config from private_config.yaml.

        Returns None if the mlflow section is absent, signalling that
        MLflow export should be silently skipped.
        """
        private_dict = get_private_config_as_dict()
        mlflow_section = private_dict.get(MLFLOW_CONFIG_KEY)

        if mlflow_section is None:
            return None

        tracking_uri = mlflow_section.get("tracking_uri")
        if not tracking_uri:
            return None

        experiment_name = mlflow_section.get("experiment_name", DEFAULT_EXPERIMENT_NAME)

        return MLflowConfig(
            tracking_uri=tracking_uri,
            experiment_name=experiment_name,
        )

    @staticmethod
    def from_dict(config_dict: dict) -> Optional["MLflowConfig"]:
        """Create config from an explicit dict (useful for testing)."""
        tracking_uri = config_dict.get("tracking_uri")
        if not tracking_uri:
            return None

        experiment_name = config_dict.get("experiment_name", DEFAULT_EXPERIMENT_NAME)

        return MLflowConfig(
            tracking_uri=tracking_uri,
            experiment_name=experiment_name,
        )
