from __future__ import annotations

import re
from typing import Any

from ..segment import Segment


_DIALOGUE_RE = re.compile(r"^\s*Dialogue:\s*", re.IGNORECASE)
_OVERRIDE_TAG_RE = re.compile(r"\{.*?\}")


def _parse_ass_time_to_ms(value: str) -> int:
    value = value.strip()
    hh_mm_ss, _, frac = value.partition(".")
    hh, mm, ss = hh_mm_ss.split(":")
    hours = int(hh)
    minutes = int(mm)
    seconds = int(ss)
    if frac:
        # ASS commonly uses centiseconds, but some producers emit milliseconds.
        if len(frac) == 1:
            ms = int(frac) * 100
        elif len(frac) == 2:
            ms = int(frac) * 10
        else:
            ms = int(frac[:3])
    else:
        ms = 0
    return ((hours * 3600 + minutes * 60 + seconds) * 1000) + ms


def _normalize_ass_text(text: Any) -> str:
    if not isinstance(text, str):
        raise TypeError("ASS dialogue text must be a string.")
    text = text.replace("\\N", " ").replace("\\n", " ")
    text = _OVERRIDE_TAG_RE.sub("", text)
    return " ".join(text.replace("\n", " ").split())


def ass_to_segments(ass_text: str) -> list[Segment]:
    segments: list[Segment] = []
    for raw_line in ass_text.splitlines():
        if not _DIALOGUE_RE.match(raw_line):
            continue
        line = _DIALOGUE_RE.sub("", raw_line, count=1)
        parts = line.split(",", 9)
        if len(parts) < 10:
            continue

        start = parts[1]
        end = parts[2]
        text = parts[9]
        segments.append(
            Segment(
                start_ms=_parse_ass_time_to_ms(start),
                end_ms=_parse_ass_time_to_ms(end),
                text=_normalize_ass_text(text),
            )
        )
    return segments

