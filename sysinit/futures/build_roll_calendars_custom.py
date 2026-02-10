import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import re
import sys
from typing import List, Dict, Tuple, Optional

DATE_INDEX_NAME = "DATE_TIME"


class RollCalendarBuilder:
    def __init__(self, data_dir: str, output_dir: str, backstop_days: int):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.backstop_days = backstop_days
        self.filename_pattern = re.compile(r"(.*)#(\d{8})\.parquet")

    def run(self):
        if not self.data_dir.exists():
            print(f"Error: Data directory {self.data_dir} does not exist.")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Scanning {self.data_dir} for parquet files...")
        files_by_instrument = self._scan_files()

        print(f"Found {len(files_by_instrument)} instruments.")

        for instrument, files in files_by_instrument.items():
            print(f"Processing {instrument}...")
            try:
                self._process_instrument(instrument, files)
            except Exception as e:
                print(f"Error processing {instrument}: {e}")

    def _scan_files(self) -> Dict[str, List[Tuple[str, Path]]]:
        files_by_instrument = {}

        for p in self.data_dir.glob("*.parquet"):
            match = self.filename_pattern.match(p.name)
            if match:
                instrument = match.group(1)
                expiry = match.group(2)

                if instrument not in files_by_instrument:
                    files_by_instrument[instrument] = []

                files_by_instrument[instrument].append((expiry, p))
            else:
                pass

        return files_by_instrument

    def _process_instrument(self, instrument: str, files: List[Tuple[str, Path]]):
        files.sort(key=lambda x: x[0])

        if len(files) < 2:
            print(f"  Not enough contracts for {instrument} to build a calendar.")
            return

        new_rolls = []

        for i in range(len(files) - 1):
            curr_expiry, curr_path = files[i]
            next_expiry, next_path = files[i + 1]

            curr_contract = curr_expiry
            next_contract = next_expiry

            try:
                roll_date = self._calculate_roll_date(curr_path, next_path, curr_expiry)
            except Exception as e:
                print(
                    f"  Error calculating roll for {curr_contract} -> {next_contract}: {e}"
                )
                continue

            if roll_date:
                new_rolls.append(
                    {
                        "current_contract": curr_contract,
                        "next_contract": next_contract,
                        "carry_contract": next_contract,
                        DATE_INDEX_NAME: roll_date,
                    }
                )

        if not new_rolls:
            print(f"  No rolls generated for {instrument}.")
            return

        df_new = pd.DataFrame(new_rolls)
        df_new.set_index(DATE_INDEX_NAME, inplace=True)

        self._save_calendar(instrument, df_new)

    def _calculate_roll_date(
        self, curr_path: Path, next_path: Path, curr_expiry: str
    ) -> Optional[pd.Timestamp]:
        df_curr = pd.read_parquet(curr_path)
        df_next = pd.read_parquet(next_path)

        if not isinstance(df_curr.index, pd.DatetimeIndex):
            df_curr.index = pd.to_datetime(df_curr.index)
        if not isinstance(df_next.index, pd.DatetimeIndex):
            df_next.index = pd.to_datetime(df_next.index)

        common_idx = df_curr.index.intersection(df_next.index)

        if len(common_idx) == 0:
            return self._get_backstop_date(curr_expiry)

        df_curr = df_curr.loc[common_idx]
        df_next = df_next.loc[common_idx]

        crossover_date = None

        if "VOLUME" in df_curr.columns and "VOLUME" in df_next.columns:
            vol_curr = df_curr["VOLUME"].fillna(0)
            vol_next = df_next["VOLUME"].fillna(0)

            mask = vol_next > vol_curr
            if mask.any():
                crossover_date = mask.idxmax()

        if (
            crossover_date is None
            and "OPEN_INTEREST" in df_curr.columns
            and "OPEN_INTEREST" in df_next.columns
        ):
            oi_curr = df_curr["OPEN_INTEREST"].fillna(0)
            oi_next = df_next["OPEN_INTEREST"].fillna(0)

            mask = oi_next > oi_curr
            if mask.any():
                crossover_date = mask.idxmax()

        backstop_date = self._get_backstop_date(curr_expiry)

        if crossover_date:
            if crossover_date > backstop_date:
                return backstop_date
            else:
                return crossover_date
        else:
            return backstop_date

    def _get_backstop_date(self, expiry_str: str) -> pd.Timestamp:
        # Handle YYYYMM00 format (pysystemtrade convention for monthly contracts)
        if expiry_str.endswith("00"):
            # Assume 15th of the month as proxy expiry
            expiry_str_fixed = expiry_str[:-2] + "15"
            try:
                expiry_date = pd.to_datetime(expiry_str_fixed, format="%Y%m%d")
            except ValueError:
                # Fallback to 1st of month
                expiry_date = pd.to_datetime(expiry_str[:-2] + "01", format="%Y%m%d")
        else:
            try:
                expiry_date = pd.to_datetime(expiry_str, format="%Y%m%d")
            except ValueError:
                # Try parsing as YYYYMM if length is 6
                if len(expiry_str) == 6:
                    expiry_date = pd.to_datetime(expiry_str + "15", format="%Y%m%d")
                else:
                    raise ValueError(f"Cannot parse expiry date: {expiry_str}")

        return expiry_date - pd.Timedelta(days=self.backstop_days)

    def _save_calendar(self, instrument: str, df_new: pd.DataFrame):
        output_path = self.output_dir / f"{instrument}.csv"

        if output_path.exists():
            try:
                df_old = pd.read_csv(
                    output_path, index_col=DATE_INDEX_NAME, parse_dates=True
                )

                df_old_reset = df_old.reset_index()
                df_new_reset = df_new.reset_index()

                combined = pd.concat([df_old_reset, df_new_reset])

                combined.drop_duplicates(
                    subset=["current_contract"], keep="last", inplace=True
                )

                combined.set_index(DATE_INDEX_NAME, inplace=True)
                combined.sort_index(inplace=True)

                df_final = combined
            except Exception as e:
                print(
                    f"  Error reading existing calendar for {instrument}, overwriting: {e}"
                )
                df_final = df_new
        else:
            df_final = df_new

        df_final.to_csv(output_path)
        print(f"  Saved calendar for {instrument} to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build custom roll calendars from Parquet files."
    )
    parser.add_argument(
        "--data-dir",
        default="/home/samir/data/futures_consolidated/",
        help="Directory containing consolidated parquet files.",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/samir/data/futures_consolidated/roll_calendars/",
        help="Directory to save roll calendars.",
    )
    parser.add_argument(
        "--backstop-days",
        type=int,
        default=5,
        help="Number of days before expiry to force roll.",
    )

    args = parser.parse_args()

    builder = RollCalendarBuilder(args.data_dir, args.output_dir, args.backstop_days)
    builder.run()


if __name__ == "__main__":
    main()
