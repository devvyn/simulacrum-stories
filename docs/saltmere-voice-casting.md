# Saltmere Chronicles: Voice Casting

**Status**: Locked
**Date**: 2026-01-07

---

## Final Cast

| Character | Voice | Voice ID | Settings | Notes |
|-----------|-------|----------|----------|-------|
| **Narrator** | George | JBFqnCBsd6RMkjVDRZzb | Default | British = literary distance |
| **Sarah Chen** | Sarah | EXAVITQu4vr4xnSDxMaL | Default | ~29, protagonist |
| **Thomas Breck** | Bill | pqHfZKP75CvOlQylNhV4 | Default | 70, weathered fisherman |
| **Margaret Holloway** | Matilda | XrExE9yKIg1WjnnlVkGX | Default | mid-50s, harbor master |
| **Eleanor Cross** | Matilda | XrExE9yKIg1WjnnlVkGX | Cold* | 78, matriarch |
| **Edith Pemberton** | Matilda | XrExE9yKIg1WjnnlVkGX | Elderly* | 92, librarian |
| **Helen Liu** | Jessica | cgSgspJ2msm6clMCkdW9 | Default | 34, letter only |

---

## Voice Settings Differentiation

### Margaret Holloway (Default Matilda)
```python
VoiceSettings(
    stability=0.5,
    similarity_boost=0.75,
    style=0.3,
    use_speaker_boost=True
)
```
Professional, controlled, slight tension underneath.

### Eleanor Cross (Cold Matilda)
```python
VoiceSettings(
    stability=0.3,
    similarity_boost=0.8,
    style=0.1,
    use_speaker_boost=True
)
```
Lower stability = more variation. Minimal style = cold precision.

### Edith Pemberton (Elderly Matilda)
```python
VoiceSettings(
    stability=0.35,
    similarity_boost=0.7,
    style=0.4,
    use_speaker_boost=True
)
```
Warmer style, slightly less stability = elderly but sharp.

---

## Voice Map for Production

```python
VOICE_MAP = {
    "NARRATOR": {
        "voice_id": "JBFqnCBsd6RMkjVDRZzb",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}
    },
    "SARAH": {
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}
    },
    "THOMAS": {
        "voice_id": "pqHfZKP75CvOlQylNhV4",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}
    },
    "MARGARET": {
        "voice_id": "XrExE9yKIg1WjnnlVkGX",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}
    },
    "ELEANOR": {
        "voice_id": "XrExE9yKIg1WjnnlVkGX",
        "settings": {"stability": 0.3, "similarity_boost": 0.8, "style": 0.1}
    },
    "EDITH": {
        "voice_id": "XrExE9yKIg1WjnnlVkGX",
        "settings": {"stability": 0.35, "similarity_boost": 0.7, "style": 0.4}
    },
    "HELEN": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",
        "settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}
    }
}
```

---

## Production Notes

- Matilda carries Margaret, Eleanor, and Edith — differentiated by settings
- Narrator (George) is British; all characters are American
- Bill (Thomas) is the only "old" male voice — fits the weathered fisherman
- Helen appears only in Chapter 11 (letter) — Jessica's warmth fits the earnest tone

---

## Test Samples

Location: `output/audio/voice-tests/`

Listen before production to confirm.
