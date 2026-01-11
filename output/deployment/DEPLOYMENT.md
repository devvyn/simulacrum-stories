# Simulacrum Stories - Netlify Deployment Guide

Your podcast site is ready to deploy! This guide will get your podcasts live and accessible in Pocket Casts.

## 🚀 Quick Start (Drag & Drop - Easiest)

**First-Time Setup:**

1. **Open Netlify Drop**: https://app.netlify.com/drop

2. **Drag the folder** to the page:
   ```
   /Users/devvynmurphy/devvyn-meta-project/podcast-site
   ```

3. **Wait for deployment** (~30 seconds)

4. **Copy your site URL**:
   - Netlify will give you a URL like `https://random-name-123.netlify.app`
   - Save this URL!

5. **Update feeds with your URL**:
   ```bash
   cd ~/devvyn-meta-project/scripts/narrative-tools
   ./publish-podcasts.sh https://YOUR-ACTUAL-URL.netlify.app
   ```

6. **Drag folder again** to update with correct feed URLs

7. **Subscribe in Pocket Casts**:
   - Go to your Netlify URL in a browser
   - Click the "Pocket Casts" button for each series
   - OR manually add feed URL

**Done!** Your podcasts are live.

---

## 🔄 Daily Updates (After Automated Episode Generation)

Every morning after new episodes generate, you have 3 options:

### Option A: Manual Drag & Drop (Current Setup)

```bash
# 1. Episodes auto-generate at 6am/7:30am
# 2. Check ~/Library/Logs/simulacrum-scheduler.log for "Podcast site updated"
# 3. Drag folder to Netlify:
open https://app.netlify.com/drop
# Drag: ~/devvyn-meta-project/podcast-site
```

### Option B: Netlify CLI (Recommended for Automation)

```bash
# One-time setup:
npm install -g netlify-cli
cd ~/devvyn-meta-project/podcast-site
netlify login
netlify init

# Daily deploy (can be automated):
cd ~/devvyn-meta-project/podcast-site
netlify deploy --prod
```

### Option C: Git-Based Auto-Deploy (Fully Automated)

```bash
# One-time setup:
cd ~/devvyn-meta-project/podcast-site
git init
git add .
git commit -m "Initial podcast site"

# Push to GitHub
gh repo create simulacrum-podcasts --private
git remote add origin https://github.com/YOUR-USERNAME/simulacrum-podcasts.git
git push -u origin main

# In Netlify dashboard:
# - Connect to GitHub repo
# - Build command: (leave empty)
# - Publish directory: .
# - Enable auto-deploy on push

# Then automate daily pushes (add to LaunchAgent or cron)
```

---

## 🎯 Custom Domain (Optional)

To use `podcasts.devvyn.ca` instead of `random-name.netlify.app`:

1. **In Netlify Dashboard**:
   - Go to Site Settings → Domain management
   - Click "Add custom domain"
   - Enter: `podcasts.devvyn.ca`

2. **In your DNS** (AWS Route 53, Cloudflare, etc.):
   - Add CNAME record: `podcasts` → `YOUR-SITE.netlify.app`
   - OR A record to Netlify's IP (shown in Netlify dashboard)

3. **Update automation**:
   ```bash
   export PODCAST_NETLIFY_URL="https://podcasts.devvyn.ca"
   # Add to ~/.zshrc or ~/.bashrc for persistence
   ```

4. **Regenerate and redeploy**:
   ```bash
   cd ~/devvyn-meta-project/scripts/narrative-tools
   ./publish-podcasts.sh https://podcasts.devvyn.ca
   # Then deploy to Netlify
   ```

---

## 📊 Current Site Contents

```
podcast-site/
├── index.html                  # Beautiful landing page
├── netlify.toml                # Netlify configuration
├── feeds/
│   ├── millbrook-chronicles.xml    (9 episodes)
│   └── saltmere-chronicles.xml     (7 episodes)
└── audio/
    ├── millbrook-chronicles/
    │   ├── E01 - E09 (9 MP3s)
    │   └── cover.jpg
    └── saltmere-chronicles/
        ├── E01 - E07 (7 MP3s)
        └── cover.jpg
```

**Total Size**: ~30MB (will grow with new episodes)

---

## 🔧 Automation Integration

The system is **already configured** to auto-prepare for deployment:

### What Happens Automatically:

1. **Daily at 6am/7:30am**: LaunchAgent runs
2. **Episodes generate**: Using ElevenLabs + budget tracking
3. **Feeds regenerate**: With your Netlify URL
4. **Site updates**: Files copied to `podcast-site/`
5. **Log message**: "Podcast site updated and ready for deployment"

### What You Need to Do:

**Option 1 (Manual)**:
- Check log in morning
- Drag folder to Netlify Drop

**Option 2 (CLI - Can automate)**:
- Add to LaunchAgent after episode generation:
  ```bash
  cd ~/devvyn-meta-project/podcast-site && netlify deploy --prod
  ```

**Option 3 (Git - Fully automated)**:
- Episodes trigger git commit + push
- Netlify auto-deploys
- Zero manual work

---

## 🎧 Subscribe URLs

After deployment, your feeds will be live at:

- **Millbrook**: `https://YOUR-URL.netlify.app/feeds/millbrook-chronicles.xml`
- **Saltmere**: `https://YOUR-URL.netlify.app/feeds/saltmere-chronicles.xml`

**Add to Pocket Casts:**
1. Open Pocket Casts app
2. Tap Search/Discover
3. Tap "+" or "Add custom feed"
4. Paste feed URL
5. Subscribe!

---

## 🐛 Troubleshooting

### "Site deployed but feeds won't load in app"

**Check:**
```bash
# Test feed is valid XML:
curl https://YOUR-URL.netlify.app/feeds/millbrook-chronicles.xml

# Should see XML, not 404
```

**Fix:** Make sure you ran `publish-podcasts.sh` with the correct URL

### "Episodes not showing up"

**Possible causes:**
1. Feeds not regenerated with public URL
2. Audio files missing from site
3. Feed cached in app (wait 5 min or force refresh)

**Fix:**
```bash
cd ~/devvyn-meta-project/scripts/narrative-tools
./publish-podcasts.sh https://YOUR-ACTUAL-URL.netlify.app
# Verify files exist:
ls ~/devvyn-meta-project/podcast-site/audio/*/E*.mp3
# Redeploy
```

### "Netlify says 'No build output'"

**This is normal!** Your site is pre-built static files. Just ignore and it will deploy fine.

---

## 📈 Next Steps

After your first successful deployment:

1. **Set environment variable** for automation:
   ```bash
   echo 'export PODCAST_NETLIFY_URL="https://YOUR-URL.netlify.app"' >> ~/.zshrc
   source ~/.zshrc
   ```

2. **Choose automation level**:
   - Manual: Just drag folder when you remember
   - Semi-auto: Run `netlify deploy --prod` daily
   - Full-auto: Git push on episode generation

3. **Share your podcasts**!
   - Send feed URLs to friends
   - Add to podcast directories (optional)
   - Enjoy your daily AI audio drama

---

## 🎉 You're Ready!

Site prepared: ✅
16 episodes ready: ✅
RSS feeds generated: ✅
Netlify config: ✅

**Next**: Drag `podcast-site/` folder to https://app.netlify.com/drop

**Questions?** Check `/Users/devvynmurphy/Music/Simulacrum-Stories/PODCAST-GUIDE.md` for general podcast info.
