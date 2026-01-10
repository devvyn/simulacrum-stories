#!/bin/bash
# Mix Enhanced Chapter Audio
# Combines voice narration with ambient bed and optional music

set -e

# Configuration
VOICE_DIR="output/audio/saltmere"
AMBIENT_DIR="output/audio/ambient"
MUSIC_DIR="output/audio/music"
OUTPUT_DIR="output/audio/saltmere-enhanced"

# Mix levels (in dB relative to voice at 0dB)
AMBIENT_LEVEL="-25dB"    # Background ambience, barely perceptible
MUSIC_LEVEL="-20dB"      # Music bed, present but not dominant
FADE_DURATION="3"        # Seconds for music fade in/out

usage() {
    echo "Usage: $0 <chapter-number> [options]"
    echo ""
    echo "Options:"
    echo "  --ambient <file>   Ambient bed (default: harbor-ambient.wav)"
    echo "  --music <file>     Music bed for intro/outro (optional)"
    echo "  --ambient-level    Ambient level in dB (default: -25dB)"
    echo "  --music-level      Music level in dB (default: -20dB)"
    echo "  --dry-run          Show commands without executing"
    echo ""
    echo "Example:"
    echo "  $0 01 --ambient ocean-fog.wav --music main-theme.wav"
    exit 1
}

# Parse arguments
CHAPTER=""
AMBIENT_FILE="harbor-ambient.wav"
MUSIC_FILE=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --ambient)
            AMBIENT_FILE="$2"
            shift 2
            ;;
        --music)
            MUSIC_FILE="$2"
            shift 2
            ;;
        --ambient-level)
            AMBIENT_LEVEL="$2"
            shift 2
            ;;
        --music-level)
            MUSIC_LEVEL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [[ -z "$CHAPTER" ]]; then
                CHAPTER="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$CHAPTER" ]]; then
    usage
fi

# Find voice file
VOICE_FILE=$(ls "$VOICE_DIR"/chapter-"$CHAPTER"*.mp3 2>/dev/null | head -1)
if [[ -z "$VOICE_FILE" ]]; then
    echo "Error: No voice file found for chapter $CHAPTER"
    exit 1
fi

echo "Voice file: $VOICE_FILE"

# Get voice duration
VOICE_DURATION=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VOICE_FILE")
echo "Voice duration: ${VOICE_DURATION}s"

# Prepare output directory
mkdir -p "$OUTPUT_DIR"

# Build output filename
BASENAME=$(basename "$VOICE_FILE" .mp3)
OUTPUT_FILE="$OUTPUT_DIR/${BASENAME}-enhanced.mp3"

# Check for ambient file
AMBIENT_PATH="$AMBIENT_DIR/$AMBIENT_FILE"
if [[ ! -f "$AMBIENT_PATH" ]]; then
    echo "Warning: Ambient file not found: $AMBIENT_PATH"
    echo "Available ambient files:"
    ls "$AMBIENT_DIR"/*.wav "$AMBIENT_DIR"/*.mp3 2>/dev/null || echo "  (none)"
    echo ""
    echo "Proceeding without ambient bed..."
    AMBIENT_PATH=""
fi

# Check for music file
MUSIC_PATH=""
if [[ -n "$MUSIC_FILE" ]]; then
    MUSIC_PATH="$MUSIC_DIR/$MUSIC_FILE"
    if [[ ! -f "$MUSIC_PATH" ]]; then
        echo "Warning: Music file not found: $MUSIC_PATH"
        MUSIC_PATH=""
    fi
fi

# Build ffmpeg command
build_command() {
    local CMD="ffmpeg -y"
    local FILTER=""
    local INPUT_COUNT=0

    # Input: Voice
    CMD="$CMD -i \"$VOICE_FILE\""
    INPUT_COUNT=$((INPUT_COUNT + 1))

    # Input: Ambient (if exists)
    if [[ -n "$AMBIENT_PATH" ]]; then
        CMD="$CMD -i \"$AMBIENT_PATH\""
        INPUT_COUNT=$((INPUT_COUNT + 1))
    fi

    # Input: Music (if exists)
    if [[ -n "$MUSIC_PATH" ]]; then
        CMD="$CMD -i \"$MUSIC_PATH\""
        INPUT_COUNT=$((INPUT_COUNT + 1))
    fi

    # Build filter complex
    if [[ -n "$AMBIENT_PATH" ]] || [[ -n "$MUSIC_PATH" ]]; then
        FILTER="-filter_complex \""

        # Voice stays at full volume
        FILTER="${FILTER}[0:a]volume=1.0[voice];"

        local MIX_INPUTS="[voice]"
        local FILTER_INDEX=1

        # Ambient: loop, trim to voice length, reduce volume
        if [[ -n "$AMBIENT_PATH" ]]; then
            FILTER="${FILTER}[${FILTER_INDEX}:a]aloop=loop=-1:size=2e+09,atrim=duration=${VOICE_DURATION},volume=${AMBIENT_LEVEL}[ambient];"
            MIX_INPUTS="${MIX_INPUTS}[ambient]"
            FILTER_INDEX=$((FILTER_INDEX + 1))
        fi

        # Music: fade in, play for intro, fade out at end, reduce volume
        if [[ -n "$MUSIC_PATH" ]]; then
            # Music fades in at start, loops under, fades out at end
            MUSIC_END=$(echo "$VOICE_DURATION - $FADE_DURATION" | bc)
            FILTER="${FILTER}[${FILTER_INDEX}:a]aloop=loop=-1:size=2e+09,atrim=duration=${VOICE_DURATION},"
            FILTER="${FILTER}afade=t=in:st=0:d=${FADE_DURATION},"
            FILTER="${FILTER}afade=t=out:st=${MUSIC_END}:d=${FADE_DURATION},"
            FILTER="${FILTER}volume=${MUSIC_LEVEL}[music];"
            MIX_INPUTS="${MIX_INPUTS}[music]"
            FILTER_INDEX=$((FILTER_INDEX + 1))
        fi

        # Mix all streams
        local MIX_COUNT=$(echo "$MIX_INPUTS" | grep -o '\[' | wc -l)
        FILTER="${FILTER}${MIX_INPUTS}amix=inputs=${MIX_COUNT}:duration=first:dropout_transition=2[out]\""

        CMD="$CMD $FILTER -map \"[out]\""
    fi

    # Output settings
    CMD="$CMD -codec:a libmp3lame -b:a 192k \"$OUTPUT_FILE\""

    echo "$CMD"
}

# Execute or display command
FFMPEG_CMD=$(build_command)

echo ""
echo "Output: $OUTPUT_FILE"
echo ""

if $DRY_RUN; then
    echo "Command (dry run):"
    echo "$FFMPEG_CMD"
else
    echo "Mixing..."
    eval "$FFMPEG_CMD"
    echo ""
    echo "Done: $OUTPUT_FILE"

    # Show file info
    DURATION=$(ffprobe -v quiet -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT_FILE")
    SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo "Duration: ${DURATION}s"
    echo "Size: $SIZE"
fi
