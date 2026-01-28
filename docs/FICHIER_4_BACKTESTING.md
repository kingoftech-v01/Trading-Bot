# TRADING BOT - FICHIER 4: BACKTESTING ET OPTIMISATION

## Introduction

Ce fichier couvre le backtesting rigoureux des stratégies de trading et l'optimisation des paramètres pour maximiser les performances[1][2]. Le backtesting est CRITIQUE avant le déploiement en live.

---

## 1. Framework de Backtesting (Pages 1-2)

### Pourquoi le Backtesting?

Un trading bot doit être testé sur l'historique avant de risquer de l'argent réel. Le backtesting permet de:
- Valider la stratégie sur 1+ an de données
- Identifier les périodes critiques (crises, rallies)
- Optimiser les paramètres des indicateurs
- Mesurer réalisme: Win Rate, Ratio, Drawdown
- Détecter les problèmes avant le live trading

### Étapes de Backtesting

1. **Récupérer l'historique** (1+ an de données OHLCV)
2. **Exécuter la stratégie** sur chaque barre historique
3. **Enregistrer chaque signal** généré
4. **Calculer P&L réaliste** (avec frais, slippage)
5. **Analyser les résultats** (statistiques, courbes)
6. **Optimiser si nécessaire** (paramètres indicateurs)
7. **Forward-test** (tester sur données récentes non utilisées)

### Architecture du Backtester

```python
class Backtester:
    def __init__(self, strategy, data, initial_balance=10000):
        self.strategy = strategy
        self.data = data  # DataFrame historique
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.trades = []
        self.equity_curve = []
        self.positions = {}
    
    def backtest(self):
        """Exécute le backtest complet"""
        
        for i in range(len(self.data)):
            # Préparer les données jusqu'au jour courant
            current_data = self.data.iloc[:i+1]
            
            # Générer signal
            signal, score = self.strategy.generate_signal(current_data)
            
            # Exécuter
            if signal == 'BUY':
                self.open_position(i, signal)
            elif signal == 'SELL':
                self.close_position(i)
            
            # Mettre à jour equity
            self.update_equity(i)
        
        return self.calculate_results()
    
    def open_position(self, bar, signal):
        """Ouvre une position"""
        price = self.data['close'].iloc[bar]
        self.positions['open_price'] = price
        self.positions['open_bar'] = bar
        self.positions['signal'] = signal
    
    def close_position(self, bar):
        """Ferme une position ouverte"""
        if not self.positions:
            return
        
        entry = self.positions['open_price']
        exit_price = self.data['close'].iloc[bar]
        
        # Calculer P&L
        pnl = (exit_price - entry) * 100 if self.positions['signal'] == 'BUY' else (entry - exit_price) * 100
        
        # Frais (0.1% par trade)
        fees = abs(entry * 100) * 0.001 + abs(exit_price * 100) * 0.001
        pnl_net = pnl - fees
        
        # Enregistrer le trade
        self.trades.append({
            'entry_bar': self.positions['open_bar'],
            'exit_bar': bar,
            'entry_price': entry,
            'exit_price': exit_price,
            'pnl': pnl_net,
            'signal': self.positions['signal'],
        })
        
        # Mettre à jour solde
        self.current_balance += pnl_net
        self.positions = {}
    
    def update_equity(self, bar):
        """Met à jour la courbe d'equity"""
        equity = self.current_balance
        
        # Ajouter P&L position ouverte
        if self.positions:
            open_price = self.positions['open_price']
            current_price = self.data['close'].iloc[bar]
            unrealized_pnl = (current_price - open_price) * 100
            equity += unrealized_pnl
        
        self.equity_curve.append(equity)
    
    def calculate_results(self):
        """Calcule les statistiques finales"""
        
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = sum([t['pnl'] for t in winning_trades]) / len(winning_trades) if winning_trades else 0
        avg_loss = sum([t['pnl'] for t in losing_trades]) / len(losing_trades) if losing_trades else 0
        
        ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        
        total_profit = self.current_balance - self.initial_balance
        roi = (total_profit / self.initial_balance) * 100
        
        # Drawdown maximum
        max_equity = max(self.equity_curve)
        min_equity = min(self.equity_curve)
        max_drawdown = ((max_equity - min_equity) / max_equity) * 100
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'ratio': ratio,
            'total_profit': total_profit,
            'roi': roi,
            'max_drawdown': max_drawdown,
            'final_balance': self.current_balance,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
        }
```

