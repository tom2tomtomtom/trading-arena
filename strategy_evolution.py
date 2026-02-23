"""
Strategy Evolution & Learning System - Bots actually learn and improve over races
"""

import json
import os
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from llm_strategies import mutate_strategy


class StrategyMemory:
    """Stores learned insights from races for each bot."""
    
    def __init__(self, character: str):
        self.character = character
        self.memory_file = f"memory/{character}_strategy_memory.json"
        self.learned_rules = []
        self.successful_setups = []
        self.failed_setups = []
        self.market_conditions_performance = {}
        self._load_memory()
    
    def _load_memory(self):
        """Load previous learning."""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
                self.learned_rules = data.get('learned_rules', [])
                self.successful_setups = data.get('successful_setups', [])
                self.failed_setups = data.get('failed_setups', [])
                self.market_conditions_performance = data.get('market_conditions', {})
    
    def _save_memory(self):
        """Save learned insights."""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump({
                'character': self.character,
                'learned_rules': self.learned_rules,
                'successful_setups': self.successful_setups,
                'failed_setups': self.failed_setups,
                'market_conditions': self.market_conditions_performance,
                'last_updated': datetime.utcnow().isoformat()
            }, f, indent=2)
    
    def record_trade_result(self, trade: Dict, result: str, pnl: float, 
                           market_condition: str = None):
        """Learn from a trade outcome."""
        
        trade_summary = {
            'symbol': trade.get('symbol'),
            'direction': trade.get('direction'),
            'entry_price': trade.get('entry_price'),
            'exit_price': trade.get('exit_price'),
            'pnl': pnl,
            'timestamp': datetime.utcnow().isoformat(),
            'market_condition': market_condition or 'unknown'
        }
        
        if result == 'win' and pnl > 0:
            self.successful_setups.append(trade_summary)
            # Keep only last 50 successful setups
            self.successful_setups = self.successful_setups[-50:]
            
            # Extract pattern
            self._extract_success_pattern(trade_summary)
            
        elif result == 'loss':
            self.failed_setups.append(trade_summary)
            self.failed_setups = self.failed_setups[-50:]
            
            # Learn what NOT to do
            self._extract_failure_lesson(trade_summary)
        
        # Track performance by market condition
        if market_condition:
            if market_condition not in self.market_conditions_performance:
                self.market_conditions_performance[market_condition] = {
                    'trades': 0, 'wins': 0, 'total_pnl': 0
                }
            perf = self.market_conditions_performance[market_condition]
            perf['trades'] += 1
            if result == 'win':
                perf['wins'] += 1
            perf['total_pnl'] += pnl
        
        self._save_memory()
    
    def _extract_success_pattern(self, trade: Dict):
        """Extract what made this trade successful."""
        symbol = trade.get('symbol')
        direction = trade.get('direction')
        
        # Learn asset preference
        rule = f"{direction} {symbol} has worked well"
        if rule not in self.learned_rules:
            self.learned_rules.append(rule)
    
    def _extract_failure_lesson(self, trade: Dict):
        """Learn from failure."""
        symbol = trade.get('symbol')
        direction = trade.get('direction')
        
        lesson = f"Avoid {direction} {symbol} - repeated losses"
        if lesson not in self.learned_rules:
            self.learned_rules.append(lesson)
    
    def get_best_market_condition(self) -> Optional[str]:
        """Get market condition where this bot performs best."""
        if not self.market_conditions_performance:
            return None
        
        best = None
        best_win_rate = 0
        
        for condition, perf in self.market_conditions_performance.items():
            if perf['trades'] >= 3:  # Minimum sample size
                win_rate = perf['wins'] / perf['trades']
                if win_rate > best_win_rate:
                    best_win_rate = win_rate
                    best = condition
        
        return best
    
    def get_learned_insights(self) -> List[str]:
        """Get list of learned insights."""
        return self.learned_rules[-10:]  # Last 10 insights


