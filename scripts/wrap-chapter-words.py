#!/usr/bin/env python3
"""
Wrap words in chapter HTML with <span class="w"> elements.

This enables word-level highlighting by the JS engine.
Words are wrapped with data-i (index) attributes that align with
the word timing JSON indices from Whisper transcripts.

The script uses transcript words as the source of truth for word indices,
ensuring HTML spans match JSON timing data exactly.

Usage:
    python scripts/wrap-chapter-words.py           # Process all chapters
    python scripts/wrap-chapter-words.py --chapter 1  # Process chapter 1 only
    python scripts/wrap-chapter-words.py --dry-run    # Preview without writing
    python scripts/wrap-chapter-words.py --force      # Re-wrap even if already wrapped
"""

import argparse
import json
import re
import unicodedata
from pathlib import Path
from html.parser import HTMLParser
from html import escape, unescape


def normalize_word(word: str) -> str:
    """Normalize word for matching: lowercase, strip/remove punctuation."""
    # Decode HTML entities
    word = unescape(word)
    # Normalize unicode
    word = unicodedata.normalize('NFKC', word)
    # Lowercase
    word = word.lower()
    # Strip leading/trailing punctuation
    word = word.strip('.,;:!?"()[]{}—–-…\'"„""''«»')
    # Remove internal em-dashes and hyphens for matching
    # This helps match "literature—advection" with "literature" + "advection"
    word = word.replace('—', '').replace('–', '').replace('-', '')
    return word


def fuzzy_match(s1: str, s2: str) -> bool:
    """Check if two strings are similar enough (handles typos and spelling variants)."""
    if not s1 or not s2:
        return False
    if s1 == s2:
        return True

    # Common spelling variants (US/UK, etc.)
    spelling_variants = {
        ('gray', 'grey'), ('color', 'colour'), ('center', 'centre'),
        ('realize', 'realise'), ('analyze', 'analyse'),
    }
    if (s1, s2) in spelling_variants or (s2, s1) in spelling_variants:
        return True

    # Length check - too different means no match
    if abs(len(s1) - len(s2)) > max(len(s1), len(s2)) * 0.3:
        return False

    # For short words (<=4 chars), require higher similarity
    # For longer words, be more lenient
    min_len = min(len(s1), len(s2))
    threshold = 0.9 if min_len <= 4 else 0.75

    # Simple character overlap ratio
    common = sum(1 for c in s1 if c in s2)
    ratio = (2.0 * common) / (len(s1) + len(s2))
    return ratio >= threshold


def load_transcript_words(project_root: Path, chapter_num: int) -> list[str] | None:
    """Load word list from word timing JSON."""
    words_path = project_root / "site" / "js" / "words" / f"chapter-{chapter_num:02d}-words.json"
    if not words_path.exists():
        return None

    with open(words_path) as f:
        data = json.load(f)

    # Extract just the word text from [start, end, word] tuples
    return [w[2] for w in data.get("words", [])]


