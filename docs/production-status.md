# Saltmere Chronicles: Production Status

**Updated:** 2026-01-10

---

## Core Assets

### Manuscript
| Item | Status | Location |
|------|--------|----------|
| Chapter 1-12 | Complete | `manuscript/saltmere/` |
| Vignette A (Thomas) | Complete | `manuscript/saltmere/` |
| Vignette B (Eleanor) | Complete | `manuscript/saltmere/` |
| Vignette C (Helen's Letter) | Complete | `manuscript/saltmere/` |

**Word count:** ~25,000

---

### Audio - Voice Narration
| Chapter | Status | File |
|---------|--------|------|
| 1 - The Research Station | Generated | `chapter-01-the-research-station.mp3` |
| 2 - The Harbor Master | Generated | `chapter-02-the-harbor-master.mp3` |
| 3 - First Samples | Generated | `chapter-03-first-samples.mp3` |
| 4 - The Librarian's Archive | Generated | `chapter-04-the-librarians-archive.mp3` |
| 5 - The Waterfront Discovery | Generated | `chapter-05-the-waterfront-discovery.mp3` |
| 6 - The Weight of Truth | Generated | `chapter-06-the-weight-of-truth.mp3` |
| 7 - Eleanor's Warning | Generated | `chapter-07-eleanors-warning.mp3` |
| 8 - The Old Cannery | Pending | Awaiting ElevenLabs reset |
| 9 - The Confrontation | Pending | Awaiting ElevenLabs reset |
| 10 - The Choice | Pending | Awaiting ElevenLabs reset |
| 11 - What Surfaces | Pending | Awaiting ElevenLabs reset |
| 12 - The Tide Goes Out | Pending | Awaiting ElevenLabs reset |
| Vignette A | Pending | Awaiting ElevenLabs reset |
| Vignette B | Pending | Awaiting ElevenLabs reset |
| Vignette C | Pending | Awaiting ElevenLabs reset |

**Generated:** ~75 minutes (~85,000 characters)
**Remaining:** ~68 minutes (~70,000 characters)
**ElevenLabs reset:** Next billing cycle

---

### Audio - Music Beds
| Track | Status | Suno Prompt Ready |
|-------|--------|-------------------|
| Main Theme | Not generated | Yes |
| Tension Bed | Not generated | Yes |
| Resolution Theme | Not generated | Yes |
| Arrival | Not generated | Yes |
| The Harbor | Not generated | Yes |
| Eleanor's Store | Not generated | Yes |
| The Library | Not generated | Yes |
| Deep Channel | Not generated | Yes |
| The Cannery | Not generated | Yes |
| Confrontation | Not generated | Yes |
| Helen's Theme | Not generated | Yes |
| Transition Sting | Not generated | Yes |

**Prompts file:** `docs/saltmere-suno-prompts.md`

---

### Audio - Ambient Beds
| Sound | Status | Source |
|-------|--------|--------|
| Harbor ambience | Not downloaded | Freesound |
| Ocean/fog | Not downloaded | Freesound |
| Rain on windows | Not downloaded | Freesound |
| Foghorn | Not downloaded | Freesound |

**Freesound client:** `~/devvyn-meta-project/tools/freesound/freesound-client.py`
**Target directory:** `output/audio/ambient/`

---

## Companion Materials

| Document | Status | Location |
|----------|--------|----------|
| Helen Liu's Research Notes | Complete | `docs/companion-helen-liu-research-notes.md` |
| Saltmere Map | Complete | `docs/companion-saltmere-map.md` |
| Voice Casting | Complete | `docs/saltmere-voice-casting.md` |
| Story Bible | Complete | `docs/saltmere-story-bible.md` |
| Character Chat Prompts | Complete | `docs/saltmere-character-prompts.md` |
| Suno Music Prompts | Complete | `docs/saltmere-suno-prompts.md` |
| Tabletop RPG Scenario | Complete | `docs/saltmere-tabletop-scenario.md` |

---

## Web Presence

| Item | Status | Location |
|------|--------|----------|
| Landing Page HTML | Complete (structure) | `site/index.html` |
| Fog effect CSS | Complete | Inline in `site/index.html` |
| Audio toggle JS | Complete | Inline in `site/index.html` |
| Open Graph images | Not created | Needed for social sharing |
| Podcast RSS feed | Existing (from prior work) | Netlify |
| Investigation Board | Not started | Planned interactive feature |

---

## Production Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `generate-chapter-audio.py` | ElevenLabs TTS generation | Complete |
| `mix-enhanced-chapter.sh` | Combine voice + ambient + music | Complete |

---

## Immediate Next Steps

### When Suno Available
1. Generate main theme from prompt
2. Generate tension bed from prompt
3. Generate resolution theme from prompt
4. Download and select best takes

### When Freesound Ready
1. Search: `harbor ambient ocean dock`
2. Search: `pacific northwest fog coast`
3. Search: `foghorn distant`
4. Search: `rain window interior`
5. Download CC0 options to `output/audio/ambient/`

### When Assets Ready
1. Run `./scripts/mix-enhanced-chapter.sh 01 --ambient harbor-ambient.wav --music main-theme.wav`
2. Review mix levels
3. Adjust and re-mix as needed
4. Create enhanced versions of chapters 2-7

### When ElevenLabs Resets
1. Generate chapters 8-12
2. Generate vignettes A, B, C
3. Create enhanced versions

### Web Launch
1. Add OG images
2. Embed Chapter 1 player
3. Link podcast feeds
4. Deploy to Netlify
5. Test across devices

---

## Budget Tracking

### ElevenLabs (Creator Plan)
- Monthly limit: 100,000 characters
- Used this cycle: ~85,000 characters
- Remaining: ~15,000 characters (not enough for Chapter 8+)
- Reset: Next billing cycle

### Suno (Pro Plan)
- Monthly credits: 500
- Estimated need: ~42 generations (420 credits)
- Sufficient for all music beds in one cycle

---

## File Structure

```
simulacrum-stories/
├── manuscript/
│   └── saltmere/
│       ├── chapter-01-the-research-station.md
│       ├── ... (12 chapters + 3 vignettes)
│       └── vignette-c-helens-letter.md
├── output/
│   └── audio/
│       ├── saltmere/           # Voice-only chapters
│       ├── saltmere-enhanced/  # Mixed with ambient/music
│       ├── ambient/            # Freesound downloads
│       ├── music/              # Suno generations
│       └── voice-tests/        # Character voice samples
├── site/
│   └── index.html              # Landing page
├── scripts/
│   ├── generate-chapter-audio.py
│   └── mix-enhanced-chapter.sh
└── docs/
    ├── saltmere-story-bible.md
    ├── saltmere-voice-casting.md
    ├── saltmere-character-prompts.md
    ├── saltmere-suno-prompts.md
    ├── saltmere-tabletop-scenario.md
    ├── companion-helen-liu-research-notes.md
    ├── companion-saltmere-map.md
    └── production-status.md    # This file
```
