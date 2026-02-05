# Getting Started with pysystemtrade

Welcome to pysystemtrade! This guide will help you get up and running with the framework.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10 or newer** installed
- **Git** installed
- Basic familiarity with Python programming
- Understanding of systematic trading concepts (helpful but not required)

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/robcarver17/pysystemtrade.git
cd pysystemtrade
```

### Step 2: Create a Virtual Environment

Using `venv` (recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Using `uv` (faster alternative):
```bash
uv venv --python 3.10
source .venv/bin/activate
```

### Step 3: Install Dependencies

Standard installation:
```bash
pip install --upgrade pip setuptools
python -m pip install .
```

Development installation (includes test dependencies):
```bash
python -m pip install --editable '.[dev]'
```

### Step 4: Verify Installation

```bash
python
>>> from sysdata.sim.csv_futures_sim_data import csvFuturesSimData
>>> data = csvFuturesSimData()
>>> data
```

You should see output indicating the number of instruments available (e.g., "csvFuturesSimData object with 249 instruments").

## Your First Backtest

Let's run a simple backtest to verify everything is working:

```python
from systems.provided.futures_chapter15.basesystem import futures_system

# Create the system (uses default CSV data)
system = futures_system()

# Get position for a specific instrument
positions = system.portfolio.get_notional_position("EUROSTX")
print(positions.tail())

# See performance statistics
profits = system.accounts.portfolio()
print(profits.percent.stats())
```

## Next Steps

1. **Learn the Basics**: Read the [Core Concepts](../core_concepts/architecture.md) section
2. **Explore Backtesting**: Follow the [Backtesting Guide](../backtesting/backtesting_guide.md)
3. **Understand Data**: Review [Data Management](../data_management/data_overview.md)
4. **Go Live**: When ready, check [Production Trading](../production_trading/production_setup.md)

## Common Issues

### Import Errors
Ensure you've activated your virtual environment and installed the package correctly.

### Missing Data
The default CSV data may be outdated. For production use, you'll need to set up your own data sources (see [Data Management](../data_management/data_overview.md)).

### MongoDB Connection
For production or database-based backtesting, you'll need MongoDB installed and running.

## Getting Help

- **GitHub Issues**: https://github.com/robcarver17/pysystemtrade/issues
- **Discussions**: Use GitHub Discussions for questions
- **Blog**: https://qoppac.blogspot.com/p/pysystemtrade.html

**Note**: This is an open-source project. While the author welcomes feedback on confusing errors and documentation, extensive technical support is not provided.
