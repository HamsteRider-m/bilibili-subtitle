# bilibili-subtitle Maintenance Plan

## Goal

Maintain a focused BBDown-only Bilibili subtitle extractor with a stable CLI and parent-skill JSON contract.

## Scope

- Keep URL/BV/av parsing
- Keep BBDown subtitle-only download
- Keep transcript, SRT, and VTT renderers
- Keep preflight and install scripts
- Exclude non-BBDown processing pipelines

## Verification

- `python -m py_compile bilibili_subtitle/*.py`
- `pixi run python -m pytest -q`
- `pixi run python -m bilibili_subtitle --help`
