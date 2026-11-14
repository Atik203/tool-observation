"""Conditional-logit slope tests on synthetic within-prefix data."""

from __future__ import annotations

import random

from toolobs.analysis.slope import (
    SlopeRow,
    bootstrap_slope,
    conditional_logit,
    holm_adjust,
    per_model_slopes,
    pooled_slope,
)


def _frame(prefixes: int = 200, models: tuple[str, ...] = ("qwen", "mistral")) -> list[SlopeRow]:
    rng = random.Random(20261108)
    rows: list[SlopeRow] = []
    for index in range(prefixes):
        threshold = rng.choice((1, 2, 3))
        for model in models:
            for severity in range(4):
                rows.append(
                    SlopeRow(
                        group_id=f"p{index}|{model}",
                        cluster_id=f"p{index}",
                        model_id=model,
                        severity=severity,
                        y=int(severity >= threshold),
                    )
                )
    return rows


def test_conditional_logit_recovers_positive_slope() -> None:
    result = conditional_logit(_frame())
    assert result.beta > 0
    assert result.p_value < 0.01
    assert result.n_groups > 100
    assert result.converged is True


def test_per_model_and_pooled_slopes() -> None:
    rows = _frame()
    per_model = per_model_slopes(rows)
    assert set(per_model) == {"qwen", "mistral"}
    assert all(result.beta > 0 for result in per_model.values())
    pooled = pooled_slope(rows)
    assert pooled.beta > 0
    assert pooled.n_groups == 2 * 200


def test_no_within_group_variation_returns_empty_fit() -> None:
    rows = [
        SlopeRow(group_id="p", cluster_id="p", model_id="qwen", severity=s, y=0)
        for s in range(4)
    ]
    result = conditional_logit(rows)
    assert result.n_groups == 0
    assert result.beta == 0.0


def test_bootstrap_returns_positive_interval() -> None:
    result = bootstrap_slope(_frame(prefixes=40), replicates=30, seed=7)
    assert result.replicates == 30
    assert result.beta_mean > 0
    assert result.ci_low <= result.ci_high


def test_holm_adjustment() -> None:
    adjusted = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adjusted["a"] == 0.03
    assert adjusted["c"] == 0.06
    assert adjusted["b"] == 0.06
