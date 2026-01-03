#!/usr/bin/env python3
"""
Budget-Driven Episode Scheduler for Simulacrum Stories

Intelligently generates episodes based on available ElevenLabs budget,
balancing series and optimizing for maximum utilization without waste.

Usage:
    # Dry run (show what would happen)
    ./budget-driven-scheduler.py --dry-run

    # Actually generate episodes
    ./budget-driven-scheduler.py

    # Force generation regardless of budget
    ./budget-driven-scheduler.py --force

    # Verbose logging
    ./budget-driven-scheduler.py --verbose
"""

import argparse
import logging
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

# Import budget manager
from simulacrum.audio.budget import AudioBudgetManager

# Import production tools
import importlib.util
spec = importlib.util.spec_from_file_location("daily_production", project_root / "scripts" / "daily-production.py")
daily_production = importlib.util.module_from_spec(spec)
spec.loader.exec_module(daily_production)
EpisodeProducer = daily_production.EpisodeProducer
SeriesManager = daily_production.SeriesManager

# =============================================================================
# Configuration
# =============================================================================

OUTPUT_BASE = Path.home() / "Music" / "Simulacrum-Stories"
LOG_DIR = Path.home() / "Library" / "Logs"
LOG_FILE = LOG_DIR / "simulacrum-scheduler.log"

# Budget thresholds (characters)
MIN_CHARS_FOR_GENERATION = 3000  # Don't generate if less than this available
EPISODE_ESTIMATE_CHARS = 4000  # Typical episode size
RESERVE_CHARS = 1000  # Keep this much in reserve

# Episode generation targets
DAILY_TARGET_EPISODES = 2  # Try to generate 1-2 episodes per day
MAX_DAILY_EPISODES = 3  # Hard cap to avoid overconsumption

# =============================================================================
# Logging Setup
# =============================================================================


