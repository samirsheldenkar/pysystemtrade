import argparse
import pandas as pd
from pathlib import Path
from typing import List

from sysobjects.multiple_prices import futuresMultiplePrices
from sysobjects.adjusted_prices import futuresAdjustedPrices


def get_instruments_from_directory(directory: Path) -> List[str]:
    """
    Scan directory for CSV files and return list of instrument names.

    :param directory: Path to scan
    :return: List of instrument names (without .csv extension)
    """
    instruments = []
    for csv_file in directory.glob("*.csv"):
        instrument = csv_file.stem
        instruments.append(instrument)
    return instruments


def build_adjusted_prices(
    input_dir: Path,
    output_dir: Path,
    forward_fill: bool = True,
):
    """
    Build adjusted prices from multiple prices for all instruments.

    :param input_dir: Directory containing multiple prices CSV files
    :param output_dir: Directory to save adjusted prices CSV files
    :param forward_fill: Whether to forward fill prices before stitching
    """
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning {input_dir} for multiple prices...")
    instruments = get_instruments_from_directory(input_dir)
    print(f"Found {len(instruments)} instruments.")

    for instrument in instruments:
        print(f"Processing {instrument}...")
        try:
            input_path = input_dir / f"{instrument}.csv"

            # Load multiple prices CSV
            multiple_prices_df = pd.read_csv(
                input_path,
                index_col="index",
                parse_dates=True,
            )

            if multiple_prices_df.empty:
                print(f"  Skipping {instrument}: empty file.")
                continue

            # Ensure unique index
            if multiple_prices_df.index.duplicated().any():
                # print(f"  Warning: Duplicate index found for {instrument}, keeping last.")
                multiple_prices_df = multiple_prices_df[
                    ~multiple_prices_df.index.duplicated(keep="last")
                ]

            # Wrap in futuresMultiplePrices object
            multiple_prices = futuresMultiplePrices(multiple_prices_df)

            # Stitch multiple prices to get adjusted prices
            adjusted_prices = futuresAdjustedPrices.stitch_multiple_prices(
                multiple_prices, forward_fill=forward_fill
            )

            # Save adjusted prices
            output_path = output_dir / f"{instrument}.csv"
            adjusted_prices.to_csv(output_path)
            print(f"  Saved adjusted prices for {instrument} to {output_path}")

        except Exception as e:
            print(f"  Error processing {instrument}: {e}")
            continue


def main():
    parser = argparse.ArgumentParser(
        description="Build adjusted prices (back-adjusted) from multiple prices CSV files."
    )
    parser.add_argument(
        "--input-dir",
        default="/home/samir/data/futures_consolidated/multiple_prices/",
        help="Directory containing multiple prices CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        default="/home/samir/data/futures_consolidated/adjusted_prices/",
        help="Directory to save adjusted prices CSV files.",
    )
    parser.add_argument(
        "--forward-fill",
        action="store_true",
        default=True,
        help="Forward fill prices and forwards before stitching (default: True).",
    )
    parser.add_argument(
        "--no-forward-fill",
        dest="forward_fill",
        action="store_false",
        help="Disable forward fill before stitching.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    build_adjusted_prices(
        input_dir=input_dir,
        output_dir=output_dir,
        forward_fill=args.forward_fill,
    )


if __name__ == "__main__":
    main()
