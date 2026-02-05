# Systems Module API Reference

This document provides API reference documentation for the `systems` module.

## Core Classes

### System

**File**: `systems/basesystem.py`

The main system class that orchestrates all stages.

```python
class System:
    def __init__(
        self, 
        stage_list,           # List of SystemStage instances
        data=None,            # Data object (simData or dataBlob)
        config=None,          # Config object
        log=None              # Logger instance
    )
```

**Key Methods**:

```python
# Get list of instruments
system.get_instrument_list()

# Get trading rules
system.rules.trading_rules()

# Access stages
system.rules.get_raw_forecast(instrument_code, rule_name)
system.forecastScaleCap.get_capped_forecast(instrument_code, rule_name)
system.combForecast.get_combined_forecast(instrument_code)
system.positionSize.get_subsystem_position(instrument_code)
system.portfolio.get_notional_position(instrument_code)
system.accounts.portfolio()

# Cache management
system.cache.delete_all_items()
system.cache.pickle(filename)
system.cache.unpickle(filename)

# Diagnostics
system.get_list_of_methods()
```

**Example**:
```python
from systems.basesystem import System
from systems.forecasting import Rules
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData

data = csvFuturesSimData()
rules = Rules()
system = System([rules], data)

forecast = system.rules.get_raw_forecast("SOFR", "ewmac")
```

---

### SystemStage

**File**: `systems/stage.py`

Base class for all system stages.

```python
class SystemStage:
    @property
    def name(self):
        """Return stage name (must be overridden)"""
        return "stageName"
    
    def system_init(self, system):
        """Called when stage is added to system"""
        self.parent = system
```

**Accessing Parent System**:
```python
def some_method(self, instrument_code):
    # Access data
    data = self.parent.data
    
    # Access other stages
    forecasts = self.parent.rules.get_capped_forecast(instrument_code, "ewmac")
    
    # Access config
    config_value = self.parent.config.some_param
```

---

## Stage Classes

### Rules (Forecasting)

**File**: `systems/forecasting.py`

Generates trading signals (forecasts) from price data.

```python
class Rules(SystemStage):
    @property
    def name(self):
        return "rules"
```

**Key Methods**:

```python
# Get raw forecast for specific rule
get_raw_forecast(instrument_code, rule_variation_name)

# Get all forecasts for instrument
get_all_forecasts(instrument_code)

# Get trading rules dict
trading_rules()

# Get list of rule variations
get_trading_rule_list(instrument_code)

# Get forecast mapping (if configured)
get_forecast_mapping(rule_variation_name)
```

**Example**:
```python
from systems.forecasting import Rules
from systems.trading_rules import TradingRule
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

rule = TradingRule(ewmac_forecast_with_defaults)
rules = Rules({'ewmac': rule})

system = System([rules], data, config)
forecast = system.rules.get_raw_forecast("SOFR", "ewmac")
```

---

### ForecastScaleCap

**File**: `systems/forecast_scale_cap.py`

Scales and caps forecasts.

```python
class ForecastScaleCap(SystemStage):
    @property
    def name(self):
        return "forecastScaleCap"
```

**Key Methods**:

```python
# Get scaled forecast
get_scaled_forecast(instrument_code, rule_variation_name)

# Get capped forecast (most commonly used)
get_capped_forecast(instrument_code, rule_variation_name)

# Get forecast scalar (scaling factor)
get_forecast_scalar(instrument_code, rule_variation_name)

# Get cap and floor values
get_forecast_cap()
get_forecast_floor()

# Get average forecast target
get_average_forecast()
```

---

### ForecastCombine

**File**: `systems/forecast_combine.py`

Combines multiple forecasts into a single forecast per instrument.

```python
class ForecastCombine(SystemStage):
    @property
    def name(self):
        return "combForecast"
```

**Key Methods**:

```python
# Get combined forecast for instrument
get_combined_forecast(instrument_code)

# Get forecast weights
get_forecast_weights(instrument_code)

# Get forecast diversification multiplier
get_forecast_diversification_multiplier(instrument_code)

# Get raw forecasts for specific rules
get_forecasts_given_rule_list(instrument_code, rule_list)

# Get raw combined forecast before mapping
get_raw_combined_forecast_before_mapping(instrument_code)
```

