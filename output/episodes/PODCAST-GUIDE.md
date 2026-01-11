# Simulacrum Stories - Podcast Publishing Guide

Complete guide to accessing, publishing, and managing your AI-generated audio drama podcasts.

## 📡 System Overview

**Automatic Workflow:**
1. ✅ Daily scheduler generates new episodes (6:00 AM / 7:30 AM)
2. ✅ Episodes use ElevenLabs multi-voice TTS
3. ✅ Budget manager tracks usage (99.6% of daily quota used today!)
4. ✅ **RSS feeds auto-update after each episode generation**
5. ✅ Episodes include metadata: POV, title, duration, artwork

## 🎧 Quick Start: Listen Now

### Method 1: Local Podcast Server (Best for Daily Use)

```bash
# Start the server
~/devvyn-meta-project/scripts/narrative-tools/start-podcast-server.sh

# Server will start at: http://localhost:8000
# Visit in browser for clickable subscribe links
```

**Subscribe URLs:**
- **Millbrook**: `http://localhost:8000/feeds/millbrook-chronicles.xml`
- **Saltmere**: `http://localhost:8000/feeds/saltmere-chronicles.xml`

**Podcast Apps:**
- **Pocket Casts**: Copy feed URL, go to Settings → Add Podcast → Custom RSS
- **Apple Podcasts**: File → Add a Show by URL → Paste feed URL
- **Overcast**: Add URL from settings
- **Any podcast app**: Supports standard RSS feed URLs

### Method 2: Direct File Access

Episodes stored at:
```
~/Music/Simulacrum-Stories/Millbrook Chronicles/
~/Music/Simulacrum-Stories/Saltmere Chronicles/
```

Add this folder to Apple Music/iTunes for automatic sync to devices.

## 📊 Current Status (2026-01-01)

**Millbrook Chronicles:**
- 9 episodes published
- Latest: E09 "The Weight of Truth" (2m 31s)
- POV rotation: Sheriff Frank, Margaret, Old Pete, Jack
- Feed: http://localhost:8000/feeds/millbrook-chronicles.xml

**Saltmere Chronicles:**
- 7 episodes published
- Latest: E07 "The Weight of Truth" (2m 58s)
- POV rotation: Sarah, Margaret, Thomas, Eleanor
- Feed: http://localhost:8000/feeds/saltmere-chronicles.xml

## 🔄 Automatic Updates

**Daily Generation Schedule:**
- 6:00 AM: First generation attempt
- 7:30 AM: Second generation attempt (if needed)

**Feed Auto-Update:**
RSS feeds regenerate automatically after each episode is produced. No manual intervention needed!

**Budget Management:**
- Daily quota: 10,000 chars (resets at midnight)
- Monthly quota: 150,000 chars
- Today's usage: 9,959/10,000 (99.6%) ✅

## 🛠️ Manual Operations

### Check System Status
```bash
~/devvyn-meta-project/scripts/narrative-tools/simulacrum-status.sh
```

Shows:
- Budget usage (daily/monthly)
- Episode counts
- Feed status
- Automation schedule
- Recent activity

### Generate Episode Now
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 budget-driven-scheduler.py
```

Automatically:
- Checks budget availability
- Selects stale series
- Generates episode with real relationship signals
- Updates RSS feed
- Logs all activity

### Manually Regenerate Feeds
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 podcast_feed.py --all --base-url http://localhost:8000
```

Use when:
- Feed files get corrupted
- Want to change base URL
- Testing feed configuration

