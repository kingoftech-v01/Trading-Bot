# Combinations App

This app implements the 8 trading combinations that form the foundation of the voting system.

## Overview

Each combination is a set of technical indicators with specific criteria that must be met to generate a buy or sell signal. The CombinationEvaluator orchestrates all 8 combinations and collects votes for the signal generation system.

## The 8 Combinations

| # | Name | Win Rate | Risk/Reward | Frequency |
|---|------|----------|-------------|-----------|
| 1 | Golden Confluence | 62% | 3.8:1 | ~73/year |
| 2 | Mean Reversion Power | 68% | 3.2:1 | ~89/year |
| 3 | Breakout Momentum Hunter | 56% | 4.1:1 | ~104/year |
| 4 | Harmonic Confluence | 64% | 3.5:1 | ~62/year |
| 5 | Linear Regression Channel | 59% | 3.8:1 | ~82/year |
| 6 | Multi-Timeframe Convergence | 66% | 3.3:1 | ~47/year |
| 7 | Stochastic Crossover System | 71% | 3.0:1 | ~156/year |
| 8 | The Ultimate Confluence | 58% | 4.5:1 | ~12/year |

## Architecture

```
combinations/
├── models.py                # Combination, CombinationResult models
├── services/
│   ├── base_combination.py           # Abstract base class
│   ├── combination_evaluator.py      # Orchestrator for all 8
│   ├── golden_confluence.py          # Combination 1
│   ├── mean_reversion.py             # Combination 2
│   ├── breakout_momentum.py          # Combination 3
│   ├── harmonic_confluence.py        # Combination 4
│   ├── linear_regression_channel.py  # Combination 5
│   ├── multi_timeframe.py            # Combination 6
│   ├── stochastic_crossover.py       # Combination 7
│   └── ultimate_confluence.py        # Combination 8
├── views_api.py             # REST API endpoints
├── views_frontend.py        # HTML views
├── serializers.py           # DRF serializers
├── forms.py                 # Django forms
├── urls.py                  # URL routing
├── admin.py                 # Admin configuration
├── tasks.py                 # Celery tasks
└── tests/                   # Test suite
```

## Services

### BaseCombination

Abstract base class that all combinations inherit from:

```python
class BaseCombination(ABC):
    def get_name(self) -> str: ...
    def get_display_name(self) -> str: ...
    def get_win_rate(self) -> float: ...
    def get_risk_reward_ratio(self) -> float: ...
    def get_required_indicators(self) -> List[str]: ...
    def evaluate_buy(self, indicators: Dict) -> Tuple[bool, int, Dict]: ...
    def evaluate_sell(self, indicators: Dict) -> Tuple[bool, int, Dict]: ...
    def evaluate(self, ohlcv_data: List[Dict]) -> Dict[str, Any]: ...
```

### CombinationEvaluator

Orchestrates all 8 combinations:

```python
evaluator = CombinationEvaluator()

# Evaluate all combinations
results = evaluator.evaluate_all(ohlcv_data)
# Returns: {
#   'buy_votes': [...],
#   'sell_votes': [...],
#   'neutral_votes': [...],
#   'summary': {...},
#   'details': {...}
# }

# Evaluate single combination
result = evaluator.evaluate_single('golden_confluence', ohlcv_data)

# Get combination info
info = evaluator.get_combination_info()
```

## API Endpoints

### REST API (namespace: `api:v1:combinations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/combinations/combinations/` | List all combinations |
| POST | `/api/v1/combinations/combinations/` | Create combination |
| GET | `/api/v1/combinations/combinations/{id}/` | Get combination |
| PUT | `/api/v1/combinations/combinations/{id}/` | Update combination |
| DELETE | `/api/v1/combinations/combinations/{id}/` | Delete combination |
| GET | `/api/v1/combinations/results/` | List results |
| GET | `/api/v1/combinations/results/{id}/` | Get result |
| POST | `/api/v1/combinations/evaluate/` | Evaluate single combination |
| POST | `/api/v1/combinations/evaluate-all/` | Evaluate all combinations |
| GET | `/api/v1/combinations/info/` | Get combination info |

### Frontend URLs (namespace: `frontend:combinations`)

