# Futures Data Validation Summary

A full scan across all 252 consolidated futures markets was completed. We looked for missing data (>10 day gaps in trading) and anomalous price spikes (>25% absolute daily return).

**Total Flags**: 17125 historical anomalies.

Many of these are normal artifacts in deep historical data (e.g., thinly traded periods from 20-30 years ago or rolling behavior in unadjusted series). Below we break them down to help identify if any recent consolidation errors exist.

## Recent Anomalies (2024 - 2026)

These occurred during the period corresponding to the newly consolidated data and warrant review:

```text
[GAS_US_mini - Adjusted Prices] SPIKE of 120.74% on 2024-03-31
[VIX - Adjusted Prices] SPIKE of 29.81% on 2024-03-28
```

## Historical Anomalies by Instrument

| Instrument | Gaps (>10d) | Spikes (>25%) |
|---|---|---|
| OATIES | 0 | 1937 |
| GASOILINE_micro | 0 | 1929 |
| GASOIL | 0 | 1425 |
| GASOILINE | 0 | 1360 |
| HEATOIL | 0 | 885 |
| COTTON2 | 0 | 806 |
| SOYMEAL | 0 | 806 |
| HEATOIL-ICE | 0 | 797 |
| SOYBEAN | 0 | 794 |
| BRENT_W | 0 | 768 |
| CRUDE_W_mini | 0 | 460 |
| GILT | 0 | 433 |
| CRUDE_W_micro | 0 | 420 |
| US10 | 0 | 351 |
| LEANHOG | 0 | 337 |
| SUGAR_WHITE | 0 | 288 |
| OMX | 12 | 271 |
| COCOA_LDN | 0 | 235 |
| HANG | 0 | 209 |
| WHEAT_ICE | 0 | 181 |
| ZAR | 4 | 176 |
| OJ | 0 | 173 |
| CRUDE_W | 0 | 164 |
| COAL | 0 | 156 |
| IBEX_mini | 0 | 140 |
| IBEX | 0 | 135 |
| SOYBEAN_mini | 0 | 132 |
| BUTTER | 0 | 125 |
| COTTON | 2 | 114 |
| ETHANOL | 0 | 111 |
| WHEY | 0 | 105 |
| US20 | 0 | 102 |
| BRE | 2 | 95 |
| CRUDE_ICE | 0 | 92 |
| IRON | 0 | 82 |
| MILLWHEAT | 0 | 78 |
| STEEL | 0 | 52 |
| MXP | 0 | 34 |
| MSCISING | 0 | 33 |
| COAL-GEORDIE | 0 | 30 |
| RUR | 0 | 25 |
| MILKWET | 24 | 0 |
| HANG_mini | 0 | 12 |
| EURO600 | 0 | 11 |
| GAS_US_mini | 0 | 10 |
| SGX | 2 | 8 |
| GAS_US | 0 | 9 |
| EUROSTX-LARGE | 8 | 0 |
| MSCITAIWAN | 0 | 8 |
| PLN | 8 | 0 |
| BRENT-LAST | 0 | 7 |
| EU-DIV30 | 4 | 3 |
| FTSECHINAH | 6 | 0 |
| EU-BANKS | 0 | 5 |
| SMI-MID | 2 | 3 |
| EU-DJ-UTIL | 4 | 0 |
| EU-REALESTATE | 4 | 0 |
| EUROSTX200-LARGE | 4 | 0 |
| FTSEINDO | 4 | 0 |
| FTSEVIET | 4 | 0 |
| GAS-PEN | 0 | 4 |
| GICS | 4 | 0 |
| HANGENT_mini | 0 | 4 |
| KR10 | 4 | 0 |
| KR3 | 4 | 0 |
| MSCIEAFA | 0 | 4 |
| US-INDUSTRY | 4 | 0 |
| US-MATERIAL | 4 | 0 |
| VIX | 0 | 4 |
| VIX_mini | 0 | 3 |
| ALUMINIUM | 2 | 0 |
| BBCOMM | 2 | 0 |
| BOVESPA | 2 | 0 |
| CH10 | 2 | 0 |
| CNH-onshore | 2 | 0 |
| ETHEREUM | 0 | 2 |
| EU-DJ-TECH | 2 | 0 |
| EU-OIL | 2 | 0 |
| EU-TECH | 2 | 0 |
| EU-TRAVEL | 2 | 0 |
| JGB | 2 | 0 |
| JGB-mini | 2 | 0 |
| JP-REALESTATE | 2 | 0 |
| KOSPI | 2 | 0 |
| KOSPI_mini | 2 | 0 |
| MILK | 2 | 0 |
| MILKDRY | 2 | 0 |
| MUMMY | 2 | 0 |
| NIKKEI | 2 | 0 |
| NIKKEI400 | 2 | 0 |
| SEK | 2 | 0 |
| SONIA3 | 2 | 0 |
| TOPIX | 2 | 0 |
| US-ENERGY | 2 | 0 |
| US-FINANCE | 2 | 0 |
| US-HEALTH | 2 | 0 |
| US-REALESTATE | 2 | 0 |
| US-STAPLES | 2 | 0 |
| US-UTILS | 2 | 0 |
| BITCOIN | 0 | 1 |
| ETHER-micro | 0 | 1 |
| EU-DJ-TELECOM | 0 | 1 |
| FTSE100 | 0 | 1 |
| GAS-LAST | 0 | 1 |
| HIGHYIELD | 0 | 1 |
| RICE | 0 | 1 |
| SP500 | 0 | 1 |
| SP500_micro | 0 | 1 |
| V2X | 0 | 1 |
| WHEAT | 0 | 1 |
| WHEAT_mini | 0 | 1 |
