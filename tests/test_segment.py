import pytest

from bilibili_subtitle.segment import Segment


def test_segment_valid() -> None:
    Segment(start_ms=0, end_ms=1000, text="hello")


@pytest.mark.parametrize(
    ("start_ms", "end_ms", "text"),
    [
        (-1, 10, "a"),
        (10, 10, "a"),
        (11, 10, "a"),
        (0, 10, "   "),
    ],
)
def test_segment_invalid(start_ms: int, end_ms: int, text: str) -> None:
    with pytest.raises((ValueError, TypeError)):
        Segment(start_ms=start_ms, end_ms=end_ms, text=text)

