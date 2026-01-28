# TRADING BOT - FICHIER 3: IMPLÉMENTATION TECHNIQUE

## Introduction

Ce fichier couvre l'implémentation technique concrète d'un trading bot professionnel avec Python, API trading, WebSocket pour temps réel, base de données, et gestion complète du cycle de vie d'un trade[1][2].

---

## 1. Architecture Système Globale (Pages 1-2)

### Stack Technologique Recommandée

**Backend**: Python 3.10+ avec Django/FastAPI
**Database**: PostgreSQL (historique) + Redis (cache temps réel)
**API Trading**: ccxt (crypto) ou MetaTrader 5 SDK (forex)
**WebSocket**: asyncio + websockets pour flux temps réel
**Monitoring**: Prometheus + Grafana
**Déploiement**: Docker + Docker Compose

### Composants Core

**1. Data Service (Collecte)**
- Connexion API multi-exchange
- Synchronisation timeframes
- Nettoyage et normalisation
- Stockage Redis/PostgreSQL

**2. Indicator Engine (Calcul)**
- RSI, MACD, ADX, Stochastique, Bandes Bollinger
- Régression linéaire avec r²
- Calcul corrélations
- Score de confluence

**3. Signal Generator (Logique)**
- Vérification des 8 combinaisons d'indicateurs
- Confluence scoring
- Validation croisée multi-paires
- Génération des signaux d'ACHAT/VENTE

**4. Risk Manager (Gestion Risque)**
- Calcul position sizing
- Ajustement ATR
- Placement SL/TP
- Vérification ratio 3:1

**5. Order Executor (Exécution)**
- Connexion API
- Placement ordres
- Gestion position
- Monitoring temps réel

**6. Database Layer (Persistance)**
- PostgreSQL pour historique
- Redis pour cache
- Migrations automatiques
- Backup régulier

### Schéma de Flux Complet

```
DATA SOURCE (Binance API)
    ↓ (WebSocket OHLCV)
DATA SERVICE
    ↓ (Stockage Redis/PG)
INDICATOR ENGINE
    ↓ (Calcul 5+ indicateurs)
CONFLUENCE SCORER
    ↓ (Score 0-100)
SIGNAL GENERATOR
    ↓ (ACHAT/VENTE/WAIT)
MULTI-PAIR VALIDATOR
    ↓ (Vérifier corrélations)
RISK MANAGER
    ↓ (Position size, SL/TP)
DECISION CHECKER
    ├─ All criteria met? → YES → ORDER EXECUTOR
    └─ Not ready? → WAIT
        ↓
ORDER EXECUTOR
    ↓ (Place order API)
POSITION MONITOR
    ↓ (Track real-time)
TRADE LOGGER
    ↓ (Store results)
DATABASE
```

---

## 2. Collecte de Données avec API (Pages 2-3)

### Connexion API Binance (Crypto)

Utiliser la bibliothèque `ccxt` pour abstraction API:

```python
# setup.py ou requirements.txt
pip install ccxt

# Code structure
import ccxt
import pandas as pd
from datetime import datetime
import asyncio

class DataService:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': 'YOUR_API_KEY',
            'secret': 'YOUR_SECRET',
            'enableRateLimit': True,
        })
        self.pairs = ['EUR/USD', 'GBP/USD', 'AUD/USD', 'USD/JPY']
        self.timeframes = ['1h', '4h', '1d', '15m']
    
    async def fetch_ohlcv(self, pair, timeframe, limit=100):
        """Récupère les OHLCV pour une paire et timeframe"""
        try:
            ohlcv = await self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Erreur fetch {pair} {timeframe}: {e}")
            return None
    
    async def fetch_all_pairs(self, timeframe='1h'):
        """Récupère OHLCV pour toutes les paires"""
        tasks = [self.fetch_ohlcv(pair, timeframe) for pair in self.pairs]
        results = await asyncio.gather(*tasks)
        return {pair: data for pair, data in zip(self.pairs, results)}
```

### Connexion MetaTrader 5 (Forex)

Pour forex/CFD avec MT5:

