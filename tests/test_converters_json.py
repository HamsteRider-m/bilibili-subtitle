import json

from bilibili_subtitle.converters.json_converter import json_to_segments


def test_json_to_segments_bilibili_body_list() -> None:
    payload = {
        "body": [
            {"from": 0.5, "to": 1.25, "content": "Hello"},
            {"from": 1.25, "to": 2.0, "content": "world"},
        ]
    }
    segments = json_to_segments(json.dumps(payload))
    assert [(s.start_ms, s.end_ms, s.text) for s in segments] == [
        (500, 1250, "Hello"),
        (1250, 2000, "world"),
    ]


def test_json_to_segments_plain_list() -> None:
    payload = [
        {"from": 0.0, "to": 1.0, "body": "a"},
        {"from": 1.0, "to": 2.0, "content": "b"},
    ]
    segments = json_to_segments(json.dumps(payload))
    assert [s.text for s in segments] == ["a", "b"]

