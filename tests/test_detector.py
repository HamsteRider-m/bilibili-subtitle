from bilibili_subtitle.detector import collect_subtitle_tracks, select_best_track


def test_select_best_track_prefers_ai_zh() -> None:
    info = {
        "subtitles": {
            "zh": [{"ext": "srt", "url": "https://example/zh.srt"}],
        },
        "automatic_captions": {
            "ai-zh": [{"ext": "json", "url": "https://example/ai-zh.json"}],
        },
    }
    tracks = collect_subtitle_tracks(info)
    best = select_best_track(tracks)
    assert best is not None
    assert best.lang == "ai-zh"


def test_select_best_track_fallback_any() -> None:
    info = {"subtitles": {"en": [{"ext": "vtt", "url": "https://example/en.vtt"}]}}
    best = select_best_track(collect_subtitle_tracks(info))
    assert best is not None
    assert best.lang == "en"

