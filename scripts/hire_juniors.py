"""
Hire juniors for promoted bots - Run this to populate desks with junior traders
"""

import sys
sys.path.insert(0, '/root/clawd/projects/trading-arena')

from career_progression import career_tracker
from desk_management import desk_manager, DESK_CONFIG
from agent_factory import AgentFactory


def hire_juniors_for_all_desks():
    """Hire juniors for all desks that have room."""
    factory = AgentFactory()
    
    print("🏢 Hiring juniors for all trading desks...")
    print("="*60)
    
    for desk_id, desk in desk_manager.desks.items():
        leader_name = desk.leader_name
        character = desk.leader_character
        title = desk.leader_title
        
        config = DESK_CONFIG.get(title, DESK_CONFIG["VP - Trading"])
        current_juniors = len(desk.juniors)
        max_juniors = config["max_juniors"]
        
        if current_juniors >= max_juniors:
            print(f"\n✅ {desk.desk_name} - Full staff ({current_juniors}/{max_juniors})")
            continue
        
        # Get leader's strategy from career data
        career = career_tracker.careers.get(leader_name, {})
        
        # Create a parent strategy based on character
        parent_strategy = {
            "name": f"{character}_Strategy",
            "max_leverage": 10,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "entry_threshold": 0.6,
            "position_size_pct": 0.2,
            "max_positions": 3,
        }
        
        # Hire up to max
        to_hire = max_juniors - current_juniors
        print(f"\n📋 {desk.desk_name}")
        print(f"   Hiring {to_hire} junior trader(s)...")
        
        for i in range(to_hire):
            junior = desk.hire_junior(parent_strategy, factory)
            if junior:
                print(f"   ✅ Hired: {junior.name}")
        
        desk_manager._save_desks()
    
    print("\n" + "="*60)
    print("Hiring complete!")
    print(desk_manager.get_leaderboard())


def show_desk_status():
    """Show status of all desks."""
    print(desk_manager.get_leaderboard())


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "hire":
        hire_juniors_for_all_desks()
    else:
        show_desk_status()
