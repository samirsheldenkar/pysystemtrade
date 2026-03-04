# Futures Data Consolidation Plan

## Background

| Directory | Contents | Files | Download Date | Data Range |
|-----------|----------|-------|--------------|-----------|
| `futures_dev/` | contract prices | 13,142 | 2025-09-04 | ~Apr 2024 – Jun 2025 |
| `futures_new/` | contract prices | 22,349 | 2025-11-06 | ~Apr 2024 – Jun 2025 |
| `futures_20251119/` | contract prices | 18,256 | 2025-11-20 | ~Nov 2024 – Nov 2025 |
| `futures/` | All 5 data types | 18,447 cp + derived | 2026-02-03 | See gap analysis |
| `futures_20260204/` | contract prices | 21,820 | 2026-02-12 | ~Feb 2025 – Feb 2026 |
| `pst-csv-data/` | multiple + adjusted CSVs | 40 instruments | — | To Sep 2025 |

## Gap Analysis

> [!CAUTION]
> The `futures/` contract prices (starting Apr 2024) are disconnected from its multiple/adjusted prices (ending Mar 2024). The original contract data no longer exists.

**Cross-instrument gap summary** (252 instruments):

| Category | Count | Description |
|----------|-------|-------------|
| No gap (overlap) | 9 | Contract prices overlap multiple prices end (SP500, GOLD, AUD, GBP, etc.) |
| Gap, covered by `pst-csv-data` | 36 | CSVs extending to Sep 2025 bridge the gap |
| Gap, 8-21 days | 150 | Most common gap size |
| Gap, 22-30 days | 18 | Medium gaps |
| Gap, >100 days | 32 | Large gaps (Asian/niche markets, up to 238 days) |
| No contract data at all | 7 | Only exist in canonical derived data |

**Total missing contracts needed to fill all gaps: 444 across 200 instruments** (each instrument needs 2-3 contracts: PRICE, CARRY, FORWARD from the last row of its multiple prices series).

---

## Step-by-Step Plan

### Step 1: Merge Contract Prices

Merge all 5 sources with `FuturesConsolidator`, oldest→newest:

```bash
python -m sysinit.futures.consolidate_futures \
  --sources \
    /home/samir/data/futures_dev/futures_contract_prices \
    /home/samir/data/futures_new/futures_contract_prices \
    /home/samir/data/futures_20251119/futures_contract_prices \
    /home/samir/data/futures/futures_contract_prices \
    /home/samir/data/futures_20260204/futures_contract_prices \
  --dest /home/samir/data/consolidated/futures_contract_prices
```

---

### Step 2: Build Baseline Derived Data

```bash
cp -r /home/samir/data/futures/futures_multiple_prices /home/samir/data/consolidated/futures_multiple_prices
cp -r /home/samir/data/futures/futures_adjusted_prices /home/samir/data/consolidated/futures_adjusted_prices
cp -r /home/samir/data/futures/roll_calendars_from_db /home/samir/data/consolidated/roll_calendars
cp -r /home/samir/data/futures/spotfx_prices /home/samir/data/consolidated/spotfx_prices
```

Overlay `pst-csv-data` for the 40 instruments it covers (extends to Sep 2025):

```python
import pandas as pd, os

PST_MP = '/home/samir/pst-csv-data/data/multiple_prices_csv'
PST_AP = '/home/samir/pst-csv-data/data/adjusted_prices_csv'
OUT_MP = '/home/samir/data/consolidated/futures_multiple_prices'
OUT_AP = '/home/samir/data/consolidated/futures_adjusted_prices'

for f in os.listdir(PST_MP):
    if not f.endswith('.csv'): continue
    inst = f.replace('.csv', '')
    mp = pd.read_csv(os.path.join(PST_MP, f), index_col=0, parse_dates=True)
    mp.to_parquet(os.path.join(OUT_MP, f'{inst}.parquet'))
    ap_f = os.path.join(PST_AP, f)
    if os.path.exists(ap_f):
        ap = pd.read_csv(ap_f, index_col=0, parse_dates=True)
        ap.to_parquet(os.path.join(OUT_AP, f'{inst}.parquet'))
    print(f"  Updated {inst}")
```

---

### Step 3: Identify and Source Gap-Filling Contracts

**Goal**: Generate a manifest of the 444 specific contracts needed to fill the gap between canonical multiple/adjusted prices (ending Mar 2024) and the earliest available contract prices, then retrieve them from Barchart or Databento.

**Phase 1 — Generate contract manifest** (save as `/tmp/generate_gap_manifest.py`):

