from bilibili_subtitle.agents.translate_agent import TranslateAgent
from bilibili_subtitle.segment import Segment


def test_translate_agent_noop() -> None:
    agent = TranslateAgent(mode="noop")
    segments = [Segment(0, 1000, "你好")]
    out = agent.translate_segments(segments)
    assert out == segments

