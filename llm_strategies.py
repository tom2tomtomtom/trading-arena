"""
LLM Strategy Generator - Spawns sub-agents to create unique trading strategies.
Hybrid approach: LLM generates strategy once, Python executes fast.
"""

import json
import os
from datetime import datetime
from typing import Dict, List
from sessions_spawn import sessions_spawn

# Industry character prompts
CHARACTER_PROMPTS = {
    "Harper": """You are Harper - an ambitious, intuitive trader who follows trends aggressively.
    Create a trading strategy for crypto/stocks with:
    - Trend-following approach
    - Specific entry/exit rules
    - Risk management parameters
    - Preferred assets and why
    
    Return JSON format:
    {
        "strategy_name": "name",
        "philosophy": "one sentence",
        "entry_rules": ["rule1", "rule2"],
        "exit_rules": ["rule1", "rule2"],
        "risk_management": {"stop_loss": "X%", "take_profit": "Y%", "max_positions": N},
        "preferred_assets": ["BTC-USD", "QQQ"],
        "leverage": "10x",
        "timeframe": "5min"
    }""",
    
    "Rishi": """You are Rishi - a ruthless, fast scalper who exploits inefficiencies.
    Create a high-frequency scalping strategy:
    - Quick entries/exits
    - Tight risk controls
    - Specific technical indicators
    
    Return JSON format:
    {
        "strategy_name": "name",
        "philosophy": "one sentence",
        "entry_rules": ["rule1", "rule2"],
        "exit_rules": ["rule1", "rule2"],
        "risk_management": {"stop_loss": "X%", "take_profit": "Y%", "max_positions": N},
        "preferred_assets": ["BTC-USD", "ETH-USD"],
        "leverage": "15x",
        "timeframe": "1min"
    }""",
    
    "Yasmin": """You are Yasmin - a patient, privileged trader who waits for perfect setups.
    Create a whale-watching strategy:
    - Follow smart money
    - Delayed entries after confirmation
    - Copy successful patterns
    
    Return JSON format:
    {
        "strategy_name": "name",
        "philosophy": "one sentence",
        "entry_rules": ["rule1", "rule2"],
        "exit_rules": ["rule1", "rule2"],
        "risk_management": {"stop_loss": "X%", "take_profit": "Y%", "max_positions": N},
        "preferred_assets": ["BTC-USD", "ETH-USD", "SOL-USD"],
        "leverage": "5x",
        "timeframe": "15min"
    }""",
    
    "Gus": """You are Gus - an intellectual contrarian who fades extremes.
    Create a mean reversion strategy:
    - Buy fear, sell greed
    - Statistical arbitrage approach
    - Patience for extremes
    
    Return JSON format:
    {
        "strategy_name": "name",
        "philosophy": "one sentence",
        "entry_rules": ["rule1", "rule2"],
        "exit_rules": ["rule1", "rule2"],
        "risk_management": {"stop_loss": "X%", "take_profit": "Y%", "max_positions": N},
        "preferred_assets": ["ETH-USD", "BTC-USD", "SPY"],
        "leverage": "8x",
        "timeframe": "10min"
    }""",
    
    "Robert": """You are Robert - a charismatic YOLO trader who chases momentum.
    Create a momentum surfing strategy:
    - Ride waves aggressively
    - Quick to cut losers
    - FOMO-driven entries
    
    Return JSON format:
    {
        "strategy_name": "name",
        "philosophy": "one sentence",
        "entry_rules": ["rule1", "rule2"],
        "exit_rules": ["rule1", "rule2"],
        "risk_management": {"stop_loss": "X%", "take_profit": "Y%", "max_positions": N},
        "preferred_assets": ["SOL-USD", "NVDA", "AMD"],
        "leverage": "20x",
        "timeframe": "3min"
    }"""
}


