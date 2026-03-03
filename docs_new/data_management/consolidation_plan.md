# Futures Data Consolidation Plan

## Background

Data lives across 5 directories under `/home/samir/data/`:

| Directory | Contents | File Count | Download Date (mtime) | Latest Data Date | Role |
|-----------|----------|------------|----------------------|-----------------|------|
| `futures_dev/` | `futures_contract_prices/` only | 13,142 | 2025-09-04 | ~2025-06-06 | Earliest IB download |
| `futures_new/` | `futures_contract_prices/` only | 22,349 | 2025-11-06 | ~2025-06-06 | Second IB download (more contracts, same date range as dev) |
| `futures_20251119/` | `futures_contract_prices/` only | 18,256 | 2025-11-20 | ~2025-11-19 | IB download from Nov 2025 |
| `futures/` | All 5 data types | 18,447 contract + 252 adj + 252 multi + 283 roll cal + 12 spotfx | 2026-02-03 | ~2025-04-17 | Canonical historical data (deepest history, but ends earliest) |
| `futures_20260204/` | `futures_contract_prices/` only | 21,820 | 2026-02-12 | ~2026-02-17 | **Most recent** IB download |

> [!IMPORTANT]
> **Validated ordering** (oldest → newest by download mtime): `futures_dev` → `futures_new` → `futures_20251119` → `futures` (canonical) → `futures_20260204`. The `futures_20260204` folder has the most recent data (extending to Feb 2026), **not** `futures_new`. `futures_new` and `futures_dev` have similar data end dates (~June 2025) but `futures_new` has more contracts and a later mtime. The canonical `futures/` has the deepest historical coverage but its contract prices only extend to ~April 2025.

All contract price files use parquet format with `INSTRUMENT#CONTRACT.parquet` naming. Some files in `futures/` also have `Day@` prefixed variants for daily frequency data. The 4 non-canonical dirs only have contract prices — derived data must be regenerated.

The pysystemtrade data pipeline flows: **Contract Prices → Roll Calendars → Multiple Prices → Adjusted Prices**, with FX prices as a parallel independent stream.

---

## Step-by-Step Consolidation Walkthrough

### Step 1: Merge Contract Prices

**Goal**: Produce a single `futures_contract_prices/` directory with one parquet file per contract, containing the best merged data from all 5 sources.

