"""Frame-count checks against the pinned τ-bench checkout.

These run only when the gitignored upstream data is present locally or on the
GPU host; CI without the data skips them.
"""

from __future__ import annotations

import pytest

from toolobs.harvest.parse import parse_frame
from toolobs.paths import UPSTREAM_DIR

UPSTREAM = UPSTREAM_DIR / "tau-bench"
TRAJECTORIES = (
    "historical_trajectories/gpt-4o-airline.json",
    "historical_trajectories/gpt-4o-retail.json",
    "historical_trajectories/sonnet-35-new-airline.json",
    "historical_trajectories/sonnet-35-new-retail.json",
)

pytestmark = pytest.mark.skipif(
    not all((UPSTREAM / relative).is_file() for relative in TRAJECTORIES),
    reason="pinned τ-bench trajectories are not present",
)


def test_real_frame_matches_preregistered_counts() -> None:
    records, stats = parse_frame(UPSTREAM, TRAJECTORIES)
    assert len(records) == 13605
    assert stats.files == 4
    assert stats.trajectories == 1980
    assert stats.candidates == 13605
    assert stats.json_parseable == 11318
    assert stats.text_observations == 2287
    assert stats.think_skipped == 389
    assert stats.no_continuation_skipped == 291
    assert stats.profile_tool_candidates == 3692
    assert stats.unknown_tools == {}
