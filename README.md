# Trading Bot - Système de Vote 5 sur 8

Un trading bot Django qui génère des signaux lorsque **au moins 5 des 8 combinaisons d'indicateurs** sont en accord (BUY ou SELL).

## Architecture

```
trading_bot/
├── manage.py
├── trading_bot/                 # Configuration Django
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── core/                    # Modèles de base, utilitaires
│   ├── market_data/             # Données OHLCV, TradingPair
│   ├── indicators/              # 10 indicateurs techniques
│   ├── combinations/            # 8 combinaisons de trading
│   ├── signals/                 # Système de vote 5/8
│   ├── risk_management/         # Position sizing, SL/TP
│   ├── orders/                  # Exécution des trades
│   ├── backtesting/             # Tests historiques
│   └── monitoring/              # Alertes, dashboards
└── requirements/
```

## Les 8 Combinaisons

| # | Combinaison | Win Rate | R:R | Description |
|---|-------------|----------|-----|-------------|
| 1 | Golden Confluence | 62% | 3.8:1 | RSI, MACD, ADX, Stochastic, Bollinger |
| 2 | Mean Reversion | 68% | 3.2:1 | Retour à la moyenne |
| 3 | Breakout Momentum | 56% | 4.1:1 | Cassure avec volume |
| 4 | Harmonic Confluence | 64% | 3.5:1 | Divergences |
| 5 | Linear Regression | 59% | 3.8:1 | Canal de régression |
| 6 | Multi-Timeframe | 66% | 3.3:1 | 4h/1h/15m alignés |
| 7 | Stochastic Crossover | 71% | 3.0:1 | Croisements stochastiques |
| 8 | Ultimate Confluence | 58% | 4.5:1 | Tous les indicateurs |

## Système de Vote

```
OHLCV Data → 8 Combinations → Voting System → Signal
                                    ↓
                              BUY: 5 votes
                              SELL: 2 votes
                              NEUTRAL: 1 vote
                                    ↓
                         Threshold (5) MET → SIGNAL BUY
```

## Installation

```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements/development.txt

# Configuration
cp .env.example .env
# Éditer .env avec vos paramètres

# Migrations
python manage.py migrate

# Créer un superuser
python manage.py createsuperuser

# Démarrer le serveur
python manage.py runserver
```

## Configuration

```python
# settings/base.py
TRADING_CONFIG = {
    'voting_threshold': 5,      # Votes minimum
    'risk_per_trade': 0.01,     # 1% par trade
    'max_daily_trades': 5,
}
```

## API Endpoints

### Signals (Core)
```
POST /api/v1/signals/generate/           # Générer un signal
GET  /api/v1/signals/signals/            # Lister les signaux
GET  /api/v1/signals/signals/active/     # Signaux actifs
POST /api/v1/signals/voting-status/      # Statut du vote
```

### Combinations
```
GET  /api/v1/combinations/combinations/  # Lister les combinaisons
POST /api/v1/combinations/evaluate-all/  # Évaluer toutes
GET  /api/v1/combinations/info/          # Info combinaisons
```

### Risk Management
```
POST /api/v1/risk/calculate/             # Calculer position size
GET  /api/v1/risk/summary/               # Résumé du risque
```

### Backtesting
```
POST /api/v1/backtesting/create/         # Créer backtest
POST /api/v1/backtesting/backtests/{id}/run/  # Lancer
GET  /api/v1/backtesting/backtests/{id}/results/  # Résultats
```

## Utilisation

### Générer un Signal

```python
from apps.signals.services import SignalGenerator
from apps.market_data.models import TradingPair, OHLCV

# Récupérer les données
pair = TradingPair.objects.get(symbol='EUR/USD')
ohlcv_data = list(OHLCV.objects.filter(
    trading_pair=pair,
    timeframe='1h'
).order_by('timestamp').values())

# Générer le signal
generator = SignalGenerator(
    voting_threshold=5,
    min_confluence=50.0,
    min_confidence=60.0,
)
result = generator.generate_signal(
    trading_pair=pair,
    ohlcv_data=ohlcv_data,
    timeframe='1h',
)

if result.success and result.data['signal_generated']:
    print(f"Signal: {result.data['signal']}")
    print(f"Entry: {result.data['entry_price']}")
    print(f"SL: {result.data['stop_loss']}")
    print(f"TP: {result.data['take_profit']}")
```

### Lancer un Backtest

```python
from apps.backtesting.models import BacktestRun
from apps.backtesting.tasks import run_backtest_task

backtest = BacktestRun.objects.create(
    name='Test EUR/USD 2024',
    trading_pair=pair,
    timeframe='1h',
    start_date=start,
    end_date=end,
    initial_balance=10000,
)

# Async
run_backtest_task.delay(str(backtest.id))
```

## Tests

```bash
# Tous les tests
python manage.py test

# App spécifique
python manage.py test apps.signals

# Avec coverage
coverage run manage.py test
coverage report
```

## Celery Tasks

```bash
# Démarrer Celery worker
celery -A trading_bot worker -l info

# Démarrer Celery beat (tâches planifiées)
celery -A trading_bot beat -l info
```

## Structure des Apps

Chaque app suit la convention définie dans `URL_AND_VIEW_CONVENTIONS.md`:

```
app_name/
├── __init__.py
├── apps.py
├── models.py
├── views_frontend.py    # Vues HTML
├── views_api.py         # Vues REST API
├── serializers.py
├── forms.py
├── urls.py
├── admin.py
├── tasks.py             # Tâches Celery
├── services/            # Logique métier
│   ├── __init__.py
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   └── test_api.py
├── README.md
└── TODO.md
```

## Technologies

- **Django 5.0**: Framework web
- **Django REST Framework**: API REST
- **Celery**: Tâches asynchrones
- **Redis**: Cache et message broker
- **PostgreSQL**: Base de données (production)
- **SQLite**: Base de données (développement)

## Licence

MIT