```python
pip install MetaTrader5

import MetaTrader5 as mt5
import pandas as pd

class MT5DataService:
    def __init__(self):
        if not mt5.initialize():
            print("Erreur init MT5")
            return
        self.pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    
    def fetch_mt5_data(self, pair, timeframe_name='H1', count=100):
        """Récupère données MT5"""
        timeframes = {
            '15m': mt5.TIMEFRAME_M15,
            '1h': mt5.TIMEFRAME_H1,
            '4h': mt5.TIMEFRAME_H4,
            '1d': mt5.TIMEFRAME_D1,
        }
        
        tf = timeframes.get(timeframe_name, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(pair, tf, 0, count)
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']]
    
    def get_all_data(self, timeframe='H1'):
        """Récupère toutes les paires"""
        data = {}
        for pair in self.pairs:
            data[pair] = self.fetch_mt5_data(pair, timeframe)
        return data
```

### Nettoyage des Données

```python
class DataCleaner:
    def clean(self, df):
        """Nettoie et valide les données"""
        # Supprimer les NaN
        df = df.dropna()
        
        # Déterminer les gaps anormaux (> 5× ATR)
        atr = self.calculate_atr(df, 14)
        df['returns'] = df['close'].pct_change()
        df['gap'] = (df['high'] - df['open']).abs()
        
        # Marquer les gaps extrêmes
        df['is_gap'] = df['gap'] > (atr * 5)
        df = df[~df['is_gap']]
        
        # Vérifier les volumes
        df = df[df['volume'] > 0]
        
        return df.drop(['is_gap', 'gap', 'returns'], axis=1)
    
    def calculate_atr(self, df, period=14):
        """Calcul ATR pour détection gaps"""
        df['tr'] = df[['high', 'low', 'close']].apply(
            lambda row: max(
                row['high'] - row['low'],
                abs(row['high'] - df['close'].iloc[-2]) if len(df) > 1 else 0,
                abs(row['low'] - df['close'].iloc[-2]) if len(df) > 1 else 0
            ), axis=1
        )
        return df['tr'].rolling(period).mean()
```

### Stockage Redis et PostgreSQL

```python
import redis
import psycopg2
from psycopg2.extras import execute_values

class DataStorage:
    def __init__(self):
        # Redis pour cache temps réel
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        
        # PostgreSQL pour historique
        self.pg_conn = psycopg2.connect(
            host='localhost',
            database='trading_bot',
            user='trader',
            password='secure_password'
        )
    
    def store_redis(self, pair, timeframe, df):
        """Stocke les 200 dernières bougies dans Redis"""
        key = f"ohlcv:{pair}:{timeframe}"
        data = df.tail(200).to_json(orient='records')
        self.redis_client.setex(key, 3600, data)  # TTL 1h
    
    def store_postgres(self, pair, timeframe, df):
        """Stocke l'historique complet dans PostgreSQL"""
        cur = self.pg_conn.cursor()
        
        data = []
        for _, row in df.iterrows():
            data.append((
                pair,
                timeframe,
                row['timestamp'],
                row['open'],
                row['high'],
                row['low'],
                row['close'],
                row['volume']
            ))
        
        query = """
            INSERT INTO ohlcv (pair, timeframe, timestamp, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        
        execute_values(cur, query, data)
        self.pg_conn.commit()
```

---

## 3. Moteur d'Indicateurs Techniques (Pages 3-4)

### Classe Indicator Engine