def setup_logging(verbose: bool = False):
    """Configure logging to file and console"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if verbose else logging.INFO

    # File handler
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# =============================================================================
# Budget Decision Logic
# =============================================================================


class BudgetDecisionEngine:
    """Decides whether and how many episodes to generate based on budget"""

    def __init__(self, budget_manager: AudioBudgetManager):
        self.budget = budget_manager
        self.logger = logging.getLogger(__name__)

    def get_available_budget(self) -> dict:
        """Get current budget availability"""
        provider = self.budget.active_provider
        tracker = self.budget.get_usage(provider)
        self.budget.check_and_reset_daily(tracker)
        self.budget.check_and_reset_monthly(tracker)

        budget_config = self.budget.budgets[provider]

        daily_remaining = budget_config["daily_limit"] - tracker.daily_used
        monthly_remaining = budget_config["monthly_limit"] - tracker.monthly_used

        return {
            "provider": provider,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "daily_limit": budget_config["daily_limit"],
            "monthly_limit": budget_config["monthly_limit"],
            "daily_used": tracker.daily_used,
            "monthly_used": tracker.monthly_used,
        }

    def can_generate_episode(self) -> tuple[bool, str]:
        """Check if we have enough budget for at least one episode"""
        budget = self.get_available_budget()

        # Check monthly budget first
        if budget["monthly_remaining"] < MIN_CHARS_FOR_GENERATION:
            return (
                False,
                f"Monthly budget nearly exhausted ({budget['monthly_remaining']:,} chars remaining)",
            )

        # Check daily budget
        if budget["daily_remaining"] < MIN_CHARS_FOR_GENERATION:
            return (
                False,
                f"Daily budget insufficient ({budget['daily_remaining']:,} chars remaining)",
            )

        # Have enough budget
        return True, "Budget available for generation"

    def estimate_possible_episodes(self) -> int:
        """Estimate how many episodes we can generate today"""
        budget = self.get_available_budget()

        # Use the more restrictive limit
        available = min(budget["daily_remaining"], budget["monthly_remaining"])

        # Reserve some budget
        usable = available - RESERVE_CHARS

        if usable < MIN_CHARS_FOR_GENERATION:
            return 0

        # Estimate episodes (with safety margin)
        estimated = int(usable / EPISODE_ESTIMATE_CHARS)

        # Cap at daily target
        return min(estimated, MAX_DAILY_EPISODES)

    def log_budget_status(self):
        """Log current budget status"""
        budget = self.get_available_budget()

        self.logger.info("=" * 60)
        self.logger.info("Budget Status")
        self.logger.info("=" * 60)
        self.logger.info(f"Provider: {budget['provider']}")
        self.logger.info(
            f"Daily: {budget['daily_used']:,}/{budget['daily_limit']:,} chars "
            f"({budget['daily_remaining']:,} remaining)"
        )
        self.logger.info(
            f"Monthly: {budget['monthly_used']:,}/{budget['monthly_limit']:,} chars "
            f"({budget['monthly_remaining']:,} remaining)"
        )

        episodes = self.estimate_possible_episodes()
        self.logger.info(f"Estimated episodes possible today: {episodes}")
        self.logger.info("=" * 60)


# =============================================================================
# Series Selection Logic
# =============================================================================


class SeriesSelector:
    """Selects which series to generate for based on staleness"""

    def __init__(self, series_manager: SeriesManager):
        self.manager = series_manager
        self.logger = logging.getLogger(__name__)

    def days_since_last_episode(self, series_name: str) -> int:
        """Calculate days since last episode for a series"""
        state = self.manager.get_series(series_name)
        if not state or not state.last_episode_at:
            return 999  # Very stale if never generated

        # Parse timestamp (handle both with and without timezone)
        last_ep_str = state.last_episode_at.replace("Z", "+00:00")
        last_ep = datetime.fromisoformat(last_ep_str)

        # Make now timezone-aware if last_ep is
        if last_ep.tzinfo is not None:
            now = datetime.now(UTC)
        else:
            now = datetime.now()

        delta = now - last_ep

        return delta.days

    def select_next_series(self) -> str | None:
        """Select the series that needs an episode most"""
        series_list = self.manager.list_series()

        if not series_list:
            self.logger.error("No series found in registry")
            return None

        # Calculate staleness for each series
        staleness = {
            state.name.lower(): self.days_since_last_episode(state.name.lower())
            for state in series_list
        }

        self.logger.debug(f"Series staleness: {staleness}")

        # Select most stale
        selected = max(staleness.keys(), key=lambda k: staleness[k])

        self.logger.info(
            f"Selected series: {selected.title()} "
            f"({staleness[selected]} days since last episode)"
        )

        return selected

    def get_balanced_series_order(self, count: int) -> list[str]:
        """Get list of series to generate for, balanced"""
        series_list = self.manager.list_series()
        series_names = [s.name.lower() for s in series_list]

        # Calculate staleness
        staleness = {name: self.days_since_last_episode(name) for name in series_names}

        # Generate balanced order (alternating between series)
        order = []
        for i in range(count):
            # Recalculate staleness accounting for what's in order
            adjusted_staleness = {
                name: staleness[name]
                + (order.count(name) * 1000)  # Penalize if already in order
                for name in series_names
            }
            next_series = max(
                adjusted_staleness.keys(), key=lambda k: adjusted_staleness[k]
            )
            order.append(next_series)

        return order


# =============================================================================
# Main Scheduler
# =============================================================================


class EpisodeScheduler:
    """Main scheduler orchestrating budget and episode generation"""

    def __init__(self, dry_run: bool = False, force: bool = False):
        self.dry_run = dry_run
        self.force = force
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.budget_engine = BudgetDecisionEngine(AudioBudgetManager())
        self.series_manager = SeriesManager()
        self.series_selector = SeriesSelector(self.series_manager)
        self.episode_producer = EpisodeProducer(OUTPUT_BASE)

        # Stats
        self.episodes_generated = 0
        self.chars_used = 0

    def run(self):
        """Main scheduling logic"""
        self.logger.info("Starting budget-driven episode scheduler")
        self.logger.info(f"Mode: {'DRY RUN' if self.dry_run else 'PRODUCTION'}")
        self.logger.info(f"Force: {self.force}")

        # Check budget
        self.budget_engine.log_budget_status()

        if not self.force:
            can_generate, reason = self.budget_engine.can_generate_episode()
            if not can_generate:
                self.logger.info(f"Skipping generation: {reason}")
                return

        # Determine how many episodes to generate
        if self.force:
            target_count = DAILY_TARGET_EPISODES
            self.logger.warning("Force mode: ignoring budget constraints")
        else:
            target_count = self.budget_engine.estimate_possible_episodes()

        if target_count == 0:
            self.logger.info("Budget insufficient for episodes today")
            return

        self.logger.info(f"Target: {target_count} episode(s)")

        # Get balanced series order
        series_order = self.series_selector.get_balanced_series_order(target_count)
        self.logger.info(
            f"Generation order: {' → '.join([s.title() for s in series_order])}"
        )

        # Generate episodes
        for i, series_name in enumerate(series_order):
            self.logger.info(f"\n{'=' * 60}")
            self.logger.info(
                f"Generating episode {i+1}/{target_count}: {series_name.title()}"
            )
            self.logger.info(f"{'=' * 60}")

            if self.dry_run:
                self.logger.info("[DRY RUN] Would generate episode here")
                continue

            try:
                self._generate_episode(series_name)
                self.episodes_generated += 1
            except Exception as e:
                self.logger.error(
                    f"Failed to generate episode for {series_name}: {e}", exc_info=True
                )
                # Continue with other series

        # Summary
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("Scheduler Summary")
        self.logger.info(f"{'=' * 60}")
        self.logger.info(
            f"Episodes generated: {self.episodes_generated}/{target_count}"
        )
        if not self.dry_run:
            self.logger.info(f"Characters used: {self.chars_used:,}")
            self.budget_engine.log_budget_status()

        # Publish to web if episodes were generated
        if self.episodes_generated > 0 and not self.dry_run:
            self._publish_to_web()

    def _generate_episode(self, series_name: str):
        """Generate a single episode for the specified series"""
        state = self.series_manager.get_series(series_name)
        if not state:
            raise ValueError(f"Series not found: {series_name}")

        # Output directory
        album_dir = OUTPUT_BASE / f"{state.name} Chronicles"
        album_dir.mkdir(parents=True, exist_ok=True)

        # Generate with real relationship signals for emotional authenticity
        self.logger.info(f"Producing episode for {state.name}...")
        self.logger.info("  Extracting relationship signals for emotional depth...")
        audio_file = self.episode_producer.produce_episode(
            state,
            album_dir,
            use_real_signals=True,  # Enable for both series
        )

        # Update series state
        self.series_manager.update_episode_count(series_name)

        # Estimate characters used (from audio duration as proxy)
        # This is rough - real tracking would happen in doc-to-audio
        # For now, use conservative estimate
        self.chars_used += EPISODE_ESTIMATE_CHARS

        self.logger.info(f"✓ Episode generated: {audio_file.name}")
        self.logger.info(f"   Location: {audio_file}")

        # Update RSS feed
        self._update_rss_feed(series_name)

    def _update_rss_feed(self, series_name: str):
        """Update RSS feed for the series"""
        self.logger.info(f"Updating RSS feed for {series_name}...")

        try:
            # Call podcast_feed.py to regenerate feed for this series
            script_dir = Path(__file__).parent
            podcast_feed_script = script_dir / "podcast_feed.py"

            # Get Netlify URL from config or use placeholder
            netlify_url = os.environ.get(
                "PODCAST_NETLIFY_URL", "https://podcasts.devvyn.ca"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(podcast_feed_script),
                    "--series",
                    series_name.lower(),
                    "--base-url",
                    netlify_url,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self.logger.info(f"✅ RSS feed updated for {series_name}")
            else:
                self.logger.warning(
                    f"RSS feed update had issues: {result.stderr or result.stdout}"
                )
        except Exception as e:
            self.logger.error(f"Failed to update RSS feed: {e}")

    def _publish_to_web(self):
        """Publish episodes and feeds to Netlify"""
        self.logger.info(f"\n{'=' * 60}")
        self.logger.info("Publishing to Web")
        self.logger.info(f"{'=' * 60}")

        try:
            script_dir = Path(__file__).parent
            publish_script = script_dir / "publish-podcasts.sh"

            if not publish_script.exists():
                self.logger.warning("Publish script not found - skipping web publish")
                return

            netlify_url = os.environ.get(
                "PODCAST_NETLIFY_URL", "https://podcasts.devvyn.ca"
            )

            self.logger.info(f"Running publish script to {netlify_url}...")

            result = subprocess.run(
                [str(publish_script), netlify_url],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                self.logger.info("✅ Podcast site updated and ready for deployment")
                self.logger.info("")
                self.logger.info("📤 Deploy with:")
                self.logger.info(
                    f"   cd {Path.home()}/devvyn-meta-project/podcast-site"
                )
                self.logger.info("   netlify deploy --prod")
                self.logger.info("")
                self.logger.info("   OR drag-and-drop to: https://app.netlify.com/drop")
            else:
                self.logger.warning(f"Publish had issues: {result.stderr}")
                # Don't fail - this is not critical
        except Exception as e:
            self.logger.error(f"Failed to publish to web: {e}")
            # Don't fail the whole job - episodes are still generated locally


# =============================================================================
# CLI
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Budget-driven episode scheduler for Simulacrum Stories"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without actually generating",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force generation regardless of budget"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        scheduler = EpisodeScheduler(dry_run=args.dry_run, force=args.force)
        scheduler.run()
    except Exception as e:
        logger.error(f"Scheduler failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