class StrategyEvolver:
    """Evolves winning strategies and eliminates losing ones."""
    
    EVOLUTION_FILE = "evolution/strategy_lineage.json"
    
    def __init__(self):
        self.lineage = {}
        self._load_lineage()
    
    def _load_lineage(self):
        """Load strategy family tree."""
        if os.path.exists(self.EVOLUTION_FILE):
            with open(self.EVOLUTION_FILE, 'r') as f:
                self.lineage = json.load(f)
    
    def _save_lineage(self):
        """Save strategy family tree."""
        os.makedirs(os.path.dirname(self.EVOLUTION_FILE), exist_ok=True)
        with open(self.EVOLUTION_FILE, 'w') as f:
            json.dump(self.lineage, f, indent=2)
    
    def record_race_outcome(self, race_id: str, results: List[Dict]):
        """
        Record race results and determine evolution.
        
        results: List of {agent_name, character, strategy, rank, pnl, pnl_pct}
        """
        # Sort by P&L
        sorted_results = sorted(results, key=lambda x: x['pnl'], reverse=True)
        
        # Top 60% survive and evolve
        survivors = sorted_results[:int(len(sorted_results) * 0.6)]
        eliminated = sorted_results[int(len(sorted_results) * 0.6):]
        
        print(f"\n🧬 STRATEGY EVOLUTION - Race {race_id}")
        print("="*60)
        
        # Record winners
        for result in survivors:
            char = result['character']
            strategy = result.get('strategy', {})
            
            if char not in self.lineage:
                self.lineage[char] = {
                    'generations': [],
                    'wins': 0,
                    'survivals': 0,
                    'eliminations': 0,
                    'evolution_score': 0
                }
            
            lineage = self.lineage[char]
            
            # Record this generation
            gen = {
                'race_id': race_id,
                'rank': result['rank'],
                'pnl': result['pnl'],
                'pnl_pct': result['pnl_pct'],
                'strategy': strategy,
                'timestamp': datetime.utcnow().isoformat(),
                'outcome': 'WIN' if result['rank'] == 1 else 'SURVIVED'
            }
            lineage['generations'].append(gen)
            
            if result['rank'] == 1:
                lineage['wins'] += 1
                print(f"🏆 {char} WON! Strategy evolves to next generation.")
            else:
                lineage['survivals'] += 1
                print(f"✅ {char} survived. Strategy cloned with minor mutations.")
            
            # Calculate evolution score
            lineage['evolution_score'] = (
                lineage['wins'] * 10 +
                lineage['survivals'] * 3 -
                lineage['eliminations'] * 5
            )
        
        # Record eliminated strategies
        for result in eliminated:
            char = result['character']
            if char in self.lineage:
                self.lineage[char]['eliminations'] += 1
                print(f"❌ {char} eliminated. Strategy dies here.")
                
                # Check if this is a recurring failure
                if self.lineage[char]['eliminations'] >= 3:
                    print(f"   💀 {char}'s strategy lineage is EXTINCT after 3 eliminations.")
        
        self._save_lineage()
        
        # Generate next race strategies
        next_gen = self._generate_next_generation(race_id)
        
        return next_gen
    
    def _generate_next_generation(self, prev_race_id: str) -> Dict[str, Dict]:
        """Generate strategies for next race based on evolution."""
        
        next_gen = {}
        
        print(f"\n🧪 GENERATING NEXT GENERATION STRATEGIES")
        print("="*60)
        
        # Sort by evolution score
        ranked = sorted(
            self.lineage.items(),
            key=lambda x: x[1]['evolution_score'],
            reverse=True
        )
        
        for char, lineage in ranked:
            if not lineage['generations']:
                continue
            
            # Get last successful strategy
            last_gen = lineage['generations'][-1]
            last_strategy = last_gen['strategy']
            
            # Determine mutation level based on performance
            if last_gen['outcome'] == 'WIN':
                # Winner - small refinement
                mutation_level = 'minor'
                generations_to_skip = 0
            elif lineage['eliminations'] > 0:
                # Was eliminated - major overhaul needed
                mutation_level = 'major'
                generations_to_skip = 1
            else:
                # Survived but didn't win - moderate mutation
                mutation_level = 'moderate'
                generations_to_skip = 0
            
            # Skip if recently eliminated (give it a break)
            if generations_to_skip > 0 and len(lineage['generations']) > 1:
                recent = lineage['generations'][-2:]
                if all(g.get('outcome') == 'ELIMINATED' for g in recent):
                    print(f"   ⏸️  {char} - Taking a break after elimination")
                    continue
            
            # Evolve the strategy
            evolved = self._evolve_strategy(last_strategy, mutation_level, char)
            next_gen[char] = evolved
            
            print(f"   🔄 {char}: {mutation_level} mutation applied")
            if evolved.get('mutation_note'):
                print(f"      └─ {evolved['mutation_note']}")
        
        return next_gen
    
    def _evolve_strategy(self, parent: Dict, mutation_level: str, character: str) -> Dict:
        """Evolve a strategy with specified mutation level."""
        
        child = parent.copy()
        child['parent_strategy'] = parent.get('strategy_name', 'unknown')
        child['generation'] = parent.get('generation', 1) + 1
        child['mutation_level'] = mutation_level
        child['created_at'] = datetime.utcnow().isoformat()
        
        # Apply mutations based on level
        if mutation_level == 'minor':
            # Winner - just fine-tune
            mutations = [
                "Tightened stop loss by 0.5%",
                "Increased position size slightly",
                "Added volume confirmation filter",
                "Extended hold time for winners"
            ]
            child['strategy_name'] = f"{parent.get('strategy_name', 'Strategy')} v{child['generation']}"
            child['mutation_note'] = random.choice(mutations)
            
            # Small numerical adjustments
            if 'risk_management' in child:
                rm = child['risk_management']
                if 'stop_loss' in rm:
                    val = float(rm['stop_loss'].rstrip('%'))
                    rm['stop_loss'] = f"{max(1, val - 0.5)}%"
        
        elif mutation_level == 'moderate':
            # Survivor - try something new
            mutations = [
                "Added new entry condition",
                "Switched primary timeframe",
                "Diversified asset selection",
                "Adjusted risk/reward ratio"
            ]
            child['strategy_name'] = f"{parent.get('strategy_name', 'Strategy')} Evo {child['generation']}"
            child['mutation_note'] = random.choice(mutations)
            
            # Medium changes
            if 'entry_rules' in child and len(child['entry_rules']) >= 3:
                # Replace one rule
                idx = random.randint(0, 2)
                child['entry_rules'][idx] = f"[EVOLVED] {child['entry_rules'][idx]}"
        
        elif mutation_level == 'major':
            # Eliminated - desperate overhaul
            mutations = [
                "Complete strategy overhaul",
                "New asset class focus",
                "Inverted logic - do the opposite",
                "Aggressive parameter changes"
            ]
            child['strategy_name'] = f"{parent.get('strategy_name', 'Strategy')} REBORN"
            child['mutation_note'] = random.choice(mutations)
            child['reborn'] = True
            
            # Major changes
            if 'risk_management' in child:
                rm = child['risk_management']
                # Flip leverage (if was low, go high; if was high, go conservative)
                if 'leverage' in rm:
                    lev = int(str(rm['leverage']).rstrip('x'))
                    if lev < 10:
                        rm['leverage'] = f"{min(20, lev + 5)}x"
                    else:
                        rm['leverage'] = f"{max(3, lev - 3)}x"
        
        return child
    
    def get_strategy_lineage(self, character: str) -> Dict:
        """Get full evolution history for a character."""
        return self.lineage.get(character, {})
    
    def get_best_strategies(self, n: int = 3) -> List[Tuple[str, Dict]]:
        """Get top N strategies by evolution score."""
        ranked = sorted(
            self.lineage.items(),
            key=lambda x: x[1]['evolution_score'],
            reverse=True
        )
        return ranked[:n]


