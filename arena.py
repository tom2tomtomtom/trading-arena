#!/usr/bin/env python3
"""
Trading Arena - Main race controller.
Manages races, runs agents, tracks performance, and evolves winners.
"""

import json
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from config import (
    RACE_DURATION_HOURS,
    STARTING_CAPITAL,
    BOTS_PER_RACE,
    TRADING_UNIVERSE,
    SURVIVAL_THRESHOLD,
    MUTATION_RATE,
)
from agent_factory import AgentFactory, TradingAgent
from paper_trader import PaperTrader, SignalGenerator
from survival_mode import (
    calculate_standings,
    get_elimination_zone,
    get_elimination_warning,
    apply_survival_mode
)


class Race:
    """A single race (competition round) between agents."""
    
    def __init__(
        self,
        race_id: str,
        agents: List[TradingAgent],
        duration_hours: float = RACE_DURATION_HOURS,
        risk_tier: str = "moderate",
    ):
        self.race_id = race_id
        self.agents = agents
        self.duration_hours = duration_hours
        self.risk_tier = risk_tier
        
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status = "pending"  # pending, running, completed
        
        self.snapshots: List[Dict] = []  # Periodic state snapshots
        
    @property
    def elapsed_time(self) -> timedelta:
        if not self.start_time:
            return timedelta(0)
        end = self.end_time or datetime.utcnow()
        return end - self.start_time
    
    @property
    def time_remaining(self) -> timedelta:
        if not self.start_time:
            return timedelta(hours=self.duration_hours)
        target_end = self.start_time + timedelta(hours=self.duration_hours)
        remaining = target_end - datetime.utcnow()
        return max(remaining, timedelta(0))
    
    @property
    def is_complete(self) -> bool:
        return self.time_remaining.total_seconds() <= 0
    
    def get_leaderboard(self) -> List[Dict]:
        """Get current leaderboard sorted by P&L."""
        leaderboard = []
        for agent in self.agents:
            leaderboard.append({
                "rank": 0,
                "color": agent.color,
                "name": agent.name,
                "archetype": agent.archetype["name"],
                "portfolio_value": agent.portfolio_value,
                "pnl": agent.total_pnl,
                "pnl_pct": agent.total_pnl_pct,
                "trades": len(agent.trades),
                "win_rate": agent.win_rate,
                "positions": len(agent.positions),
            })
        
        # Sort by P&L descending
        leaderboard.sort(key=lambda x: x["pnl"], reverse=True)
        
        # Assign ranks
        for i, entry in enumerate(leaderboard):
            entry["rank"] = i + 1
        
        return leaderboard
    
    def take_snapshot(self) -> Dict:
        """Take a snapshot of current race state."""
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "elapsed_seconds": self.elapsed_time.total_seconds(),
            "leaderboard": self.get_leaderboard(),
        }
        self.snapshots.append(snapshot)
        return snapshot
    
    def to_dict(self) -> Dict:
        return {
            "race_id": self.race_id,
            "agents": [a.agent_id for a in self.agents],
            "duration_hours": self.duration_hours,
            "risk_tier": self.risk_tier,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "snapshots": self.snapshots,
        }


