# Episode Regeneration Queue

Episodes with duplicate or problematic titles that should be regenerated.

## Priority 1: Duplicate "The Weight of Truth"

**Millbrook Chronicles:**
- E03 - The Weight of Truth ❌ (duplicate)
- E05 - The Weight of Truth ❌ (duplicate)
- E07 - The Weight of Truth ❌ (duplicate)
- E09 - The Weight of Truth ❌ (duplicate)

**Saltmere Chronicles:**
- E07 - The Weight of Truth ❌ (cross-series duplicate)

## Priority 2: Overused Pattern "The Weight of..."

While not exact duplicates, these follow a repetitive pattern:
- Saltmere E01 - The Weight of Watching
- Saltmere E03 - The Weight of Old Sins
- Saltmere E04 - The Weight of Nets
- Saltmere E05 - The Weight of Secrets ⚠️ (also exists as Millbrook E08)
- Millbrook E08 - The Weight of Secrets ⚠️

## Priority 3: Missing Episode

- Millbrook E04 - **MISSING** (sequence gap: E00, E01, E02, E03, E05...)

## Regeneration Strategy

### Immediate (Manual)
Episodes E03, E05, E07 for Millbrook should be regenerated with unique titles that:
- Reflect the actual episode content (POV character's story)
- Follow series themes without repeating "Weight of..." pattern
- Use character-specific or mystery-specific naming

### Automated (Future)
- Tomorrow's scheduler run (6-7:30am) will use improved templates with emphatic length requirements
- Future episodes will have more varied title generation
- Consider adding title uniqueness check to episode generator

## Title Suggestions (Manual Regeneration)

Based on POV rotation pattern:

**Millbrook Chronicles:**
- E03 (POV: Old Pete) → "Ashes and Memory" or "The Mill Fire's Witness"
- E05 (POV: Jack Morrison) → "The Newcomer's Burden" or "Traces of the Past"
- E07 (POV: Old Pete) → "Silence and Smoke" or "What Pete Knows"
- E09 (POV: Jack) → Keep "The Weight of Truth" (finale connotation acceptable)

**Saltmere Chronicles:**
- E07 (POV: Thomas Breck) → "Nets and Secrets" or "What the Bay Remembers"

**Millbrook E08** (POV: Old Pete) → "The Keeper's Confession" or "Pete's Testament"

## Implementation

When regenerating:
1. Delete old MP3 file
2. Regenerate episode with new title in scene metadata
3. Update RSS feed
4. Sync to S3
5. Test in Pocket Casts to verify update

## Notes

- Current episodes are SHORT (2-3 min) due to token limit issue - NOW FIXED
- Tomorrow's new episodes should be 15-20 min (2,250-3,000 words)
- Budget reset at midnight allows regeneration of ~3 episodes per day
- Prioritize the 4 Millbrook duplicates first
