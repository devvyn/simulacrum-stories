#!/usr/bin/env python3
"""
Audio Production Diagnostic Runner for Simulacrum Stories.

Checkpoint-based testing with dual output (telemetry.json + report.md).
Pattern adapted from herbarium-specimen-tools DiagnosticRunner.

Usage:
    # Full diagnostic
    uv run python scripts/diagnose_audio_production.py

    # Specific series
    uv run python scripts/diagnose_audio_production.py --series saltmere

    # Verbose output
    uv run python scripts/diagnose_audio_production.py -v

    # Step mode (pause at each checkpoint)
    uv run python scripts/diagnose_audio_production.py --step
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import struct


# === TELEMETRY SCHEMA ===
# Shared pattern with herbarium-specimen-tools

@dataclass
class TelemetryEvent:
    """Single telemetry event."""
    timestamp: str
    event_type: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None


@dataclass
class AudioCheckpoint:
    """Diagnostic checkpoint for audio production."""
    name: str
    timestamp: str
    files_checked: List[str] = field(default_factory=list)
    manifest_state: Optional[Dict[str, Any]] = None
    budget_state: Optional[Dict[str, Any]] = None
    notes: List[str] = field(default_factory=list)
    passed: bool = True
    tests_in_checkpoint: int = 0
    failures_in_checkpoint: int = 0


@dataclass
class DiagnosticSession:
    """Full diagnostic session with all telemetry."""
    session_id: str
    started_at: str
    ended_at: Optional[str] = None
    series: str = "all"

    # Telemetry collections
    checkpoints: List[AudioCheckpoint] = field(default_factory=list)
    errors: List[TelemetryEvent] = field(default_factory=list)
    warnings: List[TelemetryEvent] = field(default_factory=list)

    # Summary metrics
    total_duration_ms: Optional[float] = None
    tests_passed: int = 0
    tests_failed: int = 0
    audio_files_validated: int = 0
    total_audio_duration_sec: float = 0


class AudioDiagnosticRunner:
    """Diagnostic runner for audio production QA."""

    def __init__(
        self,
        series: str = "all",
        verbose: bool = False,
        step_mode: bool = False,
    ):
        self.series = series
        self.verbose = verbose
        self.step_mode = step_mode

        # Paths
        self.project_root = Path(__file__).parent.parent
        self.site_dir = self.project_root / "site"
        self.audio_dir = self.site_dir / "audio"
        self.manifest_path = self.site_dir / "js" / "audio-manifest.json"
        self.output_dir = self.project_root / "output" / "diagnostics"

        # Session setup
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.output_dir / f"session_{self.session_id}"
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.session = DiagnosticSession(
            session_id=self.session_id,
            started_at=datetime.now().isoformat(),
            series=series,
        )

        self._start_time: Optional[float] = None
        self._current_checkpoint: Optional[AudioCheckpoint] = None

    def _timestamp(self) -> str:
        return datetime.now().isoformat()

    def _elapsed_ms(self) -> float:
        if self._start_time:
            import time
            return (time.time() - self._start_time) * 1000
        return 0

    def _log(self, msg: str, level: str = "info"):
        """Log message with optional verbosity control."""
        if level == "error":
            print(f"  [ERROR] {msg}")
        elif level == "warn":
            print(f"  [WARN] {msg}")
        elif self.verbose or level == "info":
            print(f"  {msg}")

    def checkpoint(
        self,
        name: str,
        notes: Optional[List[str]] = None,
    ) -> AudioCheckpoint:
        """Create a diagnostic checkpoint."""
        print(f"\n{'='*60}")
        print(f"CHECKPOINT: {name}")
        print(f"{'='*60}")

        cp = AudioCheckpoint(
            name=name,
            timestamp=self._timestamp(),
            notes=notes or [],
        )

        self._current_checkpoint = cp
        self.session.checkpoints.append(cp)

        return cp

    def end_checkpoint(self):
        """Finalize current checkpoint."""
        if self._current_checkpoint:
            if self._current_checkpoint.failures_in_checkpoint > 0:
                self._current_checkpoint.passed = False

            print(f"  Checkpoint: {self._current_checkpoint.tests_in_checkpoint} tests, "
                  f"{self._current_checkpoint.failures_in_checkpoint} failures")

            if self.step_mode:
                input("\n  Press Enter to continue...")

            self._current_checkpoint = None

    def test(self, name: str, condition: bool, note: str = "") -> bool:
        """Record a test result."""
        symbol = "✓" if condition else "✗"
        print(f"  [{symbol}] {name}" + (f" - {note}" if note else ""))

        if condition:
            self.session.tests_passed += 1
        else:
            self.session.tests_failed += 1

        if self._current_checkpoint:
            self._current_checkpoint.tests_in_checkpoint += 1
            if not condition:
                self._current_checkpoint.failures_in_checkpoint += 1

        return condition

    def warn(self, message: str, data: Optional[Dict] = None):
        """Record a warning."""
        self._log(message, "warn")
        self.session.warnings.append(TelemetryEvent(
            timestamp=self._timestamp(),
            event_type="warning",
            data={"message": message, **(data or {})},
            duration_ms=self._elapsed_ms(),
        ))

    def error(self, message: str, data: Optional[Dict] = None):
        """Record an error."""
        self._log(message, "error")
        self.session.errors.append(TelemetryEvent(
            timestamp=self._timestamp(),
            event_type="error",
            data={"message": message, **(data or {})},
            duration_ms=self._elapsed_ms(),
        ))

    def get_mp3_duration(self, filepath: Path) -> Optional[float]:
        """Get MP3 duration in seconds using ffprobe or file analysis."""
        try:
            # Try ffprobe first
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(filepath)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
            pass

        # Fallback: estimate from file size (rough approximation for 192kbps)
        try:
            size_bytes = filepath.stat().st_size
            # 192kbps = 24000 bytes/sec
            return size_bytes / 24000
        except Exception:
            return None

    def validate_mp3(self, filepath: Path) -> Dict[str, Any]:
        """Validate MP3 file and return metadata."""
        result = {
            "exists": filepath.exists(),
            "size_bytes": 0,
            "duration_sec": None,
            "is_valid": False,
            "errors": [],
        }

        if not result["exists"]:
            result["errors"].append("File not found")
            return result

        result["size_bytes"] = filepath.stat().st_size

        if result["size_bytes"] < 1000:
            result["errors"].append("File too small (< 1KB)")
            return result

        # Check MP3 header
        try:
            with open(filepath, "rb") as f:
                header = f.read(3)
                # Check for ID3 tag or MP3 sync word
                if header[:3] == b"ID3" or (header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
                    result["is_valid"] = True
                else:
                    result["errors"].append("Invalid MP3 header")
        except Exception as e:
            result["errors"].append(f"Read error: {e}")

        if result["is_valid"]:
            result["duration_sec"] = self.get_mp3_duration(filepath)

        return result

    def run(self) -> DiagnosticSession:
        """Run the full diagnostic session."""
        import time
        self._start_time = time.time()

        print(f"\n{'#'*60}")
        print(f"# AUDIO PRODUCTION DIAGNOSTIC")
        print(f"# Session: {self.session_id}")
        print(f"# Series: {self.series}")
        print(f"# Output: {self.session_dir}")
        print(f"{'#'*60}\n")

        try:
            self._run_diagnostics()
        except Exception as e:
            self.error(f"Fatal error: {e}", {"type": type(e).__name__})
            import traceback
            traceback.print_exc()

        # Finalize session
        self.session.ended_at = self._timestamp()
        self.session.total_duration_ms = self._elapsed_ms()

        # Generate outputs
        self._generate_outputs()

        return self.session

    def _run_diagnostics(self):
        """Core diagnostic flow."""

        # === CHECKPOINT: Project Structure ===
        self.checkpoint("Project Structure", notes=["Verify directories and key files"])

        self.test("Site directory exists", self.site_dir.exists())
        self.test("Audio directory exists", self.audio_dir.exists())
        self.test("Manifest exists", self.manifest_path.exists())

        read_dir = self.site_dir / "read"
        self.test("Read directory exists", read_dir.exists())

        if read_dir.exists():
            chapter_files = list(read_dir.glob("chapter-*.html"))
            self.test("Chapter files present", len(chapter_files) > 0, f"{len(chapter_files)} files")

        self.end_checkpoint()

        # === CHECKPOINT: Audio Manifest ===
        self.checkpoint("Audio Manifest", notes=["Validate manifest structure and content"])

        manifest = None
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    manifest = json.load(f)
                self.test("Manifest is valid JSON", True)
                self.test("Manifest has chapters", len(manifest) > 0, f"{len(manifest)} entries")

                if self._current_checkpoint:
                    self._current_checkpoint.manifest_state = {
                        "total_entries": len(manifest),
                        "chapters_with_audio": sum(1 for v in manifest.values() if v is not None),
                        "chapters_pending": sum(1 for v in manifest.values() if v is None),
                    }
            except json.JSONDecodeError as e:
                self.test("Manifest is valid JSON", False, str(e))
                self.error("Manifest parse failed", {"error": str(e)})
        else:
            self.test("Manifest exists", False)

        self.end_checkpoint()

        # === CHECKPOINT: Audio Files ===
        self.checkpoint("Audio Files", notes=["Validate all audio files"])

        if self.audio_dir.exists():
            audio_files = list(self.audio_dir.glob("*.mp3"))
            self.test("Audio files present", len(audio_files) > 0, f"{len(audio_files)} files")

            for audio_file in sorted(audio_files):
                validation = self.validate_mp3(audio_file)

                if validation["is_valid"]:
                    self.session.audio_files_validated += 1
                    duration = validation["duration_sec"]
                    if duration:
                        self.session.total_audio_duration_sec += duration
                        self.test(
                            f"{audio_file.name}",
                            True,
                            f"{validation['size_bytes']/1024/1024:.1f}MB, {duration/60:.1f}min"
                        )
                    else:
                        self.test(f"{audio_file.name}", True, f"{validation['size_bytes']/1024/1024:.1f}MB")
                else:
                    self.test(f"{audio_file.name}", False, ", ".join(validation["errors"]))

                if self._current_checkpoint:
                    self._current_checkpoint.files_checked.append(audio_file.name)
        else:
            self.warn("Audio directory not found")

        self.end_checkpoint()

        # === CHECKPOINT: Manifest-Audio Alignment ===
        self.checkpoint("Manifest-Audio Alignment", notes=["Cross-reference manifest with actual files"])

        if manifest and self.audio_dir.exists():
            audio_files = {f.name for f in self.audio_dir.glob("*.mp3")}

            for chapter_slug, chapter_data in manifest.items():
                if chapter_data is None:
                    self._log(f"  {chapter_slug}: pending (no audio)", "info")
                    continue

                audio_path = chapter_data.get("audio", "")
                audio_filename = Path(audio_path).name if audio_path else None

                if audio_filename:
                    exists = audio_filename in audio_files
                    self.test(f"{chapter_slug} → {audio_filename}", exists)

                    # Validate duration if file exists
                    if exists and "duration" in chapter_data:
                        manifest_duration = chapter_data["duration"]
                        actual_path = self.audio_dir / audio_filename
                        actual_duration = self.get_mp3_duration(actual_path)

                        if actual_duration:
                            diff = abs(manifest_duration - actual_duration)
                            self.test(
                                f"  Duration match",
                                diff < 5,  # Allow 5 second tolerance
                                f"manifest={manifest_duration:.0f}s, actual={actual_duration:.0f}s"
                            )

                    # Validate sections
                    sections = chapter_data.get("sections", [])
                    if sections:
                        self._log(f"  {len(sections)} section markers defined", "info")

        self.end_checkpoint()

        # === CHECKPOINT: Chapter Integration ===
        self.checkpoint("Chapter HTML Integration", notes=["Verify player integration in chapter pages"])

        if read_dir.exists():
            chapter_files = sorted(read_dir.glob("chapter-*.html"))

            for chapter_file in chapter_files:
                content = chapter_file.read_text()

                has_player_css = "/css/chapter-player.css" in content
                has_player_js = "/js/chapter-player.js" in content
                has_error_tracker = "/js/error-tracker.js" in content
                has_favicon = "/favicon.svg" in content

                all_integrated = has_player_css and has_player_js and has_error_tracker and has_favicon

                missing = []
                if not has_player_css:
                    missing.append("CSS")
                if not has_player_js:
                    missing.append("JS")
                if not has_error_tracker:
                    missing.append("error-tracker")
                if not has_favicon:
                    missing.append("favicon")

                self.test(
                    chapter_file.name,
                    all_integrated,
                    f"missing: {', '.join(missing)}" if missing else "fully integrated"
                )

        self.end_checkpoint()

        # === CHECKPOINT: RSS Feed ===
        self.checkpoint("RSS Feed", notes=["Validate podcast feed if present"])

        feeds_dir = self.site_dir / "feeds"
        if feeds_dir.exists():
            feed_files = list(feeds_dir.glob("*.xml"))
            self.test("Feed files present", len(feed_files) > 0, f"{len(feed_files)} feeds")

            for feed_file in feed_files:
                try:
                    content = feed_file.read_text()
                    has_channel = "<channel>" in content
                    has_items = "<item>" in content
                    self.test(f"{feed_file.name}", has_channel and has_items)
                except Exception as e:
                    self.test(f"{feed_file.name}", False, str(e))
        else:
            self._log("No feeds directory found", "info")

        self.end_checkpoint()

        # === CHECKPOINT: Error Tracking ===
        self.checkpoint("Error Tracking Infrastructure", notes=["Verify telemetry setup"])

        error_tracker = self.site_dir / "js" / "error-tracker.js"
        self.test("error-tracker.js exists", error_tracker.exists())

        netlify_func = self.site_dir / "netlify" / "functions" / "error-report.js"
        self.test("Netlify function exists", netlify_func.exists())

        netlify_toml = self.site_dir / "netlify.toml"
        if netlify_toml.exists():
            toml_content = netlify_toml.read_text()
            has_functions = "functions" in toml_content
            self.test("netlify.toml has functions config", has_functions)

        self.end_checkpoint()

    def _generate_outputs(self):
        """Generate human and machine readable outputs."""

        # === TELEMETRY JSON ===
        telemetry_path = self.session_dir / "telemetry.json"

        session_dict = {
            "session_id": self.session.session_id,
            "started_at": self.session.started_at,
            "ended_at": self.session.ended_at,
            "series": self.session.series,
            "total_duration_ms": self.session.total_duration_ms,
            "tests_passed": self.session.tests_passed,
            "tests_failed": self.session.tests_failed,
            "audio_files_validated": self.session.audio_files_validated,
            "total_audio_duration_sec": self.session.total_audio_duration_sec,
            "checkpoints": [asdict(c) for c in self.session.checkpoints],
            "errors": [asdict(e) for e in self.session.errors],
            "warnings": [asdict(w) for w in self.session.warnings],
        }

        with open(telemetry_path, "w") as f:
            json.dump(session_dict, f, indent=2, default=str)

        print(f"\nTelemetry saved: {telemetry_path}")

        # === HUMAN REPORT ===
        report_path = self.session_dir / "report.md"

        total_minutes = self.session.total_audio_duration_sec / 60

        report = [
            f"# Audio Production Diagnostic Report",
            f"",
            f"**Session ID:** {self.session.session_id}",
            f"**Series:** {self.session.series}",
            f"**Started:** {self.session.started_at}",
            f"**Duration:** {self.session.total_duration_ms:.0f}ms" if self.session.total_duration_ms else "",
            f"",
            f"## Summary",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Tests Passed | {self.session.tests_passed} |",
            f"| Tests Failed | {self.session.tests_failed} |",
            f"| Audio Files Validated | {self.session.audio_files_validated} |",
            f"| Total Audio Duration | {total_minutes:.1f} minutes |",
            f"| Errors | {len(self.session.errors)} |",
            f"| Warnings | {len(self.session.warnings)} |",
            f"",
            f"## Checkpoints",
            f"",
        ]

        for cp in self.session.checkpoints:
            status = "✓ PASS" if cp.passed else "✗ FAIL"
            report.append(f"### {cp.name} [{status}]")
            report.append(f"")
            report.append(f"- Tests: {cp.tests_in_checkpoint}, Failures: {cp.failures_in_checkpoint}")
            if cp.notes:
                for note in cp.notes:
                    report.append(f"- {note}")
            if cp.files_checked:
                report.append(f"- Files checked: {len(cp.files_checked)}")
            if cp.manifest_state:
                report.append(f"- Manifest: {cp.manifest_state}")
            report.append(f"")

        if self.session.errors:
            report.append(f"## Errors")
            report.append(f"")
            for err in self.session.errors:
                report.append(f"- [{err.event_type}] {err.data.get('message', err.data)}")
            report.append(f"")

        if self.session.warnings:
            report.append(f"## Warnings")
            report.append(f"")
            for warn in self.session.warnings:
                report.append(f"- {warn.data.get('message', warn.data)}")
            report.append(f"")

        with open(report_path, "w") as f:
            f.write("\n".join(report))

        print(f"Report saved: {report_path}")

        # === SUMMARY ===
        print(f"\n{'='*60}")
        print(f"DIAGNOSTIC COMPLETE")
        print(f"{'='*60}")
        print(f"  Tests: {self.session.tests_passed} passed, {self.session.tests_failed} failed")
        print(f"  Audio: {self.session.audio_files_validated} files, {total_minutes:.1f} minutes")
        if self.session.total_duration_ms:
            print(f"  Duration: {self.session.total_duration_ms:.0f}ms")
        print(f"  Output: {self.session_dir}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Audio production diagnostic for Simulacrum Stories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--series", "-s",
        default="all",
        choices=["all", "saltmere", "millbrook"],
        help="Series to diagnose (default: all)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--step",
        action="store_true",
        help="Step mode: pause at each checkpoint",
    )

    args = parser.parse_args()

    runner = AudioDiagnosticRunner(
        series=args.series,
        verbose=args.verbose,
        step_mode=args.step,
    )

    session = runner.run()

    # Exit with failure code if tests failed
    sys.exit(1 if session.tests_failed > 0 else 0)


if __name__ == "__main__":
    main()
