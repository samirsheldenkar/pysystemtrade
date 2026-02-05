# Data Flow in pysystemtrade

Understanding how data flows through pysystemtrade is crucial for effective use of the framework. This document explains the data architecture, from raw price inputs to final trading decisions.

## Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Data Source │────▶│   Data Blob  │────▶│    System    │
│  (CSV/DB/IB) │     │ (Collection) │     │   (Stages)   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                   │
                           ┌───────────────────────┼───────────────────────┐
                           ▼                       ▼                       ▼
                    ┌──────────────┐      ┌──────────────┐      ┌──────────────┐
                    │   Forecast   │─────▶│   Position   │─────▶│    Orders    │
                    │   (Signals)  │      │   (Sizing)   │      │ (Execution)  │
                    └──────────────┘      └──────────────┘      └──────────────┘
```

## Data Hierarchy

### 1. Raw Data Level

**Individual Contract Prices** (`futuresContractPriceData`)
- OHLCV prices for specific futures contracts
- Identified by instrument code + contract date
- Stored in: CSV, MongoDB, Parquet, or Interactive Brokers

**Example**:
```python
# Individual contract
contract = futuresContract("SOFR", "202406")
prices = data.get_prices_for_contract_object(contract)
# Returns: OHLCV dataframe
```

### 2. Derived Data Level

**Multiple Prices** (`futuresMultiplePricesData`)
- Combines PRICE, CARRY, and FORWARD contracts
- Used for carry trading rules and adjusted price calculation

```python
# Multiple prices include:
# - PRICE: Current traded contract
# - CARRY: Contract used for carry calculation
# - FORWARD: Next contract to roll into
multiple_prices = data.get_multiple_prices("SOFR")
```

**Adjusted Prices** (`futuresAdjustedPricesData`)
- Continuous price series for backtesting
- Back-adjusted using Panama or other stitching methods
- Accounts for contract roll gaps

```python
# Back-adjusted continuous price
adj_price = data.get_adjusted_price("SOFR")
```

**Instrument Configuration** (`futuresInstrumentData`)
- Static instrument metadata
- Point sizes, currencies, asset classes
- Trading costs and restrictions

### 3. Simulation Data Level

**simData Objects** (`sysdata/sim/`)

Abstract interface providing:
- Adjusted prices
- Multiple prices  
- FX rates
- Instrument config

**Types**:
- `csvFuturesSimData`: Reads from CSV files
- `dbFuturesSimData`: Reads from database

```python
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData

data = csvFuturesSimData()
price = data.get_raw_price("SOFR")
carry = data.get_instrument_raw_carry_data("SOFR")
fx = data.get_fx_for_instrument("SOFR")
```

### 4. Production Data Level

**dataBlob** (`sysdata/data_blob.py`)

Container aggregating all data sources:
- Price data (Parquet/MongoDB)
- Contract data
- Position data
- Order data
- Capital data
- Broker connection

```python
from sysdata.data_blob import dataBlob

data = dataBlob()
# Access various data sources
prices = data.db_futures_contract_price_data
positions = data.db_contract_position_data
orders = data.db_strategy_position_data
```

## Data Transformations

### Price Data Transformation Pipeline

```
Individual Contract Prices
         │
         ▼
    Roll Calendar
         │
         ▼
   Multiple Prices
    (PRICE/CARRY/FORWARD)
         │
         ▼
   Adjusted Prices
  (Back-adjusted series)
         │
         ▼
   Trading Rules
```

### Trading Signal Flow

```
Adjusted Prices
      │
      ▼
Trading Rules
(Generate raw forecasts)
      │
      ▼
Forecast Scalars
(Normalize to target vol)
      │
      ▼
Forecast Cap
(Apply max/min limits)
      │
      ▼
Combined Forecast
(Weighted combination)
      │
      ▼
Position Sizing
(Volatility targeting)
      │
      ▼
Portfolio Construction
(Instrument weighting)
      │
      ▼
Final Positions
```

## Key Data Objects

### Futures Contract (`futuresContract`)

```python
from sysobjects.contracts import futuresContract

contract = futuresContract("SOFR", "202406")
print(contract.instrument_code)  # "SOFR"
print(contract.date_str)         # "202406"
```

### Futures Instrument (`futuresInstrument`)

```python
from sysobjects.instruments import futuresInstrument

instrument = futuresInstrument("SOFR")
meta_data = data.get_instrument_meta_data("SOFR")
print(meta_data.pointsize)      # 2500.0
print(meta_data.currency)       # "USD"
```

### Price Objects

**futuresContractPrices**:
```python
from sysobjects.futures_per_contract_prices import futuresContractPrices

# OHLCV data for a specific contract
contract_prices = futuresContractPrices(
    OPEN=open_series,
    HIGH=high_series,
    LOW=low_series,
    FINAL=close_series,
    VOLUME=volume_series
)
```

**futuresAdjustedPrices**:
```python
from sysobjects.adjusted_prices import futuresAdjustedPrices

# Continuous price series
adj_prices = futuresAdjustedPrices(price_series)
```

## Data Access Patterns

### Backtesting Data Access

```python
# Standard pattern in backtesting
data = csvFuturesSimData()

# Get instrument list
instruments = data.get_instrument_list()

