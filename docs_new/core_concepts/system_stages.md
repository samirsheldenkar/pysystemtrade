# Understanding System Stages

System stages are the building blocks of trading systems in pysystemtrade. Each stage performs a specific function in the trading pipeline, processing data and passing results to subsequent stages.

## Stage Basics

### What is a Stage?

A stage is a modular component that:
- Performs a specific calculation or transformation
- Can access data from parent system and other stages
- Caches results for performance
- Is configured through the system's configuration

### Stage Inheritance

All stages inherit from `SystemStage` (`systems/stage.py`):

```python
from systems.stage import SystemStage

class MyStage(SystemStage):
    @property
    def name(self):
        return "myStage"  # Unique identifier
    
    def my_method(self, instrument_code):
        # Implementation here
        pass
```

### Accessing Stages

Stages are accessed through the parent system:

```python
# Access a stage
system.rules.get_capped_forecast("SOFR", "ewmac")

# Access another stage from within a stage
other_stage = self.parent.otherStageName
```

## Core Stages Explained

### 1. Raw Data Stage (`rawdata`)

**File**: `systems/rawdata.py`

**Purpose**: Preprocess and transform raw price data into formats needed by trading rules.

**Key Methods**:
```python
# Get daily prices for an instrument
daily_prices = system.rawdata.daily_prices("SOFR")

# Get carry data (for carry trading rules)
carry_data = system.rawdata.get_instrument_raw_carry_data("SOFR")

# Calculate returns
returns = system.rawdata.get_percentage_returns("SOFR")
```

**Configuration Options**:
```yaml
rawdata:
  frequency: "daily"  # or "hourly", "weekly"
```

### 2. Trading Rules Stage (`rules`)

**File**: `systems/forecasting.py`

**Purpose**: Apply trading rules to generate raw forecasts.

**Key Methods**:
```python
# Get raw forecast for a specific rule
forecast = system.rules.get_raw_forecast("SOFR", "ewmac64_256")

# Get all trading rules
rules_dict = system.rules.trading_rules()

# Get forecast for instrument (across all rules)
all_forecasts = system.rules.get_all_forecasts("SOFR")
```

**Built-in Rules** (in `systems/provided/rules/`):
- **EWMAC**: Exponentially weighted moving average crossover
- **Carry**: Carry trading rule
- **Breakout**: Price breakout
- **Mean Reversion**: Mean reversion strategies

**Defining Custom Rules**:
```python
from systems.trading_rules import TradingRule

def my_rule(price, fast=16, slow=64):
    fast_ewma = price.ewm(span=fast).mean()
    slow_ewma = price.ewm(span=slow).mean()
    return fast_ewma - slow_ewma

trading_rule = TradingRule(my_rule)
```

### 3. Forecast Scale and Cap Stage (`forecastScaleCap`)

**File**: `systems/forecast_scale_cap.py`

**Purpose**: Scale forecasts to target volatility and apply caps.

**Concept**: Forecasts should have an average absolute value of 10 (configurable). This stage:
1. Calculates or uses configured forecast scalars
2. Scales raw forecasts
3. Applies maximum/minimum caps (default ±20)

**Key Methods**:
```python
# Get scaled forecast
scaled = system.forecastScaleCap.get_capped_forecast("SOFR", "ewmac64_256")

# Get forecast scalar
scalar = system.forecastScaleCap.get_forecast_scalar("SOFR", "ewmac64_256")
```

**Configuration**:
```yaml
# Fixed scalars
forecast_scalars:
  ewmac64_256: 2.65
  ewmac16_64: 5.3

# Use estimation instead
use_forecast_scale_estimates: true

# Forecast cap
forecast_cap: 20.0
```

### 4. Forecast Combine Stage (`combForecast`)

**File**: `systems/forecast_combine.py`

**Purpose**: Combine multiple forecasts into a single forecast per instrument.

**Methods**:
- Equal weights (default)
- Estimated optimal weights
- Hierarchical weighting

**Key Methods**:
```python
# Get combined forecast
combined = system.combForecast.get_combined_forecast("SOFR")

# Get forecast weights
weights = system.combForecast.get_forecast_weights("SOFR")

# Get diversification multiplier
fdm = system.combForecast.get_forecast_diversification_multiplier("SOFR")
```

**Configuration**:
```yaml
# Fixed weights
forecast_weights:
  ewmac64_256: 0.6
  ewmac16_64: 0.4

# Fixed diversification multiplier
forecast_div_multiplier: 1.1

# Or use estimation
use_forecast_weight_estimates: true
use_forecast_div_mult_estimates: true
```

### 5. Position Sizing Stage (`positionSize`)

**File**: `systems/positionsizing.py`

**Purpose**: Convert forecasts into position sizes based on volatility and capital.

**Key Formula**:
```
Position = (Forecast / 10) * (Capital * Vol Target%) / (Volatility * Contract Multiplier)
```

**Key Methods**:
```python
# Get subsystem position
position = system.positionSize.get_subsystem_position("SOFR")

# Get volatility scalar
vol_scalar = system.positionSize.get_volatility_scalar("SOFR")

# Get daily cash volatility target
target = system.positionSize.get_daily_cash_vol_target()
```

