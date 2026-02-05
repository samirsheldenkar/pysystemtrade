# Trading Rules

Trading rules are the core signal generation components of pysystemtrade. This document covers how to use built-in rules and create custom ones.

## What is a Trading Rule?

A trading rule transforms price data into trading signals (forecasts). In pysystemtrade:

- Forecasts are continuous values (not just buy/sell signals)
- Default target: average absolute value of 10
- Typical range: -20 to +20 (configurable)
- Positive = long bias, Negative = short bias
- Magnitude indicates confidence/strength

## Built-in Trading Rules

### EWMAC (Exponentially Weighted Moving Average Crossover)

**File**: `systems/provided/rules/ewmac.py`

Classic trend-following rule using two EWMAs.

```python
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

# Default: Lfast=32, Lslow=128
rule = TradingRule(ewmac_forecast_with_defaults)

# Custom parameters
from systems.provided.rules.ewmac import ewmac_forecast
rule_fast = TradingRule(
    ewmac_forecast,
    other_args={'Lfast': 8, 'Lslow': 32}
)
rule_slow = TradingRule(
    ewmac_forecast,
    other_args={'Lfast': 32, 'Lslow': 128}
)
```

**Logic**:
```python
def ewmac_forecast(price, Lfast=32, Lslow=128):
    fast_ewma = price.ewm(span=Lfast).mean()
    slow_ewma = price.ewm(span=Lslow).mean()
    raw_forecast = fast_ewma - slow_ewma
    
    # Normalize by volatility
    vol = robust_vol_calc(price.diff())
    return raw_forecast / vol
```

**Common Variations**:
- EWMAC 2,8: Very fast
- EWMAC 8,32: Fast
- EWMAC 16,64: Medium
- EWMAC 32,128: Slow (default)
- EWMAC 64,256: Very slow

### Carry Rule

**File**: `systems/provided/rules/carry.py`

Captures roll yield / carry in futures markets.

```python
from systems.provided.rules.carry import carry_forecast_with_defaults

rule = TradingRule(carry_forecast_with_defaults)
```

**Logic**: Compares near contract vs far contract price difference, normalized by volatility.

**Data Requirements**:
- Requires multiple prices (PRICE, CARRY contracts)
- Configure carry offset in roll parameters

### Breakout Rule

**File**: `systems/provided/rules/breakout.py`

Identifies when price breaks out of recent trading range.

```python
from systems.provided.rules.breakout import breakout_forecast_with_defaults

rule = TradingRule(
    breakout_forecast_with_defaults,
    other_args={'lookback': 100}
)
```

**Logic**:
```python
def breakout_forecast(price, lookback=100):
    # Position within recent range
    recent_max = price.rolling(lookback).max()
    recent_min = price.rolling(lookback).min()
    position = (price - recent_min) / (recent_max - recent_min)
    
    # Scale to forecast range
    return (position - 0.5) * 40  # -20 to +20
```

### Other Built-in Rules

**Mean Reversion** (`mr_wings.py`):
```python
from systems.provided.rules.mr_wings import mr_wings_forecast

rule = TradingRule(mr_wings_forecast)
```

**Acceleration** (`accel.py`):
```python
from systems.provided.rules.accel import accel_forecast

rule = TradingRule(accel_forecast)
```

**Cross-Sectional Momentum** (`cs_mr.py`):
```python
from systems.provided.rules.cs_mr import cs_mr_forecast

rule = TradingRule(cs_mr_forecast)
```

## Creating Custom Trading Rules

### Basic Structure

```python
from systems.trading_rules import TradingRule

def my_trading_rule(price, param1=10, param2=20):
    """
    Custom trading rule
    
    Args:
        price: pd.Series of prices
        param1: First parameter
        param2: Second parameter
    
    Returns:
        pd.Series of forecasts
    """
    # Your signal logic here
    signal = calculate_signal(price, param1, param2)
    
    # Normalize to target volatility
    # (optional - scaling stage can do this)
    return signal

# Create trading rule
my_rule = TradingRule(
    my_trading_rule,
    data=['data.daily_prices'],  # Input data
    other_args={'param1': 15, 'param2': 30}  # Parameters
)
```

### Example: RSI Rule

