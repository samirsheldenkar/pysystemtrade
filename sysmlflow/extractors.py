"""
Data extractors for pysystemtrade backtest results.

Each function accepts a pysystemtrade System object that has been fully
run (i.e. system.accounts.portfolio() is callable) and returns structured
data suitable for logging to MLflow.
"""

from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd

from sysmlflow.utils import safe_float, sanitise_metric_name, is_scalar, truncate_param_value


# ──────────────────────────────────────────────────────────────────────
# Portfolio-level metrics
# ──────────────────────────────────────────────────────────────────────

PORTFOLIO_STAT_METHODS = [
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
]


def extract_portfolio_metrics(system) -> Dict[str, float]:
    """Extract all portfolio-level performance statistics.

    Returns a flat dict of metric_name -> float. Keys are prefixed
    with 'portfolio/' and include net, gross, and costs variants for
    key stats.
    """
    metrics: Dict[str, float] = {}

    portfolio_curve = system.accounts.portfolio()

    # Net stats (default)
    for stat_name in PORTFOLIO_STAT_METHODS:
        try:
            value = safe_float(getattr(portfolio_curve.percent, stat_name)())
            if value is not None:
                metrics[f"portfolio/net/{stat_name}"] = value
        except Exception:
            pass

    # Gross stats (key subset)
    for stat_name in ["sharpe", "ann_mean", "ann_std"]:
        try:
            value = safe_float(
                getattr(portfolio_curve.percent.gross, stat_name)()
            )
            if value is not None:
                metrics[f"portfolio/gross/{stat_name}"] = value
        except Exception:
            pass

    # Costs stats (key subset)
    for stat_name in ["ann_mean", "ann_std"]:
        try:
            value = safe_float(
                getattr(portfolio_curve.percent.costs, stat_name)()
            )
            if value is not None:
                metrics[f"portfolio/costs/{stat_name}"] = value
        except Exception:
            pass

    # Total turnover
    try:
        turnover = safe_float(system.accounts.total_portfolio_level_turnover())
        if turnover is not None:
            metrics["portfolio/total_turnover"] = turnover
    except Exception:
        pass

    return metrics


# ──────────────────────────────────────────────────────────────────────
# Per-instrument metrics
# ──────────────────────────────────────────────────────────────────────

INSTRUMENT_STAT_METHODS = [
    "sharpe",
    "ann_mean",
    "ann_std",
    "worst_drawdown",
    "avg_drawdown",
    "sortino",
    "hitrate",
]


def extract_instrument_metrics(system) -> Dict[str, float]:
    """Extract per-instrument performance statistics.

    Returns a flat dict with keys like 'instrument/{code}/{stat}'.
    """
    metrics: Dict[str, float] = {}

    portfolio_curve = system.accounts.portfolio()
    instruments = portfolio_curve.asset_columns

    for instrument_code in instruments:
        for stat_name in INSTRUMENT_STAT_METHODS:
            try:
                instrument_curve = portfolio_curve.percent[instrument_code]
                value = safe_float(getattr(instrument_curve, stat_name)())
                if value is not None:
                    key = sanitise_metric_name(
                        f"instrument/{instrument_code}/{stat_name}"
                    )
                    metrics[key] = value
            except Exception:
                pass

    return metrics


# ──────────────────────────────────────────────────────────────────────
# Per-trading-rule metrics
# ──────────────────────────────────────────────────────────────────────

RULE_STAT_METHODS = [
    "sharpe",
    "ann_mean",
    "ann_std",
    "sortino",
]


def extract_rule_metrics(system) -> Dict[str, float]:
    """Extract per-trading-rule performance statistics.

    Returns a flat dict with keys like 'rule/{rule_name}/{stat}'.
    """
    metrics: Dict[str, float] = {}

    try:
        rules = system.accounts.pandl_for_all_trading_rules()
    except Exception:
        return metrics

    for rule_name in rules.asset_columns:
        for stat_name in RULE_STAT_METHODS:
            try:
                rule_curve = rules.percent[rule_name]
                value = safe_float(getattr(rule_curve, stat_name)())
                if value is not None:
                    key = sanitise_metric_name(f"rule/{rule_name}/{stat_name}")
                    metrics[key] = value
            except Exception:
                pass

    return metrics


