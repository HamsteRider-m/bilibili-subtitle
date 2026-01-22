from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Segment:
    start_ms: int
    end_ms: int
    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.start_ms, int) or not isinstance(self.end_ms, int):
            raise TypeError("start_ms/end_ms must be ints (milliseconds).")
        if self.start_ms < 0:
            raise ValueError("start_ms must be >= 0.")
        if self.start_ms >= self.end_ms:
            raise ValueError("start_ms must be < end_ms.")
        if not isinstance(self.text, str):
            raise TypeError("text must be a string.")
        if not self.text.strip():
            raise ValueError("text must be non-empty after stripping.")

