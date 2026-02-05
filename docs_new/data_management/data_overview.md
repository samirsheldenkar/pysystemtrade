# Data Management Overview

This document provides an overview of data management in pysystemtrade, covering the types of data used, storage options, and the data flow pipeline.

## Data Types

pysystemtrade works with several types of data:

### 1. Price Data

**Individual Contract Prices**
- OHLCV (Open, High, Low, Close, Volume) for specific futures contracts
- Identified by instrument code + contract date (e.g., "SOFR_202406")
- Source of truth for all other price data

**Multiple Prices**
- Combines PRICE, CARRY, and FORWARD contracts in one series
- Used for carry trading rules and creating adjusted prices
- Structure: DataFrame with PRICE, CARRY, PRICE_CONTRACT, CARRY_CONTRACT columns

**Adjusted Prices**
- Continuous price series for backtesting
- Back-adjusted to remove roll gaps
- Created by stitching together individual contracts using roll calendars

### 2. Instrument Data

**Instrument Configuration**
- Static metadata: point size, currency, asset class
- Trading costs: spread costs, slippage estimates
- Roll parameters: roll cycles, offsets, carry offsets

**Contract Specifications**
- Specific contract details
- Expiry dates
- Trading hours

### 3. Supporting Data

**FX Rates**
- Spot FX prices for currency conversion
- Used for calculating position sizes in base currency

**Roll Calendars**
- Schedule of when to roll between contracts
- Defines current, next, and carry contracts over time

## Data Storage Options

pysystemtrade supports multiple storage backends:

### CSV Files

**Best for**: Development, testing, small-scale backtesting

**Location**: `data/futures/`

```
data/futures/
├── adjusted_prices_csv/      # Back-adjusted prices
├── multiple_prices_csv/      # Multiple prices  
├── roll_calendars_csv/       # Roll calendars
└── csvconfig/                # Configuration
    ├── instrumentconfig.csv
    ├── rollconfig.csv
    └── spreadcosts.csv
```

**Pros**:
- Simple, human-readable
- Version control friendly
- No database setup required

**Cons**:
- Slower for large datasets
- No concurrent access
- Manual updates required

### MongoDB

**Best for**: Production, concurrent access, large datasets

**Collections**:
- `futures_adjusted_prices`
- `futures_multiple_prices`
- `futures_contract_prices`
- `futures_contracts`
- `futures_instruments`
- `futures_roll_calendars`
- `futures_roll_parameters`
- `fx_prices`

**Pros**:
- Fast queries
- Concurrent access
- Scalable
- Production-tested

**Cons**:
- Requires MongoDB installation
- More complex setup

### Parquet

**Best for**: Large time series, analytical workloads

**Location**: Configurable (default: `data/parquet/`)

**Pros**:
- Very fast columnar storage
- Efficient compression
- Good for large datasets
- Compatible with pandas

**Cons**:
- Not human-readable
- Less flexible than MongoDB

### Interactive Brokers

**Best for**: Real-time data, production trading

**Usage**:
- Real-time price feeds
- Historical data backfill
- Live trading data

**Pros**:
- Real-time data
- Direct market access
- Integrated with trading

**Cons**:
- API limitations (rate limits, history limits)
- Requires IB account

## Data Flow Pipeline

```
┌──────────────────┐
│ Individual       │
│ Contract Prices  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Roll Calendar    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Multiple Prices  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Adjusted Prices  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Trading System   │
└──────────────────┘
```

### Step 1: Individual Contract Prices

Source data - OHLCV for each futures contract.

**Sources**:
- Interactive Brokers API
- Barchart CSV downloads
- Norgate Data
- Manual CSV imports

**Storage**: MongoDB or Parquet (production), CSV (development)

### Step 2: Roll Calendar

Defines when to switch between contracts.

**Generation**:
```python
from sysinit.futures.rollcalendars_from_db_prices_to_csv import build_and_write_roll_calendar

build_and_write_roll_calendar(
    instrument_code="SOFR",
    output_datapath="data/futures/roll_calendars_csv"
)
```

**Components**:
- `current_contract`: Currently trading contract
- `next_contract`: Contract to roll into
- `carry_contract`: Contract for carry calculation

### Step 3: Multiple Prices

Stitches contracts together without adjustment.

**Creation**:
```python
from sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db import process_multiple_prices_single_instrument

process_multiple_prices_single_instrument("SOFR")
```

**Structure**:
```
DATE_TIME    PRICE    CARRY    PRICE_CONTRACT    CARRY_CONTRACT
2020-01-01   98.5     98.6     20200300          20200600
2020-01-02   98.6     98.7     20200300          20200600
...
2020-03-15   98.7     98.8     20200600          20200900  # Roll occurred
```

### Step 4: Adjusted Prices

Continuous series with roll gaps removed.

**Creation**:
```python
from sysinit.futures.adjustedprices_from_db_multiple_to_db import process_adjusted_prices_single_instrument

process_adjusted_prices_single_instrument("SOFR")
```

**Adjustment Methods**:
- **Panama**: Most common, adjusts historical prices
- **Pointwise**: Adjusts at roll points
- **None**: No adjustment (for spreads)

## Data Objects

### Core Data Classes

**Base Data** (`sysdata/base_data.py`)
```python
class baseData:
    """Base class for all data objects"""
    def __init__(self, log="sysdata.base_data")
    
    def keys(self):
        """Return list of available items"""
    
    def __getitem__(self, key):
        """Get item by key"""
```

**Futures Contract Price Data** (`sysdata/futures/futures_per_contract_prices.py`)
```python
class futuresContractPriceData(baseData):
    """OHLCV prices for individual contracts"""
    
    def get_prices_for_contract_object(self, contract):
        """Get prices for a specific contract"""
    
    def get_merged_prices_for_instrument(self, instrument_code):
        """Get all contracts for an instrument"""
```

