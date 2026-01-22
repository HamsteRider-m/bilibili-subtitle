from bilibili_subtitle.renderers.srt import render_srt
from bilibili_subtitle.segment import Segment


def test_render_srt_basic() -> None:
    s = render_srt([Segment(0, 1000, "a"), Segment(1000, 2000, "b")])
    assert "1\n00:00:00,000 --> 00:00:01,000\na\n\n2\n00:00:01,000 --> 00:00:02,000\nb\n" in s


def test_render_srt_bilingual() -> None:
    zh = [Segment(0, 1000, "你好")]
    en = [Segment(0, 1000, "Hello")]
    s = render_srt(zh, segments_en=en)
    assert "你好\nHello" in s

