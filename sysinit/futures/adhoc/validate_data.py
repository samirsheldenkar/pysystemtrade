import pandas as pd
import os
from sysdata.data_blob import dataBlob
from sysproduction.data.prices import diagPrices

def validate_prices(df, instrument, price_type):
    issues = []
    
    # Calculate time diff between consecutive rows
    if len(df) > 1:
        time_diffs = df.index.to_series().diff()
        
        # Determine frequency to define a gap. Most futures trade M-F, so gaps over 10 days are suspect.
        large_gaps = time_diffs[time_diffs > pd.Timedelta(days=10)]
        for date, gap in large_gaps.items():
            issues.append(f"[{instrument} - {price_type}] GAP of {gap.days} days ending on {date.date()}")
            
        # Spikes: we calculate daily percentage returns
        if hasattr(df, 'columns') and 'PRICE' in df.columns:
            prices = df['PRICE']
        else:
            prices = pd.Series(df)
            
        returns = pd.Series(prices).pct_change(fill_method=None).abs()
        # > 25% daily move is very rare and indicates a potential spike/data error
        large_spikes = returns[returns > 0.25] 
        for date, ret in large_spikes.items():
            issues.append(f"[{instrument} - {price_type}] SPIKE of {ret*100:.2f}% on {date.date()}")
            
    return issues

def main():
    print("Starting Data Validation...")
    with dataBlob() as data:
        diag = diagPrices(data)
        instruments = sorted(diag.get_list_of_instruments_in_multiple_prices())
        
        all_issues = []
        for i, code in enumerate(instruments):
            print(f"Validating {code} ({i+1}/{len(instruments)})...", end="\r")
            try:
                mp = diag.get_multiple_prices(code)
                if not mp.empty:
                    all_issues.extend(validate_prices(mp, code, "Multiple Prices"))
            except Exception as e:
                all_issues.append(f"[{code}] Failed to read MP: {e}")
                
            try:
                ap = diag.get_adjusted_prices(code)
                if not ap.empty:
                    all_issues.extend(validate_prices(ap, code, "Adjusted Prices"))
            except Exception as e:
                all_issues.append(f"[{code}] Failed to read AP: {e}")
                
    print(f"\nValidation complete. Found {len(all_issues)} issues.")
    out_path = '/home/samir/data/consolidated/validation_report.txt'
    with open(out_path, 'w') as f:
        f.write("# Data Validation Report\n\n")
        f.write(f"Total Issues Found: {len(all_issues)}\n\n")
        for issue in all_issues:
            f.write(issue + "\n")
    print(f"Report written to {out_path}")
            
if __name__ == '__main__':
    main()
