# Step-by-Step Guide: Consolidating Futures Data

Based on the available data directories (`/home/samir/data/*`) and the scripts in `sysinit/futures/`, here is the step-by-step process to consolidate your futures data. This will provide up-to-date, fully reconciled contract prices, roll calendars, multiple prices, and adjusted prices.

## Data Source Overview

Your raw data is spread across several directories in `/home/samir/data/`:
* `futures`: Contains older contract prices, plus multiple/adjusted prices and roll calendars.
* `futures_new`, `futures_20260204`, `futures_20260310`: Contain newer downloads of raw contract prices.
* `pst-csv-data/`: Contains CSV updates for multiple/adjusted prices for about 40 instruments.

To ensure no data is lost and the latest modifications take precedence, we will use the `FuturesConsolidator` script to merge these.

---

### Step 1: Merge Raw Contract Prices

Run the `consolidate_futures.py` script to merge the raw parquet files. Order the sources from oldest to newest so that the newest data overrides older data in case of overlaps.

```bash
python -m sysinit.futures.consolidate_futures \
  --sources \
    /home/samir/data/futures/futures_contract_prices \
    /home/samir/data/futures_new/futures_contract_prices \
    /home/samir/data/futures_20260204/futures_contract_prices \
    /home/samir/data/futures_20260310/futures_contract_prices \
  --dest /home/samir/data/consolidated/futures_contract_prices
```
*Note: The script generates a `consolidation_report.csv` in the `--dest` folder documenting any data conflicts.*

### Step 2: Configure the Parquet Store

Ensure `pysystemtrade` reads from your newly consolidated directory. Update your `private_config.yaml` to point to the new base folder:

```yaml
parquet_store: /home/samir/data/consolidated
```

### Step 3: Establish Baseline Derived Data

Before rebuilding rolling logic, we must carry over the "deep history" for derived prices and roll calendars that existed prior to the new IB downloads.

1. **Copy canonical historical data**:
```bash
cp -r /home/samir/data/futures/futures_multiple_prices /home/samir/data/consolidated/
cp -r /home/samir/data/futures/futures_adjusted_prices /home/samir/data/consolidated/
cp -r /home/samir/data/futures/roll_calendars_from_db /home/samir/data/consolidated/roll_calendars
cp -r /home/samir/data/futures/spotfx_prices /home/samir/data/consolidated/
```

2. **Merge `pst-csv-data` updates**:
For the ~40 instruments in `/home/samir/pst-csv-data/`, you need to append the new rows to the canonical `.parquet` files copied in the previous step. You can do this with the `merge_pst_csv_to_parquet.py` script:

```bash
python -m sysinit.futures.adhoc.merge_pst_csv_to_parquet
```

### Step 4: Extend Roll Calendars

Now that the raw prices are consolidated, extend the roll calendars forward using the dedicated custom builder script. This uses the new contract prices to find the optimal roll dates seamlessly.

```bash
python -m sysinit.futures.adhoc.build_roll_calendars_custom \
  --data-dir /home/samir/data/consolidated/futures_contract_prices \
  --output-dir /home/samir/data/consolidated/roll_calendars
```

### Step 5: Generate Up-to-Date Multiple & Adjusted Prices

Finally, rebuild the multiple and adjusted prices. Since we copied the historical baseline in Step 3, we can use the standard production update workflow. It will automatically detect the new roll calendars and new contract prices, generating the corresponding forward extended series.

Create and run a short script leveraging the existing pipeline:

```python
from sysdata.data_blob import dataBlob
from sysproduction.update_multiple_adjusted_prices import update_multiple_adjusted_prices_for_instrument
from sysproduction.data.prices import diagPrices

with dataBlob(log_name="Consolidation-Update") as data:
    diag = diagPrices(data)
    instruments = sorted(diag.get_list_of_instruments_in_multiple_prices())
    
    for code in instruments:
        print(f"Updating {code}...")
        try:
            update_multiple_adjusted_prices_for_instrument(code, data)
        except Exception as e:
            print(f"Failed for {code}: {e}")
```

### Final Validation
Verify the resulting output in `/home/samir/data/consolidated/`. You should see updated files across `futures_contract_prices`, `roll_calendars`, `futures_multiple_prices`, and `futures_adjusted_prices` with end dates reflecting your most recent `futures_20260310` downloads.