# Singleton instance
evolver = StrategyEvolver()


def record_race_for_evolution(race_id: str, agent_results: List[Dict]) -> Dict[str, Dict]:
    """Record race and get next generation strategies."""
    return evolver.record_race_outcome(race_id, agent_results)


def get_next_generation_strategies(race_id: str) -> Dict[str, Dict]:
    """Get evolved strategies for next race."""
    return evolver._generate_next_generation(race_id)


def get_evolution_report(character: str = None) -> str:
    """Get formatted evolution report."""
    if character:
        lineage = evolver.get_strategy_lineage(character)
        if not lineage:
            return f"No evolution history for {character}"
        
        lines = [
            f"\n{'='*60}",
            f"🧬 EVOLUTION REPORT: {character}",
            f"{'='*60}",
            f"Generations: {len(lineage.get('generations', []))}",
            f"Wins: {lineage.get('wins', 0)}",
            f"Survivals: {lineage.get('survivals', 0)}",
            f"Eliminations: {lineage.get('eliminations', 0)}",
            f"Evolution Score: {lineage.get('evolution_score', 0)}",
            f"\n📜 Lineage:",
        ]
        
        for gen in lineage.get('generations', [])[-5:]:  # Last 5
            lines.append(f"  Race {gen['race_id']}: Rank #{gen['rank']} | "
                        f"P&L: ${gen['pnl']:+.2f} | {gen['outcome']}")
        
        lines.append(f"{'='*60}")
        return "\n".join(lines)
    
    else:
        # Overall report
        lines = [
            f"\n{'='*60}",
            f"🧬 OVERALL EVOLUTION LEADERBOARD",
            f"{'='*60}",
        ]
        
        best = evolver.get_best_strategies(5)
        for i, (char, lineage) in enumerate(best, 1):
            lines.append(f"\n{i}. {char}")
            lines.append(f"   Score: {lineage['evolution_score']} | "
                        f"W: {lineage['wins']} S: {lineage['survivals']} E: {lineage['eliminations']}")
            if lineage['generations']:
                last = lineage['generations'][-1]
                lines.append(f"   Last: Race {last['race_id']} - {last['outcome']}")
        
        lines.append(f"{'='*60}")
        return "\n".join(lines)
