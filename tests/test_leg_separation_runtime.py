"""Regression tests for the hard no-crossed-legs invariant."""

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.leg_separation_runtime import (  # noqa: E402
    DEFAULT_LEG_SEPARATION_CONTRACT,
    LEG_GEOMETRY_POSITIVE,
    LegFailureType,
    LegSeparationError,
    LegSeparationGate,
    NO_CROSSED_LEGS_HARD_INVARIANT,
    audit_leg_prompt,
    candidate_promotion_status,
    migrate_leg_separation_fields,
    prepare_pose_only_repair,
    promote_candidate,
    validate_final_design,
    validate_pose_options,
)
from runtime.regional_style_runtime import PromptCompiler, load_style_policy  # noqa: E402


def _observations(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "thigh_relation": "separate",
        "knee_relation": "separate",
        "calf_relation": "separate",
        "ankle_relation": "separate",
        "foot_relation": "separate",
        "centerline_crossing": False,
        "leg_negative_space": True,
    }
    values.update(overrides)
    return values


def _gate(**overrides: object):
    return LegSeparationGate().review(Path(__file__), observations=_observations(**overrides))


def test_hard_invariant_is_enabled_and_contract_is_all_true() -> None:
    assert NO_CROSSED_LEGS_HARD_INVARIANT is True
    assert all(DEFAULT_LEG_SEPARATION_CONTRACT.to_dict().values())


def test_final_design_crossed_leg_language_fails() -> None:
    with pytest.raises(LegSeparationError, match="VALIDATION_ERROR"):
        validate_final_design({"pose": "crossed-leg elegant stance"})


def test_elegant_asymmetric_stance_gets_positive_geometry() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="elegant asymmetric stance",
        pose_description="elegant asymmetric stance",
    )
    assert all(item in bundle.prompt for item in LEG_GEOMETRY_POSITIVE)
    assert bundle.pose_family == "ASYMMETRIC_WEIGHT_STANCE"


def test_strong_fanservice_cannot_remove_hard_constraints() -> None:
    bundle = PromptCompiler().compile(character_visual_style="strong fanservice", fanservice_level="strong")
    assert "no crossed legs" in bundle.prompt
    assert "both thighs independently readable" in bundle.prompt


def test_male_character_receives_the_same_contract() -> None:
    bundle = PromptCompiler().compile(character_visual_style="adult male character")
    assert bundle.leg_separation_contract == DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()


def test_petite_adult_receives_the_same_contract() -> None:
    bundle = PromptCompiler().compile(character_visual_style="petite adult character", age_group="adult")
    assert "no crossed knees" in bundle.prompt


def test_narrow_separated_stance_is_allowed() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="quiet character",
        pose_description="narrow separated stance with a visible gap",
    )
    assert bundle.pose_family == "NARROW_SEPARATED_STANCE"
    assert bundle.leg_crossing_risk == "LOW"


def test_one_foot_forward_without_centerline_crossing_is_allowed() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="active character",
        pose_description="one foot slightly forward in its own lane",
    )
    assert bundle.pose_family == "FORWARD_STEP_NON_CROSSING"


def test_safe_pose_families_remain_diverse_without_wide_stance_collapse() -> None:
    families = (
        ("OPEN_PARALLEL_STANCE", "open parallel stance"),
        ("OFFSET_NON_OVERLAPPING_STANCE", "offset non-overlapping stance"),
        ("ASYMMETRIC_WEIGHT_STANCE", "elegant asymmetric stance"),
        ("WIDE_ACTIVE_STANCE", "wide active stance"),
        ("NARROW_SEPARATED_STANCE", "narrow separated stance"),
        ("LOW_ENERGY_SEPARATED_STANCE", "quiet low energy separated stance"),
        ("FORWARD_STEP_NON_CROSSING", "one foot forward in its own lane"),
    )
    bundles = [
        PromptCompiler().compile(
            character_visual_style="case-specific style",
            pose_description=description,
            pose_family=family,
        )
        for family, description in families
    ]
    assert [bundle.pose_family for bundle in bundles] == [family for family, _ in families]
    assert len({bundle.pose_family for bundle in bundles}) == 7
    assert sum(bundle.pose_family == "WIDE_ACTIVE_STANCE" for bundle in bundles) == 1


