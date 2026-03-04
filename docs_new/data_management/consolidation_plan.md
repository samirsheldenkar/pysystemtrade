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

| Category | Count | Description |
|----------|-------|-------------|
| No gap (overlap) | 9 | SP500, GOLD, AUD, GBP, etc. |
| Gap, covered by `pst-csv-data` | 36 | CSVs extending to Sep 2025 |
| Gap, 8-21 days | 150 | Most common |
| Gap, 22-30 days | 18 | Medium |
| Gap, >100 days | 32 | Asian/niche markets, up to 238 days |
| No contract data | 7 | Only in canonical derived data |

**Total missing contracts to fill all gaps: 444 across 200 instruments.**

### `pst-csv-data` Frequency

Both pst-csv and canonical data are **hourly** (not daily). However, canonical has sub-hourly data for some instruments (15-min intervals for BUND, AEX, etc.), resulting in more rows. For the 40 pst-csv instruments, a merge approach (append only post-2024-03-28 rows) preserves the canonical sub-hourly history.

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

### Step 2: Identify and Source Gap-Filling Contracts

**Phase 1 — Generate manifest** (`/tmp/generate_gap_manifest.py`):

```python
"""
Generate CSV manifest of contracts needed to fill gaps.
Output: /home/samir/data/consolidated/gap_contracts_manifest.csv
"""
import pandas as pd, os, glob

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
    if not mp_file.endswith('.parquet'): continue
    inst = mp_file.replace('.parquet', '')
    if inst in PST_INSTRUMENTS: continue

    mp = pd.read_parquet(os.path.join(MP_DIR, mp_file))
    mp_end = mp.index.max()

    cp_min = pd.Timestamp.max
    for d in CP_DIRS:
        for f in glob.glob(os.path.join(d, f'{inst}#*.parquet')):
            df = pd.read_parquet(f)
            if len(df) > 0 and df.index.min() < cp_min:
                cp_min = df.index.min()

    if cp_min == pd.Timestamp.max: continue
    gap_days = (cp_min - mp_end).days
    if gap_days <= 1: continue

    last_row = mp.iloc[-1]
    contracts = {
        'PRICE': str(int(last_row['PRICE_CONTRACT'])),
        'CARRY': str(int(last_row['CARRY_CONTRACT'])),
        'FORWARD': str(int(last_row['FORWARD_CONTRACT'])),
    }

    gap_start = (mp_end + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    gap_end = (cp_min - pd.Timedelta(days=1)).strftime('%Y-%m-%d')

    seen = set()
    for role, contract_date in contracts.items():
        if contract_date in seen: continue
        seen.add(contract_date)
        rows.append({
            'instrument': inst, 'contract_date': contract_date, 'role': role,
            'gap_start': gap_start, 'gap_end': gap_end, 'gap_days': gap_days,
        })

manifest = pd.DataFrame(rows)
manifest.to_csv(OUTPUT, index=False)
print(f"Manifest: {len(manifest)} contracts across {manifest['instrument'].nunique()} instruments")
print(manifest.head(10).to_string(index=False))
```