class Arena:
    """Main arena controller - manages races and agent evolution."""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.agents_dir = self.project_dir / "agents"
        self.races_dir = self.project_dir / "races"
        self.logs_dir = self.project_dir / "logs"
        
        # Ensure directories exist
        for d in [self.agents_dir, self.races_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        self.factory = AgentFactory(str(self.agents_dir))
        self.paper_trader = PaperTrader()
        self.signal_generator = SignalGenerator()
        
        self.current_race: Optional[Race] = None
    
    def create_race(
        self,
        num_bots: int = BOTS_PER_RACE,
        risk_tier: str = "moderate",
        duration_hours: float = RACE_DURATION_HOURS,
    ) -> Race:
        """Create a new race with fresh agents."""
        
        # Generate race ID
        race_id = datetime.utcnow().strftime("race_%Y%m%d_%H%M%S")
        
        # Create agent cohort
        agents = self.factory.create_race_cohort(
            num_bots=num_bots,
            risk_tier=risk_tier,
            starting_capital=STARTING_CAPITAL,
        )
        
        race = Race(
            race_id=race_id,
            agents=agents,
            duration_hours=duration_hours,
            risk_tier=risk_tier,
        )
        
        self.current_race = race
        self._save_race(race)
        
        return race
    
    def start_race(self) -> Optional[Race]:
        """Start the current race."""
        if not self.current_race:
            print("No race to start. Create one first.")
            return None
        
        self.current_race.start_time = datetime.utcnow()
        self.current_race.status = "running"
        self._save_race(self.current_race)
        
        print(f"\n🏁 RACE STARTED: {self.current_race.race_id}")
        print(f"   Duration: {self.current_race.duration_hours} hours")
        print(f"   Risk Tier: {self.current_race.risk_tier}")
        print(f"   Bots: {len(self.current_race.agents)}")
        print("\n📊 Starting Lineup:")
        for agent in self.current_race.agents:
            print(f"   {agent.color} {agent.name} ({agent.archetype['name']})")
        print()
        
        return self.current_race
    
    def run_cycle(self) -> Dict:
        """Run one trading cycle for all agents in the race."""
        if not self.current_race or self.current_race.status != "running":
            return {"error": "No active race"}
        
        if self.current_race.is_complete:
            self.end_race()
            return {"status": "race_complete"}
        
        # Check for elimination warnings
        minutes_remaining = self.current_race.time_remaining.total_seconds() / 60
        current_leaderboard = self.current_race.get_leaderboard()
        warning = get_elimination_warning(minutes_remaining, current_leaderboard)
        if warning:
            print(f"\n{warning}\n")
        
        # Calculate standings and elimination zone
        standings = calculate_standings([
            {
                'agent_id': a.agent_id,
                'name': a.name,
                'total_pnl': a.total_pnl,
                'pnl_pct': a.total_pnl_pct
            }
            for a in self.current_race.agents
        ])
        elimination_zone = get_elimination_zone(standings, len(self.current_race.agents))
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": [],
            "survival_mode_active": False,
        }
        
        for agent in self.current_race.agents:
            # Apply survival mode if in danger
            is_in_danger = agent.agent_id in elimination_zone
            if is_in_danger:
                results["survival_mode_active"] = True
                # Convert agent to dict for survival mode, then apply changes
                agent_dict = {
                    'agent_id': agent.agent_id,
                    'name': agent.name,
                    'character': agent.name.split('_')[0] if '_' in agent.name else agent.name,
                    'archetype': agent.archetype['name'],
                    'risk_management': agent.strategy_params.copy(),
                    'total_pnl': agent.total_pnl,
                    'pnl_pct': agent.total_pnl_pct
                }
                survival_data = apply_survival_mode(agent_dict, standings, is_in_danger)
                
                # Print survival quote if in danger
                if 'survival' in survival_data and survival_data['survival'].get('in_danger'):
                    quote = survival_data['survival']['quote']
                    mode = survival_data['survival']['mode']
                    action = survival_data['survival']['action']
                    print(f"\n🔥 {agent.name}: \"{quote}\"")
                    print(f"   Mode: {mode} | Action: {action}")
                    
                    # Apply risk adjustments to agent
                    if 'risk_management' in survival_data:
                        new_risk = survival_data['risk_management']
                        if 'leverage' in new_risk:
                            agent.strategy_params['max_leverage'] = int(str(new_risk['leverage']).rstrip('x'))
            
            agent_result = self._run_agent_cycle(agent)
            results["agents"].append(agent_result)
            self.factory.save_agent(agent)
        
        # Take snapshot
        snapshot = self.current_race.take_snapshot()
        results["leaderboard"] = snapshot["leaderboard"]
        
        self._save_race(self.current_race)
        
        return results
    
    def _run_agent_cycle(self, agent: TradingAgent) -> Dict:
        """Run one trading cycle for a single agent."""
        result = {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "color": agent.color,
            "entries": [],
            "exits": [],
        }
        
        # Update existing positions
        self.paper_trader.update_positions(agent)
        
        # Check stop losses and take profits
        stop_exits = self.paper_trader.check_stop_loss(
            agent, agent.strategy_params["stop_loss_pct"]
        )
        tp_exits = self.paper_trader.check_take_profit(
            agent, agent.strategy_params["take_profit_pct"]
        )
        result["exits"].extend(stop_exits)
        result["exits"].extend(tp_exits)
        
        # Look for new entries if we have room
        if len(agent.positions) < agent.strategy_params["max_positions"]:
            for symbol in agent.strategy_params.get("preferred_assets", TRADING_UNIVERSE[:5]):
                if symbol in agent.positions:
                    continue
                
                signal = self.signal_generator.generate_signal(agent, symbol)
                if signal and signal["strength"] >= agent.strategy_params["entry_threshold"]:
                    position = self.paper_trader.execute_entry(
                        agent=agent,
                        symbol=symbol,
                        direction=signal["direction"],
                        size_pct=agent.strategy_params["position_size_pct"],
                        leverage=min(
                            agent.strategy_params["max_leverage"],
                            1 + signal["strength"] * 10  # Scale leverage with conviction
                        ),
                        reason=signal["reason"],
                    )
                    if position:
                        result["entries"].append({
                            "symbol": symbol,
                            "direction": signal["direction"],
                            "price": position["entry_price"],
                            "leverage": position["leverage"],
                            "reason": signal["reason"],
                        })
                        
                        # Only enter one position per cycle to avoid overtrading
                        break
        
        # Record P&L
        agent.pnl_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "portfolio_value": agent.portfolio_value,
            "cash": agent.cash,
            "positions": len(agent.positions),
        })
        
        result["portfolio_value"] = agent.portfolio_value
        result["pnl"] = agent.total_pnl
        result["pnl_pct"] = agent.total_pnl_pct
        
        return result
    
    def end_race(self) -> Dict:
        """End the current race and determine winners."""
        if not self.current_race:
            return {"error": "No race to end"}
        
        self.current_race.end_time = datetime.utcnow()
        self.current_race.status = "completed"
        
        # Close all positions for final accounting
        for agent in self.current_race.agents:
            for symbol in list(agent.positions.keys()):
                self.paper_trader.execute_exit(agent, symbol, reason="RACE_END")
            self.factory.save_agent(agent)
        
        # Get final leaderboard
        leaderboard = self.current_race.get_leaderboard()
        
        # Determine survivors (top performers)
        num_survivors = int(len(leaderboard) * (1 - SURVIVAL_THRESHOLD))
        survivors = leaderboard[:num_survivors]
        eliminated = leaderboard[num_survivors:]
        
        results = {
            "race_id": self.current_race.race_id,
            "duration": str(self.current_race.elapsed_time),
            "final_leaderboard": leaderboard,
            "survivors": [s["name"] for s in survivors],
            "eliminated": [e["name"] for e in eliminated],
            "total_pnl": sum(a.total_pnl for a in self.current_race.agents),
        }
        
        self._save_race(self.current_race)
        
        # Print results
        print("\n" + "=" * 60)
        print(f"🏁 RACE COMPLETE: {self.current_race.race_id}")
        print("=" * 60)
        print(f"\n📊 FINAL STANDINGS:")
        print("-" * 50)
        
        for entry in leaderboard:
            status = "✅" if entry["name"] in results["survivors"] else "❌"
            print(f"{status} #{entry['rank']} {entry['color']} {entry['name']}")
            print(f"      P&L: ${entry['pnl']:.2f} ({entry['pnl_pct']:+.2f}%)")
            print(f"      Trades: {entry['trades']} | Win Rate: {entry['win_rate']:.1f}%")
        
        print(f"\n💰 Total Portfolio P&L: ${results['total_pnl']:.2f}")
        print(f"🏆 Survivors: {', '.join(results['survivors'])}")
        print(f"💀 Eliminated: {', '.join(results['eliminated'])}")
        
        # Dramatic elimination announcement
        print("\n" + "=" * 60)
        print("🔥 ELIMINATION CEREMONY 🔥")
        print("=" * 60)
        for e in eliminated:
            char_name = e.split('_')[0] if '_' in e else e
            dramatic_lines = {
                'Harper': "Your ambition was admirable... but ambition without results is nothing.",
                'Rishi': "Fast doesn't always mean profitable. Pack your knives.",
                'Yasmin': "Even privilege has its limits. You're out.",
                'Gus': "Your models failed. The market doesn't care about your statistics.",
                'Robert': "YOLO doesn't always work. Unfortunately, you YOLO'd your account.",
                'Eric': "The mentor has become the student... in failure.",
                'Danny': "We knew you'd go out like this. At least you went out swinging.",
                'Venetia': "Sentiment turned against you. Including ours.",
                'Clement': "Pairs diverged, and so did your career here."
            }
            print(f"\n💀 {e}")
            print(f"   \"{dramatic_lines.get(char_name, 'Your strategy failed.')}\"")
        
        print(f"\n🎉 {', '.join(results['survivors'])} - You've earned your place in the next race!")
        
        return results
    
    def get_status(self) -> Dict:
        """Get current arena status."""
        if not self.current_race:
            return {
                "status": "idle",
                "message": "No active race. Create one with: arena.py create",
            }
        
        return {
            "status": self.current_race.status,
            "race_id": self.current_race.race_id,
            "elapsed": str(self.current_race.elapsed_time),
            "remaining": str(self.current_race.time_remaining),
            "leaderboard": self.current_race.get_leaderboard(),
        }
    
    def _save_race(self, race: Race) -> None:
        """Save race state to disk."""
        filepath = self.races_dir / f"{race.race_id}.json"
        
        # Include full agent data
        race_data = race.to_dict()
        race_data["agents_full"] = [a.to_dict() for a in race.agents]
        
        with open(filepath, "w") as f:
            json.dump(race_data, f, indent=2, default=str)
    
    def load_race(self, race_id: str) -> Optional[Race]:
        """Load a race from disk."""
        filepath = self.races_dir / f"{race_id}.json"
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            data = json.load(f)
        
        # Reconstruct agents
        agents = []
        for agent_data in data.get("agents_full", []):
            agent = TradingAgent.from_dict(agent_data)
            agents.append(agent)
        
        race = Race(
            race_id=data["race_id"],
            agents=agents,
            duration_hours=data["duration_hours"],
            risk_tier=data["risk_tier"],
        )
        
        if data.get("start_time"):
            race.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            race.end_time = datetime.fromisoformat(data["end_time"])
        race.status = data["status"]
        race.snapshots = data.get("snapshots", [])
        
        self.current_race = race
        return race


