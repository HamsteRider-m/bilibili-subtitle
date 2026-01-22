import pytest

from bilibili_subtitle.merger import ChunkTranscript, merge_chunk_transcripts, validate_strictly_increasing
from bilibili_subtitle.segment import Segment


def test_merge_deduplicates_overlap_by_text_similarity() -> None:
    # Chunk0: 0-60s, Chunk1 starts at 58s (2s overlap)
    c0 = ChunkTranscript(
        chunk_start_ms=0,
        segments=[
            Segment(57_500, 58_500, "hello"),
            Segment(58_500, 59_500, "overlap text"),
        ],
    )
    c1 = ChunkTranscript(
        chunk_start_ms=58_000,
        segments=[
            Segment(0, 1000, "overlap text"),  # duplicate in overlap window
            Segment(1000, 2000, "next"),
        ],
    )
    merged = merge_chunk_transcripts([c0, c1], overlap_ms=2000, similarity_threshold=0.8)
    assert [s.text for s in merged] == ["hello", "overlap text", "next"]
    validate_strictly_increasing(merged)


def test_validate_strictly_increasing_raises() -> None:
    with pytest.raises(ValueError):
        validate_strictly_increasing([Segment(0, 1000, "a"), Segment(900, 2000, "b")])

