"""
Desk Management System - VPs, Directors, and MDs can build their own trading desks
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from agent_factory import AgentFactory, TradingAgent
from config import STARTING_CAPITAL


# Desk configuration for each rank
DESK_CONFIG = {
    "VP - Trading": {
        "max_juniors": 2,
        "junior_strategy_variance": 0.1,  # 10% variance from parent
        "starting_capital_bonus": 500,
        "capital_per_junior": 500,  # Each junior gets this much
        "desk_name_prefixes": ["VP", "Head of", "Lead"],
    },
    "Director": {
        "max_juniors": 3,
        "junior_strategy_variance": 0.15,
        "starting_capital_bonus": 1000,
        "capital_per_junior": 750,
        "desk_name_prefixes": ["Director", "Senior VP", "Head of"],
    },
    "MD": {
        "max_juniors": 5,
        "junior_strategy_variance": 0.2,
        "starting_capital_bonus": 2000,
        "capital_per_junior": 1000,
        "desk_name_prefixes": ["MD", "Managing Director", "Partner"],
    },
    "Partner": {
        "max_juniors": 7,
        "junior_strategy_variance": 0.25,
        "starting_capital_bonus": 5000,
        "capital_per_junior": 2000,
        "desk_name_prefixes": ["Partner", "Senior Partner", "Principal"],
    }
}


class JuniorTrader:
    """A junior trader employed by a senior trader's desk."""
    
    def __init__(self, 
                 name: str,
                 parent_name: str,
                 character: str,
                 strategy_params: Dict,
                 starting_capital: float = 500):
        self.name = name
        self.parent_name = parent_name
        self.character = character
        self.strategy_params = strategy_params
        self.starting_capital = starting_capital
        self.current_capital = starting_capital
        self.trades = []
        self.mentorship_benefit = 0.0  # Improves over time
        
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "parent_name": self.parent_name,
            "character": self.character,
            "starting_capital": self.starting_capital,
            "current_capital": self.current_capital,
            "trades": len(self.trades),
            "mentorship_benefit": self.mentorship_benefit,
        }


