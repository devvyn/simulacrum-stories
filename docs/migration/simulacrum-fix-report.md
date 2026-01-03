# Simulacrum Audio Story Automation - Fixed

## Problem
Audio story production stalled after Jan 1, 2026. LaunchAgent was failing with "Operation not permitted" errors.

## Root Cause
LaunchAgent configured to use system Python (`/usr/bin/python3`) which lacks Full Disk Access permissions required to read/write files in the meta-project.

## Solution Applied
Updated `~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist` to use `uv run` instead:

**Before:**
```xml
<string>/usr/bin/python3</string>
<string>/Users/devvynmurphy/devvyn-meta-project/scripts/narrative-tools/budget-driven-scheduler.py</string>
```

**After:**
```xml
<string>/Users/devvynmurphy/.local/bin/uv</string>
<string>run</string>
<string>--directory</string>
<string>/Users/devvynmurphy/devvyn-meta-project</string>
<string>python</string>
<string>/Users/devvynmurphy/devvyn-meta-project/scripts/narrative-tools/budget-driven-scheduler.py</string>
```

## Verification
- ✅ Dry run test successful
- ✅ LaunchAgent reloaded (exit status: 0)
- ✅ Schedule confirmed: 6:00 AM and 7:30 AM daily
- ✅ Budget tracking working (9,987/150,000 chars used)

## Current Status
**System:** Operational
**Last successful run:** Jan 1, 2026 10:53 AM
**Next scheduled run:** Jan 3, 2026 6:00 AM

**Episodes in deployment:**
- Saltmere Chronicles: 7 episodes
- Millbrook Chronicles: 9 episodes

## Expected Outcome
Automation will resume tomorrow morning (Jan 3) and produce:
- 2 new episodes daily (alternating series with bias toward Millbrook)
- ~4,000 characters per episode
- Automatic deployment site updates at `~/Desktop/simulacrum-podcast-deploy/`

## Notes
- Monthly budget: 140,013 chars remaining (93.3%)
- Daily budget: 10,000 chars (resets daily)
- Provider: ElevenLabs v3 Alpha (multi-voice)
