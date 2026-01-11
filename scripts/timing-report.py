#!/usr/bin/env python3
"""
Generate human-readable timing reports for audio editing.

Usage:
    python scripts/timing-report.py --chapter 01
    python scripts/timing-report.py --all
"""

import argparse
import json
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS.s"""
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes:02d}:{secs:05.2f}"


def generate_report(timing_file: Path) -> str:
    """Generate a markdown report from timing data."""
    with open(timing_file) as f:
        data = json.load(f)

    lines = []

    # Header
    lines.append(f"# Timing Report: Chapter {data['chapter']}")
    lines.append(f"## {data['title']}")
    lines.append("")
    lines.append(f"**Duration:** {format_timestamp(data['total_duration'])} ({data['total_duration']:.1f}s)")
    lines.append(f"**Word Count:** {data['word_count']}")
    lines.append(f"**Sections:** {data['section_count']}")
    lines.append("")

    # Section break summary
    summary = data['section_break_summary']
    lines.append("### Section Break Analysis")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Expected breaks | {summary['expected']} |")
    lines.append(f"| Adequate pauses (≥1.5s) | {summary['adequate_pauses']} |")
    lines.append(f"| Missing/Insufficient | {summary['missing_or_insufficient']} |")

    if summary['expected'] > 0:
        compliance = (summary['adequate_pauses'] / summary['expected']) * 100
        lines.append(f"| Compliance | {compliance:.0f}% |")

    lines.append("")

    # Section details
    lines.append("### Section Details")
    lines.append("")
    lines.append("| Section | Start | End (est) | Words | Pause After | Status |")
    lines.append("|---------|-------|-----------|-------|-------------|--------|")

    for section in data['sections']:
        start = format_timestamp(section['audio_start_time'])
        end = format_timestamp(section['audio_end_time_estimate'])
        words = section['word_count']

        if not section['expected_pause_after']:
            pause_info = "N/A (final)"
            status = "✓"
        elif section['pause_adequate']:
            pause_info = f"{section['pause_duration']:.2f}s"
            status = "✓ Adequate"
        elif section['pause_detected']:
            pause_info = f"{section['pause_duration']:.2f}s"
            status = "⚠ Insufficient"
        else:
            pause_info = "None"
            status = "✗ Missing"

        lines.append(f"| {section['id']} | {start} | {end} | {words} | {pause_info} | {status} |")

    lines.append("")

    # Issues for DAW
    if data['issues']:
        lines.append("### Edit Points for DAW")
        lines.append("")
        lines.append("The following timestamps need attention (add/extend pauses):")
        lines.append("")

        for issue in data['issues']:
            if issue['issue'] == 'insufficient_pause':
                ts = format_timestamp(issue['timestamp'])
                lines.append(f"- **{ts}** (Section {issue['section']} end): Current pause {issue['actual_pause']}, need ≥1.5s")
            elif issue['issue'] == 'no_pause_detected':
                ts = format_timestamp(issue['expected_at'])
                lines.append(f"- **{ts}** (Section {issue['section']} end): No audible pause detected")

        lines.append("")
        lines.append("**Recommended action:** Insert 1.5-2.0s silence at each marked timestamp.")
        lines.append("")

    # Editing notes
    lines.append("### Editing Notes")
    lines.append("")
    lines.append("Section breaks (`---` in manuscript) should produce audible pauses of 1.5-2.0 seconds.")
    lines.append("This signals a scene change or time skip to the listener.")
    lines.append("")
    lines.append("**Options for fixing:**")
    lines.append("1. Insert silence in DAW at marked timestamps")
    lines.append("2. Re-generate specific sections with pause markers in TTS prompt")
    lines.append("3. Accept current pacing if natural pauses exist elsewhere")
    lines.append("")

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate timing reports for audio editing')
    parser.add_argument('--chapter', type=str, help='Chapter number (01-12)')
    parser.add_argument('--all', action='store_true', help='Generate reports for all chapters')
    parser.add_argument('--timing-dir', type=Path, default=Path('output/timing/saltmere'),
                        help='Directory containing timing files')
    parser.add_argument('--stdout', action='store_true', help='Print to stdout instead of file')
    args = parser.parse_args()

    if not args.chapter and not args.all:
        parser.print_help()
        return

    # Find timing files
    if args.all:
        timing_files = sorted(args.timing_dir.glob('*-timing.json'))
    else:
        timing_files = list(args.timing_dir.glob(f'*{args.chapter}*-timing.json'))

    if not timing_files:
        print(f"No timing files found in {args.timing_dir}")
        print("Run align-timing.py first to generate timing data.")
        return

    for timing_file in timing_files:
        report = generate_report(timing_file)

        if args.stdout:
            print(report)
            print("\n" + "=" * 60 + "\n")
        else:
            report_file = timing_file.with_suffix('.md').with_stem(
                timing_file.stem.replace('-timing', '-report')
            )
            report_file.write_text(report)
            print(f"Generated: {report_file.name}")


if __name__ == '__main__':
    main()
