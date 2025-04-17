# System Initialization (sysinit) Documentation

This document provides a comprehensive overview of the scripts in the `sysinit` folder, which are essential for setting up and maintaining a production trading system.

## Directory Structure

The `sysinit` folder contains three main subdirectories:
- `transfer/`: Data transfer and backup utilities
- `futures/`: Futures market data management and roll calendar tools
- `configtools/`: Configuration management utilities

## Transfer Utilities (`transfer/`)

### `backup_arctic_to_parquet.py`
- **Purpose**: Creates backup copies of Arctic database data in Parquet format
- **Usage**: Used for data backup and migration purposes
- **Key Features**:
  - Converts Arctic database data to Parquet format
  - Supports incremental backups
  - Maintains data integrity during transfer

### `positions_from_timed_storage_to_arctic.py`
- **Purpose**: Transfers position data from timed storage to Arctic database
- **Usage**: Used during system migration or data consolidation
- **Key Features**:
  - Handles position data transfer
  - Maintains data consistency
  - Supports bulk data operations

## Futures Market Data Management (`futures/`)

### Core Data Management Scripts

#### `build_roll_calendars.py`
- **Purpose**: Generates and manages futures roll calendars
- **Usage**: Essential for futures contract roll management
- **Key Features**:
  - Creates approximate roll calendars based on price data
  - Adjusts calendars to actual price series
  - Handles carry contract management
  - Supports back-calculation from multiple prices

#### `build_multiple_prices_from_raw_data.py`
- **Purpose**: Constructs multiple price series from raw futures contract data
- **Usage**: Creates continuous futures price series
- **Key Features**:
  - Generates price, forward, and carry price series
  - Handles roll calendar integration
  - Manages contract transitions
  - Supports price interpolation and adjustment

#### `contract_prices_from_csv_to_db.py`
- **Purpose**: Imports contract prices from CSV files to database
- **Usage**: Initial data loading and updates
- **Key Features**:
  - CSV to database conversion
  - Data validation
  - Error handling

#### `adjustedprices_from_db_multiple_to_db.py`
- **Purpose**: Generates adjusted price series from multiple prices
- **Usage**: Creates continuous price series for analysis
- **Key Features**:
  - Price adjustment calculations
  - Database integration
  - Data consistency checks

### Data Import and Export Scripts

#### `seed_price_data_from_IB.py`
- **Purpose**: Imports price data from Interactive Brokers
- **Usage**: Initial data seeding and updates
- **Key Features**:
  - IB API integration
  - Historical data retrieval
  - Data formatting

#### `spotfx_from_csvAndInvestingDotCom_to_db.py`
- **Purpose**: Imports spot FX rates from Investing.com to database
- **Usage**: FX data management
- **Key Features**:
  - Web scraping integration
  - Data validation
  - Database storage

### Roll Management Scripts

#### `safely_modify_roll_parameters.py`
- **Purpose**: Safely updates roll parameters for futures contracts
- **Usage**: Roll parameter maintenance
- **Key Features**:
  - Parameter validation
  - Safe update procedures
  - Backup and rollback capabilities

#### `rollcalendars_from_db_prices_to_csv.py`
- **Purpose**: Exports roll calendars from database to CSV
- **Usage**: Roll calendar backup and analysis
- **Key Features**:
  - Database to CSV conversion
  - Data formatting
  - Export customization

### Utility Scripts

#### `check_instrument_lists.py`
- **Purpose**: Validates instrument lists and configurations
- **Usage**: System health checks
- **Key Features**:
  - Configuration validation
  - Error detection
  - Reporting

#### `create_hourly_and_daily.py`
- **Purpose**: Generates hourly and daily price series
- **Usage**: Timeframe conversion
- **Key Features**:
  - Timeframe aggregation
  - Data consistency checks
  - Multiple timeframe support

## Configuration Tools (`configtools/`)

### `csvweights_to_yaml.py`
- **Purpose**: Converts CSV weight files to YAML configuration
- **Usage**: Portfolio configuration management
- **Key Features**:
  - CSV to YAML conversion
  - Configuration validation
  - Format standardization

## Usage in Production Trading System

### Initial Setup
1. Use `seed_price_data_from_IB.py` to populate initial price data
2. Configure roll parameters using `safely_modify_roll_parameters.py`
3. Generate roll calendars with `build_roll_calendars.py`
4. Create multiple price series using `build_multiple_prices_from_raw_data.py`

### Regular Maintenance
1. Update price data using appropriate import scripts
2. Review and adjust roll parameters as needed
3. Generate new roll calendars when contracts change
4. Backup data using `backup_arctic_to_parquet.py`

### Data Management
1. Use transfer scripts for data migration
2. Validate instrument lists regularly
3. Maintain configuration files
4. Monitor data quality and consistency

## Best Practices
1. Always backup data before major operations
2. Validate configurations before applying changes
3. Monitor roll calendar generation for accuracy
4. Maintain consistent data formats across the system
5. Regular system health checks using validation scripts 