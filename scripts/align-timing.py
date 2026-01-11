#!/usr/bin/env python3
"""
Align transcription with manuscript sections for timing calibration.

Matches transcript words to manuscript text to:
- Map section boundaries to audio timestamps
- Identify missing pauses at section breaks
- Generate timing metadata for editing

Usage:
    python scripts/align-timing.py --chapter 01
    python scripts/align-timing.py --all
"""

import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    # Lowercase
    text = text.lower()
    # Remove punctuation except apostrophes
    text = re.sub(r"[^\w\s']", ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def get_words(text: str) -> list:
    """Extract words from text."""
    normalized = normalize_text(text)
    return normalized.split()


def find_best_match(needle_words: list, haystack_words: list, start_idx: int = 0) -> tuple:
    """
    Find the best match for a sequence of words in a larger sequence.

    Returns:
        (match_start_idx, match_end_idx, similarity_score)
    """
    if not needle_words:
        return (start_idx, start_idx, 0.0)

    needle_str = ' '.join(needle_words)
    best_score = 0.0
    best_start = start_idx
    best_end = start_idx

    # Sliding window search
    window_size = len(needle_words)
    search_start = max(0, start_idx - 50)  # Allow some backward search
    search_end = min(len(haystack_words), start_idx + len(needle_words) * 3)

    for i in range(search_start, search_end - window_size + 1):
        window = haystack_words[i:i + window_size]
        window_str = ' '.join(window)

        # Quick check: if first words don't match, skip
        if window[0] != needle_words[0] and i > search_start + 20:
            continue

        score = SequenceMatcher(None, needle_str, window_str).ratio()

        if score > best_score:
            best_score = score
            best_start = i
            best_end = i + window_size

    return (best_start, best_end, best_score)


def align_chapter(sections_file: Path, transcript_file: Path) -> dict:
    """
    Align manuscript sections with transcript timestamps.

    Returns:
        Timing metadata with section boundaries and pause analysis
    """
    # Load data
    with open(sections_file) as f:
        sections_data = json.load(f)

    with open(transcript_file) as f:
        transcript_data = json.load(f)

    sections = sections_data['sections']
    transcript_words = transcript_data['words']
    pauses = transcript_data['pauses']

    # Build word list from transcript
    t_words = [w['word'].lower().strip() for w in transcript_words]
    t_word_times = [(w['start'], w['end']) for w in transcript_words]

    # Align each section
    aligned_sections = []
    current_t_idx = 0
    issues = []

    for section in sections:
        # Get first ~30 words of section for matching
        preview_text = section['text_preview'].replace('...', '')
        section_words = get_words(preview_text)[:30]

        # Find match in transcript
        match_start, match_end, score = find_best_match(
            section_words, t_words, current_t_idx
        )

        if score < 0.5:
            issues.append({
                'section': section['id'],
                'issue': 'low_match_score',
                'score': round(score, 2),
                'expected_words': ' '.join(section_words[:10]),
            })

        # Get timestamps
        section_start_time = t_word_times[match_start][0] if match_start < len(t_word_times) else 0

        # Estimate section end by word count ratio
        words_per_second = len(t_words) / transcript_data['duration']
        section_duration_estimate = section['word_count'] / words_per_second
        section_end_time_estimate = section_start_time + section_duration_estimate

        # Find actual end by looking for pause near expected end
        actual_end_time = section_end_time_estimate
        pause_found = None
        pause_adequate = False

        if section['expected_pause_after']:
            # Look for pause near expected section end
            for pause in pauses:
                if section_end_time_estimate - 30 < pause['start'] < section_end_time_estimate + 30:
                    if pause_found is None or pause['duration'] > pause_found['duration']:
                        pause_found = pause

            if pause_found:
                actual_end_time = pause_found['end']
                pause_adequate = pause_found['duration'] >= 1.5

                if not pause_adequate:
                    issues.append({
                        'section': section['id'],
                        'issue': 'insufficient_pause',
                        'timestamp': round(pause_found['start'], 1),
                        'expected_pause': '>=1.5s',
                        'actual_pause': f"{pause_found['duration']:.2f}s",
                    })
            else:
                issues.append({
                    'section': section['id'],
                    'issue': 'no_pause_detected',
                    'expected_at': round(section_end_time_estimate, 1),
                    'note': 'Section break not audible',
                })

        aligned_section = {
            'id': section['id'],
            'manuscript_start_line': section['start_line'],
            'manuscript_end_line': section['end_line'],
            'word_count': section['word_count'],
            'audio_start_time': round(section_start_time, 2),
            'audio_end_time_estimate': round(section_end_time_estimate, 2),
            'audio_end_time_actual': round(actual_end_time, 2),
            'match_score': round(score, 2),
            'expected_pause_after': section['expected_pause_after'],
            'pause_detected': pause_found is not None,
            'pause_duration': round(pause_found['duration'], 2) if pause_found else None,
            'pause_adequate': pause_adequate,
        }
        aligned_sections.append(aligned_section)

        # Move search position forward
        current_t_idx = match_end

    # Calculate section break summary
    expected_breaks = sum(1 for s in sections if s['expected_pause_after'])
    detected_breaks = sum(1 for s in aligned_sections if s['pause_detected'])
    adequate_breaks = sum(1 for s in aligned_sections if s['pause_adequate'])

    result = {
        'file': sections_data['file'].replace('.md', ''),
        'chapter': sections_data['chapter'],
        'title': sections_data['title'],
        'total_duration': round(transcript_data['duration'], 1),
        'word_count': sections_data['total_words'],
        'section_count': len(aligned_sections),
        'section_break_summary': {
            'expected': expected_breaks,
            'detected_pauses': detected_breaks,
            'adequate_pauses': adequate_breaks,
            'missing_or_insufficient': expected_breaks - adequate_breaks,
        },
        'sections': aligned_sections,
        'issues': issues,
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Align transcript with manuscript sections')
    parser.add_argument('--chapter', type=str, help='Chapter number (01-12) or vignette-a/vignette-b')
    parser.add_argument('--all', action='store_true', help='Align all available chapters')
    parser.add_argument('--timing-dir', type=Path, default=Path('output/timing/saltmere'),
                        help='Directory containing sections and transcript files')
    args = parser.parse_args()

    if not args.chapter and not args.all:
        parser.print_help()
        return

    # Find files to process
    if args.all:
        section_files = sorted(args.timing_dir.glob('*-sections.json'))
    else:
        section_files = list(args.timing_dir.glob(f'*{args.chapter}*-sections.json'))

    if not section_files:
        print(f"No section files found in {args.timing_dir}")
        return

    print(f"=== Aligning {len(section_files)} chapter(s) ===\n")

    all_issues = []
    total_expected = 0
    total_adequate = 0

    for sections_file in section_files:
        # Find matching transcript
        stem = sections_file.stem.replace('-sections', '')
        transcript_file = args.timing_dir / f"{stem}-transcript.json"

        if not transcript_file.exists():
            print(f"Skipping {sections_file.name}: no transcript found")
            continue

        result = align_chapter(sections_file, transcript_file)

        # Save timing file
        output_file = args.timing_dir / f"{stem}-timing.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        summary = result['section_break_summary']
        print(f"{result['chapter']}: {result['title']}")
        print(f"  Duration: {result['total_duration']}s, Sections: {result['section_count']}")
        print(f"  Section breaks: {summary['expected']} expected, {summary['adequate_pauses']} adequate, {summary['missing_or_insufficient']} issues")
        print(f"  Saved: {output_file.name}")

        if result['issues']:
            print(f"  Issues:")
            for issue in result['issues']:
                if issue['issue'] == 'insufficient_pause':
                    print(f"    - Section {issue['section']}: pause only {issue['actual_pause']} at {issue['timestamp']}s")
                elif issue['issue'] == 'no_pause_detected':
                    print(f"    - Section {issue['section']}: no pause near {issue['expected_at']}s")

        all_issues.extend(result['issues'])
        total_expected += summary['expected']
        total_adequate += summary['adequate_pauses']

        print()

    # Summary
    print("=== Summary ===")
    print(f"Total section breaks expected: {total_expected}")
    print(f"Adequate pauses found: {total_adequate}")
    print(f"Missing or insufficient: {total_expected - total_adequate}")

    if total_expected > 0:
        pct = (total_adequate / total_expected) * 100
        print(f"Section break compliance: {pct:.0f}%")


if __name__ == '__main__':
    main()
