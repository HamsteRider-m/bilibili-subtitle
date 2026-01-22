import json
from pathlib import Path

import jsonschema

from bilibili_subtitle.agents.summarize_agent import SummarizeAgent
from bilibili_subtitle.segment import Segment


def test_noop_summary_conforms_to_schema() -> None:
    schema = json.loads(Path("schemas/summary_schema.json").read_text(encoding="utf-8"))
    agent = SummarizeAgent(mode="noop")
    result = agent.summarize([Segment(0, 1000, "a")], title="t")
    jsonschema.validate(result.summary, schema)

