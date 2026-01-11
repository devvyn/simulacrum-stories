#!/usr/bin/env python3
"""
Generate podcast RSS feed for The Saltmere Chronicles.

Creates a proper podcast feed with:
- Full chapter metadata
- Cover art
- iTunes-compatible tags
- Correct durations and file sizes

Usage:
    python scripts/generate-podcast-feed.py --base-url https://your-site.app
"""

import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


# Chapter metadata
CHAPTERS = [
    {"num": "01", "title": "The Research Station",
     "description": "A marine biologist arrives at a remote research station on the Pacific Northwest coast."},
    {"num": "02", "title": "The Harbor Master",
     "description": "Sarah meets Margaret Holloway and receives her first warning from Eleanor Cross."},
    {"num": "03", "title": "First Samples",
     "description": "Out on the water with Thomas Breck, Sarah begins to understand what Saltmere is hiding."},
    {"num": "04", "title": "The Librarian's Archive",
     "description": "Edith Pemberton has kept copies for fifty years, waiting for someone brave enough to use them."},
    {"num": "05", "title": "The Waterfront Discovery",
     "description": "Thomas finds something in the harbor that changes everything."},
    {"num": "06", "title": "The Weight of Truth",
     "description": "Margaret makes a choice, and Sarah discovers what it costs."},
    {"num": "07", "title": "Eleanor's Warning",
     "description": "A summons to tea. A philosophy of necessary evil. A line drawn."},
]

PODCAST_METADATA = {
    "title": "The Saltmere Chronicles",
    "description": "A marine biologist returns to the town where her grandmother vanished fifty years ago. What she finds in the water is poison. What she finds in the town is silence. A 12-chapter literary mystery about generational secrets, environmental crime, and the weight of complicity.",
    "author": "Simulacrum Stories",
    "email": "podcast@simulacrum.stories",
    "language": "en-us",
    "category": "Fiction",
    "subcategory": "Drama",
    "explicit": "no",
    "type": "serial",
}