### Dry Run (Test Without Generating)
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 budget-driven-scheduler.py --dry-run
```

Shows what would happen without actually generating episodes.

## 🎨 Episode Quality

**Audio Features:**
- Multi-voice narration (ElevenLabs V3)
- Character-specific voices with emotional tones
- POV-based narration (internal perspective)
- Real iMessage relationship signals for emotional depth

**Metadata:**
- Title, episode number, season
- POV character information
- Duration, file size
- Publication date
- Cover artwork
- Episode descriptions

**Target Length:**
- New episodes: 15-20 minutes (max_tokens increased to 5000)
- Current episodes: 2-3 minutes (will improve with next generation)

## 🌐 Remote Publishing (Future)

To make feeds publicly accessible:

### Option A: Tunnel Service (Cloudflare, ngrok)
```bash
# Example with ngrok
ngrok http 8000

# Update feeds with public URL
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 podcast_feed.py --all --base-url https://YOUR-NGROK-URL
```

### Option B: Web Hosting
1. Upload episodes + feeds to web server
2. Regenerate feeds with public URL:
   ```bash
   python3 podcast_feed.py --all --base-url https://your-domain.com
   ```
3. Share feed URLs publicly

### Option C: Cloud Storage (S3, R2)
1. Set up bucket with public read access
2. Upload audio files and feeds
3. Configure CloudFront/CDN
4. Regenerate feeds with CDN URL

## 📋 Feed Specifications

**RSS 2.0 Compliant** with:
- iTunes podcast tags
- Atom self-link
- Proper enclosures (audio URLs)
- Episode metadata (number, season, type)
- Category: Fiction → Drama
- Language: en-us
- Explicit: No

**Compatible With:**
- Apple Podcasts
- Spotify (via RSS)
- Pocket Casts
- Overcast
- Castro
- Podcast Addict
- Any RSS-compatible podcast app

## 🐛 Troubleshooting

### "No episodes showing in feed"
```bash
# Regenerate feeds
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 podcast_feed.py --all --base-url http://localhost:8000
```

### "Podcast server won't start"
```bash
# Check if port 8000 is in use
lsof -i :8000

# Try different port
~/devvyn-meta-project/scripts/narrative-tools/start-podcast-server.sh 8080
```

### "Episodes not generating"
```bash
# Check budget status
python3 ~/devvyn-meta-project/scripts/audio_budget_manager.py status

# Check scheduler logs
tail -f ~/Library/Logs/simulacrum-scheduler.log

# Verify LaunchAgent is running
launchctl list | grep simulacrum
```

### "Feed won't load in podcast app"
- Ensure server is running: `http://localhost:8000`
- Check feed file exists: `ls ~/Music/Simulacrum-Stories/_feeds/`
- Verify feed URL is correct (no typos)
- Some apps require public URLs (not localhost)

## 📈 Future Enhancements

**Planned:**
- [ ] Longer episodes (15-20 min) with increased max_tokens
- [ ] Custom cover artwork per series
- [ ] Enhanced episode descriptions from scene summaries
- [ ] Season transitions with recap episodes
- [ ] Cross-series story connections
- [ ] Character voice consistency tracking

**In Progress:**
- [x] Budget-driven automation ✅
- [x] Multi-voice narration ✅
- [x] Real relationship signal integration ✅
- [x] Automatic RSS feed updates ✅
- [x] Extended episode templates (testing length optimization)

## 🎯 Quick Reference

| Task | Command |
|------|---------|
| Start server | `~/devvyn-meta-project/scripts/narrative-tools/start-podcast-server.sh` |
| Check status | `~/devvyn-meta-project/scripts/narrative-tools/simulacrum-status.sh` |
| Generate now | `cd ~/devvyn-meta-project/scripts/narrative-tools && python3 budget-driven-scheduler.py` |
| View logs | `tail -f ~/Library/Logs/simulacrum-scheduler.log` |
| Budget status | `python3 ~/devvyn-meta-project/scripts/audio_budget_manager.py status` |
| Regenerate feeds | `cd ~/devvyn-meta-project/scripts/narrative-tools && python3 podcast_feed.py --all` |

---

**System:** Simulacrum Stories Budget-Driven Production
**Updated:** 2026-01-01
**Status:** ✅ Fully Operational
