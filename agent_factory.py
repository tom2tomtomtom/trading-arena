"""
Agent Factory - Creates autonomous trading bots with unique personas and strategies.
Each bot invents its own trading approach through AI generation.
"""

import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from config import BOT_COLORS, RISK_TIERS, STARTING_CAPITAL

# Strategy archetypes - AI will build on these foundations
# Industry HBO names: Harper, Rishi, Yasmin, Gus, Robert
STRATEGY_ARCHETYPES = [
    {
        "name": "YOLO",
        "industry_name": "Danny",
        "description": "High conviction, max leverage, one big bet mentality",
        "traits": ["aggressive", "concentrated", "momentum-chasing"],
        "preferred_assets": ["BTC-USD", "ETH-USD", "SOL-USD"],
    },
    {
        "name": "Scalper",
        "industry_name": "Rishi",
        "description": "Rapid-fire trades, small gains, high frequency",
        "traits": ["fast", "fee-conscious", "tight-stops"],
        "preferred_assets": ["BTC-USD", "ETH-USD"],
    },
    {
        "name": "Breakout Hunter",
        "industry_name": "Eric",
        "description": "Catches explosive moves, waits for confirmation",
        "traits": ["patient", "momentum", "wider-stops"],
        "preferred_assets": ["SOL-USD", "AVAX-USD", "DOGE-USD"],
    },
    {
        "name": "Mean Reverter",
        "industry_name": "Gus",
        "description": "Fades extremes, bets on return to normal",
        "traits": ["contrarian", "oversold-buyer", "overbought-seller"],
        "preferred_assets": ["ETH-USD", "BTC-USD", "SPY"],
    },
    {
        "name": "Trend Follower",
        "industry_name": "Harper",
        "description": "Only trades with the trend, never fights momentum",
        "traits": ["patient", "trend-aligned", "pyramiding"],
        "preferred_assets": ["BTC-USD", "QQQ", "NVDA"],
    },
    {
        "name": "Whale Watcher",
        "industry_name": "Yasmin",
        "description": "Follows big money, copies successful wallets",
        "traits": ["reactive", "copy-trading", "delayed-entry"],
        "preferred_assets": ["BTC-USD", "ETH-USD", "SOL-USD"],
    },
    {
        "name": "Sentiment Trader",
        "industry_name": "Venetia",
        "description": "Trades news and social sentiment spikes",
        "traits": ["news-reactive", "fast-entry", "fast-exit"],
        "preferred_assets": ["DOGE-USD", "SHIB-USD", "TSLA"],
    },
    {
        "name": "Pairs Trader",
        "industry_name": "Clement",
        "description": "Long one asset, short another, captures spread",
        "traits": ["market-neutral", "correlation-based", "hedged"],
        "preferred_assets": ["BTC-USD/ETH-USD", "SPY/QQQ"],
    },
    {
        "name": "Contrarian",
        "industry_name": "Bill",
        "description": "Bets against the crowd, buys fear sells greed",
        "traits": ["fear-buyer", "greed-seller", "patient"],
        "preferred_assets": ["BTC-USD", "ETH-USD", "SPY"],
    },
    {
        "name": "Momentum Surfer",
        "industry_name": "Robert",
        "description": "Rides waves, quick to cut losers, lets winners run",
        "traits": ["momentum", "trailing-stops", "asymmetric-risk"],
        "preferred_assets": ["SOL-USD", "NVDA", "AMD"],
    },
]


