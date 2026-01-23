from __future__ import annotations

from pathlib import Path

from .bbdown_client import BBDownClient
from .url_parser import parse_bilibili_ref


def extract_audio(
    url_or_id: str,
    output_dir: str | Path,
) -> Path:
    ref = parse_bilibili_ref(url_or_id)
    url = ref.canonical_url or ref.input_value
    output_dir = Path(output_dir)

    client = BBDownClient()
    return client.download_audio(url, output_dir)
