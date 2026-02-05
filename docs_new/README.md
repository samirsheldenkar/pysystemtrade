# pysystemtrade Documentation

This is the comprehensive documentation for **pysystemtrade** - a Python-based systematic futures trading framework.

## Documentation Structure

```
docs_new/
├── README.md                          # This file
├── index.md                           # Main documentation index
│
├── getting_started/                   # Getting started guides
│   ├── index.md                      # Quick start overview
│   └── installation.md               # Detailed installation
│
├── core_concepts/                     # Core concepts and architecture
│   ├── architecture.md               # System architecture overview
│   ├── system_stages.md              # Understanding stages
│   ├── data_flow.md                  # Data flow and management
│   └── configuration.md              # Configuration system
│
├── backtesting/                       # Backtesting documentation
│   ├── backtesting_guide.md          # Complete backtesting guide
│   └── trading_rules.md              # Trading rules reference
│
├── data_management/                   # Data management
│   └── data_overview.md              # Data management overview
│
├── production_trading/                # Production trading
│   └── production_setup.md           # Production setup guide
│
├── broker_integration/                # Broker integration
│   └── interactive_brokers.md        # IB setup guide
│
├── api_reference/                     # API reference
│   └── systems_module.md             # Systems module API
│
└── examples_tutorials/                # Examples and tutorials
    └── first_backtest.md             # First backtest tutorial
```

## Quick Navigation

### For New Users
1. Start with [Getting Started](getting_started/index.md)
2. Follow the [First Backtest Tutorial](examples_tutorials/first_backtest.md)
3. Read [Core Concepts - Architecture](core_concepts/architecture.md)

### For Backtesters
1. [Backtesting Guide](backtesting/backtesting_guide.md)
2. [Trading Rules](backtesting/trading_rules.md)
3. [Configuration System](core_concepts/configuration.md)

### For Production Users
1. [Production Setup](production_trading/production_setup.md)
2. [Data Management](data_management/data_overview.md)
3. [Interactive Brokers](broker_integration/interactive_brokers.md)

### For Developers
1. [API Reference](api_reference/systems_module.md)
2. [Data Flow](core_concepts/data_flow.md)
3. [System Stages](core_concepts/system_stages.md)

## Key Features Documented

### Backtesting
- Pre-baked systems (Chapter 15, examples)
- Custom system construction
- Trading rules (EWMAC, Carry, Breakout, etc.)
- Portfolio construction and optimization
- Performance analysis and statistics
- Caching for performance

### Data Management
- Multiple storage backends (CSV, MongoDB, Parquet)
- Futures data workflow
- Instrument configuration
- Roll calendar management
- FX data handling

### Production Trading
- Interactive Brokers integration
- Order management and execution
- Position tracking
- Risk management and overrides
- Daily workflow automation
- Monitoring and reporting

### Architecture
- Stage-based system design
- Data flow pipeline
- Configuration hierarchy
- Caching system
- Extensible framework

## Version Information

- **Version**: 1.8.2
- **Last Updated**: 2024-11-06
- **Python Required**: 3.10+
- **Author**: Rob Carver
- **License**: GNU v3

## External Resources

- **GitHub**: https://github.com/robcarver17/pysystemtrade
- **Author's Blog**: https://qoppac.blogspot.com/p/pysystemtrade.html
- **Book**: [Systematic Trading](https://www.systematicmoney.org/systematic-trading)
- **Issues**: https://github.com/robcarver17/pysystemtrade/issues

## Important Disclaimer

**WARNING**: All financial trading offers the possibility of loss. Leveraged trading, such as futures trading, may result in you losing all your money, and still owing more. Backtested results are no guarantee of future performance. No warranty is offered or implied for this software. Use at your own risk.

## Contributing

This documentation is open source. To contribute:

1. Fork the repository
2. Make documentation improvements
3. Submit a pull request

Please follow the existing structure and style when adding content.

## Documentation Status

This documentation is a complete rewrite designed to be:
- **Comprehensive**: Covers all major aspects of the framework
- **Structured**: Organized logically from beginner to advanced
- **Practical**: Includes examples and tutorials
- **Up-to-date**: Reflects version 1.8.2

## TODO

Future documentation additions:
- [ ] Complete data management section (futures_data.md, fx_data.md, data_sources.md)
- [ ] Production workflow and monitoring guides
- [ ] API reference for sysdata, sysobjects, sysproduction modules
- [ ] More tutorials and examples
- [ ] Troubleshooting guide
- [ ] FAQ section
- [ ] Glossary

---

**Note**: This is the new structured documentation for pysystemtrade. The old documentation in `docs/` is deprecated but retained for reference during the transition period.
