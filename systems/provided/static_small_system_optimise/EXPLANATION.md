# Static Small System Optimisation Explanation

This is a utility for optimizing the selection of instruments for a trading system with limited capital. It helps determine which markets are most suitable based on their risk-adjusted returns (Sharpe Ratio), correlation, and trading costs.

## Strategy Step-by-Step

The optimization process follows a "greedy" search algorithm:

1.  **Calculate Individual Performance**: The tool calculates the net Sharpe Ratio (SR) for each available instrument, taking into account expected returns, trading costs, and a "size penalty" for small positions.
2.  **Find Best Starting Market**: It selects the instrument with the highest net SR as the first market in the portfolio.
3.  **Iterative Selection**: It repeatedly adds the next best instrument that improves the overall portfolio SR, considering:
    *   **Correlation**: Markets that are less correlated with the existing portfolio are preferred.
    *   **Diversification**: The benefit of adding more markets against the cost of smaller, less efficient positions.
4.  **Stopping Criteria**: The process stops when adding more instruments no longer significantly improves (or starts to decrease) the portfolio's expected SR.

## Instruments Covered

The tool can be applied to any set of instruments available in the `pysystemtrade` framework. It uses the `System` object to access price and volatility data for all potential candidates.

## Full Parameterisations

The optimization is controlled by several key parameters:
*   **`capital`**: The total notional trading capital (default $500,000).
*   **`max_instrument_weight`**: The maximum weight allowed for any single instrument (default 5%).
*   **`notional_starting_IDM`**: The assumed Instrument Diversification Multiplier.
*   **`cost_multiplier`**: A factor to scale the estimated trading costs.
*   **`size_penalty`**: A function that penalizes positions that are too small to be traded efficiently with discrete contracts.
