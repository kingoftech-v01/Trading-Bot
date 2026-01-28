# Contributing to Trading Bot

Thank you for your interest in contributing to Trading Bot! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Set up the development environment
4. Create a feature branch
5. Make your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Redis (for Celery)
- PostgreSQL (for production) or SQLite (for development)

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/trading-bot.git
cd trading-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements/development.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Project Structure

```
trading_bot/
├── apps/
│   ├── core/              # Base models and utilities
│   ├── market_data/       # OHLCV data management
│   ├── indicators/        # Technical indicators
│   ├── combinations/      # Trading strategies
│   ├── signals/           # Voting system (5/8)
│   ├── risk_management/   # Position sizing, SL/TP
│   ├── orders/            # Trade execution
│   ├── backtesting/       # Historical testing
│   └── monitoring/        # Alerts and reporting
├── trading_bot/           # Django configuration
├── docs/                  # Documentation
├── requirements/          # Dependencies
└── tests/                 # Integration tests
```

### App Structure Convention

Each app follows this structure:

```
app_name/
├── __init__.py
├── apps.py
├── models.py              # Database models
├── views_api.py           # REST API views (DRF)
├── views_frontend.py      # HTML views
├── serializers.py         # DRF serializers
├── forms.py               # Django forms
├── urls.py                # URL routing
├── admin.py               # Admin configuration
├── tasks.py               # Celery tasks
├── services/              # Business logic
│   ├── __init__.py
│   └── ...
├── tests/                 # Unit tests
│   ├── __init__.py
│   ├── test_models.py
│   ├── test_services.py
│   └── test_api.py
├── README.md
└── TODO.md
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for public functions and classes

```python
from typing import Dict, List, Optional

def calculate_signal(
    ohlcv_data: List[Dict],
    threshold: int = 5
) -> Optional[str]:
    """
    Calculate trading signal from OHLCV data.

    Args:
        ohlcv_data: List of OHLCV dictionaries
        threshold: Minimum votes required (default: 5)

    Returns:
        Signal string ('buy', 'sell', or None)
    """
    pass
```

### Django Conventions

- Use class-based views
- Prefix API views with `API` or use ViewSets
- Use meaningful model names (singular)
- Add `__str__` method to all models

### Service Layer Pattern

Business logic goes in services, not views:

```python
# Good
class SignalGenerator(BaseService):
    def generate_signal(self, data):
        # Business logic here
        pass

# In views
def post(self, request):
    generator = SignalGenerator()
    result = generator.generate_signal(data)
    return Response(result)
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Models | PascalCase, singular | `TradingPair` |
| Services | PascalCase + Service/Manager | `SignalGenerator` |
| Views | PascalCase + View/ViewSet | `SignalViewSet` |
| URLs | lowercase, hyphens | `api/v1/signals/` |
| Files | lowercase, underscores | `signal_generator.py` |

## Testing

### Running Tests

```bash
# All tests
python manage.py test

# Specific app
python manage.py test apps.signals

# With coverage
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

### Writing Tests

```python
from django.test import TestCase
from apps.signals.services import SignalGenerator

class SignalGeneratorTests(TestCase):
    def setUp(self):
        self.generator = SignalGenerator()
        self.sample_data = [...]

    def test_generate_buy_signal(self):
        """Test that buy signal is generated with 5+ buy votes."""
        result = self.generator.generate_signal(self.sample_data)
        self.assertEqual(result['signal'], 'buy')

    def test_no_signal_below_threshold(self):
        """Test that no signal is generated below threshold."""
        result = self.generator.generate_signal(self.weak_data)
        self.assertIsNone(result['signal'])
```

### Test Coverage Requirements

- Minimum 80% coverage for new code
- All services must have unit tests
- API endpoints must have integration tests

## Submitting Changes

### Branch Naming

```
feature/add-new-indicator
bugfix/fix-signal-calculation
docs/update-readme
refactor/improve-voting-system
```

### Commit Messages

Follow conventional commits:

```
feat: add RSI divergence detection
fix: correct stop loss calculation for short positions
docs: update API documentation
test: add tests for voting system
refactor: simplify indicator engine
```

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New code has tests
- [ ] Documentation updated if needed
- [ ] No sensitive data in commits

## Pull Request Process

1. **Create PR** against `main` branch
2. **Fill template** with description of changes
3. **Wait for review** from maintainers
4. **Address feedback** if any
5. **Merge** after approval

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
```

## Adding New Features

### Adding a New Indicator

1. Create `apps/indicators/services/new_indicator.py`
2. Extend `BaseIndicator` class
3. Implement `calculate()` and `get_signal()` methods
4. Register in `indicator_engine.py`
5. Add tests in `apps/indicators/tests/`
6. Update README.md

### Adding a New Combination

1. Create `apps/combinations/services/new_combination.py`
2. Extend `BaseCombination` class
3. Implement `evaluate_buy()` and `evaluate_sell()` methods
4. Register in `combination_evaluator.py`
5. Add tests
6. Update README.md

## Questions?

Open an issue for questions or discussions about contributing.
