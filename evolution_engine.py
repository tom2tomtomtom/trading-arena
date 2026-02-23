"""
Evolution Engine - Mutates winning strategies for continuous improvement.

This module implements genetic algorithm concepts:
- Selection: Top performers survive
- Mutation: Surviving strategies get tweaked parameters
- Crossover: Future - combine two winning strategies
"""

import json
import random
import copy
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path


class StrategyMutator:
    """Creates mutated variants of successful trading strategies."""
    
    # Mutation intensity levels
    MUTATION_LEVELS = {
        "conservative": 0.1,  # 10% parameter change
        "moderate": 0.2,      # 20% parameter change  
        "aggressive": 0.35,   # 35% parameter change
        "extreme": 0.5,       # 50% parameter change (YOLO mode)
    }
    
    # Parameters that can be mutated
    MUTABLE_PARAMS = {
        "entry_threshold": (0.05, 0.5, "multiply"),  # min, max, mode
        "stop_loss_pct": (0.005, 0.15, "multiply"),
        "take_profit_pct": (0.02, 0.25, "multiply"),
        "max_positions": (1, 5, "int"),
        "position_size_pct": (0.1, 1.0, "multiply"),
        "max_leverage": (2, 20, "multiply"),
        "min_hold_minutes": (2, 120, "int"),
    }
    
    # Asset rotation options for mutation
    ASSET_POOLS = {
        "crypto_major": ["BTC-USD", "ETH-USD"],
        "crypto_alt": ["SOL-USD", "AVAX-USD", "LINK-USD", "OP-USD"],
        "crypto_meme": ["DOGE-USD", "SHIB-USD"],
        "equity_tech": ["NVDA", "AMD", "TSLA", "AAPL"],
        "equity_etfs": ["SPY", "QQQ"],
        "forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    }
    
    def __init__(self, mutation_level: str = "moderate"):
        self.mutation_rate = self.MUTATION_LEVELS.get(mutation_level, 0.2)
    
    def mutate_agent(self, parent_agent: Dict, mutation_type: str = "random") -> Dict:
        """
        Create a mutated clone of a successful agent.
        
        Args:
            parent_agent: The surviving agent's data
            mutation_type: Type of mutation to apply
                - "conservative": Small tweaks to working strategy
                - "risk_adjust": Only change risk parameters
                - "asset_shift": Change preferred assets
                - "time_horizon": Change hold times
                - "leverage": Max out or minimize leverage
                - "random": Mix of all above
        
        Returns:
            New agent dict with mutated parameters
        """
        # Deep copy to avoid modifying original
        child = copy.deepcopy(parent_agent)
        
        # Generate new ID and name
        old_name = child.get('name', 'Unknown')
        base_name = old_name.split('_')[0] if '_' in old_name else old_name
        
        # Mutation suffix
        mutation_suffixes = [
            "Prime", "Alpha", "Turbo", "Max", "Ultra",
            "V2", "Pro", "Elite", "Core", "Edge",
            "Aggro", "Swift", "Deep", "Hyper", "Nexus"
        ]
        suffix = random.choice(mutation_suffixes)
        new_name = f"{base_name}-{suffix}"
        
        child['name'] = new_name
        child['agent_id'] = f"{child.get('agent_id', 'unknown')[:8]}_mut_{random.randint(1000, 9999)}"
        child['parent'] = old_name
        child['mutation_type'] = mutation_type
        child['created_at'] = datetime.utcnow().isoformat()
        
        # Get strategy params
        params = child.get('strategy_params', {})
        if not params:
            params = self._create_default_params(child.get('archetype', 'Unknown'))
        
        # Apply mutations based on type
        if mutation_type == "random":
            mutation_type = random.choice([
                "conservative", "risk_adjust", "asset_shift", 
                "time_horizon", "leverage", "aggressive"
            ])
        
        if mutation_type == "conservative":
            params = self._mutate_conservative(params)
        elif mutation_type == "risk_adjust":
            params = self._mutate_risk(params)
        elif mutation_type == "asset_shift":
            params = self._mutate_assets(params)
        elif mutation_type == "time_horizon":
            params = self._mutate_time_horizon(params)
        elif mutation_type == "leverage":
            params = self._mutate_leverage(params, extreme=True)
        elif mutation_type == "aggressive":
            params = self._mutate_aggressive(params)
        
        child['strategy_params'] = params
        child['mutated_params'] = {
            "type": mutation_type,
            "rate": self.mutation_rate,
            "changes": self._get_param_changes(parent_agent.get('strategy_params', {}), params)
        }
        
        # Reset performance metrics for new race
        child['trades'] = []
        child['pnl_history'] = []
        child['cash'] = child.get('starting_capital', 1000)
        child['positions'] = {}
        
        return child
    
    def _mutate_conservative(self, params: Dict) -> Dict:
        """Small tweaks to working strategy."""
        result = params.copy()
        
        # Tweak 1-2 parameters slightly
        for _ in range(random.randint(1, 2)):
            param = random.choice(list(self.MUTABLE_PARAMS.keys()))
            if param in result:
                min_val, max_val, mode = self.MUTABLE_PARAMS[param]
                current = result[param]
                
                if mode == "multiply":
                    change = 1 + random.uniform(-0.1, 0.1)
                    new_val = current * change
                elif mode == "int":
                    change = random.randint(-1, 1)
                    new_val = current + change
                else:
                    continue
                
                result[param] = max(min_val, min(max_val, new_val))
        
        return result
    
    def _mutate_risk(self, params: Dict) -> Dict:
        """Adjust risk parameters (stops and position sizing)."""
        result = params.copy()
        
        # Tighten or widen stops
        if 'stop_loss_pct' in result:
            if random.random() < 0.5:
                # Tighter stops (more conservative)
                result['stop_loss_pct'] = result['stop_loss_pct'] * 0.7
            else:
                # Wider stops (let winners run)
                result['stop_loss_pct'] = result['stop_loss_pct'] * 1.3
        
        # Adjust take profit
        if 'take_profit_pct' in result:
            if random.random() < 0.5:
                result['take_profit_pct'] = result['take_profit_pct'] * 1.2
            else:
                result['take_profit_pct'] = result['take_profit_pct'] * 0.8
        
        return result
    
    def _mutate_assets(self, params: Dict) -> Dict:
        """Shift to different asset classes."""
        result = params.copy()
        
        # Pick new asset pool
        pool_name = random.choice(list(self.ASSET_POOLS.keys()))
        pool = self.ASSET_POOLS[pool_name]
        
        # Select 2-3 assets from pool
        num_assets = random.randint(2, min(3, len(pool)))
        result['preferred_assets'] = random.sample(pool, num_assets)
        
        return result
    
    def _mutate_time_horizon(self, params: Dict) -> Dict:
        """Change holding period."""
        result = params.copy()
        
        if 'min_hold_minutes' in result:
            if random.random() < 0.5:
                # Faster (scalping)
                result['min_hold_minutes'] = max(2, int(result['min_hold_minutes'] * 0.5))
            else:
                # Slower (swing trading)
                result['min_hold_minutes'] = min(120, int(result['min_hold_minutes'] * 2))
        
        return result
    
    def _mutate_leverage(self, params: Dict, extreme: bool = False) -> Dict:
        """Maximize or minimize leverage."""
        result = params.copy()
        
        if 'max_leverage' in result:
            if extreme:
                # Go big or go home
                result['max_leverage'] = 20
                result['position_size_pct'] = 1.0
            else:
                # Reduce leverage
                result['max_leverage'] = max(2, result['max_leverage'] * 0.5)
        
        return result
    
    def _mutate_aggressive(self, params: Dict) -> Dict:
        """Aggressive mutation - change multiple parameters."""
        result = params.copy()
        
        # Apply moderate mutations to 3-4 parameters
        for param in random.sample(list(self.MUTABLE_PARAMS.keys()), 
                                   min(4, len(self.MUTABLE_PARAMS))):
            min_val, max_val, mode = self.MUTABLE_PARAMS[param]
            current = result.get(param)
            if current is None:
                continue
            
            if mode == "multiply":
                change = 1 + random.uniform(-self.mutation_rate, self.mutation_rate)
                new_val = current * change
            elif mode == "int":
                change = int(random.randint(-5, 5) * self.mutation_rate)
                new_val = current + change
            else:
                continue
            
            result[param] = max(min_val, min(max_val, new_val))
        
        return result
    
    def _create_default_params(self, archetype: str) -> Dict:
        """Create default params for an archetype."""
        defaults = {
            "entry_threshold": 0.2,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.1,
            "max_positions": 2,
            "position_size_pct": 0.5,
            "max_leverage": 10,
            "min_hold_minutes": 15,
            "preferred_assets": ["BTC-USD", "ETH-USD"],
        }
        
        # Archetype-specific defaults
        if archetype == "YOLO":
            defaults.update({
                "max_positions": 1,
                "position_size_pct": 1.0,
                "max_leverage": 20,
            })
        elif archetype == "Scalper":
            defaults.update({
                "min_hold_minutes": 2,
                "stop_loss_pct": 0.01,
                "take_profit_pct": 0.02,
                "max_positions": 3,
            })
        
        return defaults
    
    def _get_param_changes(self, old: Dict, new: Dict) -> Dict:
        """Track what changed between parent and child."""
        changes = {}
        for key in set(old.keys()) | set(new.keys()):
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changes[key] = {"from": old_val, "to": new_val}
        return changes


class EvolutionEngine:
    """Manages the evolutionary process across races."""
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.mutator = StrategyMutator(mutation_level="moderate")
    
    def get_race_survivors(self, race_id: str, survival_threshold: float = 0.6) -> List[Dict]:
        """
        Get top performers from a race.
        
        Args:
            race_id: The race to analyze
            survival_threshold: Top X% survive (default 60%)
        
        Returns:
            List of survivor agents
        """
        race_file = self.data_dir / "races" / f"{race_id}.json"
        
        if not race_file.exists():
            print(f"Race file not found: {race_file}")
            return []
        
        with open(race_file) as f:
            race_data = json.load(f)
        
        agents = race_data.get('agents_full', [])
        if not agents:
            return []
        
        # Sort by P&L
        sorted_agents = sorted(agents, key=lambda x: x.get('total_pnl', 0), reverse=True)
        
        # Take top survivors
        num_survivors = max(1, int(len(sorted_agents) * survival_threshold))
        survivors = sorted_agents[:num_survivors]
        
        print(f"Race {race_id}: {len(survivors)} survivors from {len(agents)} bots")
        for s in survivors:
            name = s.get('name', 'Unknown').split('_')[0]
            pnl = s.get('total_pnl', 0)
            arch = s.get('archetype', 'Unknown')
            print(f"  - {name} ({arch}): ${pnl:+.2f}")
        
        return survivors
    
    def create_evolved_cohort(
        self, 
        parent_race_id: str,
        num_bots: int = 7,
        num_mutations_per_survivor: int = 2,
        include_new_bots: bool = True
    ) -> List[Dict]:
        """
        Create a new race cohort with evolved strategies.
        
        Args:
            parent_race_id: Previous race to evolve from
            num_bots: Total bots in new race
            num_mutations_per_survivor: How many variants of each survivor
            include_new_bots: Whether to include fresh random strategies
        
        Returns:
            List of agent dicts ready for the race
        """
        cohort = []
        
        # Get survivors from previous race
        survivors = self.get_race_survivors(parent_race_id)
        
        if not survivors:
            print("No survivors found - will create fresh cohort")
            return []
        
        # Create mutated variants of survivors
        for survivor in survivors:
            for i in range(num_mutations_per_survivor):
                # Random mutation type
                mutation_type = random.choice([
                    "conservative", "risk_adjust", "asset_shift",
                    "time_horizon", "aggressive"
                ])
                
                child = self.mutator.mutate_agent(survivor, mutation_type)
                cohort.append(child)
        
        # If we have too many, select the best mutations
        if len(cohort) > num_bots:
            # For now, randomly select to maintain diversity
            # Future: score mutations based on parent performance
            cohort = random.sample(cohort, num_bots)
        
        # Fill remaining slots with new bots (optional)
        remaining = num_bots - len(cohort)
        if remaining > 0 and include_new_bots:
            print(f"Adding {remaining} fresh bots for diversity")
            # These will be created by the AgentFactory
        
        print(f"\nEvolved cohort: {len(cohort)} mutated strategies")
        return cohort
    
    def analyze_strategy_fitness(self, race_ids: List[str]) -> Dict:
        """
        Analyze which archetypes perform best across multiple races.
        
        Returns:
            Dict with archetype performance stats
        """
        fitness = {}
        
        for race_id in race_ids:
            race_file = self.data_dir / "races" / f"{race_id}.json"
            if not race_file.exists():
                continue
            
            with open(race_file) as f:
                race_data = json.load(f)
            
            for agent in race_data.get('agents_full', []):
                arch = agent.get('archetype', 'Unknown')
                pnl = agent.get('total_pnl', 0)
                
                if arch not in fitness:
                    fitness[arch] = {
                        'races': 0,
                        'total_pnl': 0,
                        'wins': 0,
                        'losses': 0,
                        'avg_pnl': 0,
                    }
                
                fitness[arch]['races'] += 1
                fitness[arch]['total_pnl'] += pnl
                if pnl > 0:
                    fitness[arch]['wins'] += 1
                else:
                    fitness[arch]['losses'] += 1
        
        # Calculate averages
        for arch in fitness:
            if fitness[arch]['races'] > 0:
                fitness[arch]['avg_pnl'] = fitness[arch]['total_pnl'] / fitness[arch]['races']
                fitness[arch]['win_rate'] = fitness[arch]['wins'] / fitness[arch]['races']
        
        return fitness


# Convenience function for quick mutation
def mutate_winners(race_id: str, num_variants: int = 2) -> List[Dict]:
    """
    Quick function to mutate winners from a race.
    
    Usage:
        evolved_bots = mutate_winners('race_20260223_170125', num_variants=2)
    """
    engine = EvolutionEngine()
    return engine.create_evolved_cohort(
        race_id, 
        num_bots=7,
        num_mutations_per_survivor=num_variants
    )


if __name__ == "__main__":
    # Test the evolution engine
    print("🧬 Testing Evolution Engine")
    print("="*60)
    
    engine = EvolutionEngine()
    
    # Test with Race 3 (Danny's big win)
    survivors = engine.get_race_survivors("race_20260223_170125")
    
    if survivors:
        print("\n🔬 Creating mutated variants...")
        mutator = StrategyMutator()
        
        # Show mutation examples
        for survivor in survivors[:2]:  # Top 2 survivors
            name = survivor.get('name', 'Unknown').split('_')[0]
            print(f"\n{name} mutations:")
            
            for mutation_type in ["conservative", "risk_adjust", "aggressive"]:
                child = mutator.mutate_agent(survivor, mutation_type)
                changes = child.get('mutated_params', {}).get('changes', {})
                print(f"  {mutation_type}: {len(changes)} params changed")
                for param, change in list(changes.items())[:2]:  # Show first 2
                    print(f"    - {param}: {change['from']} → {change['to']}")
