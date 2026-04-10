# Dynamic Small System Optimisation Explanation

The `systems/provided/dynamic_small_system_optimise/` directory contains tools for a more advanced, dynamic version of the small system optimization. Unlike the static version, which picks a fixed set of markets, the dynamic version allows the set of instruments to change over time as market conditions and capital availability evolve.

## Strategy Step-by-Step

This approach is more integrated into the trading lifecycle:

1.  **Data Preparation**: The system prepares historical data for all potential instruments, including their returns and trading costs.
2.  **Continuous Optimisation**: At regular intervals (e.g., monthly), the optimizer re-evaluates the optimal set of instruments.
3.  **Greedy Algorithm**: It uses a similar greedy search as the static version to find the best combination of markets, considering current correlations and costs.
4.  **Position Transitions**: It calculates how to transition from the current set of instruments to the new optimal set, trying to minimize unnecessary turnover.
5.  **Optimised Position Stage**: A custom `optimisedPositions` stage is used in the system to calculate the final positions, replacing the standard `Portfolios` and `PositionSizing` logic with the results of the optimization.

## Instruments Covered

This can be applied across the entire range of instruments in the `pysystemtrade` framework, allowing the system to "migrate" across different markets as they become more or less attractive.

## Full Parameterisations

Key parameters for the dynamic optimization include:
*   **`notional_trading_capital`**: The current capital level used to determine position sizes.
*   **`max_risk_limit_sum_abs_risk`**: Total portfolio risk limit.
*   **`max_risk_leverage`**: Maximum allowable leverage.
*   **`greedy_algo`**: Parameters for the greedy market selection algorithm.
*   **`optimisation_frequency`**: How often the portfolio set is re-evaluated.