def get_file_info(path: Path) -> tuple:
    """Get file size and duration."""
    import subprocess

    size = path.stat().st_size

    result = subprocess.run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(path)
    ], capture_output=True, text=True)

    duration_secs = float(result.stdout.strip())

    # Format as HH:MM:SS
    hours = int(duration_secs // 3600)
    minutes = int((duration_secs % 3600) // 60)
    seconds = int(duration_secs % 60)

    if hours > 0:
        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
    else:
        duration_str = f"{minutes}:{seconds:02d}"

    return size, duration_str


def generate_guid(title: str, num: str) -> str:
    """Generate a stable GUID for an episode."""
    content = f"saltmere-{num}-{title}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def create_feed(base_url: str, audio_dir: Path, output_path: Path, cover_url: str):
    """Create the podcast RSS feed."""

    # iTunes namespace
    ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    ATOM_NS = "http://www.w3.org/2005/Atom"
    CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"

    # Root element with namespaces
    rss = Element('rss', {
        'version': '2.0',
        'xmlns:itunes': ITUNES_NS,
        'xmlns:atom': ATOM_NS,
        'xmlns:content': CONTENT_NS,
    })

    channel = SubElement(rss, 'channel')

    # Channel metadata
    SubElement(channel, 'title').text = PODCAST_METADATA['title']
    SubElement(channel, 'description').text = PODCAST_METADATA['description']
    SubElement(channel, 'language').text = PODCAST_METADATA['language']
    SubElement(channel, 'link').text = base_url
    SubElement(channel, 'generator').text = 'Simulacrum Podcast Generator'
    SubElement(channel, 'lastBuildDate').text = datetime.now(timezone.utc).strftime('%a, %d %b %Y %H:%M:%S %z')

    # Atom self link
    atom_link = SubElement(channel, '{%s}link' % ATOM_NS)
    atom_link.set('href', f"{base_url}/feeds/saltmere-chronicles.xml")
    atom_link.set('rel', 'self')
    atom_link.set('type', 'application/rss+xml')

    # iTunes channel tags
    SubElement(channel, '{%s}author' % ITUNES_NS).text = PODCAST_METADATA['author']
    SubElement(channel, '{%s}summary' % ITUNES_NS).text = PODCAST_METADATA['description']
    SubElement(channel, '{%s}explicit' % ITUNES_NS).text = PODCAST_METADATA['explicit']
    SubElement(channel, '{%s}type' % ITUNES_NS).text = PODCAST_METADATA['type']

    # Image
    image = SubElement(channel, 'image')
    SubElement(image, 'url').text = cover_url
    SubElement(image, 'title').text = PODCAST_METADATA['title']
    SubElement(image, 'link').text = base_url

    SubElement(channel, '{%s}image' % ITUNES_NS).set('href', cover_url)

    # Category
    category = SubElement(channel, '{%s}category' % ITUNES_NS)
    category.set('text', PODCAST_METADATA['category'])
    subcategory = SubElement(category, '{%s}category' % ITUNES_NS)
    subcategory.set('text', PODCAST_METADATA['subcategory'])

    # Owner
    owner = SubElement(channel, '{%s}owner' % ITUNES_NS)
    SubElement(owner, '{%s}name' % ITUNES_NS).text = PODCAST_METADATA['author']
    SubElement(owner, '{%s}email' % ITUNES_NS).text = PODCAST_METADATA['email']

    # Episodes (in reverse order for podcast apps)
    pub_date = datetime.now(timezone.utc)

    for chapter in reversed(CHAPTERS):
        # Find audio file
        audio_file = audio_dir / f"{chapter['num']} - {chapter['title']}.mp3"
        if not audio_file.exists():
            print(f"  Skipping {chapter['num']}: file not found")
            continue

        size, duration = get_file_info(audio_file)

        # Episode URL
        filename = audio_file.name.replace(' ', '%20')
        episode_url = f"{base_url}/audio/saltmere-chronicles/{filename}"

        item = SubElement(channel, 'item')

        title = f"Chapter {int(chapter['num'])}: {chapter['title']}"
        SubElement(item, 'title').text = title
        SubElement(item, 'description').text = chapter['description']
        SubElement(item, 'pubDate').text = pub_date.strftime('%a, %d %b %Y %H:%M:%S %z')
        SubElement(item, 'guid').text = generate_guid(chapter['title'], chapter['num'])

        enclosure = SubElement(item, 'enclosure')
        enclosure.set('url', episode_url)
        enclosure.set('length', str(size))
        enclosure.set('type', 'audio/mpeg')

        # iTunes episode tags
        SubElement(item, '{%s}title' % ITUNES_NS).text = title
        SubElement(item, '{%s}summary' % ITUNES_NS).text = chapter['description']
        SubElement(item, '{%s}episodeType' % ITUNES_NS).text = 'full'
        SubElement(item, '{%s}episode' % ITUNES_NS).text = chapter['num']
        SubElement(item, '{%s}season' % ITUNES_NS).text = '1'
        SubElement(item, '{%s}explicit' % ITUNES_NS).text = 'no'
        SubElement(item, '{%s}duration' % ITUNES_NS).text = duration

        print(f"  Added: Chapter {chapter['num']} ({duration})")

        # Stagger pub dates by 1 day
        from datetime import timedelta
        pub_date = pub_date - timedelta(days=1)

    # Pretty print
    xml_str = tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent='  ')

    # Remove extra blank lines
    lines = [line for line in pretty_xml.split('\n') if line.strip()]
    final_xml = '\n'.join(lines)

    output_path.write_text(final_xml)
    print(f"\nFeed saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate podcast RSS feed')
    parser.add_argument('--base-url', type=str, default='https://saltmere-chronicles.netlify.app',
                        help='Base URL for the podcast site')
    parser.add_argument('--audio-dir', type=Path, default=Path('output/distribution/mp3'),
                        help='Directory containing MP3 files')
    parser.add_argument('--output', type=Path, default=Path('output/distribution/podcast-feed.xml'),
                        help='Output path for RSS feed')
    args = parser.parse_args()

    cover_url = f"{args.base_url}/audio/saltmere-chronicles/cover.jpg"

    print("=== Generating Podcast Feed ===")
    print(f"Base URL: {args.base_url}")
    print(f"Audio dir: {args.audio_dir}")
    print()

    create_feed(args.base_url, args.audio_dir, args.output, cover_url)


if __name__ == '__main__':
    main()