class TranscriptAlignedWrapper(HTMLParser):
    """
    HTML parser that wraps text words aligned to transcript indices.
    Uses fuzzy matching to handle minor differences between HTML text
    and Whisper transcript (e.g., em-dashes, smart quotes).

    Handles HTML entities (like &#x27; for apostrophe) by buffering text
    and processing complete words.
    """

    SKIP_TAGS = {'script', 'style', 'code', 'pre', 'span'}

    def __init__(self, transcript_words: list[str] | None = None):
        super().__init__()
        self.output = []
        self.transcript_words = transcript_words or []
        self.transcript_idx = 0
        self.tag_stack = []
        self.in_content_div = False
        self.skip_depth = 0
        self.content_div_depth = 0
        self.wrapped_count = 0
        self.mismatches = []
        # Buffer for accumulating text across entity boundaries
        self.text_buffer = ""

    def _flush_buffer(self):
        """Process accumulated text buffer and wrap words."""
        if self.text_buffer:
            if self.in_content_div and self.skip_depth == 0:
                self.output.append(self._wrap_words_aligned(self.text_buffer))
            else:
                # Don't escape outside content div - preserve original text
                self.output.append(self.text_buffer)
            self.text_buffer = ""

    def handle_starttag(self, tag, attrs):
        self._flush_buffer()  # Process any pending text

        attrs_str = ''.join(f' {k}="{escape(v)}"' if v else f' {k}'
                           for k, v in attrs)

        if tag == 'div':
            for k, v in attrs:
                if k == 'class' and v and 'content' in v.split():
                    self.in_content_div = True
                    self.content_div_depth = len(self.tag_stack) + 1

        self.tag_stack.append(tag)

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

        self.output.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag):
        self._flush_buffer()  # Process any pending text

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1

        if tag == 'div' and self.in_content_div:
            if len(self.tag_stack) < self.content_div_depth:
                self.in_content_div = False
                self.content_div_depth = 0

        self.output.append(f'</{tag}>')

    def handle_data(self, data):
        # Accumulate text (may be split by entities)
        self.text_buffer += data

    def handle_entityref(self, name):
        # Convert entity to character and add to buffer
        # Common entities: &amp; &lt; &gt; &quot; &apos;
        entities = {'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"', 'apos': "'", 'nbsp': ' '}
        char = entities.get(name, f'&{name};')
        self.text_buffer += char

    def handle_charref(self, name):
        # Convert character reference to character
        # e.g., &#x27; -> ' or &#39; -> '
        try:
            if name.startswith('x') or name.startswith('X'):
                char = chr(int(name[1:], 16))
            else:
                char = chr(int(name))
            self.text_buffer += char
        except (ValueError, OverflowError):
            self.text_buffer += f'&#{name};'

    def handle_comment(self, data):
        self._flush_buffer()
        self.output.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self._flush_buffer()
        self.output.append(f'<!{decl}>')

    def _find_matching_transcript_idx(self, html_word: str) -> tuple[int | None, int]:
        """
        Find transcript index that matches this HTML word.
        Returns (index, num_consumed) - num_consumed > 1 for compound words.
        """
        if self.transcript_idx >= len(self.transcript_words):
            return None, 0

        html_norm = normalize_word(html_word)
        if not html_norm:
            return None, 0

        # Try exact match at current position
        trans_norm = normalize_word(self.transcript_words[self.transcript_idx])
        if html_norm == trans_norm:
            self.consecutive_misses = 0
            return self.transcript_idx, 1

        # Try fuzzy match for typos (e.g., "advection" vs "advaction")
        if fuzzy_match(html_norm, trans_norm):
            self.consecutive_misses = 0
            return self.transcript_idx, 1

        # Try compound word match (HTML "treeline" = transcript "tree" + "line")
        # Check if joining 2-3 transcript words matches the HTML word
        for join_count in range(2, 4):
            if self.transcript_idx + join_count > len(self.transcript_words):
                break
            joined = ''.join(
                normalize_word(self.transcript_words[self.transcript_idx + i])
                for i in range(join_count)
            )
            if html_norm == joined or fuzzy_match(html_norm, joined):
                self.consecutive_misses = 0
                return self.transcript_idx, join_count

        # Try lookahead (transcript might have extra words we should skip)
        for offset in range(1, 6):
            if self.transcript_idx + offset >= len(self.transcript_words):
                break
            trans_norm = normalize_word(self.transcript_words[self.transcript_idx + offset])
            if html_norm == trans_norm or fuzzy_match(html_norm, trans_norm):
                # Skip the unmatched transcript words
                self.mismatches.append(f"Skipped transcript words {self.transcript_idx} to {self.transcript_idx + offset - 1}")
                self.transcript_idx += offset
                self.consecutive_misses = 0
                return self.transcript_idx, 1

        # Try partial match (HTML might combine words like "water—but")
        # Check if HTML word starts with transcript word
        if html_norm.startswith(trans_norm) and len(trans_norm) >= 3:
            self.consecutive_misses = 0
            return self.transcript_idx, 1

        # Track consecutive misses for resync
        self.consecutive_misses = getattr(self, 'consecutive_misses', 0) + 1

        # If too many consecutive misses, try to resync by searching ahead in transcript
        if self.consecutive_misses >= 3:
            for look in range(6, 20):
                if self.transcript_idx + look >= len(self.transcript_words):
                    break
                look_norm = normalize_word(self.transcript_words[self.transcript_idx + look])
                if html_norm == look_norm or fuzzy_match(html_norm, look_norm):
                    # Found resync point
                    self.mismatches.append(f"Resync: jumped transcript from {self.transcript_idx} to {self.transcript_idx + look}")
                    self.transcript_idx += look
                    self.consecutive_misses = 0
                    return self.transcript_idx, 1

        # No match found - this HTML word doesn't exist in transcript
        return None, 0

    def _wrap_words_aligned(self, text: str) -> str:
        """Wrap words aligned to transcript indices."""
        if not text.strip():
            return text

        result = []
        pattern = r'(\s*)(\S+)'

        pos = 0
        for match in re.finditer(pattern, text):
            if match.start() > pos:
                result.append(text[pos:match.start()])

            whitespace = match.group(1)
            word = match.group(2)

            result.append(whitespace)

            # Try to match with transcript
            match_idx, num_consumed = self._find_matching_transcript_idx(word)

            if match_idx is not None:
                result.append(f'<span class="w" data-i="{match_idx}">{escape(word)}</span>')
                self.transcript_idx += num_consumed  # May consume multiple for compounds
                self.wrapped_count += 1
            else:
                # No transcript match - wrap without index for consistency
                # but mark it so it won't interfere with timing
                result.append(f'<span class="w">{escape(word)}</span>')
                self.mismatches.append(f"No match for HTML word: '{word}'")

            pos = match.end()

        if pos < len(text):
            result.append(text[pos:])

        return ''.join(result)

    def get_output(self) -> str:
        self._flush_buffer()  # Flush any remaining text
        return ''.join(self.output)


