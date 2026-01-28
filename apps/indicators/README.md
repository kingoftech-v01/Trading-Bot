# Indicators App

Technical indicators engine for the Trading Bot platform.

## Purpose

The Indicators app provides:
- 10 technical indicators for trading analysis
- Unified calculation interface
- Indicator result storage
- Combination-specific indicator sets

## Available Indicators

| Indicator | Default Params | Output |
|-----------|---------------|--------|
| RSI | period=14 | rsi, is_overbought, is_oversold |
| MACD | 12, 26, 9 | macd_line, signal_line, histogram |
| ADX | period=14 | adx, plus_di, minus_di |
| Stochastic | 14, 3, 3 | k, d, is_overbought, is_oversold |
| Bollinger | 20, 2 | upper, middle, lower, bandwidth |
| Linear Regression | period=50 | regression_line, slope, r_squared |
| CCI | period=20 | cci, is_overbought, is_oversold |
| ATR | period=14 | atr, atr_percent, is_high_volatility |
| Volume Profile | period=20 | volume_ratio, is_high_volume |
| Support/Resistance | period=20 | support_levels, resistance_levels |

## Usage

### Calculate Single Indicator

```python
from apps.indicators.services import RSIIndicator

indicator = RSIIndicator({'period': 14})
result = indicator.calculate(ohlcv_data)
signal = indicator.get_signal(result)
```

### Calculate All Indicators

```python
from apps.indicators.services import IndicatorEngine

engine = IndicatorEngine()
results = engine.calculate_all(ohlcv_data)

rsi = results['rsi']['rsi']
macd = results['macd']['histogram']
```

### Calculate for Combination

```python
results = engine.calculate_for_combination('golden_confluence', ohlcv_data)
```

## API Endpoints

- `GET /api/v1/indicators/types/` - List indicator types
- `GET /api/v1/indicators/configs/` - List configurations
- `POST /api/v1/indicators/calculate/` - Calculate indicators

## Testing

```bash
python manage.py test apps.indicators
```
