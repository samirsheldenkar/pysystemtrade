import argparse
from syscore.constants import arg_not_supplied
from sysdata.data_blob import dataBlob
from sysproduction.data.instruments import diagInstruments
from sysproduction.data.prices import diagPrices
from sysinit.futures.rollcalendars_from_db_prices_to_csv import (
    build_and_write_roll_calendar,
)


def build_all_roll_calendars(input_prices_path=None, output_path=None):
    """
    Generate roll calendars for all instruments using raw contract price data
    """
    # If a custom input path is provided, construct a dataBlob pointing to it
    if input_prices_path:
        data = dataBlob(parquet_store_path=input_prices_path)
    else:
        data = dataBlob()

    diag_instruments = diagInstruments(data)
    all_instruments = diag_instruments.get_list_of_instruments()

    print(
        f"Found {len(all_instruments)} instruments. Starting roll calendar generation..."
    )

    # Get custom input prices store if path is provided
    if input_prices_path:
        prices_diag = diagPrices(data)
        input_prices = prices_diag.db_futures_contract_price_data
    else:
        input_prices = arg_not_supplied

    for instrument_code in all_instruments:
        try:
            print(f"\n--- Processing {instrument_code} ---")
            build_and_write_roll_calendar(
                instrument_code,
                output_datapath=output_path if output_path else arg_not_supplied,
                write=True,
                check_before_writing=False,
                input_prices=input_prices,
            )
            print(f"Successfully generated roll calendar for {instrument_code}")
        except Exception as e:
            print(f"Failed to generate roll calendar for {instrument_code}: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Batch generate roll calendars from contract prices."
    )
    parser.add_argument(
        "--input-prices-path",
        type=str,
        default=None,
        help="Path to input parquet price store",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to write output roll calendar CSVs",
    )
    args = parser.parse_args()

    build_all_roll_calendars(
        input_prices_path=args.input_prices_path, output_path=args.output_path
    )
