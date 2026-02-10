import argparse
import pandas as pd
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

from sysobjects.multiple_prices import futuresMultiplePrices
from sysobjects.dict_of_futures_per_contract_prices import (
    dictFuturesContractFinalPrices,
)

DATE_INDEX_NAME = "DATE_TIME"


class MultiplePricesBuilder:
    def __init__(
        self,
        data_dir: str,
        roll_calendar_dir: str,
        output_dir: str,
    ):
        self.data_dir = Path(data_dir)
        self.roll_calendar_dir = Path(roll_calendar_dir)
        self.output_dir = Path(output_dir)
        self.filename_pattern = re.compile(r"(.*)#(\d{8})\.parquet")

    def run(self):
        if not self.data_dir.exists():
            print(f"Error: Data directory {self.data_dir} does not exist.")
            return

        if not self.roll_calendar_dir.exists():
            print(
                f"Error: Roll calendar directory {self.roll_calendar_dir} does not exist."
            )
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Scanning {self.roll_calendar_dir} for roll calendars...")
        roll_calendars = self._scan_roll_calendars()

        print(f"Found {len(roll_calendars)} roll calendars.")

        for instrument in roll_calendars:
            print(f"Processing {instrument}...")
            try:
                self._process_instrument(instrument)
            except Exception as e:
                print(f"  Error processing {instrument}: {e}")

    def _scan_roll_calendars(self) -> List[str]:
        instruments = []
        for csv_file in self.roll_calendar_dir.glob("*.csv"):
            instrument = csv_file.stem
            instruments.append(instrument)
        return instruments

    def _process_instrument(self, instrument: str):
        roll_calendar_path = self.roll_calendar_dir / f"{instrument}.csv"

        if not roll_calendar_path.exists():
            print(f"  Roll calendar not found for {instrument}.")
            return

        try:
            roll_calendar = pd.read_csv(
                roll_calendar_path, index_col=DATE_INDEX_NAME, parse_dates=True
            )
        except Exception as e:
            print(f"  Error reading roll calendar for {instrument}: {e}")
            return

        if roll_calendar.empty:
            print(f"  Roll calendar is empty for {instrument}.")
            return

        print(f"  Loading price data for {instrument}...")
        dict_of_prices = self._load_price_data(instrument)

        if not dict_of_prices:
            print(f"  No price data found for {instrument}.")
            return

        print(f"  Found {len(dict_of_prices)} contracts for {instrument}.")

        try:
            multiple_prices = futuresMultiplePrices.create_from_raw_data(
                roll_calendar, dict_of_prices
            )
        except Exception as e:
            print(f"  Error creating multiple prices for {instrument}: {e}")
            return

        self._save_multiple_prices(instrument, multiple_prices)

    def _load_price_data(self, instrument: str) -> dictFuturesContractFinalPrices:
        price_dict = {}

        for parquet_file in self.data_dir.glob(f"{instrument}#*.parquet"):
            match = self.filename_pattern.match(parquet_file.name)
            if not match:
                continue

            file_instrument = match.group(1)
            expiry = match.group(2)

            if file_instrument != instrument:
                continue

            try:
                df = pd.read_parquet(parquet_file)
            except Exception as e:
                print(f"    Error reading {parquet_file}: {e}")
                continue

            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            if "FINAL" in df.columns:
                price_series = df["FINAL"]
            elif "CLOSE" in df.columns:
                price_series = df["CLOSE"]
            else:
                print(
                    f"    Warning: No 'FINAL' or 'CLOSE' column in {parquet_file}, skipping."
                )
                continue

            price_series = price_series.sort_index()
            price_dict[expiry] = price_series

        return dictFuturesContractFinalPrices(price_dict)

    def _save_multiple_prices(
        self, instrument: str, multiple_prices: futuresMultiplePrices
    ):
        output_path = self.output_dir / f"{instrument}.csv"

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            multiple_prices.to_csv(output_path)
            print(f"  Saved multiple prices for {instrument} to {output_path}")
        except Exception as e:
            print(f"  Error saving multiple prices for {instrument}: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Build multiple prices (stitched) from consolidated Parquet files and custom roll calendars."
    )
    parser.add_argument(
        "--data-dir",
        default="/home/samir/data/futures_consolidated/",
        help="Directory containing consolidated parquet files.",
    )
    parser.add_argument(
        "--roll-calendar-dir",
        default="/home/samir/data/futures_consolidated/roll_calendars/",
        help="Directory containing roll calendar CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/samir/data/futures_consolidated/multiple_prices/",
        help="Directory to save multiple prices CSV files.",
    )

    args = parser.parse_args()

    builder = MultiplePricesBuilder(
        args.data_dir,
        args.roll_calendar_dir,
        args.output_dir,
    )
    builder.run()


if __name__ == "__main__":
    main()