**How**: The existing `FuturesConsolidator` in [consolidate_futures.py](file:///home/samir/pysystemtrade/sysinit/futures/consolidate_futures.py) handles this. It sorts sources by file modification time (oldest first), reads the oldest as the "master", then for each newer file: logs conflicts (values differing > 1e-6) and overwrites overlapping rows with the newer file's data. This means the **most recently modified file wins** for any given date.

**Command**:
```bash
cd /home/samir/pysystemtrade
python -m sysinit.futures.consolidate_futures \
  --sources \
    /home/samir/data/futures_dev/futures_contract_prices \
    /home/samir/data/futures_new/futures_contract_prices \
    /home/samir/data/futures_20251119/futures_contract_prices \
    /home/samir/data/futures/futures_contract_prices \
    /home/samir/data/futures_20260204/futures_contract_prices \
  --dest /home/samir/data/consolidated/futures_contract_prices
```

> [!IMPORTANT]
> Source order is from **oldest to newest download** so that the most recent data wins on overlaps. `futures_20260204` is listed last as it contains the freshest data (to Feb 2026).

**Validation**:
1. Check file count: consolidated should have ≥ 22,349 unique contracts (the max across sources)
2. Review `consolidation_report.csv` for conflicts — spot check a few
3. Spot-check contracts with pandas:
   ```python
   import pandas as pd
   for src in ["futures_dev", "futures_new", "futures_20251119", "futures", "futures_20260204"]:
       path = f"/home/samir/data/{src}/futures_contract_prices/BUND#20250600.parquet"
       try:
           df = pd.read_parquet(path)
           print(f"{src}: {len(df)} rows, {df.index.min()} to {df.index.max()}")
       except: print(f"{src}: not found")
   merged = pd.read_parquet("/home/samir/data/consolidated/futures_contract_prices/BUND#20250600.parquet")
   print(f"MERGED: {len(merged)} rows, {merged.index.min()} to {merged.index.max()}")
   ```
4. Verify the merged file has the widest date range and most rows

---

### Step 2: Configure pysystemtrade to Read from Consolidated Data

**Goal**: Point the pysystemtrade parquet data layer at the consolidated directory.

**How**: Set `parquet_store` in `private_config.yaml`:
```yaml
parquet_store: /home/samir/data/consolidated
```

**Validation**:
```python
from sysdata.data_blob import dataBlob
data = dataBlob()
contracts = data.db_futures_contract_price_data.get_contracts_with_merged_price_data()
print(f"Found {len(contracts)} contracts")
```

---

### Step 3: Generate Roll Calendars

**Goal**: Produce CSV roll calendars for every instrument from the merged contract prices.

#### Script Comparison

There are two available approaches:

| Feature | [rollcalendars_from_db_prices_to_csv.py](file:///home/samir/pysystemtrade/sysinit/futures/rollcalendars_from_db_prices_to_csv.py) | [build_roll_calendars_custom.py](file:///home/samir/pysystemtrade/sysinit/futures/adhoc/build_roll_calendars_custom.py) |
|---------|---|---|
| **Data source** | Reads via `diagPrices()` → parquet store (needs Step 2 configured) | Reads parquet files directly from a directory (standalone) |
| **Roll date logic** | Uses `rollCalendar.create_from_prices()` — sophisticated algorithm in `build_roll_calendars.py` that finds best matching roll dates across current/next/carry contracts | Uses volume/OI crossover with 5-business-day window around ideal roll date from roll params; falls back to ideal date |
| **Carry contract** | Correctly derives carry contract from roll parameters | Sets `carry_contract = next_contract` (simplification — may be incorrect for instruments where carry ≠ next) |
| **Merge with existing** | **No** — writes fresh calendar, errors if exists without `ignore_duplication` | **Yes** — `_save_calendar()` loads existing CSV and merges with new rolls (dedup by `current_contract`, keeps latest) |
| **Validation** | Built-in `check_if_date_index_monotonic()` and `check_dates_are_valid_for_prices()` | No built-in validation |
| **Batch mode** | Per-instrument (need wrapper loop) | Built-in `run()` iterates all instruments |

#### Recommendation

Use a **two-phase approach**:
1. **Start with the canonical roll calendars** from `futures/roll_calendars_from_db/` as a baseline — these have been manually curated and are known-good for historical data
2. **Extend them** using `build_roll_calendars_custom.py` to add new roll entries for contracts that now exist in the merged data but weren't in the original calendars

Alternatively, use `rollcalendars_from_db_prices_to_csv.py` to regenerate from scratch (more correct carry contracts, built-in validation) but this requires Step 2 to be configured first and may need manual fixes for edge cases.

**Phase 1 — Copy canonical calendars as baseline**:
```bash
cp -r /home/samir/data/futures/roll_calendars_from_db /home/samir/data/consolidated/roll_calendars
```

**Phase 2 — Extend with new data** (using the custom builder):
```bash
cd /home/samir/pysystemtrade
python -m sysinit.futures.adhoc.build_roll_calendars_custom \
  --data-dir /home/samir/data/consolidated/futures_contract_prices \
  --output-dir /home/samir/data/consolidated/roll_calendars
```

The custom builder's `_save_calendar()` merges new rolls into the existing CSVs, so the baseline calendars are preserved and extended.

**Validation**:
1. Check that the number of CSVs is ≥ 283 (the canonical count)
2. Compare updated calendars for key instruments:
   ```python
   import pandas as pd
   for inst in ["SP500", "GOLD", "BUND", "CORN"]:
       old = pd.read_csv(f"/home/samir/data/futures/roll_calendars_from_db/{inst}.csv", index_col=0, parse_dates=True)
       new = pd.read_csv(f"/home/samir/data/consolidated/roll_calendars/{inst}.csv", index_col=0, parse_dates=True)
       print(f"{inst}: old={len(old)} rows -> new={len(new)} rows, extends to {new.index.max()}")
   ```
3. New calendars should have equal or more rows, extending to more recent dates

---

### Step 4: Generate Multiple Prices

**Goal**: Produce parquet files with PRICE/CARRY/FORWARD contract series for each instrument.

> [!WARNING]
> **These scripts perform a full replacement, not a merge.** The `add_multiple_prices(ignore_duplication=True)` call in pysystemtrade writes the new data as a complete replacement of any existing parquet file. The multiple prices are **regenerated from scratch** using the merged contract prices (Step 1) and roll calendars (Step 3). This means the output will only cover the date range that the merged contract prices and roll calendar support — which should be a superset of the existing canonical data since the merged set includes the canonical data plus newer downloads.

**How**: The function `process_multiple_prices_single_instrument()` reads the roll calendar CSV, reads all contract closing prices from the parquet store, stitches contracts together using the roll calendar, and writes the result as a parquet file (full overwrite).

**Pre-check**: Before running, verify the merged contract prices cover at least as much history as the existing canonical `futures_multiple_prices/`:
```python
import pandas as pd
# Compare date range of existing vs what merged data supports
old_mp = pd.read_parquet("/home/samir/data/futures/futures_multiple_prices/SP500.parquet")
print(f"Existing: {old_mp.index.min()} to {old_mp.index.max()}")
# Then after generating new, compare
```

**Script** (write to `/tmp/generate_multiple_prices.py`):
```python
from sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db import (
    process_multiple_prices_single_instrument,
)
import os

ROLL_CAL_PATH = "/home/samir/data/consolidated/roll_calendars"

instrument_list = sorted([
    f.replace(".csv", "") for f in os.listdir(ROLL_CAL_PATH) if f.endswith(".csv")
])

failed = []
for i, code in enumerate(instrument_list):
    print(f"[{i+1}/{len(instrument_list)}] {code}")
    try:
        process_multiple_prices_single_instrument(
            code,
            csv_roll_data_path=ROLL_CAL_PATH,
            ADD_TO_DB=True,
            ADD_TO_CSV=False,
        )
    except Exception as e:
        print(f"  FAILED: {e}")
        failed.append((code, str(e)))

print(f"\nDone. {len(failed)} failures:")
for code, err in failed:
    print(f"  {code}: {err}")
```

**Validation**:
1. Count instruments: should match roll calendar count
2. For key instruments, verify the date range is at least as wide as the canonical data:
   ```python
   import pandas as pd
   for inst in ["SP500", "GOLD", "BUND"]:
       old = pd.read_parquet(f"/home/samir/data/futures/futures_multiple_prices/{inst}.parquet")
       new = pd.read_parquet(f"/home/samir/data/consolidated/futures_multiple_prices/{inst}.parquet")
       print(f"{inst}: old {old.index.min()} to {old.index.max()} ({len(old)} rows)")
       print(f"       new {new.index.min()} to {new.index.max()} ({len(new)} rows)")
   ```
3. The new data should start at the same date or earlier, and end at a later date

---

### Step 5: Generate Adjusted Prices

**Goal**: Produce back-adjusted continuous price series for each instrument.

> [!WARNING]
> **Same as Step 4 — this is a full replacement, not a merge.** The adjusted prices are regenerated from scratch based on the multiple prices from Step 4. The `futuresAdjustedPrices.stitch_multiple_prices()` function reads the entire multiple price history and produces a complete adjusted series via panama stitching. Since the multiple prices from Step 4 should cover the full merged date range, the adjusted prices will too.

**Script** (write to `/tmp/generate_adjusted_prices.py`):
```python
from sysinit.futures.adjustedprices_from_db_multiple_to_db import (
    process_adjusted_prices_single_instrument,
)
from sysproduction.data.prices import diagPrices

diag = diagPrices()
instrument_list = sorted(diag.db_futures_multiple_prices_data.get_list_of_instruments())

failed = []
for i, code in enumerate(instrument_list):
    print(f"[{i+1}/{len(instrument_list)}] {code}")
    try:
        process_adjusted_prices_single_instrument(code, ADD_TO_DB=True, ADD_TO_CSV=False)
    except Exception as e:
        print(f"  FAILED: {e}")
        failed.append((code, str(e)))

print(f"\nDone. {len(failed)} failures:")
for code, err in failed:
    print(f"  {code}: {err}")
```

**Validation**:
```python
for inst in ["SP500", "GOLD", "BUND"]:
    old = pd.read_parquet(f"/home/samir/data/futures/futures_adjusted_prices/{inst}.parquet")
    new = pd.read_parquet(f"/home/samir/data/consolidated/futures_adjusted_prices/{inst}.parquet")
    print(f"{inst}: old {old.index.min()} to {old.index.max()} -> new {new.index.min()} to {new.index.max()}")
```

---

### Step 6: Copy SpotFX Prices

**Goal**: Bring the FX data into the consolidated directory.

Since no other directories have spotfx data, this is a simple copy:

```bash
cp -r /home/samir/data/futures/spotfx_prices /home/samir/data/consolidated/spotfx_prices
```

**Validation**:
```python
from sysproduction.data.currency_data import dataCurrency
dc = dataCurrency()
for code in dc.db_fx_prices_data.get_list_of_fxcodes():
    prices = dc.db_fx_prices_data.get_fx_prices(code)
    print(f"  {code}: {len(prices)} rows, {prices.index.min()} to {prices.index.max()}")
```

---

### Step 7: Verify Final Output

```
/home/samir/data/consolidated/
├── futures_contract_prices/     # Step 1: merged parquet (INSTRUMENT#CONTRACT.parquet)
├── roll_calendars/              # Step 3: CSV files per instrument
├── futures_multiple_prices/     # Step 4: parquet files per instrument
├── futures_adjusted_prices/     # Step 5: parquet files per instrument
├── spotfx_prices/               # Step 6: parquet files per FX pair
└── consolidation_report.csv     # Step 1: conflict log
```

---

## Summary

| Step | Action | Depends On | Est. Time |
|------|--------|------------|-----------|
| 1 | Merge contract prices (`FuturesConsolidator`) | Nothing | ~30-60 min |
| 2 | Configure parquet store path | Step 1 | ~1 min |
| 3 | Copy canonical roll calendars + extend with custom builder | Steps 1, 2 | ~10-30 min |
| 4 | Generate multiple prices (full regeneration) | Steps 2, 3 | ~10-30 min |
| 5 | Generate adjusted prices (full regeneration) | Step 4 | ~5-15 min |
| 6 | Copy spotfx prices | Nothing (parallel) | ~1 min |
| 7 | Verify final output structure | Steps 1-6 | ~5 min |

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Multiple/adjusted prices are a full overwrite — could lose historical depth if merged contract prices don't go back far enough | The canonical `futures/` data is included in the merge (Step 1), so historical depth is preserved. Validate date ranges in Steps 4-5 |
| Roll calendar generation may fail for some instruments | Baseline from canonical CSVs ensures coverage; custom builder only extends |
| `Day@` prefixed files treated as separate contracts | These are daily-frequency snapshots — the pipeline uses mixed-frequency (non-prefixed) files for roll calendar generation |
| `build_roll_calendars_custom.py` sets `carry_contract = next_contract` | Acceptable for the extension phase since baseline carry contracts from canonical calendars are preserved |
| Conflict report may be very large | Review by instrument; focus on recent dates |
