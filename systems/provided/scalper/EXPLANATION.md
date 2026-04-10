# Scalper System Explanation

The `systems/provided/scalper/` directory contains a specialized high-frequency trading system, specifically a mean-reversion runner (`MRRunner`). This system is designed for more active, intra-day trading compared to the daily-frequency trend-following systems elsewhere in the framework.

## Strategy Step-by-Step

The `scalper` operates in a more granular, state-driven manner:

1.  **State Management**: The system maintains a `State` object that tracks current positions, active orders, and recent price action.
2.  **Price Feed**: It uses a real-time price feed (ticks) to calculate a short-term volatility or range estimate.
3.  **Action Logic**: Based on the current `State` and price action, it determines the next action (`ActionFromState`), which could be:
    *   **Entering a trade**: Placing limit orders at the edges of a calculated range.
    *   **Exiting a trade**: Closing positions when a profit target or stop loss is reached.
    *   **Adjusting orders**: Moving limit orders as the price moves.
4.  **Broker Integration**: The `BrokerController` manages the interaction with the broker's API (e.g., Interactive Brokers) to place, cancel, and monitor orders in real-time.
5.  **Heartbeat and Monitoring**: The system runs a continuous loop (`run`), checking the connection and state at very short intervals (seconds).

## Instruments Covered

This system is typically applied to highly liquid futures contracts where scalping is viable. While the instrument can be configured, it is designed for single-instrument execution per runner instance.

## Full Parameterisations

The strategy is parameterized by `StratParameters`, which include:
*   **`range_multiplier`**: Determines how far from the current price limit orders are placed.
*   **`horizon`**: The lookback period for calculating the price range.
*   **`max_position`**: The maximum number of contracts to hold.
*   **`target_profit`**: The profit target for closing a position.
*   **`stop_loss`**: The risk limit for closing a position.
*   **`time_between_heartbeats`**: The frequency of the main control loop.

Configuration details are found in `configuration.py` and can often be modified interactively during the runner's startup phase.
