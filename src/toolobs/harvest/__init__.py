"""Harvest pipeline: candidates, PII scrub, relevance, replay, sampling, freeze.

TODO(G0): implement value-used relevance labeling in scripts/03_relevance.py.
TODO(G0): implement replay verification in scripts/04_replay.py.
TODO(G0): implement the stratified 880/800/80 sample in scripts/05_sample.py.
TODO(G0): implement freeze manifests in scripts/06_freeze.py.
"""

from __future__ import annotations

__all__: list[str] = []