---

### PositionSizing

**File**: `systems/positionsizing.py`

Calculates position sizes based on forecasts and volatility.

```python
class PositionSizing(SystemStage):
    @property
    def name(self):
        return "positionSize"
```

**Key Methods**:

```python
# Get subsystem position
get_subsystem_position(instrument_code)

# Get position buffers
get_subsystem_buffers(instrument_code)

# Get volatility scalar
get_volatility_scalar(instrument_code)

# Get FX rate for instrument
get_fx_rate(instrument_code)

# Get notional trading capital
get_notional_trading_capital()

# Get volatility target dict
get_vol_target_dict()

# Get daily cash volatility target
get_daily_cash_vol_target()

# Get block value (contract value)
get_block_value(instrument_code)

# Get underlying price
get_underlying_price(instrument_code)

# Get instrument volatility
get_instrument_volatility(instrument_code)
```

---

### Portfolios

**File**: `systems/portfolio.py`

Combines instruments into a portfolio.

```python
class Portfolios(SystemStage):
    @property
    def name(self):
        return "portfolio"
```

**Key Methods**:

```python
# Get notional position
get_notional_position(instrument_code)

# Get actual position (with buffers)
get_actual_position(instrument_code)

# Get instrument weights
get_instrument_weights()

# Get instrument diversification multiplier
get_instrument_diversification_multiplier()

# Get all positions
get_all_positions()

# Get buffers for position
get_buffers_for_position(instrument_code)

# Get capital multiplier
get_capital_multiplier()

# Get list of instruments for optimization
get_instrument_list(for_instrument_weights=False)
```

---

### Account

**File**: `systems/accounts/accounts_stage.py`

Calculates P&L and performance metrics.

```python
class Account(SystemStage):
    @property
    def name(self):
        return "accounts"
```

**Key Methods**:

```python
# Get portfolio P&L
portfolio()

# Get instrument P&L
pandl_for_instrument(instrument_code)

# Get forecast P&L
pandl_for_instrument_forecast(instrument_code, rule_variation_name)

# Get positions for instrument
get_actual_position(instrument_code)

# Get buffered positions
get_buffered_position(instrument_code)

# Get capital
get_capital()

# Get turnover
get_turnover(instrument_code)
```

---

### RawData

**File**: `systems/rawdata.py`

Provides preprocessed raw data.

```python
class RawData(SystemStage):
    @property
    def name(self):
        return "rawdata"
```

**Key Methods**:

```python
# Get daily prices
daily_prices(instrument_code)

# Get hourly prices (if available)
hourly_prices(instrument_code)

# Get instrument raw carry data
get_instrument_raw_carry_data(instrument_code)

# Get daily volatility
get_daily_volatility(instrument_code)

# Get percentage returns
get_percentage_returns(instrument_code)

# Get instrument currency
get_instrument_currency(instrument_code)

# Get point size
get_point_size(instrument_code)

# Get block value
get_block_value(instrument_code)

# Get spreads
get_spread(instrument_code)
```

---

## Trading Rules

### TradingRule

**File**: `systems/trading_rules.py`

Defines a trading rule.

```python
class TradingRule:
    def __init__(
        self,
        rule_function,           # Function that generates forecasts
        data=None,               # List of data input strings
        other_args=None,         # Dict of additional arguments
        name=None                # Optional name
    )
```

**Example**:
```python
from systems.trading_rules import TradingRule
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

# Simple rule
rule = TradingRule(ewmac_forecast_with_defaults)

# With parameters
rule = TradingRule(
    ewmac_forecast_with_defaults,
    other_args={'Lfast': 8, 'Lslow': 32}
)

# With data specification
rule = TradingRule(
    my_custom_rule,
    data=['data.daily_prices', 'data.get_instrument_raw_carry_data'],
    other_args={'param': 10}
)
```

---

## Provided Systems

### futures_system (Chapter 15)

**File**: `systems/provided/futures_chapter15/basesystem.py`

