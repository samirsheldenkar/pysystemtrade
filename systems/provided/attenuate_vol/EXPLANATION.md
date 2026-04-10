# Volatility Attenuation Explanation

The `systems/provided/attenuate_vol/` directory provides a specialized system stage (`volAttenForecastScaleCap`) used to reduce trading signals during periods of high relative volatility.

## What it Does

1.  **Monitors Volatility**: It calculates the ratio between recent volatility and long-term historical volatility.
2.  **Attenuates Forecasts**: If recent volatility is significantly higher than historical norms, it scales down the trading forecasts.
3.  **Prevents Over-trading**: This helps avoid entering large positions during unstable or highly volatile market conditions where the risk of rapid loss is elevated.

## Usage

This stage is primarily used in more advanced systems like the `rob_system` to provide an extra layer of risk management and to improve the risk-adjusted returns of the portfolio.
