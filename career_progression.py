"""
Career Progression System - Bots earn titles, achievements, and leadership roles
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from desk_management import check_and_create_desk, desk_manager

CAREER_FILE = "careers/career_tracker.json"

# Achievement tiers
ACHIEVEMENTS = {
    "PROFIT_MILESTONES": {
        "first_profit": {"name": "First Blood", "desc": "Made first profitable trade", "icon": "🩸"},
        "profit_10": {"name": "Double Digit", "desc": "10%+ profit in a race", "icon": "📈"},
        "profit_25": {"name": "Quarter Master", "desc": "25%+ profit in a race", "icon": "💰"},
        "profit_50": {"name": "Halfway Hero", "desc": "50%+ profit in a race", "icon": "🚀"},
        "profit_100": {"name": "Centurion", "desc": "100%+ profit (doubled money)", "icon": "👑"},
    },
    "RACE_PERFORMANCE": {
        "survivor": {"name": "Survivor", "desc": "Survived elimination", "icon": "🏆"},
        "winner": {"name": "Champion", "desc": "Won a race", "icon": "🥇"},
        "back_to_back": {"name": "Unstoppable", "desc": "Won 2 races in a row", "icon": "🔥"},
        "comeback": {"name": "Phoenix", "desc": "Won after being in last place", "icon": "🐦‍🔥"},
        "underdog": {"name": "Underdog", "desc": "Won while in bottom 3 mid-race", "icon": "🎯"},
    },
    "TRADING_STYLE": {
        "volume_king": {"name": "Volume King", "desc": "Most trades in a race", "icon": "⚡"},
        "sniper": {"name": "Sniper", "desc": "90%+ win rate (min 5 trades)", "icon": "🎯"},
        "YOLO_god": {"name": "YOLO God", "desc": "Won with 20x leverage", "icon": "🎲"},
        "comeback_kid": {"name": "Comeback Kid", "desc": "Recovered from -10% to win", "icon": "📈"},
        "diamond_hands": {"name": "Diamond Hands", "desc": "Held through 20% drawdown to profit", "icon": "💎"},
    },
    "RANK_PROGRESSION": {
        "rookie": {"name": "Rookie", "desc": "First race completed", "icon": "🌱"},
        "analyst": {"name": "Analyst", "desc": "Survived 3 races", "icon": "📊"},
        "associate": {"name": "Associate", "desc": "Won 1 race", "icon": "💼"},
        "vp": {"name": "VP - Trading", "desc": "Won 3 races OR 2 back-to-back", "icon": "⭐"},
        "director": {"name": "Director", "desc": "Won 5 races total", "icon": "🌟"},
        "md": {"name": "Managing Director", "desc": "Won 10 races OR 5 back-to-back", "icon": "👔"},
        "partner": {"name": "Partner", "desc": "Legendary status: 15+ wins", "icon": "🏛️"},
    }
}

# VP Benefits - what they unlock
VP_BENEFITS = {
    "title_prefix": "VP",
    "starting_capital_bonus": 500,  # +$500 starting capital
    "team_size": 2,  # Can recruit junior traders
    "strategy_boost": 1.1,  # 10% better strategy parameters
    "immunity": 1,  # One elimination immunity per race
    "preferred_assets": ["BTC-USD", "ETH-USD", "NVDA", "SPY"],  # Guaranteed access
}

DIRECTOR_BENEFITS = {
    "title_prefix": "Director",
    "starting_capital_bonus": 1000,
    "team_size": 3,
    "strategy_boost": 1.2,
    "immunity": 2,
    "preferred_assets": ["BTC-USD", "ETH-USD", "NVDA", "SPY", "QQQ", "TSLA"],
}

MD_BENEFITS = {
    "title_prefix": "MD",
    "starting_capital_bonus": 2000,
    "team_size": 5,
    "strategy_boost": 1.3,
    "immunity": 3,
    "all_assets": True,  # Access to everything
    "can_influence_market": True,  # Small market influence
}


class CareerTracker:
    """Track career progression for all trading agents."""
    
    def __init__(self):
        self.careers = {}
        self._load_careers()
    
    def _load_careers(self):
        """Load career data from file."""
        if os.path.exists(CAREER_FILE):
            with open(CAREER_FILE, 'r') as f:
                self.careers = json.load(f)
        else:
            os.makedirs(os.path.dirname(CAREER_FILE), exist_ok=True)
            self.careers = {}
    
    def _save_careers(self):
        """Save career data to file."""
        with open(CAREER_FILE, 'w') as f:
            json.dump(self.careers, f, indent=2)
    
    def get_or_create_career(self, agent_name: str, character: str) -> Dict:
        """Get or create career record for an agent."""
        if agent_name not in self.careers:
            self.careers[agent_name] = {
                "character": character,
                "races_completed": 0,
                "wins": 0,
                "survivals": 0,
                "eliminations": 0,
                "current_title": "Rookie",
                "achievements": [],
                "rank_history": [],
                "best_performance": 0,
                "worst_performance": 0,
                "total_pnl": 0,
                "consecutive_wins": 0,
                "consecutive_survivals": 0,
                "team_members": [],  # Junior traders they lead
                "mentor": None,  # Senior trader they report to
                "vp_benefits_active": False,
                "career_started": datetime.utcnow().isoformat(),
            }
            self._save_careers()
        return self.careers[agent_name]
    
    def record_race_result(self, agent_name: str, race_id: str, rank: int, 
                          total_bots: int, pnl: float, pnl_pct: float, 
                          trades: int, win_rate: float) -> List[Dict]:
        """Record a race result and check for achievements."""
        
        career = self.careers.get(agent_name)
        if not career:
            return []
        
        new_achievements = []
        character = career["character"]
        
        # Update stats
        career["races_completed"] += 1
        career["total_pnl"] += pnl
        career["rank_history"].append({
            "race_id": race_id,
            "rank": rank,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "date": datetime.utcnow().isoformat()
        })
        
        # Track best/worst performance
        if pnl_pct > career["best_performance"]:
            career["best_performance"] = pnl_pct
        if pnl_pct < career["worst_performance"]:
            career["worst_performance"] = pnl_pct
        
        # Check win/survival/elimination
        elimination_zone = int(total_bots * 0.4)
        
        if rank == 1:
            # WON!
            career["wins"] += 1
            career["consecutive_wins"] += 1
            career["consecutive_survivals"] += 1
            
            # Check for achievement
            if career["consecutive_wins"] >= 2:
                new_achievements.append(self._award_achievement(agent_name, "back_to_back", character))
            else:
                new_achievements.append(self._award_achievement(agent_name, "winner", character))
                
            # Check for comeback (was in bottom 3)
            recent_ranks = [r["rank"] for r in career["rank_history"][-3:]]
            if len(recent_ranks) >= 2 and any(r > total_bots - 2 for r in recent_ranks[:-1]):
                new_achievements.append(self._award_achievement(agent_name, "comeback", character))
                
        elif rank > total_bots - elimination_zone:
            # ELIMINATED
            career["eliminations"] += 1
            career["consecutive_wins"] = 0
            career["consecutive_survivals"] = 0
            
        else:
            # SURVIVED
            career["survivals"] += 1
            career["consecutive_survivals"] += 1
            career["consecutive_wins"] = 0
            new_achievements.append(self._award_achievement(agent_name, "survivor", character))
        
        # Check profit milestones
        if pnl_pct >= 100 and "centurion" not in [a["id"] for a in career["achievements"]]:
            new_achievements.append(self._award_achievement(agent_name, "centurion", character))
        elif pnl_pct >= 50 and "profit_50" not in [a["id"] for a in career["achievements"]]:
            new_achievements.append(self._award_achievement(agent_name, "profit_50", character))
        elif pnl_pct >= 25 and "profit_25" not in [a["id"] for a in career["achievements"]]:
            new_achievements.append(self._award_achievement(agent_name, "profit_25", character))
        elif pnl_pct >= 10 and "profit_10" not in [a["id"] for a in career["achievements"]]:
            new_achievements.append(self._award_achievement(agent_name, "profit_10", character))
        
        # Check first profit
        if pnl > 0 and career["races_completed"] == 1:
            new_achievements.append(self._award_achievement(agent_name, "first_profit", character))
        
        # Check rank progression
        self._check_rank_progression(agent_name, character, career)
        
        self._save_careers()
        return new_achievements
    
    def _award_achievement(self, agent_name: str, achievement_id: str, character: str) -> Dict:
        """Award an achievement to an agent."""
        # Find achievement details
        achievement = None
        for category in ACHIEVEMENTS.values():
            if achievement_id in category:
                achievement = category[achievement_id].copy()
                achievement["id"] = achievement_id
                achievement["awarded_at"] = datetime.utcnow().isoformat()
                break
        
        if achievement:
            self.careers[agent_name]["achievements"].append(achievement)
            print(f"🏆 {character} earned: {achievement['icon']} {achievement['name']} - {achievement['desc']}")
        
        return achievement
    
    def _check_rank_progression(self, agent_name: str, character: str, career: Dict):
        """Check and update title/rank."""
        wins = career["wins"]
        survivals = career["survivals"]
        races = career["races_completed"]
        consecutive = career["consecutive_wins"]
        
        old_title = career["current_title"]
        new_title = old_title
        
        # Determine new title
        if wins >= 15:
            new_title = "Partner"
        elif wins >= 10 or consecutive >= 5:
            new_title = "MD"
        elif wins >= 5:
            new_title = "Director"
        elif wins >= 3 or consecutive >= 2:
            new_title = "VP - Trading"
        elif wins >= 1:
            new_title = "Associate"
        elif races >= 3:
            new_title = "Analyst"
        elif races >= 1:
            new_title = "Rookie"
        
        if new_title != old_title:
            career["current_title"] = new_title
            career["title_promoted_at"] = datetime.utcnow().isoformat()
            
            # Award rank achievement
            rank_key = new_title.lower().replace(" - ", "_").replace(" ", "_")
            self._award_achievement(agent_name, rank_key, character)
            
            # Apply VP benefits if promoted to VP+
            if new_title in ["VP - Trading", "Director", "MD", "Partner"]:
                career["vp_benefits_active"] = True
                print(f"⭐ {character} PROMOTED to {new_title}! VP Benefits activated!")
                
                # Create their trading desk!
                from desk_management import check_and_create_desk
                desk = check_and_create_desk(agent_name, character, new_title)
                if desk:
                    career["desk_id"] = desk.desk_id
                    career["desk_name"] = desk.desk_name
                    print(f"   🏢 {character} now runs: {desk.desk_name}")
                    print(f"   💼 Can hire up to {desk.juniors} junior traders")
            else:
                print(f"📈 {character} promoted to {new_title}!")
    
    def get_leaderboard(self) -> List[Dict]:
        """Get career leaderboard sorted by achievements and wins."""
        leaderboard = []
        for name, career in self.careers.items():
            score = (
                career["wins"] * 100 +
                career["survivals"] * 10 +
                len(career["achievements"]) * 5 +
                career["consecutive_wins"] * 50
            )
            leaderboard.append({
                "name": name,
                "character": career["character"],
                "title": career["current_title"],
                "score": score,
                "wins": career["wins"],
                "achievements": len(career["achievements"]),
                "races": career["races_completed"],
                "total_pnl": career["total_pnl"],
                "best_performance": career["best_performance"],
            })
        
        leaderboard.sort(key=lambda x: x["score"], reverse=True)
        return leaderboard
    
    def get_career_summary(self, agent_name: str) -> str:
        """Get formatted career summary for display."""
        career = self.careers.get(agent_name)
        if not career:
            return f"No career record for {agent_name}"
        
        lines = [
            f"{'='*50}",
            f"📊 CAREER PROFILE: {career['character']}",
            f"{'='*50}",
            f"Title: {career['current_title']}",
            f"Races: {career['races_completed']} (W: {career['wins']}/S: {career['survivals']}/E: {career['eliminations']})",
            f"Consecutive Wins: {career['consecutive_wins']}",
            f"Total P&L: ${career['total_pnl']:.2f}",
            f"Best Race: {career['best_performance']:+.2f}%",
            f"Worst Race: {career['worst_performance']:+.2f}%",
            f"Achievements: {len(career['achievements'])}",
        ]
        
        if career["achievements"]:
            lines.append("\n🏆 Achievements:")
            for ach in career["achievements"][-5:]:  # Last 5
                lines.append(f"  {ach['icon']} {ach['name']}")
        
        if career["vp_benefits_active"]:
            lines.append("\n⭐ VP BENEFITS ACTIVE:")
            if career["current_title"] == "VP - Trading":
                lines.append(f"  +${VP_BENEFITS['starting_capital_bonus']} starting capital")
                lines.append(f"  Can lead {VP_BENEFITS['team_size']} junior traders")
            elif career["current_title"] == "Director":
                lines.append(f"  +${DIRECTOR_BENEFITS['starting_capital_bonus']} starting capital")
                lines.append(f"  Can lead {DIRECTOR_BENEFITS['team_size']} traders")
            elif career["current_title"] in ["MD", "Partner"]:
                lines.append(f"  +${MD_BENEFITS['starting_capital_bonus']} starting capital")
                lines.append(f"  Can lead {MD_BENEFITS['team_size']} traders")
                lines.append("  Market influence: ENABLED")
        
        lines.append(f"{'='*50}")
        return "\n".join(lines)


# Singleton instance
career_tracker = CareerTracker()


def record_race_result(agent_name: str, race_id: str, rank: int, 
                      total_bots: int, pnl: float, pnl_pct: float,
                      trades: int, win_rate: float) -> List[Dict]:
    """Convenience function to record race result."""
    # Extract character from name (e.g., "Harper_abc123" -> "Harper")
    character = agent_name.split('_')[0] if '_' in agent_name else agent_name
    
    # Initialize if needed
    career_tracker.get_or_create_career(agent_name, character)
    
    # Record result
    return career_tracker.record_race_result(
        agent_name, race_id, rank, total_bots, pnl, pnl_pct, trades, win_rate
    )


def get_career_leaderboard() -> List[Dict]:
    """Get the career leaderboard."""
    return career_tracker.get_leaderboard()


def get_career_summary(agent_name: str) -> str:
    """Get career summary for an agent."""
    return career_tracker.get_career_summary(agent_name)
