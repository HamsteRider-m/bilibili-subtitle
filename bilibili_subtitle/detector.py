from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .languages import normalize_lang
from .url_parser import VideoRef, parse_bilibili_ref


SubtitleSource = Literal["subtitles", "automatic_captions"]


@dataclass(frozen=True, slots=True)
class SubtitleTrack:
    lang: str
    source: SubtitleSource
    formats: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    video_id: str | None
    title: str | None
    webpage_url: str | None
    available_tracks: list[SubtitleTrack]


_LANG_PRIORITY: tuple[str, ...] = ("ai-zh", "zh", "zh-Hans")


def extract_info(url_or_id: str, *, ydl_opts: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        from yt_dlp import YoutubeDL
    except Exception as e:  # pragma: no cover
        raise RuntimeError("yt-dlp is required. Install with: pip install yt-dlp") from e

    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    if ydl_opts:
        opts.update(ydl_opts)

    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(url_or_id, download=False)


def collect_subtitle_tracks(info: dict[str, Any]) -> list[SubtitleTrack]:
    tracks: list[SubtitleTrack] = []

    def add_tracks(source: SubtitleSource, mapping: Any) -> None:
        if not isinstance(mapping, dict):
            return
        for lang, formats in mapping.items():
            if not isinstance(lang, str):
                continue
            if not isinstance(formats, list):
                continue
            tracks.append(SubtitleTrack(lang=lang, source=source, formats=formats))

    add_tracks("subtitles", info.get("subtitles"))
    add_tracks("automatic_captions", info.get("automatic_captions"))

    return tracks


def select_best_track(tracks: list[SubtitleTrack]) -> SubtitleTrack | None:
    if not tracks:
        return None

    def priority(lang: str) -> tuple[int, str]:
        lang = normalize_lang(lang)
        try:
            idx = _LANG_PRIORITY.index(lang)
        except ValueError:
            idx = len(_LANG_PRIORITY)
        return (idx, lang)

    return sorted(tracks, key=lambda t: priority(t.lang))[0]


def extract_metadata(url_or_id: str, *, ydl_opts: dict[str, Any] | None = None) -> tuple[VideoRef, VideoMetadata]:
    ref = parse_bilibili_ref(url_or_id)
    info = extract_info(ref.canonical_url or ref.input_value, ydl_opts=ydl_opts)

    tracks = collect_subtitle_tracks(info)
    meta = VideoMetadata(
        video_id=info.get("id") or ref.video_id,
        title=info.get("title"),
        webpage_url=info.get("webpage_url") or ref.canonical_url,
        available_tracks=tracks,
    )
    return ref, meta
