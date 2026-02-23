"""
Survival Mode - Bots become desperate when facing elimination
"""

import random
from typing import Dict, List, Tuple

# Survival mode triggers
def calculate_standings(agents: List[Dict]) -> List[Tuple[int, str, float, float]]:
    """Calculate current race standings with P&L."""
    standings = []
    for agent in agents:
        pnl = agent.get('total_pnl', 0)
        pnl_pct = agent.get('pnl_pct', 0)
        standings.append((agent['agent_id'], agent['name'], pnl, pnl_pct))
    
    # Sort by P&L (highest first)
    standings.sort(key=lambda x: x[3], reverse=True)
    return standings


def get_elimination_zone(standings: List, total_bots: int = 7) -> List[str]:
    """Get agent IDs in bottom 40% (elimination zone)."""
    elimination_count = max(1, int(total_bots * 0.4))
    return [s[0] for s in standings[-elimination_count:]]


def get_survival_quote(character: str, rank: int, total: int, in_danger: bool) -> str:
    """Get a personality-appropriate survival quote."""
    
    quotes = {
        "Harper": {
            "safe": [
                "I'm where I belong - at the top.",
                "The trend is my friend, and I'm trending up.",
                "Let them fight for scraps below."
            ],
            "danger": [
                "This is NOT how this ends!",
                "I need to find a trend NOW.",
                "I will NOT be eliminated. Watch me.",
                "Time to get aggressive. Very aggressive."
            ]
        },
        "Rishi": {
            "safe": [
                "Fast and precise. Just like always.",
                "Scalping my way to victory.",
                "Can't catch what you can't see."
            ],
            "danger": [
                "Faster. I need to trade FASTER.",
                "One good scalp. Just one.",
                "I'm not going out like this!",
                "Volume is drying up... but I need this."
            ]
        },
        "Yasmin": {
            "safe": [
                "Patience pays. As always.",
                "The whales are on my side.",
                "Quality over quantity, darling."
            ],
            "danger": [
                "This is... uncomfortable.",
                "I may need to lower my standards.",
                "Father would NOT approve of this position.",
                "Perhaps I should have taken that trade..."
            ]
        },
        "Gus": {
            "safe": [
                "Markets revert. I don't.",
                "Statistically, I'm superior.",
                "The numbers don't lie."
            ],
            "danger": [
                "This is an outlier. A statistical anomaly!",
                "The market is irrational longer than I can stay solvent...",
                "My models predicted this... but I didn't listen.",
                "Reversion to mean is COMING. It HAS to."
            ]
        },
        "Robert": {
            "safe": [
                "YOLO pays when you know how!",
                "Momentum is my middle name.",
                "Fortune favors the bold!"
            ],
            "danger": [
                "ALL IN. ALL IN NOW!",
                "This is not how I go down!",
                "20x leverage? Try 50x!",
                "I need the biggest trade of my LIFE!",
                "YOLO isn't just a strategy - it's survival!"
            ]
        },
        "Eric": {
            "safe": [
                "Patience and discipline. Always.",
                "The MD doesn't panic.",
                "My strategy is sound."
            ],
            "danger": [
                "This is concerning... but I'll stick to the plan.",
                "Discipline. Even when it's hard.",
                "One breakout. That's all I need.",
                "I didn't mentor others to fail myself."
            ]
        },
        "Danny": {
            "safe": [
                "YOLO! I'm either rich or dead!",
                "All in, baby!",
                "You can't fire me if I quit first!"
            ],
            "danger": [
                "FIRED?! NOBODY FIRES DANNY!",
                "ALL IN! EVERYTHING!",
                "I'LL SHOW THEM! I'LL SHOW THEM ALL!",
                "MAX LEVERAGE! NO STOPS!",
                "THIS IS NOT HOW MY STORY ENDS!"
            ]
        }
    }
    
    char_quotes = quotes.get(character, quotes["Harper"])
    if in_danger:
        return random.choice(char_quotes["danger"])
    else:
        return random.choice(char_quotes["safe"])


