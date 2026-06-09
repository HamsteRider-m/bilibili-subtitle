"""
Preflight checks for BBDown subtitle extraction.
"""

from __future__ import annotations

import json
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
    remediation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def is_ok(self) -> bool:
        return self.status in {CheckStatus.OK, CheckStatus.WARNING, CheckStatus.SKIPPED}

    def to_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "remediation": self.remediation,
            "details": self.details,
        }


@dataclass
class PreflightReport:
    checks: list[CheckResult]

    @property
    def can_proceed(self) -> bool:
        return all(check.is_ok for check in self.checks)

    def to_json(self) -> str:
        return json.dumps(
            {
                "checks": [check.to_json() for check in self.checks],
                "summary": {
                    "can_proceed": self.can_proceed,
                    "errors": sum(1 for check in self.checks if check.status == CheckStatus.ERROR),
                    "warnings": sum(1 for check in self.checks if check.status == CheckStatus.WARNING),
                },
            },
            ensure_ascii=False,
            indent=2,
        )

    def print_report(self) -> None:
        icons = {
            CheckStatus.OK: "✅",
            CheckStatus.WARNING: "⚠️ ",
            CheckStatus.ERROR: "❌",
            CheckStatus.SKIPPED: "⏭️ ",
        }
        for check in self.checks:
            print(f"{icons[check.status]} {check.name}: {check.message}")
            if check.remediation:
                print(f"   → {check.remediation}")


def check_bbdown() -> CheckResult:
    bbdown = shutil.which("BBDown")
    if not bbdown:
        local = Path(__file__).parent.parent / "BBDown"
        if local.exists():
            bbdown = str(local)
    if not bbdown:
        return CheckResult(
            name="BBDown",
            status=CheckStatus.ERROR,
            message="Not found in PATH",
            remediation="Run ./install.sh or install BBDown from https://github.com/nilaoda/BBDown/releases",
        )

    try:
        result = subprocess.run(
            [bbdown, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        version = (result.stdout or result.stderr).strip().splitlines()[0]
    except Exception:
        version = "installed"

    return CheckResult(
        name="BBDown",
        status=CheckStatus.OK,
        message=version,
        details={"path": bbdown},
    )


def check_bbdown_auth() -> CheckResult:
    bbdown_data = Path.home() / "BBDown.data"
    if bbdown_data.exists():
        return CheckResult(
            name="BBDown Auth",
            status=CheckStatus.OK,
            message="BBDown.data found",
            details={"path": str(bbdown_data)},
        )
    return CheckResult(
        name="BBDown Auth",
        status=CheckStatus.WARNING,
        message="BBDown.data not found",
        remediation="Run BBDown login if target subtitles require authentication",
    )


def check_output_dir(path: str | Path = "./output") -> CheckResult:
    output_dir = Path(path)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        probe = output_dir / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except Exception as exc:
        return CheckResult(
            name="Output Directory",
            status=CheckStatus.ERROR,
            message=f"Cannot write to {output_dir}",
            remediation=str(exc),
        )
    return CheckResult(
        name="Output Directory",
        status=CheckStatus.OK,
        message=f"Writable: {output_dir}",
    )


def run_preflight(*, include_auth: bool = True, output_dir: str | Path = "./output") -> PreflightReport:
    checks = [check_bbdown()]
    if include_auth:
        checks.append(check_bbdown_auth())
    checks.append(check_output_dir(output_dir))
    return PreflightReport(checks=checks)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Preflight checks")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--skip-auth", action="store_true", help="Skip auth check")
    parser.add_argument("-o", "--output-dir", default="./output", help="Output directory to test")
    args = parser.parse_args()

    report = run_preflight(include_auth=not args.skip_auth, output_dir=args.output_dir)
    if args.json:
        print(report.to_json())
    else:
        report.print_report()
        print()
        print("✅ Ready to proceed" if report.can_proceed else "❌ Fix errors before proceeding")
    return 0 if report.can_proceed else 1


if __name__ == "__main__":
    raise SystemExit(main())
