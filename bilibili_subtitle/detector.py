from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .bbdown_client import BBDownClient
from .url_parser import VideoRef, parse_bilibili_ref


@dataclass(frozen=True, slots=True)
class VideoMetadata:
    video_id: str
    title: str | None
    has_subtitle: bool
    has_ai_subtitle: bool
    subtitle_files: list[Path]


def detect_subtitles(
    url_or_id: str,
    output_dir: str | Path,
) -> tuple[VideoRef, VideoMetadata]:
    ref = parse_bilibili_ref(url_or_id)
    url = ref.canonical_url or ref.input_value
    output_dir = Path(output_dir)

    client = BBDownClient()
    info = client.get_video_info(url, output_dir)

    meta = VideoMetadata(
        video_id=info.video_id or ref.video_id or "unknown",
        title=info.title,
        has_subtitle=info.subtitle_info.has_subtitle,
        has_ai_subtitle=info.subtitle_info.has_ai_subtitle,
        subtitle_files=info.subtitle_files,
    )
    return ref, meta
