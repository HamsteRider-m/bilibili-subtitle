from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SubtitleInfo:
    has_subtitle: bool
    has_ai_subtitle: bool
    languages: list[str]


@dataclass(frozen=True, slots=True)
class VideoInfo:
    video_id: str
    title: str | None
    subtitle_info: SubtitleInfo
    subtitle_files: list[Path]


class BBDownError(Exception):
    pass


class BBDownClient:
    def __init__(self) -> None:
        self._bbdown = self._find_bbdown()

    def _find_bbdown(self) -> str:
        path = shutil.which("BBDown")
        if path:
            return path
        local = Path(__file__).parent.parent / "BBDown"
        if local.exists():
            return str(local)
        raise BBDownError(
            "BBDown not found. Download from: https://github.com/nilaoda/BBDown/releases"
        )

    def _base_args(self) -> list[str]:
        return [self._bbdown]

    def _run(
        self, args: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=check,
            )
        except subprocess.CalledProcessError as e:
            raise BBDownError(f"BBDown failed: {e.stderr}") from e

    def get_video_info(self, url: str, work_dir: Path) -> VideoInfo:
        work_dir.mkdir(parents=True, exist_ok=True)
        video_id = self._extract_video_id(url)

        existing_files = set(work_dir.glob(f"{video_id}*.srt"))

        args = self._base_args() + [
            "--sub-only",
            "--skip-ai",
            "false",
            "-F",
            video_id,
            "--work-dir",
            str(work_dir),
            url,
        ]
        result = self._run(args, check=False)
        output = result.stdout + result.stderr

        new_files = sorted(set(work_dir.glob(f"{video_id}*.srt")) - existing_files)

        title = self._extract_title(output)
        subtitle_info = self._extract_subtitle_info(output)
        return VideoInfo(
            video_id=video_id,
            title=title,
            subtitle_info=subtitle_info,
            subtitle_files=new_files,
        )

    def _extract_video_id(self, url: str) -> str:
        bv_match = re.search(r"(BV[0-9A-Za-z]{10})", url)
        if bv_match:
            return bv_match.group(1)
        av_match = re.search(r"av(\d+)", url, re.IGNORECASE)
        if av_match:
            return f"av{av_match.group(1)}"
        return "unknown"

    def _extract_title(self, output: str) -> str | None:
        for line in output.splitlines():
            cleaned = re.sub(r"^\[[^\]]+\]\s*-\s*", "", line).strip()
            match = re.search(r"(?:视频标题|标题|Title)\s*[:：]\s*(.+)", cleaned)
            if match:
                return match.group(1).strip()
        return None

    def _extract_subtitle_info(self, output: str) -> SubtitleInfo:
        has_subtitle = False
        has_ai_subtitle = False
        languages: list[str] = []

        for line in output.splitlines():
            if "下载字幕" in line:
                has_subtitle = True
                if "ai-" in line.lower() or "AI识别" in line:
                    has_ai_subtitle = True
                lang_match = re.search(r"(ai-)?zh", line.lower())
                if lang_match and "zh" not in languages:
                    languages.append("zh")

        return SubtitleInfo(
            has_subtitle=has_subtitle,
            has_ai_subtitle=has_ai_subtitle,
            languages=languages,
        )

    def download_audio(self, url: str, work_dir: Path) -> Path:
        work_dir.mkdir(parents=True, exist_ok=True)
        video_id = self._extract_video_id(url)

        args = self._base_args() + [
            "--audio-only",
            "-F",
            video_id,
            "--work-dir",
            str(work_dir),
            url,
        ]
        self._run(args)

        audio_files = list(work_dir.glob(f"{video_id}.*"))
        audio_exts = (".m4a", ".aac", ".mp3", ".flac", ".wav")
        for f in audio_files:
            if f.suffix.lower() in audio_exts:
                return f

        all_audio = [f for f in work_dir.iterdir() if f.suffix.lower() in audio_exts]
        if all_audio:
            return sorted(all_audio, key=lambda p: p.stat().st_mtime, reverse=True)[0]

        raise BBDownError("Audio download produced no output.")