# ──────────────────────────────────────────────────────────────────────
# Parameters extraction
# ──────────────────────────────────────────────────────────────────────


def extract_parameters(system) -> Dict[str, str]:
    """Extract system configuration as flat parameters for MLflow.

    MLflow params are key-value string pairs with max 500 chars per value.
    Complex nested structures are flattened with '/' separators.
    Only scalar values are included.
    """
    params: Dict[str, str] = {}

    try:
        config_dict = system.config.as_dict()
    except Exception:
        config_dict = {}

    # Flatten and filter to scalars
    _flatten_to_params(config_dict, params, prefix="config")

    # Instrument list
    try:
        instruments = system.get_instrument_list()
        params["instrument_count"] = str(len(instruments))
        params["instruments"] = truncate_param_value(", ".join(instruments))
    except Exception:
        pass

    # Trading rules
    try:
        rules = system.rules.trading_rules()
        params["rule_count"] = str(len(rules))
        params["rules"] = truncate_param_value(", ".join(rules.keys()))
    except Exception:
        pass

    # Capital
    try:
        capital = system.positionSize.get_notional_capital()
        params["notional_capital"] = str(float(capital))
    except Exception:
        pass

    return params


def _flatten_to_params(
    d: dict,
    params: Dict[str, str],
    prefix: str = "",
    max_depth: int = 3,
    current_depth: int = 0,
):
    """Recursively flatten a dict into MLflow-compatible params."""
    if current_depth >= max_depth:
        return

    for key, value in d.items():
        full_key = f"{prefix}/{key}" if prefix else str(key)
        full_key = sanitise_metric_name(full_key)

        if isinstance(value, dict):
            _flatten_to_params(
                value, params, full_key,
                max_depth=max_depth,
                current_depth=current_depth + 1,
            )
        elif is_scalar(value):
            params[full_key] = truncate_param_value(value)
        elif isinstance(value, list) and len(value) <= 20:
            # Small lists get serialised as comma-separated strings
            params[full_key] = truncate_param_value(", ".join(str(v) for v in value))


# ──────────────────────────────────────────────────────────────────────
# Timeseries extraction
# ──────────────────────────────────────────────────────────────────────


def extract_timeseries(system) -> Dict[str, pd.DataFrame]:
    """Extract key timeseries as DataFrames.

    Returns a dict of name -> DataFrame.  Each will be saved as a CSV
    artifact in MLflow.
    """
    timeseries: Dict[str, pd.DataFrame] = {}

    # Portfolio equity curve (net, gross, costs)
    try:
        portfolio_curve = system.accounts.portfolio()
        equity_df = portfolio_curve.percent.to_ncg_frame()
        cumulative_equity = equity_df.cumsum()
        timeseries["portfolio_equity_curve"] = cumulative_equity
        timeseries["portfolio_daily_returns"] = equity_df
    except Exception:
        pass

    # Per-instrument P&L
    try:
        portfolio_curve = system.accounts.portfolio()
        instrument_returns = portfolio_curve.percent.to_frame()
        timeseries["instrument_returns"] = instrument_returns
    except Exception:
        pass

    # Positions
    try:
        instruments = system.get_instrument_list()
        position_frames = {}
        for code in instruments:
            try:
                pos = system.portfolio.get_notional_position(code)
                position_frames[code] = pos
            except Exception:
                pass
        if position_frames:
            positions_df = pd.concat(position_frames, axis=1)
            positions_df.columns = list(position_frames.keys())
            timeseries["positions"] = positions_df
    except Exception:
        pass

    return timeseries
