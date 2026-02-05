# Tutorial: Your First Backtest

This tutorial walks you through running your first backtest with pysystemtrade.

## Prerequisites

- pysystemtrade installed (see [Installation](../getting_started/installation.md))
- Basic Python knowledge
- Understanding of futures markets (helpful but not required)

## Step 1: Verify Installation

First, let's make sure everything is working:

```python
from sysdata.sim.csv_futures_sim_data import csvFuturesSimData

# Load data
data = csvFuturesSimData()

# Check available instruments
instruments = data.get_instrument_list()
print(f"Available instruments: {len(instruments)}")
print(f"First 10: {instruments[:10]}")
```

You should see something like:
```
Available instruments: 249
First 10: ['CORN', 'LEANHOG', 'LIVECOW', 'SOYBEAN', 'WHEAT', 'KR10', 'KR3', 'BOBL', 'BTP', 'BUND']
```

## Step 2: Run a Pre-Baked System

The easiest way to start is using a pre-configured system:

```python
from systems.provided.futures_chapter15.basesystem import futures_system

# Create system (uses default CSV data)
system = futures_system()

# Check system configuration
print(system)
```

Output:
```
System with stages: accounts, portfolio, positionSize, combForecast, forecastScaleCap, rules
```

## Step 3: Get Trading Positions

Let's see what positions the system recommends:

```python
# Get positions for a specific instrument
positions = system.portfolio.get_notional_position("SOFR")
print("\nSOFR Positions (last 5 days):")
print(positions.tail())

# Get positions for another instrument
positions2 = system.portfolio.get_notional_position("US10")
print("\nUS10 Positions (last 5 days):")
print(positions2.tail())
```

## Step 4: Analyze Performance

Now let's see how profitable this system was:

```python
# Calculate P&L
profits = system.accounts.portfolio()

# Get statistics
stats = profits.percent.stats()
print("\nPortfolio Performance Statistics:")
print(stats)
```

Key metrics you'll see:
- **Sharpe Ratio**: Risk-adjusted return (higher is better)
- **Annual Return**: Average yearly return
- **Annual Volatility**: Standard deviation of returns
- **Max Drawdown**: Largest peak-to-trough decline

## Step 5: Visualize Results

```python
import matplotlib.pyplot as plt

# Plot equity curve
plt.figure(figsize=(12, 6))
profits.curve().plot()
plt.title("Portfolio Equity Curve")
plt.ylabel("Cumulative Returns")
plt.show()

# Plot drawdown
plt.figure(figsize=(12, 6))
profits.drawdown().plot()
plt.title("Portfolio Drawdown")
plt.ylabel("Drawdown %")
plt.show()
```

## Step 6: Examine Intermediate Results

Let's look at how the system arrived at these positions:

```python
# Get raw forecast from trading rule
raw_forecast = system.rules.get_raw_forecast("SOFR", "ewmac64_256")
print("\nRaw Forecast (last 5 days):")
print(raw_forecast.tail())

# Get scaled and capped forecast
scaled_forecast = system.forecastScaleCap.get_capped_forecast("SOFR", "ewmac64_256")
print("\nScaled Forecast (last 5 days):")
print(scaled_forecast.tail())

# Get combined forecast (if multiple rules)
combined_forecast = system.combForecast.get_combined_forecast("SOFR")
print("\nCombined Forecast (last 5 days):")
print(combined_forecast.tail())
```

## Step 7: Customize Configuration

Let's modify some parameters:

```python
from sysdata.config.configdata import Config

# Create custom configuration
config = Config({
    'instruments': ['SOFR', 'US10', 'CORN', 'SP500_micro'],
    'percentage_vol_target': 20.0,  # Lower risk
    'notional_trading_capital': 1000000,
    'base_currency': 'USD'
})

# Create system with custom config
system2 = futures_system(config=config)

# Compare performance
profits2 = system2.accounts.portfolio()
print("\nOriginal System Sharpe:", profits.sharpe())
print("Custom System Sharpe:", profits2.sharpe())
```

## Step 8: Test Different Trading Rules

Let's see how different trading rules perform:

