from __future__ import annotations

import re

from ..segment import Segment


_TIME_RE = re.compile(
    r"(?P<sh>\d{2}):(?P<sm>\d{2}):(?P<ss>\d{2}),(?P<sms>\d{3})\s*-->\s*"
    r"(?P<eh>\d{2}):(?P<em>\d{2}):(?P<es>\d{2}),(?P<ems>\d{3})"
)


def _to_ms(h: str, m: str, s: str, ms: str) -> int:
    return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)


def srt_to_segments(srt_text: str) -> list[Segment]:
    blocks = re.split(r"\r?\n\r?\n+", srt_text.strip())
    segments: list[Segment] = []
    for block in blocks:
        lines = [ln.strip("\r") for ln in block.splitlines() if ln.strip("\r").strip()]
        if len(lines) < 2:
            continue

        # Optional numeric index line.
        time_line = lines[1] if lines[0].isdigit() else lines[0]
        m = _TIME_RE.search(time_line)
        if not m:
            continue

        start_ms = _to_ms(m["sh"], m["sm"], m["ss"], m["sms"])
        end_ms = _to_ms(m["eh"], m["em"], m["es"], m["ems"])
        text_lines = lines[2:] if lines[0].isdigit() else lines[1:]
        text = " ".join(" ".join(text_lines).replace("\n", " ").split())
        segments.append(Segment(start_ms=start_ms, end_ms=end_ms, text=text))

    return segments

