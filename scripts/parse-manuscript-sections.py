#!/usr/bin/env python3
"""
Parse manuscript sections for timing calibration.

Extracts:
- Section boundaries (line numbers where --- occurs)
- Text content per section (cleaned, no markdown)
- Word counts per section
- Expected pause locations

Usage:
    python scripts/parse-manuscript-sections.py --chapter 01
    python scripts/parse-manuscript-sections.py --all
"""

import argparse
import json
import re
from pathlib import Path


def clean_text(text: str) -> str:
    """Remove markdown formatting, keep plain text for matching."""
    # Remove emphasis markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.+?)\*', r'\1', text)       # italic
    text = re.sub(r'_(.+?)_', r'\1', text)         # underscore italic

    # Remove headers
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def count_words(text: str) -> int:
    """Count words in cleaned text."""
    cleaned = clean_text(text)
    if not cleaned:
        return 0
    return len(cleaned.split())


def parse_chapter(chapter_path: Path) -> dict:
    """Parse a chapter markdown file into sections."""
    content = chapter_path.read_text()
    lines = content.split('\n')

    # Extract chapter info from filename
    stem = chapter_path.stem
    if stem.startswith('chapter-'):
        # chapter-01-the-research-station -> 01
        parts = stem.split('-')
        chapter_num = parts[1]
        chapter_title = ' '.join(parts[2:]).replace('-', ' ').title()
    elif stem.startswith('vignette-'):
        # vignette-a-thomas-and-the-nets -> vignette-a
        parts = stem.split('-')
        chapter_num = f"vignette-{parts[1]}"
        chapter_title = ' '.join(parts[2:]).replace('-', ' ').title()
    else:
        chapter_num = stem
        chapter_title = stem

    # Find all section separators
    separator_lines = []
    for i, line in enumerate(lines):
        if line.strip() == '---':
            separator_lines.append(i + 1)  # 1-indexed

    # Filter out separators that are part of end matter
    # Look for patterns like "End of Chapter" or "Editorial Notes"
    content_separators = []
    for sep_line in separator_lines:
        # Check what follows this separator
        following_text = '\n'.join(lines[sep_line:sep_line + 5])

        # Skip if followed by end matter
        if re.search(r'End of (Chapter|Vignette)', following_text, re.IGNORECASE):
            break
        if 'Editorial Notes' in following_text:
            break

        content_separators.append(sep_line)

    # Build sections
    sections = []
    section_starts = [1] + [s + 1 for s in content_separators]  # Line after each separator
    section_ends = content_separators + [len(lines)]

    for i, (start, end) in enumerate(zip(section_starts, section_ends)):
        # Get lines for this section
        section_lines = lines[start - 1:end - 1]  # Convert to 0-indexed

        # Skip empty sections
        text = '\n'.join(section_lines).strip()
        if not text:
            continue

        # Skip if this is just a separator or end matter
        if text == '---' or text.startswith('*End of'):
            continue

        # Clean and count
        cleaned = clean_text(text)
        word_count = count_words(text)

        section = {
            'id': i + 1,
            'start_line': start,
            'end_line': end - 1,
            'word_count': word_count,
            'text_preview': cleaned[:100] + '...' if len(cleaned) > 100 else cleaned,
            'expected_pause_after': i < len(content_separators),  # All but last section
        }
        sections.append(section)

    # Recalculate end lines to exclude separator
    for i, section in enumerate(sections[:-1]):
        # End line should be the line before the next separator
        section['end_line'] = content_separators[i] - 1

    return {
        'file': chapter_path.name,
        'chapter': chapter_num,
        'title': chapter_title,
        'total_lines': len(lines),
        'total_words': sum(s['word_count'] for s in sections),
        'section_count': len(sections),
        'separator_count': len(content_separators),
        'sections': sections,
    }


def main():
    parser = argparse.ArgumentParser(description='Parse manuscript sections for timing calibration')
    parser.add_argument('--chapter', type=str, help='Chapter number (01-12) or vignette-a/vignette-b')
    parser.add_argument('--all', action='store_true', help='Process all chapters')
    parser.add_argument('--output-dir', type=Path, default=Path('output/timing/saltmere'),
                        help='Output directory for section JSON files')
    args = parser.parse_args()

    manuscript_dir = Path('manuscript/saltmere')

    if not args.chapter and not args.all:
        parser.print_help()
        return

    # Collect files to process
    files = []
    if args.all:
        files = sorted(manuscript_dir.glob('*.md'))
    else:
        # Find matching file
        pattern = f'*{args.chapter}*.md'
        matches = list(manuscript_dir.glob(pattern))
        if not matches:
            print(f"No chapter found matching: {args.chapter}")
            return
        files = matches

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Process each file
    all_sections = []
    total_separators = 0

    for chapter_path in files:
        print(f"Parsing: {chapter_path.name}")
        result = parse_chapter(chapter_path)

        # Save individual chapter JSON
        output_file = args.output_dir / f"{chapter_path.stem}-sections.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Sections: {result['section_count']}, Separators: {result['separator_count']}, Words: {result['total_words']}")

        all_sections.append(result)
        total_separators += result['separator_count']

    # Summary
    print(f"\n=== Summary ===")
    print(f"Files processed: {len(files)}")
    print(f"Total section separators: {total_separators}")
    print(f"Total words: {sum(r['total_words'] for r in all_sections)}")

    # Save summary
    summary = {
        'files_processed': len(files),
        'total_separators': total_separators,
        'total_words': sum(r['total_words'] for r in all_sections),
        'chapters': [
            {
                'file': r['file'],
                'chapter': r['chapter'],
                'title': r['title'],
                'sections': r['section_count'],
                'separators': r['separator_count'],
                'words': r['total_words'],
            }
            for r in all_sections
        ]
    }

    summary_file = args.output_dir / 'manuscript-summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to: {summary_file}")


if __name__ == '__main__':
    main()
