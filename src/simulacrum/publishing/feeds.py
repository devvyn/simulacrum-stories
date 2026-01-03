#!/usr/bin/env python3
"""
Podcast Feed Generator for Simulacrum Series

Generates podcast-compatible RSS feeds that work with Pocket Casts,
Apple Podcasts, Overcast, and other podcatchers.

Usage:
    # Generate feed for a series
    ./podcast_feed.py --series millbrook --base-url http://localhost:8000

    # Generate all feeds
    ./podcast_feed.py --all --base-url http://localhost:8000

    # Start local podcast server
    ./podcast_feed.py --serve --port 8000

    # Generate and serve (one command)
    ./podcast_feed.py --all --serve --port 8000
"""

import argparse
import hashlib
import http.server
import socketserver
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from xml.dom import minidom

# =============================================================================
# Configuration
# =============================================================================

SERIES_REGISTRY = (
    Path.home() / "devvyn-meta-project" / "data" / "simulacrum-series.json"
)
PODCAST_DIR = Path.home() / "Music" / "Simulacrum-Stories"
FEED_DIR = PODCAST_DIR / "_feeds"

AUTHOR = "Simulacrum Stories"
AUTHOR_EMAIL = "podcast@devvyn.ca"
LANGUAGE = "en-us"
CATEGORY = "Fiction"
SUBCATEGORY = "Drama"

# Rich series descriptions
SERIES_DESCRIPTIONS = {
    "millbrook-chronicles": {
        "title": "The Millbrook Chronicles",
        "subtitle": "Small Town Secrets, Big Town Lies",
        "description": """A small industrial town in 1950s Midwest America harbors dark secrets beneath its wholesome facade. When evidence from a devastating mill fire resurfaces, Sheriff Frank Donovan must confront the town's buried past while navigating a web of lies that reaches into every corner of Millbrook.

Through rotating perspectives—the suspicious sheriff, conflicted teacher Margaret Holloway, weathered witness Old Pete Anderson, and nervous newcomer Jack Morrison—each episode peels back another layer of a mystery that threatens to tear the community apart.

Multi-voice audio drama featuring ElevenLabs V3 AI voices and emotionally authentic storytelling drawn from real relationship dynamics. New episodes generated daily.""",
        "keywords": [
            "mystery",
            "noir",
            "small town",
            "1950s",
            "secrets",
            "drama",
            "serialized",
        ],
    },
    "saltmere-chronicles": {
        "title": "The Saltmere Chronicles",
        "subtitle": "Some Secrets Should Stay Buried at Sea",
        "description": """A 1970s Pacific Northwest coastal fishing village holds mysteries beneath its foggy waterfront. Marine biologist Sarah Chen returns to uncover family secrets, discovering that the bay doesn't just hold fish—it holds the town's darkest truths.

As Sarah teams with educator Margaret Holloway, fisherman Thomas Breck, and town matriarch Eleanor Cross, they uncover strange occurrences tied to Sarah's family legacy. Some secrets wash ashore. Others pull you under.

POV rotation delivers intimate character perspectives through multi-voice narration with ElevenLabs V3 AI, grounded in real emotional patterns. Daily episodes.""",
        "keywords": [
            "mystery",
            "coastal",
            "environmental",
            "family secrets",
            "1970s",
            "Pacific Northwest",
            "serialized",
        ],
    },
}


# =============================================================================
# Episode Metadata
# =============================================================================


@dataclass
class Episode:
    """Podcast episode metadata"""

    title: str
    file_path: Path
    duration_seconds: int
    size_bytes: int
    description: str
    pub_date: datetime
    episode_number: int
    season: int = 1
    guid: str = ""

    def __post_init__(self):
        if not self.guid:
            self.guid = hashlib.sha256(
                f"{self.title}{self.pub_date.isoformat()}".encode()
            ).hexdigest()[:16]


@dataclass
class PodcastSeries:
    """Podcast series metadata"""

    title: str
    description: str
    artwork_url: str
    episodes: list[Episode]
    author: str = AUTHOR
    language: str = LANGUAGE
    category: str = CATEGORY
    subcategory: str = SUBCATEGORY
    explicit: bool = False
    website: str = ""
    subtitle: str = ""
    keywords: list[str] = None
    directory_slug: str = ""  # Original directory name slug for audio paths


# =============================================================================
# Feed Generator
# =============================================================================


