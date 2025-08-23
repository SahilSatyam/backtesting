# Migration Guide: Unified Data Fetcher

## Overview

We've consolidated the data fetching logic into a single, more reliable implementation using `yfinance`. The old implementations (`DataFetcher` and `AlternativeDataFetcher`) are now deprecated and will be removed in a future version.

## Key Changes

1. **New Unified Fetcher**: `UnifiedDataFetcher` combines the best features of both previous implementations
2. **Removed Dependencies**:
   - Removed `nsepy` dependency
   - Simplified to use only `yfinance`
3. **Improved Reliability**:
   - Better error handling and retries
   - Multiple symbol format support
   - Standardized data format

## How to Update Your Code

### Before (Old Way)

```python
from data.fetcher import data_fetcher
# or
from data.alternative_fetcher import alternative_data_fetcher

data = data_fetcher.fetch_nse_data("RELIANCE", start_date, end_date)
# or
data = alternative_data_fetcher.fetch_yahoo_data("RELIANCE", start_date, end_date)
```

### After (New Way)

```python
from data import get_fetcher

# Get the fetcher instance
fetcher = get_fetcher()

# Fetch data for a single symbol
data = fetcher.fetch_stock_data("RELIANCE", start_date, end_date)

# Or fetch multiple symbols at once
symbols = ["RELIANCE", "TCS", "HDFCBANK"]
all_data = fetcher.fetch_multiple_stocks(symbols, start_date, end_date)
```

### Data Format

The new fetcher returns data in a standardized format with the following columns:
- `date`: The trading date
- `open`: Opening price
- `high`: Highest price during the day
- `low`: Lowest price during the day
- `close`: Closing price
- `volume`: Trading volume
- `dividends`: Dividend payments (if any)
- `splits`: Stock splits (if any)
- `symbol`: The stock symbol

## Benefits of the New Implementation

1. **Simpler Codebase**: Single implementation to maintain
2. **More Reliable**: Better error handling and retry logic
3. **Consistent Data**: Standardized format across all symbols
4. **Better Performance**: Optimized for batch operations

## Next Steps

1. Update your code to use the new `UnifiedDataFetcher`
2. Remove any direct dependencies on `nsepy`
3. Test your application with the new implementation
4. Report any issues or unexpected behavior

## Deprecation Notice

The old fetchers (`DataFetcher` and `AlternativeDataFetcher`) are now deprecated and will be removed in a future version. Please update your code to use the new `UnifiedDataFetcher` as soon as possible.