```python
import pandas as pd
from systems.trading_rules import TradingRule

def rsi_forecast(price, lookback=14, oversold=30, overbought=70):
    """
    RSI-based trading rule
    
    Returns forecast based on RSI levels:
    - RSI < oversold: positive forecast (long)
    - RSI > overbought: negative forecast (short)
    """
    # Calculate RSI
    delta = price.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=lookback).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=lookback).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # Convert to forecast
    forecast = pd.Series(0, index=price.index)
    forecast[rsi < oversold] = 10   # Long signal
    forecast[rsi > overbought] = -10  # Short signal
    
    # Scale by distance from neutral (50)
    forecast = (50 - rsi) / 5
    
    return forecast

# Create rule
rsi_rule = TradingRule(
    rsi_forecast,
    data=['data.daily_prices'],
    other_args={'lookback': 14, 'oversold': 30, 'overbought': 70}
)
```

### Example: Multi-Input Rule

Rules can use multiple data sources:

```python
def multi_input_rule(daily_prices, carry_data, vol_data, vol_lookback=36):
    """
    Rule using price, carry, and volatility data
    """
    # Trend component
    fast = daily_prices.ewm(span=16).mean()
    slow = daily_prices.ewm(span=64).mean()
    trend = (fast - slow) / vol_data
    
    # Carry component
    carry = carry_data.CARRY - carry_data.PRICE
    carry_signal = carry / vol_data
    
    # Combine
    forecast = 0.7 * trend + 0.3 * carry_signal
    return forecast

# Create rule with multiple data inputs
multi_rule = TradingRule(
    multi_input_rule,
    data=[
        'data.daily_prices',
        'data.get_instrument_raw_carry_data',
        'data.get_daily_volatility'
    ],
    other_args={'vol_lookback': 36}
)
```

## The TradingRule Class

### Constructor

```python
TradingRule(
    rule_function,           # Function that generates forecasts
    data=None,               # List of data inputs
    other_args=None,         # Dict of additional arguments
    name=None                # Optional name
)
```

### Data Inputs

Data inputs are specified as strings referencing system attributes:

```python
# Common data sources
data=['data.daily_prices']                           # Daily prices
data=['data.get_instrument_raw_carry_data']         # Carry data
data=['data.hourly_prices']                         # Hourly prices
data=['data.get_daily_volatility']                  # Volatility

# Multiple inputs
data=[
    'data.daily_prices',
    'data.get_instrument_raw_carry_data'
]
```

### Alternative Ways to Create TradingRules

**From tuple**:
```python
rule = TradingRule((my_function, ['data.daily_prices'], {'param': 10}))
```

**From dict**:
```python
rule = TradingRule({
    'function': my_function,
    'data': ['data.daily_prices'],
    'other_args': {'param': 10}
})
```

**From YAML**:
```yaml
trading_rules:
  my_rule:
    function: my_module.my_function
    data:
      - data.daily_prices
    other_args:
      param: 10
```

## Using Trading Rules in Systems

### Adding Rules to Configuration

```python
from sysdata.config.configdata import Config
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults
from systems.trading_rules import TradingRule

# Create rules
ewmac_fast = TradingRule(
    ewmac_forecast_with_defaults,
    other_args={'Lfast': 8, 'Lslow': 32}
)

ewmac_slow = TradingRule(
    ewmac_forecast_with_defaults,
    other_args={'Lfast': 32, 'Lslow': 128}
)

# Create config
config = Config({
    'trading_rules': {
        'ewmac_fast': ewmac_fast,
        'ewmac_slow': ewmac_slow
    },
    'forecast_weights': {
        'ewmac_fast': 0.5,
        'ewmac_slow': 0.5
    }
})
```

### Adding Rules to Rules Stage

```python
from systems.forecasting import Rules

# Method 1: Pass to constructor
my_rules = Rules({
    'ewmac_fast': ewmac_fast,
    'ewmac_slow': ewmac_slow
})

# Method 2: Set on config
empty_rules = Rules()
config.trading_rules = {'ewmac_fast': ewmac_fast, 'ewmac_slow': ewmac_slow}

# Build system
system = System([empty_rules, ...], data, config)
```

## Rule Evaluation

### Testing Individual Rules

