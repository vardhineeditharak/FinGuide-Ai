# Code & Sources Reference

## 1. Market Data (Daily)

- NIFTY 50, S&P 500, USD/INR, Gold, Brent, 10Y yields downloaded using `yfinance`.
- Tickers used:
  - NIFTY 50: ^NSEI
  - S&P 500: ^GSPC
  - USD/INR: INR=X
  - Gold (Spot/Futures): GC=F
  - Brent Crude: BZ=F
  - US 10Y Treasury Yield: ^TNX or FRED DGS10
  - India 10Y Yield: (source used if available)

## 2. US Macroeconomic Data (Monthly)

Pulled via Federal Reserve (FRED) series:

- CPI Index (CPIAUCSL)
- Unemployment Rate (UNRATE)
- Fed Funds Rate (FEDFUNDS)
- 10Y Treasury Yield (DGS10)

## 3. India Macroeconomic Data

Collected from publicly available sources:

- CPI, GDP, Unemployment, Repo Rate
- Sources: World Bank Open Data, Indian economic data portals

## 4. Monthly Market Returns

Computed using Python:

- Monthly returns = (Close_this_month - Close_last_month) / Close_last_month
- Monthly FX change = pct_change of USD/INR

## 5. Cleaning Notes

- Missing values for holidays kept as NaN
- Macro NaN for latest months = data not yet published
- No interpolation done for macro series