def apply_survival_mode(agent: Dict, standings: List, is_in_danger: bool) -> Dict:
    """Apply survival mode adjustments to an agent."""
    
    character = agent.get('character', agent.get('name', '').split('_')[0])
    rank = next((i+1 for i, s in enumerate(standings) if s[0] == agent['agent_id']), len(standings))
    
    # Add survival status to agent
    agent['survival'] = {
        'rank': rank,
        'total': len(standings),
        'in_danger': is_in_danger,
        'quote': get_survival_quote(character, rank, len(standings), is_in_danger)
    }
    
    # Adjust behavior based on danger level
    if is_in_danger:
        # Get current risk params
        risk = agent.get('risk_management', {})
        archetype = agent.get('archetype', 'Unknown')
        
        # Each archetype responds differently to danger
        if archetype == 'YOLO':
            # Danny/Robert: Go MORE aggressive
            risk['leverage'] = min(int(risk.get('leverage', '10x').rstrip('x')) + 5, 20)
            risk['stop_loss'] = '20%'  # Wider stops
            agent['survival']['mode'] = 'DESPERATE'
            agent['survival']['action'] = 'MAX_RISK'
            
        elif archetype == 'Scalper':
            # Rishi: Trade more frequently
            risk['frequency_multiplier'] = 2.0
            risk['profit_target_reduction'] = 0.5  # Take smaller profits faster
            agent['survival']['mode'] = 'HYPERACTIVE'
            agent['survival']['action'] = 'VOLUME_UP'
            
        elif archetype == 'Trend Follower':
            # Harper: Lower standards for trend confirmation
            risk['trend_confirmation'] = 'loose'
            risk['early_entry'] = True
            agent['survival']['mode'] = 'AGGRESSIVE'
            agent['survival']['action'] = 'EARLY_ENTRY'
            
        elif archetype == 'Mean Reverter':
            # Gus: Wait longer or give up sooner
            risk['mean_threshold'] = 1.5  # Less extreme requirements
            risk['max_hold_time'] = '30min'  # Don't wait forever
            agent['survival']['mode'] = 'ADAPTIVE'
            agent['survival']['action'] = 'FASTER_EXITS'
            
        elif archetype == 'Whale Watcher':
            # Yasmin: Lower standards for whale signals
            risk['whale_threshold'] = 0.7  # Accept weaker signals
            risk['confirmation_time'] = '3min'  # Less patience
            agent['survival']['mode'] = 'PRAGMATIC'
            agent['survival']['action'] = 'LOWER_STANDARDS'
            
        elif archetype == 'Breakout Hunter':
            # Eric: Take more breakout attempts
            risk['breakout_confirmation'] = 'single_candle'
            risk['retest_not_required'] = True
            agent['survival']['mode'] = 'OPPORTUNISTIC'
            agent['survival']['action'] = 'EARLIER_ENTRIES'
            
        elif archetype == 'Momentum Surfer':
            # Robert: Chase harder
            risk['chase_threshold'] = 1.0  # Smaller moves to chase
            risk['fomo_factor'] = 2.0
            agent['survival']['mode'] = 'FOMO_MAX'
            agent['survival']['action'] = 'CHASE_EVERYTHING'
    else:
        agent['survival']['mode'] = 'NORMAL'
        agent['survival']['action'] = 'STANDARD_OPS'
    
    return agent


def get_elimination_warning(minutes_remaining: int, standings: List) -> str:
    """Get dramatic elimination warnings as race nears end."""
    
    if minutes_remaining <= 10:
        danger_zone = get_elimination_zone(standings)
        danger_names = [s[1] for s in standings if s[0] in danger_zone]
        
        warnings = [
            f"🔥 FINAL {minutes_remaining} MINUTES! 🔥",
            f"⚠️ At risk: {', '.join(danger_names[:2])}...",
            "💀 ELIMINATION IMMINENT",
            "🚨 THIS IS NOT A DRILL 🚨"
        ]
        return '\n'.join(warnings)
    
    elif minutes_remaining <= 30:
        return f"⏰ {minutes_remaining} minutes left. The bottom 40% are sweating..."
    
    elif minutes_remaining <= 60:
        return f"⚡ Final hour! Survival mode activated for the struggling..."
    
    return None


# Export main functions
__all__ = [
    'calculate_standings',
    'get_elimination_zone', 
    'get_survival_quote',
    'apply_survival_mode',
    'get_elimination_warning'
]
