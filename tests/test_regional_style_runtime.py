"""Regression tests for regional visual language and style-layer governance."""

from pathlib import Path
import json
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.regional_style_runtime import (  # noqa: E402
    DEFAULT_REGIONAL_VISUAL_LANGUAGE,
    DriftType,
    GachaStyleCritic,
    MaleRegionalBodyReview,
    FOOTWEAR_FAMILIES,
    LEG_ACCESSORY_FAMILIES,
    LEGWEAR_FAMILIES,
    PromptCompiler,
    RegionalStyleError,
    RegionalStyleCritic,
    StrongFemaleRegionalStyleReview,
    RegionalVisualLanguageSource,
    detect_archetype_shortcut_replacement,
    detect_background_presentation_collapse,
    detect_generic_fantasy_rpg_drift,
    detect_outfit_family_collapse,
    detect_lower_body_collapse,
    check_lower_body_grounding,
    load_style_policy,
    migrate_regional_style_fields,
    resolve_regional_visual_language,
    review_male_regional_body,
    review_strong_female_regional_style,
    review_lower_body_design,
)
from runtime.visual_preference_runtime import VisualPreferenceSession  # noqa: E402
from test_visual_preference_runtime import make_sheet  # noqa: E402


def _observations(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "east_asian_gacha_read": 9,
        "western_anime_drift": "NONE",
        "western_concept_art_drift": "NONE",
        "facial_abstraction_match": 9,
        "body_rendering_match": 8,
        "costume_language_match": 8,
        "presentation_match": 9,
        "confidence": 0.9,
    }
    values.update(overrides)
    return values


def _lower_body(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "exposure_strategy": "mostly covered",
        "legwear_family": "opaque tights",
        "leg_accessory_family": "none",
        "footwear_family": "barefoot",
        "foot_visibility": "toes visible",
        "visual_reason": "clean lower-body silhouette and grounded mobility",
        "relationship_to_character_style": "quiet modern elegance",
        "relationship_to_pose": "both feet remain readable in the frontal standee",
        "repetition_risk": "low",
    }
    values.update(overrides)
    return values


def test_default_regional_style() -> None:
    selection = resolve_regional_visual_language()
    assert selection.regional_visual_language == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert selection.regional_visual_language_source == "default_style_policy"


def test_explicit_override_requires_reason_and_wins() -> None:
    selection = resolve_regional_visual_language(
        "WESTERN_ANIME_INSPIRED",
        explicit_user_override=True,
        override_reason="User explicitly requested western anime-inspired rendering.",
    )
    assert selection.regional_visual_language == "WESTERN_ANIME_INSPIRED"
    assert selection.regional_visual_language_source == "explicit_user_override"


def test_regional_source_supports_selection_and_benchmark_delegation() -> None:
    selection = resolve_regional_visual_language(
        "WESTERN_ANIME_INSPIRED",
        source=RegionalVisualLanguageSource.EXPLICIT_USER_SELECTION,
    )
    delegated = resolve_regional_visual_language(
        "REGION_NEUTRAL_ANIME",
        source=RegionalVisualLanguageSource.BENCHMARK_DELEGATION,
    )
    assert selection.regional_visual_language_source == "explicit_user_selection"
    assert delegated.regional_visual_language_source == "benchmark_delegation"


def test_regional_style_is_not_ethnicity_or_costume_lock() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="modern street",
        character_identity="dark-skinned adult character in contemporary clothing",
    )
    assert bundle.regional_visual_language == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert "dark-skinned" in bundle.prompt
    assert "hanfu" not in bundle.prompt.lower()
    assert "kimono" not in bundle.prompt.lower()
    assert "qipao" not in bundle.prompt.lower()


def test_mature_male_is_not_infantilized() -> None:
    critic = RegionalStyleCritic()
    review = critic.review(
        Path(__file__),
        observations=_observations(maturity_required=True, maturity_read=8),
    )
    assert review.result == "STYLE_VALID"
    assert review.maturity_read == 8


def test_strong_female_superhero_drift_fails_regional_gate() -> None:
    regional, gate = GachaStyleCritic().review(
        Path(__file__),
        global_rendering_result="PASS",
        observations=_observations(
            strong_female_required=True,
            western_superhero_anatomy_drift="HIGH",
        ),
    )
    assert regional.result == "FAIL"
    assert gate.overall_result == "FAIL"
    assert DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value in gate.detected_drift_types