class PodcastFeedGenerator:
    """Generate podcast RSS feeds"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def scan_series_directory(self, series_dir: Path) -> list[Episode]:
        """Scan directory for episode MP3 files"""
        episodes = []

        for mp3_file in sorted(series_dir.glob("E*.mp3")):
            # Extract episode number from filename (E01, E02, etc.)
            try:
                ep_num = int(mp3_file.stem.split("-")[0][1:])
            except (ValueError, IndexError):
                ep_num = len(episodes) + 1

            # Get file stats
            stat = mp3_file.stat()

            # Get duration using ffprobe
            duration = self._get_duration(mp3_file)

            # Get title from filename or metadata
            title = (
                mp3_file.stem.split(" - ", 1)[-1]
                if " - " in mp3_file.stem
                else mp3_file.stem
            )

            # Try to get description from lyrics metadata
            description = self._get_description(mp3_file)

            episodes.append(
                Episode(
                    title=title,
                    file_path=mp3_file,
                    duration_seconds=duration,
                    size_bytes=stat.st_size,
                    description=description,
                    pub_date=datetime.fromtimestamp(stat.st_mtime),
                    episode_number=ep_num,
                )
            )

        return episodes

    def _get_duration(self, mp3_file: Path) -> int:
        """Get audio duration in seconds"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "csv=p=0",
                    str(mp3_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return int(float(result.stdout.strip()))
        except Exception:
            return 0

    def _get_description(self, mp3_file: Path) -> str:
        """Extract description from MP3 metadata"""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-show_entries",
                    "format_tags=comment",
                    "-of",
                    "csv=p=0",
                    str(mp3_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            comment = result.stdout.strip()
            if comment:
                return comment
        except Exception:
            pass
        return "An episode of Simulacrum Stories audio drama."

    def generate_feed(self, series: PodcastSeries, output_path: Path) -> Path:
        """Generate RSS feed XML"""

        # Create RSS structure with iTunes namespace
        rss = ET.Element(
            "rss",
            {
                "version": "2.0",
                "xmlns:itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
                "xmlns:content": "http://purl.org/rss/1.0/modules/content/",
                "xmlns:atom": "http://www.w3.org/2005/Atom",
            },
        )

        channel = ET.SubElement(rss, "channel")

        # Channel metadata
        ET.SubElement(channel, "title").text = series.title
        ET.SubElement(channel, "description").text = series.description
        ET.SubElement(channel, "language").text = series.language
        ET.SubElement(channel, "link").text = series.website or self.base_url
        ET.SubElement(channel, "generator").text = "Simulacrum Podcast Generator"
        ET.SubElement(channel, "lastBuildDate").text = datetime.now().strftime(
            "%a, %d %b %Y %H:%M:%S +0000"
        )

        # Atom self-link (required by some validators)
        feed_url = (
            f"{self.base_url}/feeds/{quote(series.title.lower().replace(' ', '-'))}.xml"
        )
        atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
        atom_link.set("href", feed_url)
        atom_link.set("rel", "self")
        atom_link.set("type", "application/rss+xml")

        # iTunes-specific metadata
        ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}author"
        ).text = series.author
        ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}summary"
        ).text = series.description
        if series.subtitle:
            ET.SubElement(
                channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}subtitle"
            ).text = series.subtitle
        if series.keywords:
            ET.SubElement(
                channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}keywords"
            ).text = ", ".join(series.keywords)
        ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit"
        ).text = "yes" if series.explicit else "no"
        ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}type"
        ).text = "serial"

        # Artwork
        if series.artwork_url:
            image = ET.SubElement(channel, "image")
            ET.SubElement(image, "url").text = series.artwork_url
            ET.SubElement(image, "title").text = series.title
            ET.SubElement(image, "link").text = self.base_url

            itunes_image = ET.SubElement(
                channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}image"
            )
            itunes_image.set("href", series.artwork_url)

        # Category
        category = ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}category"
        )
        category.set("text", series.category)
        if series.subcategory:
            subcat = ET.SubElement(
                category, "{http://www.itunes.com/dtds/podcast-1.0.dtd}category"
            )
            subcat.set("text", series.subcategory)

        # Owner
        owner = ET.SubElement(
            channel, "{http://www.itunes.com/dtds/podcast-1.0.dtd}owner"
        )
        ET.SubElement(
            owner, "{http://www.itunes.com/dtds/podcast-1.0.dtd}name"
        ).text = series.author
        ET.SubElement(
            owner, "{http://www.itunes.com/dtds/podcast-1.0.dtd}email"
        ).text = AUTHOR_EMAIL

        # Episodes (items)
        for ep in sorted(series.episodes, key=lambda e: e.episode_number, reverse=True):
            item = ET.SubElement(channel, "item")

            ET.SubElement(item, "title").text = ep.title
            ET.SubElement(item, "description").text = ep.description
            ET.SubElement(item, "pubDate").text = ep.pub_date.strftime(
                "%a, %d %b %Y %H:%M:%S +0000"
            )
            ET.SubElement(item, "guid").text = ep.guid

            # Enclosure (the audio file) - use directory slug from series
            file_url = f"{self.base_url}/audio/{series.directory_slug}/{quote(ep.file_path.name)}"
            enclosure = ET.SubElement(item, "enclosure")
            enclosure.set("url", file_url)
            enclosure.set("length", str(ep.size_bytes))
            enclosure.set("type", "audio/mpeg")

            # iTunes episode metadata
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}title"
            ).text = ep.title
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}summary"
            ).text = ep.description
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}episodeType"
            ).text = "full"
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}episode"
            ).text = str(ep.episode_number)
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}season"
            ).text = str(ep.season)
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}explicit"
            ).text = "no"

            # Duration in HH:MM:SS format
            hours = ep.duration_seconds // 3600
            minutes = (ep.duration_seconds % 3600) // 60
            seconds = ep.duration_seconds % 60
            if hours > 0:
                duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_str = f"{minutes}:{seconds:02d}"
            ET.SubElement(
                item, "{http://www.itunes.com/dtds/podcast-1.0.dtd}duration"
            ).text = duration_str

        # Write formatted XML
        output_path.parent.mkdir(parents=True, exist_ok=True)

        xml_str = ET.tostring(rss, encoding="unicode")
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        # Remove extra blank lines
        pretty_xml = "\n".join(line for line in pretty_xml.split("\n") if line.strip())

        output_path.write_text(pretty_xml)
        return output_path


