"""Inference harness: vLLM serving, batched prompts, generation ledger.

TODO(G1): implement the calibration runner (60 prefixes x 3 models).
TODO(P2): implement the resumable main runner (34,800-generation envelope).
TODO(P2): record one ledger row per generation and checkpoint per shard.
"""

from __future__ import annotations

__all__: list[str] = []
