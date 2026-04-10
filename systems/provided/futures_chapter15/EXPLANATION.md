# Futures System (Chapter 15) Explanation

This system is a pre-configured implementation of the trading strategy described in Chapter 15 of "Systematic Trading" by Robert Carver.

## Strategy Step-by-Step

1.  **Trading Rules**: The system calculates raw forecasts using several trading rules:
    *   **EWMAC (Exponentially Weighted Moving Average Crossover)**: Used at multiple speeds (2/8, 4/16, 8/32, 16/64, 32/128, 64/256).
    *   **Carry**: A rule that captures the yield or cost of holding a futures contract.
2.  **Forecast Scaling and Capping**:
    *   Raw forecasts from each rule are scaled to have a target average absolute value (default 10).
    *   Forecasts are capped (default at ±20) to prevent extreme positions.
3.  **Forecast Combination**:
    *   The scaled and capped forecasts for each instrument are combined using pre-defined weights.
    *   A diversification multiplier is applied to account for the lack of perfect correlation between rules.
4.  **Position Sizing**:
    *   The combined forecast is converted into a target position size.
    *   This takes into account the instrument's volatility, the target portfolio volatility (default 20%), and the notional trading capital (default $250,000).
5.  **Portfolio Creation**:
    *   Target positions for all instruments are aggregated.
    *   Instrument weights are applied to determine the allocation to each market.
    *   An instrument diversification multiplier is applied.
6.  **Account Management**:
    *   The system tracks the simulated performance, including P&L, trades, and commissions.

## Instruments Covered

The default configuration includes the following instruments:
*   **SOFR**: Secured Overnight Financing Rate (Interest Rates)
*   **US10**: 10-Year US Treasury Note (Interest Rates)
*   **EUROSTX**: Euro Stoxx 50 Index (Equities)
*   **V2X**: EURO STOXX 50 Volatility Index (Volatility)
*   **MXP**: Mexican Peso (FX)
*   **CORN**: Corn (Commodities)

## Full Parameterisations

The system parameters are defined in `futuresconfig.yaml`. Key parameters include:

### Trading Rules
| Rule | Lfast | Lslow | Forecast Scalar |
| :--- | :--- | :--- | :--- |
| ewmac2_8 | 2 | 8 | 10.6 |
| ewmac4_16 | 4 | 16 | 7.5 |
| ewmac8_32 | 8 | 32 | 5.3 |
| ewmac16_64 | 16 | 64 | 3.75 |
| ewmac32_128 | 32 | 128 | 2.65 |
| ewmac64_256 | 64 | 256 | 1.87 |
| carry | N/A | N/A | 30.0 (smooth_days: 90) |

### Forecast Combination
*   **Weights**:
    *   ewmac16_64: 0.21
    *   ewmac32_128: 0.08
    *   ewmac64_256: 0.21
    *   carry: 0.50
*   **Forecast Diversification Multiplier**: 1.31
*   **Forecast Cap**: 20.0

### Capital and Risk
*   **Notional Trading Capital**: $250,000
*   **Percentage Vol Target**: 20.0%
*   **Base Currency**: USD

### Portfolio Weights
*   SOFR: 0.117
*   US10: 0.117
*   EUROSTX: 0.20
*   V2X: 0.098
*   MXP: 0.233
*   CORN: 0.233
*   **Instrument Diversification Multiplier**: 1.89
