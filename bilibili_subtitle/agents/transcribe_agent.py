from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Literal

from ..segment import Segment


Mode = Literal["noop", "openai"]


@dataclass(frozen=True, slots=True)
class TranscribeResult:
    segments: list[Segment]
    raw: Any | None = None


class TranscribeAgent:
    def __init__(
        self,
        *,
        mode: Mode = "openai",
        model: str = "whisper-1",
        api_key: str | None = None,
    ) -> None:
        self._mode = mode
        self._model = model
        self._api_key = api_key

    def transcribe(self, audio_path: str) -> TranscribeResult:
        if self._mode == "noop":
            return TranscribeResult(segments=[], raw=None)

        api_key = self._api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY (or pass api_key=...).")

        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except Exception as e:  # pragma: no cover
            raise RuntimeError("openai package is required for transcription. Install: pip install openai") from e

        client = OpenAI(api_key=api_key)
        with open(audio_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                model=self._model,
                file=f,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments: list[Segment] = []
        for seg in getattr(resp, "segments", []) or []:
            start_s = getattr(seg, "start", None)
            end_s = getattr(seg, "end", None)
            text = getattr(seg, "text", "") or ""
            if start_s is None or end_s is None:
                continue
            segments.append(
                Segment(
                    start_ms=int(round(float(start_s) * 1000)),
                    end_ms=int(round(float(end_s) * 1000)),
                    text=" ".join(str(text).split()),
                )
            )

        return TranscribeResult(segments=segments, raw=resp)

