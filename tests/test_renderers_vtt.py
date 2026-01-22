from bilibili_subtitle.renderers.vtt import render_vtt
from bilibili_subtitle.segment import Segment


def test_render_vtt_basic() -> None:
    s = render_vtt([Segment(0, 1000, "a")])
    assert s.startswith("WEBVTT")
    assert "00:00:00.000 --> 00:00:01.000" in s

