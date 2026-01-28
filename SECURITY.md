# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Trading Bot seriously. If you discover a security vulnerability, please follow these steps:

### Do NOT

- Do not open a public GitHub issue for security vulnerabilities
- Do not disclose the vulnerability publicly before it has been addressed

### Do

1. **Email**: Send a detailed report to the project maintainers
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-48 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

## Security Best Practices

### API Keys and Secrets

```bash
# Never commit API keys
# Use environment variables
COINAPI_KEY=your_key_here
BINANCE_API_KEY=your_key_here
BINANCE_SECRET_KEY=your_key_here
```

### Environment Configuration

1. Copy `.env.example` to `.env`
2. Never commit `.env` files
3. Use different keys for development and production

### Database Security

- Use strong passwords for PostgreSQL in production
- Enable SSL for database connections
- Regularly backup your database

### Django Security Settings

Production settings include:
- `DEBUG = False`
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS = 31536000`

### API Security

- All API endpoints require authentication
- Rate limiting is enabled
- Input validation on all endpoints

## Security Checklist for Deployment

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Enable HTTPS
- [ ] Set secure cookie flags
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

## Dependencies

We regularly update dependencies to patch security vulnerabilities:

```bash
# Check for security issues
pip-audit

# Update dependencies
pip install --upgrade -r requirements/production.txt
```

## Audit Log

Security-relevant actions are logged:
- Authentication attempts
- Order executions
- Configuration changes
- API key usage

## Contact

For security concerns, contact the project maintainers directly.