```python
"""
Generate a CSV manifest of all contracts needed to fill the gap between
the canonical multiple/adjusted prices and the available contract prices.

Output: /home/samir/data/consolidated/gap_contracts_manifest.csv
Columns: instrument, contract_date, gap_start, gap_end, gap_days, role, data_needed_from, data_needed_to
"""
import pandas as pd
import os
import glob

MP_DIR = '/home/samir/data/futures/futures_multiple_prices'
CP_DIRS = [
    '/home/samir/data/futures_dev/futures_contract_prices',
    '/home/samir/data/futures_new/futures_contract_prices',
    '/home/samir/data/futures_20251119/futures_contract_prices',
    '/home/samir/data/futures/futures_contract_prices',
    '/home/samir/data/futures_20260204/futures_contract_prices',
]
PST_INSTRUMENTS = set(
    f.replace('.csv', '') for f in os.listdir('/home/samir/pst-csv-data/data/multiple_prices_csv')
    if f.endswith('.csv')
)
OUTPUT = '/home/samir/data/consolidated/gap_contracts_manifest.csv'

rows = []

for mp_file in sorted(os.listdir(MP_DIR)):
    if not mp_file.endswith('.parquet'):
        continue
    inst = mp_file.replace('.parquet', '')

    # Skip instruments covered by pst-csv-data
    if inst in PST_INSTRUMENTS:
        continue

    mp = pd.read_parquet(os.path.join(MP_DIR, mp_file))
    mp_end = mp.index.max()

    # Find earliest contract data across all sources
    cp_min = pd.Timestamp.max
    for d in CP_DIRS:
        for f in glob.glob(os.path.join(d, f'{inst}#*.parquet')):
            df = pd.read_parquet(f)
            if len(df) > 0 and df.index.min() < cp_min:
                cp_min = df.index.min()

    if cp_min == pd.Timestamp.max:
        continue  # no contract data at all

    gap_days = (cp_min - mp_end).days
    if gap_days <= 1:
        continue  # no gap

    # Get last contract references from multiple prices
    last_row = mp.iloc[-1]
    contracts = {
        'PRICE': str(int(last_row['PRICE_CONTRACT'])),
        'CARRY': str(int(last_row['CARRY_CONTRACT'])),
        'FORWARD': str(int(last_row['FORWARD_CONTRACT'])),
    }

    # Determine the date range we need data for (gap period)
    gap_start = mp_end + pd.Timedelta(days=1)
    gap_end = cp_min - pd.Timedelta(days=1)

    seen = set()
    for role, contract_date in contracts.items():
        if contract_date in seen:
            continue  # avoid duplicates (e.g., CARRY == FORWARD)
        seen.add(contract_date)
        rows.append({
            'instrument': inst,
            'contract_date': contract_date,
            'role': role,
            'gap_start': gap_start.strftime('%Y-%m-%d'),
            'gap_end': gap_end.strftime('%Y-%m-%d'),
            'gap_days': gap_days,
            'data_needed_from': gap_start.strftime('%Y-%m-%d'),
            'data_needed_to': gap_end.strftime('%Y-%m-%d'),
        })

manifest = pd.DataFrame(rows)
manifest.to_csv(OUTPUT, index=False)

print(f"Manifest written to {OUTPUT}")
print(f"Total contracts to retrieve: {len(manifest)}")
print(f"Total instruments: {manifest['instrument'].nunique()}")
print(f"\nGap distribution:")
print(manifest.groupby('instrument')[['gap_days']].first()['gap_days'].describe())
print(f"\nSample rows:")
print(manifest.head(10).to_string(index=False))
```

**Phase 2 — Retrieve data using Barchart or Databento**

The manifest CSV has the format:

| instrument | contract_date | role | gap_start | gap_end | gap_days | data_needed_from | data_needed_to |
|-----------|--------------|------|-----------|---------|----------|-----------------|---------------|
| BUND | 20240600 | PRICE | 2024-03-29 | 2024-04-17 | 21 | 2024-03-29 | 2024-04-17 |
| BUND | 20240900 | CARRY | 2024-03-29 | 2024-04-17 | 21 | 2024-03-29 | 2024-04-17 |

