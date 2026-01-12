#!/usr/bin/env python3
"""
Wrap words in chapter HTML with <span class="w"> elements.

This enables word-level highlighting by the JS engine.
Words are wrapped with data-i (index) attributes.
Timestamps are loaded separately by JS from word timing JSONs.

Usage:
    python scripts/wrap-chapter-words.py           # Process all chapters
    python scripts/wrap-chapter-words.py --chapter 1  # Process chapter 1 only
    python scripts/wrap-chapter-words.py --dry-run    # Preview without writing
"""

import argparse
import re
from pathlib import Path
from html.parser import HTMLParser
from html import escape


class WordWrapper(HTMLParser):
    """
    HTML parser that wraps text words in <span class="w"> elements.
    Preserves all existing HTML structure.
    """

    # Tags whose content should not be word-wrapped
    SKIP_TAGS = {'script', 'style', 'code', 'pre', 'span'}

    # Tags that are inline (don't break words)
    INLINE_TAGS = {'a', 'em', 'strong', 'b', 'i', 'u', 'mark', 'small', 'sub', 'sup'}

    def __init__(self, in_content_div=False):
        super().__init__()
        self.output = []
        self.word_index = 0
        self.tag_stack = []
        self.in_content_div = in_content_div
        self.skip_depth = 0
        self.content_div_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_str = ''.join(f' {k}="{escape(v)}"' if v else f' {k}'
                           for k, v in attrs)

        # Track if we're entering the content div
        if tag == 'div':
            for k, v in attrs:
                if k == 'class' and v and 'content' in v.split():
                    self.in_content_div = True
                    self.content_div_depth = len(self.tag_stack) + 1

        self.tag_stack.append(tag)

        # Track skip depth for script/style/etc
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1

        # Handle self-closing tags
        if tag in ('br', 'hr', 'img', 'input', 'meta', 'link'):
            self.output.append(f'<{tag}{attrs_str}>')
        else:
            self.output.append(f'<{tag}{attrs_str}>')

    def handle_endtag(self, tag):
        if self.tag_stack and self.tag_stack[-1] == tag:
            self.tag_stack.pop()

        if tag in self.SKIP_TAGS and self.skip_depth > 0:
            self.skip_depth -= 1

        # Check if we're exiting the content div
        if tag == 'div' and self.in_content_div:
            if len(self.tag_stack) < self.content_div_depth:
                self.in_content_div = False
                self.content_div_depth = 0

        self.output.append(f'</{tag}>')

    def handle_data(self, data):
        # Only wrap words inside the content div, and not in skip tags
        if self.in_content_div and self.skip_depth == 0:
            self.output.append(self._wrap_words(data))
        else:
            self.output.append(data)

    def handle_entityref(self, name):
        self.output.append(f'&{name};')

    def handle_charref(self, name):
        self.output.append(f'&#{name};')

    def handle_comment(self, data):
        self.output.append(f'<!--{data}-->')

    def handle_decl(self, decl):
        self.output.append(f'<!{decl}>')

    def _wrap_words(self, text: str) -> str:
        """Wrap each word in a span with word index."""
        if not text.strip():
            return text

        result = []
        # Split while preserving whitespace
        # Pattern: (whitespace)(word)(whitespace)...
        pattern = r'(\s*)(\S+)'

        pos = 0
        for match in re.finditer(pattern, text):
            # Add any text before this match (shouldn't happen with this pattern)
            if match.start() > pos:
                result.append(text[pos:match.start()])

            whitespace = match.group(1)
            word = match.group(2)

            result.append(whitespace)
            result.append(f'<span class="w" data-i="{self.word_index}">{escape(word)}</span>')
            self.word_index += 1

            pos = match.end()

        # Add any trailing text
        if pos < len(text):
            result.append(text[pos:])

        return ''.join(result)

    def get_output(self) -> str:
        return ''.join(self.output)


def wrap_chapter_html(html_content: str) -> tuple[str, int]:
    """
    Wrap words in chapter HTML content.
    Returns (wrapped_html, word_count).
    """
    wrapper = WordWrapper()
    wrapper.feed(html_content)
    return wrapper.get_output(), wrapper.word_index


def process_chapter(chapter_path: Path, dry_run: bool = False) -> int:
    """Process a single chapter file. Returns word count."""
    content = chapter_path.read_text()

    # Skip if already wrapped
    if 'class="w"' in content:
        print(f"  Skipped: {chapter_path.name} (already wrapped)")
        return 0

    wrapped, word_count = wrap_chapter_html(content)

    if not dry_run:
        chapter_path.write_text(wrapped)
        print(f"  Wrapped: {chapter_path.name} ({word_count} words)")
    else:
        print(f"  Would wrap: {chapter_path.name} ({word_count} words)")

    return word_count


def main():
    parser = argparse.ArgumentParser(description="Wrap chapter words for highlighting")
    parser.add_argument("--chapter", "-c", type=int, help="Process only this chapter number")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Preview without writing")
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

    print(f"Processing {len(chapter_files)} chapter(s)..." + (" (dry run)" if args.dry_run else ""))

    total_words = 0
    for chapter_path in chapter_files:
        total_words += process_chapter(chapter_path, args.dry_run)

    print(f"\nDone. Total words wrapped: {total_words}")


if __name__ == "__main__":
    main()