def main():
    parser = argparse.ArgumentParser(description="Trading Arena - AI Bot Competition")
    parser.add_argument("action", choices=["create", "start", "run", "status", "end", "cycle"],
                        help="Action to perform")
    parser.add_argument("--bots", type=int, default=BOTS_PER_RACE, help="Number of bots")
    parser.add_argument("--risk", choices=["moderate", "high", "yolo"], default="moderate",
                        help="Risk tier")
    parser.add_argument("--duration", type=float, default=RACE_DURATION_HOURS,
                        help="Race duration in hours")
    parser.add_argument("--race-id", type=str, help="Race ID for loading")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between cycles")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    arena = Arena()
    
    if args.action == "create":
        race = arena.create_race(
            num_bots=args.bots,
            risk_tier=args.risk,
            duration_hours=args.duration,
        )
        if args.json:
            print(json.dumps(race.to_dict(), indent=2, default=str))
        else:
            print(f"\n✅ Race created: {race.race_id}")
            print(f"   Bots: {len(race.agents)}")
            print(f"   Risk: {race.risk_tier}")
            print(f"   Duration: {race.duration_hours}h")
            print("\n   Run 'arena.py start' to begin the race!")
    
    elif args.action == "start":
        if args.race_id:
            arena.load_race(args.race_id)
        race = arena.start_race()
        if race and args.json:
            print(json.dumps(race.to_dict(), indent=2, default=str))
    
    elif args.action == "run":
        # Full race runner - creates, starts, and runs until complete
        race = arena.create_race(
            num_bots=args.bots,
            risk_tier=args.risk,
            duration_hours=args.duration,
        )
        arena.start_race()
        
        print(f"\n🏃 Running race for {args.duration} hours...")
        print(f"   Cycle interval: {args.interval} seconds")
        
        while not arena.current_race.is_complete:
            result = arena.run_cycle()
            
            # Print mini update
            elapsed = arena.current_race.elapsed_time
            remaining = arena.current_race.time_remaining
            print(f"\n⏱️  {elapsed} elapsed | {remaining} remaining")
            
            leader = result["leaderboard"][0]
            print(f"   🥇 {leader['color']} {leader['name']}: ${leader['pnl']:.2f}")
            
            time.sleep(args.interval)
        
        results = arena.end_race()
        if args.json:
            print(json.dumps(results, indent=2, default=str))
    
    elif args.action == "cycle":
        if args.race_id:
            arena.load_race(args.race_id)
        
        for i in range(args.cycles):
            result = arena.run_cycle()
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"\n📊 Cycle {i+1}/{args.cycles} complete")
                for entry in result.get("leaderboard", [])[:3]:
                    print(f"   #{entry['rank']} {entry['color']} {entry['name']}: ${entry['pnl']:.2f}")
            
            if i < args.cycles - 1:
                time.sleep(args.interval)
    
    elif args.action == "status":
        if args.race_id:
            arena.load_race(args.race_id)
        status = arena.get_status()
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            print(f"\n🏟️  Arena Status: {status['status']}")
            if status['status'] != 'idle':
                print(f"   Race: {status['race_id']}")
                print(f"   Elapsed: {status['elapsed']}")
                print(f"   Remaining: {status['remaining']}")
                print("\n📊 Leaderboard:")
                for entry in status.get("leaderboard", []):
                    print(f"   #{entry['rank']} {entry['color']} {entry['name']}: ${entry['pnl']:.2f}")
    
    elif args.action == "end":
        if args.race_id:
            arena.load_race(args.race_id)
        results = arena.end_race()
        if args.json:
            print(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    main()
