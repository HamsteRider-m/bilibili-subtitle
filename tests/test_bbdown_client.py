"""Tests for bbdown_client.py — Fix 1 (retry/timeout), Fix 5 (regex), Fix 7 (error propagation)."""
from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from bilibili_subtitle.bbdown_client import (
    BBDownClient,
    BBDownError,
    _SUBTITLE_LINE_RE,
    _AI_MARKER_RE,
    _LANG_RE,
    _LANG_NORMALIZE,
)


# ── Fix 5: Regex tests ──

class TestSubtitleLineRegex:
    @pytest.mark.parametrize("line", [
        "下载字幕 zh-Hans", "Download subtitle for BV123",
        "Saving subtitle file...", "字幕下载完成",
    ])
    def test_matches(self, line: str):
        assert _SUBTITLE_LINE_RE.search(line)

    def test_no_match(self):
        assert _SUBTITLE_LINE_RE.search("downloading video") is None


class TestAIMarkerRegex:
    @pytest.mark.parametrize("line", [
        "ai-zh subtitle", "AI识别字幕", "auto-generated captions",
        "asr transcription", "自动识别", "ai_en",
    ])
    def test_matches(self, line: str):
        assert _AI_MARKER_RE.search(line)

    def test_no_match(self):
        assert _AI_MARKER_RE.search("human translated") is None


class TestLangRegex:
    @pytest.mark.parametrize("text,expected", [
        ("zh-Hans", "zh"), ("zh-Hant", "zh-hant"),
        ("en", "en"), ("ja", "ja"), ("ko", "ko"),
    ])
    def test_normalize(self, text: str, expected: str):
        m = _LANG_RE.search(text)
        assert m
        raw = m.group(1).lower()
        assert _LANG_NORMALIZE.get(raw, raw) == expected


# ── Fix 1: Retry + timeout ──

def _make_client() -> BBDownClient:
    with patch.object(BBDownClient, "_find_bbdown", return_value="/usr/bin/BBDown"):
        return BBDownClient()


@patch("bilibili_subtitle.bbdown_client.time.sleep")
@patch("bilibili_subtitle.bbdown_client.subprocess.run")
def test_succeeds_first_try(mock_run, mock_sleep):
    mock_run.return_value = subprocess.CompletedProcess([], 0, "ok", "")
    assert _make_client()._run(["x"]).returncode == 0
    mock_sleep.assert_not_called()


@patch("bilibili_subtitle.bbdown_client.time.sleep")
@patch("bilibili_subtitle.bbdown_client.subprocess.run")
def test_retries_transient(mock_run, mock_sleep):
    mock_run.side_effect = [
        subprocess.CompletedProcess([], 1, "", "network error"),
        subprocess.CompletedProcess([], 0, "ok", ""),
    ]
    assert _make_client()._run(["x"], retry_delay=0.01).returncode == 0
    assert mock_run.call_count == 2


@patch("bilibili_subtitle.bbdown_client.time.sleep")
@patch("bilibili_subtitle.bbdown_client.subprocess.run")
def test_no_retry_fatal(mock_run, mock_sleep):
    mock_run.return_value = subprocess.CompletedProcess([], 1, "", "login required auth")
    with pytest.raises(BBDownError, match="non-retryable"):
        _make_client()._run(["x"])
    assert mock_run.call_count == 1


@patch("bilibili_subtitle.bbdown_client.time.sleep")
@patch("bilibili_subtitle.bbdown_client.subprocess.run")
def test_retries_timeout(mock_run, mock_sleep):
    mock_run.side_effect = [
        subprocess.TimeoutExpired("x", 120),
        subprocess.CompletedProcess([], 0, "ok", ""),
    ]
    assert _make_client()._run(["x"], retry_delay=0.01).returncode == 0


@patch("bilibili_subtitle.bbdown_client.time.sleep")
@patch("bilibili_subtitle.bbdown_client.subprocess.run")
def test_exhausts_retries(mock_run, mock_sleep):
    mock_run.return_value = subprocess.CompletedProcess([], 1, "", "transient")
    with pytest.raises(BBDownError):
        _make_client()._run(["x"], max_retries=2, retry_delay=0.01)
    assert mock_run.call_count == 2


# ── Fix 5: _extract_subtitle_info ──

@patch("bilibili_subtitle.bbdown_client.time.sleep")
def test_extract_subtitle_info_ai_zh(mock_sleep):
    client = _make_client()
    info = client._extract_subtitle_info("下载字幕 ai-zh\n其他行")
    assert info.has_subtitle is True
    assert info.has_ai_subtitle is True
    assert "zh" in info.languages


@patch("bilibili_subtitle.bbdown_client.time.sleep")
def test_extract_subtitle_info_no_subtitle(mock_sleep):
    client = _make_client()
    info = client._extract_subtitle_info("视频标题: test\n完成")
    assert info.has_subtitle is False
    assert info.languages == []
