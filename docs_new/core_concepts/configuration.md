# Configuration System

pysystemtrade uses a hierarchical configuration system that allows flexible customization at multiple levels. This document explains how configuration works and how to use it effectively.

## Configuration Hierarchy

Configuration is resolved in this priority order (later overrides earlier):

```
1. Project Defaults
   ↓
2. Private Configuration
   ↓
3. System Configuration  
   ↓
4. Runtime Configuration
```

### 1. Project Defaults

**File**: `sysdata/config/defaults.yaml`

Contains default values for all configuration parameters. These are the fallback values if nothing else is specified.

**Key sections**:
- Trading rules configuration
- Forecast scaling parameters
- Position sizing parameters
- Portfolio construction settings
- Cost assumptions
- Logging configuration

### 2. Private Configuration

**File**: `private/private_config.yaml`

User-specific settings that apply across all systems:

```yaml
# Database connections
mongo_host: localhost
mongo_db: production
parquet_store: /home/user/data/parquet

# Interactive Brokers
ib_ipaddress: 127.0.0.1
ib_port: 4001
broker_account: U123456

# Email notifications
email_address: user@example.com
smtp_server: smtp.gmail.com

# Trading parameters
percentage_vol_target: 25.0
notional_trading_capital: 500000
base_currency: USD
```

### 3. System Configuration

**Location**: `private/your_system/config.yaml`

System-specific configuration for a particular trading strategy:

```yaml
# Instruments to trade
instruments:
  - SOFR
  - US10
  - CORN
  - SP500_micro

# Trading rules
trading_rules:
  ewmac_fast:
    function: systems.provided.rules.ewmac.ewmac_forecast_with_defaults
    other_args:
      Lfast: 8
      Lslow: 32
  ewmac_slow:
    function: systems.provided.rules.ewmac.ewmac_forecast_with_defaults
    other_args:
      Lfast: 32
      Lslow: 128

# Forecast scalars
forecast_scalars:
  ewmac_fast: 5.3
  ewmac_slow: 2.65

# Forecast weights
forecast_weights:
  ewmac_fast: 0.5
  ewmac_slow: 0.5

# Portfolio parameters
instrument_weights:
  SOFR: 0.4
  US10: 0.3
  CORN: 0.2
  SP500_micro: 0.1

instrument_div_multiplier: 1.5
```

### 4. Runtime Configuration

Pass configuration directly when creating a system:

```python
from sysdata.config.configdata import Config

config_dict = {
    'instruments': ['SOFR', 'US10'],
    'percentage_vol_target': 20.0,
    'forecast_scalars': {'ewmac': 2.65}
}

config = Config(config_dict)
system = futures_system(config=config)
```

## Creating Configuration Objects

### From YAML File

```python
from sysdata.config.configdata import Config

# Absolute path
config = Config("/path/to/config.yaml")

# Relative to project (using dot notation)
config = Config("private.my_system.config")
```

### From Dictionary

```python
config_dict = {
    'instruments': ['SOFR', 'US10'],
    'percentage_vol_target': 25.0
}

config = Config(config_dict)
```

### Modifying Configuration

```python
# Modify existing config
config.instruments = ['SOFR', 'US10', 'CORN']
config.forecast_scalars = {'ewmac': 2.65}

# Access values
print(config.instruments)
print(config.get_element('percentage_vol_target'))
```

## Key Configuration Parameters

### Risk and Capital

```yaml
# Annual volatility target (percentage)
percentage_vol_target: 25.0

# Trading capital in base currency
notional_trading_capital: 500000

# Base currency for calculations
base_currency: "GBP"

# Capital multiplier (for leverage)
capital_multiplier: 1.0
```

### Trading Rules

```yaml
# Define trading rules
trading_rules:
  ewmac_fast:
    function: systems.provided.rules.ewmac.ewmac_forecast_with_defaults
    data: 
      - data.daily_prices
    other_args:
      Lfast: 8
      Lslow: 32
```

Or using fixed rules dictionary:
```python
from systems.trading_rules import TradingRule

ewmac_8 = TradingRule(
    (ewmac_forecast_with_defaults, [], dict(Lfast=8, Lslow=32))
)

config.trading_rules = dict(ewmac8=ewmac_8)
```

### Forecast Configuration

```yaml
# Forecast scalars (for fixed scaling)
forecast_scalars:
  ewmac_fast: 5.3
  ewmac_slow: 2.65

# Forecast weights
forecast_weights:
  ewmac_fast: 0.5
  ewmac_slow: 0.5

# Forecast diversification multiplier
forecast_div_multiplier: 1.1

# Forecast cap (max absolute forecast)
forecast_cap: 20.0

# Average absolute forecast target
average_absolute_forecast: 10.0
```

### Estimation Configuration

```yaml
# Use estimated forecast scalars
use_forecast_scale_estimates: true

# Parameters for forecast scalar estimation
forecast_scalar_estimate:
  pool_instruments: true
  min_periods: 20
  ewma_span: 500

# Use estimated forecast weights
use_forecast_weight_estimates: true

# Parameters for forecast weight estimation
forecast_weight_estimate:
  method: "bootstrap"  # or "shrinkage", "one_period"
  date_method: "rolling"
  rollyears: 10
  monte_carlo_runs: 100
```

### Portfolio Configuration