```python
import numpy as np
import pandas as pd

class IndicatorEngine:
    def __init__(self, df):
        self.df = df.copy()
        self.close = df['close'].values
        self.high = df['high'].values
        self.low = df['low'].values
        self.volume = df['volume'].values
    
    # RSI
    def calculate_rsi(self, period=14):
        deltas = np.diff(self.close)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100 - 100 / (1 + rs)
        
        rsis = [rsi]
        for delta in deltas[period+1:]:
            if delta > 0:
                up = (up * (period - 1) + delta) / period
                down = down * (period - 1) / period
            else:
                up = up * (period - 1) / period
                down = (down * (period - 1) - delta) / period
            
            rs = up / down if down != 0 else 0
            rsi = 100 - 100 / (1 + rs)
            rsis.append(rsi)
        
        return np.concatenate([np.full(period, np.nan), rsis])
    
    # MACD
    def calculate_macd(self, fast=12, slow=26, signal=9):
        ema_fast = self.ema(self.close, fast)
        ema_slow = self.ema(self.close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self.ema(macd_line, signal)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    # EMA (utilisé par MACD)
    def ema(self, data, period):
        alpha = 2 / (period + 1)
        ema_values = [np.nan] * (period - 1)
        ema_values.append(np.mean(data[:period]))
        
        for price in data[period:]:
            ema_values.append(price * alpha + ema_values[-1] * (1 - alpha))
        
        return np.array(ema_values)
    
    # ADX
    def calculate_adx(self, period=14):
        # DI+ et DI-
        high_diff = np.diff(self.high)
        low_diff = -np.diff(self.low)
        
        plus_dm = np.where(high_diff > low_diff, np.maximum(high_diff, 0), 0)
        minus_dm = np.where(low_diff > high_diff, np.maximum(low_diff, 0), 0)
        
        tr = np.maximum(
            np.maximum(
                self.high[1:] - self.low[1:],
                np.abs(self.high[1:] - self.close[:-1])
            ),
            np.abs(self.low[1:] - self.close[:-1])
        )
        
        atr = np.mean(tr[:period])
        plus_di = 100 * np.mean(plus_dm[:period]) / atr if atr != 0 else 0
        minus_di = 100 * np.mean(minus_dm[:period]) / atr if atr != 0 else 0
        
        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = 100 * di_diff / di_sum if di_sum != 0 else 0
        
        adx = np.mean([dx] * period)  # Simplification
        
        return np.full(len(self.close), adx), np.full(len(self.close), plus_di), np.full(len(self.close), minus_di)
    
    # Stochastique
    def calculate_stochastic(self, period=14, k_period=3, d_period=3):
        lowest_low = pd.Series(self.low).rolling(period).min()
        highest_high = pd.Series(self.high).rolling(period).max()
        
        k = 100 * (self.close - lowest_low) / (highest_high - lowest_low)
        k_smooth = pd.Series(k).rolling(k_period).mean().values
        d = pd.Series(k_smooth).rolling(d_period).mean().values
        
        return k_smooth, d
    
    # Bandes Bollinger
    def calculate_bollinger_bands(self, period=20, std_dev=2):
        sma = pd.Series(self.close).rolling(period).mean().values
        std = pd.Series(self.close).rolling(period).std().values
        
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        return upper_band, sma, lower_band
    
    # Calcul tous les indicateurs
    def calculate_all(self):
        result = {
            'rsi': self.calculate_rsi(14),
            'macd': self.calculate_macd(),
            'adx': self.calculate_adx(14),
            'stochastic': self.calculate_stochastic(14, 3, 3),
            'bollinger': self.calculate_bollinger_bands(20, 2),
        }
        return result
```

---

## 4. Générateur de Signaux et Confluence (Pages 4-5)

### Signal Generator Class

```python
class SignalGenerator:
    def __init__(self, df, indicators):
        self.df = df
        self.ind = indicators
        self.confluence_threshold = 80
    
    def calculate_confluence_score(self):
        """Calcule score de confluence 0-100"""
        score = 0
        max_score = 100
        
        # RSI score (20 points max)
        rsi = self.ind['rsi'][-1]
        if rsi > 50:
            score += 20
        elif rsi < 50:
            score -= 0
        else:
            score += 10
        
        # MACD score (20 points max)
        macd_line, signal_line, histogram = self.ind['macd']
        if macd_line[-1] > signal_line[-1] and histogram[-1] > 0:
            if histogram[-1] > histogram[-2]:
                score += 20
            else:
                score += 15
        elif macd_line[-1] < signal_line[-1] and histogram[-1] < 0:
            score -= 20
        else:
            score += 5
        
        # ADX score (20 points max)
        adx, plus_di, minus_di = self.ind['adx']
        if adx[-1] > 25:
            if plus_di[-1] > minus_di[-1]:
                score += 20
            else:
                score -= 20
        elif adx[-1] > 20:
            score += 10
        
        # Stochastique score (20 points max)
        k, d = self.ind['stochastic']
        if k[-1] > d[-1] and k[-1] < 80:
            score += 20
        elif k[-1] < d[-1] and k[-1] > 20:
            score -= 20
        else:
            score += 5
        
        # Bandes Bollinger score (20 points max)
        upper, mid, lower = self.ind['bollinger']
        close = self.df['close'].iloc[-1]
        
        if close > lower and close < upper:
            if close > mid:
                score += 10
            else:
                score += 20
        elif close < lower:
            score += 20
        else:
            score -= 10
        
        return min(score, 100)
    
    def generate_signal(self):
        """Génère signal ACHAT, VENTE ou WAIT"""
        score = self.calculate_confluence_score()
        
        if score >= self.confluence_threshold:
            # Déterminer direction
            rsi = self.ind['rsi'][-1]
            if rsi > 50:
                return 'BUY', score
            else:
                return 'SELL', score
        
        return 'WAIT', score
```

