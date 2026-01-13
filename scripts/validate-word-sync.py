#!/usr/bin/env python3
"""
Validate word synchronization between HTML, manuscripts, and audio transcripts.

Catches mismatches early before they cause click-to-seek failures.

Usage:
    python scripts/validate-word-sync.py              # Check all chapters
    python scripts/validate-word-sync.py --chapter 3  # Check specific chapter
    python scripts/validate-word-sync.py --fix        # Attempt auto-fixes
"""

import argparse
import json
import re
from pathlib import Path
from html import unescape
from difflib import SequenceMatcher


def normalize_word(word: str) -> str:
    """Normalize word for comparison."""
    return unescape(word).lower().strip('.,!?"\'-:;()[]""''')


def load_transcript_words(chapter_num: int) -> list[str] | None:
    """Load words from audio transcript JSON."""
    words_path = Path(f'site/public/js/words/chapter-{chapter_num:02d}-words.json')
    if not words_path.exists():
        return None
    data = json.loads(words_path.read_text())
    return [w[2] for w in data['words']]


def load_html_words(chapter_num: int) -> list[tuple[str, int | None]] | None:
    """Load words from HTML, returning (word_text, data_i or None)."""
    html_files = list(Path('site/read').glob(f'chapter-{chapter_num:02d}*.html'))
    if not html_files:
        return None

    content = html_files[0].read_text()
    pattern = r'<span class="w"(?: data-i="(\d+)")?>([^<]+)</span>'

    words = []
    for match in re.finditer(pattern, content):
        data_i = int(match.group(1)) if match.group(1) else None
        word_text = unescape(match.group(2))
        words.append((word_text, data_i))

    return words


def load_manuscript_words(chapter_num: int) -> list[str] | None:
    """Load words from manuscript markdown."""
    md_files = list(Path('manuscript/saltmere').glob(f'chapter-{chapter_num:02d}*.md'))
    if not md_files:
        return None

    content = md_files[0].read_text()
    # Remove markdown formatting
    content = re.sub(r'\*+', '', content)
    content = re.sub(r'_+', '', content)
    content = re.sub(r'^#.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^---$', '', content, flags=re.MULTILINE)

    # Split into words
    words = re.findall(r'[\w\']+[.,!?"\'-:;]*', content)
    return words


def find_mismatches(chapter_num: int) -> dict:
    """Find mismatches between HTML, transcript, and manuscript."""
    results = {
        'chapter': chapter_num,
        'errors': [],
        'warnings': [],
        'dead_words': [],
        'mismatches': [],
    }

    transcript = load_transcript_words(chapter_num)
    html_words = load_html_words(chapter_num)
    manuscript = load_manuscript_words(chapter_num)

    if not transcript:
        results['errors'].append('No transcript found')
        return results

    if not html_words:
        results['errors'].append('No HTML found')
        return results

    # Check for dead words (no data-i)
    for i, (word_text, data_i) in enumerate(html_words):
        if data_i is None:
            results['dead_words'].append({
                'html_index': i,
                'word': word_text,
            })

    # Check for HTML/transcript mismatches at indexed positions
    for i, (word_text, data_i) in enumerate(html_words):
        if data_i is not None and data_i < len(transcript):
            html_norm = normalize_word(word_text)
            trans_norm = normalize_word(transcript[data_i])

            # Check similarity
            ratio = SequenceMatcher(None, html_norm, trans_norm).ratio()
            if ratio < 0.6 and html_norm != trans_norm:
                results['mismatches'].append({
                    'data_i': data_i,
                    'html_word': word_text,
                    'transcript_word': transcript[data_i],
                    'similarity': round(ratio, 2),
                })

    # Summary warnings
    if len(results['dead_words']) > 10:
        results['warnings'].append(f"{len(results['dead_words'])} words without data-i (not clickable)")

    if results['mismatches']:
        results['warnings'].append(f"{len(results['mismatches'])} HTML/transcript mismatches")

    return results


def print_report(results: dict, verbose: bool = False):
    """Print validation report."""
    ch = results['chapter']

    if results['errors']:
        print(f"Chapter {ch}: ERRORS")
        for err in results['errors']:
            print(f"  - {err}")
        return

    status = "OK" if not results['warnings'] else "WARNINGS"
    print(f"Chapter {ch}: {status}")

    for warn in results['warnings']:
        print(f"  ⚠ {warn}")

    if verbose or results['mismatches']:
        for mm in results['mismatches'][:5]:  # Show first 5
            print(f"  MISMATCH at [{mm['data_i']}]: HTML '{mm['html_word']}' vs transcript '{mm['transcript_word']}'")
        if len(results['mismatches']) > 5:
            print(f"  ... and {len(results['mismatches']) - 5} more mismatches")

    if verbose and results['dead_words']:
        print(f"  Dead words: {[d['word'] for d in results['dead_words'][:10]]}")
        if len(results['dead_words']) > 10:
            print(f"  ... and {len(results['dead_words']) - 10} more")


def main():
    parser = argparse.ArgumentParser(description='Validate word synchronization')
    parser.add_argument('--chapter', type=int, help='Check specific chapter')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show details')
    parser.add_argument('--fix', action='store_true', help='Attempt auto-fixes (not implemented)')
    args = parser.parse_args()

    chapters = [args.chapter] if args.chapter else list(range(1, 8))

    print("=== Word Sync Validation ===\n")

    total_mismatches = 0
    total_dead = 0

    for ch in chapters:
        results = find_mismatches(ch)
        print_report(results, verbose=args.verbose)
        total_mismatches += len(results.get('mismatches', []))
        total_dead += len(results.get('dead_words', []))

    print()
    if total_mismatches > 0:
        print(f"⚠ Total mismatches: {total_mismatches} (click-to-seek may fail)")
    if total_dead > 0:
        print(f"⚠ Total dead words: {total_dead} (not clickable)")

    if total_mismatches == 0 and total_dead == 0:
        print("✓ All words validated successfully")
        return 0

    return 1 if total_mismatches > 0 else 0


if __name__ == '__main__':
    exit(main())
