# DataBento Gap-Filling Download Tool

This tool downloads missing futures contract data from DataBento to fill gaps identified in the data consolidation process.

## Overview

The consolidation process identified **439 contracts across 200 instruments** with data gaps. This tool automates downloading those contracts from DataBento and saving them in the pysystemtrade Parquet format.

## Files

| File | Description |
|------|-------------|
| `download_gap_contracts.py` | Main download script |
| `config/databento_mappings.json` | Instrument-to-DataBento symbol mappings |
| `gap_contracts_manifest.csv` | List of contracts to download (generated in Step 2) |

## Prerequisites

### 1. DataBento Account

Sign up at [databento.com](https://databento.com) and obtain an API key.

### 2. Install DataBento Python Client

```bash
pip install databento
```

### 3. Set API Key

```bash
export DATABENTO_API_KEY="db-your-api-key-here"
```

Or pass it directly to the script with `--api-key`.

### 4. Verify DataBento Credits

Ensure you have sufficient API credits. DataBento charges per MB of data downloaded.

- **Estimated cost**: $200-400 for the full 439 contracts (depending on data frequency and gap sizes)
- **Cost optimization**: The script uses daily data (`ohlcv-1d` schema) to minimize costs

## Usage

### Step 1: Dry Run (Verify Mappings)

Before downloading, verify that all instruments have valid mappings:

```bash
cd /home/samir/pysystemtrade

python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --dry-run
```

This will:
- Check that all 200 instruments have mappings
- Print any missing or problematic mappings
- Show what would be downloaded (without actually downloading)

**Expected output**:
```
Loaded 200 instrument mappings from sysinit/futures/config/databento_mappings.json
WARNING: 75 instruments need verification: [...]
Loaded manifest with 439 contracts to download
[DRY RUN] Would download AEX_mini#20240400 from 2024-03-29 to 2024-04-17
...
```

### Step 2: Verify Symbol Mappings

Some instruments are marked with `"needs_verification": true` in the mapping file. You should verify these before proceeding:

1. Check DataBento's symbol reference: https://databento.com/docs/standards-and-conventions/symbology
2. Or use DataBento's API to test individual symbols:

```python
import databento as db

client = db.Historical("your-api-key")

# Test a symbol
result = client.symbology.resolve(
    dataset="IFEU.IMPACT",
    symbols=["B"],
    stype_in="raw_symbol",
    stype_out="instrument_id",
    start_date="2024-01-01",
)
print(result)
```

### Step 3: Run Download

Once mappings are verified, run the full download:

```bash
python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --output /home/samir/data/consolidated/futures_contract_prices \
  --schema ohlcv-1d \
  --max-workers 4
```

**Options**:
- `--manifest`: Path to the gap contracts manifest CSV
- `--output`: Directory to save Parquet files (default: consolidated futures_contract_prices)
- `--schema`: DataBento data schema (default: `ohlcv-1d` for daily OHLCV)
- `--max-workers`: Number of parallel downloads (default: 4)

### Step 4: Resume Interrupted Downloads

If the download is interrupted, resume from where it left off:

```bash
python sysinit/futures/adhoc/download_gap_contracts.py \
  --manifest /home/samir/data/consolidated/gap_contracts_manifest.csv \
  --output /home/samir/data/consolidated/futures_contract_prices \
  --resume-from /home/samir/data/consolidated/futures_contract_prices/download_progress.json
```

The script automatically saves progress to `download_progress.json` in the output directory.

## Understanding the Output

### Download Progress

The script shows progress as it downloads:

```
Progress: 50/439 (completed: 45, failed: 5)
```

### Final Summary

At completion, you'll see a summary:

```
============================================================
DOWNLOAD SUMMARY
============================================================
Total contracts processed: 439
  Completed: 410
  Failed: 29
  Skipped: 0

Failed downloads:
  - ALUMINIUM_LME#20240600: No data returned
  - COPPER_LME#20240700: No data returned
  ...
============================================================
```

### Output Files

Downloaded data is saved to:
```
/home/samir/data/consolidated/futures_contract_prices/
├── AEX_mini#20240400.parquet
├── ALUMINIUM#20240600.parquet
├── ...
└── download_progress.json
```

Each file contains OHLCV data in the pysystemtrade format:
- Index: Datetime
- Columns: OPEN, HIGH, LOW, FINAL, VOLUME

## Troubleshooting

### Missing Mappings

If you see:
```
ERROR: Unmapped instruments: ['NEW_INSTRUMENT']
```

Add the mapping to `config/databento_mappings.json`:

```json
{
  "NEW_INSTRUMENT": {
    "databento_root": "SYMBOL",
    "dataset": "GLBX.MDP3",
    "exchange": "CME",
    "schema": "ohlcv-1d",
    "notes": "Description"
  }
}
```

### No Data Returned

If downloads fail with "No data returned":

1. **Check symbol**: Verify the DataBento symbol is correct
2. **Check date range**: Data may not be available for the requested dates
3. **Check dataset**: The instrument might be on a different exchange/dataset
4. **Check availability**: Some datasets have limited historical coverage

### Rate Limiting

If you hit rate limits:

1. Reduce `--max-workers` to 2 or 1
2. The script has built-in retry logic with exponential backoff

### API Key Issues

```
ERROR: DataBento API key required
```

Ensure the API key is set:
```bash
export DATABENTO_API_KEY="db-..."
echo $DATABENTO_API_KEY  # Should show your key
```

## Mapping Reference

### Month Codes

DataBento uses standard futures month codes:

| Month | Code | Month | Code |
|-------|------|-------|------|
| Jan | F | Jul | N |
| Feb | G | Aug | Q |
| Mar | H | Sep | U |
| Apr | J | Oct | V |
| May | K | Nov | X |
| Jun | M | Dec | Z |

### Symbol Construction

**pysystemtrade format**: `ES202406` (root + YYYY + MM)
**DataBento format**: `ESM4` (root + month_code + year_digit)

Example conversions:
- `ES202406` → `ESM4` (June 2024)
- `CL202412` → `CLZ4` (December 2024)
- `BRENT_W202407` → `BN4` (July 2024 Brent)

### Dataset Codes

| Dataset | Exchange | Coverage |
|---------|----------|----------|
| `GLBX.MDP3` | CME Globex | CME, CBOT, NYMEX, COMEX |
| `IFEU.IMPACT` | ICE Futures Europe | Brent, Gasoil, Softs |
| `IFUS.IMPACT` | ICE Futures US | US Softs |
| `XEUR.EOBI` | Eurex | Bund, DAX, EuroStoxx |
| `XHKG.ITCH` | HKEX | Hang Seng indices |
| `XOSE.ITCH` | OSE | Nikkei, JGB, Topix |

## Cost Estimation

DataBento pricing is usage-based. Rough estimates:

| Dataset | Cost per Day | Notes |
|---------|--------------|-------|
| GLBX.MDP3 (CME) | ~$0.01-0.02 | Most liquid, lowest cost |
| IFEU.IMPACT (ICE) | ~$0.02-0.03 | European markets |
| XEUR.EOBI (Eurex) | ~$0.01-0.02 | European derivatives |

For 439 contracts with average 30 days gap:
- **Estimated total**: $150-300

Cost-saving tips:
- Use `ohlcv-1d` instead of higher frequency data
- Batch requests where possible (script does this automatically)
- Verify mappings first to avoid wasted API calls

## Next Steps After Download

After downloading all gap contracts:

1. **Verify downloads**:
   ```bash
   ls /home/samir/data/consolidated/futures_contract_prices/*.parquet | wc -l
   ```

2. **Continue with consolidation Step 3-8** (see consolidation_plan.md):
   - Step 3: Configure Parquet store
   - Step 4: Build baseline derived data
   - Step 5: Extend roll calendars
   - Step 6: Extend multiple & adjusted prices
   - Step 7: Add new instruments
   - Step 8: Verify final output

## Support

For DataBento-specific issues:
- DataBento Docs: https://databento.com/docs
- DataBento Support: support@databento.com

For pysystemtrade issues:
- Check the main project documentation
- Review consolidation_plan.md for context
