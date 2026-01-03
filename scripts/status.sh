#!/bin/bash
#
# Simulacrum Stories Status Dashboard
# Shows budget utilization, series health, and recent activity
#

set -euo pipefail

VERBOSE=false
if [[ "${1:-}" == "--verbose" ]] || [[ "${1:-}" == "-v" ]]; then
    VERBOSE=true
fi

# Paths
SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
BUDGET_MANAGER="$SCRIPTS_DIR/../audio_budget_manager.py"
SERIES_REGISTRY="$HOME/devvyn-meta-project/data/simulacrum-series.json"
SCHEDULER_LOG="$HOME/Library/Logs/simulacrum-scheduler.log"
LAUNCHAGENT_PLIST="$HOME/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist"
OUTPUT_DIR="$HOME/Music/Simulacrum-Stories"

# Colors
RESET="\033[0m"
BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
BLUE="\033[34m"
CYAN="\033[36m"
RED="\033[31m"

print_header() {
    echo -e "${BOLD}${BLUE}$1${RESET}"
    python3 -c "print('=' * 70)"
}

print_section() {
    echo -e "\n${BOLD}${CYAN}$1${RESET}"
    python3 -c "print('-' * 70)"
}

# =============================================================================
# Budget Status
# =============================================================================

print_header "🎙️  SIMULACRUM STORIES - STATUS DASHBOARD"
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo

print_section "📊 Budget Status"
python3 "$BUDGET_MANAGER" status
echo

# =============================================================================
# Series Health
# =============================================================================

print_section "📚 Series Health"

if [[ ! -f "$SERIES_REGISTRY" ]]; then
    echo -e "${RED}✗ Series registry not found${RESET}"
