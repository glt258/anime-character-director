"""Contract tests for strict adherence versus repair disposition."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.adherence_policy import (  # noqa: E402
    AdherencePolicyError,
    evaluate_adherence_disposition,
)
from runtime.interaction_runtime import InteractionRuntime  # noqa: E402
from runtime.visual_adherence_critic import VisualAdherenceReview  # noqa: E402
from runtime.visual_repair import build_repair_plan  # noqa: E402


IMAGE = Path(__file__)


def _review(
    fields: dict[str, tuple[str, str, str]],
    *,
    anatomy: str = "PASS",
) -> dict[str, object]:
    field_results = {
        name: {
            "required": required,
            "observed": observed,
            "result": result,
            "failure_types": ["TYPE 3"] if result == "FAIL" else ["TYPE 4"] if result == "PARTIAL" else [],
            "rationale": "fixture",
        }
        for name, (required, result, observed) in fields.items()
    }
    failed = [item for item in field_results.values() if item["result"] == "FAIL"]
    partial = [item for item in field_results.values() if item["result"] == "PARTIAL"]
    overall = "FAIL" if failed or anatomy == "FAIL" else "PARTIAL" if partial else "PASS"
    return {
        "actual_image": str(IMAGE),
        "overall_result": overall,
        "field_results": field_results,
        "anatomy_check": {"result": anatomy},
        "repair_targets": [
            {"field": name, **value}
            for name, value in field_results.items()
            if value["result"] in {"FAIL", "PARTIAL"}
        ]
        + ([{"field": "anatomy_check", "result": anatomy}] if anatomy != "PASS" else []),
    }


def _context(
    ownership: dict[str, str],
    *,
    strengths: dict[str, str] | None = None,
    overrides: dict[str, dict[str, object]] | None = None,
) -> tuple[dict[str, object], dict[str, object]]:
    strengths = strengths or {}
    metadata = {name: {"ownership": value} for name, value in ownership.items()}
    for name, value in (overrides or {}).items():
        metadata.setdefault(name, {}).update(value)
    contract = {
        "hard_constraints": {name: "required" for name in ownership if strengths.get(name, "HARD") == "HARD"},
        "strong_preferences": {name: "required" for name in ownership if strengths.get(name) == "STRONG"},
        "soft_intent": {name: "required" for name in ownership if strengths.get(name) == "SOFT"},
        "field_metadata": metadata,
    }
    return {"field_metadata": metadata}, contract


def _policy(fields: dict[str, tuple[str, str, str]], ownership: dict[str, str], **kwargs: object) -> dict[str, object]:
    manifest, contract = _context(ownership, **kwargs)
    return evaluate_adherence_disposition(_review(fields), manifest=manifest, visual_specification_contract=contract).to_dict()


def test_human_explicit_fail_is_critical_and_requires_repair() -> None:
    disposition = _policy({"footwear_category": ("open-toe high heels", "FAIL", "boots")}, {"footwear_category": "HUMAN_EXPLICIT"})

    assert disposition["strict_overall_result"] == "FAIL"
    assert disposition["human_constraint_result"] == "FAIL"
    assert disposition["disposition"] == "REPAIR_REQUIRED"
    assert disposition["repair_required"] is True
    assert disposition["auto_repair_eligible"] is True
    assert [item["field"] for item in disposition["actionable_repair_targets"]] == ["footwear_category"]
    assert disposition["actionable_repair_targets"][0]["repair_importance"] == "CRITICAL"


def test_human_explicit_partial_is_major_but_recommended() -> None:
    disposition = _policy({"footwear_category": ("open-toe high heels", "PARTIAL", "heels")}, {"footwear_category": "HUMAN_EXPLICIT"})

    assert disposition["disposition"] == "REPAIR_RECOMMENDED"
    assert disposition["repair_required"] is False
    assert disposition["auto_repair_eligible"] is True
    assert disposition["actionable_repair_targets"][0]["repair_importance"] == "MAJOR"


def test_human_selection_fail_keeps_human_priority() -> None:
    disposition = _policy({"costume_topology": ("maid outfit", "FAIL", "gothic dress")}, {"costume_topology": "HUMAN_SELECTION"})

    target = disposition["actionable_repair_targets"][0]
    assert target["ownership"] == "HUMAN_SELECTION"
    assert target["repair_importance"] == "CRITICAL"
    assert disposition["disposition"] == "REPAIR_REQUIRED"


def test_ai_resolved_fail_is_strict_fail_but_nonblocking() -> None:
    disposition = _policy({"architecture_presence": ("none", "FAIL", "gothic cathedral")}, {"architecture_presence": "AI_RESOLVED"})

    assert disposition["strict_overall_result"] == "FAIL"
    assert disposition["human_constraint_result"] == "NOT_APPLICABLE"
    assert disposition["ai_design_fidelity_result"] == "FAIL"
    assert disposition["disposition"] == "ACCEPT_WITH_DEVIATIONS"
    assert disposition["repair_required"] is False
    assert disposition["auto_repair_eligible"] is False
    assert disposition["actionable_repair_targets"] == []
    assert disposition["informational_deviations"][0]["field"] == "architecture_presence"


def test_ai_resolved_partial_is_informational() -> None:
    disposition = _policy({"head_attitude": ("quiet", "PARTIAL", "dramatic")}, {"head_attitude": "AI_RESOLVED"})

    assert disposition["ai_design_fidelity_result"] == "PARTIAL"
    assert disposition["disposition"] == "ACCEPT_WITH_DEVIATIONS"
    assert disposition["informational_deviations"][0]["repair_importance"] == "INFORMATIONAL"


def test_system_default_fail_does_not_auto_repair() -> None:
    disposition = _policy({"background_complexity": ("low", "FAIL", "busy")}, {"background_complexity": "SYSTEM_DEFAULT"})

    assert disposition["disposition"] == "ACCEPT_WITH_DEVIATIONS"
    assert disposition["auto_repair_eligible"] is False
    assert disposition["repair_required"] is False


def test_anatomy_invariant_failure_requires_repair() -> None:
    review = _review({}, anatomy="FAIL")
    disposition = evaluate_adherence_disposition(review).to_dict()

    target = disposition["actionable_repair_targets"][0]
    assert target["field"] == "anatomy_check"
    assert target["ownership"] == "SYSTEM_INVARIANT"
    assert target["repair_importance"] == "CRITICAL"
    assert disposition["system_invariant_result"] == "FAIL"
    assert disposition["disposition"] == "REPAIR_REQUIRED"


def test_global_rendering_invariant_can_use_major_override() -> None:
    disposition = _policy(
        {"global_rendering_style": ("commercial gacha anime", "FAIL", "photorealistic")},
        {"global_rendering_style": "SYSTEM_INVARIANT"},
        overrides={"global_rendering_style": {"repair_importance": "MAJOR"}},
    )

    assert disposition["actionable_repair_targets"][0]["repair_importance"] == "MAJOR"
    assert disposition["disposition"] == "REPAIR_REQUIRED"


def test_real_run_a_fixture_accepts_ai_deviations_without_repair() -> None:
    fields = {
        "role_identity": ("maid commander", "PASS", "maid commander"),
        "costume_topology": ("maid outfit", "PASS", "maid outfit"),
        "human_form_requirement": ("human appearance", "PASS", "human appearance"),
        "companion_count": ("exactly two ghost dolls", "PASS", "exactly two ghost dolls"),
        "architecture_presence": ("none", "FAIL", "complex architecture"),
        "lower_body_structure": ("open trouser line", "PARTIAL", "skirt-like silhouette"),
    }
    ownership = {name: "HUMAN_EXPLICIT" for name in list(fields)[:4]}
    ownership.update({"architecture_presence": "AI_RESOLVED", "lower_body_structure": "AI_RESOLVED"})
    disposition = _policy(fields, ownership)

    assert disposition["strict_overall_result"] == "FAIL"
    assert disposition["human_constraint_result"] == "PASS"
    assert disposition["system_invariant_result"] == "PASS"
    assert disposition["ai_design_fidelity_result"] == "FAIL"
    assert disposition["disposition"] == "ACCEPT_WITH_DEVIATIONS"
    assert disposition["repair_required"] is False
    assert disposition["actionable_repair_targets"] == []
    assert {item["field"] for item in disposition["informational_deviations"]} == {"architecture_presence", "lower_body_structure"}


def test_mixed_failure_only_human_target_is_actionable() -> None:
    fields = {
        "costume_topology": ("maid outfit", "PASS", "maid outfit"),
        "props": ("fan", "FAIL", "no prop"),
        "architecture_presence": ("none", "FAIL", "cathedral"),
    }
    disposition = _policy(fields, {"costume_topology": "HUMAN_EXPLICIT", "props": "HUMAN_EXPLICIT", "architecture_presence": "AI_RESOLVED"})

    assert disposition["disposition"] == "REPAIR_REQUIRED"
    assert [item["field"] for item in disposition["actionable_repair_targets"]] == ["props"]
    assert [item["field"] for item in disposition["informational_deviations"]] == ["architecture_presence"]


def test_manual_user_request_promotes_ai_target() -> None:
    review = _review({"architecture_presence": ("none", "FAIL", "cathedral")})
    manifest, contract = _context({"architecture_presence": "AI_RESOLVED"})
    disposition = evaluate_adherence_disposition(
        review,
        manifest=manifest,
        visual_specification_contract=contract,
        manual_repair_fields=("architecture_presence",),
    ).to_dict()

    target = disposition["actionable_repair_targets"][0]
    assert target["field"] == "architecture_presence"
    assert target["manual_repair_requested"] is True
    assert target["auto_repair_eligible"] is False
    assert disposition["disposition"] == "REPAIR_RECOMMENDED"


def test_not_evaluable_blocks_decision_but_never_triggers_repair() -> None:
    disposition = _policy({"hair_structure": ("braided", "NOT_EVALUABLE", "")}, {"hair_structure": "HUMAN_EXPLICIT"})

    assert disposition["disposition"] == "BLOCKED"
    assert disposition["repair_required"] is False
    assert disposition["auto_repair_eligible"] is False
    assert disposition["actionable_repair_targets"] == []


def test_configured_high_risk_blocks_automatic_repair() -> None:
    disposition = _policy(
        {"footwear_category": ("combat boots", "FAIL", "stilettos")},
        {"footwear_category": "HUMAN_EXPLICIT"},
        overrides={"footwear_category": {"repair_risk": "HIGH"}},
    )

    target = disposition["informational_deviations"][0]
    assert target["repair_risk"] == "HIGH"
    assert target["auto_repair_eligible"] is False
    assert disposition["repair_required"] is True


def test_repair_plan_consumes_actionable_targets_only() -> None:
    review = _review(
        {
            "props": ("fan", "FAIL", "none"),
            "architecture_presence": ("none", "FAIL", "cathedral"),
        }
    )
    manifest, contract = _context({"props": "HUMAN_EXPLICIT", "architecture_presence": "AI_RESOLVED"})
    plan = build_repair_plan(review, manifest=manifest, visual_specification_contract=contract)

    assert [item["field"] for item in plan.repair_targets] == ["props"]
    assert [item["field"] for item in plan.actionable_repair_targets] == ["props"]
    assert [item["field"] for item in plan.informational_deviations] == ["architecture_presence"]


def test_pass_fields_locking_remains_unchanged() -> None:
    review = _review({"footwear_category": ("combat boots", "PASS", "combat boots"), "props": ("fan", "FAIL", "none")})
    manifest, contract = _context({"footwear_category": "HUMAN_SELECTION", "props": "HUMAN_EXPLICIT"})
    plan = build_repair_plan(review, manifest=manifest, visual_specification_contract=contract)

    assert plan.locked_fields["footwear_category"] == "combat boots"
    assert [item["field"] for item in plan.repair_targets] == ["props"]


def test_replay_preserves_disposition_snapshot(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=31)
    runtime.record_generation_artifact(response.session_id, IMAGE)
    session = runtime.load_session(response.session_id)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = {name: value for source in ("hard_constraints", "strong_preferences") for name, value in manifest.get(source, {}).items()}
    observations = {
        "field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()},
        "hand_anatomy_check": {"result": "PASS"},
        "foot_visibility_and_integrity_check": {"result": "PASS"},
    }
    first = next(iter(fields))
    observations["field_results"][first] = {"observed": "wrong", "result": "FAIL"}
    review = runtime.record_visual_adherence_review(response.session_id, IMAGE, observations=observations)
    replay = runtime.replay_session(response.session_id)

    assert replay["visual_adherence_review"]["adherence_disposition"] == review["adherence_disposition"]
    assert replay["visual_adherence_review"]["repair_trigger_decision"] == review["repair_trigger_decision"]


def test_legacy_review_remains_readable_and_is_marked_legacy_derived() -> None:
    legacy = {
        "actual_image": str(IMAGE),
        "overall_result": "FAIL",
        "field_results": {"background_complexity": {"required": "low", "observed": "busy", "result": "FAIL", "failure_types": ["TYPE 5"], "rationale": ""}},
        "anatomy_check": {"result": "PASS"},
        "repair_targets": [{"field": "background_complexity", "result": "FAIL"}],
    }
    restored = VisualAdherenceReview.from_dict(legacy)
    disposition = evaluate_adherence_disposition(restored.to_dict()).to_dict()

    assert restored.overall_result == "FAIL"
    assert disposition["disposition_source"] == "legacy_derived"
    assert disposition["strict_overall_result"] == "FAIL"


def test_invalid_ownership_is_rejected() -> None:
    review = _review({"props": ("fan", "FAIL", "none")})
    manifest, contract = _context({"props": "NOT_A_VALID_OWNER"})

    with pytest.raises(AdherencePolicyError, match="unsupported ownership"):
        evaluate_adherence_disposition(review, manifest=manifest, visual_specification_contract=contract)


def test_policy_fields_are_schema_declared() -> None:
    schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" / "visual_adherence.schema.json").read_text(encoding="utf-8"))

    assert "adherence_disposition" in schema["properties"]
    assert "repair_trigger_decision" in schema["properties"]
