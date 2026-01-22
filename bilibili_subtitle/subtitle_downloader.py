from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from .detector import SubtitleTrack, VideoMetadata, extract_metadata, select_best_track


@dataclass(frozen=True, slots=True)
class DownloadedSubtitle:
    metadata: VideoMetadata
    track: SubtitleTrack
    file_path: Path


_EXT_PREFERENCE: tuple[str, ...] = ("json", "ass", "srt", "vtt")


def _choose_format(formats: list[dict[str, Any]]) -> dict[str, Any]:
    if not formats:
        raise ValueError("No subtitle formats available.")

    by_ext: dict[str, dict[str, Any]] = {}
    for fmt in formats:
        ext = fmt.get("ext")
        if isinstance(ext, str):
            by_ext.setdefault(ext, fmt)

    for ext in _EXT_PREFERENCE:
        if ext in by_ext:
            return by_ext[ext]

    return formats[0]


def _download_url(url: str, dest: Path, *, headers: dict[str, str] | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = Request(url, headers=headers or {})
    with urlopen(req) as resp, dest.open("wb") as f:
        f.write(resp.read())


def download_best_subtitle(
    url_or_id: str,
    output_dir: str | Path,
    *,
    ydl_opts: dict[str, Any] | None = None,
) -> DownloadedSubtitle:
    _, meta = extract_metadata(url_or_id, ydl_opts=ydl_opts)
    best_track = select_best_track(meta.available_tracks)
    if best_track is None:
        raise ValueError("No subtitle track found in yt-dlp metadata.")

    best_format = _choose_format(best_track.formats)
    sub_url = best_format.get("url")
    if not isinstance(sub_url, str) or not sub_url:
        raise ValueError("Selected subtitle format has no URL.")

    ext = best_format.get("ext")
    if not isinstance(ext, str) or not ext:
        ext = "txt"

    video_id = meta.video_id or "unknown"
    dest = Path(output_dir) / f"{video_id}.{best_track.lang}.{ext}"

    headers = best_format.get("http_headers")
    if headers is not None and not isinstance(headers, dict):
        headers = None
    _download_url(sub_url, dest, headers=headers)  # type: ignore[arg-type]

    return DownloadedSubtitle(metadata=meta, track=best_track, file_path=dest)


def download_subtitles_via_ytdlp(
    url_or_id: str,
    output_dir: str | Path,
    *,
    langs: tuple[str, ...] = ("zh", "ai-zh"),
    ydl_opts: dict[str, Any] | None = None,
) -> list[Path]:
    """
    Downloads subtitle files using yt-dlp's built-in subtitle writer, similar to:
      yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs zh,ai-zh URL
    """
    try:
        from yt_dlp import YoutubeDL
    except Exception as e:  # pragma: no cover
        raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp") from e

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    base_opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": list(langs),
        "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
    }
    if ydl_opts:
        base_opts.update(ydl_opts)

    with YoutubeDL(base_opts) as ydl:
        info = ydl.extract_info(url_or_id, download=False)
        ydl.download([url_or_id])

    video_id = info.get("id")
    if not isinstance(video_id, str) or not video_id:
        return sorted(output_dir.glob("*"))

    # yt-dlp writes subs as: {outtmpl_base}.{lang}.{ext}
    return sorted(output_dir.glob(f"{video_id}.*.*"))
