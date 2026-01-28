# Orders App

Trade execution and position management.

## Models
- **Order**: Trade orders (market, limit, stop)
- **Trade**: Completed trades with P&L tracking
- **Position**: Current open positions

## Services
- **OrderExecutor**: Creates and executes orders
- **PositionManager**: Manages open positions, checks SL/TP
- **TradeLogger**: Trade statistics and history

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/orders/orders/` | List orders |
| POST | `/api/v1/orders/create-order/` | Create order |
| GET | `/api/v1/orders/trades/` | List trades |
| GET | `/api/v1/orders/trades/statistics/` | Trade stats |
| GET | `/api/v1/orders/positions/` | List positions |
| GET | `/api/v1/orders/positions/summary/` | Position summary |
