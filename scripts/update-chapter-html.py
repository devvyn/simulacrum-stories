#!/usr/bin/env python3
"""
Update chapter HTML files to include audio player CSS and JS.
"""
from pathlib import Path
import re

SITE_DIR = Path(__file__).parent.parent / "site"
READ_DIR = SITE_DIR / "read"

# CSS link to add before </head>
CSS_LINK = '    <link rel="stylesheet" href="/css/chapter-player.css">\n'

# JS script to add before </body>
JS_SCRIPT = '''    <!-- Netlify Forms (for audio issue reports) -->
    <form name="audio-issue-report" netlify netlify-honeypot="bot-field" hidden>
        <input type="hidden" name="form-name" value="audio-issue-report">
        <input type="text" name="bot-field">
        <input type="text" name="chapter">
        <input type="text" name="timestamp">
        <input type="text" name="timestamp-display">
        <input type="text" name="issue-type">
        <textarea name="description"></textarea>
    </form>
    <script src="/js/chapter-player.js"></script>
'''

def update_chapter_file(filepath: Path) -> bool:
    """Update a single chapter HTML file."""
    content = filepath.read_text()
    modified = False

    # Add CSS link if not present
    if '/css/chapter-player.css' not in content:
        content = content.replace('</head>', CSS_LINK + '</head>')
        modified = True

    # Add JS script if not present
    if '/js/chapter-player.js' not in content:
        content = content.replace('</body>', JS_SCRIPT + '</body>')
        modified = True

    # Add has-audio-player class to body if not present
    # (The JS will add this dynamically, but we can add the class preparation)
    if modified:
        filepath.write_text(content)
        return True
    return False

def main():
    """Update all chapter HTML files."""
    print("Updating chapter HTML files...")

    chapter_files = sorted(READ_DIR.glob("chapter-*.html"))
    updated = 0

    for filepath in chapter_files:
        if update_chapter_file(filepath):
            print(f"  Updated: {filepath.name}")
            updated += 1
        else:
            print(f"  Skipped (already has player): {filepath.name}")

    print(f"\nDone. Updated {updated} files.")

if __name__ == "__main__":
    main()