class SimpleWordWrapper(HTMLParser):
    """Fallback wrapper when no transcript is available."""

    SKIP_TAGS = {'script', 'style', 'code', 'pre', 'span'}

    def __init__(self):
        super().__init__()
        self.output = []
        self.word_index = 0
        self.tag_stack = []
        self.in_content_div = False
        self.skip_depth = 0
        self.content_div_depth = 0
        self.text_buffer = ""

    def _flush_buffer(self):
        """Process accumulated text buffer and wrap words."""
        if self.text_buffer:
            if self.in_content_div and self.skip_depth == 0:
                self.output.append(self._wrap_words(self.text_buffer))
            else:
                # Don't escape outside content div - preserve original text
                self.output.append(self.text_buffer)
            self.text_buffer = ""

    def handle_starttag(self, tag, attrs):
        self._flush_buffer()

        attrs_str = ''.join(f' {k}="{escape(v)}"' if v else f' {k}'
                           for k, v in attrs)

        if tag == 'div':
            for k, v in attrs:
                if k == 'class' and v and 'content' in v.split():
                    self.in_content_div = True
                    self.content_div_depth = len(self.tag_stack) + 1

        self.tag_stack.append(tag)

        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

        self.output.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag):
        self._flush_buffer()

        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1

        if tag == 'div' and self.in_content_div:
            if len(self.tag_stack) < self.content_div_depth:
                self.in_content_div = False
                self.content_div_depth = 0

        self.output.append(f'</{tag}>')

    def handle_data(self, data):
        self.text_buffer += data

    def handle_entityref(self, name):
        entities = {'amp': '&', 'lt': '<', 'gt': '>', 'quot': '"', 'apos': "'", 'nbsp': ' '}
        self.text_buffer += entities.get(name, f'&{name};')

    def handle_charref(self, name):
        try:
            if name.startswith('x') or name.startswith('X'):
                self.text_buffer += chr(int(name[1:], 16))
            else:
                self.text_buffer += chr(int(name))
        except (ValueError, OverflowError):
            self.text_buffer += f'&#{name};'

    def handle_comment(self, data):
        self._flush_buffer()
        self.output.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self._flush_buffer()
        self.output.append(f'<!{decl}>')

    def _wrap_words(self, text: str) -> str:
        if not text.strip():
            return text

        result = []
        pattern = r'(\s*)(\S+)'

        pos = 0
        for match in re.finditer(pattern, text):
            if match.start() > pos:
                result.append(text[pos:match.start()])

            whitespace = match.group(1)
            word = match.group(2)

            result.append(whitespace)
            result.append(f'<span class="w" data-i="{self.word_index}">{escape(word)}</span>')
            self.word_index += 1

            pos = match.end()

        if pos < len(text):
            result.append(text[pos:])

        return ''.join(result)

    def get_output(self) -> str:
        self._flush_buffer()
        return ''.join(self.output)