@pytest.mark.parametrize("fanservice_level", ["light", "moderate", "strong"])
def test_fanservice_levels_keep_explicit_barefoot_thigh_ring_and_safe_geometry(fanservice_level: str) -> None:
    lower_body = {
        "exposure_strategy": "full-leg exposure",
        "legwear_family": "none",
        "leg_accessory_family": "thigh ring",
        "footwear_family": "barefoot",
        "foot_visibility": "toes visible",
        "visual_reason": "adult character-specific lower-body framing",
    }
    bundle = PromptCompiler().compile(
        character_visual_style="adult sensual design",
        fanservice_level=fanservice_level,
        pose_description="open parallel stance",
        lower_body=lower_body,
    )
    assert "Skin Exposure Strategy: full-leg exposure" in bundle.prompt
    assert "Leg Accessory Family: thigh ring" in bundle.prompt
    assert "Footwear Family: barefoot" in bundle.prompt
    assert "visible negative space between the legs" in bundle.prompt


def test_ankles_crossing_is_a_blocking_fail() -> None:
    result = _gate(ankle_relation="crossed")
    assert result.result == "FAIL"
    assert LegFailureType.ANKLE_CROSSING_FAIL.value in result.failure_types
    assert LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value in result.failure_types


def test_calves_crossing_is_a_blocking_fail() -> None:
    result = _gate(calf_relation="overlapping")
    assert result.result == "FAIL"
    assert LegFailureType.CALF_CROSSING_FAIL.value in result.failure_types


def test_safe_pose_prior_override_is_a_blocking_fail() -> None:
    result = _gate(safe_pose_prior_override_fail=True, stance_family="ASYMMETRIC_WEIGHT_STANCE")
    assert result.result == "FAIL"
    assert LegFailureType.SAFE_POSE_PRIOR_OVERRIDE_FAIL.value in result.failure_types
    assert result.stance_family == "ASYMMETRIC_WEIGHT_STANCE"


def test_knees_overlapping_is_uncertain_when_not_confirmed() -> None:
    result = _gate(knee_relation="uncertain")
    assert result.result == "UNCERTAIN"
    assert LegFailureType.LEG_OCCLUSION_UNCERTAIN.value in result.failure_types


def test_uncertain_gate_blocks_normal_candidate_promotion() -> None:
    result = _gate(knee_relation="uncertain")
    assert candidate_promotion_status(result) == "REJECTED_BY_HARD_ANATOMY_GATE"
    assert promote_candidate(result)["promoted"] is False


def test_first_pass_benchmark_preserves_failure_without_promoting_it() -> None:
    result = _gate(thigh_relation="crossed")
    assert candidate_promotion_status(result, first_pass_benchmark=True) == "FIRST_PASS_LEG_CROSSING_FAIL"


def test_first_crossed_result_allows_one_pose_only_repair() -> None:
    repair = prepare_pose_only_repair({"face": "locked", "outfit": "locked"}, 0)
    assert repair["status"] == "POSE_ONLY_REGENERATION"
    assert repair["pose_repair_count"] == 1
    assert repair["change_only"] == ("stance", "leg geometry")


def test_second_pose_repair_stops_as_unresolved() -> None:
    repair = prepare_pose_only_repair({"face": "locked", "outfit": "locked"}, 1)
    assert repair["status"] == "LEG_GEOMETRY_UNRESOLVED"


def test_visual_preference_pose_options_reject_crossed_pose() -> None:
    with pytest.raises(LegSeparationError):
        validate_pose_options([{"id": "bad", "value": "coy leg pose", "reason": "bad", "diversity_risk": "high"}])


