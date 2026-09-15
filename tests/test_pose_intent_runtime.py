"""Focused regression tests for pose-intent preservation."""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.leg_separation_runtime import (  # noqa: E402
    DEFAULT_LEG_SEPARATION_CONTRACT,
    LegSeparationGate,
    candidate_promotion_status,
    promote_candidate,
)
from runtime.pose_intent_runtime import (  # noqa: E402
    PoseIntentFailureType,
    PoseIntentGate,
    PoseIntentType,
    PoseDiversityLedger,
    audit_pose_intent_prompt,
    build_pose_intent_contract,
    compose_pose_validation,
    detect_safe_pose_homogenization,
    migrate_pose_intent_fields,
    prepare_pose_intent_repair,
)
from runtime.regional_style_runtime import PromptCompiler  # noqa: E402


IMAGE = Path(__file__)


def actual(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "stance_width": "NORMAL",
        "foot_depth": "SAME_PLANE",
        "weight_distribution": "LEFT",
        "knee_state": "SOFT",
        "torso": "TILTED",
        "shoulder_relation": "ASYMMETRIC",
        "arm_activity": "ASYMMETRIC",
        "head_angle": "TILTED",
        "energy_read": "MEDIUM",
    }
    values.update(overrides)
    return values


def gate(intent: str, **overrides: object):
    contract = build_pose_intent_contract(intent, resolved_pose_family="TEST_FAMILY")
    return PoseIntentGate().review(IMAGE, observations=actual(**overrides), contract=contract)


def test_intent_enum_covers_required_types() -> None:
    assert {item.value for item in PoseIntentType} >= {
        "ELEGANT",
        "SENSUAL",
        "RELAXED_ASYMMETRIC",
        "LOW_ENERGY",
        "NARROW_STANCE",
        "ONE_FOOT_FORWARD",
        "OPEN_STANCE",
        "WIDE_ACTIVE",
        "STABLE_OPEN",
        "CUSTOM",
    }


def test_elegant_contract_requires_body_language() -> None:
    contract = build_pose_intent_contract("ELEGANT", resolved_pose_family="ASYMMETRIC_WEIGHT_STANCE")
    assert contract.minimum_visible_signals >= 3
    assert "intentional body asymmetry" in contract.required_body_signals


def test_prompt_compiler_keeps_elegant_intent_out_of_neutral_pose() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="simple",
        pose_intent="ELEGANT",
        pose_description="elegant standing pose",
    )
    assert bundle.pose_intent == "ELEGANT"
    assert "controlled posture" in bundle.prompt
    assert "intentional body asymmetry" in bundle.prompt
    assert bundle.prompt.index("## POSE INTENT") < bundle.prompt.index("## LEG GEOMETRY / ANATOMY CONSTRAINT")
    assert audit_pose_intent_prompt(bundle.prompt, "ELEGANT")["passed"] is True


def test_sensual_contract_requires_body_language_not_clothing() -> None:
    contract = build_pose_intent_contract("SENSUAL")
    assert "torso waist relationship" in contract.required_body_signals
    assert "clothing fanservice replacing body language" in contract.forbidden_shortcuts


def test_sensual_outfit_only_read_is_weak_or_fail() -> None:
    result = gate(
        "SENSUAL",
        stance_width="NORMAL",
        weight_distribution="CENTERED",
        knee_state="STRAIGHT",
        torso="UPRIGHT",
        shoulder_relation="LEVEL",
        arm_activity="CLOSED",
        head_angle="NEUTRAL",
        outfit_only_sensuality=True,
    )
    assert result.result in {"WEAK", "FAIL"}
    assert PoseIntentFailureType.SENSUAL_POSE_REDUCED_TO_OUTFIT.value in result.failure_types


def test_low_energy_prompt_contains_quiet_body_signals() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="quiet character",
        pose_intent="LOW_ENERGY",
        pose_description="low energy standing pose",
    )
    for signal in ("lowered shoulders", "softened knees", "settled weight", "quiet arm placement"):
        assert signal in bundle.prompt


def test_narrow_intent_preserves_narrow_width_requirement() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="refined character",
        pose_intent="NARROW_STANCE",
        pose_description="narrow separated standing pose",
    )
    assert bundle.pose_intent_contract["stance_width_requirement"] == "NARROW"
    assert "narrow stance width" in bundle.prompt


