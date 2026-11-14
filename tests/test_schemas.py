"""Record contract tests."""

from __future__ import annotations

from toolobs.schemas import (
    DecisionSignature,
    FrozenManifest,
    LedgerRow,
    ModelPins,
    PerturbationRecord,
    PinRecord,
    PrefixRecord,
    SampleRecord,
)


def test_prefix_round_trip() -> None:
    record = PrefixRecord(
        prefix_id="p1",
        domain="airline",
        task_id="t1",
        trajectory_id="traj",
        donor="gpt-4o",
        trial=0,
        step_index=2,
        tool_name="get_reservation_details",
        observation_json='{"a": 1}',
        factual_continuation='{"tool": "x"}',
        tool_family="read",
        step_index_bucket="early",
        used_fields=[{"json_path": "/a", "value": 1}],
        critical_fields=["a"],
        renderer_version="cto-prose-v1",
        arm="s0",
        severity=0,
    )
    restored = PrefixRecord.from_dict(record.to_dict())
    assert restored == record
    assert restored.schema_version == "toolresult800-prefix-v1"


def test_perturbation_round_trip() -> None:
    record = PerturbationRecord(
        prefix_id="p1",
        arm="s2",
        severity=2,
        json_path="/refund_amount",
        true_value=84.5,
        false_value=48.5,
        criticality="critical",
        expected_action_change=True,
        renderer_version="cto-prose-v1",
        record_id="r1",
        perturbation_mode="numeric_scale",
        pii_check=True,
        identifier_check=True,
    )
    restored = PerturbationRecord.from_dict(record.to_dict())
    assert restored == record
    assert restored.schema_version == "toolresult800-perturbation-v1"


def test_signature_canonical_order_independent() -> None:
    left = DecisionSignature(tool_name="f", arguments={"b": 2, "a": 1})
    right = DecisionSignature(tool_name="f", arguments={"a": 1, "b": 2})
    assert left.canonical() == right.canonical()


def test_ledger_round_trip() -> None:
    row = LedgerRow(
        run_id="run",
        model_id="qwen",
        prefix_id="p1",
        arm="V",
        step=0,
        prompt_hash="abc",
        output_text="{}",
        parsed=True,
        latency_ms=12.5,
        cost_usd=0.0,
        timestamp_utc="2026-11-15T00:00:00+00:00",
        stage="calibration",
        gpu_hours=0.01,
        storage_gb=0.001,
        parser_version="cto-parser-v1",
        prompt_version="cto-next-decision-v1",
        manifest_hash="def",
    )
    restored = LedgerRow.from_dict(row.to_dict())
    assert restored == row
    assert restored.schema_version == "toolresult800-ledger-v1"


def test_auxiliary_records_round_trip() -> None:
    sample = SampleRecord(
        prefix_id="p1",
        domain="retail",
        task_id="t1",
        donor="gpt-4o",
        step_bucket="mid",
        tool_family="read",
        split="primary",
        stratum="retail|gpt-4o|mid|read",
        seed=20261108,
    )
    assert SampleRecord.from_dict(sample.to_dict()) == sample

    pin = PinRecord(
        repo_url="https://example.invalid/repo",
        commit_sha="0" * 40,
        license="MIT",
        trajectory_hashes={"a.json": "abc"},
        task_db_hashes={"db.json": "def"},
        harness_hash="ghi",
    )
    assert PinRecord.from_dict(pin.to_dict()) == pin

    model = ModelPins(
        model_id="qwen",
        repo_id="org/qwen",
        revision="0" * 40,
        quantization="awq_4bit",
        tokenizer_hash="abc",
        license="Apache-2.0",
    )
    assert ModelPins.from_dict(model.to_dict()) == model

    manifest = FrozenManifest(
        schema_version="toolresult800-manifest-v1",
        manifest_id="m1",
        created_utc="2026-11-15T00:00:00+00:00",
        prereg_hash="p",
        renderer_version="v1",
        renderer_hash="r",
        field_registry_hash="f",
        sample_hash="s",
        perturbations_hash="x",
        counts={"primary": 800},
    )
    assert FrozenManifest.from_dict(manifest.to_dict()) == manifest