def unwrap_chapter_html(html_content: str) -> str:
    """Remove existing word span wrappers from HTML."""
    # Remove <span class="w" data-i="N"> and </span> while keeping inner text
    # Pattern handles optional data-i attribute
    unwrapped = re.sub(r'<span class="w"(?: data-i="\d+")?>', '', html_content)
    # Remove the closing spans (be careful to only remove the ones we added)
    # This is tricky - we need to count properly. Simpler approach: process sequentially
    # Actually, since we're replacing opening tags, we need to remove equal closing tags

    # Count how many we removed
    removed_count = html_content.count('<span class="w"')

    # Remove that many </span> tags from the content div area
    # For safety, just remove all </span> that follow our word spans
    # This is a simplified approach - in practice, the structure is predictable

    # Better approach: use regex to remove span+content+/span as a unit
    unwrapped = re.sub(r'<span class="w"(?: data-i="\d+")?>(.*?)</span>', r'\1', html_content)

    return unwrapped


def extract_chapter_num(filename: str) -> int | None:
    """Extract chapter number from filename."""
    match = re.search(r'chapter-(\d+)', filename)
    return int(match.group(1)) if match else None


def process_chapter(chapter_path: Path, project_root: Path, dry_run: bool = False, force: bool = False) -> dict:
    """Process a single chapter file. Returns stats dict."""
    content = chapter_path.read_text()
    chapter_num = extract_chapter_num(chapter_path.name)

    stats = {
        "file": chapter_path.name,
        "chapter": chapter_num,
        "wrapped": 0,
        "transcript_words": 0,
        "mismatches": [],
        "status": "skipped"
    }

    # Check if already wrapped
    already_wrapped = 'class="w"' in content

    if already_wrapped and not force:
        print(f"  Skipped: {chapter_path.name} (already wrapped, use --force to re-wrap)")
        return stats

    # Unwrap if forcing re-wrap
    if already_wrapped and force:
        content = unwrap_chapter_html(content)
        print(f"  Unwrapped: {chapter_path.name}")

    # Load transcript words for alignment
    transcript_words = None
    if chapter_num:
        transcript_words = load_transcript_words(project_root, chapter_num)
        if transcript_words:
            stats["transcript_words"] = len(transcript_words)
            print(f"  Loaded {len(transcript_words)} transcript words for chapter {chapter_num}")

    # Wrap with appropriate method
    if transcript_words:
        wrapper = TranscriptAlignedWrapper(transcript_words)
        wrapper.feed(content)
        wrapped = wrapper.get_output()
        stats["wrapped"] = wrapper.wrapped_count
        stats["mismatches"] = wrapper.mismatches[:10]  # First 10 only
        if wrapper.mismatches:
            print(f"  Warning: {len(wrapper.mismatches)} alignment mismatches")
    else:
        wrapper = SimpleWordWrapper()
        wrapper.feed(content)
        wrapped = wrapper.get_output()
        stats["wrapped"] = wrapper.word_index
        print(f"  Note: No transcript available, using simple wrapping")

    if not dry_run:
        chapter_path.write_text(wrapped)
        stats["status"] = "wrapped"
        print(f"  Wrapped: {chapter_path.name} ({stats['wrapped']} words)")
    else:
        stats["status"] = "would_wrap"
        print(f"  Would wrap: {chapter_path.name} ({stats['wrapped']} words)")

    return stats


def main():
    parser = argparse.ArgumentParser(description="Wrap chapter words for highlighting")
    parser.add_argument("--chapter", "-c", type=int, help="Process only this chapter number")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview without writing")
    parser.add_argument("--force", "-f", action="store_true", help="Re-wrap even if already wrapped")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    read_dir = project_root / "site" / "read"

    if args.chapter:
        pattern = f"chapter-{args.chapter:02d}-*.html"
    else:
        pattern = "chapter-*.html"

    chapter_files = sorted(read_dir.glob(pattern))

    if not chapter_files:
        print(f"No chapter files found matching {pattern}")
        return

    flags = []
    if args.dry_run:
        flags.append("dry run")
    if args.force:
        flags.append("force")
    flag_str = f" ({', '.join(flags)})" if flags else ""

    print(f"Processing {len(chapter_files)} chapter(s)...{flag_str}")

    all_stats = []
    for chapter_path in chapter_files:
        stats = process_chapter(chapter_path, project_root, args.dry_run, args.force)
        all_stats.append(stats)

    # Summary
    total_wrapped = sum(s["wrapped"] for s in all_stats)
    total_mismatches = sum(len(s["mismatches"]) for s in all_stats)

    print(f"\nDone. Total words wrapped: {total_wrapped}")
    if total_mismatches:
        print(f"Total alignment mismatches: {total_mismatches}")


if __name__ == "__main__":
    main()
