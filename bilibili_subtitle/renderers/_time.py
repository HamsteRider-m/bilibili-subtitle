from __future__ import annotations


def format_timestamp_srt(ms: int) -> str:
    if ms < 0:
        raise ValueError("ms must be >= 0")
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def format_timestamp_vtt(ms: int) -> str:
    if ms < 0:
        raise ValueError("ms must be >= 0")
    hours, rem = divmod(ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    seconds, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