class TradingDesk:
    """A trading desk led by a senior trader with junior employees."""
    
    def __init__(self, 
                 leader_name: str,
                 leader_character: str,
                 leader_title: str,
                 desk_id: str = None):
        self.desk_id = desk_id or f"desk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.leader_name = leader_name
        self.leader_character = leader_character
        self.leader_title = leader_title
        self.juniors: List[JuniorTrader] = []
        self.created_at = datetime.utcnow().isoformat()
        self.desk_name = self._generate_desk_name()
        self.total_desk_pnl = 0.0
        self.desk_rank = 0  # Among all desks
        
    def _generate_desk_name(self) -> str:
        """Generate a prestigious desk name."""
        config = DESK_CONFIG.get(self.leader_title, DESK_CONFIG["VP - Trading"])
        prefix = random.choice(config["desk_name_prefixes"])
        
        desk_names = {
            "Harper": [f"{prefix} Harper Global Macro", f"{prefix} Harper Alpha Strategies"],
            "Rishi": [f"{prefix} Rishi High-Frequency", f"{prefix} Rishi Quant Trading"],
            "Yasmin": [f"{prefix} Yasmin Institutional", f"{prefix} Yasmin Smart Money"],
            "Gus": [f"{prefix} Gus Statistical Arbitrage", f"{prefix} Gus Quant Research"],
            "Robert": [f"{prefix} Robert Momentum", f"{prefix} Robert YOLO Capital"],
            "Eric": [f"{prefix} Eric Breakout Strategies", f"{prefix} Eric Technical Analysis"],
            "Danny": [f"{prefix} Danny YOLO Ventures", f"{prefix} Danny High Risk"],
        }
        
        return random.choice(desk_names.get(self.leader_character, [f"{prefix} Trading Desk"]))
    
    def can_hire(self) -> bool:
        """Check if desk can hire more juniors."""
        config = DESK_CONFIG.get(self.leader_title, DESK_CONFIG["VP - Trading"])
        return len(self.juniors) < config["max_juniors"]
    
    def hire_junior(self, parent_strategy: Dict, factory: AgentFactory) -> Optional[JuniorTrader]:
        """Hire a new junior trader."""
        if not self.can_hire():
            return None
        
        config = DESK_CONFIG.get(self.leader_title, DESK_CONFIG["VP - Trading"])
        
        # Generate junior name
        junior_num = len(self.juniors) + 1
        junior_name = f"{self.leader_character}_Jr{junior_num}_{random.randint(1000,9999)}"
        
        # Create strategy with variance from parent
        junior_strategy = self._create_junior_strategy(parent_strategy, config["junior_strategy_variance"])
        
        # Create junior trader
        junior = JuniorTrader(
            name=junior_name,
            parent_name=self.leader_name,
            character=f"{self.leader_character}_Jr{junior_num}",
            strategy_params=junior_strategy,
            starting_capital=config["capital_per_junior"]
        )
        
        self.juniors.append(junior)
        
        print(f"\n📋 {self.desk_name}")
        print(f"   ➕ HIRED: {junior_name}")
        print(f"   💰 Capital: ${config['capital_per_junior']}")
        print(f"   🎯 Strategy: {junior_strategy.get('name', 'Inherited from leader')}")
        
        return junior
    
    def _create_junior_strategy(self, parent_strategy: Dict, variance: float) -> Dict:
        """Create a junior strategy based on parent's with some variance."""
        junior = parent_strategy.copy()
        
        # Apply variance to numerical parameters
        if "max_leverage" in junior:
            base_lev = junior["max_leverage"]
            junior["max_leverage"] = int(base_lev * (1 + random.uniform(-variance, variance)))
            junior["max_leverage"] = max(1, min(20, junior["max_leverage"]))  # Clamp 1-20x
        
        if "stop_loss_pct" in junior:
            base_sl = junior["stop_loss_pct"]
            junior["stop_loss_pct"] = base_sl * (1 + random.uniform(-variance, variance))
        
        if "take_profit_pct" in junior:
            base_tp = junior["take_profit_pct"]
            junior["take_profit_pct"] = base_tp * (1 + random.uniform(-variance, variance))
        
        if "entry_threshold" in junior:
            base_et = junior["entry_threshold"]
            junior["entry_threshold"] = base_et * (1 + random.uniform(-variance, variance))
        
        # Junior gets mentored - slight improvement over time
        junior["mentorship_factor"] = 1.0  # Starts at 1.0, improves with wins
        
        return junior
    
    def get_desk_performance(self) -> Dict:
        """Get combined desk performance."""
        total_capital = sum(j.current_capital for j in self.juniors)
        total_trades = sum(len(j.trades) for j in self.juniors)
        
        return {
            "desk_name": self.desk_name,
            "leader": self.leader_name,
            "title": self.leader_title,
            "juniors_count": len(self.juniors),
            "total_desk_capital": total_capital,
            "total_desk_pnl": self.total_desk_pnl,
            "total_trades": total_trades,
            "desk_rank": self.desk_rank,
        }
    
    def to_dict(self) -> Dict:
        return {
            "desk_id": self.desk_id,
            "desk_name": self.desk_name,
            "leader_name": self.leader_name,
            "leader_character": self.leader_character,
            "leader_title": self.leader_title,
            "created_at": self.created_at,
            "juniors": [j.to_dict() for j in self.juniors],
            "total_desk_pnl": self.total_desk_pnl,
        }


