# Simulacrum Stories: Budget-Driven Automation System

**Deployed:** 2025-12-31
**Status:** ✅ Active and running

## Overview

Your Simulacrum Stories podcasts are now fully automated with budget-driven scheduling. The system will automatically generate new episodes every morning (6-8am) based on available ElevenLabs quota, ensuring optimal utilization without waste.

## What Was Built

### 1. Series Initialization
- **Millbrook Chronicles**: 4 episodes, 1980s small-town mystery
- **Saltmere Chronicles**: 3 episodes, 1970s coastal secrets
- World files created with characters, themes, and narrative arcs
- Series registry tracks episode count and staleness

### 2. Budget-Driven Scheduler
**Location:** `~/devvyn-meta-project/scripts/narrative-tools/budget-driven-scheduler.py`

**Intelligence:**
- Checks budget before generating (daily/monthly limits)
- Estimates 1-2 episodes per day based on available quota
- Selects stale series first (budget-weighted mix)
- Queues episodes if budget insufficient
- Logs all activity to `~/Library/Logs/simulacrum-scheduler.log`

**Budget Targets:**
- Daily: 3k-6k chars (1-2 episodes)
- Monthly: 120k-140k chars (30-35 episodes)
- Current utilization: **0%** (ready to scale up)

### 3. Daily Automation (LaunchAgent)
**Service:** `ca.devvyn.simulacrum-daily`
**Schedule:** Daily at 6:00 AM and 7:30 AM
**Status:** ✅ Loaded and active

The system will run automatically every morning. Episodes will be ready when you wake up.

### 4. Status Dashboard
**Command:** `~/devvyn-meta-project/scripts/narrative-tools/simulacrum-status.sh`

**Shows:**
- Current budget utilization (daily/monthly)
- Series health (episodes, staleness)
- Automation status
- Recent generation activity
- Quick command reference

## How It Works

### Daily Workflow (Automatic)

**6:00 AM:**
1. Scheduler wakes up
2. Checks ElevenLabs budget (10k daily quota)
3. Estimates how many episodes possible (typically 1-2)
4. Selects most stale series (Millbrook or Saltmere)
5. Generates episode(s) using daily_production.py
6. Updates RSS feeds
7. Records usage
8. Logs results

**Result:** Fresh episodes waiting in `~/Music/Simulacrum-Stories/` when you wake up.

### Budget Optimization

The system targets **85-93% utilization** of your monthly budget:

| Metric | Target | Current |
|--------|--------|---------|
| Monthly chars | 120k-140k / 150k | 0 / 150k (0%) |
| Daily chars | 3k-6k / 10k | 0 / 10k (0%) |
| Episodes/week | 7-10 | 0 (ready to start) |
| Episodes/month | 30-35 | 7 (backlog) |

**You're currently severely underutilizing.** The automation will fix this starting tomorrow morning.

## Manual Control

### Check Status
```bash
~/devvyn-meta-project/scripts/narrative-tools/simulacrum-status.sh
```

### Generate Now (Manual Override)
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
./budget-driven-scheduler.py          # Generate if budget allows
./budget-driven-scheduler.py --force  # Generate regardless of budget
```

### Test Without Generating
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
./budget-driven-scheduler.py --dry-run --verbose
```

### View Logs
```bash
tail -f ~/Library/Logs/simulacrum-scheduler.log
```

### Pause Automation
```bash
launchctl unload ~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist
```

### Resume Automation
```bash
launchctl load ~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist
```

## Budget Management

The system uses the existing audio-budget-manager.py:

```bash
# Check budget
~/devvyn-meta-project/scripts/audio_budget_manager.py status

# View provider details
~/devvyn-meta-project/scripts/audio_budget_manager.py --help
```

**Current plan:**
- ElevenLabs V3 Alpha
- 150k chars/month ($5/month)
- 80% discount until June 2025
- **Best value available**

## File Locations

### Configuration
- Series registry: `~/devvyn-meta-project/data/simulacrum-series.json`
- World files: `~/devvyn-meta-project/data/worlds/*.json`
- Budget config: `~/devvyn-meta-project/config/audio-budget.json`

### Scripts
- Scheduler: `~/devvyn-meta-project/scripts/narrative-tools/budget-driven-scheduler.py`
- Status: `~/devvyn-meta-project/scripts/narrative-tools/simulacrum-status.sh`
- Episode generator: `~/devvyn-meta-project/scripts/narrative-tools/daily_production.py`

### Output
- Episodes: `~/Music/Simulacrum-Stories/*/E##-*.mp3`
- RSS feeds: `~/Music/Simulacrum-Stories/_feeds/*.xml`
- Logs: `~/Library/Logs/simulacrum-scheduler.log`

### LaunchAgent
- Config: `~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist`

## Expected Results

### Week 1 (Starting Tomorrow)
- 7-10 new episodes generated
- Both series progress (3-5 episodes each)
- Budget utilization: 40-60%

### Week 2+
- Steady state: 1-2 episodes per day
- Automatic series balancing
- Budget utilization: 85-93%
- Episodes always fresh (< 2 days old)

## Troubleshooting

### "No episodes being generated"
1. Check scheduler log: `tail ~/Library/Logs/simulacrum-scheduler.log`
2. Check LaunchAgent: `launchctl list | grep simulacrum`
3. Run manually: `cd ~/devvyn-meta-project/scripts/narrative-tools && ./budget-driven-scheduler.py --verbose`

### "Budget exceeded"
The system prevents this automatically. If you hit limits:
1. Check status: `~/devvyn-meta-project/scripts/audio_budget_manager.py status`
2. Episodes will queue for next day automatically
3. Monthly reset happens automatically on the 1st

### "Series not balancing"
The algorithm prioritizes staleness. If one series is more stale, it gets multiple episodes until balanced. This is correct behavior.

### "Want to generate more episodes"
Upgrade your ElevenLabs plan or adjust thresholds in the scheduler:
```python
# In budget-driven-scheduler.py
EPISODE_ESTIMATE_CHARS = 4000  # Reduce to fit more episodes
DAILY_TARGET_EPISODES = 3      # Increase target
```

## Next Steps

1. **Tomorrow morning:** Check for new episodes in `~/Music/Simulacrum-Stories/`
2. **End of week:** Run status dashboard to see utilization
3. **Month 1:** Monitor and tune budget thresholds if needed
4. **Enjoy:** Your podcast backlog now grows automatically while you sleep

## Success Metrics

✅ Automation deployed and active
✅ Budget system integrated
✅ Two series initialized
⏳ First automated generation: Tomorrow 6:00 AM
⏳ Target utilization: 85-93% (currently 0%)
⏳ Stale content eliminated: Episodes always < 2 days old

---

**Summary:** You went from manual generation (0% utilization, 7-day stale content) to fully automated, budget-optimized daily production. Starting tomorrow, you'll have fresh episodes every morning, using nearly your full ElevenLabs quota efficiently.

The system makes optimal use of both ElevenLabs and Claude Code without waste or hitting limits.
