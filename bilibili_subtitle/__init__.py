"""
Bilibili Subtitle Extraction Skill.

Extract subtitles from Bilibili videos with ASR fallback for videos without subtitles.
"""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = [
    "BBDownClient",
    "BBDownError",
    "VideoInfo",
    "SubtitleInfo",
    "detect_subtitles",
    "VideoMetadata",
    "parse_bilibili_ref",
    "VideoRef",
    "SkillError",
    "ErrorLevel",
    "Remediation",
    "PreflightReport",
    "run_preflight",
    "ExecutionResult",
    "SubtitleOutput",
    "ExitCode",
    "build_cli_command",
]

from .bbdown_client import BBDownClient, BBDownError, SubtitleInfo, VideoInfo
from .contract import (
    ExitCode,
    ExecutionResult,
    SubtitleOutput,
    build_cli_command,
)
from .detector import VideoMetadata, detect_subtitles
from .errors import ErrorLevel, Remediation, SkillError
from .preflight import PreflightReport, run_preflight
from .url_parser import VideoRef, parse_bilibili_ref