class DeskManager:
    """Manages all trading desks in the arena."""
    
    DESKS_FILE = "careers/desks.json"
    
    def __init__(self):
        self.desks: Dict[str, TradingDesk] = {}
        self._load_desks()
    
    def _load_desks(self):
        """Load existing desks."""
        if os.path.exists(self.DESKS_FILE):
            with open(self.DESKS_FILE, 'r') as f:
                data = json.load(f)
                for desk_id, desk_data in data.items():
                    # Recreate desk from data
                    desk = TradingDesk(
                        leader_name=desk_data["leader_name"],
                        leader_character=desk_data["leader_character"],
                        leader_title=desk_data["leader_title"],
                        desk_id=desk_id
                    )
                    desk.desk_name = desk_data["desk_name"]
                    desk.created_at = desk_data["created_at"]
                    desk.total_desk_pnl = desk_data.get("total_desk_pnl", 0)
                    self.desks[desk_id] = desk
    
    def _save_desks(self):
        """Save all desks."""
        os.makedirs(os.path.dirname(self.DESKS_FILE), exist_ok=True)
        data = {desk_id: desk.to_dict() for desk_id, desk in self.desks.items()}
        with open(self.DESKS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def create_desk(self, leader_name: str, leader_character: str, 
                   leader_title: str) -> Optional[TradingDesk]:
        """Create a new trading desk when promoted to VP+."""
        if leader_title not in DESK_CONFIG:
            return None
        
        desk = TradingDesk(leader_name, leader_character, leader_title)
        self.desks[desk.desk_id] = desk
        self._save_desks()
        
        print(f"\n🏢 NEW TRADING DESK ESTABLISHED!")
        print(f"   📋 {desk.desk_name}")
        print(f"   👔 Led by: {leader_character} ({leader_title})")
        print(f"   💼 Can hire up to {DESK_CONFIG[leader_title]['max_juniors']} junior traders")
        
        return desk
    
    def get_or_create_desk(self, leader_name: str, leader_character: str,
                          leader_title: str) -> Optional[TradingDesk]:
        """Get existing desk or create new one."""
        # Check if desk exists
        for desk in self.desks.values():
            if desk.leader_name == leader_name:
                return desk
        
        # Create new if VP+
        if leader_title in DESK_CONFIG:
            return self.create_desk(leader_name, leader_character, leader_title)
        
        return None
    
    def hire_for_desk(self, leader_name: str, parent_strategy: Dict, 
                     factory: AgentFactory) -> Optional[JuniorTrader]:
        """Hire a junior for a leader's desk."""
        for desk in self.desks.values():
            if desk.leader_name == leader_name:
                junior = desk.hire_junior(parent_strategy, factory)
                if junior:
                    self._save_desks()
                return junior
        return None
    
    def get_desk_rankings(self) -> List[Dict]:
        """Get ranked list of all desks by performance."""
        rankings = []
        for desk in self.desks.values():
            perf = desk.get_desk_performance()
            rankings.append(perf)
        
        rankings.sort(key=lambda x: x["total_desk_pnl"], reverse=True)
        
        # Update ranks
        for i, rank in enumerate(rankings, 1):
            rank["desk_rank"] = i
            # Update desk object
            for desk in self.desks.values():
                if desk.desk_name == rank["desk_name"]:
                    desk.desk_rank = i
        
        return rankings
    
    def get_leaderboard(self) -> str:
        """Get formatted desk leaderboard."""
        rankings = self.get_desk_rankings()
        
        if not rankings:
            return "No active trading desks yet."
        
        lines = ["\n" + "="*60, "🏢 TRADING DESK LEADERBOARD", "="*60]
        
        for i, desk in enumerate(rankings[:5], 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            lines.append(f"\n{emoji} {desk['desk_name']}")
            lines.append(f"   Leader: {desk['leader']} ({desk['title']})")
            lines.append(f"   Juniors: {desk['juniors_count']} | P&L: ${desk['total_desk_pnl']:+.2f}")
        
        lines.append("="*60)
        return "\n".join(lines)


# Singleton instance
desk_manager = DeskManager()


def check_and_create_desk(agent_name: str, character: str, new_title: str) -> Optional[TradingDesk]:
    """Check if promoted bot should get a desk."""
    if new_title in DESK_CONFIG:
        return desk_manager.get_or_create_desk(agent_name, character, new_title)
    return None


def hire_junior_for_bot(agent_name: str, parent_strategy: Dict, factory: AgentFactory) -> Optional[JuniorTrader]:
    """Hire a junior for a bot that has a desk."""
    return desk_manager.hire_for_desk(agent_name, parent_strategy, factory)


def get_desk_leaderboard() -> str:
    """Get the desk leaderboard."""
    return desk_manager.get_leaderboard()


def get_desk_for_bot(agent_name: str) -> Optional[TradingDesk]:
    """Get desk for a specific bot."""
    for desk in desk_manager.desks.values():
        if desk.leader_name == agent_name:
            return desk
    return None