def test_prompt_compiler_orders_three_layers_and_protects_regional_layer() -> None:
    bundle = PromptCompiler().compile(
        character_visual_style="western fantasy-inspired costume",
        regional_visual_language=DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        regional_visual_language_source="default_style_policy",
    )
    assert bundle.prompt.index("## Rendering Foundation") < bundle.prompt.index("## Regional Visual Language")
    assert bundle.prompt.index("## Regional Visual Language") < bundle.prompt.index("## Character Visual Style")
    assert bundle.regional_visual_language == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert bundle.prompt.index("## GLOBAL RENDERING MEDIUM") < bundle.prompt.index("## REGIONAL VISUAL LANGUAGE")
    assert bundle.prompt.index("## REGIONAL VISUAL LANGUAGE") < bundle.prompt.index("## CHARACTER VISUAL STYLE")


def test_prompt_compiler_rejects_an_unapplied_visual_context_firewall() -> None:
    with pytest.raises(RegionalStyleError, match="Visual Context Firewall"):
        PromptCompiler().compile(
            character_visual_style="clean-line contemporary gacha anime",
            visual_context_firewall={"visual_context_firewall_applied": False},
        )


def test_regional_critic_requires_actual_image_and_labeled_observations() -> None:
    critic = RegionalStyleCritic()
    review = critic.review(Path(__file__), observations=_observations(western_anime_drift="HIGH"))
    assert review.regional_visual_language_match == "FAIL"


def test_regional_review_records_perceived_language_and_drift_contract() -> None:
    review = RegionalStyleCritic().review(
        Path(__file__),
        observations=_observations(
            perceived_regional_visual_language="WESTERN_FANTASY_CONCEPT",
            pseudo_oriental_default_detected=True,
            generic_fantasy_rpg_drift="HIGH",
            material_language_match=7,
            rationale="Human observed a generic fantasy costume recipe.",
        ),
    )
    assert review.result == "FAIL"
    assert review.expected_regional_visual_language == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert review.pseudo_oriental_default_detected is True
    assert DriftType.GENERIC_FANTASY_RPG_DRIFT.value in review.detected_drift_types


def test_style_gate_requires_global_and_regional_pass() -> None:
    _, gate = GachaStyleCritic().review(
        Path(__file__), global_rendering_result="FAIL", observations=_observations()
    )
    assert gate.overall_result == "FAIL"


def test_outfit_family_collapse_is_a_diagnostic_not_a_hard_gate() -> None:
    records = [
        {
            "outfit_features": {
                "outfit_family": "generic fantasy robe",
                "sash_presence": True,
                "hanging_cloth_presence": True,
                "major_trim_language": "gold trim",
            }
        }
        for _ in range(4)
    ]
    result = detect_outfit_family_collapse(records)
    assert result["result"] == "HIGH"
    assert result["hard_gate"] is False
    assert result["diagnostic"] == DriftType.OUTFIT_FAMILY_COLLAPSE.value


def test_negative_fixture_classification_is_deterministic() -> None:
    _, gate = GachaStyleCritic().review(
        Path(__file__),
        global_rendering_result="PASS",
        observations=_observations(
            western_anime_drift="HIGH",
            western_concept_art_drift="HIGH",
        ),
    )
    assert DriftType.WESTERN_ANIME_STYLE_DRIFT.value in gate.detected_drift_types
    assert DriftType.WESTERN_FANTASY_CONCEPT_DRIFT.value in gate.detected_drift_types


def test_old_session_migrates_without_mutating_input() -> None:
    old_sheet = {"schema_version": "1.0.0", "variables": {}}
    migrated, event = migrate_regional_style_fields(old_sheet)
    assert "regional_visual_language" not in old_sheet
    assert migrated["regional_visual_language"] == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert migrated["regional_visual_language_source"] == "migrated_default"
    assert event and event["source"] == "migrated_default"
    assert event["audit_event"] == "REGIONAL_VISUAL_LANGUAGE_DEFAULT_MIGRATION"
    assert event["old_artifact_version"] == "1.0.0"


def test_visual_preference_session_records_migration() -> None:
    session = VisualPreferenceSession()
    sheet = make_sheet()
    session.propose(sheet)
    assert session.sheet["regional_visual_language"] == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert session.sheet["regional_visual_language_source"] == "migrated_default"
    assert all(session.sheet["leg_separation_contract"].values())
    assert session.history[0]["event"] == "regional_visual_language_migration"
    assert session.history[1]["event"] == "leg_separation_contract_migration"


