# DataBento Gap-Filling Implementation Plan

## Overview

This document outlines the plan for downloading missing futures contract data from DataBento to fill gaps identified in the data consolidation process. The manifest at `/home/samir/data/consolidated/gap_contracts_manifest.csv` contains **439 contracts across 200 instruments** that need to be retrieved.

## Current State

- **Step 1 Complete**: Contract prices merged from 3 sources
- **Step 2 Partial Complete**: Gap manifest generated at `/home/samir/data/consolidated/gap_contracts_manifest.csv`
- **Next**: Build symbology mapping and download missing contracts

## Gap Manifest Structure

```csv
instrument,contract_date,role,gap_start,gap_end,gap_days,data_needed_from,data_needed_to
AEX_mini,20240400,PRICE,2024-03-29,2024-04-17,21,2024-03-29,2024-04-17
ALUMINIUM,20240600,PRICE,2024-03-29,2024-04-17,21,2024-03-29,2024-04-17
...
```

Each row represents a contract (identified by `instrument` + `contract_date`) that needs data for a specific date range.

## Part 1: Symbology Mapping Plan

### 1.1 DataBento Symbology Overview

DataBento uses exchange-native symbology with the following format:

```
{ROOT}{MONTH_CODE}{YEAR_DIGIT}
```

**Month Codes** (industry standard):
```
F=Jan, G=Feb, H=Mar, J=Apr, K=May, M=Jun,
N=Jul, Q=Aug, U=Sep, V=Oct, X=Nov, Z=Dec
```

**Examples**:
- `ESM4` = E-mini S&P 500, June 2024
- `CLZ4` = Crude Oil, December 2024
- `ZBH4` = US Treasury Bonds, March 2024

### 1.2 pysystemtrade to DataBento Conversion

**pysystemtrade format**: `ROOT` + `YYYY` + `MM` (e.g., `ES202406`)
**DataBento format**: `ROOT` + `MONTH_CODE` + `YEAR_DIGIT` (e.g., `ESM4`)

**Conversion Logic**:
```python
MONTH_CODES = {
    1: "F", 2: "G", 3: "H", 4: "J", 5: "K", 6: "M",
    7: "N", 8: "Q", 9: "U", 10: "V", 11: "X", 12: "Z"
}

# Example: ES202406 -> ESM4
root = "ES"  # Extracted from pysystemtrade instrument
year = 2024  # From contract_date
month = 6    # From contract_date
month_code = MONTH_CODES[month]  # "M"
year_digit = str(year)[-1]       # "4"
databento_symbol = f"{root}{month_code}{year_digit}"  # "ESM4"
```

### 1.3 Exchange/Dataset Mapping

DataBento organizes data by **dataset** (exchange). Each instrument maps to a specific dataset:

| Exchange | Dataset ID | Instruments |
|----------|------------|-------------|
| **CME Globex** | `GLBX.MDP3` | ES, NQ, YM, CL, GC, currencies (EUR, GBP, JPY), SOFR, etc. |
| **ICE Futures Europe** | `IFEU.IMPACT` | Brent (B), Gasoil (G), softs (cocoa, coffee), CO2 |
| **ICE Futures US** | `IFUS.IMPACT` | Sugar, coffee, cocoa (US) |
| **ICE Endex** | `NDEX.IMPACT` | Dutch gas (TTF), power |
| **Eurex** | `XEUR.EOBI` | Bund, Bobl, Schatz, DAX, EuroStoxx |
| **EEX** | `XEEE.EOBI` | German power, EUA (carbon) |
| **SGX** | `XNAS.ITCH` | A50, Nifty, iron ore |
| **COMEX** | `GLBX.MDP3` | Gold, silver, copper (same as CME) |

**Mapping Approach**:

1. **Create a JSON mapping file** (`sysinit/futures/config/databento_mappings.json`) with entries like:
```json
{
  "ES": {
    "databento_root": "ES",
    "dataset": "GLBX.MDP3",
    "exchange": "CME"
  },
  "BRENT_W": {
    "databento_root": "B",
    "dataset": "IFEU.IMPACT",
    "exchange": "ICE"
  },
  "BUND": {
    "databento_root": "GBL",
    "dataset": "XEUR.EOBI",
    "exchange": "EUREX"
  }
}
```

