"""Trading Arena Configuration"""

# Race Settings
RACE_DURATION_HOURS = 3
STARTING_CAPITAL = 1000.0
BOTS_PER_RACE = 5

# Risk Tiers
RISK_TIERS = {
    "moderate": {"max_leverage": 5, "max_position_pct": 0.3},
    "high": {"max_leverage": 20, "max_position_pct": 0.5},
    "yolo": {"max_leverage": 50, "max_position_pct": 1.0},
}

# Trading Universe - Assets bots can trade
TRADING_UNIVERSE = [
    # Crypto
    "BTC-USD", "ETH-USD", "SOL-USD", "AVAX-USD", "LINK-USD",
    "OP-USD", "ARB-USD", "MATIC-USD", "DOGE-USD", "SHIB-USD",
    # FX
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X",
    # Stocks (if market open)
    "SPY", "QQQ", "NVDA", "TSLA", "AMD", "AAPL",
]

# Bot Colors for Dashboard
BOT_COLORS = ["🔴", "🟠", "🟡", "🟢", "🔵", "🟣", "⚪", "🟤", "⬛", "🩷"]

# Evolution Settings
SURVIVAL_THRESHOLD = 0.4  # Bottom 40% get culled
MUTATION_RATE = 0.2  # 20% parameter variation when cloning winners
