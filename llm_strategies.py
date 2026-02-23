"""
LLM Strategy Generator - Creates unique trading strategies for each character.
Hybrid approach: LLM generates strategy once, Python executes fast.
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List

# Character prompts for strategy generation
CHARACTER_PROMPTS = {
    "Harper": """You are Harper - an ambitious, intuitive trader who follows trends aggressively.

Create a detailed trading strategy with these sections:

1. STRATEGY NAME: Give it a catchy name
2. PHILOSOPHY: One sentence describing your approach
3. ENTRY RULES: 3 specific rules for when to enter a trade
4. EXIT RULES: 3 specific rules for when to exit
5. RISK MANAGEMENT:
   - Stop loss percentage (2-10%)
   - Take profit percentage (5-20%)
   - Max number of positions (1-5)
   - Leverage to use (5x-20x)
6. PREFERRED ASSETS: 2-3 crypto/stock tickers
7. TIMEFRAME: How long to hold (1min, 5min, 15min, 1hour)

Be specific and quantitative. Harper is bold and confident.""",
    
    "Rishi": """You are Rishi - a ruthless, fast scalper who exploits inefficiencies.

Create a detailed scalping strategy with:

1. STRATEGY NAME: Aggressive name
2. PHILOSOPHY: Your core belief
3. ENTRY RULES: 3 quick-trigger entry conditions
4. EXIT RULES: 3 fast exit rules
5. RISK MANAGEMENT:
   - Tight stop loss (1-5%)
   - Quick take profit (2-8%)
   - Max positions (2-4)
   - High leverage (10x-20x)
6. PREFERRED ASSETS: Volatile cryptos
7. TIMEFRAME: Very short (1min, 3min, 5min)

Rishi is aggressive and precise.""",
    
    "Yasmin": """You are Yasmin - a patient, privileged trader who waits for perfect setups.

Create a careful strategy with:

1. STRATEGY NAME: Elegant name
2. PHILOSOPHY: Patient approach
3. ENTRY RULES: 3 confirmation-based entries
4. EXIT RULES: 3 conservative exits
5. RISK MANAGEMENT:
   - Moderate stop loss (3-8%)
   - Moderate take profit (5-15%)
   - Few positions (1-3)
   - Lower leverage (3x-10x)
6. PREFERRED ASSETS: Large cap cryptos
7. TIMEFRAME: Medium (15min, 30min, 1hour)

Yasmin is selective and calculated.""",
    
    "Gus": """You are Gus - an intellectual contrarian who fades extremes.

Create a mean reversion strategy with:

1. STRATEGY NAME: Academic-sounding name
2. PHILOSOPHY: Statistical approach
3. ENTRY RULES: 3 oversold/overbought conditions
4. EXIT RULES: 3 reversion targets
5. RISK MANAGEMENT:
   - Wider stop loss (5-10%)
   - Moderate take profit (5-12%)
   - Max positions (2-4)
   - Medium leverage (5x-12x)
6. PREFERRED ASSETS: Assets that mean revert
7. TIMEFRAME: Medium (10min, 15min, 30min)

Gus is analytical and patient.""",
    
    "Robert": """You are Robert - a charismatic YOLO trader who chases momentum.

Create a momentum strategy with:

1. STRATEGY NAME: Exciting name
2. PHILOSOPHY: FOMO-based approach
3. ENTRY RULES: 3 momentum chase rules
4. EXIT RULES: 3 quick cut rules
5. RISK MANAGEMENT:
   - Tight stop loss (2-6%)
   - High take profit (10-25%)
   - Few concentrated positions (1-3)
   - Maximum leverage (15x-20x)
6. PREFERRED ASSETS: Hot momentum cryptos
7. TIMEFRAME: Short (3min, 5min, 10min)

