#!/usr/bin/env python3
"""
Add end-of-chapter feedback forms to chapters 1-7.
"""
from pathlib import Path
import re

SITE_DIR = Path(__file__).parent.parent / "site"
READ_DIR = SITE_DIR / "read"

# Feedback prompts for each chapter
FEEDBACK_PROMPTS = {
    1: {
        "question": "Sarah tells herself she's here for science. Did you believe her?",
        "options": [
            ("yes", "Yes, she's professional"),
            ("no", "No, she's searching for answers"),
            ("both", "Both, and she knows it")
        ]
    },
    2: {
        "question": "Margaret says she doesn't remember. Does her silence feel protective or guilty?",
        "options": [
            ("protective", "Protective"),
            ("guilty", "Guilty"),
            ("both", "Both")
        ]
    },
    3: {
        "question": "Thomas almost says something, then stops. What was he holding back?",
        "options": [
            ("warning", "A warning"),
            ("truth", "A difficult truth"),
            ("memory", "A painful memory")
        ]
    },
    4: {
        "question": "Edith kept copies for fifty years. Wisdom or cowardice?",
        "options": [
            ("wisdom", "Wisdom"),
            ("cowardice", "Cowardice"),
            ("survival", "Survival")
        ]
    },
    5: {
        "question": "The waterfront yields clues. What surprised you most?",
        "options": [
            ("physical", "The physical evidence"),
            ("silence", "The town's silence"),
            ("sarah", "Sarah's reaction")
        ]
    },
    6: {
        "question": "The weight of truth settles. Did you see it coming?",
        "options": [
            ("yes", "Yes, the signs were there"),
            ("no", "No, I was surprised"),
            ("suspected", "I suspected something different")
        ]
    },
    7: {
        "question": "Eleanor warns Sarah. Truth vs. consequences—whose side are you on?",
        "options": [
            ("truth", "Truth must come out"),
            ("peace", "Some things stay buried"),
            ("complicated", "It's more complicated")
        ]
    }
}

def generate_feedback_html(chapter_num: int) -> str:
    """Generate the feedback form HTML for a chapter."""
    if chapter_num not in FEEDBACK_PROMPTS:
        return ""

    prompt = FEEDBACK_PROMPTS[chapter_num]
    options_html = "\n                        ".join([
        f'<button type="submit" name="response" value="{val}">{label}</button>'
        for val, label in prompt["options"]
    ])

    return f'''
            <div class="chapter-feedback">
                <p class="feedback-prompt">{prompt["question"]}</p>
                <form name="feedback-ch{chapter_num:02d}" method="POST" data-netlify="true" netlify-honeypot="bot-field">
                    <input type="hidden" name="form-name" value="feedback-ch{chapter_num:02d}">
                    <input type="hidden" name="bot-field">
                    <input type="hidden" name="chapter" value="{chapter_num}">
                    <div class="feedback-options">
                        {options_html}
                    </div>
                    <textarea name="note" placeholder="What stayed with you? (optional)"></textarea>
                </form>
            </div>
'''

def update_chapter_file(filepath: Path, chapter_num: int) -> bool:
    """Add feedback form to a chapter file if needed."""
    content = filepath.read_text()

    # Skip if already has feedback
    if 'chapter-feedback' in content:
        return False

    # Only add to chapters 1-7
    if chapter_num not in FEEDBACK_PROMPTS:
        return False

    feedback_html = generate_feedback_html(chapter_num)

    # Find the "End of Chapter X" marker and insert feedback before navigation
    # Pattern: <p><em>End of Chapter X</em></p>
    end_pattern = r'(<p><em>End of Chapter \d+</em></p>\s*<hr>)'

    if re.search(end_pattern, content):
        content = re.sub(
            end_pattern,
            r'\1' + feedback_html,
            content
        )
    else:
        # Fallback: insert before navigation div
        content = content.replace(
            '<div class="navigation">',
            feedback_html + '\n        <div class="navigation">'
        )

    filepath.write_text(content)
    return True

def main():
    """Add feedback forms to chapter files."""
    print("Adding feedback forms to chapters 1-7...")

    for chapter_num in range(1, 13):
        ch_str = str(chapter_num).zfill(2)
        # Find the chapter file
        chapter_files = list(READ_DIR.glob(f"chapter-{ch_str}-*.html"))
        if not chapter_files:
            print(f"  Chapter {chapter_num}: file not found")
            continue

        filepath = chapter_files[0]
        if update_chapter_file(filepath, chapter_num):
            print(f"  Chapter {chapter_num}: added feedback form")
        else:
            if chapter_num <= 7:
                print(f"  Chapter {chapter_num}: already has feedback or skipped")
            else:
                print(f"  Chapter {chapter_num}: no feedback (chapters 8-12)")

    print("\nDone.")

if __name__ == "__main__":
    main()
