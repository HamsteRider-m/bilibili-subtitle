"""
Preflight checks for skill execution.

Usage:
    pixi run python -m bilibili_subtitle --check
    pixi run python -m bilibili_subtitle --check --json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CheckStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "remediation": self.remediation,
        }


@dataclass
class PreflightReport:
    results: list[CheckResult]

    @property
    def has_errors(self) -> bool:
        return any(r.status == CheckStatus.ERROR for r in self.results)

    @property
    def has_warnings(self) -> bool:
        return any(r.status == CheckStatus.WARNING for r in self.results)

    @property
    def can_proceed(self) -> bool:
        return not self.has_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [r.to_dict() for r in self.results],
            "summary": {
                "total": len(self.results),
                "ok": sum(1 for r in self.results if r.status == CheckStatus.OK),
                "warnings": sum(
                    1 for r in self.results if r.status == CheckStatus.WARNING
                ),
                "errors": sum(1 for r in self.results if r.status == CheckStatus.ERROR),
                "can_proceed": self.can_proceed,
            },
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def print_report(self) -> None:
        for r in self.results:
            icon = {
                CheckStatus.OK: "✅",
                CheckStatus.WARNING: "⚠️",
                CheckStatus.ERROR: "❌",
                CheckStatus.SKIPPED: "⏭️",
            }[r.status]
            print(f"{icon} {r.name}: {r.message}")
            if r.remediation:
                print(f"   → {r.remediation}")


def check_bbdown() -> CheckResult:
    bbdown_path = shutil.which("BBDown")
    if bbdown_path:
        try:
            result = subprocess.run(
                ["BBDown", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            version = version_line.split()[-1] if version_line else "unknown"
            return CheckResult(
                name="BBDown",
                status=CheckStatus.OK,
                message=f"Installed ({version})",
                details={"path": bbdown_path, "version": version},
            )
        except Exception as e:
            return CheckResult(
                name="BBDown",
                status=CheckStatus.WARNING,
                message=f"Installed but check failed: {e}",
                details={"path": bbdown_path},
            )
    return CheckResult(
        name="BBDown",
        status=CheckStatus.ERROR,
        message="Not found in PATH",
        remediation="Run: ./install.sh",
    )


def check_bbdown_auth() -> CheckResult:
    bbdown_data = Path.home() / "BBDown.data"
    if bbdown_data.exists():
        try:
            content = bbdown_data.read_text()
            has_sessdata = "SESSDATA" in content
            if has_sessdata:
                return CheckResult(
                    name="BBDown Auth",
                    status=CheckStatus.OK,
                    message="Logged in",
                    details={"cookie_file": str(bbdown_data)},
                )
            return CheckResult(
                name="BBDown Auth",
                status=CheckStatus.ERROR,
                message="Cookie file exists but no SESSDATA",
                remediation="Run: BBDown login",
            )
        except Exception as e:
            return CheckResult(
                name="BBDown Auth",
                status=CheckStatus.WARNING,
                message=f"Cannot read cookie file: {e}",
                remediation="Run: BBDown login",
            )
    return CheckResult(
        name="BBDown Auth",
        status=CheckStatus.ERROR,
        message="Not logged in",
        remediation="Run: BBDown login",
    )


def check_ffmpeg() -> CheckResult:
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
            return CheckResult(
                name="ffmpeg",
                status=CheckStatus.OK,
                message="Installed",
                details={
                    "path": ffmpeg_path,
                    "version": version_line.split()[2]
                    if len(version_line.split()) > 2
                    else "unknown",
                },
            )
        except Exception:
            return CheckResult(
                name="ffmpeg",
                status=CheckStatus.WARNING,
                message="Installed but version check failed",
                details={"path": ffmpeg_path},
            )
    return CheckResult(
        name="ffmpeg",
        status=CheckStatus.ERROR,
        message="Not found",
        remediation="Run: pixi install",
    )


def check_anthropic_key() -> CheckResult:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        return CheckResult(
            name="ANTHROPIC_API_KEY",
            status=CheckStatus.OK,
            message="Configured",
            details={"key_hint": masked},
        )
    return CheckResult(
        name="ANTHROPIC_API_KEY",
        status=CheckStatus.WARNING,
        message="Not set (required for proofreading/summarization)",
        remediation='export ANTHROPIC_API_KEY="your-key"',
    )


def check_dashscope_key() -> CheckResult:
    key = os.environ.get("DASHSCOPE_API_KEY")
    if key:
        masked = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
        return CheckResult(
            name="DASHSCOPE_API_KEY",
            status=CheckStatus.OK,
            message="Configured",
            details={"key_hint": masked},
        )
    return CheckResult(
        name="DASHSCOPE_API_KEY",
        status=CheckStatus.WARNING,
        message="Not set (required for ASR transcription of videos without subtitles)",
        remediation='export DASHSCOPE_API_KEY="your-key"',
    )


def check_python_deps() -> CheckResult:
    missing: list[str] = []
    try:
        import anthropic  # noqa: F401
    except ImportError:
        missing.append("anthropic")

    try:
        import dashscope  # noqa: F401
    except ImportError:
        missing.append("dashscope")

    if not missing:
        return CheckResult(
            name="Python Dependencies",
            status=CheckStatus.OK,
            message="All installed",
        )
    return CheckResult(
        name="Python Dependencies",
        status=CheckStatus.WARNING,
        message=f"Missing: {', '.join(missing)}",
        remediation="Run: pixi run pip install -e .[claude,transcribe]",
    )


def run_preflight(*, include_auth: bool = True) -> PreflightReport:
    checks = [
        check_bbdown(),
        check_ffmpeg(),
        check_anthropic_key(),
        check_dashscope_key(),
        check_python_deps(),
    ]
    if include_auth:
        checks.insert(1, check_bbdown_auth())
    return PreflightReport(results=checks)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Preflight checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--skip-auth", action="store_true", help="Skip auth check")
    args = parser.parse_args()

    report = run_preflight(include_auth=not args.skip_auth)

    if args.json:
        print(report.to_json())
    else:
        report.print_report()
        print()
        if report.can_proceed:
            print("✅ Ready to proceed")
        else:
            print("❌ Fix errors before proceeding")

    return 0 if report.can_proceed else 1


if __name__ == "__main__":
    exit(main())