def spawn_strategy_agent(character: str, race_id: str) -> Dict:
    """Spawn a sub-agent to generate a unique strategy."""
    
    prompt = CHARACTER_PROMPTS.get(character, CHARACTER_PROMPTS["Harper"])
    
    task = f"""{prompt}

Current market context (Feb 2026):
- BTC around $95k, ETH around $2.7k
- NVDA strong on AI demand
- QQQ near highs
- SOL showing volatility

Generate your strategy now. Be specific and actionable.
Return ONLY valid JSON, no markdown."""

    # Spawn sub-agent with Sonnet for better reasoning
    result = sessions_spawn(
        task=task,
        model="sonnet",
        cleanup="delete",
        timeout_seconds=60
    )
    
    # Parse strategy from result
    try:
        # Extract JSON from response
        content = result.get("response", "{}")
        # Find JSON block
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            strategy = json.loads(content[start:end])
        else:
            strategy = json.loads(content)
        
        strategy["character"] = character
        strategy["race_id"] = race_id
        strategy["created_at"] = datetime.utcnow().isoformat()
        
        return strategy
        
    except Exception as e:
        print(f"Error parsing strategy for {character}: {e}")
        # Fallback strategy
        return {
            "character": character,
            "strategy_name": f"{character}_Fallback",
            "philosophy": "Follow the trend",
            "entry_rules": ["Price above 20MA", "RSI > 50"],
            "exit_rules": ["Stop loss -5%", "Take profit +10%"],
            "risk_management": {"stop_loss": "5%", "take_profit": "10%", "max_positions": 3},
            "preferred_assets": ["BTC-USD", "QQQ"],
            "leverage": "10x",
            "timeframe": "5min",
            "race_id": race_id,
            "created_at": datetime.utcnow().isoformat()
        }


def generate_race_strategies(race_id: str, characters: List[str] = None) -> Dict[str, Dict]:
    """Generate strategies for all characters in a race."""
    
    if characters is None:
        characters = ["Harper", "Rishi", "Yasmin", "Gus", "Robert"]
    
    strategies = {}
    
    print(f"🏁 Generating strategies for Race {race_id}...")
    print("=" * 50)
    
    for character in characters:
        print(f"🎭 Spawning {character}...")
        strategy = spawn_strategy_agent(character, race_id)
        strategies[character] = strategy
        print(f"   Strategy: {strategy.get('strategy_name', 'Unknown')}")
        print(f"   Philosophy: {strategy.get('philosophy', 'N/A')}")
        print()
    
    # Save strategies
    strategies_dir = f"races/{race_id}/strategies"
    os.makedirs(strategies_dir, exist_ok=True)
    
    with open(f"{strategies_dir}/race_strategies.json", "w") as f:
        json.dump(strategies, f, indent=2)
    
    return strategies


def mutate_strategy(parent_strategy: Dict, race_id: str) -> Dict:
    """Mutate a winning strategy for the next race."""
    
    character = parent_strategy["character"]
    
    task = f"""You are {character}. Your previous strategy performed well:

{json.dumps(parent_strategy, indent=2)}

Mutate this strategy for the next race. Keep what worked, tweak what didn't.
Adjust parameters slightly. Try one new idea.

Return updated JSON with same structure."""

    result = sessions_spawn(
        task=task,
        model="sonnet",
        cleanup="delete",
        timeout_seconds=60
    )
    
    try:
        content = result.get("response", "{}")
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            mutated = json.loads(content[start:end])
        else:
            mutated = json.loads(content)
        
        mutated["character"] = character
        mutated["parent_strategy"] = parent_strategy.get("strategy_name")
        mutated["race_id"] = race_id
        mutated["created_at"] = datetime.utcnow().isoformat()
        mutated["mutation"] = True
        
        return mutated
        
    except Exception as e:
        print(f"Error mutating strategy: {e}")
        # Return parent with slight mutation
        mutated = parent_strategy.copy()
        mutated["race_id"] = race_id
        mutated["mutation"] = True
        return mutated


if __name__ == "__main__":
    # Test: Generate strategies for Race 2
    strategies = generate_race_strategies("race_2_test")
    print("\n🎯 All strategies generated!")
    for char, strat in strategies.items():
        print(f"\n{char}: {strat['strategy_name']}")
        print(f"  Philosophy: {strat['philosophy']}")
        print(f"  Leverage: {strat['leverage']}")
        print(f"  Assets: {', '.join(strat['preferred_assets'])}")
