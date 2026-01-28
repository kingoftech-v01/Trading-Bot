# Monitoring App

System monitoring, alerts, and reporting.

## Features
- Alert management (create, acknowledge, resolve)
- Health checks (database, Redis, Celery)
- Performance reports (daily, weekly, custom)
- System metrics tracking

## Services
- **AlertManager**: Create and manage alerts
- **HealthChecker**: Monitor system health
- **ReportGenerator**: Generate trading reports

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/monitoring/health/` | System health |
| GET | `/api/v1/monitoring/alerts/` | List alerts |
| POST | `/api/v1/monitoring/alerts/{id}/acknowledge/` | Acknowledge alert |
| POST | `/api/v1/monitoring/generate-report/` | Generate report |
| GET | `/api/v1/monitoring/reports/` | List reports |
