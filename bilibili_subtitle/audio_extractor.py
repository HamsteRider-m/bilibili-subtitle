from __future__ import annotations

from pathlib import Path
from typing import Any


def extract_audio_with_ytdlp(
    url_or_id: str,
    output_dir: str | Path,
    *,
    audio_format: str = "m4a",
    ydl_opts: dict[str, Any] | None = None,
) -> Path:
    try:
        from yt_dlp import YoutubeDL
    except Exception as e:  # pragma: no cover
        raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp") from e

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_format,
            }
        ],
    }
    if ydl_opts:
        base_opts.update(ydl_opts)

    with YoutubeDL(base_opts) as ydl:
        info = ydl.extract_info(url_or_id, download=True)

    video_id = info.get("id")
    if isinstance(video_id, str) and video_id:
        candidates = sorted(output_dir.glob(f"{video_id}.*"))
        for p in candidates:
            if p.suffix.lstrip(".") == audio_format:
                return p
        if candidates:
            return candidates[0]

    # Fallback: return most recent file in output_dir
    files = sorted(output_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        raise RuntimeError("Audio extraction produced no output.")
    return files[0]

