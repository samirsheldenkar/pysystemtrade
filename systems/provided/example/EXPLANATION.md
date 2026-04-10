# Example Systems Explanation

The `systems/provided/example/` directory contains several examples of how to configure and run trading systems using the `pysystemtrade` framework.

## Simple System (`simplesystem.py`)

This is a minimal, easy-to-understand system that demonstrates the core components of the framework.

### Strategy Step-by-Step

1.  **Trading Rules**: Calculates raw forecasts using two EWMAC rules (8/32 and 32/128).
2.  **Forecast Scaling**: Scales the raw forecasts to a standard scale.
3.  **Forecast Combination**: Combines the two EWMAC rules with equal weights (50% each).
4.  **Position Sizing**: Calculates position sizes based on volatility, a 25% volatility target, and £500,000 in notional capital.
5.  **Portfolio Creation**: Combines the instruments into a portfolio using target weights.

### Instruments Covered

The default configuration (`simplesystemconfig.yaml`) includes:
*   **SOFR**: Interest Rates (40% weight)
*   **US10**: Interest Rates (10% weight)
*   **CORN**: Commodities (30% weight)
*   **SP500**: Equities (20% weight)

### Key Parameters

*   **Volatility Target**: 25%
*   **Notional Capital**: £500,000
*   **Base Currency**: GBP
*   **Trading Rules**:
    *   `ewmac8_32`: Scalar 5.3
    *   `ewmac32_128`: Scalar 2.65
*   **Diversification Multipliers**:
    *   Forecast: 1.1
    *   Instrument: 1.5

---

## Other Example Systems

### Daily with Order Simulation (`daily_with_order_simulation.py`)
Demonstrates how to run a system with simulated order execution at a daily frequency.

### Hourly with Order Simulation (`hourly_with_order_simulation.py`)
Demonstrates how to run a system with simulated order execution at an hourly frequency, using a more granular data source.
