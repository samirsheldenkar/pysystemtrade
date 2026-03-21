#!/usr/bin/env python3
"""
Download gap-filling futures contract data from DataBento.

This script reads the gap manifest CSV and downloads missing contract data
from DataBento, saving it in the pysystemtrade Parquet format.

Usage:
    # Dry run to verify mappings
    python download_gap_contracts.py --manifest gap_contracts_manifest.csv --dry-run

    # Download all gaps
    python download_gap_contracts.py --manifest gap_contracts_manifest.csv --output /home/samir/data/consolidated/futures_contract_prices

    # Resume interrupted download
    python download_gap_contracts.py --manifest gap_contracts_manifest.csv --resume-from progress.json
"""

import argparse
import json
import logging
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Month code mapping for futures symbology
MONTH_CODES = {
    1: "F",
    2: "G",
    3: "H",
    4: "J",
    5: "K",
    6: "M",
    7: "N",
    8: "Q",
    9: "U",
    10: "V",
    11: "X",
    12: "Z",
}

# Reverse mapping for validation
CODE_TO_MONTH = {v: k for k, v in MONTH_CODES.items()}

# DataBento column to pysystemtrade column mapping
COLUMN_MAP = {
    "open": "OPEN",
    "high": "HIGH",
    "low": "LOW",
    "close": "FINAL",
    "volume": "VOLUME",
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class DataBentoDownloader:
    """Handles downloading futures data from DataBento."""

    def __init__(
        self,
        api_key: str,
        mapping_path: str,
        output_dir: str,
        schema: str = "ohlcv-1d",
        max_workers: int = 4,
        dry_run: bool = False,
    ):
        self.api_key = api_key
        self.output_dir = Path(output_dir)
        self.schema = schema
        self.max_workers = max_workers
        self.dry_run = dry_run
        self.progress_file = None

        # Load mappings
        self.mappings = self._load_mappings(mapping_path)

        # Initialize DataBento client (lazy import)
        self._client = None

        # Track progress
        self.completed: List[Dict] = []
        self.failed: List[Dict] = []
        self.skipped: List[Dict] = []

    @property
    def client(self):
        """Lazy initialization of DataBento client."""
        if self._client is None and not self.dry_run:
            try:
                import databento as db

                self._client = db.Historical(self.api_key)
                logger.info("Initialized DataBento client")
            except ImportError:
                logger.error(
                    "databento package not installed. Install with: pip install databento"
                )
                raise
        return self._client

    def _load_mappings(self, path: str) -> Dict:
        """Load instrument to DataBento mapping from JSON."""
        with open(path, "r") as f:
            data = json.load(f)
        mappings = data.get("mappings", {})
        logger.info(f"Loaded {len(mappings)} instrument mappings from {path}")

        # Log instruments needing verification
        needs_verify = [k for k, v in mappings.items() if v.get("needs_verification")]
        if needs_verify:
            logger.warning(
                f"{len(needs_verify)} instruments need verification: {needs_verify[:10]}..."
            )

        return mappings

    def convert_contract_to_symbol(
        self, instrument: str, contract_date: str
    ) -> Tuple[str, str]:
        """
        Convert pysystemtrade contract date to DataBento symbol.

        Args:
            instrument: pysystemtrade instrument code (e.g., 'ES')
            contract_date: Contract date string (e.g., '20240600')

        Returns:
            Tuple of (databento_symbol, dataset)
        """
        # Get mapping for instrument
        mapping = self.mappings.get(instrument)
        if not mapping:
            raise ValueError(f"No mapping found for instrument: {instrument}")

        # Parse contract date (format: YYYYMM00)
        if len(contract_date) >= 6:
            year = int(contract_date[:4])
            month = int(contract_date[4:6])
        else:
            raise ValueError(f"Invalid contract_date format: {contract_date}")

        # Build DataBento symbol
        root = mapping["databento_root"]
        month_code = MONTH_CODES[month]
        year_digit = str(year)[-1]
        symbol = f"{root}{month_code}{year_digit}"

        dataset = mapping["dataset"]

        return symbol, dataset

    def download_contract(
        self,
        instrument: str,
        contract_date: str,
        start_date: str,
        end_date: str,
    ) -> Optional[pd.DataFrame]:
        """
        Download data for a single contract from DataBento.

        Args:
            instrument: pysystemtrade instrument code
            contract_date: Contract date (e.g., '20240600')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data or None if download failed
        """
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would download {instrument}#{contract_date} "
                f"from {start_date} to {end_date}"
            )
            return pd.DataFrame()

        try:
            # Convert to DataBento symbol
            symbol, dataset = self.convert_contract_to_symbol(instrument, contract_date)

            logger.debug(
                f"Downloading {instrument}#{contract_date} -> {symbol} "
                f"from {dataset} ({start_date} to {end_date})"
            )

            # Query DataBento
            # Add one day to end_date to make it inclusive
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            end_date_inclusive = end_date_obj.strftime("%Y-%m-%d")

            data = self.client.timeseries.get_range(
                dataset=dataset,
                symbols=[symbol],
                schema=self.schema,
                start=start_date,
                end=end_date_inclusive,
            )

            df = data.to_pandas()

            if df.empty:
                logger.warning(
                    f"No data returned for {instrument}#{contract_date} ({symbol})"
                )
                return None

            # Transform to pysystemtrade format
            df = self._transform_data(df, instrument, contract_date)

            logger.info(f"Downloaded {len(df)} rows for {instrument}#{contract_date}")
            return df

        except Exception as e:
            logger.error(f"Failed to download {instrument}#{contract_date}: {e}")
            return None

    def _transform_data(
        self, df: pd.DataFrame, instrument: str, contract_date: str
    ) -> pd.DataFrame:
        """
        Transform DataBento data to pysystemtrade format.

        Args:
            df: DataFrame from DataBento
            instrument: Instrument code
            contract_date: Contract date

        Returns:
            Transformed DataFrame
        """
        # Rename columns
        df = df.rename(columns=COLUMN_MAP)

        # Ensure index is datetime
        if "ts_event" in df.columns:
            df.index = pd.to_datetime(df["ts_event"])
        elif "ts_init" in df.columns:
            df.index = pd.to_datetime(df["ts_init"])

        # Keep only required columns
        required_cols = ["OPEN", "HIGH", "LOW", "FINAL", "VOLUME"]
        df = df[[col for col in required_cols if col in df.columns]]

        # Sort by index
        df = df.sort_index()

        return df

    def save_contract_data(
        self, instrument: str, contract_date: str, df: pd.DataFrame
    ) -> bool:
        """
        Save contract data to Parquet file.

        Args:
            instrument: Instrument code
            contract_date: Contract date
            df: DataFrame with OHLCV data

        Returns:
            True if successful
        """
        if self.dry_run:
            return True

        try:
            # Create output directory if needed
            self.output_dir.mkdir(parents=True, exist_ok=True)

            # File path: {instrument}#{contract_date}.parquet
            filename = f"{instrument}#{contract_date}.parquet"
            filepath = self.output_dir / filename

            if filepath.exists():
                # Merge with existing data
                existing = pd.read_parquet(filepath)
                combined = pd.concat([existing, df])
                combined = combined[~combined.index.duplicated(keep="last")]
                combined = combined.sort_index()
                combined.to_parquet(filepath)
                logger.debug(
                    f"Updated {filepath} ({len(existing)} -> {len(combined)} rows)"
                )
            else:
                df.to_parquet(filepath)
                logger.debug(f"Created {filepath} ({len(df)} rows)")

            return True

        except Exception as e:
            logger.error(f"Failed to save {instrument}#{contract_date}: {e}")
            return False

    def process_manifest(self, manifest_path: str, resume_from: Optional[str] = None):
        """
        Process the gap manifest and download all contracts.

        Args:
            manifest_path: Path to manifest CSV
            resume_from: Path to progress JSON to resume from
        """
        # Load manifest
        manifest = pd.read_csv(manifest_path)
        logger.info(f"Loaded manifest with {len(manifest)} contracts to download")

        # Load progress if resuming
        completed_contracts = set()
        if resume_from and os.path.exists(resume_from):
            with open(resume_from, "r") as f:
                progress = json.load(f)
                completed_contracts = {
                    (item["instrument"], item["contract_date"])
                    for item in progress.get("completed", [])
                }
            logger.info(f"Resuming: {len(completed_contracts)} already completed")

        # Filter out completed
        if completed_contracts:
            mask = ~manifest.apply(
                lambda row: (row["instrument"], row["contract_date"])
                in completed_contracts,
                axis=1,
            )
            manifest = manifest[mask]
            logger.info(f"Remaining: {len(manifest)} contracts to download")

        # Check for unmapped instruments
        unmapped = set(manifest["instrument"]) - set(self.mappings.keys())
        if unmapped:
            logger.error(f"Unmapped instruments: {sorted(unmapped)}")
            # Filter out unmapped
            manifest = manifest[~manifest["instrument"].isin(unmapped)]
            logger.info(f"After filtering unmapped: {len(manifest)} contracts")

        if len(manifest) == 0:
            logger.info("No contracts to download")
            return

        # Group by dataset for efficiency
        manifest["dataset"] = manifest["instrument"].apply(
            lambda x: self.mappings.get(x, {}).get("dataset", "UNKNOWN")
        )

        # Process downloads
        if self.dry_run:
            # Sequential for dry run
            for _, row in manifest.iterrows():
                self._process_row(row)
        else:
            # Parallel downloads
            self._parallel_download(manifest)

        # Save final progress
        self._save_progress()

        # Print summary
        self._print_summary()

    def _process_row(self, row: pd.Series) -> bool:
        """Process a single manifest row."""
        instrument = row["instrument"]
        contract_date = str(row["contract_date"])
        start_date = row["data_needed_from"]
        end_date = row["data_needed_to"]

        try:
            df = self.download_contract(instrument, contract_date, start_date, end_date)

            if df is None:
                self.failed.append(
                    {
                        "instrument": instrument,
                        "contract_date": contract_date,
                        "reason": "No data returned",
                    }
                )
                return False

            if self.dry_run:
                return True

            if self.save_contract_data(instrument, contract_date, df):
                self.completed.append(
                    {
                        "instrument": instrument,
                        "contract_date": contract_date,
                        "rows": len(df),
                    }
                )
                return True
            else:
                self.failed.append(
                    {
                        "instrument": instrument,
                        "contract_date": contract_date,
                        "reason": "Save failed",
                    }
                )
                return False

        except Exception as e:
            logger.error(f"Error processing {instrument}#{contract_date}: {e}")
            self.failed.append(
                {
                    "instrument": instrument,
                    "contract_date": contract_date,
                    "reason": str(e),
                }
            )
            return False

    def _parallel_download(self, manifest: pd.DataFrame):
        """Download contracts in parallel using thread pool."""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_row = {
                executor.submit(self._process_row, row): row
                for _, row in manifest.iterrows()
            }

            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_row)):
                row = future_to_row[future]
                try:
                    future.result()
                except Exception as e:
                    logger.error(
                        f"Exception for {row['instrument']}#{row['contract_date']}: {e}"
                    )
                    self.failed.append(
                        {
                            "instrument": row["instrument"],
                            "contract_date": row["contract_date"],
                            "reason": str(e),
                        }
                    )

                # Save progress periodically
                if (i + 1) % 10 == 0:
                    self._save_progress()
                    logger.info(
                        f"Progress: {i + 1}/{len(manifest)} "
                        f"(completed: {len(self.completed)}, failed: {len(self.failed)})"
                    )

    def _save_progress(self):
        """Save progress to JSON file."""
        progress = {
            "completed": self.completed,
            "failed": self.failed,
            "skipped": self.skipped,
            "timestamp": datetime.now().isoformat(),
        }

        progress_path = self.output_dir / "download_progress.json"
        with open(progress_path, "w") as f:
            json.dump(progress, f, indent=2)

    def _print_summary(self):
        """Print download summary."""
        total = len(self.completed) + len(self.failed) + len(self.skipped)

        print("\n" + "=" * 60)
        print("DOWNLOAD SUMMARY")
        print("=" * 60)
        print(f"Total contracts processed: {total}")
        print(f"  Completed: {len(self.completed)}")
        print(f"  Failed: {len(self.failed)}")
        print(f"  Skipped: {len(self.skipped)}")

        if self.failed:
            print("\nFailed downloads:")
            for item in self.failed[:20]:  # Show first 20
                print(
                    f"  - {item['instrument']}#{item['contract_date']}: {item['reason']}"
                )
            if len(self.failed) > 20:
                print(f"  ... and {len(self.failed) - 20} more")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Download gap-filling futures data from DataBento"
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to gap contracts manifest CSV",
    )
    parser.add_argument(
        "--mapping",
        default="sysinit/futures/config/databento_mappings.json",
        help="Path to DataBento mappings JSON",
    )
    parser.add_argument(
        "--output",
        default="/home/samir/data/consolidated/futures_contract_prices",
        help="Output directory for Parquet files",
    )
    parser.add_argument(
        "--schema",
        default="ohlcv-1d",
        help="DataBento schema (default: ohlcv-1d)",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=4,
        help="Number of parallel download workers (default: 4)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify mappings without downloading",
    )
    parser.add_argument(
        "--resume-from",
        help="Resume from progress JSON file",
    )
    parser.add_argument(
        "--api-key",
        help="DataBento API key (or set DATABENTO_API_KEY env var)",
    )

    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("DATABENTO_API_KEY")
    if not api_key and not args.dry_run:
        logger.error(
            "DataBento API key required. Set DATABENTO_API_KEY env var or use --api-key"
        )
        sys.exit(1)

    # Verify paths exist
    if not os.path.exists(args.manifest):
        logger.error(f"Manifest not found: {args.manifest}")
        sys.exit(1)

    if not os.path.exists(args.mapping):
        # Try relative to script location
        script_dir = Path(__file__).parent
        alt_mapping = script_dir / "config" / "databento_mappings.json"
        if alt_mapping.exists():
            args.mapping = str(alt_mapping)
        else:
            logger.error(f"Mapping file not found: {args.mapping}")
            sys.exit(1)

    # Create downloader
    downloader = DataBentoDownloader(
        api_key=api_key or "",  # Empty string for dry run
        mapping_path=args.mapping,
        output_dir=args.output,
        schema=args.schema,
        max_workers=args.max_workers,
        dry_run=args.dry_run,
    )

    # Process manifest
    downloader.process_manifest(args.manifest, args.resume_from)


if __name__ == "__main__":
    main()