```yaml
# Instrument weights
instrument_weights:
  SOFR: 0.4
  US10: 0.3
  CORN: 0.2
  SP500_micro: 0.1

# Instrument diversification multiplier
instrument_div_multiplier: 1.5

# Use estimated instrument weights
use_instrument_weight_estimates: true

# Parameters for instrument weight estimation
instrument_weight_estimate:
  method: "handcraft"
  date_method: "rolling"
  rollyears: 20
```

### Cost Configuration

```yaml
# Cost calculation
spread_costs:
  SOFR: 0.0025
  US10: 0.005

# Cost multiplier for conservative estimation
cost_multiplier: 1.0

# Cost ceiling (max cost in SR units)
cost_ceiling: 0.01
```

### Instrument Selection

```yaml
# Always exclude these instruments
exclude_instrument_lists:
  ignore_instruments:
    - EURIBOR
  trading_restrictions:
    - US-DISCRETE
    - US-ENERGY
  bad_markets:
    - ALUMINIUM
    - V2X

# Duplicate instrument handling
duplicate_instruments:
  include:
    sp500: SP500_micro
    nasdaq: NASDAQ_micro
  exclude:
    sp500: SP500
    nasdaq: NASDAQ
```

## Configuration in Practice

### Complete Example

```python
from sysdata.config.configdata import Config
from systems.provided.futures_chapter15.basesystem import futures_system

# Create configuration
config = Config({
    'instruments': ['SOFR', 'US10', 'CORN'],
    'percentage_vol_target': 25.0,
    'notional_trading_capital': 500000,
    'base_currency': 'USD',
    
    'forecast_scalars': {
        'ewmac_fast': 5.3,
        'ewmac_slow': 2.65
    },
    
    'forecast_weights': {
        'ewmac_fast': 0.5,
        'ewmac_slow': 0.5
    },
    
    'instrument_weights': {
        'SOFR': 0.5,
        'US10': 0.3,
        'CORN': 0.2
    },
    
    'use_forecast_scale_estimates': False,
    'use_forecast_weight_estimates': False,
    'use_instrument_weight_estimates': False
})

# Create system with custom config
system = futures_system(config=config)

# Run backtest
profits = system.accounts.portfolio()
print(profits.percent.stats())
```

### Changing Configuration After System Creation

```python
# Create system
system = futures_system()

# Change configuration (requires cache clear)
system.cache.delete_all_items()
system.config.percentage_vol_target = 20.0

# Re-run
profits = system.accounts.portfolio()
```

### Saving Configuration

```python
# Save to YAML
system.config.save("my_system_config.yaml")

# Or use private directory
system.config.save("private.my_system.config")
```

## Production Configuration

### Control Configuration

**File**: `private/private_control_config.yaml`

Controls production system behavior:

```yaml
# Process control
process_configuration:
  run_daily_prices:
    run_mode: "auto"
    max_executions: 1
  
  run_strategy_order_generator:
    run_mode: "auto"
    max_executions: 5

# Trade limits
trade_limits:
  SOFR:
    max_trades_per_day: 10
    max_positions_per_day: 1

# Position limits
position_limits:
  SOFR:
    max_position: 100
    min_position: -100
```

### Process-Specific Configuration

Each production process can have its own configuration section in `control_config.yaml`:

```yaml
# In syscontrol/control_config.yaml or private/private_control_config.yaml
process_configuration:
  run_daily_price_updates:
    run_mode: "auto"
    start_time: "00:01"
    end_time: "23:59"
    frequency: "Daily"
  
  run_systems:
    run_mode: "auto"
    start_time: "06:00"
    end_time: "08:00"
```

## Configuration Validation

### Checking Configuration

```python
# List all configuration elements
print(config)

# Check if element exists
if hasattr(config, 'percentage_vol_target'):
    print(f"Vol target: {config.percentage_vol_target}")

# Get with default
vol_target = config.get_element_or_default('percentage_vol_target', 25.0)
```

### Common Configuration Errors

1. **Missing instruments list**: When using estimation, must explicitly define `instruments`
2. **Inconsistent weights**: Weights should sum to 1.0 (though system will normalize)
3. **Missing scalars**: If `use_forecast_scale_estimates: False`, must provide `forecast_scalars`

## Best Practices

1. **Use Private Config for Secrets**: API keys, account numbers in `private_config.yaml`
2. **System Config for Strategy**: Trading parameters in system-specific config
3. **Version Control**: Commit template configs, keep private configs out of git
4. **Documentation**: Comment complex configuration sections
5. **Testing**: Test configs with small instrument sets first

## Configuration Templates

### Conservative System

```yaml
# Low volatility target
percentage_vol_target: 15.0

# High diversification
forecast_div_multiplier: 1.5
instrument_div_multiplier: 2.0

# Conservative costs
cost_multiplier: 1.5
```

### Aggressive System

```yaml
# High volatility target
percentage_vol_target: 35.0

# Lower diversification (more concentrated)
forecast_div_multiplier: 1.0
instrument_div_multiplier: 1.2

# Cost ceiling
cost_ceiling: 0.02
```

## Next Steps

- Learn about [Backtesting](../backtesting/backtesting_guide.md)
- Understand [Data Management](../data_management/data_overview.md)
- Explore [Production Setup](../production_trading/production_setup.md)
