# Private Configuration Documentation

This document provides detailed documentation for each section of the `private_config.yaml` file, which is used to configure a production trading system.

## Production Configuration

### Strategy Configuration
```yaml
strategy_list:
  example:
    load_backtests:
      object: sysproduction.strategy_code.run_system_classic.runSystemClassic
      function: system_method
    reporting_code:
      function: sysproduction.strategy_code.report_system_classic.report_system_classic
```
- **Purpose**: Defines the strategies to be run in production
- **Parameters**:
  - `load_backtests`: Specifies the class and method for loading backtest data
  - `reporting_code`: Defines the reporting function for the strategy

### Strategy Capital Allocation
```yaml
strategy_capital_allocation:
  function: sysproduction.strategy_code.strategy_allocation.weighted_strategy_allocation
  strategy_weights:
    example: 100.0
```
- **Purpose**: Allocates capital across different strategies
- **Parameters**:
  - `function`: The allocation method to use
  - `strategy_weights`: Weights for each strategy (must sum to 100)

### Storage Directories
```yaml
backtest_store_directory: 'private.backtests'
csv_backup_directory: 'data.backups_csv'
mongo_dump_directory: 'data.mongo_dump'
echo_directory: 'data.echos'
```
- **Purpose**: Defines storage locations for various system components
- **Parameters**:
  - `backtest_store_directory`: Location for backtest data
  - `csv_backup_directory`: Location for CSV backups
  - `mongo_dump_directory`: Location for MongoDB dumps
  - `echo_directory`: Location for echo files

### Interactive Brokers Configuration
```yaml
ib_ipaddress: 127.0.0.1
ib_port: 4001
ib_idoffset: 100
broker_factory_func: 'sysbrokers.broker_factory.get_ib_class_list'
```
- **Purpose**: Configures connection to Interactive Brokers
- **Parameters**:
  - `ib_ipaddress`: IB Gateway/TWS IP address
  - `ib_port`: Connection port
  - `ib_idoffset`: ID offset for order management
  - `broker_factory_func`: Function to get broker class list

### Database Configuration
```yaml
mongo_host: 127.0.0.1
mongo_db: 'production'
mongo_port: 27017
parquet_store: '/home/samir/data/parquet'
```
- **Purpose**: Configures database connections and storage
- **Parameters**:
  - `mongo_host`: MongoDB host address
  - `mongo_db`: Database name
  - `mongo_port`: MongoDB port (DO NOT CHANGE from 27017)
  - `parquet_store`: Location for Parquet file storage

### Price Filtering Configuration
```yaml
max_price_spike: 8.0
GMT_offset_hours: 0
ignore_future_prices: True
ignore_prices_with_zero_volumes_intraday: True
ignore_prices_with_zero_volumes_daily: False
ignore_zero_prices: True
ignore_negative_prices: False
```
- **Purpose**: Controls how price data is filtered and processed
- **Parameters**:
  - `max_price_spike`: Maximum allowed price spike (in standard deviations)
  - `GMT_offset_hours`: Timezone offset from GMT
  - Various ignore flags for different price conditions

### Roll Status Configuration
```yaml
roll_status_auto_update:
  auto_roll_if_relative_volume_higher_than: 1.0
  min_relative_volume: 0.01
  min_absolute_volume: 100
  near_expiry_days: 10
  default_roll_state_if_undecided: Ask
  auto_roll_expired: True
```
- **Purpose**: Controls automatic roll management
- **Parameters**:
  - `auto_roll_if_relative_volume_higher_than`: Volume threshold for auto-roll
  - `min_relative_volume`: Minimum relative volume requirement
  - `min_absolute_volume`: Minimum absolute volume requirement
  - `near_expiry_days`: Days before expiry to consider for rolling
  - `default_roll_state_if_undecided`: Default action when roll state is unclear
  - `auto_roll_expired`: Whether to automatically roll expired contracts