# =============================================================================
# Podcast Server
# =============================================================================


class PodcastHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for serving podcast feeds and audio"""

    def __init__(self, *args, podcast_dir: Path, **kwargs):
        self.podcast_dir = podcast_dir
        super().__init__(*args, directory=str(podcast_dir), **kwargs)

    def do_GET(self):
        # Route requests
        if self.path.startswith("/feeds/"):
            # Serve RSS feeds
            feed_name = self.path[7:]  # Remove /feeds/
            feed_path = self.podcast_dir / "_feeds" / feed_name
            if feed_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/rss+xml")
                self.send_header("Content-Length", feed_path.stat().st_size)
                self.end_headers()
                self.wfile.write(feed_path.read_bytes())
                return

        elif self.path.startswith("/audio/"):
            # Serve audio files
            # /audio/series-slug/filename.mp3
            parts = self.path[7:].split("/", 1)
            if len(parts) == 2:
                series_slug, filename = parts
                # Find the series directory
                for d in self.podcast_dir.iterdir():
                    if d.is_dir() and not d.name.startswith("_"):
                        if (
                            d.name.lower().replace(" ", "-").replace(":", "")
                            == series_slug
                        ):
                            audio_path = d / filename
                            if audio_path.exists():
                                self.send_response(200)
                                self.send_header("Content-Type", "audio/mpeg")
                                self.send_header(
                                    "Content-Length", audio_path.stat().st_size
                                )
                                self.send_header("Accept-Ranges", "bytes")
                                self.end_headers()
                                self.wfile.write(audio_path.read_bytes())
                                return

        elif self.path == "/" or self.path == "/index.html":
            # Serve index page
            self.send_index_page()
            return

        # 404 for everything else
        self.send_error(404, "File not found")

    def send_index_page(self):
        """Generate an index page listing all podcast feeds"""
        feeds_dir = self.podcast_dir / "_feeds"

        html = """<!DOCTYPE html>
