from bilibili_subtitle.converters.srt_converter import srt_to_segments


def test_srt_to_segments_basic() -> None:
    srt = "1\n00:00:00,000 --> 00:00:01,000\nhello\n\n2\n00:00:01,000 --> 00:00:02,000\nworld\n"
    segments = srt_to_segments(srt)
    assert [(s.start_ms, s.end_ms, s.text) for s in segments] == [
        (0, 1000, "hello"),
        (1000, 2000, "world"),
    ]

