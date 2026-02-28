from __future__ import annotations

import logging
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Compiled regexes for subtitle info extraction (Fix 5) ---
_SUBTITLE_LINE_RE = re.compile(
    r"下载字幕|download.*subtitle|saving subtitle|字幕下载", re.IGNORECASE
)
_AI_MARKER_RE = re.compile(
    r"ai[_\-]|AI识别|auto.?generated|asr|自动识别", re.IGNORECASE
)
_LANG_RE = re.compile(
    r"\b(zh-hans|zh-hant|zh|en|ja|ko)\b", re.IGNORECASE
)

_LANG_NORMALIZE: dict[str, str] = {
    "zh-hans": "zh",
    "zh-hant": "zh-hant",
}

# Errors that should NOT be retried
_FATAL_PATTERNS = re.compile(
    r"login|auth|cookie|not found|不存在|404|权限", re.IGNORECASE
)


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
        self,
        args: list[str],
        *,
        check: bool = True,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        """Run BBDown with retry + timeout (Fix 1)."""
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            try:
                result = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=timeout,
                )
                # If check requested and non-zero, see if it's fatal
                if check and result.returncode != 0:
                    combined = result.stdout + result.stderr
                    if _FATAL_PATTERNS.search(combined):
                        raise BBDownError(f"BBDown failed (non-retryable): {result.stderr}")
                    # Retryable error
                    last_exc = BBDownError(f"BBDown failed (rc={result.returncode}): {result.stderr}")
                    logger.warning(
                        "BBDown attempt %d/%d failed (rc=%d), retrying in %.1fs",
                        attempt + 1, max_retries, result.returncode, retry_delay * (2 ** attempt),
                    )
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                return result

            except subprocess.TimeoutExpired:
                last_exc = BBDownError(f"BBDown timed out after {timeout}s")
                logger.warning(
                    "BBDown attempt %d/%d timed out, retrying in %.1fs",
                    attempt + 1, max_retries, retry_delay * (2 ** attempt),
                )
                time.sleep(retry_delay * (2 ** attempt))
                continue

            except BBDownError:
                raise

            except Exception as e:
                raise BBDownError(f"BBDown failed: {e}") from e

        raise last_exc or BBDownError("BBDown failed after retries")

    def get_video_info(
        self, url: str, work_dir: Path, *, lang: str | None = "zh-Hans"
    ) -> VideoInfo:
        """Download subtitles and return video info (Fix 4, 7)."""
        work_dir.mkdir(parents=True, exist_ok=True)
        video_id = self._extract_video_id(url)

        existing_files = set(work_dir.glob(f"{video_id}*.srt")) | set(
            work_dir.glob(f"{video_id}*.vtt")
        )

        args = self._base_args() + [
            "--sub-only",
            "--skip-ai",
            "false",
            "-F",
            video_id,
            "--work-dir",
            str(work_dir),
        ]
        if lang is not None:
            args += ["--select-lang", lang]
        args.append(url)

        result = self._run(args, check=False)
        output = result.stdout + result.stderr

        new_files = sorted(
            (set(work_dir.glob(f"{video_id}*.srt")) | set(work_dir.glob(f"{video_id}*.vtt")))
            - existing_files
        )

        # Fix 7: raise on non-zero exit when no files were produced
        if result.returncode != 0 and not new_files:
            logger.error("BBDown exited %d with no subtitle files", result.returncode)
            raise BBDownError(
                f"BBDown failed (rc={result.returncode}): {output[-500:]}"
            )

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
        """Parse BBDown output for subtitle metadata (Fix 5)."""
        has_subtitle = False
        has_ai_subtitle = False
        languages: list[str] = []

        for line in output.splitlines():
            if not _SUBTITLE_LINE_RE.search(line):
                continue
            has_subtitle = True
            if _AI_MARKER_RE.search(line):
                has_ai_subtitle = True
            lang_match = _LANG_RE.search(line)
            if lang_match:
                raw = lang_match.group(1).lower()
                normalized = _LANG_NORMALIZE.get(raw, raw)
                if normalized not in languages:
                    languages.append(normalized)

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
