# System Architecture

This document provides an overview of pysystemtrade's architecture and how its components work together.

## High-Level Overview

pysystemtrade follows a modular, stage-based architecture designed for both backtesting and live trading. The system is organized into several key layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Production Scripts                        │
│  (Scheduling, Order Generation, Execution, Monitoring)      │
├─────────────────────────────────────────────────────────────┤
│                    Backtesting System                        │
│  (Stages: Rules → Scale/Cap → Combine → Portfolio → P&L)   │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  (Data Blobs → Data Sources → Storage Backends)             │
├─────────────────────────────────────────────────────────────┤
│                    Broker Interface                          │
│  (Interactive Brokers / Other Brokers)                      │
└─────────────────────────────────────────────────────────────┘
```

## Core Modules

### 1. Systems Module (`systems/`)

The heart of the backtesting framework. Systems are composed of **stages** that process data sequentially:

- **basesystem.py**: Core system class that orchestrates stages
- **stage.py**: Base class for all stages
- **forecasting.py**: Trading rule execution
- **forecast_scale_cap.py**: Forecast scaling and capping
- **forecast_combine.py**: Combining multiple forecasts
- **positionsizing.py**: Position size calculation
- **portfolio.py**: Portfolio construction
- **accounts**: P&L calculation and reporting

**Key Concept**: Stages are connected through a parent-child relationship, with each stage able to access its parent system's data and other stages.

### 2. Data Module (`sysdata/`)

Provides data access abstraction:

- **base_data.py**: Base class for all data objects
- **data_blob.py**: Container for multiple data sources
- **sim/**: Simulation data for backtesting
- **mongodb/**: MongoDB storage implementations
- **parquet/**: Parquet file storage
- **csv/**: CSV file storage
- **futures/**: Futures-specific data objects
- **production/**: Production-only data objects

### 3. Objects Module (`sysobjects/`)

Data structures representing trading entities:

- **instruments.py**: Futures instrument definitions
- **contracts.py**: Futures contract specifications
- **adjusted_prices.py**: Back-adjusted price series
- **multiple_prices.py**: Multi-contract price data
- **roll_calendars.py**: Roll schedule management
- **production/**: Order and position objects

### 4. Broker Module (`sysbrokers/`)

Broker integration layer:

- **IB/**: Interactive Brokers implementation
- **broker_factory.py**: Broker connection factory
- **broker_*_data.py**: Broker-specific data interfaces

### 5. Production Module (`sysproduction/`)

Live trading components:

- **run_*.py**: Scheduled execution scripts
- **data/**: Production data interfaces
- **interactive_*.py**: Interactive management tools
- **update_*.py**: Data update scripts

### 6. Core Utilities (`syscore/`)

Shared utility functions:

- **dateutils.py**: Date and time handling
- **pandas/**: Pandas DataFrame utilities
- **cache.py**: Caching mechanisms
- **fileutils.py**: File operations

### 7. Quantitative Analysis (`sysquant/`)

Statistical and mathematical tools:

- **estimators/**: Volatility, correlation estimators
- **optimisation/**: Portfolio optimization
- **returns.py**: Return calculations

### 8. Execution Module (`sysexecution/`)

Order execution management:

- **orders/**: Order types and definitions
- **order_stacks/**: Order queue management
- **stack_handler/**: Order processing pipeline
- **algos/**: Execution algorithms

## System Stages in Detail

A typical futures trading system includes these stages:

### 1. Raw Data Stage (`rawdata`)
- **Purpose**: Preprocess raw price data
- **Key Methods**: `daily_prices()`, `get_instrument_raw_carry_data()`
- **Output**: Cleaned price series

### 2. Rules Stage (`rules`)
- **Purpose**: Generate trading signals (forecasts)
- **Key Methods**: `get_raw_forecast()`, `trading_rules()`
- **Output**: Raw forecast values

### 3. Forecast Scale and Cap Stage (`forecastScaleCap`)
- **Purpose**: Normalize forecasts and apply limits
- **Key Methods**: `get_forecast_scalar()`, `get_capped_forecast()`
- **Output**: Scaled forecasts (target abs value = 10)

### 4. Forecast Combine Stage (`combForecast`)
- **Purpose**: Aggregate multiple forecasts
- **Key Methods**: `get_combined_forecast()`, `get_forecast_weights()`
- **Output**: Single combined forecast per instrument

### 5. Position Sizing Stage (`positionSize`)
- **Purpose**: Calculate position sizes based on volatility
- **Key Methods**: `get_subsystem_position()`, `get_volatility_scalar()`
- **Output**: Subsystem positions

### 6. Portfolio Stage (`portfolio`)
- **Purpose**: Combine instruments into portfolio
- **Key Methods**: `get_notional_position()`, `get_instrument_weights()`
- **Output**: Final portfolio positions

### 7. Accounts Stage (`accounts`)
- **Purpose**: Calculate P&L and performance metrics
- **Key Methods**: `portfolio()`, `pandl_for_instrument()`
- **Output**: Account curves and statistics

## Data Flow

```
Raw Prices → Trading Rules → Scaled Forecasts → Combined Forecast → 
Subsystem Position → Portfolio Position → P&L Accounting
```

Each stage can be configured independently through YAML configuration files or Python dictionaries.

## Configuration Hierarchy

Configuration is resolved in this order (later overrides earlier):

1. **Project Defaults** (`sysdata/config/defaults.yaml`)
2. **Private Config** (`private/private_config.yaml`)
3. **System Config** (`private/your_system/config.yaml`)
4. **Runtime Config** (Python dictionary passed to system)

## Caching System

pysystemtrade uses sophisticated caching to avoid redundant calculations:

- **System Cache**: Each system has a cache storing intermediate results
- **Pickling**: Save/load cache for expensive calculations
- **Invalidation**: Automatic cache invalidation when inputs change

Example:
```python
# Save system state
system.cache.pickle("my_system_cache.pck")

# Load in new session
system.cache.unpickle("my_system_cache.pck")
```

## Production Architecture

In production, additional components are active:

```
Scheduled Scripts → Data Updates → System Backtest → 
Order Generation → Order Stack → Broker Execution → 
Fill Processing → Position Updates → Reporting
```

### Key Production Components:

1. **Process Control** (`syscontrol/`): Monitors and manages running processes
2. **Order Stack** (`sysexecution/order_stacks/`): Manages order lifecycle
3. **Stack Handler** (`sysexecution/stack_handler/`): Processes orders through execution
4. **Interactive Tools**: Manual intervention and diagnostics

## Extensibility

The architecture supports extension at multiple points:

### Adding a New Trading Rule
```python
from systems.trading_rules import TradingRule

def my_custom_rule(price, param1=10):
    return price.ewm(span=param1).mean()

rule = TradingRule(my_custom_rule)
```

### Creating a Custom Stage
```python
from systems.stage import SystemStage

class MyCustomStage(SystemStage):
    @property
    def name(self):
        return "myStage"
    
    def some_method(self, instrument_code):
        # Access other stages
        forecasts = self.parent.rules.get_capped_forecast(instrument_code, "ewmac")
        return forecasts * 2
```

### Adding a New Data Source
Implement the data object interface (e.g., `futuresContractPriceData`) for your storage backend.

## Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Composability**: Stages can be combined in various configurations
3. **Abstraction**: Data sources are interchangeable
4. **Testability**: Clear interfaces enable unit testing
5. **Reproducibility**: Configuration-driven behavior ensures consistency

## Next Steps

- Learn about [System Stages](./system_stages.md) in detail
- Understand [Data Flow](./data_flow.md)
- Explore the [Configuration System](./configuration.md)