Pre-configured system from "Systematic Trading" Chapter 15.

```python
from systems.provided.futures_chapter15.basesystem import futures_system

# Default system
system = futures_system()

# With custom config
system = futures_system(config=my_config)

# With custom data
system = futures_system(data=my_data)

# Both
system = futures_system(config=my_config, data=my_data)
```

### Estimated System

**File**: `systems/provided/futures_chapter15/estimatedsystem.py`

System with estimated parameters.

```python
from systems.provided.futures_chapter15.estimatedsystem import futures_system

system = futures_system()  # Estimates scalars, weights, multipliers
```

---

## Configuration

### Config

**File**: `sysdata/config/configdata.py`

Configuration object for systems.

```python
from sysdata.config.configdata import Config

# From dict
config = Config({'instruments': ['SOFR', 'US10']})

# From YAML file
config = Config("private.my_system.config")

# From module path
config = Config("systems.provided.futures_chapter15.futuresconfig")

# Access values
instruments = config.instruments
vol_target = config.percentage_vol_target

# Modify
config.instruments = ['SOFR', 'CORN']

# Save
config.save("my_config.yaml")
```

---

## Caching

### SystemCache

**File**: `systems/system_cache.py`

Caches intermediate results for performance.

```python
# Access cache
cache = system.cache

# Delete all items
cache.delete_all_items()

# Delete items for specific instrument
cache.delete_items_for_instrument("SOFR")

# Save to disk
cache.pickle("cache_file.pck")

# Load from disk
cache.unpickle("cache_file.pck")

# Get cache item (internal use)
cache.get_item(cache_key)

# Set cache item (internal use)
cache.set_item(cache_key, value)
```

---

## Decorators

### Diagnostic Decorators

**File**: `systems/system_cache.py`

```python
from systems.system_cache import diagnostic, dont_cache

class MyStage(SystemStage):
    @diagnostic
    def my_method(self, instrument_code):
        """Result will be cached"""
        return expensive_calculation()
    
    @dont_cache
    def my_volatile_method(self, instrument_code):
        """Result won't be cached"""
        return volatile_calculation()
```

---

## Examples

### Complete System Setup

```python
from systems.basesystem import System
from systems.forecasting import Rules
from systems.forecast_scale_cap import ForecastScaleCap
from systems.forecast_combine import ForecastCombine
from systems.positionsizing import PositionSizing
from systems.rawdata import RawData
from systems.portfolio import Portfolios
from systems.accounts.accounts_stage import Account
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from sysdata.config.configdata import Config

# Data
data = csvFuturesSimData()

# Config
config = Config({
    'instruments': ['SOFR', 'US10'],
    'percentage_vol_target': 25.0,
    'notional_trading_capital': 500000,
    'forecast_scalars': {'ewmac': 2.65},
    'forecast_weights': {'ewmac': 1.0},
    'instrument_weights': {'SOFR': 0.6, 'US10': 0.4}
})

# Stages
stages = [
    Rules(),
    ForecastScaleCap(),
    ForecastCombine(),
    RawData(),
    PositionSizing(),
    Portfolios(),
    Account()
]

# System
system = System(stages, data, config)

# Use
profits = system.accounts.portfolio()
print(profits.percent.stats())
```

### Custom Stage

```python
from systems.stage import SystemStage

class RiskOverlay(SystemStage):
    @property
    def name(self):
        return "riskOverlay"
    
    def get_notional_position(self, instrument_code):
        # Get base position
        base_pos = self.parent.portfolio.get_notional_position(instrument_code)
        
        # Apply risk overlay
        risk_factor = self.calculate_risk_factor(instrument_code)
        
        return base_pos * risk_factor
    
    def calculate_risk_factor(self, instrument_code):
        # Custom risk logic
        return 0.95  # Reduce all positions by 5%

# Use in system
system = System([..., portfolio, RiskOverlay(), ...], data, config)
```

---

## See Also

- [Backtesting Guide](../backtesting/backtesting_guide.md)
- [Trading Rules](../backtesting/trading_rules.md)
- [Core Concepts - System Stages](../core_concepts/system_stages.md)
