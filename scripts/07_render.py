#!/usr/bin/env python
"""Stage 07 — render observations and apply severity perturbations.

Input:  frozen prefixes, configs/field_registry.yaml, configs/arms.yaml
Output: data/manifests/perturbations.jsonl, rendered prompts

The renderer is deterministic (key-value/bullet template), never an LLM
paraphrase. s=0 must preserve the full value set of V; any information loss
excludes the prefix. Every perturbation stores JSON path, true value, false
value, criticality label, and expected action change.

GATE: 100% s=0 value-set equality with V; perturbed field present in observation.

TODO: implement. This is a scaffold stub and intentionally performs no work.
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manifest", default="data/manifests/toolresult800_v1.json")
    parser.add_argument("--out", default="data/manifests/perturbations.jsonl")
    args = parser.parse_args(argv)
    print(f"[07_render] not implemented (manifest={args.manifest})")
    return 2


if __name__ == "__main__":
    sys.exit(main())
