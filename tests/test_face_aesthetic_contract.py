from __future__ import annotations

from runtime.interaction_runtime import _visual_sheet
from runtime.natural_language_interaction import ExplicitConstraintExtractor
from runtime.natural_language_interaction import NaturalLanguageInteractionParser
from runtime.regional_style_runtime import (
    DEFAULT_FACE_AESTHETIC_PROFILE,
    DEFAULT_STYLE_INHERITANCE_POLICY,
    PromptCompiler,
    build_visual_specification_contract,
    migrate_face_aesthetic_fields,
)
from runtime.visual_adherence_critic import VisualAdherenceCritic
from runtime.visual_context_firewall import VisualContextFirewall
from runtime.visual_repair import build_repair_plan, compile_repair_prompt


def _firewall() -> dict[str, object]:
    return VisualContextFirewall().to_dict()


def test_default_face_contract_is_east_asian_and_compiled() -> None:
    contract = build_visual_specification_contract(character_visual_style="clean-line anime")
    bundle = PromptCompiler().compile(
        character_visual_style="clean-line anime",
        visual_specification_contract=contract,
        visual_context_firewall=_firewall(),
    )

    assert contract.face_aesthetic_profile == DEFAULT_FACE_AESTHETIC_PROFILE
    assert contract.face_aesthetic_is_default is True
    assert contract.style_inheritance_policy == DEFAULT_STYLE_INHERITANCE_POLICY
    assert "## FACE AESTHETIC CONTRACT" in bundle.prompt
    assert "East Asian commercial gacha anime facial design language" in bundle.prompt
    assert "semi-realistic western portrait language" in bundle.prompt


def test_explicit_western_face_is_current_run_only() -> None:
    constraints = ExplicitConstraintExtractor().extract("use a western-inspired face")
    assert constraints["face_aesthetic_profile"] == "WESTERN_INSPIRED_GACHA_FACE"
    assert constraints["face_aesthetic_source"] == "human_explicit"
    contract = build_visual_specification_contract(
        visual_preferences=constraints,
        explicit_user_fields=constraints["explicit_user_fields"],
    )
    prompt = PromptCompiler().compile(
        character_visual_style="clean-line anime",
        visual_specification_contract=contract,
        visual_context_firewall=_firewall(),
    ).prompt

    assert "WESTERN_INSPIRED_GACHA_FACE" in prompt
    assert "contemporary commercial gacha anime" in prompt
    assert "western realistic illustration" in prompt


def test_visual_gate_parser_accepts_explicit_face_profile() -> None:
    intent = NaturalLanguageInteractionParser().parse(
        "欧美脸型",
        {"gate_type": "VISUAL_PREFERENCE_GATE", "visual_variables": {"face_aesthetic_profile": {}}},
    )

    assert intent.field_updates["face_aesthetic_profile"]["value"] == "WESTERN_INSPIRED_GACHA_FACE"


def test_previous_western_run_does_not_change_fresh_default() -> None:
    old = ExplicitConstraintExtractor().extract("western-inspired face")
    fresh = ExplicitConstraintExtractor().extract("画一个魅魔角色，有魅魔角，体现魅力")
    old_sheet = _visual_sheet(old, original_input=old["raw"])
    fresh_sheet = _visual_sheet(fresh, original_input=fresh["raw"])

    assert old_sheet["face_aesthetic_profile"] == "WESTERN_INSPIRED_GACHA_FACE"
    assert fresh_sheet["face_aesthetic_profile"] == DEFAULT_FACE_AESTHETIC_PROFILE
    assert fresh_sheet["face_aesthetic_source"] == "system_default"
    assert fresh_sheet["style_inheritance_policy"] == DEFAULT_STYLE_INHERITANCE_POLICY


def test_firewall_blocks_historical_face_data_but_exposes_anti_repetition_path() -> None:
    firewall = VisualContextFirewall()
    history = {
        "face_aesthetic_profile": "WESTERN_INSPIRED_GACHA_FACE",
        "regional_face_language": "western face structure",
        "final_design": {"face_aesthetic_profile": "WESTERN_INSPIRED_GACHA_FACE"},
    }
    current = firewall.generation_context(current_user_request="new role", historical_visual_context=history)
    anti_repetition = firewall.anti_repetition_context(history)

    assert "explicitly_inherited_visuals" not in current
    assert "previous_run_face_aesthetic" in current["blocked_context_sources"]
    assert anti_repetition["generation_allowed"] is False
    assert anti_repetition["history"] == history


def test_explicit_inheritance_can_name_only_face_profile() -> None:
    constraints = ExplicitConstraintExtractor().extract("沿用上一版的欧美脸型，其他重新设计")
    firewall = VisualContextFirewall.from_request(constraints["raw"], constraints)

    assert firewall.inherit_previous_visuals is True
    assert any(item.startswith("face_aesthetic_profile=") for item in firewall.allowed_visual_inheritance)


def test_critic_and_repair_preserve_face_contract(tmp_path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"fixture")
    contract = build_visual_specification_contract(character_visual_style="clean-line anime")
    prompt = PromptCompiler().compile(
        character_visual_style="clean-line anime",
        visual_specification_contract=contract,
        visual_context_firewall=_firewall(),
    ).prompt
    review = VisualAdherenceCritic().review(
        image,
        manifest=contract.to_dict(),
        observations={
            "face_aesthetic_profile": {
                "observed": "WESTERN_INSPIRED_GACHA_FACE",
                "result": "FAIL",
            }
        },
        prompt_bundle_metadata={"prompt": prompt},
        prompt_hash="prompt-hash",
        generation_id="generation-1",
    )
    plan = build_repair_plan(
        review,
        manifest=contract.to_dict(),
        visual_specification_contract=contract.to_dict(),
        generation_artifact={
            "generation_id": "generation-1",
            "image_hash": review.actual_image_hash,
            "prompt_hash": "prompt-hash",
        },
    )
    repair_prompt = compile_repair_prompt(
        {
            "prompt": prompt,
            "visual_context_firewall_applied": True,
            "visual_specification_contract": contract.to_dict(),
        },
        plan,
    )

    assert any(item["field"] == "face_aesthetic_profile" for item in review.repair_targets)
    assert plan.face_aesthetic_contract["face_aesthetic_profile"] == DEFAULT_FACE_AESTHETIC_PROFILE
    assert "FACE AESTHETIC CONTRACT" in repair_prompt.prompt
    assert "Preserve costume, silhouette, pose, props, palette, and background" in repair_prompt.prompt


def test_old_artifact_migrates_face_contract_without_mutation() -> None:
    old = {"schema_version": "1.0.0", "regional_visual_language": "EAST_ASIAN_CONTEMPORARY_GACHA"}
    migrated, event = migrate_face_aesthetic_fields(old)

    assert old == {"schema_version": "1.0.0", "regional_visual_language": "EAST_ASIAN_CONTEMPORARY_GACHA"}
    assert migrated["face_aesthetic_profile"] == DEFAULT_FACE_AESTHETIC_PROFILE
    assert migrated["face_aesthetic_source"] == "migrated_default"
    assert migrated["face_aesthetic_contract"]["style_inheritance_policy"] == DEFAULT_STYLE_INHERITANCE_POLICY
    assert event and event["audit_event"] == "FACE_AESTHETIC_DEFAULT_MIGRATION"