---

## 2. Collecte de Données Historiques (Pages 2-3)

### Téléchargement Données Historiques

```python
import ccxt
import pandas as pd

class HistoricalDataDownloader:
    def __init__(self, exchange_name='binance'):
        self.exchange = getattr(ccxt, exchange_name)()
    
    def download_ohlcv(self, pair, timeframe='1h', days=365):
        """Télécharge l'historique OHLCV"""
        
        all_candles = []
        since = int((pd.Timestamp.now() - pd.Timedelta(days=days)).timestamp() * 1000)
        
        while since < int(pd.Timestamp.now().timestamp() * 1000):
            try:
                candles = self.exchange.fetch_ohlcv(pair, timeframe, since=since, limit=1000)
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                since = candles[-1][0] + 1000  # Prochaine barre
            
            except Exception as e:
                print(f"Erreur téléchargement {pair}: {e}")
                break
        
        # Convertir en DataFrame
        df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        return df.drop_duplicates(subset=['timestamp']).reset_index(drop=True)
    
    def download_all_pairs(self, pairs, timeframe='1h', days=365):
        """Télécharge plusieurs paires"""
        data = {}
        
        for pair in pairs:
            print(f"Téléchargement {pair}...")
            df = self.download_ohlcv(pair, timeframe, days)
            data[pair] = df
        
        return data

# Utilisation
downloader = HistoricalDataDownloader('binance')
pairs = ['EUR/USD', 'GBP/USD', 'AUD/USD']
data = downloader.download_all_pairs(pairs, timeframe='1h', days=365)

# Sauvegarder en CSV
for pair, df in data.items():
    df.to_csv(f"data_{pair}.csv", index=False)
```

### Validation des Données

```python
class DataValidator:
    @staticmethod
    def validate(df):
        """Valide la qualité des données"""
        
        # Vérifier les NaN
        if df.isnull().sum().sum() > 0:
            print("⚠ Valeurs manquantes détectées!")
            return False
        
        # Vérifier les doublons
        if df.duplicated(subset=['timestamp']).sum() > 0:
            print("⚠ Doublons détectés!")
            return False
        
        # Vérifier l'ordre
        if not df['timestamp'].is_monotonic_increasing:
            print("⚠ Timestamps non ordonnés!")
            return False
        
        # Vérifier les gaps extrêmes (>5× ATR)
        atr = df['high'] - df['low']
        if (atr > atr.mean() * 5).sum() > 0:
            print("⚠ Gaps extrêmes détectés!")
        
        print("✓ Données valides!")
        return True

# Valider
DataValidator.validate(data['EUR/USD'])
```

---

## 3. Exécution du Backtest (Pages 3-4)

### Run Complet

```python
# Charger les données
df_eurusd = pd.read_csv('data_EUR_USD.csv')
df_eurusd['timestamp'] = pd.to_datetime(df_eurusd['timestamp'])

# Créer la stratégie
class MyTradingStrategy:
    def __init__(self):
        self.indicators = None
    
    def generate_signal(self, df):
        """Génère signal basé sur les 8 combinaisons"""
        
        # Calculer indicateurs
        from indicator_engine import IndicatorEngine
        engine = IndicatorEngine(df)
        self.indicators = engine.calculate_all()
        
        # Confluence scoring
        rsi = self.indicators['rsi'][-1]
        macd_line, signal_line, histogram = self.indicators['macd']
        
        score = 0
        if rsi > 50:
            score += 20
        if macd_line[-1] > signal_line[-1]:
            score += 20
        
        if score >= 80:
            return 'BUY', score
        
        return 'WAIT', score

# Exécuter backtest
strategy = MyTradingStrategy()
backtester = Backtester(strategy, df_eurusd, initial_balance=10000)
results = backtester.backtest()

# Afficher résultats
print(f"Total Trades: {results['total_trades']}")
print(f"Win Rate: {results['win_rate']:.1f}%")
print(f"Ratio: {results['ratio']:.2f}:1")
print(f"ROI: {results['roi']:.1f}%")
print(f"Max Drawdown: {results['max_drawdown']:.1f}%")
print(f"Final Balance: {results['final_balance']:.2f}€")
```