> [!IMPORTANT]
> The `instrument` column uses pysystemtrade instrument codes (e.g., `BUND`, `CRUDE_W`). These need to be mapped to exchange symbols for the data provider. pysystemtrade maintains this mapping in [instrumentconfig.csv](file:///home/samir/pysystemtrade/data/futures/csvconfig/instrumentconfig.csv) and optionally in the IB config files. A mapping step will be needed for Barchart (which uses its own symbol convention) or Databento (which uses exchange-native symbols like `ZB` for BUND on CBOT).

**Option A — Barchart**:
- Barchart uses symbols like `ZBM24` (symbol + month code + 2-digit year)
- Historical OHLCV data available via API or manual download
- Contract month codes: F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun, N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec

**Option B — Databento**:
- Uses exchange-native symbols with venue prefix (e.g., `GLBX.MBO` for CME Globex)
- Python API: `databento.Historical().timeseries.get_range()`
- Can retrieve OHLCV bars directly for specific contract months
- More granular control over frequency (daily, hourly, etc.)

**Phase 3 — Ingest retrieved data**

After downloading, convert to pysystemtrade's parquet format:

```python
import pandas as pd

def ingest_gap_contract(instrument, contract_date, df, dest_dir):
    """
    Write a gap-filling contract's data to the consolidated directory.
    df should have DatetimeIndex and columns: OPEN, HIGH, LOW, FINAL (close), VOLUME
    """
    output_path = f"{dest_dir}/{instrument}#{contract_date}.parquet"
    
    # If file already exists (from Step 1 merge), merge with gap data
    if os.path.exists(output_path):
        existing = pd.read_parquet(output_path)
        # Only add rows that don't already exist
        new_rows = df[~df.index.isin(existing.index)]
        if len(new_rows) > 0:
            combined = pd.concat([new_rows, existing]).sort_index()
            combined.to_parquet(output_path)
            print(f"  Extended {instrument}#{contract_date}: +{len(new_rows)} rows")
    else:
        df.to_parquet(output_path)
        print(f"  Created {instrument}#{contract_date}: {len(df)} rows")
```

---

### Step 4: Configure Parquet Store

```yaml
# private_config.yaml
parquet_store: /home/samir/data/consolidated
```

---

### Step 5: Extend Roll Calendars

Use [build_roll_calendars_custom.py](file:///home/samir/pysystemtrade/sysinit/futures/adhoc/build_roll_calendars_custom.py) (merges with existing):

```bash
python -m sysinit.futures.adhoc.build_roll_calendars_custom \
  --data-dir /home/samir/data/consolidated/futures_contract_prices \
  --output-dir /home/samir/data/consolidated/roll_calendars
```

---

### Step 6: Extend Multiple & Adjusted Prices

Use the production incremental update (preserves deep history):

```python
from sysdata.data_blob import dataBlob
from sysproduction.update_multiple_adjusted_prices import update_multiple_adjusted_prices_for_instrument
from sysproduction.data.prices import diagPrices

with dataBlob(log_name="Consolidation-Update") as data:
    diag = diagPrices(data)
    instruments = sorted(diag.get_list_of_instruments_in_multiple_prices())
    
    failed = []
    for i, code in enumerate(instruments):
        print(f"[{i+1}/{len(instruments)}] {code}")
        try:
            update_multiple_adjusted_prices_for_instrument(code, data)
        except Exception as e:
            print(f"  FAILED: {e}")
            failed.append((code, str(e)))
    
    print(f"\nDone. {len(failed)} failures:")
    for code, err in failed:
        print(f"  {code}: {err}")
```

---

### Step 7: Add New Instruments

For instruments in merged contract prices that don't exist in canonical derived data, use init scripts.

---

### Step 8: Verify Final Output

```
/home/samir/data/consolidated/
├── futures_contract_prices/     # Merged from all 5 sources + gap fills
├── roll_calendars/              # Extended CSVs
├── futures_multiple_prices/     # Extended parquet (deep history preserved)
├── futures_adjusted_prices/     # Extended parquet (deep history preserved)
├── spotfx_prices/               # Copied from canonical
├── consolidation_report.csv     # Conflict log
└── gap_contracts_manifest.csv   # Gap-fill contract list
```

---

## Summary

| Step | Action | Notes |
|------|--------|-------|
| 1 | Merge contract prices | 5 sources, mtime priority |
| 2 | Build baseline derived data | Canonical + pst-csv-data overlay (40 instruments) |
| 3 | **Identify & source gap contracts** | **Generate manifest (444 contracts), retrieve from Barchart/Databento, ingest** |
| 4 | Configure parquet store | Point to consolidated dir |
| 5 | Extend roll calendars | Custom builder (merges with existing) |
| 6 | Extend multiple/adjusted | Production incremental update (preserves history) |
| 7 | Add new instruments | Init scripts for genuinely new |
| 8 | Verify | Date range checks |