class TradingAgent:
    """An autonomous trading bot with its own persona and strategy."""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        color: str,
        archetype: Dict,
        risk_tier: str,
        starting_capital: float = STARTING_CAPITAL,
    ):
        self.agent_id = agent_id
        self.name = name
        self.color = color
        self.archetype = archetype
        self.risk_tier = risk_tier
        self.risk_params = RISK_TIERS[risk_tier]
        
        # Paper wallet
        self.starting_capital = starting_capital
        self.cash = starting_capital
        self.positions: Dict = {}  # symbol -> {qty, entry_price, direction}
        
        # Performance tracking
        self.trades: List[Dict] = []
        self.pnl_history: List[Dict] = []  # timestamp, portfolio_value
        self.created_at = datetime.utcnow()
        
        # Strategy parameters (AI-generated, can mutate)
        self.strategy_params = self._generate_strategy_params()
    
    def _generate_strategy_params(self) -> Dict:
        """Generate unique strategy parameters based on archetype."""
        base_params = {
            "entry_threshold": round(random.uniform(0.1, 0.4), 2),
            "stop_loss_pct": round(random.uniform(0.02, 0.08), 3),
            "take_profit_pct": round(random.uniform(0.04, 0.15), 3),
            "max_positions": random.randint(1, 5),
            "position_size_pct": round(random.uniform(0.1, self.risk_params["max_position_pct"]), 2),
            "max_leverage": self.risk_params["max_leverage"],
            "min_hold_minutes": random.randint(5, 60),
            "preferred_assets": self.archetype.get("preferred_assets", []),
        }
        
        # Archetype-specific adjustments
        if self.archetype["name"] == "YOLO":
            base_params["max_positions"] = 1
            base_params["position_size_pct"] = 1.0
            base_params["max_leverage"] = self.risk_params["max_leverage"]
        elif self.archetype["name"] == "Scalper":
            base_params["min_hold_minutes"] = 2
            base_params["stop_loss_pct"] = 0.01
            base_params["take_profit_pct"] = 0.02
            base_params["max_positions"] = 3
        elif self.archetype["name"] == "Breakout Hunter":
            base_params["stop_loss_pct"] = 0.05
            base_params["take_profit_pct"] = 0.12
        elif self.archetype["name"] == "Mean Reverter":
            base_params["entry_threshold"] = 0.3  # Wait for extremes
        
        return base_params
    
    @property
    def portfolio_value(self) -> float:
        """Calculate current portfolio value (cash + margin locked + unrealized P&L)."""
        # Cash + margin locked in positions + unrealized P&L
        margin_locked = sum(pos.get("margin", 0) for pos in self.positions.values())
        unrealized_pnl = sum(pos.get("unrealized_pnl", 0) for pos in self.positions.values())
        return self.cash + margin_locked + unrealized_pnl
    
    @property
    def total_pnl(self) -> float:
        """Total P&L from starting capital."""
        return self.portfolio_value - self.starting_capital
    
    @property
    def total_pnl_pct(self) -> float:
        """Total P&L as percentage."""
        return (self.total_pnl / self.starting_capital) * 100
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate from completed trades."""
        if not self.trades:
            return 0.0
        winners = sum(1 for t in self.trades if t.get("pnl", 0) > 0)
        return (winners / len(self.trades)) * 100
    
    def to_dict(self) -> Dict:
        """Serialize agent to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "color": self.color,
            "archetype": self.archetype["name"],
            "risk_tier": self.risk_tier,
            "starting_capital": self.starting_capital,
            "cash": self.cash,
            "positions": self.positions,
            "trades": self.trades,
            "pnl_history": self.pnl_history,
            "strategy_params": self.strategy_params,
            "created_at": self.created_at.isoformat(),
            "portfolio_value": self.portfolio_value,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "win_rate": self.win_rate,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "TradingAgent":
        """Deserialize agent from dictionary."""
        archetype = next(
            (a for a in STRATEGY_ARCHETYPES if a["name"] == data["archetype"]),
            STRATEGY_ARCHETYPES[0]
        )
        agent = cls(
            agent_id=data["agent_id"],
            name=data["name"],
            color=data["color"],
            archetype=archetype,
            risk_tier=data["risk_tier"],
            starting_capital=data["starting_capital"],
        )
        agent.cash = data.get("cash", agent.starting_capital)
        agent.positions = data.get("positions", {})
        agent.trades = data.get("trades", [])
        agent.pnl_history = data.get("pnl_history", [])
        agent.strategy_params = data.get("strategy_params", agent.strategy_params)
        return agent


