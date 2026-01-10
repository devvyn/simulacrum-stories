#!/usr/bin/env python3
"""
Generate HTML reading pages from manuscript markdown files.
"""

import re
from pathlib import Path
import html

PROJECT_ROOT = Path(__file__).parent.parent
MANUSCRIPT_DIR = PROJECT_ROOT / "manuscript" / "saltmere"
SITE_DIR = PROJECT_ROOT / "site"
READ_DIR = SITE_DIR / "read"

# Chapter order and metadata
CHAPTERS = [
    ("chapter-01-the-research-station.md", "Chapter 1", "The Research Station"),
    ("chapter-02-the-harbor-master.md", "Chapter 2", "The Harbor Master"),
    ("chapter-03-first-samples.md", "Chapter 3", "First Samples"),
    ("chapter-04-the-librarians-archive.md", "Chapter 4", "The Librarian's Archive"),
    ("chapter-05-the-waterfront-discovery.md", "Chapter 5", "The Waterfront Discovery"),
    ("chapter-06-the-weight-of-truth.md", "Chapter 6", "The Weight of Truth"),
    ("chapter-07-eleanors-warning.md", "Chapter 7", "Eleanor's Warning"),
    ("chapter-08-the-old-cannery.md", "Chapter 8", "The Old Cannery"),
    ("chapter-09-the-reckoning.md", "Chapter 9", "The Reckoning"),
    ("chapter-10-what-rises.md", "Chapter 10", "What Rises"),
    ("chapter-11-what-surfaces.md", "Chapter 11", "What Surfaces"),
    ("chapter-12-the-tide-goes-out.md", "Chapter 12", "The Tide Goes Out"),
]