<html>
<head>
    <title>Simulacrum Stories - Podcast Feeds</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
               max-width: 800px; margin: 40px auto; padding: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #e94560; }
        .feed { background: #16213e; padding: 20px; margin: 20px 0; border-radius: 8px; }
        .feed h2 { margin-top: 0; color: #0f3460; }
        .feed h2 { color: #e94560; }
        a { color: #00d9ff; }
        code { background: #0f3460; padding: 2px 8px; border-radius: 4px; }
        .subscribe { margin-top: 10px; }
        .subscribe a {
            display: inline-block; padding: 8px 16px; background: #e94560;
            color: white; text-decoration: none; border-radius: 4px; margin-right: 10px;
        }
    </style>
</head>
<body>
    <h1>🎭 Simulacrum Stories</h1>
    <p>AI-generated audio dramas with multi-voice narration.</p>
"""

        if feeds_dir.exists():
            for feed_file in sorted(feeds_dir.glob("*.xml")):
                feed_url = f"http://{self.headers.get('Host', 'localhost:8000')}/feeds/{feed_file.name}"
                series_name = feed_file.stem.replace("-", " ").title()

                # Parse feed for episode count
                try:
                    tree = ET.parse(feed_file)
                    episodes = len(tree.findall(".//item"))
                except:
                    episodes = "?"

                html += f"""
    <div class="feed">
        <h2>{series_name}</h2>
        <p>Episodes: {episodes}</p>
        <p>Feed URL: <code>{feed_url}</code></p>
        <div class="subscribe">
            <a href="pktc://subscribe/{feed_url}">📱 Pocket Casts</a>
            <a href="podcast://{feed_url.replace('http://', '')}">🎧 Apple Podcasts</a>
            <a href="overcast://x-callback-url/add?url={feed_url}">☁️ Overcast</a>
            <a href="{feed_url}">📄 RSS Feed</a>
        </div>
    </div>
"""
        else:
            html += "<p>No feeds generated yet. Run with --all to generate feeds.</p>"

        html += """
    <hr>
    <p><small>Generated by Simulacrum Stories Podcast Generator</small></p>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", len(html.encode()))
        self.end_headers()
        self.wfile.write(html.encode())


def run_server(podcast_dir: Path, port: int = 8000):
    """Run the podcast server"""

    handler = lambda *args, **kwargs: PodcastHandler(
        *args, podcast_dir=podcast_dir, **kwargs
    )

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(
            f"\n🎙️  Podcast server running at http://localhost:{port}", file=sys.stderr
        )
        print(f"   Feed directory: {podcast_dir / '_feeds'}", file=sys.stderr)
        print(
            f"\n   Add to Pocket Casts: pktc://subscribe/http://localhost:{port}/feeds/YOUR-SERIES.xml",
            file=sys.stderr,
        )
        print("\n   Press Ctrl+C to stop\n", file=sys.stderr)

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.", file=sys.stderr)


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate and serve podcast feeds for Simulacrum Stories"
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--series", help="Generate feed for specific series")
    mode.add_argument(
        "--all", action="store_true", help="Generate feeds for all series"
    )

    parser.add_argument(
        "--serve", action="store_true", help="Start local podcast server"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Server port (default: 8000)"
    )
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="Base URL for feed links"
    )
    parser.add_argument(
        "--podcast-dir", default=str(PODCAST_DIR), help="Podcast content directory"
    )

    args = parser.parse_args()

    podcast_dir = Path(args.podcast_dir)
    feed_dir = podcast_dir / "_feeds"
    feed_dir.mkdir(parents=True, exist_ok=True)

    generator = PodcastFeedGenerator(base_url=args.base_url)

    # Generate feeds
    if args.series or args.all:
        series_dirs = []

        if args.all:
            # Find all series directories (non-hidden, non-feed directories)
            series_dirs = [
                d
                for d in podcast_dir.iterdir()
                if d.is_dir()
                and not d.name.startswith("_")
                and not d.name.startswith(".")
            ]
        elif args.series:
            # Find specific series
            for d in podcast_dir.iterdir():
                if d.is_dir() and args.series.lower() in d.name.lower():
                    series_dirs.append(d)
                    break

        for series_dir in series_dirs:
            print(f"Processing: {series_dir.name}", file=sys.stderr)

            # Scan for episodes
            episodes = generator.scan_series_directory(series_dir)

            if not episodes:
                print("  No episodes found, skipping", file=sys.stderr)
                continue

            # Check for artwork
            artwork_url = ""
            for art_name in ["cover.jpg", "cover.png", "artwork.jpg"]:
                art_path = series_dir / art_name
                if art_path.exists():
                    series_slug = (
                        series_dir.name.lower().replace(" ", "-").replace(":", "")
                    )
                    artwork_url = f"{args.base_url}/audio/{series_slug}/{art_name}"
                    break

            # Get rich series metadata if available
            series_slug = series_dir.name.lower().replace(" ", "-").replace(":", "")
            series_meta = SERIES_DESCRIPTIONS.get(series_slug, {})

            # Create series metadata
            series = PodcastSeries(
                title=series_meta.get("title", series_dir.name),
                description=series_meta.get(
                    "description",
                    f"An AI-generated audio drama series. {len(episodes)} episodes.",
                ),
                artwork_url=artwork_url,
                episodes=episodes,
                website=args.base_url,
                subtitle=series_meta.get("subtitle", ""),
                keywords=series_meta.get("keywords", []),
                directory_slug=series_slug,  # Use actual directory name for audio paths
            )

            # Generate feed
            feed_slug = series_dir.name.lower().replace(" ", "-").replace(":", "")
            feed_path = feed_dir / f"{feed_slug}.xml"
            generator.generate_feed(series, feed_path)

            print(
                f"  ✅ Generated: {feed_path.name} ({len(episodes)} episodes)",
                file=sys.stderr,
            )

    # Start server if requested
    if args.serve:
        run_server(podcast_dir, args.port)
    elif not args.series and not args.all:
        # No action specified, show help
        parser.print_help()


if __name__ == "__main__":
    main()
