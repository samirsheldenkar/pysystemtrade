import pandas as pd
import numpy as np
import pytest
from sysobjects.futures_per_contract_prices import futuresContractPrices
from sysinit.futures.update_seed_all_instruments_from_IB import (
    merge_preferring_new,
    detect_junction_gap,
)


def test_merge_preferring_new_empty():
    empty = futuresContractPrices.create_empty()

    idx = pd.to_datetime(["2020-01-01", "2020-01-02"])
    data = pd.DataFrame(
        {
            "OPEN": [10.0, 11.0],
            "HIGH": [10.5, 11.5],
            "LOW": [9.5, 10.5],
            "FINAL": [10.0, 11.0],
            "VOLUME": [100.0, 200.0],
        },
        index=idx,
    )
    prices = futuresContractPrices(data)

    # Empty old_data
    merged = merge_preferring_new(empty, prices)
    pd.testing.assert_frame_equal(merged, prices)

    # Empty new_data
    merged = merge_preferring_new(prices, empty)
    pd.testing.assert_frame_equal(merged, prices)


def test_merge_preferring_new_overlapping():
    idx_old = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    data_old = pd.DataFrame(
        {
            "OPEN": [10.0, 11.0, 12.0],
            "HIGH": [10.5, 11.5, 12.5],
            "LOW": [9.5, 10.5, 11.5],
            "FINAL": [10.0, 11.0, 12.0],
            "VOLUME": [100.0, 200.0, 300.0],
        },
        index=idx_old,
    )
    old_prices = futuresContractPrices(data_old)

    idx_new = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-04"])
    data_new = pd.DataFrame(
        {
            "OPEN": [21.0, 22.0, 23.0],
            "HIGH": [21.5, 22.5, 23.5],
            "LOW": [20.5, 21.5, 22.5],
            "FINAL": [21.0, 22.0, 23.0],
            "VOLUME": [210.0, 220.0, 230.0],
        },
        index=idx_new,
    )
    new_prices = futuresContractPrices(data_new)

    merged = merge_preferring_new(old_prices, new_prices)

    # Overlapping indices (02, 03) should be overwritten by new_prices
    assert merged.loc["2020-01-01", "OPEN"] == 10.0
    assert merged.loc["2020-01-02", "OPEN"] == 21.0
    assert merged.loc["2020-01-03", "OPEN"] == 22.0
    assert merged.loc["2020-01-04", "OPEN"] == 23.0
    assert len(merged) == 4


def test_detect_junction_gap():
    # Overlapping series -> should return None
    idx_old = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    old_df = pd.DataFrame(index=idx_old)
    idx_new = pd.to_datetime(["2020-01-03", "2020-01-04", "2020-01-05"])
    new_df = pd.DataFrame(index=idx_new)

    assert detect_junction_gap(old_df, new_df) is None

    # Non-overlapping, small gap (e.g. 1 day gap on daily data)
    idx_old = pd.to_datetime(["2020-01-01", "2020-01-02"])
    old_df = pd.DataFrame(index=idx_old)
    idx_new = pd.to_datetime(["2020-01-03", "2020-01-04"])
    new_df = pd.DataFrame(index=idx_new)

    # typical gap is 1 day, actual gap is 1 day (not > 5 * 1 day)
    assert detect_junction_gap(old_df, new_df) is None

    # Significant gap (e.g. 10 days gap on daily data)
    idx_new_large = pd.to_datetime(["2020-01-12", "2020-01-13"])
    new_df_large = pd.DataFrame(index=idx_new_large)

    gap = detect_junction_gap(old_df, new_df_large)
    assert gap is not None
    gap_start, gap_end, gap_duration = gap
    assert gap_start == pd.Timestamp("2020-01-02")
    assert gap_end == pd.Timestamp("2020-01-12")
    assert gap_duration == pd.Timedelta(days=10)