def test_prompt_audit_fails_when_positive_geometry_is_missing() -> None:
    bundle = PromptCompiler().compile(character_visual_style="simple")
    audit = audit_leg_prompt(bundle.prompt.replace("both calves independently readable\n", ""))
    assert audit["positive_leg_geometry_present"] is False
    assert audit["passed"] is False


def test_elegant_style_words_are_rewritten_not_allowed_to_override() -> None:
    bundle = PromptCompiler().compile(character_visual_style="elegant crossed-leg fashion")
    assert "crossed-leg" not in bundle.character_visual_style.lower()
    assert "no crossed legs" in bundle.prompt


def test_model_and_fashion_style_words_are_rewritten() -> None:
    bundle = PromptCompiler().compile(character_visual_style="elegant model pose, fashion stance")
    assert "model pose" not in bundle.character_visual_style.lower()
    assert "fashion stance" not in bundle.character_visual_style.lower()


def test_sensual_style_words_keep_the_hard_geometry() -> None:
    bundle = PromptCompiler().compile(character_visual_style="sensual adult design", fanservice_level="strong")
    assert "visible negative space between the legs" in bundle.prompt
    assert "no crossed ankles" in bundle.prompt


def test_regional_style_cannot_override_the_contract() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="regional fashion pose",
        regional_visual_language="EAST_ASIAN_CONTEMPORARY_GACHA",
    )
    assert bundle.leg_separation_contract["no_centerline_crossing"] is True
    assert bundle.leg_crossing_risk == "LOW"


def test_legacy_migration_adds_contract_without_mutating_input() -> None:
    legacy = {"schema_version": "1.0.0", "pose": "quiet stance"}
    migrated, event = migrate_leg_separation_fields(legacy)
    assert "leg_separation_contract" not in legacy
    assert migrated["leg_separation_contract"] == DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
    assert migrated["pose_family"] == "LOW_ENERGY_SEPARATED_STANCE"
    assert event is not None


def test_pass_gate_promotes_candidate() -> None:
    result = _gate()
    assert result.result == "PASS"
    assert promote_candidate(result)["candidate_promotion_status"] == "PROMOTED_TO_CANDIDATE"


def test_yaml_policy_makes_override_impossible_and_repair_bounded() -> None:
    policy = load_style_policy(Path(__file__).parents[1] / "config" / "anime_style_policy.yaml")
    hard = policy["pose_constraints"]["no_crossed_legs"]
    assert hard["enabled"] is True
    assert hard["severity"] == "blocking"
    assert hard["allow_user_override"] is False
    assert hard["max_pose_only_repair"] == 1


def test_schema_declares_leg_contract_gate_and_promotion_fields() -> None:
    schema = json.loads((Path(__file__).parents[1] / "schemas" / "regional_style.schema.json").read_text(encoding="utf-8"))
    assert "leg_separation_contract" in schema["properties"]
    assert "leg_separation_gate" in schema["properties"]
    assert "candidate_promotion_status" in schema["properties"]
    assert schema["$defs"]["legSeparationContract"]["properties"]["thighs_separate"] == {"const": True}


def test_historical_leg_failures_are_negative_fixtures_only() -> None:
    fixture_path = Path(__file__).parent / "fixtures" / "hard_no_crossed_legs_negative_fixtures.json"
    fixture_set = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert fixture_set["future_image_reference_allowed"] is False
    assert len(fixture_set["fixtures"]) == 4
    assert all("LEG_CROSSING_BLOCKING_FAIL" in item["failure_types"] for item in fixture_set["fixtures"])


def test_visual_preference_schema_declares_the_migrated_contract() -> None:
    schema = json.loads(
        (Path(__file__).parents[1] / "schemas" / "visual_preference_sheet.schema.json").read_text(encoding="utf-8")
    )
    assert "leg_separation_contract" in schema["properties"]
    assert schema["$defs"]["legSeparationContract"]["properties"]["ankles_separate"] == {"const": True}
