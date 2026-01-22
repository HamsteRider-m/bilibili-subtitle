from __future__ import annotations

from ..segment import Segment
from ._time import format_timestamp_srt


def render_srt(segments_zh: list[Segment], *, segments_en: list[Segment] | None = None) -> str:
    if segments_en is not None and len(segments_en) != len(segments_zh):
        raise ValueError("Bilingual output requires equal-length zh/en segment lists.")

    lines: list[str] = []
    for idx, zh in enumerate(segments_zh, start=1):
        if segments_en is not None:
            en = segments_en[idx - 1]
            if (en.start_ms, en.end_ms) != (zh.start_ms, zh.end_ms):
                raise ValueError("Bilingual zh/en segments must share timestamps.")
            text = f"{zh.text}\n{en.text}"
        else:
            text = zh.text

        lines.extend(
            [
                str(idx),
                f"{format_timestamp_srt(zh.start_ms)} --> {format_timestamp_srt(zh.end_ms)}",
                text,
                "",
            ]
        )
    return "\n".join(lines).rstrip("\n") + "\n"

