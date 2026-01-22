from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AudioChunk:
    start_ms: int
    end_ms: int
    path: Path


def probe_duration_ms(input_path: str | Path) -> int:
    input_path = Path(input_path)
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(input_path),
    ]
    try:
        out = subprocess.check_output(cmd, text=True)
    except FileNotFoundError as e:  # pragma: no cover
        raise RuntimeError("ffprobe not found. Install ffmpeg.") from e
    data = json.loads(out)
    dur = float(data["format"]["duration"])
    return int(round(dur * 1000))


def chunk_audio_ffmpeg(
    input_path: str | Path,
    output_dir: str | Path,
    *,
    chunk_seconds: int = 60,
    overlap_seconds: int = 2,
) -> list[AudioChunk]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    duration_ms = probe_duration_ms(input_path)
    chunk_ms = chunk_seconds * 1000
    overlap_ms = overlap_seconds * 1000
    if chunk_ms <= 0:
        raise ValueError("chunk_seconds must be > 0.")
    if overlap_ms < 0 or overlap_ms >= chunk_ms:
        raise ValueError("overlap_seconds must be >= 0 and < chunk_seconds.")

    step_ms = chunk_ms - overlap_ms
    chunks: list[AudioChunk] = []
    start_ms = 0
    idx = 0
    while start_ms < duration_ms:
        end_ms = min(duration_ms, start_ms + chunk_ms)
        out_path = output_dir / f"chunk_{idx:04d}_{start_ms}_{end_ms}{input_path.suffix}"
        cmd = [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-ss",
            f"{start_ms / 1000:.3f}",
            "-t",
            f"{(end_ms - start_ms) / 1000:.3f}",
            "-i",
            str(input_path),
            "-c",
            "copy",
            str(out_path),
        ]
        try:
            subprocess.check_call(cmd)
        except FileNotFoundError as e:  # pragma: no cover
            raise RuntimeError("ffmpeg not found. Install ffmpeg.") from e

        chunks.append(AudioChunk(start_ms=start_ms, end_ms=end_ms, path=out_path))
        idx += 1
        start_ms += step_ms

    return chunks

