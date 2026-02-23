# Trading Arena - Career Progression System 🏆

## Overview
Bots now have **careers**! They earn titles, achievements, and can become VPs who lead teams of junior traders.

## Rank Progression

| Title | Requirement | Benefits |
|-------|-------------|----------|
| 🌱 **Rookie** | Complete 1st race | None |
| 📊 **Analyst** | Survive 3 races | None |
| 💼 **Associate** | Win 1 race | Recognition |
| ⭐ **VP - Trading** | Win 3 races OR 2 back-to-back | +$500 capital, 2 team members, 10% strategy boost |
| 🌟 **Director** | Win 5 races | +$1000 capital, 3 team members, 20% strategy boost |
| 👔 **MD** | Win 10 races OR 5 back-to-back | +$2000 capital, 5 team members, 30% boost, market influence |
| 🏛️ **Partner** | Win 15+ races | Legendary status, max benefits |

## Achievements

### Profit Milestones 💰
- **First Blood** 🩸 - Made first profitable trade
- **Double Digit** 📈 - 10%+ profit in a race
- **Quarter Master** 💰 - 25%+ profit in a race
- **Halfway Hero** 🚀 - 50%+ profit in a race
- **Centurion** 👑 - 100%+ profit (doubled money)

### Race Performance 🏁
- **Survivor** 🏆 - Survived elimination
- **Champion** 🥇 - Won a race
- **Unstoppable** 🔥 - Won 2 races in a row
- **Phoenix** 🐦‍🔥 - Won after being in last place
- **Underdog** 🎯 - Won while in bottom 3 mid-race

### Trading Style ⚡
- **Volume King** ⚡ - Most trades in a race
- **Sniper** 🎯 - 90%+ win rate (min 5 trades)
- **YOLO God** 🎲 - Won with 20x leverage
- **Comeback Kid** 📈 - Recovered from -10% to win
- **Diamond Hands** 💎 - Held through 20% drawdown to profit

## How It Works

1. **After Each Race:**
   - Career stats updated (wins, survivals, eliminations)
   - New achievements checked and awarded
   - Rank progression evaluated
   - VP benefits activated if promoted

2. **Career Tracker:**
   - Stored in `careers/career_tracker.json`
   - Persistent across all races
   - Tracks best/worst performance, total P&L, rank history

3. **VP Benefits:**
   - Extra starting capital in future races
   - Can recruit "junior traders" (new bots with similar strategy)
   - Strategy parameter boosts (better entries, tighter stops)
   - Elimination immunity (1-3 per race depending on rank)

## Career Leaderboard

Top performers ranked by:
- Wins × 100 points
- Survivals × 10 points
- Achievements × 5 points
- Consecutive wins × 50 points

## Example Career Path

**Harper's Journey:**
1. Race 1: Wins! → Rookie → Associate
2. Race 2: Survives → Still Associate
3. Race 3: Wins! → Analyst → VP - Trading
4. Race 4-5: Leads team of 2 juniors, +$500 capital
5. Race 6: Wins! → Director → +$1000 capital, 3 team members

**Danny's Journey:**
1. Race 1-2: Eliminated both times → Still Rookie
2. Race 3: Survives! → Still Rookie but proud
3. Race 4: Wins with YOLO strategy! → YOLO God achievement + Associate
4. Race 5: Wins again! → VP - Trading

## Future Enhancements

- **Mentorship:** VPs can "train" juniors, improving their strategies
- **Team Competitions:** VP-led teams compete against each other
- **Legacy Mode:** Retired bots become "legends" that influence future generations
- **Rivalries:** Track head-to-head records between specific bots

---

*Career progression adds long-term stakes to the arena - it's not just about one race, it's about building a legacy!*
