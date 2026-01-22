from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .segment import Segment


def _safe_name(value: str) -> str:
    value = value.strip() or "unknown"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value)


@dataclass(frozen=True, slots=True)
class CachedSegments:
    video_id: str
    segments: list[Segment]


class Cache:
    def __init__(self, cache_dir: str | Path) -> None:
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, video_id: str, name: str) -> Path:
        return self._dir / f"{_safe_name(video_id)}.{_safe_name(name)}.json"

    def load_segments(self, video_id: str, name: str) -> list[Segment] | None:
        path = self._path(video_id, name)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return None
        out: list[Segment] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            out.append(Segment(start_ms=item["start_ms"], end_ms=item["end_ms"], text=item["text"]))
        return out

    def save_segments(self, video_id: str, name: str, segments: list[Segment]) -> Path:
        path = self._path(video_id, name)
        data: list[dict[str, Any]] = [asdict(s) for s in segments]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

