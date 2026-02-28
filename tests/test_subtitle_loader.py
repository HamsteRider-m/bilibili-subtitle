"""Tests for subtitle_loader.py — Fix 2 (relevance), Fix 6 (VTT)."""
from __future__ import annotations

import pytest

from bilibili_subtitle.segment import Segment
from bilibili_subtitle.subtitle_loader import (
    LoadResult,
    check_title_relevance,
    load_segments_from_subtitle_file,
    _normalize_vtt_timestamps,
)
from bilibili_subtitle.errors import SubtitleContentError


def _segs(text: str) -> list[Segment]:
    return [Segment(start_ms=0, end_ms=1000, text=text)]


# ── Fix 2: check_title_relevance ──

def test_relevance_cjk_match():
    assert check_title_relevance(_segs("今天讲量子力学的基础"), "量子力学入门") is True

def test_relevance_cjk_no_match():
    assert check_title_relevance(_segs("今天做红烧肉"), "量子力学入门") is False

def test_relevance_latin_match():
    assert check_title_relevance(
        _segs("introduction to quantum physics"), "Quantum Physics 101"
    ) is True

def test_relevance_latin_no_match():
    assert check_title_relevance(
        _segs("cooking recipe for pasta"), "Quantum Physics 101"
    ) is False

def test_relevance_short_title_skipped():
    assert check_title_relevance(_segs("anything"), "ab") is True

def test_relevance_none_title():
    assert check_title_relevance(_segs("anything"), None) is True


# ── Fix 6: VTT timestamp normalization ──

def test_vtt_timestamps_converted():
    vtt = "00:01:23.456 --> 00:01:25.789\nHello world"
    result = _normalize_vtt_timestamps(vtt)
    assert "00:01:23,456 --> 00:01:25,789" in result

def test_vtt_preserves_text_dots():
    vtt = "00:01:23.456 --> 00:01:25.789\nVersion 3.14 is out"
    result = _normalize_vtt_timestamps(vtt)
    assert "3.14" in result
    assert "00:01:23,456" in result


# ── File loading ──

_SRT = "1\n00:00:01,000 --> 00:00:03,000\n量子力学很有趣\n\n2\n00:00:04,000 --> 00:00:06,000\n今天学习\n"
_VTT = "WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n量子力学很有趣\n\n2\n00:00:04.000 --> 00:00:06.000\n今天学习\n"

def test_load_srt(tmp_path):
    p = tmp_path / "test.srt"
    p.write_text(_SRT, encoding="utf-8")
    r = load_segments_from_subtitle_file(p, title="量子力学入门")
    assert len(r.segments) == 2
    assert r.relevant is True

def test_load_vtt(tmp_path):
    p = tmp_path / "test.vtt"
    p.write_text(_VTT, encoding="utf-8")
    r = load_segments_from_subtitle_file(p, title="量子力学入门")
    assert len(r.segments) == 2
    assert r.relevant is True

def test_load_irrelevant(tmp_path):
    p = tmp_path / "test.srt"
    p.write_text(_SRT, encoding="utf-8")
    r = load_segments_from_subtitle_file(p, title="How to cook pasta at home")
    assert r.relevant is False
    assert len(r.segments) == 2  # still returns segments

def test_load_empty_raises(tmp_path):
    p = tmp_path / "test.srt"
    p.write_text("no valid blocks here\n", encoding="utf-8")
    with pytest.raises(SubtitleContentError):
        load_segments_from_subtitle_file(p)

def test_unsupported_ext(tmp_path):
    p = tmp_path / "test.ass"
    p.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        load_segments_from_subtitle_file(p)