### Analyse Détaillée des Trades

```python
import matplotlib.pyplot as plt

# Analyser les trades
trades = results['trades']

# Statistiques par jour/heure
trades_df = pd.DataFrame(trades)
trades_df['entry_time'] = df['timestamp'].iloc[trades_df['entry_bar']].values
trades_df['hour'] = trades_df['entry_time'].dt.hour
trades_df['day'] = trades_df['entry_time'].dt.dayofweek

# Meilleurs heures de trading
best_hours = trades_df.groupby('hour')['pnl'].agg(['mean', 'count']).sort_values('mean', ascending=False)
print("Top hours for trading:")
print(best_hours.head(5))

# Graphique equity curve
plt.figure(figsize=(12, 6))
plt.plot(results['equity_curve'])
plt.title('Equity Curve - Backtest')
plt.xlabel('Bar')
plt.ylabel('Balance (€)')
plt.grid(True)
plt.show()

# Histogramme P&L
plt.figure(figsize=(10, 5))
plt.hist([t['pnl'] for t in trades], bins=50, edgecolor='black')
plt.title('Distribution of Trade P&L')
plt.xlabel('P&L (€)')
plt.ylabel('Frequency')
plt.axvline(x=0, color='red', linestyle='--')
plt.show()
```

---

## 4. Optimisation des Paramètres (Pages 4-5)

### Grid Search pour Optimisation

```python
from itertools import product

class ParameterOptimizer:
    def __init__(self, strategy_class, data):
        self.strategy_class = strategy_class
        self.data = data
        self.results = []
    
    def optimize(self, param_ranges):
        """Teste toutes les combinaisons de paramètres"""
        
        # Générer toutes les combinaisons
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        combinations = product(*param_values)
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            
            print(f"Test {i}: {params}")
            
            # Créer stratégie avec ces paramètres
            strategy = self.strategy_class(**params)
            
            # Backtester
            backtester = Backtester(strategy, self.data, initial_balance=10000)
            result = backtester.backtest()
            
            # Enregistrer résultat
            self.results.append({
                'params': params,
                'roi': result['roi'],
                'win_rate': result['win_rate'],
                'ratio': result['ratio'],
                'max_drawdown': result['max_drawdown'],
                'total_profit': result['total_profit'],
            })
        
        return self.get_best_params()
    
    def get_best_params(self):
        """Retourne les meilleurs paramètres"""
        
        # Trier par ROI
        sorted_results = sorted(self.results, key=lambda x: x['roi'], reverse=True)
        
        print("\nTop 5 Parameter Combinations:")
        for i, result in enumerate(sorted_results[:5], 1):
            print(f"\n{i}. ROI: {result['roi']:.1f}%")
            print(f"   Params: {result['params']}")
            print(f"   Win Rate: {result['win_rate']:.1f}%")
            print(f"   Ratio: {result['ratio']:.2f}:1")
        
        return sorted_results[0]['params']

# Utilisation
class ParametrizedStrategy:
    def __init__(self, rsi_period=14, macd_fast=12, macd_slow=26):
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
    
    def generate_signal(self, df):
        # Utiliser les paramètres...
        pass

param_ranges = {
    'rsi_period': [10, 12, 14, 16, 18],
    'macd_fast': [10, 12, 14],
    'macd_slow': [24, 26, 28],
}

optimizer = ParameterOptimizer(ParametrizedStrategy, df_eurusd)
best_params = optimizer.optimize(param_ranges)
```

---

## 5. Forward Testing et Walk-Forward Analysis (Pages 5-6)

### Walk-Forward Analysis