### Execution Algorithm Configuration
```yaml
execution_algos:
  default_algo: sysexecution.algos.algo_original_best.algoOriginalBest
  market_algo: sysexecution.algos.algo_snaps.algoSnapMkt
  limit_order_algo: sysexecution.algos.algo_limit_orders.algoLimit
  best_algo: sysexecution.algos.algo_original_best.algoOriginalBest
  algo_overrides:
    some_market_name_eg_IRON: sysexecution.algos.algo_market.algoMarket
```
- **Purpose**: Defines execution algorithms for different order types
- **Parameters**:
  - Various algorithm classes for different execution scenarios
  - `algo_overrides`: Market-specific algorithm overrides

## Backtesting Configuration

### Volatility Calculation
```yaml
volatility_calculation:
  func: "sysquant.estimators.vol.mixed_vol_calc"
  name_returns_attr_in_rawdata: "daily_returns"
  multiplier_to_get_daily_vol: 1.0
  days: 35
  min_periods: 10
  slow_vol_years: 10
  proportion_of_slow_vol: 0.3
  vol_abs_min: 0.0000000001
```
- **Purpose**: Configures volatility calculation parameters
- **Parameters**:
  - `func`: Volatility calculation function
  - `days`: Lookback period for volatility
  - `min_periods`: Minimum periods required for calculation
  - Various other parameters for mixed volatility calculation

### Forecast Configuration
```yaml
forecast_scalar: 1.0
forecast_cap: 20.0
average_absolute_forecast: 10.0
forecast_div_multiplier: 1.0
```
- **Purpose**: Controls forecast scaling and capping
- **Parameters**:
  - `forecast_scalar`: Global forecast scaling factor
  - `forecast_cap`: Maximum allowed forecast value
  - `average_absolute_forecast`: Target average absolute forecast
  - `forecast_div_multiplier`: Diversification multiplier for forecasts

### Capital Configuration
```yaml
percentage_vol_target: 16.0
notional_trading_capital: 1000000
base_currency: "GBP"
capital_multiplier:
   func: syscore.capital.fixed_capital
```
- **Purpose**: Defines capital allocation and risk parameters
- **Parameters**:
  - `percentage_vol_target`: Target annualized volatility
  - `notional_trading_capital`: Base trading capital
  - `base_currency`: System's base currency
  - `capital_multiplier`: Function for capital calculation

### Portfolio Configuration
```yaml
instrument_div_multiplier: 1.0
buffer_method: forecast
buffer_size: 0.10
buffer_trade_to_edge: True
```
- **Purpose**: Controls portfolio construction and position management
- **Parameters**:
  - `instrument_div_multiplier`: Diversification multiplier for instruments
  - `buffer_method`: Method for position buffering
  - `buffer_size`: Size of position buffer
  - `buffer_trade_to_edge`: Whether to trade to buffer edge

### Instrument Management
```yaml
duplicate_instruments:
  include:
    things: 'thing_we_want'
  exclude:
    things: ['bad_thing', 'Another_thing']
exclude_instrument_lists:
  ignore_instruments:
    - 'NIFTY'
    - 'USIRS2'
  trading_restrictions:
    - RESTRICTED_EXAMPLE
  bad_markets:
    - BAD_EXAMPLE
```
- **Purpose**: Manages instrument inclusion/exclusion and restrictions
- **Parameters**:
  - `duplicate_instruments`: Handles duplicate instrument selection
  - `ignore_instruments`: Instruments to ignore in backtests
  - `trading_restrictions`: Instruments with trading restrictions
  - `bad_markets`: Markets considered too expensive or illiquid

## Best Practices
1. Always maintain a backup of your private_config.yaml
2. Test configuration changes in a development environment first
3. Document any custom changes made to the configuration
4. Regularly review and update instrument lists and restrictions
5. Monitor system performance after configuration changes
6. Keep sensitive information (like API keys) in separate secure files 