import pytest

from bilibili_subtitle.url_parser import parse_bilibili_ref


def test_parse_bv_id() -> None:
    ref = parse_bilibili_ref("BV1Q5411c7mD")
    assert ref.id_type == "BV"
    assert ref.video_id == "BV1Q5411c7mD"
    assert ref.canonical_url == "https://www.bilibili.com/video/BV1Q5411c7mD/"


def test_parse_bv_url() -> None:
    ref = parse_bilibili_ref("https://www.bilibili.com/video/BV1Q5411c7mD/?p=1")
    assert ref.id_type == "BV"
    assert ref.video_id == "BV1Q5411c7mD"


def test_parse_av_id() -> None:
    ref = parse_bilibili_ref("av123456")
    assert ref.id_type == "av"
    assert ref.video_id == "av123456"


def test_parse_unknown_url() -> None:
    ref = parse_bilibili_ref("https://b23.tv/abcd")
    assert ref.id_type == "unknown"
    assert ref.video_id is None


def test_parse_empty() -> None:
    with pytest.raises(ValueError):
        parse_bilibili_ref("  ")

