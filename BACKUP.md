# Saltmere Chronicles - Backup Strategy

## Asset Classification

### CRITICAL: Paid Service Artifacts (Irreplaceable)

These files cost money to generate via ElevenLabs API (~$0.30/1000 chars, monthly limits).

| Path | Contents | Size |
|------|----------|------|
| `output/audio/saltmere/*.mp3` | Raw TTS narration (7 chapters) | ~170MB |
| `output/audio/bumpers/*.wav` | TTS intro/outro bumpers | ~42MB |
| `output/audio/bumpers-with-titles/*.wav` | TTS chapter title intros | ~12MB |

**Total paid artifacts: ~307MB**

### DERIVED: Regenerable from Sources

These can be rebuilt from paid artifacts + scripts. Ignored in git.

| Path | Contents | Regenerate With |
|------|----------|-----------------|
| `output/audio/saltmere-enhanced/` | Mixed hybrid versions | `scripts/rebuild_v9.py` |
| `site/audio/` | Deployed MP3s | Copy from enhanced |

---

## Backup Locations

### 1. Git LFS (Primary)
- **What:** All paid TTS artifacts
- **Where:** GitHub repository
- **Restore:** `git lfs pull`

### 2. iCloud Drive (Automatic)
- **What:** Entire ~/Documents/Code/ directory
- **Where:** Apple iCloud
- **Restore:** Re-download from iCloud

---

## Recovery Procedures

### If paid artifacts are missing after clone:

```bash
git lfs pull
```

### If repository is lost:

1. Clone from GitHub (includes LFS pointers)
2. Run `git lfs pull` to fetch actual audio files

### If both GitHub and local are lost:

Regenerate from ElevenLabs:
- Cost: ~$15-20 for all 7 chapters
- Time: 2-3 hours
- Requires API quota availability

---

## Cost of Loss

| Asset | Replacement Cost | Time to Replace |
|-------|------------------|-----------------|
| Raw TTS (7 chapters) | ~$15-20 | 2-3 hours |
| TTS bumpers | ~$2-3 | 30 min |
| Enhanced mixes | $0 | 10 min (scripted) |
