# Market Data App

Market data collection and storage for the Trading Bot platform.

## Purpose

The Market Data app handles:
- Exchange configuration and management
- Trading pair definitions
- OHLCV (candlestick) data collection
- Cross-pair correlation tracking
- Data cleaning and validation

## Models

### Exchange
Supported data sources:
- CoinAPI (REST API for forex/crypto)
- Binance (via CCXT)
- MetaTrader 5 (forex broker)

### TradingPair
Trading pair definitions with:
- Symbol (e.g., EURUSD, BTCUSD)
- Base/Quote currency
- Pip value and lot sizes
- Forex/Crypto classification

### OHLCV
Candlestick data:
- Open, High, Low, Close, Volume
- Multiple timeframes (15m, 1h, 4h, 1d)
- Bullish/Bearish indicators

### CorrelationMatrix
Cross-pair correlations for multi-pair validation.

## Services

### DataFetcher
Orchestrates data collection from all exchanges.

```python
from apps.market_data.services import DataFetcher

fetcher = DataFetcher()
result = fetcher.fetch_ohlcv(
    trading_pair=pair,
    timeframe='1h',
    limit=100
)
```

### CoinAPIService
Direct integration with CoinAPI REST API.

### DataCleaner
Validates and cleans OHLCV data:
- Gap detection
- Outlier removal
- OHLCV validation

## API Endpoints

### Exchanges
- `GET /api/v1/market-data/exchanges/` - List exchanges
- `GET /api/v1/market-data/exchanges/{id}/` - Exchange detail
- `POST /api/v1/market-data/exchanges/` - Create exchange

### Trading Pairs
- `GET /api/v1/market-data/trading-pairs/` - List pairs
- `GET /api/v1/market-data/trading-pairs/forex/` - Forex pairs only
- `GET /api/v1/market-data/trading-pairs/crypto/` - Crypto pairs only

### OHLCV
- `GET /api/v1/market-data/ohlcv/` - List OHLCV data
- `GET /api/v1/market-data/ohlcv/chart-data/` - Chart-formatted data
- `GET /api/v1/market-data/ohlcv/latest/` - Latest candle

### Data Fetch
- `POST /api/v1/market-data/fetch/` - Trigger data fetch

## Frontend URLs

- `/market-data/` - Dashboard
- `/market-data/exchanges/` - Exchange list
- `/market-data/trading-pairs/` - Trading pair list
- `/market-data/chart/{id}/` - OHLCV chart

## Celery Tasks

### fetch_all_pairs_data
Fetches data for all active pairs (runs every 5 minutes).

### calculate_correlations
Calculates correlation matrix (runs daily).

### cleanup_old_data
Removes old OHLCV data (runs weekly).

## Testing

```bash
python manage.py test apps.market_data
```