**Futures Adjusted Prices Data** (`sysdata/futures/futures_adjusted_prices.py`)
```python
class futuresAdjustedPricesData(baseData):
    """Back-adjusted continuous prices"""
    
    def get_adjusted_prices(self, instrument_code):
        """Get adjusted prices for instrument"""
```

**Futures Multiple Prices Data** (`sysdata/futures/futures_multiple_prices.py`)
```python
class futuresMultiplePricesData(baseData):
    """Multiple price series (price, carry, forward)"""
    
    def get_multiple_prices(self, instrument_code):
        """Get multiple prices for instrument"""
```

## Data Access Patterns

### Simulation Data

```python
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from sysdata.sim.db_futures_sim_data import dbFuturesSimData

# CSV data (for backtesting)
data = csvFuturesSimData()

# Database data (for production-like backtesting)
data = dbFuturesSimData()

# Access methods
prices = data.get_raw_price("SOFR")
carry = data.get_instrument_raw_carry_data("SOFR")
fx = data.get_fx_for_instrument("SOFR")
instruments = data.get_instrument_list()
```

### Production Data

```python
from sysdata.data_blob import dataBlob

data = dataBlob()

# Price data
adj_prices = data.db_futures_adjusted_prices_data.get_adjusted_prices("SOFR")

# Position data
positions = data.db_contract_position_data.get_all_current_positions()

# Order data
orders = data.db_strategy_position_data.get_current_position_for_strategy("my_strategy")

# FX data
fx = data.db_fx_prices_data.get_fx_prices("GBPUSD")
```

### Broker Data

```python
from sysbrokers.IB.ib_connection import connectionIB
from sysbrokers.IB.ib_futures_contract_price_data import ibFuturesContractPriceData

conn = connectionIB(1)
ib_data = ibFuturesContractPriceData(conn, dataBlob())

# Get live prices
contract = futuresContract("SOFR", "202406")
prices = ib_data.get_prices_for_contract_object(contract)
```

## Data Initialization Workflow

### Complete Setup from Scratch

```python
# 1. Copy instrument configuration
from sysinit.futures.repocsv_spread_costs import init_spread_costs
init_spread_costs()

# 2. Seed individual contract prices from IB
from sysinit.futures.seed_price_data_from_IB import seed_price_data_from_IB
seed_price_data_from_IB(instrument_code="SOFR")

# 3. Create roll calendar
from sysinit.futures.rollcalendars_from_db_prices_to_csv import build_and_write_roll_calendar
build_and_write_roll_calendar("SOFR")

# 4. Create multiple prices
from sysinit.futures.multipleprices_from_db_prices_and_csv_calendars_to_db import process_multiple_prices_single_instrument
process_multiple_prices_single_instrument("SOFR")

# 5. Create adjusted prices
from sysinit.futures.adjustedprices_from_db_multiple_to_db import process_adjusted_prices_single_instrument
process_adjusted_prices_single_instrument("SOFR")

# 6. Initialize FX data
from sysinit.futures.repocsv_spotfx_prices import init_spotfx_prices
init_spotfx_prices()
```

### Updating Existing Data

```python
# Update contract prices from IB
from sysproduction.update_historical_prices import update_historical_prices
update_historical_prices()

# Update multiple and adjusted prices
from sysproduction.update_multiple_adjusted_prices import update_multiple_and_adjusted_prices
update_multiple_and_adjusted_prices()

# Update FX prices
from sysproduction.update_fx_prices import update_fx_prices
update_fx_prices()
```

## Data Backup and Recovery

### MongoDB Backup

```bash
# Create dump
mongodump --db production --out /backup/mongodb/$(date +%Y%m%d)

# Restore
mongorestore --db production /backup/mongodb/20240101/production
```

### CSV Backup

```python
from sysproduction.backup_db_to_csv import backup_db_to_csv
backup_db_to_csv()
```

### Parquet Backup

```python
from sysproduction.backup_parquet_data_to_remote import backup_parquet_data
backup_parquet_data()
```

## Data Quality

### Validation Checks

```python
# Check for missing data
from sysdata.tools.cleaner import check_for_missing_data
missing = check_for_missing_data(data, instrument_code="SOFR")

# Check for gaps
from sysdata.tools.cleaner import check_for_gaps
gaps = check_for_gaps(data, instrument_code="SOFR")

# Check roll calendar
from sysobjects.roll_calendars import rollCalendar
calendar = rollCalendar.create_from_prices(prices, roll_params)
calendar.check_if_date_index_monotonic()
calendar.check_dates_are_valid_for_prices(prices)
```

### Common Issues

**Issue**: Missing contract prices
- **Solution**: Run `seed_price_data_from_IB` or import from CSV

**Issue**: Gaps in adjusted prices
- **Solution**: Check roll calendar and multiple prices

**Issue**: Stale data
- **Solution**: Set up automated daily updates

**Issue**: Incorrect roll dates
- **Solution**: Manually edit roll calendar CSV

## Best Practices

1. **Use Database for Production**: MongoDB or Parquet for production systems
2. **Use CSV for Development**: Easier to inspect and modify
3. **Backup Regularly**: Automated daily backups
4. **Validate Data**: Check data quality before trading
5. **Version Control Config**: Keep instrument/roll configs in git
6. **Monitor Staleness**: Alert if data is outdated
7. **Test with Subset**: Use few instruments when testing

## Next Steps

- Learn about [Futures Data](./futures_data.md) in detail
- Understand [FX Data](./fx_data.md) management
- Explore [Data Sources](./data_sources.md) and import methods