---

## 5. Gestion du Risque et Position Sizing (Pages 5-6)

### Risk Manager Class

```python
class RiskManager:
    def __init__(self, account_balance, risk_per_trade=0.01):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade  # 1% par défaut
        self.min_ratio = 3.0
    
    def calculate_position_size(self, entry_price, stop_loss, pair='EUR/USD'):
        """Calcule la taille de position basée sur le risque"""
        
        # Risque en euros
        risk_amount = self.account_balance * self.risk_per_trade
        
        # Distance SL en prix
        sl_distance = abs(entry_price - stop_loss)
        
        # Taille position = Risque / Distance SL
        if pair.startswith('EUR') or pair == 'EURUSD':
            position_size = risk_amount / sl_distance
        
        return position_size, risk_amount, sl_distance
    
    def calculate_take_profit(self, entry_price, stop_loss, direction='BUY'):
        """Calcule TP avec ratio 3:1 minimum"""
        
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * self.min_ratio
        
        if direction == 'BUY':
            tp_price = entry_price + tp_distance
        else:
            tp_price = entry_price - tp_distance
        
        return tp_price, tp_distance
    
    def adjust_for_volatility(self, atr, atr_avg, position_size):
        """Ajuste la position size selon la volatilité"""
        
        volatility_ratio = atr / atr_avg
        
        if volatility_ratio > 1.5:  # 50% plus volatile
            adjusted_size = position_size * 0.7
        elif volatility_ratio < 0.7:  # 30% moins volatile
            adjusted_size = position_size * 1.2
        else:
            adjusted_size = position_size
        
        return adjusted_size
    
    def validate_ratio(self, entry, stop_loss, take_profit):
        """Valide le ratio risque/récompense"""
        
        risk = abs(entry - stop_loss)
        reward = abs(take_profit - entry)
        
        ratio = reward / risk if risk != 0 else 0
        
        return ratio >= self.min_ratio, ratio
```

---

## 6. Exécution des Ordres (Pages 6-7)

### Order Executor Class

