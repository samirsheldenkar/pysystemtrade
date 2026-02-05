# Backtesting Guide

This guide covers how to use pysystemtrade for backtesting trading strategies on historical futures data.

## Overview

Backtesting in pysystemtrade follows a stage-based architecture where data flows through various processing stages:

```
Raw Data → Trading Rules → Forecast Scaling → Forecast Combination → 
Position Sizing → Portfolio Construction → P&L Calculation
```

Each stage is modular and configurable, allowing you to customize every aspect of the backtesting process.

## Quick Start

### Running Your First Backtest

The simplest way to run a backtest is using a pre-baked system:

```python
from systems.provided.futures_chapter15.basesystem import futures_system

# Create system with default configuration
system = futures_system()

# Get positions for an instrument
positions = system.portfolio.get_notional_position("SOFR")
print(positions.tail())

# Calculate P&L
profits = system.accounts.portfolio()
print(profits.percent.stats())
```

### Available Pre-Baked Systems

1. **futures_chapter15.basesystem**: Fixed parameter system from Chapter 15 of "Systematic Trading"
2. **futures_chapter15.estimatedsystem**: System with estimated parameters (weights, scalars)
3. **provided.example.simplesystem**: Minimal example system

## Building Custom Systems

### Step-by-Step System Construction

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

# 1. Load data
data = csvFuturesSimData()

# 2. Create configuration
config = Config({
    'instruments': ['SOFR', 'US10', 'CORN'],
    'percentage_vol_target': 25.0,
    'notional_trading_capital': 500000,
    'base_currency': 'USD',
    'forecast_scalars': {'ewmac': 2.65},
    'forecast_weights': {'ewmac': 1.0},
    'instrument_weights': {
        'SOFR': 0.5,
        'US10': 0.3,
        'CORN': 0.2
    }
})

# 3. Create stages
my_rules = Rules()
fcs = ForecastScaleCap()
combiner = ForecastCombine()
raw_data = RawData()
position_size = PositionSizing()
portfolio = Portfolios()
accounts = Account()

# 4. Build system
system = System(
    [my_rules, fcs, combiner, raw_data, position_size, portfolio, accounts],
    data,
    config
)

# 5. Run backtest
profits = system.accounts.portfolio()
```

### Using Configuration Files

Create a YAML configuration file:

```yaml
# my_system_config.yaml
instruments:
  - SOFR
  - US10
  - CORN

percentage_vol_target: 25.0
notional_trading_capital: 500000
base_currency: USD

forecast_scalars:
  ewmac_fast: 5.3
  ewmac_slow: 2.65

forecast_weights:
  ewmac_fast: 0.5
  ewmac_slow: 0.5

instrument_weights:
  SOFR: 0.5
  US10: 0.3
  CORN: 0.2

instrument_div_multiplier: 1.5
```

Load and use it:

```python
from sysdata.config.configdata import Config

config = Config("private.my_system.config")
system = futures_system(config=config)
```

## Working with Trading Rules

### Built-in Trading Rules

Located in `systems/provided/rules/`:

```python
# EWMAC (Exponentially Weighted Moving Average Crossover)
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults

# Carry rule
from systems.provided.rules.carry import carry_forecast_with_defaults

# Breakout rule
from systems.provided.rules.breakout import breakout_forecast_with_defaults
```

### Creating Custom Trading Rules

```python
import pandas as pd
from systems.trading_rules import TradingRule

def my_custom_rule(price, fast=16, slow=64):
    """
    Custom EWMAC rule
    
    Args:
        price: Price series
        fast: Fast EWMA span
        slow: Slow EWMA span
    
    Returns:
        Forecast series
    """
    fast_ewma = price.ewm(span=fast).mean()
    slow_ewma = price.ewm(span=slow).mean()
    raw_forecast = fast_ewma - slow_ewma
    
    # Normalize by volatility
    vol = price.diff().ewm(span=36).std()
    return raw_forecast / vol

# Create trading rule
my_rule = TradingRule(
    my_custom_rule,
    data=['data.daily_prices'],  # Data inputs
    other_args={'fast': 8, 'slow': 32}  # Default parameters
)

# Add to system
config.trading_rules = {'my_rule': my_rule}
```

## Accessing Backtest Results

### Portfolio Results

```python
# Get full portfolio P&L
portfolio_pandl = system.accounts.portfolio()

