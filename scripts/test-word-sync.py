#!/usr/bin/env python3
"""
Automated word-sync testing using Playwright.

Tests that clicking words seeks to the correct audio position.

Usage:
    uv run python scripts/test-word-sync.py [--chapter N] [--headed]
"""

import argparse
import asyncio
from playwright.async_api import async_playwright


# Test points: (word_index, expected_raw_time, word_text)
# Note: intro_duration is now 24s (12s title bumper + 12s ambient intro)
CHAPTER_1_TESTS = [
    (0, 0.0, "The"),           # First word - expects 24s final
    (7, 1.52, "exhalation"),   # Early word - expects ~25.5s final
    (32, 10.88, "Sarah"),      # ~11s raw - expects ~35s final
    (100, 34.64, "only"),      # From word data - expects ~59s final
    (500, 182.5, "moored"),    # From word data - expects ~213s final (after 1 break)
    (1000, 358.86, "chaos"),   # From word data - expects ~396s final (after 2 breaks)
]


async def test_word_sync(chapter: int = 1, headed: bool = False, base_url: str = "http://localhost:8000"):
    """Run automated word sync tests."""

    async with async_playwright() as p:
        # Use Firefox which handles audio better
        browser = await p.firefox.launch(headless=not headed)
        context = await browser.new_context()
        page = await context.new_page()

        # Capture console messages and network errors
        console_messages = []
        page.on("console", lambda msg: console_messages.append(f"[{msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: console_messages.append(f"[PAGE_ERROR] {err}"))
        page.on("requestfailed", lambda req: console_messages.append(f"[FAILED] {req.url} - {req.failure}"))

        # Navigate to chapter
        chapter_slug = {
            1: "chapter-01-the-research-station",
            2: "chapter-02-the-harbor-master",
            3: "chapter-03-first-samples",
        }.get(chapter, f"chapter-{chapter:02d}")

        url = f"{base_url}/read/{chapter_slug}.html"
        print(f"Loading: {url}")
        await page.goto(url)

        # Wait for page to load (don't wait for networkidle as audio keeps network busy)
        await page.wait_for_load_state("domcontentloaded")
        await asyncio.sleep(5)  # Give time for JS to initialize

        # Check chapter-player init status
        cp_init = await page.evaluate("""
            () => ({
                hasAudioManifest: !!window.audioManifest || document.querySelector('.chapter-modalities') !== null,
                playerContainer: !!document.getElementById('chapter-player-container')
            })
        """)
        print(f"Chapter player init: {cp_init}")

        # Check if modality header with play button exists
        modality_header = page.locator(".modality-header")
        play_btn = page.locator("#listen-mode-btn")

        print(f"Modality header exists: {await modality_header.count() > 0}")
        print(f"Play button exists: {await play_btn.count() > 0}")

        # Debug: find where the play button actually is
        btn_location = await page.evaluate("""
            () => {
                const btn = document.getElementById('listen-mode-btn');
                if (!btn) return null;
                return {
                    parent: btn.parentElement?.className,
                    outerHTML: btn.outerHTML.slice(0, 200)
                };
            }
        """)
        print(f"Button location: {btn_location}")

        # If no play button, the audio manifest may not have loaded
        if await play_btn.count() == 0:
            # Check if chapter-player.js loaded
            cp_status = await page.evaluate("""
                () => ({
                    chapterPlayerDefined: typeof initChapterPlayer !== 'undefined',
                    manifestFetched: window._audioManifestLoaded || false
                })
            """)
            print(f"Chapter player status: {cp_status}")

            # Wait a bit more for async loading
            await asyncio.sleep(3)
            print("Waited 3 more seconds...")

        # Click "Play Audio" button to initialize player
        play_btn = page.locator("#listen-mode-btn")
        if await play_btn.count() > 0:
            print("Clicking Play Audio button...")
            await play_btn.click()
            await asyncio.sleep(5)  # Wait longer for audio to load

            # Also click the play button in the player if it exists
            player_play = page.locator(".audio-player .play-pause")
            if await player_play.count() > 0:
                await player_play.click()
                await asyncio.sleep(2)
        else:
            print("No Play Audio button found!")

        # Wait for player container to appear (audio is inside)
        print("Waiting for player...")
        try:
            await page.wait_for_selector("#chapter-player-container", timeout=10000)
            print("Player container found!")
        except Exception as e:
            print(f"No player container: {e}")

        # Debug: check page state
        page_state = await page.evaluate("""
            () => ({
                hasAudio: !!document.querySelector('audio'),
                hasPlayer: !!document.querySelector('.audio-player'),
                hasWordSpans: document.querySelectorAll('.content .w[data-i]').length,
                hasContent: !!document.querySelector('.content'),
                contentText: document.querySelector('.content')?.textContent?.slice(0, 100),
                bodyClasses: document.body.className,
                wordHighlightLoaded: !!window.WordHighlight,
                url: window.location.href
            })
        """)
        print(f"Page state: {page_state}")

        # Take screenshot for debugging
        await page.screenshot(path="/tmp/word-sync-debug.png")
        print("Screenshot saved to /tmp/word-sync-debug.png")

        # Print console messages
        print(f"\nConsole messages ({len(console_messages)} total):")
        for msg in console_messages:
            print(f"  {msg}")

        # Get calibration info from page
        calibration = await page.evaluate("""
            () => {
                if (window.WordHighlight && window.WordHighlight.getCalibration) {
                    return window.WordHighlight.getCalibration();
                }
                return null;
            }
        """)
        print(f"Calibration loaded: {calibration}")

        # Get audio element info
        audio_ready = await page.evaluate("""
            () => {
                const container = document.getElementById('chapter-player-container');
                if (!container) return { error: 'no container' };

                const currentTime = container.querySelector('.current-time');
                const playerTime = container.querySelector('.player-time');

                return {
                    containerExists: true,
                    hasCurrentTime: !!currentTime,
                    currentTimeText: currentTime?.textContent,
                    playerTimeText: playerTime?.textContent,
                };
            }
        """)
        print(f"Audio: {audio_ready}")

        if audio_ready.get('error'):
            print(f"ERROR: {audio_ready['error']}")
            await browser.close()
            return

        if not audio_ready.get('hasCurrentTime'):
            print("ERROR: No time display found - player may not have loaded")
            await browser.close()
            return

        # Wait for audio to be ready - check duration is shown
        print("Waiting for audio to fully load...")
        for _ in range(10):
            duration_check = await page.evaluate("""
                () => {
                    const pt = document.querySelector('.player-time');
                    // Chapter 1 duration is ~10:50 (650s)
                    const text = pt?.textContent || '';
                    return text.includes('10:') || text.includes('11:');
                }
            """)
            if duration_check:
                print("Audio duration confirmed!")
                break
            await asyncio.sleep(1)
        else:
            print("WARNING: Audio may not have fully loaded")

        print(f"\n{'='*60}")
        print("WORD SYNC TEST RESULTS")
        print(f"{'='*60}\n")

        results = []

        # Find all word spans
        word_spans = page.locator(".content .w[data-i]")
        word_count = await word_spans.count()
        print(f"Found {word_count} word spans\n")

        for word_idx, expected_raw, expected_word in CHAPTER_1_TESTS:
            # Find word by data-i attribute (transcript index), not DOM position
            word_span = page.locator(f'.content .w[data-i="{word_idx}"]')
            if await word_span.count() == 0:
                print(f"[SKIP] No element with data-i={word_idx}")
                continue

            word_text = await word_span.text_content()

            # Click the word
            print(f"  Clicking word {word_idx} (data-i={word_idx})...")

            # Clear console for this click
            click_console = []
            page.on("console", lambda msg: click_console.append(f"{msg.text}"))

            await word_span.click()

            # Wait for click handler and seek to complete
            await asyncio.sleep(1.0)

            # Show any console output from click
            for msg in click_console:
                if 'WordClick' in msg or 'rawToFinal' in msg:
                    print(f"    Console: {msg}")

            # Check actual audio state after click
            audio_state = await page.evaluate("""
                () => {
                    // Find audio element - it's created via new Audio() so not in DOM
                    // but WordHighlight has a reference to it
                    const audio = window._chapterPlayerAudio;
                    if (!audio) return { error: 'no audio reference' };
                    return {
                        currentTime: audio.currentTime,
                        duration: audio.duration,
                        readyState: audio.readyState,
                        paused: audio.paused,
                        seeking: audio.seeking,
                        networkState: audio.networkState,
                    };
                }
            """)
            print(f"    Audio state: {audio_state}")

            # Get current audio time via the time display
            time_result = await page.evaluate("""
                () => {
                    const display = document.querySelector('.current-time');
                    if (!display) return { error: 'no display' };
                    const text = display.textContent.trim();
                    const parts = text.split(':').map(s => parseInt(s, 10));
                    let seconds = 0;
                    if (parts.length === 2) seconds = parts[0] * 60 + parts[1];
                    else if (parts.length === 1) seconds = parts[0];
                    return { text, parts, seconds };
                }
            """)
            current_time = time_result.get('seconds', 0) if isinstance(time_result, dict) else 0

            # Calculate expected final time (raw + intro_duration + section breaks before)
            intro_dur = calibration.get("intro_duration", 24) if calibration else 24
            expected_final = expected_raw + intro_dur

            # Check accuracy
            diff = abs(current_time - expected_final)
            status = "✓ PASS" if diff < 1.0 else "✗ FAIL" if diff > 3.0 else "~ CLOSE"

            result = {
                "word_idx": word_idx,
                "word": word_text.strip() if word_text else "?",
                "expected_raw": expected_raw,
                "expected_final": expected_final,
                "actual": current_time,
                "diff": diff,
                "status": status,
                "time_debug": time_result,
            }
            results.append(result)

            print(f"[{status}] Word #{word_idx}: \"{result['word']}\" (debug: {time_result})")
            print(f"        Raw: {expected_raw:.1f}s → Expected final: {expected_final:.1f}s")
            print(f"        Actual: {current_time:.1f}s (diff: {diff:.1f}s)")
            print()

            # Wait a moment before next test
            await asyncio.sleep(0.5)

        # Summary
        passed = sum(1 for r in results if "PASS" in r["status"])
        failed = sum(1 for r in results if "FAIL" in r["status"])

        print(f"{'='*60}")
        print(f"SUMMARY: {passed} passed, {failed} failed, {len(results) - passed - failed} close")
        print(f"{'='*60}")

        await browser.close()
        return results


def main():
    parser = argparse.ArgumentParser(description="Test word-level audio sync")
    parser.add_argument("--chapter", type=int, default=1, help="Chapter to test")
    parser.add_argument("--headed", action="store_true", help="Run with visible browser")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL")
    args = parser.parse_args()

    asyncio.run(test_word_sync(args.chapter, args.headed, args.url))


if __name__ == "__main__":
    main()