```python
class WalkForwardAnalysis:
    def __init__(self, data, strategy_class, initial_balance=10000):
        self.data = data
        self.strategy_class = strategy_class
        self.initial_balance = initial_balance
        self.results = []
    
    def run(self, in_sample_period=180, out_sample_period=30):
        """
        Divise les données en périodes:
        - In-sample: Optimize les paramètres
        - Out-of-sample: Test les paramètres sur nouvelles données
        """
        
        total_length = len(self.data)
        start = 0
        
        while start + in_sample_period + out_sample_period <= total_length:
            # Données in-sample (optimisation)
            in_sample_data = self.data.iloc[start:start + in_sample_period]
            
            # Données out-of-sample (test)
            oos_data = self.data.iloc[
                start + in_sample_period:start + in_sample_period + out_sample_period
            ]
            
            print(f"\nWalk {len(self.results) + 1}:")
            print(f"  In-sample: {in_sample_data.iloc[0]['timestamp']} to {in_sample_data.iloc[-1]['timestamp']}")
            print(f"  Out-of-sample: {oos_data.iloc[0]['timestamp']} to {oos_data.iloc[-1]['timestamp']}")
            
            # Optimiser sur in-sample
            optimizer = ParameterOptimizer(self.strategy_class, in_sample_data)
            best_params = optimizer.optimize({
                'rsi_period': [12, 14, 16],
                'macd_fast': [10, 12],
                'macd_slow': [24, 26],
            })
            
            # Tester sur out-of-sample
            strategy = self.strategy_class(**best_params)
            backtester = Backtester(strategy, oos_data, self.initial_balance)
            oos_result = backtester.backtest()
            
            self.results.append({
                'window': len(self.results) + 1,
                'best_params': best_params,
                'oos_result': oos_result,
                'oos_roi': oos_result['roi'],
            })
            
            start += 30  # Glisser de 30 jours
    
    def summarize(self):
        """Résume les résultats walk-forward"""
        
        rois = [r['oos_roi'] for r in self.results]
        avg_roi = sum(rois) / len(rois)
        
        print(f"\n=== WALK-FORWARD ANALYSIS ===")
        print(f"Number of windows: {len(self.results)}")
        print(f"Average out-of-sample ROI: {avg_roi:.1f}%")
        print(f"Min ROI: {min(rois):.1f}%")
        print(f"Max ROI: {max(rois):.1f}%")

# Utilisation
wfa = WalkForwardAnalysis(df_eurusd, ParametrizedStrategy)
wfa.run(in_sample_period=180, out_sample_period=30)
wfa.summarize()
```

---

## 6. Analyse de Robustesse (Pages 6-7)

### Stress Testing

```python
class StressTest:
    def __init__(self, backtester_results):
        self.results = backtester_results
        self.trades = backtester_results['trades']
    
    def test_slippage_impact(self, slippage_bps=[1, 2, 5, 10]):
        """Teste impact du slippage"""
        
        print("\n=== SLIPPAGE IMPACT ===")
        
        for slip_bps in slippage_bps:
            slip_pct = slip_bps / 10000
            total_pnl = 0
            
            for trade in self.trades:
                entry_slip = trade['entry_price'] * slip_pct
                exit_slip = trade['exit_price'] * slip_pct
                
                pnl = (trade['exit_price'] - entry_slip - trade['entry_price'] - entry_slip) * 100
                total_pnl += pnl
            
            print(f"Slippage {slip_bps} bps: {total_pnl:.2f}€ (Impact: {(total_pnl - self.results['total_profit']):.2f}€)")
    
    def test_market_crash(self, crash_pct=20):
        """Simule crash de marché"""
        
        print(f"\n=== MARKET CRASH TEST (-{crash_pct}%) ===")
        
        # Réduire tous les prix de crash_pct
        worst_case_pnl = 0
        
        for trade in self.trades:
            if trade['signal'] == 'BUY':
                # Worst case: le crash arrive au-dessus de notre position
                exit_worst = trade['exit_price'] * (1 - crash_pct / 100)
                pnl = (exit_worst - trade['entry_price']) * 100
            else:
                pnl = (trade['entry_price'] - trade['exit_price']) * 100
            
            worst_case_pnl += pnl
        
        print(f"P&L en cas de crash: {worst_case_pnl:.2f}€")
        print(f"Baisse: {(self.results['total_profit'] - worst_case_pnl):.2f}€")
    
    def test_volatility_surge(self, volatility_multiplier=2):
        """Teste augmentation volatilité"""
        
        print(f"\n=== VOLATILITY SURGE TEST (×{volatility_multiplier}) ===")
        
        # Élargir les stops et profits
        adjusted_pnl = 0
        
        for trade in self.trades:
            entry = trade['entry_price']
            exit = trade['exit_price']
            
            # Avec volatilité augmentée, plus de risk de SL
            sl_distance = abs(exit - entry) * 0.05  # 5% de marge
            
            # 50% de chance d'être stoppé
            stop_risk = 0.5
            adjusted_pnl += (trade['pnl'] * (1 - stop_risk))
        
        print(f"Adjusted P&L: {adjusted_pnl:.2f}€")
```

