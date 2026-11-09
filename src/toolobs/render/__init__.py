"""Deterministic prose rendering and severity perturbations.

The renderer is template-based, never LLM-generated. s=0 must preserve the full
value set of the verbatim observation; any information loss excludes the prefix.

TODO(G0): implement the key-value/bullet renderer and renderer hash.
TODO(G0): implement s=1/s=2/s=3 perturbation records from the field registry.
"""

from __future__ import annotations

__all__: list[str] = []