def test_forward_intent_preserves_depth_requirement() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="moving character",
        pose_intent="ONE_FOOT_FORWARD",
        pose_description="one foot naturally forward",
    )
    assert bundle.pose_intent_contract["depth_requirement"] == "FORWARD_LEFT_OR_RIGHT"
    assert "clear forward foot depth" in bundle.prompt


def test_relaxed_asymmetric_intent_preserves_asymmetry_signals() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="natural character",
        pose_intent="RELAXED_ASYMMETRIC",
        pose_description="relaxed asymmetric standing pose",
    )
    assert bundle.pose_intent_contract["asymmetry_requirement"] == "REQUIRED"
    assert "shoulder asymmetry" in bundle.prompt
    assert "asymmetric arm placement" in bundle.prompt


def test_leg_contract_does_not_turn_narrow_into_wide() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="simple",
        pose_intent="NARROW_STANCE",
        pose_description="narrow separated stance",
    )
    assert bundle.pose_family == "NARROW_SEPARATED_STANCE"
    assert bundle.pose_intent_contract["stance_width_requirement"] == "NARROW"
    assert "wide stance" not in bundle.pose_intent_contract["forbidden_shortcuts"]
    assert bundle.leg_separation_contract == DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()


def test_leg_contract_does_not_turn_forward_step_into_same_plane() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="simple",
        pose_intent="ONE_FOOT_FORWARD",
        pose_description="one foot forward in its own lane",
    )
    assert bundle.pose_family == "FORWARD_STEP_NON_CROSSING"
    assert bundle.pose_intent_contract["depth_requirement"] == "FORWARD_LEFT_OR_RIGHT"


def test_narrow_requested_but_normal_actual_fails() -> None:
    result = gate("NARROW_STANCE", stance_width="NORMAL")
    assert result.result == "FAIL"
    assert PoseIntentFailureType.NARROW_STANCE_EXPANDED.value in result.failure_types


def test_forward_requested_but_same_plane_actual_fails() -> None:
    result = gate("ONE_FOOT_FORWARD", foot_depth="SAME_PLANE")
    assert result.result == "FAIL"
    assert PoseIntentFailureType.ONE_FOOT_FORWARD_DEPTH_MISSING.value in result.failure_types


def test_low_energy_requested_but_high_energy_actual_fails() -> None:
    result = gate("LOW_ENERGY", energy_read="HIGH", torso="UPRIGHT", shoulder_relation="LEVEL")
    assert result.result == "FAIL"
    assert PoseIntentFailureType.LOW_ENERGY_READ_MISSING.value in result.failure_types


def test_elegant_neutral_military_read_fails() -> None:
    result = gate(
        "ELEGANT",
        stance_width="NORMAL",
        weight_distribution="CENTERED",
        knee_state="STRAIGHT",
        torso="UPRIGHT",
        shoulder_relation="LEVEL",
        arm_activity="CLOSED",
        head_angle="NEUTRAL",
    )
    assert result.result == "FAIL"
    assert PoseIntentFailureType.ELEGANT_POSE_REDUCED_TO_NEUTRAL.value in result.failure_types


def test_relaxed_asymmetric_visible_asymmetry_passes() -> None:
    result = gate("RELAXED_ASYMMETRIC")
    assert result.result in {"STRONG", "ACCEPTABLE"}
    assert PoseIntentFailureType.RELAXED_ASYMMETRY_MISSING.value not in result.failure_types


def test_pose_gate_distinguishes_leg_pass_and_pose_fail() -> None:
    pose = gate("NARROW_STANCE", stance_width="NORMAL")
    leg = LegSeparationGate().review(
        IMAGE,
        observations={
            "thigh_relation": "separate",
            "knee_relation": "separate",
            "calf_relation": "separate",
            "ankle_relation": "separate",
            "foot_relation": "separate",
            "centerline_crossing": False,
            "leg_negative_space": True,
        },
    )
    assert compose_pose_validation(leg, pose).overall_result == "POSE_INTENT_FAIL"
    assert candidate_promotion_status(leg, pose_intent_gate=pose) == "POSE_INTENT_FAIL"
    assert promote_candidate(leg, pose_intent_gate=pose)["promoted"] is False


