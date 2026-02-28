"""
Error taxonomy with severity levels and remediation hints.

Level 1: FATAL - Cannot proceed, requires user action
Level 2: RECOVERABLE - Can continue with degraded functionality
Level 3: WARNING - Non-critical, proceed with caution
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal


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
                hint="Install BBDown from GitHub releases",
                command="./install.sh",
                doc_url="https://github.com/nilaoda/BBDown/releases",
            ),
        )


class BBDownAuthError(SkillError):
    def __init__(self, details: str = "") -> None:
        super().__init__(
            code="E002",
            level=ErrorLevel.FATAL,
            message=f"BBDown authentication required{': ' + details if details else ''}",
            remediation=Remediation(
                hint="Login to Bilibili via BBDown",
                command="BBDown login",
            ),
        )


class BBDownDownloadError(SkillError):
    def __init__(self, url: str, reason: str = "") -> None:
        super().__init__(
            code="E003",
            level=ErrorLevel.RECOVERABLE,
            message=f"Failed to download: {url}{': ' + reason if reason else ''}",
            remediation=Remediation(
                hint="Check URL validity or network connection",
            ),
        )


class NoSubtitleError(SkillError):
    def __init__(self, video_id: str) -> None:
        super().__init__(
            code="E004",
            level=ErrorLevel.RECOVERABLE,
            message=f"Video {video_id} has no subtitles",
            remediation=Remediation(
                hint="ASR transcription will be attempted if DASHSCOPE_API_KEY is set",
            ),
        )


class ASRConfigError(SkillError):
    def __init__(self) -> None:
        super().__init__(
            code="E005",
            level=ErrorLevel.FATAL,
            message="DASHSCOPE_API_KEY not configured",
            remediation=Remediation(
                hint="Set DASHSCOPE_API_KEY for ASR transcription",
                command='export DASHSCOPE_API_KEY="your-key"',
            ),
        )


class AnthropicConfigError(SkillError):
    def __init__(self, feature: str = "proofreading") -> None:
        super().__init__(
            code="E006",
            level=ErrorLevel.RECOVERABLE,
            message=f"ANTHROPIC_API_KEY not configured, {feature} skipped",
            remediation=Remediation(
                hint="Set ANTHROPIC_API_KEY or use --skip-proofread --skip-summary",
                command='export ANTHROPIC_API_KEY="your-key"',
            ),
        )


class FFmpegNotFoundError(SkillError):
    def __init__(self) -> None:
        super().__init__(
            code="E007",
            level=ErrorLevel.FATAL,
            message="ffmpeg not found",
            remediation=Remediation(
                hint="ffmpeg is required for audio conversion",
                command="pixi install",
            ),
        )


class InvalidURLError(SkillError):
    def __init__(self, url: str) -> None:
        super().__init__(
            code="E008",
            level=ErrorLevel.FATAL,
            message=f"Invalid Bilibili URL or BV ID: {url}",
            remediation=Remediation(
                hint="Provide a valid URL (e.g., https://www.bilibili.com/video/BVxxx) or BV ID",
            ),
        )


class OutputWriteError(SkillError):
    def __init__(self, path: str, reason: str = "") -> None:
        super().__init__(
            code="E009",
            level=ErrorLevel.FATAL,
            message=f"Cannot write to {path}{': ' + reason if reason else ''}",
            remediation=Remediation(
                hint="Check directory permissions or use -o to specify a different output directory",
            ),
        )


class VideoNotFoundError(SkillError):
    def __init__(self, video_id: str) -> None:
        super().__init__(
            code="E010",
            level=ErrorLevel.FATAL,
            message=f"Video not found or unavailable: {video_id}",
            remediation=Remediation(
                hint="The video may be deleted, private, or region-restricted",
            ),
        )


class RateLimitError(SkillError):
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            code="E011",
            level=ErrorLevel.RECOVERABLE,
            message=f"Rate limited, retry after {retry_after}s",
            remediation=Remediation(
                hint="Wait and retry, or reduce request frequency",
            ),
        )


class SubtitleContentError(SkillError):
    def __init__(self, reason: str = "empty segments") -> None:
        super().__init__(
            code="E012",
            level=ErrorLevel.RECOVERABLE,
            message=f"Subtitle content issue: {reason}",
            remediation=Remediation(
                hint="Retry download or try a different subtitle language",
            ),
        )


def exit_code_for_error(error: SkillError) -> int:
    return {
        ErrorLevel.FATAL: 1,
        ErrorLevel.RECOVERABLE: 2,
        ErrorLevel.WARNING: 0,
    }[error.level]