def test_yaml_policy_is_loaded_and_has_default() -> None:
    policy = load_style_policy(Path(__file__).parents[1] / "config" / "anime_style_policy.yaml")
    assert policy["default"] == DEFAULT_REGIONAL_VISUAL_LANGUAGE
    assert policy["allow_user_override"] is True
    assert policy["contracts"][DEFAULT_REGIONAL_VISUAL_LANGUAGE]["positive"]


def test_migrated_default_source_is_not_human_selection() -> None:
    selection = resolve_regional_visual_language(migrated_default=True)
    assert selection.regional_visual_language_source == RegionalVisualLanguageSource.MIGRATED_DEFAULT.value


def test_schemas_declare_regional_fields_and_style_gate_shape() -> None:
    root = Path(__file__).parents[1]
    preference_schema = json.loads((root / "schemas" / "visual_preference_sheet.schema.json").read_text(encoding="utf-8"))
    regional_schema = json.loads((root / "schemas" / "regional_style.schema.json").read_text(encoding="utf-8"))
    assert "regional_visual_language" in preference_schema["properties"]
    assert "regional_visual_language_source" in preference_schema["properties"]
    assert "style_gate_result" in regional_schema["properties"]
    assert "explicit_user_selection" in preference_schema["properties"]["regional_visual_language_source"]["enum"]
    assert "regional_style_review" in regional_schema["properties"]
    assert "strong_female_regional_style_review" in regional_schema["properties"]


def test_six_archetype_images_are_negative_fixtures_not_references() -> None:
    root = Path(__file__).parents[1]
    fixture_set = json.loads(
        (root / "tests" / "fixtures" / "regional_style_negative_fixtures.json").read_text(encoding="utf-8")
    )
    assert len(fixture_set["fixtures"]) == 6
    assert fixture_set["future_image_reference_allowed"] is False
    assert all(item["possible_drift_types"] for item in fixture_set["fixtures"])
    assert fixture_set["fixtures"][4]["local_positive_behavior"]


def test_strong_female_review_rejects_superhero_shortcut() -> None:
    review = review_strong_female_regional_style(
        {
            "western_superhero_anatomy_drift": "HIGH",
            "body_grammar": "Amazon warrior with giant trapezius",
        }
    )
    assert isinstance(review, StrongFemaleRegionalStyleReview)
    assert review.result == "FAIL"
    assert DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value in review.detected_drift_types


def test_male_body_review_keeps_body_type_open_without_triangle_default() -> None:
    review = review_male_regional_body({"body_type": "slender", "body_grammar": "lean anime abstraction"})
    assert isinstance(review, MaleRegionalBodyReview)
    assert review.result == "PASS"
    failed = review_male_regional_body({"body_type": "broad", "western_heroic_triangle_drift": "HIGH"})
    assert failed.result == "FAIL"


def test_generic_fantasy_rpg_drift_allows_character_specific_reason() -> None:
    features = {
        "outfit_family": "generic fantasy robe",
        "upper_body_structure": "robe-like structure",
        "sash_presence": "sash",
        "major_trim_language": "gold trim",
        "outer_layer_family": "cloak",
    }
    assert detect_generic_fantasy_rpg_drift(features)["result"] == "HIGH"
    assert detect_generic_fantasy_rpg_drift(features, character_specific_reason="ceremonial mourning uniform")["result"] == "NONE"


def test_background_collapse_and_archetype_shortcut_are_diagnostics() -> None:
    records = [
        {"background_features": {"background_family": "abstract", "giant_circle_presence": True}}
        for _ in range(4)
    ]
    result = detect_background_presentation_collapse(records)
    assert result["diagnostic"] == DriftType.BACKGROUND_PRESENTATION_COLLAPSE.value
    shortcut = detect_archetype_shortcut_replacement("mature male", {"body_grammar": "western fantasy brute"})
    assert shortcut["detected_drift_types"] == [DriftType.ARCHETYPE_SHORTCUT_REPLACEMENT.value]


def test_lower_body_families_are_open_design_vocabularies() -> None:
    assert "barefoot" in FOOTWEAR_FAMILIES
    assert "sheer tights" in LEGWEAR_FAMILIES
    assert "thigh ring" in LEG_ACCESSORY_FAMILIES