# Get statistics
stats = portfolio_pandl.percent.stats()
print(stats)

# Individual metrics
sharpe = portfolio_pandl.sharpe()
max_drawdown = portfolio_pandl.max_drawdown()
annual_return = portfolio_pandl.ann_mean()

# Plot results
portfolio_pandl.curve().plot()
portfolio_pandl.drawdown().plot()
```

### Instrument-Level Results

```python
# P&L for specific instrument
instrument_pandl = system.accounts.pandl_for_instrument("SOFR")
print(instrument_pandl.percent.stats())

# P&L for specific trading rule
rule_pandl = system.accounts.pandl_for_instrument_forecast("SOFR", "ewmac")
print(rule_pandl.sharpe())
```

### Intermediate Results

Access results from any stage:

```python
# Raw forecast (from rules stage)
raw_forecast = system.rules.get_raw_forecast("SOFR", "ewmac")

# Scaled forecast (from scale/cap stage)
scaled_forecast = system.forecastScaleCap.get_capped_forecast("SOFR", "ewmac")

# Combined forecast (from combine stage)
combined_forecast = system.combForecast.get_combined_forecast("SOFR")

# Subsystem position (from position sizing stage)
subsystem_position = system.positionSize.get_subsystem_position("SOFR")

# Final position (from portfolio stage)
final_position = system.portfolio.get_notional_position("SOFR")
```

## Optimization and Estimation

### Estimating Forecast Scalars

```python
# Enable estimation
config.use_forecast_scale_estimates = True

# Configure estimation parameters
config.forecast_scalar_estimate = {
    'pool_instruments': True,
    'min_periods': 20,
    'ewma_span': 500
}
```

### Estimating Forecast Weights

```python
# Enable estimation
config.use_forecast_weight_estimates = True
config.use_forecast_div_mult_estimates = True

# Configure estimation
config.forecast_weight_estimate = {
    'method': 'bootstrap',  # or 'shrinkage', 'one_period'
    'date_method': 'rolling',
    'rollyears': 10,
    'monte_carlo_runs': 100
}
```

### Estimating Instrument Weights

```python
# Enable estimation
config.use_instrument_weight_estimates = True
config.use_instrument_div_mult_estimates = True

# Configure estimation
config.instrument_weight_estimate = {
    'method': 'handcraft',  # or 'bootstrap', 'shrinkage'
    'date_method': 'rolling',
    'rollyears': 20
}
```

## Performance Analysis

### Account Curve Methods

The `accountCurve` object (returned by `accounts.portfolio()`) provides many analysis methods:

```python
profits = system.accounts.portfolio()

# Returns
daily_returns = profits.daily
weekly_returns = profits.weekly
monthly_returns = profits.monthly
annual_returns = profits.annual

# Cumulative
cumulative = profits.curve()
percent_cumulative = profits.percent.curve()

# Risk metrics
sharpe = profits.sharpe()
sortino = profits.sortino()
max_dd = profits.max_drawdown()
avg_dd = profits.avg_drawdown()
calmar = profits.calmar()

# Distribution
mean = profits.mean()
std = profits.std()
skew = profits.skew()
kurtosis = profits.kurtosis()
hit_rate = profits.hitrate()

# Costs
gross_returns = profits.gross
costs = profits.costs
net_returns = profits.net
```

### Comparative Analysis

```python
# Compare multiple systems
system1 = futures_system(config=config1)
system2 = futures_system(config=config2)

profits1 = system1.accounts.portfolio()
profits2 = system2.accounts.portfolio()

print(f"System 1 Sharpe: {profits1.sharpe()}")
print(f"System 2 Sharpe: {profits2.sharpe()}")

# Plot comparison
import matplotlib.pyplot as plt
profits1.curve().plot(label='System 1')
profits2.curve().plot(label='System 2')
plt.legend()
plt.show()
```

## Caching and Performance

### Using Cache

```python
# Results are automatically cached
# First call computes
forecast1 = system.rules.get_capped_forecast("SOFR", "ewmac")

# Second call uses cache
forecast2 = system.rules.get_capped_forecast("SOFR", "ewmac")  # Fast!

# Clear cache if needed
system.cache.delete_all_items()

