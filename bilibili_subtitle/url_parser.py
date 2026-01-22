from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


_BV_RE = re.compile(r"\b(BV[0-9A-Za-z]{10})\b")
_AV_RE = re.compile(r"\bav(\d+)\b", re.IGNORECASE)


VideoIdType = Literal["BV", "av", "unknown"]


@dataclass(frozen=True, slots=True)
class VideoRef:
    id_type: VideoIdType
    video_id: str | None
    input_value: str
    canonical_url: str | None


def parse_bilibili_ref(value: str) -> VideoRef:
    value = (value or "").strip()
    if not value:
        raise ValueError("Empty input.")

    # Raw IDs.
    bv_match = _BV_RE.search(value)
    if bv_match:
        bv = bv_match.group(1)
        return VideoRef(
            id_type="BV",
            video_id=bv,
            input_value=value,
            canonical_url=f"https://www.bilibili.com/video/{bv}/",
        )

    av_match = _AV_RE.search(value)
    if av_match:
        avid = f"av{av_match.group(1)}"
        return VideoRef(
            id_type="av",
            video_id=avid,
            input_value=value,
            canonical_url=f"https://www.bilibili.com/video/{avid}/",
        )

    # URLs.
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        # We might still be able to parse BV/av from the path.
        bv_match = _BV_RE.search(parsed.path)
        if bv_match:
            bv = bv_match.group(1)
            return VideoRef(
                id_type="BV",
                video_id=bv,
                input_value=value,
                canonical_url=f"https://www.bilibili.com/video/{bv}/",
            )

        av_match = _AV_RE.search(parsed.path)
        if av_match:
            avid = f"av{av_match.group(1)}"
            return VideoRef(
                id_type="av",
                video_id=avid,
                input_value=value,
                canonical_url=f"https://www.bilibili.com/video/{avid}/",
            )

        return VideoRef(
            id_type="unknown",
            video_id=None,
            input_value=value,
            canonical_url=value,
        )

    return VideoRef(id_type="unknown", video_id=None, input_value=value, canonical_url=None)

