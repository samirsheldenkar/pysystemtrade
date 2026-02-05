# pysystemtrade Documentation

**Version:** 1.8.2  
**Last Updated:** 2024-11-06

Welcome to the comprehensive documentation for pysystemtrade - a Python-based systematic futures trading framework developed by Rob Carver.

## What is pysystemtrade?

pysystemtrade is an open-source systematic trading framework that implements the principles outlined in Rob Carver's book ["Systematic Trading"](https://www.systematicmoney.org/systematic-trading). It serves as both:

1. **A Backtesting Environment** - Test trading strategies on historical futures data
2. **A Production Trading System** - Fully automated futures trading (primarily for Interactive Brokers)

The framework is actively used by the author for live trading, ensuring continuous development and real-world testing.

## Key Features

- **Complete Trading Pipeline**: From data acquisition to order execution
- **Multiple Trading Rules**: EWMAC, carry, breakout, and more
- **Portfolio Optimization**: Instrument and forecast weight optimization
- **Risk Management**: Built-in position sizing and risk controls
- **Production Ready**: Automated scheduling, monitoring, and reporting
- **Flexible Data Sources**: CSV, MongoDB, Parquet, Interactive Brokers
- **Extensible Architecture**: Easy to add custom trading rules and stages

## Documentation Structure

### [Getting Started](./getting_started/index.md)
- Installation guide
- Quick start tutorial
- First backtest

### [Core Concepts](./core_concepts/architecture.md)
- System architecture
- Understanding stages
- Data flow
- Configuration system

### [Backtesting](./backtesting/backtesting_guide.md)
- Creating backtests
- Trading rules
- Portfolio construction
- Performance analysis

### [Data Management](./data_management/data_overview.md)
- Futures data workflow
- Price data types
- Data sources
- Database setup

### [Production Trading](./production_trading/production_setup.md)
- Production system setup
- Daily workflow
- Order management
- Monitoring and reporting

### [Broker Integration](./broker_integration/interactive_brokers.md)
- Interactive Brokers setup
- Connection management
- Order execution

### [API Reference](./api_reference/systems_module.md)
- Systems module
- Data objects
- Production components

### [Examples & Tutorials](./examples_tutorials/first_backtest.md)
- Step-by-step tutorials
- Example strategies
- Common patterns

### [Reference](./reference/glossary.md)
- Glossary
- Configuration options
- Command reference

## Quick Links

- **GitHub Repository**: https://github.com/robcarver17/pysystemtrade
- **Author's Blog**: https://qoppac.blogspot.com/p/pysystemtrade.html
- **Book**: [Systematic Trading](https://www.systematicmoney.org/systematic-trading)
- **Issues**: https://github.com/robcarver17/pysystemtrade/issues

## Important Disclaimer

**WARNING**: All financial trading offers the possibility of loss. Leveraged trading, such as futures trading, may result in you losing all your money, and still owing more. Backtested results are no guarantee of future performance. No warranty is offered or implied for this software. The author can take no responsibility for any losses caused by live trading using pysystemtrade. Use at your own risk.

## License

GNU v3 - See [LICENSE](../LICENSE) for details.

---

**Note**: This documentation is for pysystemtrade version 1.8.2. Ensure you are using the correct version of the code and documentation together.
