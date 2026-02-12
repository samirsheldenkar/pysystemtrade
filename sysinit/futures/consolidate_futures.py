"""
Futures Consolidation Module

This module provides functionality to consolidate futures data from multiple source directories
into a single destination directory. It handles:
- Scanning multiple source directories for Parquet files.
- Grouping files by contract name.
- Merging data from multiple sources, prioritizing the most recently modified files.
- identifying and logging data conflicts between sources where values differ beyond a tolerance.
- Generating a consolidation report (CSV) detailing any conflicts found.

Usage:
    Run the script from the command line, specifying source directories and a destination directory.

    $ python consolidate_futures.py --sources /path/to/source1 /path/to/source2 --dest /path/to/output
"""

import argparse
import pandas as pd
import pathlib
import csv
from typing import List, Dict
import sys


class FuturesConsolidator:
    """
    Consolidates futures data files from multiple sources into a single destination.

    This class handles the logic of finding, reading, merging, and writing futures data.
    It prioritizes files based on modification time (later is better) but processes them
    sequentially to build a master record. It also identifies and logs any value discrepancies
    (conflicts) found between overlapping data points from different sources.

    Attributes:
        source_dirs (List[pathlib.Path]): A list of directory paths to search for source data.
        dest_dir (pathlib.Path): The directory path where consolidated files will be written.
        report_path (pathlib.Path): The file path for the CSV conflict report.
        conflict_log (List): Internal storage for conflicts (currently unused).
    """

    def __init__(self, source_dirs: List[str], dest_dir: str):
        """
        Initialize the FuturesConsolidator.

        Args:
            source_dirs (List[str]): A list of strings representing paths to source directories.
            dest_dir (str): A string representing the path to the destination directory.
        """
        self.source_dirs = [pathlib.Path(d) for d in source_dirs]
        self.dest_dir = pathlib.Path(dest_dir)
        self.report_path = self.dest_dir / "consolidation_report.csv"
        self.conflict_log = []

    def run(self):
        """
        Execute the consolidation process.

        This method performs the following steps:
        1. Creates the destination directory if it doesn't exist.
        2. Scans all source directories for contract files (.parquet).
        3. Initializes the conflict report CSV.
        4. Iterates through each unique contract found, processing its files.
        5. prints progress to stdout.
        """
        self.dest_dir.mkdir(parents=True, exist_ok=True)

        contract_files = self._scan_files()
        self._init_report()

        total_contracts = len(contract_files)
        print(f"Found {total_contracts} contracts to process.")

        for i, (contract, files) in enumerate(contract_files.items(), 1):
            print(f"[{i}/{total_contracts}] Processing {contract}...")
            self._process_contract(contract, files)

        print("Consolidation complete.")

    def _scan_files(self) -> Dict[str, List[pathlib.Path]]:
        """
        Scan source directories for Parquet files and group them by contract name.

        Returns:
            Dict[str, List[pathlib.Path]]: A dictionary where keys are contract filenames
            (e.g., 'ES.parquet') and values are lists of full paths to those files found
            across the source directories.
        """
        contract_files = {}
        for src in self.source_dirs:
            if not src.exists():
                print(f"Warning: Source directory {src} does not exist. Skipping.")
                continue

            for p in src.glob("*.parquet"):
                contract_name = p.name
                if contract_name not in contract_files:
                    contract_files[contract_name] = []
                contract_files[contract_name].append(p)
        return contract_files

    def _init_report(self):
        """
        Initialize the consolidation report CSV file.

        Creates (or overwrites) the report file and writes the header row.
        """
        headers = [
            "Contract",
            "Date",
            "Column",
            "Value_A",
            "Value_B",
            "Source_A",
            "Source_B",
        ]
        with open(self.report_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _log_conflicts(self, conflicts: List[dict]):
        """
        Append a list of conflicts to the report file.

        Args:
            conflicts (List[dict]): A list of dictionaries, where each dictionary represents
            a single conflict record containing keys like 'Contract', 'Date', 'Column', etc.
        """
        if not conflicts:
            return

        with open(self.report_path, "a", newline="") as f:
            writer = csv.writer(f)
            for c in conflicts:
                writer.writerow(
                    [
                        c["Contract"],
                        c["Date"],
                        c["Column"],
                        c["Value_A"],
                        c["Value_B"],
                        c["Source_A"],
                        c["Source_B"],
                    ]
                )

    def _process_contract(self, contract_name: str, files: List[pathlib.Path]):
        """
        Process all source files for a single contract and produce a consolidated file.

        This method:
        1. Sorts files by modification time (oldest to newest).
        2. Reads the oldest file as the initial 'master' dataframe.
        3. Iteratively reads subsequent files.
        4. Checks for conflicts on overlapping dates between the current master and the new file.
        5. Updates the master dataframe with data from the new file (overwriting overlaps).
        6. Saves the final consolidated dataframe to the destination directory.

        Args:
            contract_name (str): The name of the contract file (e.g., 'data.parquet').
            files (List[pathlib.Path]): List of paths to the source files for this contract.
        """
        files.sort(key=lambda x: x.stat().st_mtime)

        if not files:
            return

        try:
            master_df = pd.read_parquet(files[0])
            master_source = pd.Series(
                str(files[0]), index=master_df.index, name="Source"
            )
        except Exception as e:
            print(f"Error reading {files[0]}: {e}")
            return

        for next_file in files[1:]:
            try:
                next_df = pd.read_parquet(next_file)
            except Exception as e:
                print(f"Error reading {next_file}: {e}")
                continue

            common_idx = master_df.index.intersection(next_df.index)

            if not common_idx.empty:
                self._check_conflicts(
                    contract_name,
                    master_df,
                    next_df,
                    master_source,
                    next_file,
                    common_idx,
                )

            # Update master with new data (simulating an overwrite / upsert)
            master_df = master_df[~master_df.index.isin(next_df.index)]
            master_source = master_source[~master_source.index.isin(next_df.index)]

            master_df = pd.concat([master_df, next_df])

            next_source = pd.Series(str(next_file), index=next_df.index, name="Source")
            master_source = pd.concat([master_source, next_source])

        master_df = master_df.sort_index()

        dest_path = self.dest_dir / contract_name
        master_df.to_parquet(dest_path)

    def _check_conflicts(
        self,
        contract: str,
        df_a: pd.DataFrame,
        df_b: pd.DataFrame,
        source_a: pd.Series,
        file_b: pathlib.Path,
        idx: pd.DatetimeIndex,
    ):
        """
        Check for value discrepancies between two dataframes on overlapping indices.

        Compares numeric values in common columns. If values differ by more than 1e-6,
        it records a conflict.

        Args:
            contract (str): The contract identifier.
            df_a (pd.DataFrame): The 'master' or existing dataframe.
            df_b (pd.DataFrame): The 'new' dataframe being merged in.
            source_a (pd.Series): A Series tracking the source filename for each row in df_a.
            file_b (pathlib.Path): The path to the source file for df_b.
            idx (pd.DatetimeIndex): The intersecting index (dates) to check.
        """
        conflicts = []
        common_cols = df_a.columns.intersection(df_b.columns)

        for col in common_cols:
            s_a = df_a.loc[idx, col]
            s_b = df_b.loc[idx, col]

            # Assume numeric data for conflict checking
            try:
                diff = (s_a - s_b).abs()
                mask = diff > 1e-6

                if mask.any():
                    conflict_dates = idx[mask]
                    for date in conflict_dates:
                        val_a = s_a.loc[date]
                        val_b = s_b.loc[date]
                        src_a = source_a.loc[date]

                        conflicts.append(
                            {
                                "Contract": contract,
                                "Date": date,
                                "Column": col,
                                "Value_A": val_a,
                                "Value_B": val_b,
                                "Source_A": src_a,
                                "Source_B": str(file_b),
                            }
                        )
            except Exception:
                # Fallback or strict skip for non-numeric columns if necessary
                # For now, we assume simple float columns as per typical futures data
                pass

        self._log_conflicts(conflicts)


def main():
    """
    Main entry point for the script.

    Parses command-line arguments and initiates the consolidation process.
    """
    parser = argparse.ArgumentParser(
        description="Consolidate futures data from multiple sources."
    )
    parser.add_argument(
        "--sources", nargs="+", required=True, help="List of source directories"
    )
    parser.add_argument("--dest", required=True, help="Destination directory")

    args = parser.parse_args()

    consolidator = FuturesConsolidator(args.sources, args.dest)
    consolidator.run()


if __name__ == "__main__":
    main()
