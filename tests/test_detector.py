from bilibili_subtitle.bbdown_client import SubtitleInfo, VideoInfo


def test_video_info_with_subtitle() -> None:
    info = VideoInfo(
        video_id="BV1234567890",
        title="Test Video",
        subtitle_info=SubtitleInfo(has_subtitle=True, has_ai_subtitle=True, languages=["zh"]),
        subtitle_files=[],
    )
    assert info.subtitle_info.has_subtitle is True
    assert info.subtitle_info.has_ai_subtitle is True


def test_video_info_without_subtitle() -> None:
    info = VideoInfo(
        video_id="BV1234567890",
        title="Test Video",
        subtitle_info=SubtitleInfo(has_subtitle=False, has_ai_subtitle=False, languages=[]),
        subtitle_files=[],
    )
    assert info.subtitle_info.has_subtitle is False
    assert info.subtitle_info.has_ai_subtitle is False
