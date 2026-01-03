#!/usr/bin/env python3
"""
Audio Budget Manager for TTS API Usage

Manages monthly subscription limits and daily quotas for audio generation services.
Tracks usage, enforces limits, and provides queuing for batch operations.

Usage:
    # Check current usage/quota
    ./audio-budget-manager.py status

    # Request characters (returns approval + updates tracking)
    ./audio-budget-manager.py request elevenlabs 5000

    # Queue a document for generation
    ./audio-budget-manager.py queue doc.md --provider elevenlabs --priority high

    # Process queue within daily limits
    ./audio-budget-manager.py process-queue

    # Reset monthly counters (run on 1st of month)
    ./audio-budget-manager.py reset-month
"""

import json
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Literal

# Budget configuration file
BUDGET_CONFIG = Path.home() / "devvyn-meta-project" / "config" / "audio-budget.json"

# Default budget limits (characters per month)
# Note: Prices shown in USD. For CAD multiply by ~1.35-1.40 (exchange rate varies)
DEFAULT_BUDGETS = {
    "elevenlabs_starter": {
        "monthly_limit": 30000,  # 30k characters/month (verified Nov 2025)
        "daily_limit": 2000,  # ~4 minutes/day (conservative estimate)
        "cost_per_month": 5.00,  # USD (CAD: ~$6.75-7.00)
        "description": "ElevenLabs Starter Plan ($5 USD/mo, 30k chars)",
    },
    "elevenlabs_creator": {
        "monthly_limit": 100000,  # 100k characters/month (verified Nov 2025)
        "daily_limit": 5000,  # ~10 minutes/day (conservative estimate)
        "cost_per_month": 22.00,  # USD regular price (CAD: ~$29.70-30.80)
        "description": "ElevenLabs Creator Plan ($22 USD/mo, 100k chars, first month 50% off)",
    },
    "elevenlabs_v3_alpha": {
        "monthly_limit": 150000,  # 5x effective credits due to 80% discount
        "daily_limit": 10000,  # Conservative daily quota
        "cost_per_month": 5.00,  # USD - same Starter cost but 5x credits with V3
        "description": "ElevenLabs V3 Alpha (80% discount until June 30, 2025) - BEST VALUE",
    },
    "openai_tts": {
        "monthly_limit": 1000000,  # $15 budget = 1M chars @ $0.015/1k chars
        "daily_limit": 50000,
        "cost_per_month": 15.00,  # USD (CAD: ~$20.25-21.00)
        "description": "OpenAI TTS API ($15 USD/1M chars)",
    },
    "macos_native": {
        "monthly_limit": float("inf"),  # Unlimited
        "daily_limit": float("inf"),
        "cost_per_month": 0.00,
        "description": "macOS Native TTS (Free, Unlimited)",
    },
}


@dataclass
class UsageTracker:
    """Track usage for a specific provider"""

    provider: str
    month: str  # YYYY-MM format
    monthly_used: int  # characters used this month
    daily_used: int  # characters used today
    last_reset_date: str  # YYYY-MM-DD format
    history: list  # List of {date, chars, doc} entries


@dataclass
class QueuedJob:
    """Audio generation job in queue"""

    job_id: str
    doc_path: str
    provider: str
    priority: Literal["low", "medium", "high", "urgent"]
    estimated_chars: int
    added_date: str  # ISO format
    status: Literal["queued", "processing", "completed", "failed"]
    error: str = ""


