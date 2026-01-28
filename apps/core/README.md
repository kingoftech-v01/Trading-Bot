# Core App

Base models and utilities for the Trading Bot platform.

## Purpose

The Core app provides foundational classes and utilities that other apps extend:

- **BaseModel**: Abstract model with UUID primary key, timestamps, and soft delete
- **TimeframeMixin**: Mixin for models that work with trading timeframes
- **SignalDirectionMixin**: Mixin for models that represent trading signals
- **StatusMixin**: Mixin for models with status workflows
- **BaseService**: Abstract service class for business logic
- **ServiceResult**: Wrapper for service operation results

## Models

### BaseModel

All models in the trading bot inherit from `BaseModel`:

```python
from apps.core.models import BaseModel

class MyModel(BaseModel):
    name = models.CharField(max_length=100)
```

Features:
- UUID primary key
- `created_at` / `updated_at` timestamps
- `is_active` flag for soft delete
- `soft_delete()` and `restore()` methods

### Mixins

```python
from apps.core.models import BaseModel, TimeframeMixin, SignalDirectionMixin

class MyTradingModel(BaseModel, TimeframeMixin, SignalDirectionMixin):
    # Inherits timeframe and signal fields
    pass
```

## Services

### BaseService

All services extend `BaseService`:

```python
from apps.core.services import BaseService

class MyService(BaseService):
    def do_something(self):
        self.log_info("Doing something")
        return ServiceResult.ok(data={'result': 'success'})
```

### ServiceResult

Wrap service results for consistent handling:

```python
result = my_service.do_something()
if result.success:
    data = result.data
else:
    error = result.error
```

## URLs

- API: `/api/v1/health/` - Health check endpoint

## Testing

```bash
python manage.py test apps.core
```