```python
# Get raw forecast
forecast = system.rules.get_raw_forecast("SOFR", "ewmac_fast")

# Plot
forecast.plot(title="Raw Forecast")

# Statistics
print(f"Mean: {forecast.mean()}")
print(f"Std: {forecast.std()}")
print(f"Abs Mean: {forecast.abs().mean()}")
```

### Rule Performance

```python
# Get P&L for specific rule
rule_pandl = system.accounts.pandl_for_instrument_forecast("SOFR", "ewmac_fast")

# Statistics
print(rule_pandl.percent.stats())
print(f"Sharpe: {rule_pandl.sharpe()}")

# Compare rules
for rule_name in system.rules.trading_rules().keys():
    pandl = system.accounts.pandl_for_instrument_forecast("SOFR", rule_name)
    print(f"{rule_name}: Sharpe {pandl.sharpe():.2f}")
```

## Best Practices

### 1. Normalize Outputs

Aim for consistent forecast distributions:

```python
def normalized_rule(price, ...):
    # Calculate raw signal
    signal = calculate_signal(price, ...)
    
    # Normalize to have roughly std=1
    # (so scaling to avg abs of 10 works properly)
    normalized = signal / signal.std()
    
    return normalized
```

### 2. Handle Missing Data

```python
def robust_rule(price, ...):
    # Handle NaN values
    price = price.fillna(method='ffill')
    
    # Your logic
    signal = ...
    
    # Return NaN where we don't have enough data
    min_periods = 100
    signal.iloc[:min_periods] = np.nan
    
    return signal
```

### 3. Use Robust Volatility

```python
from sysquant.estimators.vol import robust_vol_calc

def rule_with_vol_normalization(price, ...):
    signal = calculate_signal(price, ...)
    vol = robust_vol_calc(price.diff())  # Robust volatility estimate
    return signal / vol
```

### 4. Document Parameters

```python
def well_documented_rule(price, fast_span=16, slow_span=64, vol_lookback=36):
    """
    EWMAC variant with custom parameters
    
    Parameters:
    -----------
    price : pd.Series
        Price series
    fast_span : int
        Fast EWMA span (default: 16)
    slow_span : int
        Slow EWMA span (default: 64)
    vol_lookback : int
        Volatility estimation window (default: 36)
    
    Returns:
    --------
    pd.Series
        Forecast series
    """
    ...
```

## Advanced Topics

### Dynamic Rule Parameters

Use configuration to change parameters without code changes:

```python
# In config
config.my_rule_params = {'fast': 8, 'slow': 32}

# In rule
def dynamic_rule(price, system, ...):
    params = system.config.my_rule_params
    fast = params['fast']
    slow = params['slow']
    ...
```

### Rule Combinations

Combine rules within a single function:

```python
def combined_rule(price, ...):
    # Calculate multiple signals
    trend = calculate_trend(price, ...)
    carry = calculate_carry(price, ...)
    
    # Dynamic weighting based on regime
    regime = detect_regime(price, ...)
    if regime == 'trending':
        return 0.8 * trend + 0.2 * carry
    else:
        return 0.3 * trend + 0.7 * carry
```

### Cross-Sectional Rules

Rules that compare across instruments:

```python
def cross_sectional_rule(system, instrument_code, ...):
    # Get data for all instruments
    all_instruments = system.get_instrument_list()
    
    # Calculate signal for each
    signals = {}
    for inst in all_instruments:
        price = system.data.daily_prices(inst)
        signals[inst] = calculate_signal(price, ...)
    
    # Rank and select
    current_signal = signals[instrument_code]
    rank = pd.Series(signals).rank()[instrument_code]
    
    # Go long top quartile, short bottom quartile
    if rank > 0.75:
        return 10
    elif rank < 0.25:
        return -10
    else:
        return 0
```

## Rule Library

### Trend Following
- EWMAC (multiple timeframes)
- Breakout
- Acceleration
- Linear trend

### Mean Reversion
- RSI
- Bollinger Bands
- MR Wings
- Statistical arbitrage

### Carry
- Standard carry
- Vol-adjusted carry
- Seasonal carry

### Multi-Factor
- Trend + Carry combination
- Momentum + Value
- Custom factor blends

## Next Steps

- Learn about [Forecast Scaling and Combination](./backtesting_guide.md)
- Explore [Portfolio Construction](./backtesting_guide.md)
- See [Provided Systems](./provided_systems.md) for complete examples
