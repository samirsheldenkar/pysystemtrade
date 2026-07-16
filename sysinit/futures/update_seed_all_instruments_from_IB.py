import time
import logging
import os
from datetime import datetime
import pandas as pd

from sysdata.data_blob import dataBlob
from sysproduction.data.instruments import diagInstruments
from sysproduction.data.broker import dataBroker
from sysproduction.data.prices import updatePrices, diagPrices
from sysbrokers.IB.ib_futures_contract_price_data import futuresContract
from sysproduction.update_historical_prices import write_merged_prices_for_contract
from sysobjects.futures_per_contract_prices import futuresContractPrices
from syscore.dateutils import DAILY_PRICE_FREQ, HOURLY_FREQ, Frequency
from syscore.exceptions import missingData


def setup_logging() -> str:
    """
    Set up logging configuration with both file and console handlers
    """
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"update_seed_ib_prices_{timestamp}.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )

    return log_file


def merge_preferring_new(
    old_data: futuresContractPrices, new_data: futuresContractPrices
) -> futuresContractPrices:
    if len(old_data) == 0:
        return new_data
    if len(new_data) == 0:
        return old_data

    # Ensure unique indices
    old_clean = old_data.groupby(level=0).last()
    new_clean = new_data.groupby(level=0).last()

    # Align timezone awareness
    if old_clean.index.tz is None and new_clean.index.tz is not None:
        new_clean = new_clean.copy()
        new_clean.index = new_clean.index.tz_localize(None)
    elif old_clean.index.tz is not None and new_clean.index.tz is None:
        old_clean = old_clean.copy()
        old_clean.index = old_clean.index.tz_localize(None)

    union_idx = old_clean.index.union(new_clean.index)
    merged_df = old_clean.reindex(union_idx)
    merged_df.loc[new_clean.index, :] = new_clean

    return futuresContractPrices(merged_df)


def detect_junction_gap(old_data: pd.DataFrame, new_data: pd.DataFrame) -> tuple | None:
    """
    Checks if there is a significant gap between the old and new data series.
    Returns: (gap_start, gap_end, gap_duration) if a non-weekend gap > 5 * typical_gap exists,
             else None.
    """
    if len(old_data) == 0 or len(new_data) == 0:
        return None

    old_idx = old_data.index.sort_values()
    new_idx = new_data.index.sort_values()

    # If they overlap, there is no junction gap
    if new_idx[0] <= old_idx[-1] and new_idx[-1] >= old_idx[0]:
        return None

    # Determine direction of gap
    if new_idx[0] > old_idx[-1]:
        gap_start = old_idx[-1]
        gap_end = new_idx[0]
    else:
        gap_start = new_idx[-1]
        gap_end = old_idx[0]

    gap_duration = gap_end - gap_start

    # Calculate typical gap in merged dataset
    merged_idx = old_idx.union(new_idx).sort_values()
    diffs = pd.Series(merged_idx).diff()
    typical_gap = diffs.median()

    if pd.isna(typical_gap) or typical_gap == pd.Timedelta(0):
        return None

    if gap_duration > 5 * typical_gap:
        # Check if the gap is just a standard weekend closure
        # Weekend gaps are ignored if gap spans from Friday/Saturday to Sunday/Monday
        if gap_duration.total_seconds() > 3600 * 24:  # Greater than 1 day
            if gap_start.weekday() in [4, 5] and gap_end.weekday() in [6, 0]:
                return None
        return gap_start, gap_end, gap_duration

    return None