```python
from systems.provided.rules.ewmac import ewmac_forecast_with_defaults
from systems.provided.rules.carry import carry_forecast_with_defaults
from systems.trading_rules import TradingRule

# Create rules
carry_rule = TradingRule(carry_forecast_with_defaults)

# Test carry rule
config_carry = Config({
    'instruments': ['SOFR', 'US10'],
    'trading_rules': {'carry': carry_rule},
    'forecast_weights': {'carry': 1.0}
})

system_carry = futures_system(config=config_carry)
profits_carry = system_carry.accounts.portfolio()

print("\nCarry Rule Sharpe:", profits_carry.sharpe())
print("EWMAC Rule Sharpe:", profits.sharpe())
```

## Step 9: Instrument-Level Analysis

Let's analyze performance by instrument:

```python
for instrument in ['SOFR', 'US10', 'CORN']:
    # Get P&L for this instrument
    inst_pandl = system.accounts.pandl_for_instrument(instrument)
    
    print(f"\n{instrument}:")
    print(f"  Sharpe: {inst_pandl.sharpe():.2f}")
    print(f"  Ann. Return: {inst_pandl.ann_mean():.2%}")
    print(f"  Ann. Vol: {inst_pandl.ann_std():.2%}")
```

## Step 10: Save Your Work

```python
# Save system cache for faster loading later
system.cache.pickle("my_first_backtest.pck")

# In future session, load it:
# system.cache.unpickle("my_first_backtest.pck")

# Save configuration
system.config.save("my_first_config.yaml")
```

## Full Example Script

Here's the complete script:

```python
#!/usr/bin/env python3
"""
First Backtest Example
"""

from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
from systems.provided.futures_chapter15.basesystem import futures_system
from sysdata.config.configdata import Config
import matplotlib.pyplot as plt

print("=" * 60)
print("PYSYSTEMTRADE FIRST BACKTEST")
print("=" * 60)

# 1. Load data
print("\n1. Loading data...")
data = csvFuturesSimData()
instruments = data.get_instrument_list()
print(f"   Available instruments: {len(instruments)}")

# 2. Create system
print("\n2. Creating system...")
system = futures_system()
print(f"   System stages: {system.stage_names}")

# 3. Get positions
print("\n3. Getting positions...")
positions = system.portfolio.get_notional_position("SOFR")
print(f"   Current SOFR position: {positions.iloc[-1]:.2f} contracts")

# 4. Calculate performance
print("\n4. Calculating performance...")
profits = system.accounts.portfolio()
print(f"   Sharpe Ratio: {profits.sharpe():.2f}")
print(f"   Annual Return: {profits.ann_mean():.2%}")
print(f"   Annual Volatility: {profits.ann_std():.2%}")
print(f"   Max Drawdown: {profits.max_drawdown():.2%}")

# 5. Plot results
print("\n5. Creating plots...")
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

profits.curve().plot(ax=axes[0])
axes[0].set_title("Portfolio Equity Curve")
axes[0].set_ylabel("Cumulative Returns")

profits.drawdown().plot(ax=axes[1])
axes[1].set_title("Portfolio Drawdown")
axes[1].set_ylabel("Drawdown %")

plt.tight_layout()
plt.savefig("first_backtest_results.png")
print("   Saved plot to first_backtest_results.png")

# 6. Instrument analysis
print("\n6. Instrument-level analysis:")
for instrument in ['SOFR', 'US10', 'CORN']:
    inst_pandl = system.accounts.pandl_for_instrument(instrument)
    print(f"   {instrument}: Sharpe {inst_pandl.sharpe():.2f}")

print("\n" + "=" * 60)
print("BACKTEST COMPLETE")
print("=" * 60)
```

## Next Steps

Now that you've run your first backtest:

1. **Learn More**: Read the [Backtesting Guide](../backtesting/backtesting_guide.md)
2. **Create Custom Rules**: See [Trading Rules](../backtesting/trading_rules.md)
3. **Understand Data**: Explore [Data Management](../data_management/data_overview.md)
4. **Go Live**: When ready, check [Production Setup](../production_trading/production_setup.md)

## Common Issues

**Import Error**: Make sure you've activated your virtual environment

**No Data**: Check that CSV files are in `data/futures/adjusted_prices_csv/`

**Memory Error**: Reduce number of instruments in config

**Slow Performance**: Use cache.pickle() to save intermediate results

## Exercise

Try modifying the script to:
1. Test on different instruments
2. Change the volatility target
3. Compare different trading rules
4. Add more stages to the system
