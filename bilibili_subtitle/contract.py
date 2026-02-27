"""
Sub-skill invocation contract.

Standardized interface for parent skills to invoke this skill.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class ExitCode(Enum):
    SUCCESS = 0
    FATAL_ERROR = 1
    RECOVERABLE_ERROR = 2
    PARTIAL_SUCCESS = 3


@dataclass
class SubtitleOutput:
    video_id: str
    title: str | None = None
    transcript_md: Path | None = None
    srt_file: Path | None = None
    vtt_file: Path | None = None
    summary_json: Path | None = None
    summary_md: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "title": self.title,
            "files": {
                "transcript": str(self.transcript_md) if self.transcript_md else None,
                "srt": str(self.srt_file) if self.srt_file else None,
                "vtt": str(self.vtt_file) if self.vtt_file else None,
                "summary_json": str(self.summary_json) if self.summary_json else None,
                "summary_md": str(self.summary_md) if self.summary_md else None,
            },
        }


@dataclass
class ExecutionResult:
    exit_code: ExitCode
    output: SubtitleOutput | None = None
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.exit_code in (ExitCode.SUCCESS, ExitCode.PARTIAL_SUCCESS)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exit_code": self.exit_code.value,
            "success": self.success,
            "output": self.output.to_dict() if self.output else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def write_manifest(self, path: Path) -> None:
        path.write_text(self.to_json(), encoding="utf-8")


def build_cli_command(
    url_or_id: str,
    output_dir: str | Path,
    *,
    skip_proofread: bool = False,
    skip_summary: bool = True,
    output_lang: Literal["zh", "en", "zh+en"] = "zh",
    cache_dir: str | Path | None = None,
    verbose: bool = False,
) -> list[str]:
    cmd = [
        "pixi",
        "run",
        "python",
        "-m",
        "bilibili_subtitle",
        url_or_id,
        "-o",
        str(output_dir),
        "--output-lang",
        output_lang,
    ]
    if skip_proofread:
        cmd.append("--skip-proofread")
    if skip_summary:
        cmd.append("--skip-summary")
    if cache_dir:
        cmd.extend(["--cache-dir", str(cache_dir)])
    if verbose:
        cmd.append("-v")
    return cmd


def parse_execution_result(
    output_dir: Path, exit_code: int, stderr: str = ""
) -> ExecutionResult:
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []

    video_id = _extract_video_id_from_dir(output_dir)

    srt_files = list(output_dir.glob("*.srt"))
    vtt_files = list(output_dir.glob("*.vtt"))
    transcript_files = list(output_dir.glob("*.transcript.md"))
    summary_json_files = list(output_dir.glob("*.summary.json"))
    summary_md_files = list(output_dir.glob("*.summary.md"))

    has_transcript = bool(transcript_files)
    has_subtitle = bool(srt_files)

    result_exit_code = (
        ExitCode(exit_code) if exit_code in (0, 1, 2, 3) else ExitCode.FATAL_ERROR
    )

    if stderr:
        parsed_errors = _parse_stderr(stderr)
        errors.extend(parsed_errors)

    if not has_transcript and not has_subtitle:
        if exit_code == 0:
            result_exit_code = ExitCode.PARTIAL_SUCCESS
            warnings.append("No transcript or subtitle files generated")
        else:
            result_exit_code = ExitCode.FATAL_ERROR

    output = None
    if video_id:
        output = SubtitleOutput(
            video_id=video_id,
            transcript_md=transcript_files[0] if transcript_files else None,
            srt_file=srt_files[0] if srt_files else None,
            vtt_file=vtt_files[0] if vtt_files else None,
            summary_json=summary_json_files[0] if summary_json_files else None,
            summary_md=summary_md_files[0] if summary_md_files else None,
        )

    return ExecutionResult(
        exit_code=result_exit_code,
        output=output,
        errors=errors,
        warnings=warnings,
        metadata={
            "output_dir": str(output_dir),
        },
    )


def _extract_video_id_from_dir(output_dir: Path) -> str | None:
    for f in output_dir.iterdir():
        if f.suffix in (".srt", ".md", ".json", ".vtt"):
            name = f.stem
            if name.endswith(".transcript"):
                name = name[:-10]
            if name.endswith(".summary"):
                name = name[:-7]
            if name.endswith((".zh", ".en")):
                name = name[:-3]
            if name.startswith("BV") or name.startswith("av"):
                return name
    return None


def _parse_stderr(stderr: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        if "error" in line.lower() or "failed" in line.lower():
            errors.append(
                {
                    "type": "error",
                    "message": line,
                }
            )
        elif "warning" in line.lower():
            errors.append(
                {
                    "type": "warning",
                    "message": line,
                }
            )
    return errors


CONTRACT_VERSION = "1.0.0"
REQUIRED_OUTPUTS = ["*.transcript.md"]
OPTIONAL_OUTPUTS = ["*.srt", "*.vtt", "*.summary.json", "*.summary.md"]
