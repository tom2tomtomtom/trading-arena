"""
Paper Trading Execution Engine - Executes trades for agents using real market data.
"""

import json
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Try to import from parent project's data sources
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "day-trader"))
sys.path.insert(0, str(Path(__file__).parent.parent / "market-behavior"))


class PaperTrader:
    """Executes paper trades using real market data."""
    
    def __init__(self):
        self.price_cache: Dict[str, Tuple[float, datetime]] = {}
        self.cache_duration = timedelta(seconds=30)
    
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol."""
        # Check cache
        if symbol in self.price_cache:
            price, cached_at = self.price_cache[symbol]
            if datetime.utcnow() - cached_at < self.cache_duration:
                return price
        
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                self.price_cache[symbol] = (price, datetime.utcnow())
                return price
        except Exception as e:
            print(f"Error getting price for {symbol}: {e}")
        
        return None
    
    def execute_entry(
        self,
        agent,
        symbol: str,
        direction: str,  # "LONG" or "SHORT"
        size_pct: float,  # Percentage of capital to use
        leverage: float = 1.0,
        reason: str = "",
    ) -> Optional[Dict]:
        """Execute an entry trade for an agent."""
        
        price = self.get_price(symbol)
        if not price:
            return None
        
        # Calculate position size
        capital_to_use = agent.cash * size_pct
        notional_value = capital_to_use * leverage
        qty = notional_value / price
        
        # Margin required (simplified)
        margin_required = capital_to_use
        
        if margin_required > agent.cash:
            print(f"Insufficient funds: need ${margin_required:.2f}, have ${agent.cash:.2f}")
            return None
        
        # Deduct margin from cash
        agent.cash -= margin_required
        
        # Create position
        position = {
            "symbol": symbol,
            "direction": direction,
            "qty": qty,
            "entry_price": price,
            "entry_time": datetime.utcnow().isoformat(),
            "leverage": leverage,
            "margin": margin_required,
            "notional_value": notional_value,
            "unrealized_pnl": 0.0,
            "reason": reason,
        }
        
        agent.positions[symbol] = position
        
        # Log trade
        trade_log = {
            "type": "ENTRY",
            "symbol": symbol,
            "direction": direction,
            "price": price,
            "qty": qty,
            "leverage": leverage,
            "margin": margin_required,
            "time": datetime.utcnow().isoformat(),
            "reason": reason,
        }
        agent.trades.append(trade_log)
        
        return position
    
    def execute_exit(
        self,
        agent,
        symbol: str,
        reason: str = "",
    ) -> Optional[Dict]:
        """Exit a position for an agent."""
        
        if symbol not in agent.positions:
            return None
        
        position = agent.positions[symbol]
        current_price = self.get_price(symbol)
        
        if not current_price:
            return None
        
        # Calculate P&L
        if position["direction"] == "LONG":
            pnl = (current_price - position["entry_price"]) * position["qty"]
        else:  # SHORT
            pnl = (position["entry_price"] - current_price) * position["qty"]
        
        pnl_pct = (pnl / position["margin"]) * 100
        
        # Return margin + P&L to cash
        agent.cash += position["margin"] + pnl
        
        # Remove position
        del agent.positions[symbol]
        
        # Log trade
        trade_log = {
            "type": "EXIT",
            "symbol": symbol,
            "direction": position["direction"],
            "entry_price": position["entry_price"],
            "exit_price": current_price,
            "qty": position["qty"],
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "hold_time": str(datetime.utcnow() - datetime.fromisoformat(position["entry_time"])),
            "time": datetime.utcnow().isoformat(),
            "reason": reason,
        }
        agent.trades.append(trade_log)
        
        return trade_log
    
    def update_positions(self, agent) -> None:
        """Update unrealized P&L for all positions."""
        for symbol, position in agent.positions.items():
            current_price = self.get_price(symbol)
            if current_price:
                if position["direction"] == "LONG":
                    pnl = (current_price - position["entry_price"]) * position["qty"]
                else:
                    pnl = (position["entry_price"] - current_price) * position["qty"]
                position["unrealized_pnl"] = pnl
                position["current_price"] = current_price
    
    def check_stop_loss(self, agent, stop_loss_pct: float) -> List[Dict]:
        """Check and execute stop losses."""
        exits = []
        symbols_to_exit = []
        
        for symbol, position in agent.positions.items():
            current_price = self.get_price(symbol)
            if not current_price:
                continue
            
            if position["direction"] == "LONG":
                pnl_pct = ((current_price - position["entry_price"]) / position["entry_price"]) * 100
            else:
                pnl_pct = ((position["entry_price"] - current_price) / position["entry_price"]) * 100
            
            if pnl_pct <= -stop_loss_pct * 100:
                symbols_to_exit.append(symbol)
        
        for symbol in symbols_to_exit:
            exit_result = self.execute_exit(agent, symbol, reason="STOP_LOSS")
            if exit_result:
                exits.append(exit_result)
        
        return exits
    
    def check_take_profit(self, agent, take_profit_pct: float) -> List[Dict]:
        """Check and execute take profits."""
        exits = []
        symbols_to_exit = []
        
        for symbol, position in agent.positions.items():
            current_price = self.get_price(symbol)
            if not current_price:
                continue
            
            if position["direction"] == "LONG":
                pnl_pct = ((current_price - position["entry_price"]) / position["entry_price"]) * 100
            else:
                pnl_pct = ((position["entry_price"] - current_price) / position["entry_price"]) * 100
            
            if pnl_pct >= take_profit_pct * 100:
                symbols_to_exit.append(symbol)
        
        for symbol in symbols_to_exit:
            exit_result = self.execute_exit(agent, symbol, reason="TAKE_PROFIT")
            if exit_result:
                exits.append(exit_result)
        
        return exits


class SignalGenerator:
    """Generates trading signals based on agent's strategy."""
    
    def __init__(self):
        self.paper_trader = PaperTrader()
    
    def get_market_data(self, symbol: str, period: str = "1d", interval: str = "5m") -> Optional[Dict]:
        """Get market data for analysis."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            if hist.empty:
                return None
            
            current_price = float(hist["Close"].iloc[-1])
            open_price = float(hist["Open"].iloc[0])
            high = float(hist["High"].max())
            low = float(hist["Low"].min())
            volume = float(hist["Volume"].sum())
            
            # Simple indicators
            sma_20 = float(hist["Close"].tail(20).mean()) if len(hist) >= 20 else current_price
            
            # RSI (simplified)
            delta = hist["Close"].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs.iloc[-1])) if not loss.iloc[-1] == 0 else 50
            
            # Trend
            trend = "UP" if current_price > sma_20 else "DOWN"
            
            # Change
            change_pct = ((current_price - open_price) / open_price) * 100
            
            return {
                "symbol": symbol,
                "price": current_price,
                "open": open_price,
                "high": high,
                "low": low,
                "volume": volume,
                "sma_20": sma_20,
                "rsi": float(rsi) if not pd.isna(rsi) else 50,
                "trend": trend,
                "change_pct": change_pct,
            }
        except Exception as e:
            print(f"Error getting market data for {symbol}: {e}")
            return None
    
    def generate_signal(self, agent, symbol: str) -> Optional[Dict]:
        """Generate trading signal based on agent's strategy archetype."""
        
        data = self.get_market_data(symbol)
        if not data:
            return None
        
        archetype = agent.archetype["name"]
        params = agent.strategy_params
        
        signal = None
        
        if archetype == "YOLO":
            # YOLO: Big momentum moves only
            if abs(data["change_pct"]) > 3:
                direction = "LONG" if data["change_pct"] > 0 else "SHORT"
                signal = {
                    "symbol": symbol,
                    "direction": direction,
                    "strength": abs(data["change_pct"]) / 5,
                    "reason": f"YOLO: Big move {data['change_pct']:.1f}%",
                }
        
        elif archetype == "Breakout Hunter":
            # Breakout: Price near high/low
            range_pct = (data["high"] - data["low"]) / data["low"] * 100
            if data["price"] > data["high"] * 0.98 and range_pct > 2:
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": 0.7,
                    "reason": f"Breakout: Near high ${data['high']:.2f}",
                }
            elif data["price"] < data["low"] * 1.02 and range_pct > 2:
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": 0.7,
                    "reason": f"Breakdown: Near low ${data['low']:.2f}",
                }
        
        elif archetype == "Mean Reverter":
            # Mean reversion: Oversold/overbought
            if data["rsi"] < 30:
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": (30 - data["rsi"]) / 30,
                    "reason": f"Oversold: RSI {data['rsi']:.0f}",
                }
            elif data["rsi"] > 70:
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": (data["rsi"] - 70) / 30,
                    "reason": f"Overbought: RSI {data['rsi']:.0f}",
                }
        
        elif archetype == "Trend Follower":
            # Trend: Only trade with SMA direction
            if data["trend"] == "UP" and data["rsi"] < 60:
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": 0.6,
                    "reason": f"Trend: Above SMA, RSI {data['rsi']:.0f}",
                }
            elif data["trend"] == "DOWN" and data["rsi"] > 40:
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": 0.6,
                    "reason": f"Trend: Below SMA, RSI {data['rsi']:.0f}",
                }
        
        elif archetype == "Momentum Surfer":
            # Momentum: Ride the wave
            if data["change_pct"] > 1 and data["trend"] == "UP":
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": data["change_pct"] / 3,
                    "reason": f"Momentum: +{data['change_pct']:.1f}% and trending up",
                }
            elif data["change_pct"] < -1 and data["trend"] == "DOWN":
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": abs(data["change_pct"]) / 3,
                    "reason": f"Momentum: {data['change_pct']:.1f}% and trending down",
                }
        
        elif archetype == "Contrarian":
            # Contrarian: Bet against the crowd
            if data["change_pct"] < -5:
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": abs(data["change_pct"]) / 10,
                    "reason": f"Contrarian: Down {data['change_pct']:.1f}%, buying fear",
                }
            elif data["change_pct"] > 5:
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": data["change_pct"] / 10,
                    "reason": f"Contrarian: Up {data['change_pct']:.1f}%, selling greed",
                }
        
        elif archetype == "Scalper":
            # Scalper: Small moves, frequent trades
            if 0.5 < abs(data["change_pct"]) < 2:
                direction = "LONG" if data["change_pct"] > 0 else "SHORT"
                signal = {
                    "symbol": symbol,
                    "direction": direction,
                    "strength": 0.5,
                    "reason": f"Scalp: {data['change_pct']:.1f}% move",
                }
        
        else:
            # Default: Simple momentum
            if data["change_pct"] > params["entry_threshold"] * 100:
                signal = {
                    "symbol": symbol,
                    "direction": "LONG",
                    "strength": data["change_pct"] / 5,
                    "reason": f"Default: +{data['change_pct']:.1f}%",
                }
            elif data["change_pct"] < -params["entry_threshold"] * 100:
                signal = {
                    "symbol": symbol,
                    "direction": "SHORT",
                    "strength": abs(data["change_pct"]) / 5,
                    "reason": f"Default: {data['change_pct']:.1f}%",
                }
        
        # Filter by entry threshold
        if signal and signal["strength"] < params["entry_threshold"]:
            return None
        
        return signal


# Import pandas for RSI calculation
try:
    import pandas as pd
except ImportError:
    pd = None


if __name__ == "__main__":
    # Test
    trader = PaperTrader()
    print(f"BTC Price: ${trader.get_price('BTC-USD')}")
    print(f"ETH Price: ${trader.get_price('ETH-USD')}")
