"""
Sub-skill invocation contract.

Stable interface for parent skills to invoke the BBDown subtitle extractor.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ExitCode(Enum):
    SUCCESS = 0
    FATAL_ERROR = 1
    RECOVERABLE_ERROR = 2


@dataclass
class SubtitleOutput:
    video_id: str
    title: str | None
    transcript: Path
    srt: Path | None = None
    vtt: Path | None = None

    def to_json(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "files": {
                "transcript": str(self.transcript),
                "srt": str(self.srt) if self.srt else None,
                "vtt": str(self.vtt) if self.vtt else None,
            },
        }


@dataclass
class ExecutionResult:
    exit_code: ExitCode
    output: SubtitleOutput | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return self.exit_code == ExitCode.SUCCESS

    def to_json(self) -> dict[str, Any]:
        return {
            "exit_code": self.exit_code.value,
            "success": self.success,
            "output": self.output.to_json() if self.output else None,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    def to_json_string(self) -> str:
        return json.dumps(self.to_json(), ensure_ascii=False, indent=2)


def build_cli_command(
    url_or_id: str,
    *,
    output_dir: str | Path | None = None,
    language: str = "zh-Hans",
    json_output: bool = False,
    verbose: bool = False,
) -> list[str]:
    cmd = [
        "pixi",
        "run",
        "python",
        "-m",
        "bilibili_subtitle",
        url_or_id,
    ]
    if output_dir is not None:
        cmd.extend(["-o", str(output_dir)])
    if language:
        cmd.extend(["--language", language])
    if json_output:
        cmd.append("--json-output")
    if verbose:
        cmd.append("--verbose")
    return cmd


def parse_json_output(output: str) -> ExecutionResult:
    data = json.loads(output)
    subtitle_output = None
    if data.get("output"):
        files = data["output"].get("files", {})
        subtitle_output = SubtitleOutput(
            video_id=data["output"]["video_id"],
            title=data["output"].get("title"),
            transcript=Path(files["transcript"]),
            srt=Path(files["srt"]) if files.get("srt") else None,
            vtt=Path(files["vtt"]) if files.get("vtt") else None,
        )
    return ExecutionResult(
        exit_code=ExitCode(data["exit_code"]),
        output=subtitle_output,
        warnings=data.get("warnings", []),
        errors=data.get("errors", []),
    )


CONTRACT_VERSION = "1.0.0"
REQUIRED_OUTPUTS = ["*.transcript.md"]
OPTIONAL_OUTPUTS = ["*.srt", "*.vtt"]