class AudioBudgetManager:
    """Manage audio generation budgets and quotas"""

    def __init__(self, config_path: Path = BUDGET_CONFIG):
        self.config_path = config_path
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.load_or_create_config()

    def load_or_create_config(self):
        """Load existing config or create new one"""
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = json.load(f)
            self.active_provider = data.get("active_provider", "macos_native")
            self.budgets = data.get("budgets", DEFAULT_BUDGETS)
            self.usage = {
                k: UsageTracker(**v) for k, v in data.get("usage", {}).items()
            }
            self.queue = [QueuedJob(**j) for j in data.get("queue", [])]
        else:
            # Create default config
            self.active_provider = "macos_native"
            self.budgets = DEFAULT_BUDGETS
            self.usage = {}
            self.queue = []
            self.save_config()

    def save_config(self):
        """Save current state to JSON"""
        data = {
            "active_provider": self.active_provider,
            "budgets": self.budgets,
            "usage": {k: asdict(v) for k, v in self.usage.items()},
            "queue": [asdict(j) for j in self.queue],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_usage(self, provider: str) -> UsageTracker:
        """Get or create usage tracker for provider"""
        if provider not in self.usage:
            self.usage[provider] = UsageTracker(
                provider=provider,
                month=date.today().strftime("%Y-%m"),
                monthly_used=0,
                daily_used=0,
                last_reset_date=date.today().isoformat(),
                history=[],
            )
        return self.usage[provider]

    def check_and_reset_daily(self, tracker: UsageTracker):
        """Reset daily counter if date changed"""
        today = date.today().isoformat()
        if tracker.last_reset_date != today:
            tracker.daily_used = 0
            tracker.last_reset_date = today

    def check_and_reset_monthly(self, tracker: UsageTracker):
        """Reset monthly counter if month changed"""
        current_month = date.today().strftime("%Y-%m")
        if tracker.month != current_month:
            tracker.month = current_month
            tracker.monthly_used = 0

    def can_use(self, provider: str, chars: int) -> tuple[bool, str]:
        """Check if usage is within limits"""
        if provider not in self.budgets:
            return False, f"Unknown provider: {provider}"

        tracker = self.get_usage(provider)
        self.check_and_reset_daily(tracker)
        self.check_and_reset_monthly(tracker)

        budget = self.budgets[provider]
        monthly_limit = budget["monthly_limit"]
        daily_limit = budget["daily_limit"]

        # Check monthly limit
        if tracker.monthly_used + chars > monthly_limit:
            remaining = monthly_limit - tracker.monthly_used
            return False, f"Monthly limit exceeded. Remaining: {remaining:,} chars"

        # Check daily limit
        if tracker.daily_used + chars > daily_limit:
            remaining = daily_limit - tracker.daily_used
            return False, f"Daily limit exceeded. Remaining: {remaining:,} chars"

        return True, "OK"

    def record_usage(self, provider: str, chars: int, doc: str = ""):
        """Record actual usage"""
        tracker = self.get_usage(provider)
        self.check_and_reset_daily(tracker)
        self.check_and_reset_monthly(tracker)

        tracker.monthly_used += chars
        tracker.daily_used += chars
        tracker.history.append(
            {
                "date": datetime.now().isoformat(),
                "chars": chars,
                "doc": doc,
            }
        )

        self.save_config()

    def add_to_queue(
        self, doc_path: str, provider: str, priority: str, estimated_chars: int
    ):
        """Add job to queue"""
        job = QueuedJob(
            job_id=f"{date.today().isoformat()}-{len(self.queue)}",
            doc_path=doc_path,
            provider=provider,
            priority=priority,
            estimated_chars=estimated_chars,
            added_date=datetime.now().isoformat(),
            status="queued",
        )
        self.queue.append(job)
        self.save_config()
        return job.job_id

    def process_queue(self, dry_run: bool = False) -> list[QueuedJob]:
        """Process queued jobs within daily limits"""
        processed = []

        # Sort by priority (urgent > high > medium > low)
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        queued_jobs = [j for j in self.queue if j.status == "queued"]
        queued_jobs.sort(key=lambda j: priority_order.get(j.priority, 99))

        for job in queued_jobs:
            can_process, reason = self.can_use(job.provider, job.estimated_chars)

            if can_process:
                if not dry_run:
                    # Actually record usage
                    self.record_usage(job.provider, job.estimated_chars, job.doc_path)
                    job.status = "completed"

                processed.append(job)
            else:
                print(f"⏸️  Skipping {job.doc_path}: {reason}")
                break  # Stop processing if we hit limits

        if not dry_run:
            self.save_config()

        return processed

    def status_report(self) -> str:
        """Generate status report"""
        lines = []
        lines.append("=" * 70)
        lines.append("🎙️  AUDIO BUDGET STATUS")
        lines.append("=" * 70)
        lines.append(f"\nActive Provider: {self.active_provider}")

        if self.active_provider in self.budgets:
            budget = self.budgets[self.active_provider]
            tracker = self.get_usage(self.active_provider)
            self.check_and_reset_daily(tracker)
            self.check_and_reset_monthly(tracker)

            lines.append(f"Plan: {budget['description']}")
            lines.append(f"Cost: ${budget['cost_per_month']:.2f}/month")
            lines.append("")

            # Monthly usage
            monthly_pct = (tracker.monthly_used / budget["monthly_limit"]) * 100
            monthly_bar = self._progress_bar(
                tracker.monthly_used, budget["monthly_limit"]
            )
            lines.append(f"📅 Monthly Usage ({tracker.month}):")
            lines.append(f"  {monthly_bar} {monthly_pct:.1f}%")
            lines.append(
                f"  Used: {tracker.monthly_used:,} / {budget['monthly_limit']:,} chars"
            )
            lines.append(
                f"  Remaining: {budget['monthly_limit'] - tracker.monthly_used:,} chars"
            )
            lines.append("")

            # Daily usage
            daily_pct = (tracker.daily_used / budget["daily_limit"]) * 100
            daily_bar = self._progress_bar(tracker.daily_used, budget["daily_limit"])
            lines.append(f"☀️  Daily Usage ({tracker.last_reset_date}):")
            lines.append(f"  {daily_bar} {daily_pct:.1f}%")
            lines.append(
                f"  Used: {tracker.daily_used:,} / {budget['daily_limit']:,} chars"
            )
            lines.append(
                f"  Remaining: {budget['daily_limit'] - tracker.daily_used:,} chars"
            )

        # Queue status
        lines.append("")
        lines.append("=" * 70)
        lines.append("📋 QUEUE STATUS")
        lines.append("=" * 70)

        queued = [j for j in self.queue if j.status == "queued"]
        processing = [j for j in self.queue if j.status == "processing"]
        completed = [j for j in self.queue if j.status == "completed"]
        failed = [j for j in self.queue if j.status == "failed"]

        lines.append(f"Queued: {len(queued)}")
        lines.append(f"Processing: {len(processing)}")
        lines.append(f"Completed: {len(completed)}")
        lines.append(f"Failed: {len(failed)}")

        if queued:
            lines.append("")
            lines.append("Next in Queue:")
            for job in queued[:5]:
                lines.append(
                    f"  [{job.priority.upper()}] {Path(job.doc_path).name} ({job.estimated_chars:,} chars)"
                )

        lines.append("=" * 70)

        return "\n".join(lines)

    def _progress_bar(self, used: int, limit: int, width: int = 30) -> str:
        """Generate progress bar"""
        if limit == float("inf"):
            return "[" + "=" * width + "]"

        pct = min(used / limit, 1.0)
        filled = int(width * pct)
        bar = "=" * filled + " " * (width - filled)
        return f"[{bar}]"


def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    manager = AudioBudgetManager()
    command = sys.argv[1]

    if command == "status":
        print(manager.status_report())

    elif command == "request":
        if len(sys.argv) < 4:
            print("Usage: audio-budget-manager.py request <provider> <chars>")
            sys.exit(1)

        provider = sys.argv[2]
        chars = int(sys.argv[3])

        can_use, reason = manager.can_use(provider, chars)
        if can_use:
            manager.record_usage(provider, chars)
            print(f"✅ Approved: {chars:,} chars for {provider}")
            print(f"   {reason}")
        else:
            print(f"❌ Denied: {reason}")
            sys.exit(1)

    elif command == "queue":
        if len(sys.argv) < 3:
            print(
                "Usage: audio-budget-manager.py queue <doc.md> --provider <provider> --priority <priority>"
            )
            sys.exit(1)

        doc_path = sys.argv[2]
        provider = (
            sys.argv[sys.argv.index("--provider") + 1]
            if "--provider" in sys.argv
            else manager.active_provider
        )
        priority = (
            sys.argv[sys.argv.index("--priority") + 1]
            if "--priority" in sys.argv
            else "medium"
        )

        # Estimate characters (rough: file size in bytes)
        estimated_chars = Path(doc_path).stat().st_size

        job_id = manager.add_to_queue(doc_path, provider, priority, estimated_chars)
        print(f"✅ Added to queue: {job_id}")
        print(f"   Doc: {doc_path}")
        print(f"   Provider: {provider}")
        print(f"   Priority: {priority}")
        print(f"   Estimated: {estimated_chars:,} chars")

    elif command == "process-queue":
        dry_run = "--dry-run" in sys.argv
        processed = manager.process_queue(dry_run=dry_run)

        if dry_run:
            print(f"🔍 DRY RUN: Would process {len(processed)} jobs")
        else:
            print(f"✅ Processed {len(processed)} jobs")

        for job in processed:
            print(f"  - {Path(job.doc_path).name} ({job.estimated_chars:,} chars)")

    elif command == "reset-month":
        # Reset all monthly counters
        for tracker in manager.usage.values():
            tracker.monthly_used = 0
            tracker.month = date.today().strftime("%Y-%m")
        manager.save_config()
        print("✅ Monthly counters reset")

    elif command == "set-provider":
        if len(sys.argv) < 3:
            print("Usage: audio-budget-manager.py set-provider <provider>")
            print(f"Available: {', '.join(manager.budgets.keys())}")
            sys.exit(1)

        provider = sys.argv[2]
        if provider not in manager.budgets:
            print(f"❌ Unknown provider: {provider}")
            print(f"Available: {', '.join(manager.budgets.keys())}")
            sys.exit(1)

        manager.active_provider = provider
        manager.save_config()
        print(f"✅ Active provider set to: {provider}")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
