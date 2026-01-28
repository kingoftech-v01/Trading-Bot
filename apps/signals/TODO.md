# Signals App - TODO

## Completed

- [x] Create models (Vote, SignalSession, Signal, ConfluenceScore)
- [x] Implement VotingSystem service with "5 out of 8" logic
- [x] Implement SignalGenerator with entry/SL/TP calculation
- [x] Implement ConfluenceScorer with detailed breakdown
- [x] Implement MultiPairValidator for correlation validation
- [x] Create serializers
- [x] Create forms
- [x] Create API views
- [x] Create frontend views
- [x] Create URL routing
- [x] Create admin configuration
- [x] Create Celery tasks
- [x] Create tests

## Future Enhancements

### Signal Validation

- [ ] Add more sophisticated correlation validation
- [ ] Implement cross-market validation (crypto, forex, stocks)
- [ ] Add news/sentiment integration for signal filtering

### Entry Level Optimization

- [ ] Implement multiple entry strategies (aggressive, conservative)
- [ ] Add support/resistance-based entry levels
- [ ] Add Fibonacci-based targets

### Performance Tracking

- [ ] Track signal performance over time
- [ ] Calculate actual vs expected win rates
- [ ] Add performance attribution by combination

### Notifications

- [ ] Implement Telegram bot notifications
- [ ] Add email notifications
- [ ] Add Discord webhook integration
- [ ] Add mobile push notifications

### Machine Learning

- [ ] Add ML-based signal filtering
- [ ] Implement adaptive threshold adjustment
- [ ] Add pattern recognition for false signal filtering

### Risk Integration

- [ ] Integrate with risk_management app for position sizing
- [ ] Add portfolio-level risk checks
- [ ] Implement correlation-based position limits

### Testing

- [ ] Add integration tests with real market data
- [ ] Add performance benchmarks
- [ ] Add stress tests for high-frequency signals

### Documentation

- [ ] Add detailed algorithm documentation
- [ ] Create visualization tools for voting process
- [ ] Add backtesting documentation
