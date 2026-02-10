import argparse
import pandas as pd
import pathlib
import csv
from typing import List, Dict
import sys


class FuturesConsolidator:
    def __init__(self, source_dirs: List[str], dest_dir: str):
        self.source_dirs = [pathlib.Path(d) for d in source_dirs]
        self.dest_dir = pathlib.Path(dest_dir)
        self.report_path = self.dest_dir / "consolidation_report.csv"
        self.conflict_log = []

    def run(self):
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
        conflicts = []
        common_cols = df_a.columns.intersection(df_b.columns)

        for col in common_cols:
            s_a = df_a.loc[idx, col]
            s_b = df_b.loc[idx, col]

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

        self._log_conflicts(conflicts)


def main():
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
