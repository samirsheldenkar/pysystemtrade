# Trading Rules Explanation

The `systems/provided/rules/` directory contains various trading rules (forecast generators) that can be used as components in a trading system. These rules process price, carry, or return data into a forecast signal (typically scaled to ±20).

## Common Trading Rules

### EWMAC (Exponentially Weighted Moving Average Crossover)
*   **What it does**: A trend-following rule that compares a fast moving average to a slow moving average. A positive crossover (fast above slow) generates a long signal.
*   **File**: `ewmac.py`
*   **Parameters**: `Lfast` (Fast span), `Lslow` (Slow span).

### Carry
*   **What it does**: Measures the yield or cost of holding a futures contract (e.g., from the roll yield). A positive carry generates a long signal.
*   **File**: `carry.py`
*   **Parameters**: `smooth_days` (Period to smooth the carry calculation).

### Breakout
*   **What it does**: Generates signals based on whether the current price has broken out of a historical range (highest/lowest price over a lookback period).
*   **File**: `breakout.py`
*   **Parameters**: `lookback` (Lookback period in days).

### Relative Momentum (`rel_mom.py`)
*   **What it does**: Measures momentum relative to other instruments in an asset class or the overall market.
*   **Parameters**: `horizon` (Lookback period).

### Cross-Sectional Mean Reversion (`cs_mr.py`)
*   **What it does**: Generates signals based on an instrument's relative return compared to a group, expecting extreme performers to revert to the mean.
*   **Parameters**: `horizon` (Lookback period).

### Acceleration (`accel.py`)
*   **What it does**: Measures the "momentum of momentum" to identify accelerating trends.

### MR Wings (`mr_wings.py`)
*   **What it does**: A mean-reversion rule specifically designed for extreme price moves (the "wings" of the distribution).