2. **Special Cases to Handle**:
   - **Different roots on different exchanges**: Some instruments trade on multiple exchanges (e.g., EUR on CME and ICE)
   - **Suffixes**: `_mini`, `_micro`, `_LDN` suffixes in pysystemtrade may map to different roots
   - **Non-standard symbols**: LME metals (ALUMINIUM_LME, COPPER_LME) need special mapping
   - **Asian markets**: SGX, HKEX, OSE instruments may have different symbology

3. **Manual Research Required**:
   - Check DataBento's symbol reference: https://databento.com/docs/standards-and-conventions/symbology
   - Use DataBento's `symbology.resolve()` API to verify symbol mappings
   - Test each instrument with a single date query before bulk download

### 1.4 Instrument Mapping Research Checklist

For each of the 200 instruments in the gap manifest, determine:

- [ ] **DataBento root symbol** (may differ from pysystemtrade name)
- [ ] **Dataset** (exchange venue code)
- [ ] **Schema** (ohlcv-1d for daily, ohlcv-1h for hourly)
- [ ] **Date availability** (DataBento's historical coverage varies by dataset)

**Priority Tiers**:
1. **Tier 1** (CME/CBOT/NYMEX/COMEX): Most common, GLBX.MDP3 dataset, extensive history
2. **Tier 2** (ICE Europe): IFEU.IMPACT, good coverage from Dec 2018
3. **Tier 3** (Eurex): XEUR.EOBI, recent addition but growing
4. **Tier 4** (Asian/Specialty): SGX, OSE, LME - may have limited coverage or require special handling

## Part 2: Download Script Architecture

### 2.1 Script Components

```
download_gap_contracts.py
├── Configuration Loading
│   ├── Read manifest CSV
│   ├── Load instrument mappings
│   └── Validate API key
├── Symbol Resolution
│   ├── Convert contract_date to DataBento symbol
│   ├── Apply instrument-specific root mappings
│   └── Handle special cases
├── Data Retrieval
│   ├── Batch requests by dataset (for efficiency)
│   ├── Rate limiting (respect API limits)
│   └── Error handling with retries
├── Data Transformation
│   ├── Rename columns to pysystemtrade format
│   ├── Handle timezone conversion
│   └── Filter to requested date range
└── Output
    ├── Write Parquet files to consolidated directory
    ├── Log successful downloads
    └── Report failures for retry
```

### 2.2 Data Flow

```
Manifest CSV
    ↓
[For each contract]
    ↓
Map instrument → DataBento (root, dataset)
    ↓
Convert contract_date → DataBento symbol
    ↓
Query DataBento API (timeseries.get_range)
    ↓
Transform OHLCV columns
    ↓
Write to /home/samir/data/consolidated/futures_contract_prices/
    ↓
Parquet file: {instrument}#{contract_date}.parquet
```

### 2.3 Schema Mapping

**DataBento Output** → **pysystemtrade Format**:

```python
COLUMN_MAP = {
    'open': 'OPEN',
    'high': 'HIGH', 
    'low': 'LOW',
    'close': 'FINAL',
    'volume': 'VOLUME'
}
```

**Index**: DataBento returns `ts_event` (timestamp) → pysystemtrade uses datetime index

### 2.4 Batch Processing Strategy

To optimize API usage and reduce costs:

1. **Group by Dataset**: Process all GLBX.MDP3 instruments together, then IFEU.IMPACT, etc.
2. **Batch Symbol Requests**: DataBento allows multiple symbols per request (up to 100)
3. **Parallel Downloads**: Use asyncio or ThreadPoolExecutor for concurrent requests
4. **Resume Capability**: Save progress to allow resuming interrupted downloads

### 2.5 Error Handling

**Expected Errors**:
- `404 Not Found`: Symbol doesn't exist in dataset
- `429 Rate Limit`: Too many requests
- `402 Payment Required**: Insufficient API credits
- Empty response: No data for date range

**Retry Logic**:
- Exponential backoff for rate limits
- Skip and log symbols that don't exist
- Quarantine failed downloads for manual review

## Part 3: Implementation Steps

### Step 3.1: Create Mapping Configuration

1. Extract unique instruments from gap manifest (200 instruments)
2. Research each instrument's DataBento mapping
3. Create `databento_mappings.json` with verified mappings
4. Include metadata: dataset, exchange, schema, notes

### Step 3.2: Build Download Script

1. Implement core download logic
2. Add batch processing
3. Implement error handling and retries
4. Add progress tracking and logging
5. Create dry-run mode for testing

### Step 3.3: Testing

1. **Unit Tests**: Test symbol conversion functions
2. **Integration Test**: Download single contract with known data
3. **Batch Test**: Download 10 contracts from different datasets
4. **Full Run**: Execute on full manifest with monitoring

### Step 3.4: Validation

After download, verify:
1. All expected files exist
2. Date ranges cover gaps
3. OHLCV data is present and reasonable
4. No duplicate timestamps

## Part 4: Usage Instructions

### Prerequisites

1. **DataBento Account**: Sign up at https://databento.com
2. **API Key**: Export as environment variable:
   ```bash
   export DATABENTO_API_KEY="db-..."
   ```
3. **Credits**: Ensure sufficient API credits (check DataBento pricing)

### Running the Download

```bash
# Dry run (verify mappings without downloading)
python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --mapping sysinit/futures/config/databento_mappings.json \
  --output /home/samir/data/consolidated/futures_contract_prices \
  --dry-run

# Full download
python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --mapping sysinit/futures/config/databento_mappings.json \
  --output /home/samir/data/consolidated/futures_contract_prices \
  --schema ohlcv-1d \
  --max-workers 4

# Resume interrupted download
python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --mapping sysinit/futures/config/databento_mappings.json \
  --output /home/samir/data/consolidated/futures_contract_prices \
  --resume-from progress.json
```

### Post-Download

After downloading, merge new data into consolidated contract prices:

```python
# The download script outputs Parquet files directly to the consolidated directory
# Existing files will be updated (gap-filled), new files created
# Verify with:
ls /home/samir/data/consolidated/futures_contract_prices/ | wc -l
```

## Part 5: Cost Estimation

DataBento pricing is based on **data size** and **dataset**. Rough estimates:

- **GLBX.MDP3 (CME)**: ~$0.50-1.00 per instrument per day of history
- **IFEU.IMPACT (ICE Europe)**: ~$0.50-1.00 per instrument per day
- **XEUR.EOBI (Eurex)**: ~$0.50 per instrument per day

For 439 contracts with average 30 days gap:
- Estimated cost: $200-400 (highly dependent on actual gaps and datasets)

**Cost Optimization**:
- Use `ohlcv-1d` instead of higher frequency data
- Batch symbol requests (reduces overhead)
- Verify all mappings in dry-run first

## Appendix A: Sample Mappings

| pysystemtrade | DataBento Root | Dataset | Notes |
|---------------|----------------|---------|-------|
| ES | ES | GLBX.MDP3 | E-mini S&P 500 |
| NQ | NQ | GLBX.MDP3 | E-mini Nasdaq |
| CL | CL | GLBX.MDP3 | WTI Crude Oil |
| GC | GC | GLBX.MDP3 | Gold |
| ZB | ZB | GLBX.MDP3 | US Treasury Bonds |
| BRENT_W | B | IFEU.IMPACT | ICE Brent Crude |
| GASOIL | G | IFEU.IMPACT | ICE Low Sulphur Gasoil |
| BUND | GBL | XEUR.EOBI | Euro Bund |
| DAX | FDAX | XEUR.EOBI | DAX Futures |
| EUROSTX | FESX | XEUR.EOBI | Euro Stoxx 50 |
| CORN | ZC | GLBX.MDP3 | CBOT Corn |
| SOYBEAN | ZS | GLBX.MDP3 | CBOT Soybeans |
| EUR | 6E | GLBX.MDP3 | EUR/USD Futures |
| GBP | 6B | GLBX.MDP3 | GBP/USD Futures |
| JPY | 6J | GLBX.MDP3 | JPY/USD Futures |

## Appendix B: Resources

- **DataBento Docs**: https://databento.com/docs
- **Symbology Guide**: https://databento.com/docs/standards-and-conventions/symbology
- **Dataset Catalog**: https://databento.com/datasets
- **Python API**: https://databento.com/docs/api-reference/python

---

*Document Version: 1.0*
*Created: 2026-03-04*
*Next Step: Implement mapping configuration and download script*