class AgentFactory:
    """Factory for creating and managing trading agents."""
    
    def __init__(self, agents_dir: str = "agents"):
        self.agents_dir = Path(agents_dir)
        self.agents_dir.mkdir(parents=True, exist_ok=True)
    
    def create_agent(
        self,
        archetype_name: Optional[str] = None,
        risk_tier: str = "moderate",
        starting_capital: float = STARTING_CAPITAL,
    ) -> TradingAgent:
        """Create a new trading agent with a unique persona."""
        
        # Pick archetype (random if not specified)
        if archetype_name:
            archetype = next(
                (a for a in STRATEGY_ARCHETYPES if a["name"] == archetype_name),
                random.choice(STRATEGY_ARCHETYPES)
            )
        else:
            archetype = random.choice(STRATEGY_ARCHETYPES)
        
        # Generate unique ID and name (use Industry name if available)
        agent_id = str(uuid.uuid4())[:8]
        display_name = archetype.get("industry_name", archetype["name"])
        name = f"{display_name}_{agent_id}"
        
        # Assign color
        used_colors = self._get_used_colors()
        available_colors = [c for c in BOT_COLORS if c not in used_colors]
        color = available_colors[0] if available_colors else random.choice(BOT_COLORS)
        
        agent = TradingAgent(
            agent_id=agent_id,
            name=name,
            color=color,
            archetype=archetype,
            risk_tier=risk_tier,
            starting_capital=starting_capital,
        )
        
        # Save agent
        self.save_agent(agent)
        
        return agent
    
    def create_race_cohort(
        self,
        num_bots: int = 5,
        risk_tier: str = "moderate",
        starting_capital: float = STARTING_CAPITAL,
    ) -> List[TradingAgent]:
        """Create a cohort of agents for a race."""
        agents = []
        used_archetypes = []
        
        for i in range(num_bots):
            # Try to pick unique archetypes
            available = [a for a in STRATEGY_ARCHETYPES if a["name"] not in used_archetypes]
            if not available:
                available = STRATEGY_ARCHETYPES
            
            archetype = random.choice(available)
            used_archetypes.append(archetype["name"])
            
            agent = self.create_agent(
                archetype_name=archetype["name"],
                risk_tier=risk_tier,
                starting_capital=starting_capital,
            )
            agents.append(agent)
        
        return agents
    
    def save_agent(self, agent: TradingAgent) -> None:
        """Save agent to disk."""
        filepath = self.agents_dir / f"{agent.agent_id}.json"
        with open(filepath, "w") as f:
            json.dump(agent.to_dict(), f, indent=2, default=str)
    
    def load_agent(self, agent_id: str) -> Optional[TradingAgent]:
        """Load agent from disk."""
        filepath = self.agents_dir / f"{agent_id}.json"
        if not filepath.exists():
            return None
        with open(filepath) as f:
            data = json.load(f)
        return TradingAgent.from_dict(data)
    
    def list_agents(self) -> List[TradingAgent]:
        """List all saved agents."""
        agents = []
        for filepath in self.agents_dir.glob("*.json"):
            with open(filepath) as f:
                data = json.load(f)
            agents.append(TradingAgent.from_dict(data))
        return agents
    
    def _get_used_colors(self) -> List[str]:
        """Get colors already assigned to active agents."""
        return [a.color for a in self.list_agents()]
    
    def clone_with_mutation(
        self,
        agent: TradingAgent,
        mutation_rate: float = 0.2
    ) -> TradingAgent:
        """Clone a winning agent with slight parameter mutations."""
        new_agent = self.create_agent(
            archetype_name=agent.archetype["name"],
            risk_tier=agent.risk_tier,
            starting_capital=agent.starting_capital,
        )
        
        # Copy and mutate strategy params
        for key, value in agent.strategy_params.items():
            if isinstance(value, (int, float)) and random.random() < mutation_rate:
                # Mutate by ±20%
                mutation = value * random.uniform(-0.2, 0.2)
                if isinstance(value, int):
                    new_agent.strategy_params[key] = max(1, int(value + mutation))
                else:
                    new_agent.strategy_params[key] = round(value + mutation, 3)
            else:
                new_agent.strategy_params[key] = value
        
        self.save_agent(new_agent)
        return new_agent


if __name__ == "__main__":
    # Test: Create a race cohort
    factory = AgentFactory()
    cohort = factory.create_race_cohort(num_bots=5, risk_tier="high")
    
    print("🏁 Race 1 Cohort Created:")
    print("-" * 50)
    for agent in cohort:
        print(f"{agent.color} {agent.name}")
        print(f"   Strategy: {agent.archetype['name']}")
        print(f"   Risk Tier: {agent.risk_tier}")
        print(f"   Capital: ${agent.starting_capital}")
        print(f"   Max Leverage: {agent.strategy_params['max_leverage']}x")
        print(f"   Stop Loss: {agent.strategy_params['stop_loss_pct']*100:.1f}%")
        print()