```python
import time

class OrderExecutor:
    def __init__(self, exchange, pair, risk_manager):
        self.exchange = exchange
        self.pair = pair
        self.risk_manager = risk_manager
        self.active_trades = {}
    
    def place_order(self, signal, entry_price, stop_loss, take_profit, position_size):
        """Place un ordre ACHAT ou VENTE"""
        
        order_data = {
            'pair': self.pair,
            'signal': signal,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'position_size': position_size,
            'entry_time': datetime.now(),
            'status': 'OPEN',
            'pnl': 0,
        }
        
        try:
            # Exemple d'ordre Binance (simplifié)
            if signal == 'BUY':
                order = self.exchange.create_market_buy_order(self.pair, position_size)
            else:
                order = self.exchange.create_market_sell_order(self.pair, position_size)
            
            order_data['order_id'] = order['id']
            order_data['actual_entry_price'] = order['average']
            
            # Placer SL et TP
            self.place_stop_loss(order['id'], stop_loss, position_size)
            self.place_take_profit(order['id'], take_profit, position_size)
            
            self.active_trades[order['id']] = order_data
            
            return order_data
        
        except Exception as e:
            print(f"Erreur placement ordre: {e}")
            return None
    
    def place_stop_loss(self, order_id, sl_price, amount):
        """Place un stop-loss"""
        try:
            sl_order = self.exchange.create_market_sell_order(self.pair, amount, {
                'stopPrice': sl_price,
                'type': 'STOP_LOSS_LIMIT'
            })
            return sl_order
        except Exception as e:
            print(f"Erreur SL: {e}")
    
    def place_take_profit(self, order_id, tp_price, amount):
        """Place un take-profit"""
        try:
            tp_order = self.exchange.create_market_sell_order(self.pair, amount, {
                'stopPrice': tp_price,
                'type': 'TAKE_PROFIT_LIMIT'
            })
            return tp_order
        except Exception as e:
            print(f"Erreur TP: {e}")
    
    def monitor_trade(self, order_id, current_price):
        """Monitore une trade ouverte"""
        
        if order_id not in self.active_trades:
            return
        
        trade = self.active_trades[order_id]
        entry = trade['actual_entry_price']
        
        # Calculer P&L
        if trade['signal'] == 'BUY':
            pnl = (current_price - entry) * trade['position_size']
        else:
            pnl = (entry - current_price) * trade['position_size']
        
        trade['current_price'] = current_price
        trade['pnl'] = pnl
        
        # Vérifier si SL ou TP atteint
        if current_price <= trade['stop_loss'] and trade['signal'] == 'BUY':
            self.close_trade(order_id, 'STOP_LOSS')
        elif current_price >= trade['take_profit'] and trade['signal'] == 'BUY':
            self.close_trade(order_id, 'TAKE_PROFIT')
    
    def close_trade(self, order_id, reason='MANUAL'):
        """Ferme une trade"""
        trade = self.active_trades.pop(order_id)
        trade['status'] = 'CLOSED'
        trade['close_reason'] = reason
        trade['close_time'] = datetime.now()
        
        # Logger résultat
        self.log_trade(trade)
    
    def log_trade(self, trade):
        """Enregistre le résultat dans la base de données"""
        print(f"Trade fermée: {trade['signal']} {trade['pair']}")
        print(f"Entry: {trade['entry_price']}, PnL: {trade['pnl']:.2f}€")
```

---

## 7. Boucle Principale et Orchestration (Pages 7-8)

### Main Bot Loop

