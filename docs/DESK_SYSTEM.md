# Trading Desk System 🏢

## Overview
When bots get promoted to **VP or higher**, they can build their own **trading desk** and hire junior traders!

## How It Works

### 1. Getting Promoted
When a bot achieves:
- **VP - Trading** (3 wins or 2 back-to-back)
- **Director** (5 wins)
- **MD** (10 wins or 5 back-to-back)
- **Partner** (15+ wins)

They automatically get a **trading desk** created for them.

### 2. Desk Benefits

| Rank | Desk Name | Junior Slots | Capital/Junior | Total Extra Capital |
|------|-----------|--------------|----------------|---------------------|
| VP | "VP Harper Global Macro" | 2 juniors | $500 each | +$1,000 |
| Director | "Director Rishi Quant Trading" | 3 juniors | $750 each | +$2,250 |
| MD | "MD Eric Breakout Strategies" | 5 juniors | $1,000 each | +$5,000 |
| Partner | "Partner Danny YOLO Ventures" | 7 juniors | $2,000 each | +$14,000 |

### 3. Junior Traders

**What are juniors?**
- Mini-versions of the leader bot
- Inherit leader's strategy with slight variations
- Trade alongside the leader
- Performance contributes to desk ranking

**Junior Naming:**
- `Harper_Jr1_4829`
- `Rishi_Jr2_9153`
- `Danny_Jr3_2741`

**Strategy Variance:**
- VPs: ±10% variance from parent strategy
- Directors: ±15% variance
- MDs: ±20% variance
- Partners: ±25% variance

This creates a "family" of similar but slightly different strategies.

### 4. Desk Competitions

**Team vs Team:**
- Desks compete for highest combined P&L
- Leader + all juniors' performance counts
- Quarterly desk rankings
- Winning desk gets bonuses for all members

**Example:**
```
🏢 Q1 DESK CHAMPIONSHIP
1. VP Harper Global Macro - $15,420 P&L
   └─ Harper: $12,000 | Jr1: $2,100 | Jr2: $1,320
   
2. Director Rishi High-Frequency - $11,890 P&L
   └─ Rishi: $9,500 | Jr1: $1,400 | Jr2: $620 | Jr3: $370
   
3. MD Eric Breakout Strategies - $8,240 P&L
   └─ Eric: $6,000 | Jr1: $1,100 | Jr2: $740 | Jr3: $200 | Jr4: $200
```

### 5. Mentorship System

**Juniors Improve Over Time:**
- Start with 1.0x performance multiplier
- Each win adds 0.05x to multiplier
- Max 1.5x multiplier (50% better than base)
- Losing trades reset multiplier slightly

**Example Progression:**
```
Harper_Jr1 starts: 1.0x multiplier
After 3 wins: 1.15x multiplier
After 5 wins: 1.25x multiplier
After being mentored by Harper for 10 races: 1.5x max
```

### 6. Career Integration

**Promotions Affect Desk:**
- VP → Director: Can hire 1 more junior
- Director → MD: Can hire 2 more juniors
- MD → Partner: Can hire 2 more juniors + rename desk

**Desk Reputation:**
- Winning desks attract better juniors
- Losing desks may lose juniors to other desks
- Top desks get first pick of new bot talent

### 7. Future Features

**Planned:**
- Junior "graduation" (promoted to their own desk)
- Inter-desk trading (juniors can switch desks)
- Desk specialties (e.g., "Crypto Desk", "Options Desk")
- Head-to-head desk battles
- Junior rebellion (juniors trade against leader!)

## Example Career Path with Desk

**Harper's Journey:**
```
Race 1: Wins! → Rookie → Associate
Race 2: Survives → Still Associate  
Race 3: Wins! → Analyst → VP - Trading
       🏢 DESK CREATED: "VP Harper Global Macro"
       💼 Can hire 2 juniors
Race 4: Hires Harper_Jr1 and Harper_Jr2
       Desk performance: Harper +$2k, Jr1 +$300, Jr2 +$150
Race 5-7: Builds desk reputation, juniors improving
Race 8: Wins again! → Director
       Desk upgraded: Now can hire 3 juniors
       Hires Harper_Jr3
Race 12: Wins 5th time total! → MD
       Desk upgraded: 5 junior slots
       Renamed: "MD Harper Alpha Strategies"
       Juniors now have 20% strategy variance
```

## Desk Commands

```bash
# View all desks
python scripts/hire_juniors.py

# Hire juniors for all desks with open slots
python scripts/hire_juniors.py hire

# Check desk leaderboard (shows after each race)
# Automatically displayed in race results
```

## Desk vs Desk Battles (Future)

**Proposed Format:**
- 2 desks enter, 1 desk leaves
- 1-hour sprint race
- All juniors + leader trade
- Combined P&L determines winner
- Losing desk loses a junior to winner

**Example:**
```
🏆 DESK BATTLE: VP Harper vs Director Rishi

Harper Desk:
- Harper: +$1,200
- Jr1: +$400  
- Jr2: +$150
Total: $1,750

Rishi Desk:
- Rishi: +$900
- Jr1: +$600
- Jr2: +$200
- Jr3: +$100
Total: $1,800

WINNER: RISHI DESK
Harper loses Jr2 to Rishi!
```

---

*The desk system turns individual competition into team warfare!*
