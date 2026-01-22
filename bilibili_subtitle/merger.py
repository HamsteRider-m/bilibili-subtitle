from __future__ import annotations

import difflib
from dataclasses import dataclass

from .segment import Segment


@dataclass(frozen=True, slots=True)
class ChunkTranscript:
    chunk_start_ms: int
    segments: list[Segment]


def validate_strictly_increasing(segments: list[Segment]) -> None:
    prev_end = -1
    for seg in segments:
        if seg.start_ms < prev_end:
            raise ValueError("Non-monotonic timestamps: segment overlaps previous segment.")
        prev_end = seg.end_ms


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def _shift_segments(segments: list[Segment], offset_ms: int) -> list[Segment]:
    if offset_ms == 0:
        return segments
    return [
        Segment(start_ms=s.start_ms + offset_ms, end_ms=s.end_ms + offset_ms, text=s.text) for s in segments
    ]


def merge_chunk_transcripts(
    transcripts: list[ChunkTranscript],
    *,
    overlap_ms: int = 2000,
    similarity_threshold: float = 0.8,
) -> list[Segment]:
    if not transcripts:
        return []

    transcripts = sorted(transcripts, key=lambda t: t.chunk_start_ms)
    merged: list[Segment] = []

    for t in transcripts:
        shifted = _shift_segments(t.segments, t.chunk_start_ms)
        if not merged:
            merged.extend(shifted)
            continue

        overlap_start = t.chunk_start_ms
        overlap_end = overlap_start + max(0, overlap_ms)
        candidates = [s for s in merged if s.end_ms > overlap_start and s.start_ms < overlap_end]

        def is_duplicate(seg: Segment) -> bool:
            if seg.start_ms >= overlap_end:
                return False
            for cand in candidates:
                time_overlaps = max(seg.start_ms, cand.start_ms) < min(seg.end_ms, cand.end_ms)
                if not time_overlaps:
                    continue
                if _similarity(seg.text, cand.text) >= similarity_threshold:
                    return True
            return False

        for seg in shifted:
            if is_duplicate(seg):
                continue
            merged.append(seg)

    merged.sort(key=lambda s: (s.start_ms, s.end_ms))

    # Enforce strict monotonicity by clamping any overlap forward.
    fixed: list[Segment] = []
    prev_end = 0
    for seg in merged:
        start_ms = max(seg.start_ms, prev_end)
        if start_ms >= seg.end_ms:
            continue
        if start_ms != seg.start_ms:
            seg = Segment(start_ms=start_ms, end_ms=seg.end_ms, text=seg.text)
        fixed.append(seg)
        prev_end = seg.end_ms

    validate_strictly_increasing(fixed)
    return fixed
