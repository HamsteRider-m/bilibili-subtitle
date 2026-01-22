from bilibili_subtitle.cache import Cache
from bilibili_subtitle.segment import Segment


def test_cache_roundtrip(tmp_path) -> None:
    cache = Cache(tmp_path)
    segs = [Segment(0, 1000, "a")]
    cache.save_segments("BV1xxx", "segments.zh", segs)
    loaded = cache.load_segments("BV1xxx", "segments.zh")
    assert loaded == segs

