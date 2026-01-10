#!/bin/bash
# Generate Chapter Bumpers for Saltmere Chronicles
# Creates intro and outro bumpers using main theme + ambient

set -e

# Paths
MUSIC_DIR="$HOME/Music/Suno/Saltmere-Pallette"
AMBIENT_DIR="$HOME/Music/Freesound/Saltmere-Ambient"
OUTPUT_DIR="output/audio/bumpers"
MAIN_THEME="$MUSIC_DIR/1. Saltmere Main - Fog and Secrets.wav"
HARBOR_AMBIENT="$AMBIENT_DIR/254125-Harbor Ambience 1.wav"

# Durations
INTRO_MUSIC_DUR=12      # Main theme intro duration
OUTRO_STING_DUR=6       # Main theme outro sting
FADE_DUR=3              # Fade in/out duration
AMBIENT_BED_DUR=5       # Ambient bed after intro music

# Levels (dB)
MUSIC_LEVEL="-3dB"
AMBIENT_LEVEL="-18dB"

usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --chapter N     Generate bumpers for specific chapter (01-12)"
    echo "  --all           Generate bumpers for all chapters"
    echo "  --intro-only    Generate only intro bumpers"
    echo "  --outro-only    Generate only outro bumpers"
    echo "  --dry-run       Show commands without executing"
    echo ""
    echo "Example:"
    echo "  $0 --chapter 01"
    echo "  $0 --all"
    exit 1
}

# Chapter metadata
get_chapter_title() {
    case $1 in
        01) echo "The Research Station" ;;
        02) echo "The Harbor Master" ;;
        03) echo "First Samples" ;;
        04) echo "The Librarian's Archive" ;;
        05) echo "The Waterfront Discovery" ;;
        06) echo "The Weight of Truth" ;;
        07) echo "Eleanor's Warning" ;;
        08) echo "The Old Cannery" ;;
        09) echo "The Reckoning" ;;
        10) echo "What Rises" ;;
        11) echo "What Surfaces" ;;
        12) echo "The Tide Goes Out" ;;
        *) echo "Unknown" ;;
    esac
}

generate_intro_bumper() {
    local chapter_num=$1
    local chapter_title=$(get_chapter_title "$chapter_num")
    local output_file="$OUTPUT_DIR/intro-chapter-${chapter_num}.wav"

    echo "Generating intro bumper for Chapter $chapter_num: $chapter_title"

    # Intro structure:
    # 1. Main theme (12s, fade in 3s, fade out last 3s)
    # 2. Crossfade to ambient bed (5s, fading down)
    # Total: ~15s

    ffmpeg -y \
        -i "$MAIN_THEME" \
        -i "$HARBOR_AMBIENT" \
        -filter_complex "
            [0:a]atrim=0:${INTRO_MUSIC_DUR},
                 afade=t=in:st=0:d=${FADE_DUR},
                 afade=t=out:st=$((INTRO_MUSIC_DUR - FADE_DUR)):d=${FADE_DUR},
                 volume=${MUSIC_LEVEL}[music];
            [1:a]atrim=0:${AMBIENT_BED_DUR},
                 afade=t=in:st=0:d=2,
                 afade=t=out:st=$((AMBIENT_BED_DUR - 2)):d=2,
                 volume=${AMBIENT_LEVEL},
                 adelay=$((INTRO_MUSIC_DUR * 1000 - 2000))|$((INTRO_MUSIC_DUR * 1000 - 2000))[ambient];
            [music][ambient]amix=inputs=2:duration=longest:normalize=0[out]
        " \
        -map "[out]" \
        -c:a pcm_s16le \
        "$output_file" 2>/dev/null

    echo "  Created: $output_file"
}

generate_outro_bumper() {
    local chapter_num=$1
    local output_file="$OUTPUT_DIR/outro-chapter-${chapter_num}.wav"

    echo "Generating outro bumper for Chapter $chapter_num"

    # Outro structure:
    # 1. Ambient swell (3s)
    # 2. Main theme sting (6s, fade out)
    # Total: ~8s

    ffmpeg -y \
        -i "$HARBOR_AMBIENT" \
        -i "$MAIN_THEME" \
        -filter_complex "
            [0:a]atrim=0:4,
                 afade=t=in:st=0:d=2,
                 afade=t=out:st=2:d=2,
                 volume=-12dB[ambient];
            [1:a]atrim=0:${OUTRO_STING_DUR},
                 afade=t=in:st=0:d=1,
                 afade=t=out:st=$((OUTRO_STING_DUR - 2)):d=2,
                 volume=${MUSIC_LEVEL},
                 adelay=2000|2000[music];
            [ambient][music]amix=inputs=2:duration=longest:normalize=0[out]
        " \
        -map "[out]" \
        -c:a pcm_s16le \
        "$output_file" 2>/dev/null

    echo "  Created: $output_file"
}

# Parse arguments
CHAPTER=""
ALL=false
INTRO_ONLY=false
OUTRO_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --chapter)
            CHAPTER=$(printf "%02d" "$2")
            shift 2
            ;;
        --all)
            ALL=true
            shift
            ;;
        --intro-only)
            INTRO_ONLY=true
            shift
            ;;
        --outro-only)
            OUTRO_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            shift
            ;;
    esac
done

# Validate
if [[ -z "$CHAPTER" ]] && [[ "$ALL" == false ]]; then
    usage
fi

# Check dependencies
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is required"
    exit 1
fi

# Check source files
if [[ ! -f "$MAIN_THEME" ]]; then
    echo "Error: Main theme not found: $MAIN_THEME"
    exit 1
fi

if [[ ! -f "$HARBOR_AMBIENT" ]]; then
    echo "Error: Harbor ambient not found: $HARBOR_AMBIENT"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=== Saltmere Chapter Bumper Generator ==="
echo "Main theme: $MAIN_THEME"
echo "Ambient: $HARBOR_AMBIENT"
echo "Output: $OUTPUT_DIR"
echo ""

if $ALL; then
    CHAPTERS=(01 02 03 04 05 06 07 08 09 10 11 12)
else
    CHAPTERS=("$CHAPTER")
fi

for ch in "${CHAPTERS[@]}"; do
    if ! $OUTRO_ONLY; then
        if $DRY_RUN; then
            echo "[DRY RUN] Would generate intro for Chapter $ch"
        else
            generate_intro_bumper "$ch"
        fi
    fi

    if ! $INTRO_ONLY; then
        if $DRY_RUN; then
            echo "[DRY RUN] Would generate outro for Chapter $ch"
        else
            generate_outro_bumper "$ch"
        fi
    fi
done

echo ""
echo "Done!"
if ! $DRY_RUN; then
    echo "Bumpers saved to: $OUTPUT_DIR/"
    ls -la "$OUTPUT_DIR/"
fi