# Or clear specific items
system.cache.delete_items_for_instrument("SOFR")
```

### Saving and Loading Cache

```python
# Save expensive calculations
system.cache.pickle("my_backtest_cache.pck")

# In new session, load cache
system.cache.unpickle("my_backtest_cache.pck")
# Now runs are much faster!
profits = system.accounts.portfolio()  # Uses cached results
```

## Advanced Topics

### Rolling Window Backtests

```python
# Configure rolling estimation
config.forecast_weight_estimate = {
    'method': 'bootstrap',
    'date_method': 'rolling',  # or 'in_sample', 'expanding'
    'rollyears': 10,
    'frequency': 'yearly'  # Re-estimate annually
}
```

### Cost Analysis

```python
# Get cost breakdown
gross = system.accounts.portfolio().gross
costs = system.accounts.portfolio().costs
net = system.accounts.portfolio()

print(f"Gross Sharpe: {gross.sharpe()}")
print(f"Net Sharpe: {net.sharpe()}")
print(f"Cost impact: {gross.sharpe() - net.sharpe()}")

# Cost per instrument
for instrument in system.get_instrument_list():
    inst_pandl = system.accounts.pandl_for_instrument(instrument)
    print(f"{instrument}: Costs = {inst_pandl.costs.ann_mean()}")
```

### Risk Analysis

```python
# Portfolio risk
from systems.risk import Risk

risk = Risk()
system = System([..., risk, ...], data, config)

# Get risk metrics
portfolio_risk = system.risk.get_portfolio_risk()
instrument_risk = system.risk.get_instrument_risk("SOFR")
correlation = system.risk.get_correlation_matrix()
```

## Best Practices

1. **Start Simple**: Begin with pre-baked systems before building custom ones
2. **Use Fixed Parameters First**: Understand the system before enabling estimation
3. **Cache Expensive Calculations**: Save cache for systems with estimation
4. **Validate Results**: Check intermediate outputs at each stage
5. **Test on Subset**: Use few instruments when developing
6. **Version Control Configs**: Track configuration changes with git

## Common Patterns

### Pattern 1: Parameter Sensitivity Analysis

```python
vol_targets = [15, 20, 25, 30]
results = {}

for vol in vol_targets:
    config.percentage_vol_target = vol
    system = futures_system(config=config)
    profits = system.accounts.portfolio()
    results[vol] = profits.sharpe()

for vol, sharpe in results.items():
    print(f"Vol target {vol}%: Sharpe {sharpe:.2f}")
```

### Pattern 2: Rule Comparison

```python
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults
from systems.provided.rules.carry import carry_forecast_with_defaults

rules = {
    'ewmac': TradingRule(ewmac_forecast_with_defaults),
    'carry': TradingRule(carry_forecast_with_defaults)
}

for rule_name, rule in rules.items():
    config.trading_rules = {rule_name: rule}
    system = futures_system(config=config)
    profits = system.accounts.portfolio()
    print(f"{rule_name}: Sharpe {profits.sharpe():.2f}")
```

### Pattern 3: Walk-Forward Testing

```python
# Split data by date
train_end = '2020-01-01'
test_start = '2020-01-02'

# Train on first period
config.instrument_weight_estimate['date_method'] = 'in_sample'
system_train = futures_system(config=config)
# ... extract optimal parameters ...

# Test on second period with fixed parameters
config.use_instrument_weight_estimates = False
config.instrument_weights = trained_weights
system_test = futures_system(config=config)
# ... evaluate performance ...
```

## Troubleshooting

### Issue: Slow Performance

**Solution**: Enable caching and use fixed parameters
```python
config.use_forecast_scale_estimates = False
config.use_forecast_weight_estimates = False
```

### Issue: Memory Errors

**Solution**: Reduce instrument set or use database instead of CSV
```python
config.instruments = ['SOFR', 'US10']  # Subset only
```

### Issue: Missing Data

**Solution**: Check instrument list and data availability
```python
available = data.get_instrument_list()
required = config.instruments
missing = [i for i in required if i not in available]
print(f"Missing instruments: {missing}")
```

## Next Steps

- Learn about [Trading Rules](./trading_rules.md) in detail
- Explore [Data Management](../data_management/data_overview.md)
- Read about [Production Trading](../production_trading/production_setup.md)
- See [Provided Systems](./provided_systems.md) documentation
