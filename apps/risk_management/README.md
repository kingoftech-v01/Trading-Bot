# Risk Management App

Position sizing, stop loss/take profit calculation, and risk control.

## Features

- **Position Sizing**: Risk-based position size calculation
- **Stop Loss**: ATR, percentage, S/R, and swing-based methods
- **Take Profit**: R:R, S/R, ATR, and Fibonacci-based methods
- **Daily Tracking**: Track daily risk exposure and limits

## Usage

```python
from apps.risk_management.services import RiskManager

manager = RiskManager()
result = manager.calculate_trade_parameters(
    entry_price=50000,
    direction='buy',
    atr=500,
)

if result.success:
    print(f"Position size: {result.data['position_size']}")
    print(f"Stop loss: {result.data['stop_loss']}")
    print(f"Take profit: {result.data['take_profit']}")
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/risk/profiles/` | List profiles |
| POST | `/api/v1/risk/calculate/` | Calculate position |
| GET | `/api/v1/risk/summary/` | Get risk summary |
