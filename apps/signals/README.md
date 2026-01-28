# Signals App

This app implements the **"5 out of 8" voting system** that generates trading signals when at least 5 combinations agree.

## Overview

The signals app is the core of the trading bot. It orchestrates:
1. Collecting votes from all 8 combinations
2. Determining if the voting threshold is met
3. Calculating confluence scores
4. Generating actionable trading signals with entry/SL/TP levels

## How the Voting System Works

```
┌─────────────────────────────────────────────────────────────┐
│                    OHLCV Market Data                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              8 Combination Evaluators                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Golden  │ │  Mean   │ │Breakout │ │Harmonic │           │
│  │Confluenc│ │Reversion│ │Momentum │ │Confluenc│           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │BUY        │SELL       │BUY        │BUY              │
│  ┌────┴────┐ ┌────┴────┐ ┌────┴────┐ ┌────┴────┐           │
│  │  Lin.   │ │  Multi  │ │ Stoch.  │ │Ultimate │           │
│  │  Reg.   │ │Timeframe│ │Crossover│ │Confluenc│           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │NEUTRAL    │BUY        │BUY        │NEUTRAL          │
└───────┴───────────┴───────────┴───────────┴─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    VOTING SYSTEM                             │
│                                                              │
│  BUY Votes:  5  │  Threshold: 5  │  THRESHOLD MET!          │
│  SELL Votes: 1  │                │                           │
│  NEUTRAL:    2  │                │                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SIGNAL GENERATED                            │
│                                                              │
│  Signal: BUY                                                 │
│  Confluence Score: 78.5                                      │
│  Confidence: 82%                                             │
│  Entry: 50000.00                                             │
│  Stop Loss: 49000.00                                         │
│  Take Profit: 53000.00                                       │
│  R:R Ratio: 3.0                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Concepts

### Voting Threshold
- Default: **5 out of 8** combinations must agree
- Configurable via `TRADING_CONFIG['voting_threshold']`

### Confluence Score
A 0-100 score representing signal strength based on:
- **Vote Weight (40%)**: Number of agreeing combinations
- **Confidence (25%)**: Average confidence of votes
- **Win Rate (20%)**: Historical win rates of voting combinations
- **Risk/Reward (10%)**: R:R ratios of combinations
- **Alignment (5%)**: Absence of contradicting signals

### Signal Categories
- **Excellent**: Confluence score ≥ 85
- **Strong**: Confluence score ≥ 70
- **Moderate**: Confluence score ≥ 50
- **Weak**: Confluence score ≥ 30
- **None**: Confluence score < 30

## Architecture

```
signals/
├── models.py                # Vote, SignalSession, Signal, ConfluenceScore
├── services/
│   ├── voting_system.py     # Core "5 out of 8" logic
│   ├── signal_generator.py  # Orchestrates signal generation
│   ├── confluence_scorer.py # Detailed scoring
│   └── multi_pair_validator.py  # Correlation validation
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

### VotingSystem

The core voting logic:

```python
from apps.signals.services import VotingSystem

voting_system = VotingSystem(voting_threshold=5)

# Collect votes from all 8 combinations
result = voting_system.collect_votes(ohlcv_data)

# Result contains:
# - final_signal: 'buy', 'sell', or 'wait'
# - buy_votes: list of buy votes
# - sell_votes: list of sell votes
# - neutral_votes: list of neutral votes
# - threshold_met: whether threshold was met
# - confluence_score: overall score
```

### SignalGenerator

Orchestrates the complete signal generation:

```python
from apps.signals.services import SignalGenerator

generator = SignalGenerator(
    min_confluence=50.0,
    min_confidence=60.0,
)

result = generator.generate_signal(
    trading_pair=pair,
    ohlcv_data=data,
    timeframe='1h',
)

if result.success and result.data['signal_generated']:
    print(f"Signal: {result.data['signal']}")
    print(f"Entry: {result.data['entry_price']}")
    print(f"SL: {result.data['stop_loss']}")
    print(f"TP: {result.data['take_profit']}")
```

### ConfluenceScorer

Detailed scoring breakdown:

```python
from apps.signals.services import ConfluenceScorer

scorer = ConfluenceScorer()
details = scorer.calculate_detailed_score(voting_result)

# Returns detailed breakdown of all score components
```

## API Endpoints

### REST API (namespace: `api:v1:signals`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/signals/signals/` | List all signals |
| GET | `/api/v1/signals/signals/{id}/` | Get signal |
| GET | `/api/v1/signals/signals/active/` | Get active signals |
| POST | `/api/v1/signals/signals/{id}/execute/` | Mark as executed |
| POST | `/api/v1/signals/signals/{id}/cancel/` | Cancel signal |
| GET | `/api/v1/signals/sessions/` | List sessions |
| GET | `/api/v1/signals/sessions/{id}/` | Get session |
| GET | `/api/v1/signals/sessions/actionable/` | Get actionable sessions |
| POST | `/api/v1/signals/generate/` | Generate signal |
| POST | `/api/v1/signals/voting-status/` | Get voting status |

### Frontend URLs (namespace: `frontend:signals`)

| URL | View | Description |
|-----|------|-------------|
| `/signals/` | SignalDashboardView | Dashboard |
| `/signals/list/` | SignalListView | List signals |
| `/signals/active/` | ActiveSignalsView | Active signals |
| `/signals/{id}/` | SignalDetailView | Signal detail |
| `/signals/sessions/` | SignalSessionListView | List sessions |
| `/signals/sessions/{id}/` | SignalSessionDetailView | Session detail |
| `/signals/generate/` | GenerateSignalView | Generate form |
| `/signals/voting-status/` | VotingStatusView | Voting status |

## Usage Examples

### Generate Signal via API

```bash
curl -X POST http://localhost:8000/api/v1/signals/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "trading_pair_id": "uuid-here",
    "timeframe": "1h",
    "min_confluence": 50.0,
    "min_confidence": 60.0
  }'
```

### Generate Signal via Celery

```python
from apps.signals.tasks import generate_signal_task

# Queue signal generation
generate_signal_task.delay(
    trading_pair_id='uuid-here',
    timeframe='1h',
)

# Generate for all pairs
from apps.signals.tasks import generate_signals_for_all_pairs_task
generate_signals_for_all_pairs_task.delay(timeframe='1h')
```

## Configuration

```python
# settings/base.py
TRADING_CONFIG = {
    'voting_threshold': 5,      # Minimum votes required
    'risk_per_trade': 0.01,     # 1% risk per trade
    'max_daily_trades': 5,
}
```

## Testing

```bash
# Run all tests
python manage.py test apps.signals

# Run specific test file
python manage.py test apps.signals.tests.test_services

# Run with coverage
coverage run manage.py test apps.signals
coverage report
```

## Dependencies

- `apps.core` - BaseModel, BaseService
- `apps.combinations` - CombinationEvaluator
- `apps.market_data` - TradingPair, OHLCV
- `apps.indicators` - IndicatorEngine (via combinations)
