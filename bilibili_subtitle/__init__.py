"""
Bilibili subtitle extraction with BBDown.
"""

from __future__ import annotations

__version__ = "0.2.0"

from .bbdown_client import BBDownClient, BBDownError, SubtitleInfo, VideoInfo
from .contract import (
    CONTRACT_VERSION,
    OPTIONAL_OUTPUTS,
    REQUIRED_OUTPUTS,
    ExitCode,
    ExecutionResult,
    SubtitleOutput,
    build_cli_command,
    parse_json_output,
)
from .detector import VideoMetadata, detect_subtitles
from .errors import ErrorLevel, Remediation, SkillError
from .preflight import PreflightReport, run_preflight
from .url_parser import VideoRef, parse_bilibili_ref

__all__ = [
    "__version__",
    "BBDownClient",
    "BBDownError",
    "SubtitleInfo",
    "VideoInfo",
    "CONTRACT_VERSION",
    "OPTIONAL_OUTPUTS",
    "REQUIRED_OUTPUTS",
    "ExitCode",
    "ExecutionResult",
    "SubtitleOutput",
    "build_cli_command",
    "parse_json_output",
    "VideoMetadata",
    "detect_subtitles",
    "ErrorLevel",
    "Remediation",
    "SkillError",
    "PreflightReport",
    "run_preflight",
    "VideoRef",
    "parse_bilibili_ref",
]
