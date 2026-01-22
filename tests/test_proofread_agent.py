from bilibili_subtitle.agents.proofread_agent import ProofreadAgent, diff_segments
from bilibili_subtitle.segment import Segment


def test_proofread_agent_noop() -> None:
    agent = ProofreadAgent(mode="noop")
    segments = [Segment(0, 1000, "a"), Segment(1000, 2000, "b")]
    out = agent.proofread_segments(segments)
    assert out == segments


def test_diff_segments_reports_changes() -> None:
    before = [Segment(0, 1000, "a"), Segment(1000, 2000, "b")]
    after = [Segment(0, 1000, "a"), Segment(1000, 2000, "B")]
    diff = diff_segments(before, after)
    assert diff == [{"index": 1, "before": "b", "after": "B"}]

