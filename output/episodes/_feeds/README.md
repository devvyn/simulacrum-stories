# Simulacrum Stories Podcast Feeds

Auto-generated RSS feeds for podcast consumption.

## 📡 Available Feeds

### Millbrook Chronicles
- **Episodes**: 9
- **Feed**: `http://localhost:8000/feeds/millbrook-chronicles.xml`
- **Local file**: `~/Music/Simulacrum-Stories/_feeds/millbrook-chronicles.xml`

### Saltmere Chronicles
- **Episodes**: 7
- **Feed**: `http://localhost:8000/feeds/saltmere-chronicles.xml`
- **Local file**: `~/Music/Simulacrum-Stories/_feeds/saltmere-chronicles.xml`

## 🎧 How to Listen

### Option 1: Local Podcast Server (Recommended)

Start the local server:
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 podcast_feed.py --serve --port 8000
```

Then subscribe in your podcast app:
- **Pocket Casts**: `pktc://subscribe/http://localhost:8000/feeds/millbrook-chronicles.xml`
- **Apple Podcasts**: Add feed URL manually in the app
- **Overcast**: Add custom feed URL
- **Web**: Visit `http://localhost:8000` for clickable subscribe links

### Option 2: File-Based Access

Episodes are stored at:
- Millbrook: `~/Music/Simulacrum-Stories/Millbrook Chronicles/`
- Saltmere: `~/Music/Simulacrum-Stories/Saltmere Chronicles/`

### Option 3: Remote Server (Future)

To make feeds publicly accessible:
1. Set up a web server with public URL
2. Regenerate feeds with that URL:
   ```bash
   cd ~/devvyn-meta-project/scripts/narrative-tools
   python3 podcast_feed.py --all --base-url https://your-domain.com
   ```

## 🔄 Auto-Update

Feeds are automatically regenerated when:
- New episodes are produced by the daily scheduler
- Manual generation via `budget-driven-scheduler.py`

## 📝 Manual Feed Regeneration

```bash
# Regenerate all feeds
cd ~/devvyn-meta-project/scripts/narrative-tools
python3 podcast_feed.py --all --base-url http://localhost:8000

# Regenerate specific series
python3 podcast_feed.py --series millbrook --base-url http://localhost:8000
```

## 📊 Feed Metadata

Each episode includes:
- Title, description, duration
- POV character information
- Episode/season numbers
- Publication date
- High-quality MP3 audio (ElevenLabs multi-voice)
- Cover artwork

## 🎨 Cover Artwork

Default artwork is auto-generated per series. To customize:
1. Create `cover.jpg` in the series directory
2. Regenerate the feed
3. Artwork will be automatically included

---

**Generated**: 2026-01-01
**System**: Simulacrum Stories Budget-Driven Production