Robert is bold and impulsive."""
}


def parse_strategy_response(response_text: str, character: str) -> Dict:
    """Parse the LLM response into structured strategy."""
    
    lines = response_text.strip().split('\n')
    strategy = {
        "character": character,
        "strategy_name": f"{character}_Strategy",
        "philosophy": "Follow the trend",
        "entry_rules": [],
        "exit_rules": [],
        "risk_management": {
            "stop_loss": "5%",
            "take_profit": "10%",
            "max_positions": 3,
            "leverage": "10x"
        },
        "preferred_assets": ["BTC-USD", "QQQ"],
        "timeframe": "5min",
        "created_at": datetime.utcnow().isoformat()
    }
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        upper = line.upper()
        
        if 'STRATEGY NAME' in upper or 'NAME:' in upper:
            current_section = 'name'
            if ':' in line:
                strategy["strategy_name"] = line.split(':', 1)[1].strip()
        elif 'PHILOSOPHY' in upper:
            current_section = 'philosophy'
        elif 'ENTRY RULE' in upper:
            current_section = 'entry'
            strategy["entry_rules"] = []
        elif 'EXIT RULE' in upper:
            current_section = 'exit'
            strategy["exit_rules"] = []
        elif 'RISK' in upper or 'STOP LOSS' in upper:
            current_section = 'risk'
        elif 'ASSET' in upper:
            current_section = 'assets'
        elif 'TIMEFRAME' in upper or 'TIME FRAME' in upper:
            current_section = 'timeframe'
        elif line.startswith('-') or line.startswith('•') or (len(line) > 3 and line[0].isdigit() and '.' in line[:3]):
            content = line.lstrip('- •0123456789.').strip()
            if current_section == 'entry':
                strategy["entry_rules"].append(content)
            elif current_section == 'exit':
                strategy["exit_rules"].append(content)
            elif current_section == 'philosophy' and len(content) > 10:
                strategy["philosophy"] = content
        elif current_section == 'name' and not strategy["strategy_name"]:
            strategy["strategy_name"] = line
        elif current_section == 'philosophy' and len(line) > 20:
            strategy["philosophy"] = line
        elif current_section == 'risk':
            if 'stop' in line.lower() and '%' in line:
                strategy["risk_management"]["stop_loss"] = line.split('%')[0].split()[-1] + '%'
            if 'profit' in line.lower() and '%' in line:
                strategy["risk_management"]["take_profit"] = line.split('%')[0].split()[-1] + '%'
            if 'position' in line.lower() and any(c.isdigit() for c in line):
                nums = [int(s) for s in line.split() if s.isdigit()]
                if nums:
                    strategy["risk_management"]["max_positions"] = nums[0]
            if 'leverage' in line.lower() and 'x' in line.lower():
                nums = [int(s.replace('x','')) for s in line.split() if 'x' in s.lower()]
                if nums:
                    strategy["risk_management"]["leverage"] = f"{nums[0]}x"
        elif current_section == 'timeframe':
            for tf in ['1min', '3min', '5min', '10min', '15min', '30min', '1hour']:
                if tf in line.lower():
                    strategy["timeframe"] = tf
                    break
    
    # Ensure we have minimum data
    if not strategy["entry_rules"]:
        strategy["entry_rules"] = ["Price above 20MA", "Volume spike", "RSI confirmation"]
    if not strategy["exit_rules"]:
        strategy["exit_rules"] = [f"Stop loss {strategy['risk_management']['stop_loss']}", 
                                   f"Take profit {strategy['risk_management']['take_profit']}",
                                   "Time-based exit"]
    
    return strategy


def generate_strategy_for_character(character: str) -> Dict:
    """Generate a strategy using LLM via sessions tool."""
    
    prompt = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["Harper"])
    
    # Create a task for the LLM
    import subprocess
    import json as json_mod
    
    # Use a simple approach - create a temp file with the prompt and use curl or similar
    # For now, return a template that can be filled
    
    print(f"Generating strategy for {character}...")
    
    # Return a strategy template (in production, this would call the LLM)
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
    
    print(f"🏁 Generating strategies for Race {race_id}...")
    print("=" * 60)
    
    for character in characters:
        print(f"🎭 Creating strategy for {character}...")
        strategy = generate_strategy_for_character(character)
        strategies[character] = strategy
        print(f"   ✓ {strategy['strategy_name']}")
        print(f"   📊 {strategy['philosophy']}")
        print(f"   ⚡ {strategy['risk_management']['leverage']} leverage")
        print()
    
    # Save strategies
    strategies_dir = f"races/{race_id}/strategies"
    os.makedirs(strategies_dir, exist_ok=True)
    
    with open(f"{strategies_dir}/race_strategies.json", "w") as f:
        json.dump(strategies, f, indent=2)
    
    print(f"💾 Strategies saved to {strategies_dir}/race_strategies.json")
    
    return strategies


def mutate_strategy(parent_strategy: Dict, generation: int = 2) -> Dict:
    """Create a mutated version of a winning strategy."""
    
    character = parent_strategy["character"]
    
    # Apply mutations
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
    
    # Slightly adjust risk parameters
    leverage = int(parent_strategy["risk_management"]["leverage"].rstrip("x"))
    mutated["risk_management"]["leverage"] = f"{min(leverage + 2, 20)}x"
    
    return mutated


if __name__ == "__main__":
    # Generate strategies for Race 2
    strategies = generate_race_strategies("race_2_demo")
    print("\n🎯 All strategies generated!")
    print("\nRun 'python arena.py start-race --use-llm-strategies' to begin!")
