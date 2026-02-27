"""Time formatting utilities for subtitle renderers."""

from __future__ import annotations


def format_timestamp_srt(ms: int) -> str:
    """Format milliseconds to SRT timestamp format: HH:MM:SS,mmm"""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def format_timestamp_vtt(ms: int) -> str:
    """Format milliseconds to VTT timestamp format: HH:MM:SS.mmm"""
    total_seconds = ms // 1000
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    milliseconds = ms % 1000
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
