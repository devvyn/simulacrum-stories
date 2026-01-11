# Saltmere Chronicles - Backup Strategy

## Asset Classification

### CRITICAL: Paid Service Artifacts (Irreplaceable)

These files cost money to generate via ElevenLabs API (~$0.30/1000 chars, monthly limits).
**Must be backed up in multiple locations.**

| Path | Contents | Size | Backup Method |
|------|----------|------|---------------|
| `output/audio/saltmere/*.mp3` | Raw TTS narration (7 chapters) | ~170MB | Git LFS + External |
| `output/audio/bumpers/*.wav` | TTS intro/outro bumpers | ~42MB | Git LFS + External |
| `output/audio/bumpers-with-titles/*.wav` | TTS chapter title intros | ~12MB | Git LFS + External |

**Total paid artifacts: ~307MB**

### DERIVED: Regenerable from Sources

These can be rebuilt from paid artifacts + scripts. Ignored in git.

| Path | Contents | Regenerate With |
|------|----------|-----------------|
| `output/audio/saltmere-enhanced/` | Mixed hybrid versions | `scripts/rebuild_v9.py` |
| `site/audio/` | Deployed MP3s | Copy from enhanced |
| `output/timing/samples/` | Debug audio clips | Timing scripts |

### SOURCE: Already in Git

- Manuscript markdown files
- Production scripts (mixing, timing, deployment)
- Audio manifest and metadata
- Transition sound design elements

---

## Backup Locations

### 1. Git LFS (Primary)
- **What:** All paid TTS artifacts
- **Where:** GitHub/origin repository
- **Tracked via:** `.gitattributes`
- **Restore:** `git lfs pull`

### 2. iCloud Drive (Automatic)
- **What:** Entire project directory (partial sync)
- **Where:** ~/Documents/Code/ is iCloud-enabled
- **Limitation:** Sync can be inconsistent; not a true backup

### 3. External Backup (Manual/Scheduled)
- **What:** Paid artifacts tarball
- **Where:** Configure in `scripts/backup-audio.sh`
- **Frequency:** After any new TTS generation

---

## Backup Script Usage

```bash
# Create backup tarball of paid artifacts
./scripts/backup-audio.sh

# With custom destination
./scripts/backup-audio.sh /Volumes/ExternalDrive/saltmere-backups/

# Restore from backup
tar -xzf saltmere-paid-audio-YYYY-MM-DD.tar.gz -C output/audio/
```

---

## Recovery Procedures

### If paid artifacts are lost:

1. **Check Git LFS first:**
   ```bash
   git lfs pull
   ```

2. **Check external backup:**
   ```bash
   ls -la /path/to/backup/saltmere-paid-audio-*.tar.gz
   tar -xzf <latest>.tar.gz -C output/audio/
   ```

3. **Check iCloud:**
   - Look in ~/Library/Mobile Documents/com~apple~CloudDocs/
   - Or access via iCloud.com

4. **Last resort - regenerate:**
   - Costs ~$15-20 to regenerate all 7 chapters
   - Requires ElevenLabs API quota availability
   - Use `scripts/generate-chapter-audio.py`

### If derived files are lost:

No problem. Regenerate:
```bash
python scripts/rebuild_v9.py  # Creates enhanced mixes
cp output/audio/saltmere-enhanced/chapter-*-hybrid-v9.mp3 site/audio/
# Rename as needed for deployment
```

---

## Verification

Run periodically to ensure backups are current:

```bash
# Check Git LFS status
git lfs ls-files

# Check last backup date
ls -la /path/to/backup/saltmere-paid-audio-*.tar.gz

# Verify file integrity
md5sum output/audio/saltmere/*.mp3 > checksums.md5
md5sum -c checksums.md5
```

---

## Cost of Loss

| Asset | Replacement Cost | Time to Replace |
|-------|------------------|-----------------|
| Raw TTS (7 chapters) | ~$15-20 | 2-3 hours |
| TTS bumpers | ~$2-3 | 30 min |
| Enhanced mixes | $0 | 10 min (scripted) |
| Deployed files | $0 | 5 min (copy) |

**Protect the paid artifacts. Everything else is regenerable.**
