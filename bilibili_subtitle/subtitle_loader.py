from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from .converters.srt_converter import srt_to_segments
from .errors import SubtitleContentError
from .segment import Segment

logger = logging.getLogger(__name__)

# VTT timestamp pattern: 00:01:23.456 (dot before ms)
_VTT_TS_RE = re.compile(r"(\d{2}:\d{2}:\d{2})\.(\d{3})")


def _normalize_vtt_timestamps(text: str) -> str:
    """Convert VTT timestamps (dot separator) to SRT format (comma separator).

    Only touches timestamp lines — preserves dots in subtitle text content.
    """
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        # A timestamp line contains --> and HH:MM:SS.mmm patterns
        if "-->" in line and _VTT_TS_RE.search(line):
            line = _VTT_TS_RE.sub(r"\1,\2", line)
        out.append(line)
    return "".join(out)


def check_title_relevance(segments: list[Segment], title: str | None) -> bool:
    """Check if subtitle content is relevant to the video title.

    Uses character bigram matching for CJK titles and word matching for Latin titles.
    Returns True (relevant) if any title token appears in the subtitle text,
    or if the check cannot be performed (title too short / None).
    """
    if not title or len(title) <= 2:
        return True  # Can't check, assume relevant

    subtitle_text = " ".join(seg.text for seg in segments)
    if not subtitle_text.strip():
        return True  # Empty text handled elsewhere

    # Detect if title is primarily CJK
    cjk_chars = sum(1 for c in title if "\u4e00" <= c <= "\u9fff")
    if cjk_chars > len(title) * 0.3:
        # CJK: generate character bigrams
        clean = re.sub(r"\s+", "", title)
        bigrams = {clean[i : i + 2] for i in range(len(clean) - 1)}
        return any(bg in subtitle_text for bg in bigrams)
    else:
        # Latin/mixed: split by whitespace, filter short words
        words = {w.lower() for w in title.split() if len(w) >= 3}
        if not words:
            return True
        text_lower = subtitle_text.lower()
        return any(w in text_lower for w in words)


@dataclass
class LoadResult:
    """Result of loading subtitles, with optional relevance warning."""
    segments: list[Segment]
    relevant: bool = True


def load_segments_from_subtitle_file(
    path: str | Path, *, title: str | None = None
) -> LoadResult:
    """Load subtitle segments from SRT or VTT file.

    Returns LoadResult with segments and a relevance flag.
    Raises SubtitleContentError if the file produces zero segments.
    """
    path = Path(path)
    ext = path.suffix.lower().lstrip(".")
    text = path.read_text(encoding="utf-8", errors="replace")

    if ext == "vtt":
        # Strip WEBVTT header, then normalize timestamps for SRT parser
        text = _normalize_vtt_timestamps(text)
        segments = srt_to_segments(text)
    elif ext == "srt":
        segments = srt_to_segments(text)
    else:
        raise ValueError(f"Unsupported subtitle extension: .{ext}")

    if not segments:
        raise SubtitleContentError("parsed subtitle file contains no segments")

    relevant = check_title_relevance(segments, title)
    if not relevant:
        logger.warning(
            "Subtitle content may not match video title %r", title
        )

    return LoadResult(segments=segments, relevant=relevant)
