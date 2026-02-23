"""
LLM Strategy Generator - Creates unique trading strategies for each character.
Hybrid approach: LLM generates strategy once, Python executes fast.
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List


def generate_strategy_for_character(character: str) -> Dict:
    """Generate a strategy for a character."""
    
    print(f"Generating strategy for {character}...")
    
    templates = {
        "Harper": {
            "strategy_name": "Trend Surfer Pro",
            "philosophy": "Ride the wave, never fight the trend",
            "entry_rules": [
                "Price breaks above 20-period EMA",
                "RSI(14) > 50 and rising",
                "Volume > 1.5x average"
            ],
            "exit_rules": [
                "Stop loss at -5%",
                "Take profit at +15%",
                "Price closes below 20 EMA"
            ],
            "risk_management": {"stop_loss": "5%", "take_profit": "15%", "max_positions": 3, "leverage": "10x"},
            "preferred_assets": ["BTC-USD", "QQQ", "NVDA"],
            "timeframe": "5min"
        },
        "Rishi": {
            "strategy_name": "Blade Runner",
            "philosophy": "Cut losses fast, let winners run briefly",
            "entry_rules": [
                "1-minute breakout above resistance",
                "Order book imbalance bullish",
                "Momentum spike detected"
            ],
            "exit_rules": [
                "Stop loss at -2%",
                "Take profit at +4%",
                "Hold time > 10 minutes"
            ],
            "risk_management": {"stop_loss": "2%", "take_profit": "4%", "max_positions": 4, "leverage": "15x"},
            "preferred_assets": ["BTC-USD", "ETH-USD", "SOL-USD"],
            "timeframe": "1min"
        },
        "Yasmin": {
            "strategy_name": "Whale Watcher Elite",
            "philosophy": "Let others test the water, then dive in",
            "entry_rules": [
                "Smart money flow positive for 5+ minutes",
                "Large block trades detected",
                "Price stability after initial move"
            ],
            "exit_rules": [
                "Stop loss at -4%",
                "Take profit at +8%",
                "Whale flow reverses"
            ],
            "risk_management": {"stop_loss": "4%", "take_profit": "8%", "max_positions": 2, "leverage": "5x"},
            "preferred_assets": ["BTC-USD", "ETH-USD"],
            "timeframe": "15min"
        },
        "Gus": {
            "strategy_name": "Statistical Arbitrage",
            "philosophy": "Markets revert to mean, always",
            "entry_rules": [
                "RSI(14) < 30 (oversold)",
                "Price 2+ std dev below mean",
                "Volume declining (capitulation)"
            ],
            "exit_rules": [
                "Stop loss at -8%",
                "Take profit at mean reversion",
                "RSI returns to 50"
            ],
            "risk_management": {"stop_loss": "8%", "take_profit": "10%", "max_positions": 3, "leverage": "8x"},
            "preferred_assets": ["ETH-USD", "BTC-USD", "SPY"],
            "timeframe": "15min"
        },
        "Robert": {
            "strategy_name": "YOLO Momentum",
            "philosophy": "Fortune favors the bold",
            "entry_rules": [
                "FOMO indicator maxed",
                "Price up 3% in 5 minutes",
                "Social sentiment surging"
            ],
            "exit_rules": [
                "Stop loss at -5%",
                "Take profit at +20%",
                "Momentum stalls"
            ],
            "risk_management": {"stop_loss": "5%", "take_profit": "20%", "max_positions": 1, "leverage": "20x"},
            "preferred_assets": ["SOL-USD", "DOGE-USD", "AMD"],
            "timeframe": "3min"
        },
        "Eric": {
            "strategy_name": "Breakout Master",
            "philosophy": "Patience and confirmation win wars",
            "entry_rules": [
                "Clean breakout above resistance",
                "Volume confirms the move",
                "Retest holds as support"
            ],
            "exit_rules": [
                "Stop loss below breakout level",
                "Take profit at next resistance",
                "Breakdown below support"
            ],
            "risk_management": {"stop_loss": "7%", "take_profit": "20%", "max_positions": 2, "leverage": "10x"},
            "preferred_assets": ["BTC-USD", "ETH-USD", "NVDA"],
            "timeframe": "30min"
        },
        "Danny": {
            "strategy_name": "ALL IN",
            "philosophy": "YOLO - You Only Live Once",
            "entry_rules": [
                "Gut feeling says yes",
                "Saw it on Twitter",
                "FOMO is strong"
            ],
            "exit_rules": [
                "Margin call",
                "100% gain",
                "Never (diamond hands)"
            ],
            "risk_management": {"stop_loss": "15%", "take_profit": "50%", "max_positions": 1, "leverage": "20x"},
            "preferred_assets": ["DOGE-USD", "SHIB-USD", "SOL-USD"],
            "timeframe": "1min"
        }
    }
    
    template = templates.get(character, templates["Harper"])
    template["character"] = character
    template["created_at"] = datetime.utcnow().isoformat()
    
    return template


def generate_race_strategies(race_id: str, characters: List[str] = None) -> Dict[str, Dict]:
    """Generate strategies for all characters in a race."""
    
    if characters is None:
        characters = ["Harper", "Rishi", "Yasmin", "Gus", "Robert"]
    
    strategies = {}
    
    print(f"Generating strategies for Race {race_id}...")
    print("=" * 60)
    
    for character in characters:
        strategy = generate_strategy_for_character(character)
        strategies[character] = strategy
        print(f"{character}: {strategy['strategy_name']} ({strategy['risk_management']['leverage']} leverage)")
    
    # Save strategies
    strategies_dir = f"races/{race_id}/strategies"
    os.makedirs(strategies_dir, exist_ok=True)
    
    with open(f"{strategies_dir}/race_strategies.json", "w") as f:
        json.dump(strategies, f, indent=2)
    
    print(f"\nStrategies saved to {strategies_dir}/race_strategies.json")
    
    return strategies


def mutate_strategy(parent_strategy: Dict, generation: int = 2) -> Dict:
    """Create a mutated version of a winning strategy."""
    
    character = parent_strategy["character"]
    
    mutations = [
        "Tightened stop loss by 1%",
        "Added volume confirmation",
        "Extended hold time",
        "Added RSI filter",
        "Increased leverage slightly"
    ]
    
    mutated = parent_strategy.copy()
    mutated["strategy_name"] = f"{parent_strategy['strategy_name']} v{generation}"
    mutated["philosophy"] = f"{parent_strategy['philosophy']} (Refined)"
    mutated["generation"] = generation
    mutated["parent"] = parent_strategy["strategy_name"]
    mutated["mutation"] = random.choice(mutations)
    mutated["created_at"] = datetime.utcnow().isoformat()
    
    leverage = int(parent_strategy["risk_management"]["leverage"].rstrip("x"))
    mutated["risk_management"]["leverage"] = f"{min(leverage + 2, 20)}x"
    
    return mutated


if __name__ == "__main__":
    strategies = generate_race_strategies("race_2", ["Harper", "Rishi", "Yasmin", "Gus", "Robert", "Eric", "Danny"])
    print("\nAll strategies generated for 7 traders!")