# Get price data
for instrument in instruments:
    price = data.get_raw_price(instrument)
    carry_data = data.get_instrument_raw_carry_data(instrument)
```

### Production Data Access

```python
# Production uses dataBlob
data = dataBlob()

# Get current positions
positions = data.db_contract_position_data.get_all_current_positions()

# Get historical prices for backtest
prices = data.db_futures_adjusted_prices_data.get_adjusted_prices("SOFR")

# Get FX rates
fx = data.db_fx_prices_data.get_fx_prices("GBPUSD")
```

### Broker Data Access

```python
from sysbrokers.IB.ib_connection import connectionIB
from sysbrokers.IB.ib_futures_contract_price_data import ibFuturesContractPriceData

# Connect to broker
conn = connectionIB(1)

# Get live data
ib_prices = ibFuturesContractPriceData(conn, dataBlob())
contract = futuresContract("DAX", "202406")
prices = ib_prices.get_prices_for_contract_object(contract)
```

## Data Storage Backends

### CSV Storage

**Location**: `data/futures/`

```
data/futures/
├── adjusted_prices_csv/     # Back-adjusted prices
├── multiple_prices_csv/     # Multiple prices
├── roll_calendars_csv/      # Roll calendars
└── csvconfig/               # Configuration files
    ├── instrumentconfig.csv
    ├── rollconfig.csv
    └── spreadcosts.csv
```

**Usage**:
```python
from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData

csv_adj = csvFuturesAdjustedPricesData()
prices = csv_adj.get_adjusted_prices("SOFR")
```

### MongoDB Storage

**Collections**:
- `futures_adjusted_prices`
- `futures_multiple_prices`
- `futures_contract_prices`
- `futures_contracts`
- `futures_instruments`
- `futures_roll_calendars`
- `futures_roll_parameters`

**Usage**:
```python
from sysdata.mongodb.mongo_futures_adjusted_prices import mongoFuturesAdjustedPricesData

mongo_adj = mongoFuturesAdjustedPricesData()
prices = mongo_adj.get_adjusted_prices("SOFR")
```

### Parquet Storage

**Location**: Configurable (default: `data/parquet/`)

**Usage**:
```python
from sysdata.parquet.parquet_futures_adjusted_prices import parquetFuturesAdjustedPricesData

pq_adj = parquetFuturesAdjustedPricesData()
prices = pq_adj.get_adjusted_prices("SOFR")
```

## Data Initialization Workflow

For setting up a new system from scratch:

```python
# 1. Set up instrument configuration
from sysinit.futures.repocsv_spread_costs import *
init_spread_costs()

# 2. Seed individual contract prices
from sysinit.futures.seed_price_data_from_IB import *
seed_price_data_from_IB(instrument_code="SOFR")

# 3. Create roll calendars
from sysinit.futures.rollcalendars_from_db_prices_to_csv import *
build_and_write_roll_calendar("SOFR")

# 4. Create multiple prices
from sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db import *
process_multiple_prices_single_instrument("SOFR")

# 5. Create adjusted prices
from sysinit.futures.adjustedprices_from_db_multiple_to_db import *
process_adjusted_prices_single_instrument("SOFR")
```

## Data Caching

### System Cache

Each system maintains a cache to avoid redundant calculations:

```python
# Results are cached automatically
forecast1 = system.rules.get_capped_forecast("SOFR", "ewmac")
forecast2 = system.rules.get_capped_forecast("SOFR", "ewmac")  # Uses cache

# Clear cache if needed
system.cache.delete_all_items()

# Save cache
system.cache.pickle("my_cache.pck")

# Load cache
system.cache.unpickle("my_cache.pck")
```

### Data Object Caching

Data objects implement their own caching:

```python
# First call reads from disk/db
prices = data.get_adjusted_price("SOFR")

# Second call uses cached version
prices = data.get_adjusted_price("SOFR")
```

## Data Validation

### Checking Data Quality

```python
# Check for missing data
missing = data.missing_instruments()

# Check price data quality
from sysdata.tools.cleaner import *
check_price_data(data, "SOFR")
```

### Data Consistency Checks

```python
# Verify roll calendar
roll_calendar.check_if_date_index_monotonic()
roll_calendar.check_dates_are_valid_for_prices(prices)

# Verify multiple prices
multiple_prices.check_validity()
```

## Best Practices

1. **Data Source Abstraction**: Write code that works with any data source
2. **Caching**: Let the system handle caching; don't manually cache results
3. **Validation**: Always validate data before using in production
4. **Backup**: Regularly backup your data (especially MongoDB)
5. **Testing**: Use CSV data for testing, databases for production

## Troubleshooting

### Missing Data

```python
# Check what data is available
available = data.get_instrument_list()
missing = [i for i in required_instruments if i not in available]
```

### Data Gaps

```python
# Check for gaps in price data
prices = data.get_adjusted_price("SOFR")
gaps = prices[prices.diff() > pd.Timedelta(days=7)]
```

### Stale Data

```python
# Check data freshness
last_date = prices.index[-1]
if last_date < datetime.now() - timedelta(days=7):
    print("Data is stale!")
```

## Next Steps

- Learn about [Configuration](./configuration.md)
- Explore [Data Management](../data_management/data_overview.md) in detail
- Understand [Backtesting](../backtesting/backtesting_guide.md)