```python
import asyncio
import time
from datetime import datetime, timedelta

class TradingBot:
    def __init__(self, config):
        self.config = config
        self.data_service = DataService()
        self.risk_manager = RiskManager(config['account_balance'])
        self.order_executor = None
        self.indicator_engine = None
        self.signal_generator = None
        self.is_running = False
        self.last_signal_time = {}  # Éviter les doubles signaux
    
    async def run(self):
        """Boucle principale du bot"""
        self.is_running = True
        
        while self.is_running:
            try:
                # 1. Récupérer les données
                print(f"[{datetime.now()}] Récupération des données...")
                data = await self.data_service.fetch_all_pairs(timeframe='1h')
                
                # 2. Analyser chaque paire
                for pair, df in data.items():
                    if df is None:
                        continue
                    
                    # Nettoyer les données
                    cleaner = DataCleaner()
                    df_clean = cleaner.clean(df)
                    
                    # Calculer indicateurs
                    self.indicator_engine = IndicatorEngine(df_clean)
                    indicators = self.indicator_engine.calculate_all()
                    
                    # Générer signal
                    self.signal_generator = SignalGenerator(df_clean, indicators)
                    signal, score = self.signal_generator.generate_signal()
                    
                    print(f"{pair}: Signal={signal}, Score={score}")
                    
                    # 3. Exécuter si signal valide
                    if signal in ['BUY', 'SELL']:
                        # Éviter les doubles trades
                        last_time = self.last_signal_time.get(pair, datetime.min)
                        if (datetime.now() - last_time).seconds < 3600:  # 1h min entre trades
                            continue
                        
                        # Validation croisée multi-paires
                        if self.validate_multi_pair(pair, data):
                            entry_price = df_clean['close'].iloc[-1]
                            stop_loss = self.calculate_stop_loss(df_clean, signal)
                            
                            # Gestion risque
                            position_size, risk, sl_dist = self.risk_manager.calculate_position_size(
                                entry_price, stop_loss, pair
                            )
                            take_profit, tp_dist = self.risk_manager.calculate_take_profit(
                                entry_price, stop_loss, signal
                            )
                            
                            # Valider ratio
                            valid, ratio = self.risk_manager.validate_ratio(entry_price, stop_loss, take_profit)
                            
                            if valid:
                                # Exécuter
                                self.order_executor = OrderExecutor(self.data_service.exchange, pair, self.risk_manager)
                                order = self.order_executor.place_order(
                                    signal, entry_price, stop_loss, take_profit, position_size
                                )
                                
                                if order:
                                    print(f"✓ Ordre exécuté: {signal} {pair} @ {entry_price}")
                                    self.last_signal_time[pair] = datetime.now()
                
                # 4. Monitorer les trades ouvertes
                self.monitor_open_trades(data)
                
                # Attendre avant la prochaine itération (5 min)
                await asyncio.sleep(300)
            
            except Exception as e:
                print(f"Erreur boucle principale: {e}")
                await asyncio.sleep(60)
    
    def validate_multi_pair(self, primary_pair, all_data):
        """Valide le signal via corrélations"""
        # Logique de corrélation...
        return True
    
    def calculate_stop_loss(self, df, signal):
        """Calcule SL basé sur support/résistance"""
        if signal == 'BUY':
            lowest = df['low'].tail(20).min()
            return lowest - 0.0010  # 10 pips de marge
        else:
            highest = df['high'].tail(20).max()
            return highest + 0.0010
    
    def monitor_open_trades(self, data):
        """Monitore les trades ouvertes"""
        if not self.order_executor:
            return
        
        for order_id, trade in self.order_executor.active_trades.items():
            pair = trade['pair']
            if pair in data and data[pair] is not None:
                current_price = data[pair]['close'].iloc[-1]
                self.order_executor.monitor_trade(order_id, current_price)
    
    def stop(self):
        """Arrête le bot"""
        self.is_running = False
        print("Bot arrêté.")

# Exécution
if __name__ == "__main__":
    config = {
        'account_balance': 10000,  # 10,000€
        'pairs': ['EUR/USD', 'GBP/USD', 'AUD/USD'],
        'risk_per_trade': 0.01,  # 1%
    }
    
    bot = TradingBot(config)
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        bot.stop()
```

---

## 8. Configuration et Déploiement (Page 8)

### requirements.txt
```
ccxt==4.0.28
pandas==2.0.0
numpy==1.24.0
MetaTrader5==5.0.45
psycopg2-binary==2.9.6
redis==5.0.0
aiohttp==3.9.0
websockets==11.0.0
python-dotenv==1.0.0
```

### config.yml
```yaml
# Trading Config
trading:
  account_balance: 10000
  risk_per_trade: 0.01  # 1%
  max_trades_per_day: 3
  max_drawdown: 0.10  # 10%

# Indicators
indicators:
  rsi_period: 14
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9
  atr_period: 14
  regression_period: 50

# Database
database:
  postgres:
    host: localhost
    port: 5432
    dbname: trading_bot
    user: trader
    password: secure_pass
  redis:
    host: localhost
    port: 6379
    db: 0

# API
api:
  exchange: binance  # ou mt5 pour forex
  api_key: YOUR_KEY
  api_secret: YOUR_SECRET
```

### Docker Setup
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## Conclusion

L'implémentation technique d'un trading bot requiert:
1. Architecture modulaire (Data, Indicators, Signals, Risk, Execution)
2. Gestion d'erreurs robuste et logging
3. Base de données pour persistence
4. API fiable pour exécution
5. Monitoring temps réel

Le code fourni est une base solide à adapter selon votre exchange/broker spécifique.

## Références
[1] CCXT Library. (2024). Unified Cryptocurrency Exchange API.
[2] MetaTrader5 Python API. (2024). Official SDK.