> [!IMPORTANT]
> The `instrument` column uses pysystemtrade codes (e.g., `BUND`, `CRUDE_W`). These need mapping to exchange symbols for data providers. pysystemtrade maintains mappings in [instrumentconfig.csv](file:///home/samir/pysystemtrade/data/futures/csvconfig/instrumentconfig.csv).
>
> - **Barchart**: symbols like `ZBM24` (root + month code + 2-digit year). Month codes: F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun, N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec
> - **Databento**: exchange-native symbols with venue prefix (e.g., `GLBX.MBO`). Python API: `databento.Historical().timeseries.get_range()`

**Phase 2 — Retrieve data** using Barchart or Databento based on the manifest.

**Phase 3 — Ingest** retrieved data into consolidated contract prices:

```python
import pandas as pd, os

def ingest_gap_contract(instrument, contract_date, df, dest_dir):
    """df should have DatetimeIndex and columns: OPEN, HIGH, LOW, FINAL, VOLUME"""
    path = f"{dest_dir}/{instrument}#{contract_date}.parquet"
    if os.path.exists(path):
        existing = pd.read_parquet(path)
        new_rows = df[~df.index.isin(existing.index)]
        if len(new_rows) > 0:
            combined = pd.concat([new_rows, existing]).sort_index()
            combined.to_parquet(path)
    else:
        df.to_parquet(path)
```

---

### Step 3: Configure Parquet Store

```yaml
# private_config.yaml
parquet_store: /home/samir/data/consolidated
```

---

### Step 4: Build Baseline Derived Data

> [!NOTE]
> This step comes **after** all raw contract data is gathered (Steps 1-2), so that derived data generation has the complete dataset available.

```bash
# Copy canonical deep-history derived data as starting point
cp -r /home/samir/data/futures/futures_multiple_prices /home/samir/data/consolidated/futures_multiple_prices
cp -r /home/samir/data/futures/futures_adjusted_prices /home/samir/data/consolidated/futures_adjusted_prices
cp -r /home/samir/data/futures/roll_calendars_from_db /home/samir/data/consolidated/roll_calendars
cp -r /home/samir/data/futures/spotfx_prices /home/samir/data/consolidated/spotfx_prices
```

**Merge** pst-csv-data for the 40 instruments (append post-2024-03-28 rows only, preserving canonical sub-hourly history):

```python
import pandas as pd, os

PST_MP = '/home/samir/pst-csv-data/data/multiple_prices_csv'
PST_AP = '/home/samir/pst-csv-data/data/adjusted_prices_csv'
OUT_MP = '/home/samir/data/consolidated/futures_multiple_prices'
OUT_AP = '/home/samir/data/consolidated/futures_adjusted_prices'

for f in sorted(os.listdir(PST_MP)):
    if not f.endswith('.csv'): continue
    inst = f.replace('.csv', '')
    
    # Multiple prices: merge (keep canonical history, append pst-csv extension)
    pst = pd.read_csv(os.path.join(PST_MP, f), index_col=0, parse_dates=True)
    can_f = os.path.join(OUT_MP, f'{inst}.parquet')
    if os.path.exists(can_f):
        can = pd.read_parquet(can_f)
        can_end = can.index.max()
        new_rows = pst[pst.index > can_end]
        merged = pd.concat([can, new_rows]).sort_index()
        merged.to_parquet(can_f)
        print(f"  {inst}: appended {len(new_rows)} rows (canonical={len(can)}, now={len(merged)})")
    else:
        pst.to_parquet(can_f)
        print(f"  {inst}: created from pst-csv ({len(pst)} rows)")
    
    # Adjusted prices: same merge
    ap_pst_f = os.path.join(PST_AP, f)
    ap_can_f = os.path.join(OUT_AP, f'{inst}.parquet')
    if os.path.exists(ap_pst_f):
        ap_pst = pd.read_csv(ap_pst_f, index_col=0, parse_dates=True)
        if os.path.exists(ap_can_f):
            ap_can = pd.read_parquet(ap_can_f)
            ap_new = ap_pst[ap_pst.index > ap_can.index.max()]
            ap_merged = pd.concat([ap_can, ap_new]).sort_index()
            ap_merged.to_parquet(ap_can_f)
        else:
            ap_pst.to_parquet(ap_can_f)
```

---

### Step 5: Extend Roll Calendars

```bash
python -m sysinit.futures.adhoc.build_roll_calendars_custom \
  --data-dir /home/samir/data/consolidated/futures_contract_prices \
  --output-dir /home/samir/data/consolidated/roll_calendars
```

---

### Step 6: Extend Multiple & Adjusted Prices

Production incremental update (preserves deep history):

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
├── futures_contract_prices/     # Steps 1+2: merged + gap-filled
├── roll_calendars/              # Step 5: extended CSVs
├── futures_multiple_prices/     # Steps 4+6: deep history + extended
├── futures_adjusted_prices/     # Steps 4+6: deep history + extended
├── spotfx_prices/               # Step 4: copied
├── consolidation_report.csv     # Step 1: conflict log
└── gap_contracts_manifest.csv   # Step 2: gap-fill contract list
```

## Summary

| Step | Action | Notes |
|------|--------|-------|
| 1 | Merge contract prices | 5 sources, mtime priority |
| 2 | **Identify & source gap contracts** | **Manifest (444 contracts, 200 instruments), retrieve from Barchart/Databento** |
| 3 | Configure parquet store | Point to consolidated dir |
| 4 | Build baseline derived data | Canonical + merge pst-csv-data (append only, preserves sub-hourly) |
| 5 | Extend roll calendars | Custom builder (merges with existing) |
| 6 | Extend multiple/adjusted | Production incremental update (preserves history) |
| 7 | Add new instruments | Init scripts for genuinely new |
| 8 | Verify | Date range checks |
