# Rob System Explanation

This is a comprehensive trading system used by the author (Robert Carver) for live trading. It is more advanced than the Chapter 15 system, incorporating volatility attenuation and optimized position sizing.

## Strategy Step-by-Step

1.  **Trading Rules**: The system uses a large ensemble of trading rules, including:
    *   **Breakout**: Multiple lookback periods (10, 20, 40, 80, 160, 320 days).
    *   **Relative Momentum**: Horizon-based momentum relative to asset classes.
    *   **Carry**: Multiple smoothing periods (10, 30, 60, 125 days).
    *   **Asset Trend (EWMAC)**: Applied at the asset class level.
    *   **Normalized Momentum**: Volatility-normalized momentum.
    *   **Cross-Sectional Mean Reversion**: Mean reversion across instruments.
2.  **Volatility Attenuation**:
    *   The system applies "attenuation" to certain forecasts. This reduces the forecast strength when recent volatility is high relative to historical volatility, helping to avoid over-trading in unstable markets.
3.  **Forecast Combination**:
    *   Forecasts from all rules are combined for each instrument.
    *   Weights for these rules are pre-defined in the configuration.
4.  **Position Sizing and Optimization**:
    *   Instead of simple weighting, this system uses an **Optimized Position Sizing** stage.
    *   It considers constraints and tries to find an optimal set of positions that balances expected returns (from forecasts) against risk and transaction costs.
5.  **Risk Overlay**:
    *   A final `Risk()` stage monitors the total portfolio risk and can scale down positions if they exceed pre-set leverage or risk limits.

## Instruments Covered

The system covers a very broad range of over 100 instruments across various asset classes, including:
*   **Equities**: AEX, CAC, DAX, DOW, EUROSTX, FTSE, KOSPI, NASDAQ, SMI, SPI, etc.
*   **Fixed Income**: BB3M, BOBL, BTP, BUND, BUXL, FED, JGB, US2, US5, US10, US30, etc.
*   **Commodities**: ALUMINIUM, BRENT, CORN, COTTON, CRUDE, GOLD, IRON, LIVECOW, NATURALGAS, NICKEL, SILVER, SOYBEANS, SUGAR, WHEAT, etc.
*   **FX**: AUD, CAD, CHF, EUR, GBP, JPY, MXN, NZD, etc.
*   **Crypto**: BITCOIN, ETHEREUM.

## Full Parameterisations

The system parameters are defined in `config.yaml` in the `rob_system` directory.

### Key Configuration Sections
*   **`trading_rules`**: Defines all the rules and their specific arguments (e.g., lookback periods).
*   **`use_attenuation`**: List of rules that have volatility attenuation applied.
*   **`forecast_weights`**: Weights used to combine the various trading rules.
*   **`instrument_weights`**: Target weights for each instrument in the portfolio.
*   **`optimisation`**: Parameters for the position optimization engine, including risk limits and cost models.
*   **`volatility_calculation`**: Specific parameters for calculating the volatility used in position sizing.

For the full list of parameters, refer to the 7,000+ line `config.yaml` file.
