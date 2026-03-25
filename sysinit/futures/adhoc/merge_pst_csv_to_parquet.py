"""
Merge `pst-csv-data` into Canonical Parquet Files

This script appends new rows from the CSV files in `pst-csv-data` 
to the canonical parquet files generated from deep history. It ensures
that only rows strictly after the latest date in the canonical data are appended.
"""

import pandas as pd
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Merge pst-csv-data into canonical parquet files.")
    parser.add_argument(
        "--pst-csv-dir", 
        default="/home/samir/pst-csv-data/data", 
        help="Path to the pst-csv-data data directory"
    )
    parser.add_argument(
        "--consolidated-dir", 
        default="/home/samir/data/consolidated", 
        help="Path to the consolidated data directory"
    )
    args = parser.parse_args()

    PST_MP = os.path.join(args.pst_csv_dir, 'multiple_prices_csv')
    PST_AP = os.path.join(args.pst_csv_dir, 'adjusted_prices_csv')
    OUT_MP = os.path.join(args.consolidated_dir, 'futures_multiple_prices')
    OUT_AP = os.path.join(args.consolidated_dir, 'futures_adjusted_prices')

    # Ensure output directories exist
    os.makedirs(OUT_MP, exist_ok=True)
    os.makedirs(OUT_AP, exist_ok=True)

    if not os.path.exists(PST_MP):
        print(f"Directory {PST_MP} does not exist. Skipping.")
        return

    print(f"Processing multiple and adjusted prices from {args.pst_csv_dir} ...")

    for f in sorted(os.listdir(PST_MP)):
        if not f.endswith('.csv'): 
            continue
            
        inst = f.replace('.csv', '')
        print(f"\nProcessing instrument: {inst}")
        
        # 1. Process Multiple Prices
        pst_mp_path = os.path.join(PST_MP, f)
        can_mp_path = os.path.join(OUT_MP, f'{inst}.parquet')
        
        pst_mp = pd.read_csv(pst_mp_path, index_col=0, parse_dates=True)
        
        def format_contract_cols(df):
            contract_cols = ['PRICE_CONTRACT', 'CARRY_CONTRACT', 'FORWARD_CONTRACT']
            for c in contract_cols:
                if c in df.columns:
                    df[c] = df[c].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip().lower() not in ['nan', ''] else None)
            return df
            
        pst_mp = format_contract_cols(pst_mp)
        
        if os.path.exists(can_mp_path):
            can_mp = pd.read_parquet(can_mp_path)
            can_end = can_mp.index.max()
            new_rows = pst_mp[pst_mp.index > can_end]
            if not new_rows.empty:
                merged_mp = pd.concat([can_mp, new_rows]).sort_index()
                merged_mp.to_parquet(can_mp_path)
                print(f"  [Multiple] Appended {len(new_rows)} rows (canonical={len(can_mp)}, now={len(merged_mp)})")
            else:
                print(f"  [Multiple] No new rows to append (last canonical date: {can_end})")
        else:
            pst_mp.to_parquet(can_mp_path)
            print(f"  [Multiple] Created from pst-csv ({len(pst_mp)} rows)")
        
        # 2. Process Adjusted Prices
        pst_ap_path = os.path.join(PST_AP, f)
        can_ap_path = os.path.join(OUT_AP, f'{inst}.parquet')
        
        if os.path.exists(pst_ap_path):
            pst_ap = pd.read_csv(pst_ap_path, index_col=0, parse_dates=True)
            if os.path.exists(can_ap_path):
                can_ap = pd.read_parquet(can_ap_path)
                ap_new = pst_ap[pst_ap.index > can_ap.index.max()]
                if not ap_new.empty:
                    ap_merged = pd.concat([can_ap, ap_new]).sort_index()
                    ap_merged.to_parquet(can_ap_path)
                    print(f"  [Adjusted] Appended {len(ap_new)} rows (canonical={len(can_ap)}, now={len(ap_merged)})")
                else:
                    print(f"  [Adjusted] No new rows to append (last canonical date: {can_ap.index.max()})")
            else:
                pst_ap.to_parquet(can_ap_path)
                print(f"  [Adjusted] Created from pst-csv ({len(pst_ap)} rows)")
        else:
             print(f"  [Adjusted] Warning: No CSV file found for {inst} in {PST_AP}")

    print("\nMerge complete.")

if __name__ == "__main__":
    main()