| URL | View | Description |
|-----|------|-------------|
| `/combinations/` | CombinationListView | List combinations |
| `/combinations/create/` | CombinationCreateView | Create form |
| `/combinations/{id}/` | CombinationDetailView | Detail view |
| `/combinations/{id}/edit/` | CombinationUpdateView | Edit form |
| `/combinations/results/` | CombinationResultListView | List results |
| `/combinations/evaluate/` | EvaluateCombinationsView | Evaluation form |
| `/combinations/info/` | CombinationInfoView | Combination info |

## Combination Details

### 1. Golden Confluence (62%, 3.8:1)

**Indicators:** RSI(14), MACD(12,26,9), ADX(14), Stochastic(14,3,3), Bollinger(20,2)

**BUY Criteria:**
- RSI > 50
- MACD > Signal Line
- ADX > 25 with +DI > -DI
- Stochastic K% > D%
- Price > Middle BB

### 2. Mean Reversion Power (68%, 3.2:1)

**Indicators:** RSI(14), Stochastic(14,3,3), Bollinger(20,2), MACD, ATR(14)

**BUY Criteria:**
- RSI < 30 (oversold)
- Stochastic K% < 20
- Price touches lower BB
- MACD divergence forming
- ATR normal range

### 3. Breakout Momentum Hunter (56%, 4.1:1)

**Indicators:** Bollinger(20,2), ADX(14), RSI(14), Volume, Linear Regression(50)

**BUY Criteria:**
- Price breaks above upper BB
- ADX > 25 and rising
- RSI > 60 (momentum)
- Volume > 1.5x average
- LR slope > 0.02

### 4. Harmonic Confluence (64%, 3.5:1)

**Indicators:** RSI divergence, MACD divergence, Linear Regression, Stochastic, Volume

**BUY Criteria:**
- RSI bullish divergence
- MACD histogram divergence
- LR supports move
- Stochastic confirms
- Volume increasing

### 5. Linear Regression Channel (59%, 3.8:1)

**Indicators:** Linear Regression(50), RSI(14), ADX(14), Bollinger(20,2), CCI(20)

**BUY Criteria:**
- LR slope > 0.02
- r² > 0.60
- Price at lower channel
- RSI 30-50
- ADX > 20

### 6. Multi-Timeframe Convergence (66%, 3.3:1)

**Indicators per Timeframe:**
- 4h: ADX, Linear Regression
- 1h: RSI, MACD, Stochastic
- 15m: Bollinger, Volume

**BUY Criteria:**
- 4h: LR uptrend, ADX > 25
- 1h: RSI > 50, MACD bullish
- 15m: BB bounce, volume spike

### 7. Stochastic Crossover System (71%, 3.0:1)

**Indicators:** Stochastic Fast(14,3,3), Stochastic Slow(20,5,5), RSI(14), Volume, S/R

**BUY Criteria:**
- Fast K% crosses above Slow K%
- RSI in 30-70 neutral zone
- Volume > average
- Price above support

### 8. The Ultimate Confluence (58%, 4.5:1)

**Indicators:** All 8+ indicators

**BUY Criteria (ALL must be met):**
- RSI > 50
- MACD histogram positive and growing
- ADX > 25 with +DI > -DI
- Stochastic K% > D%
- Price > Lower BB
- LR slope > 0.02 and r² > 0.60
- Volume > average
- CCI > 0 and rising

## Usage

### Evaluating Combinations

```python
from apps.combinations.services import CombinationEvaluator
from apps.market_data.models import OHLCV

# Get OHLCV data
ohlcv_data = list(OHLCV.objects.filter(
    trading_pair=pair,
    timeframe='1h'
).order_by('timestamp').values())

# Evaluate all combinations
evaluator = CombinationEvaluator()
results = evaluator.evaluate_all(ohlcv_data)

# Check votes
print(f"Buy votes: {len(results['buy_votes'])}")
print(f"Sell votes: {len(results['sell_votes'])}")
```

### Celery Tasks

```python
from apps.combinations.tasks import evaluate_all_combinations_task

# Queue evaluation task
evaluate_all_combinations_task.delay(
    trading_pair_id=str(pair.id),
    timeframe='1h'
)
```

## Testing

```bash
# Run all tests
python manage.py test apps.combinations

# Run specific test file
python manage.py test apps.combinations.tests.test_services

# Run with coverage
coverage run manage.py test apps.combinations
coverage report
```

## Dependencies

- `apps.core` - BaseModel, BaseService
- `apps.indicators` - IndicatorEngine for calculating indicators
- `apps.market_data` - TradingPair, OHLCV models
