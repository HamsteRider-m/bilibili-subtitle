"""
Error taxonomy for BBDown-only subtitle extraction.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorLevel(Enum):
    FATAL = "fatal"
    RECOVERABLE = "recoverable"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Remediation:
    hint: str
    command: str | None = None
    doc_url: str | None = None


@dataclass
class SkillError(Exception):
    code: str
    level: ErrorLevel
    message: str
    remediation: Remediation | None = None

    def __str__(self) -> str:
        parts = [f"[{self.code}] {self.message}"]
        if self.remediation:
            parts.append(f"  Hint: {self.remediation.hint}")
            if self.remediation.command:
                parts.append(f"  Run: {self.remediation.command}")
            if self.remediation.doc_url:
                parts.append(f"  See: {self.remediation.doc_url}")
        return "\n".join(parts)

    def to_json(self) -> dict:
        return {
            "code": self.code,
            "level": self.level.value,
            "message": self.message,
            "remediation": {
                "hint": self.remediation.hint,
                "command": self.remediation.command,
                "doc_url": self.remediation.doc_url,
            }
            if self.remediation
            else None,
        }


class BBDownNotFoundError(SkillError):
    def __init__(self) -> None:
        super().__init__(
            code="E001",
            level=ErrorLevel.FATAL,
            message="BBDown not found in PATH",
            remediation=Remediation(
                hint="Install BBDown from GitHub nightly builds",
                command="./install.sh",
                doc_url="https://github.com/nilaoda/BBDown",
            ),
        )


class BBDownAuthError(SkillError):
    def __init__(self, details: str = "") -> None:
        super().__init__(
            code="E002",
            level=ErrorLevel.FATAL,
            message=f"BBDown authentication required{': ' + details if details else ''}",
            remediation=Remediation(
                hint="Login to Bilibili with BBDown",
                command="BBDown login",
            ),
        )


class BBDownDownloadError(SkillError):
    def __init__(self, url: str, reason: str = "") -> None:
        super().__init__(
            code="E003",
            level=ErrorLevel.RECOVERABLE,
            message=f"Failed to download subtitles: {url}{': ' + reason if reason else ''}",
            remediation=Remediation(
                hint="Check the URL, network, login status, or selected subtitle language",
                command="BBDown login",
            ),
        )


class NoSubtitleError(SkillError):
    def __init__(self, video_id: str = "video") -> None:
        super().__init__(
            code="E004",
            level=ErrorLevel.RECOVERABLE,
            message=f"{video_id} has no downloadable subtitles",
            remediation=Remediation(
                hint="Try another language or confirm the video has Bilibili subtitles",
                command="pixi run python -m bilibili_subtitle <URL> --language zh-Hans",
            ),
        )


class InvalidURLError(SkillError):
    def __init__(self, url: str) -> None:
        super().__init__(
            code="E005",
            level=ErrorLevel.FATAL,
            message=f"Invalid Bilibili URL or ID: {url}",
            remediation=Remediation(
                hint="Provide a bilibili.com URL, BV ID, or av ID",
            ),
        )


class OutputWriteError(SkillError):
    def __init__(self, path: str, reason: str = "") -> None:
        super().__init__(
            code="E006",
            level=ErrorLevel.FATAL,
            message=f"Cannot write output to {path}{': ' + reason if reason else ''}",
            remediation=Remediation(
                hint="Check that the output directory exists and is writable",
            ),
        )


class SubtitleContentError(SkillError):
    def __init__(self, reason: str = "") -> None:
        super().__init__(
            code="E007",
            level=ErrorLevel.RECOVERABLE,
            message=f"Downloaded subtitle content is invalid{': ' + reason if reason else ''}",
            remediation=Remediation(
                hint="Retry the download or inspect the subtitle file produced by BBDown",
            ),
        )


def exit_code_for_error(error: SkillError) -> int:
    if error.level == ErrorLevel.FATAL:
        return 1
    if error.level == ErrorLevel.RECOVERABLE:
        return 2
    return 0