**Configuration**:
```yaml
# Risk targeting
percentage_vol_target: 25.0  # Annual volatility target
notional_trading_capital: 500000
base_currency: "GBP"

# Trading capital
capital_multiplier: 1.0
```

### 6. Portfolio Stage (`portfolio`)

**File**: `systems/portfolio.py`

**Purpose**: Combine multiple instruments into a diversified portfolio.

**Functions**:
- Applies instrument weights
- Calculates instrument diversification multiplier
- Produces final notional positions

**Key Methods**:
```python
# Get notional position
position = system.portfolio.get_notional_position("SOFR")

# Get instrument weights
weights = system.portfolio.get_instrument_weights()

# Get instrument diversification multiplier
idm = system.portfolio.get_instrument_diversification_multiplier()

# Get all instrument positions
all_positions = system.portfolio.get_all_positions()
```

**Configuration**:
```yaml
# Fixed instrument weights
instrument_weights:
  SOFR: 0.4
  US10: 0.3
  CORN: 0.2
  SP500_micro: 0.1

# Fixed IDM
instrument_div_multiplier: 1.5

# Or use estimation
use_instrument_weight_estimates: true
use_instrument_div_mult_estimates: true
```

### 7. Accounts Stage (`accounts`)

**Directory**: `systems/accounts/`

**Purpose**: Calculate P&L, performance metrics, and account curves.

**Key Methods**:
```python
# Get portfolio P&L
portfolio_pandl = system.accounts.portfolio()

# Get instrument P&L
instrument_pandl = system.accounts.pandl_for_instrument("SOFR")

# Get forecast P&L
forecast_pandl = system.accounts.pandl_for_instrument_forecast("SOFR", "ewmac")

# Get statistics
stats = portfolio_pandl.percent.stats()
sharpe = portfolio_pandl.sharpe()
```

**Account Curve Methods**:
```python
# Cumulative returns
curve = portfolio_pandl.curve()

# Drawdown
drawdown = portfolio_pandl.drawdown()

# Rolling statistics
rolling_sharpe = portfolio_pandl.rolling_sharpe()

# Costs breakdown
gross_pandl = portfolio_pandl.gross
costs = portfolio_pandl.costs
```

## Optional Stages

### Buffering Stage

**File**: `systems/buffering.py`

Reduces trading by applying position buffers:

```python
# Get buffered position
buffered_pos = system.buffering.get_buffered_position("SOFR")
```

### Risk Overlay Stage

**File**: `systems/risk_overlay.py`

Applies risk management overlays:

```python
# Get position with risk overlay
risk_adjusted_pos = system.riskOverlay.get_notional_position("SOFR")
```

## Stage Interaction Example

Here's how stages interact in a complete system:

```python
from systems.basesystem import System
from systems.forecasting import Rules
from systems.forecast_scale_cap import ForecastScaleCap
from systems.forecast_combine import ForecastCombine
from systems.positionsizing import PositionSizing
from systems.rawdata import RawData
from systems.portfolio import Portfolios
from systems.accounts.accounts_stage import Account

# Create stages
my_rules = Rules(dict(ewmac=ewmac_rule))
fcs = ForecastScaleCap()
combiner = ForecastCombine()
raw_data = RawData()
position_size = PositionSizing()
portfolio = Portfolios()
accounts = Account()

# Build system (order doesn't matter)
system = System(
    [my_rules, fcs, combiner, raw_data, position_size, portfolio, accounts],
    data,
    config
)

# Access results from any stage
forecast = system.rules.get_capped_forecast("SOFR", "ewmac")
combined = system.combForecast.get_combined_forecast("SOFR")
position = system.portfolio.get_notional_position("SOFR")
profits = system.accounts.portfolio()
```

## Creating Custom Stages

To create a custom stage:

1. **Inherit from SystemStage**:
```python
from systems.stage import SystemStage

class CustomStage(SystemStage):
    @property
    def name(self):
        return "customStage"
```

2. **Access Parent System**:
```python
def some_method(self, instrument_code):
    # Access other stages
    forecast = self.parent.rules.get_capped_forecast(instrument_code, "ewmac")
    
    # Access data
    prices = self.parent.data.daily_prices(instrument_code)
    
    # Access config
    param = self.parent.config.my_param
```

3. **Add to System**:
```python
custom_stage = CustomStage()
system = System([..., custom_stage, ...], data, config)
```

## Stage Diagnostics

Each stage provides diagnostic methods:

```python
# List available methods
print(system.rules.methods())

# Get stage description
print(system.rules)
```

## Best Practices

1. **Stage Independence**: Stages should be self-contained
2. **Cache Awareness**: Use `@diagnostic` decorator for cached methods
3. **Configuration**: Expose parameters through config, not hardcoded
4. **Error Handling**: Validate inputs and provide clear error messages
5. **Documentation**: Document expected inputs and outputs

## Next Steps

- Learn about [Data Flow](./data_flow.md)
- Understand the [Configuration System](./configuration.md)
- Explore [Trading Rules](../backtesting/trading_rules.md)