---

## 7. Métriques de Performance (Pages 7-8)

### Calcul Complet des Métriques

```python
class PerformanceMetrics:
    def __init__(self, backtest_results):
        self.results = backtest_results
        self.trades = backtest_results['trades']
        self.equity_curve = backtest_results['equity_curve']
    
    def sharpe_ratio(self, risk_free_rate=0.02):
        """Calcule le Sharpe ratio"""
        
        # Returns du portefeuille
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        
        excess_return = np.mean(returns) - (risk_free_rate / 252)
        volatility = np.std(returns)
        
        sharpe = excess_return / volatility if volatility != 0 else 0
        
        return sharpe * np.sqrt(252)  # Annualisé
    
    def sortino_ratio(self, target_return=0.0005):
        """Calcule le Sortino ratio (plus strict que Sharpe)"""
        
        returns = np.diff(self.equity_curve) / self.equity_curve[:-1]
        excess = returns - target_return
        
        downside = np.sqrt(np.mean(np.minimum(excess, 0)**2))
        
        sortino = np.mean(excess) / downside if downside != 0 else 0
        
        return sortino * np.sqrt(252)
    
    def recovery_factor(self):
        """Temps pour récupérer le max drawdown"""
        
        max_dd = self.results['max_drawdown']
        profit = self.results['total_profit']
        
        if max_dd == 0:
            return float('inf')
        
        return profit / (max_dd / 100)
    
    def consecutive_losses(self):
        """Nombre de pertes consécutives maximum"""
        
        consecutive = 0
        max_consecutive = 0
        
        for trade in self.trades:
            if trade['pnl'] < 0:
                consecutive += 1
                max_consecutive = max(max_consecutive, consecutive)
            else:
                consecutive = 0
        
        return max_consecutive
    
    def print_all_metrics(self):
        """Affiche tous les metrics"""
        
        print("\n=== PERFORMANCE METRICS ===")
        print(f"Total Trades: {self.results['total_trades']}")
        print(f"Win Rate: {self.results['win_rate']:.1f}%")
        print(f"Ratio: {self.results['ratio']:.2f}:1")
        print(f"ROI: {self.results['roi']:.1f}%")
        print(f"Max Drawdown: {self.results['max_drawdown']:.1f}%")
        print(f"Sharpe Ratio: {self.sharpe_ratio():.2f}")
        print(f"Sortino Ratio: {self.sortino_ratio():.2f}")
        print(f"Recovery Factor: {self.recovery_factor():.2f}")
        print(f"Max Consecutive Losses: {self.consecutive_losses()}")

# Utilisation
metrics = PerformanceMetrics(results)
metrics.print_all_metrics()
```

---

## 8. Critères d'Approbation (Page 8)

### Checklist Avant Déploiement Live

```
✓ Backtest Requirements:

[ ] Win Rate > 50% (de préférence > 55%)
[ ] Ratio >= 3:1 (minimum)
[ ] Total Profit > 0€
[ ] ROI > 15% (annualisé)
[ ] Max Drawdown < 20% (de préférence < 15%)
[ ] Sharpe Ratio > 1.0
[ ] Min 50+ trades dans le backtest
[ ] Pas plus de 5 pertes consécutives
[ ] Walk-forward analysis positive
[ ] Stress test stable (slippage, crash, volatility)

✓ Technical Requirements:

[ ] Code compilé et testé
[ ] Gestion d'erreurs complète
[ ] Logging actif et détaillé
[ ] Database fonctionnelle
[ ] API connections testées
[ ] Risk management strictement appliqué
[ ] Stop-loss et Take-profit définis
[ ] Position sizing automatique

✓ Pre-Live Checklist:

[ ] Paper trading 2+ semaines
[ ] Paper trading ROI > 10%
[ ] Monitoring 24/7 mis en place
[ ] Discord/Email alerts configurés
[ ] Emergency kill switch opérationnel
[ ] Capital risqué < 10% du portefeuille
[ ] Journal de trading prêt
```

---

## Références

[1] Pardo, R. (2008). Design, Testing, and Optimization of Trading Systems
[2] Kaufman, P. J. (2020). New Trading Systems and Methods
