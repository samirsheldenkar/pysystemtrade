import argparse
import pandas as pd
import os
import sys
import re
from typing import Optional, Dict, List
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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


def parse_contract_name(contract_name: str) -> tuple[str, int, int]:
    """
    Parses contract name (e.g., 'ES202306') into (root, year, month).
    Assumes format: [Letters][YYYY][MM]
    """
    match = re.match(r"([A-Z]+)(\d{4})(\d{2})", contract_name)
    if not match:
        raise ValueError(f"Could not parse contract name: {contract_name}")

    root, year, month = match.groups()
    return root, int(year), int(month)


def get_databento_symbol(contract_name: str) -> str:
    """
    Converts pysystemtrade contract name to a likely Databento symbol.
    Heuristic: Root + MonthCode + LastDigitOfYear
    Example: ES202306 -> ESM3
    Note: This is a heuristic and might need adjustment for specific datasets.
    """
    try:
        root, year, month = parse_contract_name(contract_name)
        month_code = MONTH_CODES[month]
        year_digit = str(year)[-1]
        return f"{root}{month_code}{year_digit}"
    except Exception as e:
        logger.warning(f"Failed to generate symbol for {contract_name}: {e}")
        return contract_name


def fetch_databento_data(
    api_key: str, dataset: str, symbol: str, date: str
) -> Optional[Dict]:
    """
    Fetches OHLCV data for a specific symbol and date from Databento.
    """
    try:
        import databento as db
    except ImportError:
        logger.error(
            "databento library not installed. Please install it with 'pip install databento'"
        )
        sys.exit(1)

    client = db.Historical(api_key)

    try:
        start_date = pd.Timestamp(date)
        if pd.isna(start_date):
            return None
        end_date = start_date + pd.Timedelta(days=1)

        data = client.timeseries.get_range(
            dataset=dataset,
            symbols=[symbol],
            start=start_date,
            end=end_date,
            schema="ohlcv-1d",
        )

        df = data.to_pandas()
        if df.empty:
            return None

        row = df.iloc[0]
        return {
            "Ref_Open": row.get("open", float("nan")),
            "Ref_High": row.get("high", float("nan")),
            "Ref_Low": row.get("low", float("nan")),
            "Ref_Close": row.get("close", float("nan")),
            "Ref_Vol": row.get("volume", float("nan")),
        }

    except Exception as e:
        logger.warning(f"Error fetching data for {symbol} on {date}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Verify data conflicts using Databento."
    )
    parser.add_argument(
        "--input", default="consolidation_report.csv", help="Input CSV file path"
    )
    parser.add_argument(
        "--output",
        default="consolidation_report_verified.csv",
        help="Output CSV file path",
    )
    parser.add_argument(
        "--dataset",
        default="GLBX.MDP3",
        help="Databento dataset ID (default: GLBX.MDP3)",
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock data instead of calling API"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} rows from {args.input}")

    ref_cols = ["Ref_Open", "Ref_High", "Ref_Low", "Ref_Close", "Ref_Vol"]
    for col in ref_cols:
        df[col] = float("nan")

    api_key = os.environ.get("DATABENTO_API_KEY")
    if not args.mock and not api_key:
        logger.error(
            "DATABENTO_API_KEY environment variable not set. Use --mock to run without API key."
        )
        sys.exit(1)

    unique_pairs = df[["Contract", "Date"]].drop_duplicates()
    logger.info(f"Found {len(unique_pairs)} unique contract/date pairs to verify.")

    cache = {}

    for _, row in unique_pairs.iterrows():
        contract = row["Contract"]
        date = row["Date"]

        if args.mock:
            data = {k: -1 for k in ref_cols}
        else:
            symbol = get_databento_symbol(str(contract))
            # api_key is checked above, so we know it's not None here
            data = fetch_databento_data(str(api_key), args.dataset, symbol, str(date))

        if data:
            cache[(contract, date)] = data

    for idx, row in df.iterrows():
        key = (row["Contract"], row["Date"])
        if key in cache:
            for col, val in cache[key].items():
                df.at[idx, col] = val

    df.to_csv(args.output, index=False)
    logger.info(f"Saved verified report to {args.output}")


if __name__ == "__main__":
    main()