def update_seed_price_data_for_contract_at_frequency(
    data: dataBlob, contract_object: futuresContract, frequency: Frequency
):
    data_broker = dataBroker(data)
    update_prices = updatePrices(data)
    diag_prices = diagPrices(data)
    log_attrs = {**contract_object.log_attributes(), "method": "temp"}

    try:
        new_prices = (
            data_broker.get_prices_at_frequency_for_potentially_expired_contract_object(
                contract_object, frequency=frequency
            )
        )
    except missingData:
        data.log.warning(
            "Error getting data from IB for %s" % str(contract_object),
            **log_attrs,
        )
        return None

    data.log.debug(
        "Got %d lines of new prices from IB for %s"
        % (len(new_prices), str(contract_object)),
        **log_attrs,
    )

    if len(new_prices) == 0:
        data.log.info(
            "No new price data returned from IB for %s, keeping existing data intact"
            % str(contract_object),
            **log_attrs,
        )
        return

    # Load existing data
    old_prices = diag_prices.get_prices_at_frequency_for_contract_object(
        contract_object, frequency=frequency, return_empty=True
    )

    if len(old_prices) > 0:
        data.log.debug(
            "Loaded %d lines of existing prices for %s"
            % (len(old_prices), str(contract_object)),
            **log_attrs,
        )

        # Check for significant gaps at the junction
        gap_info = detect_junction_gap(old_prices, new_prices)
        if gap_info is not None:
            gap_start, gap_end, gap_duration = gap_info
            data.log.warning(
                "Significant junction gap of %s detected for %s at frequency %s: old data ends %s, new data starts %s"
                % (
                    str(gap_duration),
                    str(contract_object),
                    str(frequency),
                    str(gap_start),
                    str(gap_end),
                ),
                **log_attrs,
            )

    # Perform the merge
    merged_prices = merge_preferring_new(old_prices, new_prices)

    if len(merged_prices) == 0:
        data.log.warning(
            "No price data to save for %s" % str(contract_object),
            **log_attrs,
        )
    else:
        update_prices.overwrite_prices_at_frequency_for_contract(
            contract_object=contract_object,
            frequency=frequency,
            new_prices=merged_prices,
        )


def update_seed_price_data_for_contract(
    data: dataBlob, contract_object: futuresContract
):
    log_attrs = {**contract_object.log_attributes(), "method": "temp"}

    list_of_frequencies = [HOURLY_FREQ, DAILY_PRICE_FREQ]
    for frequency in list_of_frequencies:
        data.log.debug("Updating data at frequency %s" % str(frequency), **log_attrs)
        update_seed_price_data_for_contract_at_frequency(
            data=data, contract_object=contract_object, frequency=frequency
        )

    data.log.debug("Writing merged data for %s" % str(contract_object), **log_attrs)
    write_merged_prices_for_contract(
        data, contract_object=contract_object, list_of_frequencies=list_of_frequencies
    )


def update_seed_price_data_for_instrument(instrument_code: str):
    data = dataBlob()
    data_broker = dataBroker(data)

    list_of_contracts = data_broker.get_list_of_contract_dates_for_instrument_code(
        instrument_code, allow_expired=True
    )

    for contract_date in list_of_contracts:
        date_str = contract_date[:6]
        contract_object = futuresContract(instrument_code, date_str)

        update_seed_price_data_for_contract(data=data, contract_object=contract_object)


def update_seed_all_instruments_from_IB():
    """
    Seeds/Updates price data from Interactive Brokers for all instruments in the system
    preserving existing non-overlapping data and preferring IB data on overlap.
    """
    # Setup logging
    log_file = setup_logging()
    logging.info(f"Log file created at: {log_file}")

    data = dataBlob()
    diag_instruments = diagInstruments(data)

    # Get list of all instruments
    all_instruments = diag_instruments.get_list_of_instruments()

    logging.info(f"Found {len(all_instruments)} instruments to process")
    logging.info(f"Instruments to process: {', '.join(all_instruments)}")

    success_count = 0
    error_count = 0
    error_instruments = []

    for instrument_code in all_instruments:
        try:
            logging.info(f"\nProcessing instrument: {instrument_code}")
            start_time = time.time()

            update_seed_price_data_for_instrument(instrument_code)

            end_time = time.time()
            duration = end_time - start_time
            logging.info(
                f"Successfully processed {instrument_code} in {duration:.2f} seconds"
            )
            success_count += 1

            # Add a small delay to avoid overwhelming IB
            time.sleep(1)

        except Exception as e:
            error_msg = f"Error processing {instrument_code}: {str(e)}"
            logging.error(error_msg, exc_info=True)
            error_count += 1
            error_instruments.append((instrument_code, str(e)))
            continue

    # Log summary
    logging.info("\n=== Processing Summary ===")
    logging.info(f"Total instruments processed: {len(all_instruments)}")
    logging.info(f"Successfully processed: {success_count}")
    logging.info(f"Failed to process: {error_count}")

    if error_count > 0:
        logging.warning("\nFailed instruments:")
        for instrument, error in error_instruments:
            logging.warning(f"{instrument}: {error}")


if __name__ == "__main__":
    logging.info(
        "Starting to update/seed price data for all instruments from IB (preserving non-overlapping data)"
    )
    update_seed_all_instruments_from_IB()
    logging.info("Completed updating price data for all instruments")
