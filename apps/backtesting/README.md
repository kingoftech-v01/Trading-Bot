# Backtesting App

Historical strategy testing framework for the trading bot.

## Features
- Run backtests on historical data
- Calculate performance metrics (Sharpe, Sortino, max drawdown)
- Track individual trades and equity curve
- Compare different configurations

## Usage

```python
from apps.backtesting.services import Backtester
from apps.backtesting.models import BacktestRun

# Create backtest
backtest = BacktestRun.objects.create(
    name='Test Strategy',
    trading_pair=pair,
    timeframe='1h',
    start_date=start,
    end_date=end,
    initial_balance=10000,
)

# Run backtest
backtester = Backtester()
result = backtester.run_backtest(backtest)
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/backtesting/backtests/` | List backtests |
| POST | `/api/v1/backtesting/create/` | Create backtest |
| POST | `/api/v1/backtesting/backtests/{id}/run/` | Run backtest |
| GET | `/api/v1/backtesting/backtests/{id}/results/` | Get results |
