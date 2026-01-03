#!/bin/bash
# Publish Simulacrum Stories podcasts to Netlify
# Usage: ./publish-podcasts.sh [netlify-site-url]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PODCAST_DIR="${HOME}/Music/Simulacrum-Stories"
SITE_DIR="${HOME}/devvyn-meta-project/podcast-site"
FEEDS_SOURCE="${PODCAST_DIR}/_feeds"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🎙️  Simulacrum Stories - Podcast Publisher${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get Netlify site URL
if [[ $# -eq 0 ]]; then
    echo -e "${YELLOW}No Netlify URL provided. Using placeholder.${NC}"
    echo ""
    echo "After first deployment, run:"
    echo "  $0 https://your-site.netlify.app"
    echo ""
    NETLIFY_URL="https://podcasts.devvyn.ca"
else
    NETLIFY_URL="$1"
fi

echo "Target URL: ${NETLIFY_URL}"
echo ""

# Step 1: Regenerate feeds with public URL
echo -e "${GREEN}[1/4] Regenerating RSS feeds with public URL...${NC}"
cd "$SCRIPT_DIR"
python3 podcast_feed.py --all --base-url "$NETLIFY_URL"
echo ""

# Step 2: Copy feeds to site directory
echo -e "${GREEN}[2/4] Copying feeds to site directory...${NC}"
mkdir -p "${SITE_DIR}/feeds"
cp -v "${FEEDS_SOURCE}"/*.xml "${SITE_DIR}/feeds/" 2>/dev/null || {
    echo -e "${RED}Error: No feeds found${NC}"
    exit 1
}
echo ""

# Step 3: Copy audio files to site directory
echo -e "${GREEN}[3/4] Copying audio files...${NC}"
for series in "Millbrook Chronicles" "Saltmere Chronicles"; do
    series_dir="${PODCAST_DIR}/${series}"
    series_slug=$(echo "$series" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    target_dir="${SITE_DIR}/audio/${series_slug}"

    mkdir -p "$target_dir"

    if [[ -d "$series_dir" ]]; then
        # Copy MP3 files
        mp3_count=$(find "$series_dir" -name "E*.mp3" -type f | wc -l | tr -d ' ')
        if [[ $mp3_count -gt 0 ]]; then
            echo "  Copying $mp3_count episodes from $series..."
            find "$series_dir" -name "E*.mp3" -type f -exec cp -v {} "$target_dir/" \;
        fi

        # Copy artwork if exists
        for artwork in cover.jpg cover.png artwork.jpg; do
            if [[ -f "$series_dir/$artwork" ]]; then
                cp -v "$series_dir/$artwork" "$target_dir/"
                break
            fi
        done
    fi
done
echo ""

# Step 4: Show deployment instructions
echo -e "${GREEN}[4/4] Site ready for deployment!${NC}"
echo ""
echo "Site directory: ${SITE_DIR}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Deployment Options:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if netlify CLI is available
if command -v netlify &> /dev/null; then
    echo -e "${GREEN}Option 1: Netlify CLI (Recommended)${NC}"
    echo ""
    echo "  cd ${SITE_DIR}"
    echo "  netlify deploy --prod"
    echo ""
else
    echo -e "${YELLOW}Option 1: Install Netlify CLI${NC}"
    echo ""
    echo "  npm install -g netlify-cli"
    echo "  cd ${SITE_DIR}"
    echo "  netlify login"
    echo "  netlify init"
    echo "  netlify deploy --prod"
    echo ""
fi

echo -e "${GREEN}Option 2: Netlify Drag & Drop${NC}"
echo ""
echo "  1. Open: https://app.netlify.com/drop"
echo "  2. Drag folder: ${SITE_DIR}"
echo "  3. Wait for deployment"
echo "  4. Copy your site URL (e.g., https://random-name-123.netlify.app)"
echo "  5. Run: $0 https://your-site.netlify.app"
echo "  6. Drag folder again to update feeds"
echo ""

echo -e "${BLUE}Option 3: Git-based Deployment${NC}"
echo ""
echo "  cd ${SITE_DIR}"
echo "  git init"
echo "  git add ."
echo "  git commit -m 'Initial podcast site'"
echo "  # Push to GitHub/GitLab"
echo "  # Connect repo in Netlify dashboard"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Site preparation complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show file count
total_mp3s=$(find "${SITE_DIR}/audio" -name "*.mp3" -type f 2>/dev/null | wc -l | tr -d ' ')
total_feeds=$(find "${SITE_DIR}/feeds" -name "*.xml" -type f 2>/dev/null | wc -l | tr -d ' ')

echo "📊 Summary:"
echo "   Episodes: ${total_mp3s}"
echo "   Feeds: ${total_feeds}"
echo "   Target: ${NETLIFY_URL}"
echo ""
