from __future__ import annotations


def normalize_lang(lang: str) -> str:
    raw = (lang or "").strip()
    if not raw:
        return raw

    lowered = raw.lower()
    aliases = {
        "zh-cn": "zh",
        "zh_cn": "zh",
        "zh-hans": "zh-Hans",
        "zh-hans-cn": "zh-Hans",
        "zh-hans_cn": "zh-Hans",
        "zh-sg": "zh",
        "zh_tw": "zh-Hant",
        "zh-tw": "zh-Hant",
        "zh-hant": "zh-Hant",
    }
    if lowered in aliases:
        return aliases[lowered]

    if lowered == "ai-zh":
        return "ai-zh"

    # Preserve original casing for non-aliases; most yt-dlp lang IDs are case-sensitive-ish.
    return raw