VIGNETTES = [
    ("vignette-a-thomas-and-the-nets.md", "Vignette", "Thomas and the Nets"),
    ("vignette-b-eleanors-diary.md", "Vignette", "Eleanor's Diary, 1962"),
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | The Saltmere Chronicles</title>
    <meta name="description" content="{description}">
    <style>
        :root {{
            --deep-water: #1a2a3a;
            --grey-green: #3a4a4a;
            --driftwood: #8a7a6a;
            --salt-white: #f0f2f4;
            --fog: rgba(180, 190, 195, 0.1);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', serif;
            background: var(--deep-water);
            color: var(--salt-white);
            line-height: 1.8;
            font-size: 18px;
        }}

        header {{
            background: rgba(0,0,0,0.3);
            padding: 1rem 2rem;
            position: sticky;
            top: 0;
            z-index: 100;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        header a {{
            color: var(--salt-white);
            text-decoration: none;
            opacity: 0.8;
        }}

        header a:hover {{
            opacity: 1;
        }}

        .site-title {{
            font-size: 1.2rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }}

        nav a {{
            margin-left: 1.5rem;
            font-size: 0.9rem;
        }}

        main {{
            max-width: 700px;
            margin: 0 auto;
            padding: 3rem 2rem 5rem;
        }}

        .chapter-header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--driftwood);
        }}

        .chapter-number {{
            font-size: 0.9rem;
            letter-spacing: 0.3em;
            text-transform: uppercase;
            opacity: 0.6;
            margin-bottom: 0.5rem;
        }}

        .chapter-title {{
            font-size: 2rem;
            font-weight: normal;
            font-style: italic;
        }}

        .content p {{
            margin-bottom: 1.5rem;
            text-align: justify;
            hyphens: auto;
        }}

        .content hr {{
            border: none;
            text-align: center;
            margin: 2.5rem 0;
        }}

        .content hr::before {{
            content: "* * *";
            color: var(--driftwood);
            letter-spacing: 0.5em;
        }}

        .navigation {{
            display: flex;
            justify-content: space-between;
            margin-top: 4rem;
            padding-top: 2rem;
            border-top: 1px solid var(--driftwood);
        }}

        .navigation a {{
            color: var(--salt-white);
            text-decoration: none;
            opacity: 0.7;
            font-size: 0.9rem;
        }}

        .navigation a:hover {{
            opacity: 1;
        }}

        .nav-disabled {{
            opacity: 0.3;
            pointer-events: none;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            opacity: 0.5;
            font-size: 0.8rem;
        }}

        @media (max-width: 600px) {{
            body {{
                font-size: 16px;
            }}
            main {{
                padding: 2rem 1.5rem 4rem;
            }}
            .chapter-title {{
                font-size: 1.5rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <a href="/" class="site-title">Saltmere</a>
        <nav>
            <a href="/read/">All Chapters</a>
            <a href="/#listen">Listen</a>
            <a href="/#explore">Explore</a>
        </nav>
    </header>

    <main>
        <div class="chapter-header">
            <div class="chapter-number">{chapter_number}</div>
            <h1 class="chapter-title">{chapter_title}</h1>
        </div>

        <div class="content">
{content}
        </div>

        <div class="navigation">
            {prev_link}
            {next_link}
        </div>
    </main>

    <footer>
        The Saltmere Chronicles
    </footer>
</body>
</html>
"""

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Read | The Saltmere Chronicles</title>
    <meta name="description" content="Read The Saltmere Chronicles - a literary mystery about generational secrets and environmental crime.">
    <style>
        :root {{
            --deep-water: #1a2a3a;
            --grey-green: #3a4a4a;
            --driftwood: #8a7a6a;
            --salt-white: #f0f2f4;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Georgia', serif;
            background: var(--deep-water);
            color: var(--salt-white);
            line-height: 1.7;
        }}

        header {{
            background: rgba(0,0,0,0.3);
            padding: 1rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        header a {{
            color: var(--salt-white);
            text-decoration: none;
            opacity: 0.8;
        }}

        header a:hover {{
            opacity: 1;
        }}

        .site-title {{
            font-size: 1.2rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
        }}

        nav a {{
            margin-left: 1.5rem;
            font-size: 0.9rem;
        }}

        main {{
            max-width: 700px;
            margin: 0 auto;
            padding: 3rem 2rem 5rem;
        }}

        h1 {{
            font-size: 2rem;
            font-weight: normal;
            margin-bottom: 1rem;
            letter-spacing: 0.1em;
        }}

        .intro {{
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 1px solid var(--driftwood);
            opacity: 0.8;
        }}

        .chapter-list {{
            list-style: none;
        }}

        .chapter-list li {{
            margin-bottom: 1rem;
        }}

        .chapter-list a {{
            color: var(--salt-white);
            text-decoration: none;
            display: block;
            padding: 1rem;
            background: rgba(0,0,0,0.2);
            border-left: 3px solid transparent;
            transition: all 0.2s ease;
        }}

        .chapter-list a:hover {{
            background: rgba(0,0,0,0.3);
            border-left-color: var(--driftwood);
        }}

        .chapter-num {{
            font-size: 0.8rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            opacity: 0.6;
        }}

        .chapter-name {{
            font-size: 1.1rem;
            font-style: italic;
        }}

        .section-title {{
            font-size: 0.9rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            margin: 3rem 0 1.5rem;
            opacity: 0.6;
        }}

        footer {{
            text-align: center;
            padding: 2rem;
            opacity: 0.5;
            font-size: 0.8rem;
        }}
    </style>
</head>
<body>
    <header>
        <a href="/" class="site-title">Saltmere</a>
        <nav>
            <a href="/#listen">Listen</a>
            <a href="/#explore">Explore</a>
            <a href="/#about">About</a>
        </nav>
    </header>

    <main>
        <h1>Read the Chronicles</h1>
        <p class="intro">
            A marine biologist returns to the town where her grandmother vanished fifty years ago.
            What she finds in the water is poison. What she finds in the town is silence.
        </p>

        <h2 class="section-title">The Novella</h2>
        <ul class="chapter-list">
{chapter_links}
        </ul>

        <h2 class="section-title">Vignettes</h2>
        <ul class="chapter-list">
{vignette_links}
        </ul>
    </main>

    <footer>
        The Saltmere Chronicles
    </footer>
</body>
</html>
"""


def markdown_to_html(md_text: str) -> str:
    """Convert simple markdown to HTML paragraphs."""
    # Remove the chapter title header
    md_text = re.sub(r'^# .+\n+', '', md_text)

    # Remove editorial notes section
    md_text = re.sub(r'\*\*Editorial Notes:\*\*.*$', '', md_text, flags=re.DOTALL)

    # Convert horizontal rules
    md_text = re.sub(r'^---+$', '<hr>', md_text, flags=re.MULTILINE)

    # Convert bold
    md_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', md_text)

    # Convert italic
    md_text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', md_text)

    # Split into paragraphs
    paragraphs = md_text.strip().split('\n\n')

    html_parts = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para == '<hr>':
            html_parts.append('            <hr>')
        else:
            # Clean up any remaining newlines within paragraphs
            para = re.sub(r'\n', ' ', para)
            html_parts.append(f'            <p>{para}</p>')

    return '\n'.join(html_parts)


def generate_chapter_page(filename: str, chapter_num: str, chapter_title: str,
                          prev_link: str, next_link: str) -> str:
    """Generate HTML for a chapter page."""
    md_path = MANUSCRIPT_DIR / filename
    md_text = md_path.read_text()

    content = markdown_to_html(md_text)

    # Build navigation links
    if prev_link:
        prev_html = f'<a href="{prev_link}">← Previous</a>'
    else:
        prev_html = '<span class="nav-disabled">← Previous</span>'

    if next_link:
        next_html = f'<a href="{next_link}">Next →</a>'
    else:
        next_html = '<span class="nav-disabled">Next →</span>'

    return HTML_TEMPLATE.format(
        title=f"{chapter_num}: {chapter_title}",
        description=f"Read {chapter_num}: {chapter_title} from The Saltmere Chronicles",
        chapter_number=chapter_num,
        chapter_title=chapter_title,
        content=content,
        prev_link=prev_html,
        next_link=next_html,
    )


def generate_index_page() -> str:
    """Generate the chapter index page."""
    chapter_links = []
    for filename, num, title in CHAPTERS:
        slug = filename.replace('.md', '.html')
        chapter_links.append(f'''            <li>
                <a href="{slug}">
                    <span class="chapter-num">{num}</span><br>
                    <span class="chapter-name">{title}</span>
                </a>
            </li>''')

    vignette_links = []
    for filename, num, title in VIGNETTES:
        slug = filename.replace('.md', '.html')
        vignette_links.append(f'''            <li>
                <a href="{slug}">
                    <span class="chapter-num">{num}</span><br>
                    <span class="chapter-name">{title}</span>
                </a>
            </li>''')

    return INDEX_TEMPLATE.format(
        chapter_links='\n'.join(chapter_links),
        vignette_links='\n'.join(vignette_links),
    )


def main():
    READ_DIR.mkdir(parents=True, exist_ok=True)

    # Generate chapter pages
    all_items = CHAPTERS + VIGNETTES
    for i, (filename, num, title) in enumerate(all_items):
        # Determine prev/next links
        prev_link = None
        next_link = None

        if i > 0:
            prev_file = all_items[i-1][0].replace('.md', '.html')
            prev_link = prev_file

        if i < len(all_items) - 1:
            next_file = all_items[i+1][0].replace('.md', '.html')
            next_link = next_file

        html_content = generate_chapter_page(filename, num, title, prev_link, next_link)

        output_path = READ_DIR / filename.replace('.md', '.html')
        output_path.write_text(html_content)
        print(f"Generated: {output_path.name}")

    # Generate index page
    index_html = generate_index_page()
    (READ_DIR / 'index.html').write_text(index_html)
    print("Generated: index.html")

    print(f"\nDone! {len(all_items) + 1} pages generated in {READ_DIR}")


if __name__ == '__main__':
    main()