else
    # Parse JSON and display series info
    while IFS= read -r series_key; do
        name=$(python3 -c "import sys, json; d=json.load(open('$SERIES_REGISTRY')); print(d['$series_key']['name'])" 2>/dev/null || echo "Unknown")
        ep_count=$(python3 -c "import sys, json; d=json.load(open('$SERIES_REGISTRY')); print(d['$series_key']['episode_count'])" 2>/dev/null || echo "0")
        last_ep=$(python3 -c "import sys, json; d=json.load(open('$SERIES_REGISTRY')); print(d['$series_key'].get('last_episode_at', 'Never'))" 2>/dev/null || echo "Never")

        # Calculate days since last episode
        if [[ "$last_ep" != "Never" ]]; then
            last_date=$(date -j -f "%Y-%m-%dT%H:%M:%S" "${last_ep%%.*}" "+%s" 2>/dev/null || echo "0")
            now=$(date "+%s")
            days_ago=$(( (now - last_date) / 86400 ))

            if [[ $days_ago -eq 0 ]]; then
                staleness="${GREEN}Today${RESET}"
            elif [[ $days_ago -eq 1 ]]; then
                staleness="${GREEN}Yesterday${RESET}"
            elif [[ $days_ago -le 3 ]]; then
                staleness="${GREEN}${days_ago} days ago${RESET}"
            elif [[ $days_ago -le 7 ]]; then
                staleness="${YELLOW}${days_ago} days ago${RESET}"
            else
                staleness="${RED}${days_ago} days ago${RESET}"
            fi
        else
            staleness="${RED}Never${RESET}"
        fi

        echo -e "  ${BOLD}$name${RESET}"
        echo -e "    Episodes: $ep_count"
        echo -e "    Last episode: $staleness"

        # Show episode files if verbose
        if [[ "$VERBOSE" == true ]]; then
            series_dir="$OUTPUT_DIR/${name} Chronicles"
            if [[ -d "$series_dir" ]]; then
                echo "    Files:"
                /bin/ls -1t "$series_dir"/*.mp3 2>/dev/null | head -5 | while read -r f; do
                    echo "      $(basename "$f")"
                done
            fi
        fi
        echo

    done < <(python3 -c "import json; d=json.load(open('$SERIES_REGISTRY')); print('\n'.join(d.keys()))")
fi

# =============================================================================
# Podcast Feeds
# =============================================================================

print_section "📡 Podcast Feeds"

FEED_DIR="$OUTPUT_DIR/_feeds"
if [[ -d "$FEED_DIR" ]]; then
    feed_count=$(find "$FEED_DIR" -name "*.xml" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$feed_count" -gt 0 ]]; then
        echo -e "  ${GREEN}✓ $feed_count feed(s) published${RESET}"
        echo ""
        for feed in "$FEED_DIR"/*.xml; do
            if [[ -f "$feed" ]]; then
                feed_name=$(basename "$feed" .xml | sed 's/-/ /g' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2));}1')
                episodes=$(grep -c "<item>" "$feed" 2>/dev/null || echo "0")
                last_update=$(date -r "$feed" "+%b %d, %Y %H:%M" 2>/dev/null || echo "Unknown")
                echo "  $feed_name"
                echo "    Episodes in feed: $episodes"
                echo "    Last updated: $last_update"
                echo "    Feed: http://localhost:8000/feeds/$(basename "$feed")"
                echo ""
            fi
        done
        echo "  ${BLUE}Start server:${RESET} ~/devvyn-meta-project/scripts/narrative-tools/start-podcast-server.sh"
    else
        echo -e "  ${YELLOW}⚠ No feeds generated yet${RESET}"
        echo "  Run: cd ~/devvyn-meta-project/scripts/narrative-tools && python3 podcast_feed.py --all"
    fi
else
    echo -e "  ${YELLOW}⚠ Feed directory not found${RESET}"
fi
echo

# =============================================================================
# Scheduler Status
# =============================================================================

print_section "⏰ Automation Status"

if [[ -f "$LAUNCHAGENT_PLIST" ]]; then
    # Check if loaded
    if launchctl list | grep -q "ca.devvyn.simulacrum-daily"; then
        echo -e "${GREEN}✓ LaunchAgent loaded and active${RESET}"

        # Get next run time
        echo "  Schedule: Daily at 6:00 AM and 7:30 AM"

        # Show last run from log
        if [[ -f "$SCHEDULER_LOG" ]]; then
            last_run=$(grep "Starting budget-driven" "$SCHEDULER_LOG" | tail -1 | cut -d' ' -f1-2)
            if [[ -n "$last_run" ]]; then
                echo "  Last run: $last_run"
            fi
        fi
    else
        echo -e "${YELLOW}⚠ LaunchAgent exists but not loaded${RESET}"
        echo "  To load: launchctl load ~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist"
    fi
else
    echo -e "${RED}✗ LaunchAgent not configured${RESET}"
fi
echo

# =============================================================================
# Recent Activity
# =============================================================================

print_section "📝 Recent Activity"

if [[ -f "$SCHEDULER_LOG" ]]; then
    echo "Last 10 scheduler runs:"
    echo
    grep -E "(Starting budget-driven|Episodes generated|Failed)" "$SCHEDULER_LOG" | tail -20 | while read -r line; do
        if echo "$line" | grep -q "Starting"; then
            echo -e "${CYAN}${line}${RESET}"
        elif echo "$line" | grep -q "Failed"; then
            echo -e "${RED}${line}${RESET}"
        else
            echo "$line"
        fi
    done
else
    echo "No scheduler log found. Scheduler hasn't run yet."
fi
echo

# =============================================================================
# Disk Usage
# =============================================================================

if [[ "$VERBOSE" == true ]]; then
    print_section "💾 Disk Usage"

    if [[ -d "$OUTPUT_DIR" ]]; then
        echo "Total size: $(du -sh "$OUTPUT_DIR" | cut -f1)"
        echo
        echo "By series:"
        for series_dir in "$OUTPUT_DIR"/*/ ; do
            if [[ -d "$series_dir" ]]; then
                size=$(du -sh "$series_dir" | cut -f1)
                name=$(basename "$series_dir")
                echo "  $name: $size"
            fi
        done
    fi
    echo
fi

# =============================================================================
# Next Steps
# =============================================================================

print_section "🚀 Quick Commands"
echo "  Test scheduler:   cd ~/devvyn-meta-project/scripts/narrative-tools && ./budget-driven-scheduler.py --dry-run"
echo "  Generate now:     cd ~/devvyn-meta-project/scripts/narrative-tools && ./budget-driven-scheduler.py"
echo "  Load automation:  launchctl load ~/Library/LaunchAgents/ca.devvyn.simulacrum-daily.plist"
echo "  View logs:        tail -f ~/Library/Logs/simulacrum-scheduler.log"
echo "  Budget status:    ~/devvyn-meta-project/scripts/audio-budget-manager.py status"
echo

print_header "Dashboard complete"
