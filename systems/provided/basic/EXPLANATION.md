# Basic Futures System Explanation

The `systems/provided/basic/` directory provides a minimum viable system structure without any predefined trading rules. It is intended as a starting point for building custom systems.

## Strategy Step-by-Step

This system is essentially a shell. Without trading rules, it will not generate any signals or positions. It consists of the following standard stages:

1.  **Rules**: The placeholder for trading rule logic.
2.  **Forecast Scaling and Capping**: A stage to ensure forecasts are on a consistent scale.
3.  **Forecast Combination**: Merges multiple rule outputs.
4.  **Raw Data**: Accesses the underlying price and volatility data.
5.  **Position Sizing**: Converts forecasts into instrument positions based on risk parameters.
6.  **Portfolios**: Aggregates positions across instruments.
7.  **Account**: Tracks simulated performance.

## Instruments Covered

By default, the `basic_csv_futures_system` reads data from the available CSV files in the data directory. The instruments covered depend entirely on the provided data and configuration.

## Parameterisations

The basic system uses default parameters from the framework unless a configuration is provided. To use this system, you would typically pass a `Config` object with your own rules and instrument weights.