def test_adult_unspecified_footwear_does_not_lock_black_stockings_or_heels() -> None:
    bundle = PromptCompiler().compile(character_visual_style="sensual adult character")
    assert bundle.lower_body_variables == {}
    assert bundle.lower_body_constraints == ()
    assert "black stockings" not in bundle.prompt.lower()
    assert "high heels" not in bundle.prompt.lower()


def test_male_lower_body_does_not_default_to_trousers_and_boots() -> None:
    bundle = PromptCompiler().compile(character_visual_style="mature male character")
    assert "trousers + boots" not in bundle.prompt.lower()
    assert "boots" not in bundle.prompt.lower()


def test_explicit_white_tights_and_barefoot_toeloop_are_preserved() -> None:
    lower_body = _lower_body(
        legwear_family="white opaque tights",
        footwear_family="barefoot with toe-loop footwear",
        foot_visibility="toes visible",
    )
    bundle = PromptCompiler().compile(character_visual_style="minimal premium", lower_body=lower_body)
    assert "Legwear Family: white opaque tights" in bundle.prompt
    assert "Footwear Family: barefoot with toe-loop footwear" in bundle.prompt
    assert bundle.lower_body_variables["legwear_family"] == "white opaque tights"


def test_adult_thigh_ring_is_not_filtered() -> None:
    review = review_lower_body_design(
        _lower_body(leg_accessory_family="thigh ring"),
        age_group="adult",
    )
    assert review.leg_accessory_family == "thigh ring"
    assert review.result == "PASS"


def test_fanservice_and_lower_body_coverage_are_independent() -> None:
    strong = review_lower_body_design(
        _lower_body(legwear_family="full opaque tights"),
        age_group="adult",
        fanservice_level="strong",
    )
    none = review_lower_body_design(
        _lower_body(
            exposure_strategy="full-leg exposure",
            legwear_family="none",
            footwear_family="open sandals",
        ),
        age_group="adult",
        fanservice_level="none",
    )
    assert strong.fanservice_is_independent is True
    assert none.fanservice_is_independent is True


def test_minor_can_use_ordinary_socks_or_barefoot_but_not_sexualized_leg_accessories() -> None:
    ordinary = review_lower_body_design(
        _lower_body(
            legwear_family="knee-high socks",
            footwear_family="barefoot",
            visual_reason="age-appropriate mobility",
        ),
        age_group="minor",
    )
    assert ordinary.result == "PASS"
    try:
        review_lower_body_design(
            _lower_body(leg_accessory_family="thigh ring", visual_reason="sexualized framing"),
            age_group="minor",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("minor sexualized leg accessories must be rejected")


def test_lower_body_review_marks_generic_pants_boots_as_genericness_risk() -> None:
    review = review_lower_body_design(
        _lower_body(
            legwear_family="none",
            footwear_family="ankle boots",
            visual_reason="default",
            outfit_family="generic pants",
        )
    )
    assert review.genericness_risk == "HIGH"
    assert review.result == "PASS_WITH_NOTE"


def test_lower_body_ledger_detects_pants_boots_and_remains_soft() -> None:
    records = [
        {
            "outfit_features": {"outfit_family": "trousers", "lower_body_structure": "trousers"},
            "lower_body_features": {
                "thigh_exposure": "fully covered",
                "legwear_family": "none",
                "footwear_family": "ankle boots",
            },
        }
        for _ in range(4)
    ]
    result = detect_lower_body_collapse(records)
    assert "CONSERVATIVE_COVERAGE_COLLAPSE" in result["detected_drift_types"]
    assert "FOOTWEAR_FAMILY_COLLAPSE" in result["detected_drift_types"]
    assert result["hard_gate"] is False


def test_lower_body_grounding_reports_footwear_legwear_and_anchor_misses() -> None:
    review = check_lower_body_grounding(
        Path(__file__),
        final_design={"lower_body": _lower_body(leg_accessory_family="thigh ring")},
        actual_features={"legwear_family": "none", "footwear_family": "boots", "leg_accessory_family": "none"},
    )
    assert review.result == "FAIL"
    assert "FOOTWEAR_GROUNDING_FAIL" in review.detected_drift_types
    assert "LEGWEAR_GROUNDING_FAIL" in review.detected_drift_types
    assert "LOWER_BODY_ANCHOR_MISS" in review.detected_drift_types