def test_leg_fail_and_pose_pass_still_fails_overall_pose() -> None:
    pose = gate("NARROW_STANCE", stance_width="NARROW")
    leg = LegSeparationGate().review(
        IMAGE,
        observations={
            "thigh_relation": "crossed",
            "knee_relation": "separate",
            "calf_relation": "separate",
            "ankle_relation": "separate",
            "foot_relation": "separate",
            "centerline_crossing": False,
            "leg_negative_space": True,
        },
    )
    assert compose_pose_validation(leg, pose).overall_result == "FAIL"


def test_both_gates_pass_to_pose_valid() -> None:
    pose = gate("NARROW_STANCE", stance_width="NARROW")
    leg = LegSeparationGate().review(
        IMAGE,
        observations={
            "thigh_relation": "separate",
            "knee_relation": "separate",
            "calf_relation": "separate",
            "ankle_relation": "separate",
            "foot_relation": "separate",
            "centerline_crossing": False,
            "leg_negative_space": True,
        },
    )
    assert compose_pose_validation(leg, pose).overall_result == "POSE_VALID"


def test_pose_intent_repair_preserves_character_identity_and_reruns_leg_gate() -> None:
    final_design = {
        "character_identity": "locked face and hair",
        "outfit": "locked outfit",
        "palette": "locked palette",
        "body_build": "locked body",
        "regional_visual_language": "EAST_ASIAN_CONTEMPORARY_GACHA",
        "background_direction": "locked background",
    }
    repair = prepare_pose_intent_repair(final_design, gate("NARROW_STANCE", stance_width="NORMAL"))
    assert repair["status"] == "POSE_INTENT_ONLY_REPAIR"
    assert repair["design_snapshot"] == final_design
    assert repair["revalidate_leg_separation_gate"] is True
    assert "outfit" not in repair["change_only"]


def test_pose_intent_migration_maps_reliable_family_without_mutation() -> None:
    legacy = {"schema_version": "1.0.0", "pose_family": "NARROW_SEPARATED_STANCE"}
    migrated, event = migrate_pose_intent_fields(legacy)
    assert "pose_intent" not in legacy
    assert migrated["pose_intent"] == "NARROW_STANCE"
    assert migrated["pose_intent_contract"]["leg_safety_required"] is True
    assert event and event["reliable_mapping"] is True


def test_pose_intent_migration_uses_unknown_for_ambiguous_legacy_family() -> None:
    migrated, event = migrate_pose_intent_fields({"pose_family": "ASYMMETRIC_WEIGHT_STANCE"})
    assert migrated["pose_intent"] == "UNKNOWN_LEGACY_POSE_INTENT"
    assert event and event["reliable_mapping"] is False


def test_pose_diversity_ledger_detects_same_actual_pose_under_different_names() -> None:
    records = [
        {
            "stance_width": "NORMAL",
            "foot_depth": "SAME_PLANE",
            "weight_distribution": "CENTERED",
            "knee_state": "STRAIGHT",
            "torso": "UPRIGHT",
            "shoulder_relation": "LEVEL",
            "arm_activity": "CLOSED",
            "head_angle": "NEUTRAL",
            "energy_read": "MEDIUM",
            "requested_intent": intent,
        }
        for intent in ("ELEGANT", "SENSUAL", "OPEN_STANCE")
    ]
    result = detect_safe_pose_homogenization(records)
    assert result["result"] == "SAFE_POSE_HOMOGENIZATION"
    assert result["hard_gate"] is False


def test_pose_diversity_ledger_allows_explicit_uniform_request() -> None:
    ledger = PoseDiversityLedger()
    ledger.add(actual())
    ledger.add(actual())
    result = ledger.homogenization(user_requested_uniform=True)
    assert result["result"] == "NONE"
    assert result["user_requested_uniform"] is True


def test_both_schemas_expose_pose_intent_fields() -> None:
    root = Path(__file__).parents[1]
    for name in ("regional_style.schema.json", "visual_preference_sheet.schema.json"):
        schema = json.loads((root / "schemas" / name).read_text(encoding="utf-8"))
        assert "pose_intent" in schema["properties"]
        assert "pose_intent_contract" in schema["properties"]
        assert "pose_intent_gate" in schema["properties"]
        assert "poseDiversityLedger" in schema["$defs"]
