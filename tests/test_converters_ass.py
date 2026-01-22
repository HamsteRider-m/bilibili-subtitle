from bilibili_subtitle.converters.ass_converter import ass_to_segments


def test_ass_to_segments_dialogue_lines() -> None:
    ass = """[Script Info]
Title: test

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.50,0:00:01.20,Default,,0,0,0,,Hello
Dialogue: 0,0:00:01.20,0:00:02.00,Default,,0,0,0,,{\\i1}world{\\i0}\\Nnext
"""
    segments = ass_to_segments(ass)
    assert [(s.start_ms, s.end_ms, s.text) for s in segments] == [
        (500, 1200, "Hello"),
        (1200, 2000, "world next"),
    ]

