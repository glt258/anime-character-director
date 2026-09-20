"""Focused v2 regression tests for Game Style projection and workflow safety."""

from __future__ import annotations

from pathlib import Path

from runtime.game_style_runtime import (
    CharacterDesignContext,
    RENDERING_SIGNATURE_SLOTS,
    evaluate_style_difference_validity,
    game_style_registry,
    project_game_style,
    resolve_game_style,
)
from runtime.interaction_runtime import CreationMode, InteractionRuntime
from runtime.regional_style_runtime import PromptCompiler


STYLE_IDS = (None, "genshin_impact", "zenless_zone_zero", "wuthering_waves", "neverness_to_everness")
FIXED_CHARACTER = "adult woman; pink shoulder-length hair; teal eyes; petite build; white and navy short jacket; black shorts; flat ankle boots; no stockings; human; stable open stance; neutral soft directional studio-like daylight"
FIXED_BACKGROUND = "simple neutral commercial character showcase background, light neutral architectural panels, subtle depth, no game-specific landmarks, no fantasy city, no futuristic skyline, no faction symbols, no environmental storytelling, background secondary"
FIXED_CONTRACT = {
    "background_specification": {
        "environment_type": FIXED_BACKGROUND,
        "lighting_context": "neutral soft directional studio-like daylight, stable key direction, moderate overall contrast",
    },
    "pose_specification": {"lower_body_pose": "stable open stance, both legs visibly separate"},
}


def _compile(style_id: str | None):
    fragment = project_game_style(resolve_game_style(style_id), CharacterDesignContext()) if style_id else None
    return PromptCompiler().compile(
        character_visual_style="fixed subject presentation",
        character_identity=FIXED_CHARACTER,
        visual_specification_contract=FIXED_CONTRACT,
        game_style_fragment=fragment,
    )


def _user_runtime(tmp_path: Path) -> tuple[InteractionRuntime, str]:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("设计一个固定角色，我自己选", CreationMode.USER_DECIDE)
    runtime.resume_session(response.session_id, "B")
    runtime.resume_session(response.session_id, "A")
    return runtime, response.session_id


def _finish_with_style(runtime: InteractionRuntime, session_id: str, style_id: str) -> None:
    runtime.resume_session(
        session_id,
        {"action": "SELECT", "payload": {"field_updates": {"game_rendering_style": {"value": style_id, "source": "human_select"}}}},
    )
    runtime.resume_session(session_id, {"action": "USE_ALL_RECOMMENDED", "payload": {}})


def test_back_game_style_invalidates_old_projection(tmp_path: Path) -> None:
    runtime, session_id = _user_runtime(tmp_path)
    _finish_with_style(runtime, session_id, "wuthering_waves")
    assert runtime.load_session(session_id).compiled_prompt["game_style_id"] == "wuthering_waves"

    response = runtime.resume_session(session_id, {"action": "BACK", "payload": {"target": "VISUAL_PREFERENCE_GATE"}})
    saved = runtime.load_session(session_id)
    assert response.gate and saved.compiled_prompt is None
    assert any(item.get("event") == "game_style_projection_invalidated" for item in saved.audit_log)


def test_back_wuwa_to_nte_has_no_stale_rules(tmp_path: Path) -> None:
    runtime, session_id = _user_runtime(tmp_path)
    runtime.resume_session(
        session_id,
        {
            "action": "SELECT",
            "payload": {
                "field_updates": {
                    "hair_color": {"value": "pink", "source": "human_custom"},
                    "body_build": {"value": "petite", "source": "human_custom"},
                    "outfit_direction": {"value": "white and navy short jacket", "source": "human_custom"},
                    "footwear_family": {"value": "flat ankle boots", "source": "human_custom"},
                    "background_direction": {"value": FIXED_BACKGROUND, "source": "human_custom"},
                }
            },
        },
    )
    _finish_with_style(runtime, session_id, "wuthering_waves")
    runtime.resume_session(session_id, {"action": "BACK", "payload": {"target": "VISUAL_PREFERENCE_GATE"}})
    _finish_with_style(runtime, session_id, "neverness_to_everness")
    saved = runtime.load_session(session_id)
    assert saved.status == "GENERATION_READY"
    assert saved.compiled_prompt["game_style_id"] == "neverness_to_everness"
    assert "wuthering_waves" not in str(saved.compiled_prompt)
    assert "Allow deliberate alternating contour treatment" not in saved.compiled_prompt["prompt"]
    assert saved.final_design["visual_preferences"]["hair_color"] == "pink"


def test_checkpoint_game_style_replacement(tmp_path: Path) -> None:
    runtime, session_id = _user_runtime(tmp_path)
    _finish_with_style(runtime, session_id, "wuthering_waves")
    runtime.resume_session(session_id, {"action": "BACK", "payload": {"target": "VISUAL_PREFERENCE_GATE"}})
    _finish_with_style(runtime, session_id, "neverness_to_everness")
    reloaded = InteractionRuntime(tmp_path).load_session(session_id)
    assert reloaded.visual_preference_sheet["game_style_id"] == "neverness_to_everness"
    assert reloaded.compiled_prompt["game_style_debug_trace"]["game_specialization"] == "neverness_to_everness"


def test_unsupported_hsr_falls_back_global(tmp_path: Path) -> None:
    saved = InteractionRuntime(tmp_path).load_session(
        InteractionRuntime(tmp_path).create_session("设计一个成年女性角色，按崩坏：星穹铁道画风").session_id
    )
    assert saved.status == "GENERATION_READY"
    assert saved.compiled_prompt["game_style_id"] is None
    assert saved.compiled_prompt["rendering_foundation"] == "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"
    assert saved.compiled_prompt["game_style_requested"] == "崩坏：星穹铁道"
    assert saved.compiled_prompt["game_style_fallback_reason"] == "UNSUPPORTED_GAME_STYLE"
    assert saved.compiled_prompt["explicit_constraint_coverage"]["status"] == "PASS"


def test_unsupported_style_not_mapped_to_genshin(tmp_path: Path) -> None:
    saved = InteractionRuntime(tmp_path).load_session(
        InteractionRuntime(tmp_path).create_session("按崩坏：星穹铁道画风设计角色").session_id
    )
    assert saved.compiled_prompt["game_style_id"] is None
    assert saved.compiled_prompt["game_style_debug_trace"]["game_specialization"] is None


def test_fallback_keeps_requested_style_metadata(tmp_path: Path) -> None:
    saved = InteractionRuntime(tmp_path).load_session(
        InteractionRuntime(tmp_path).create_session("使用崩坏：星穹铁道渲染").session_id
    )
    assert saved.final_design["game_style_request"] == "崩坏：星穹铁道"
    assert saved.final_design["game_style_fallback_reason"] == "UNSUPPORTED_GAME_STYLE"
    assert saved.final_design["game_style_audit"]["resolved_style_id"] is None


def test_runtime_signature_slots() -> None:
    for profile in game_style_registry().profiles.values():
        assert set(RENDERING_SIGNATURE_SLOTS[:12]).issubset({item.slot for item in profile.rendering_signature})
        assert any(item.status == "no_reliable_discriminator" for item in profile.rendering_signature)


def test_character_rendering_rule_minimum() -> None:
    assert all(5 <= len(profile.core_rendering_instructions) <= 8 for profile in game_style_registry().profiles.values())
    assert all(sum(1 for item in profile.core_rendering_instructions if item["slot"] in {"LINE_CONTOUR", "INTERNAL_EDGE", "PRIMARY_SHADOW", "SECONDARY_GRADIENT", "DETAIL_FREQUENCY"}) >= 4 for profile in game_style_registry().profiles.values())


def test_background_not_primary_style_discriminator() -> None:
    for style_id in STYLE_IDS[1:]:
        fragment = project_game_style(resolve_game_style(style_id), CharacterDesignContext())
        assert all("background" not in item.casefold() and "environment" not in item.casefold() for item in fragment.instructions)


def test_projection_v2_budget() -> None:
    for profile in game_style_registry().profiles.values():
        fragment = project_game_style(profile, CharacterDesignContext())
        assert 5 <= len(fragment.core_instructions) <= 8
        assert len(fragment.supporting_instructions) <= 2
        assert len(fragment.instructions) <= 10


def test_projection_rules_are_how_only() -> None:
    forbidden = ("hair", "body", "clothing", "footwear", "pose", "background", "palette", "accessory", "game name")
    for style_id in STYLE_IDS[1:]:
        fragment = project_game_style(resolve_game_style(style_id), CharacterDesignContext())
        assert not any(term in text.casefold() for text in fragment.instructions for term in forbidden)
        assert all("relative to global" in text.casefold() for text in fragment.contrastive_instructions)


def test_game_style_rule_strength_schema() -> None:
    for profile in game_style_registry().profiles.values():
        assert all(item["strength"] in {"strong", "medium", "subtle"} for item in profile.core_rendering_instructions)


def test_user_conflict_drops_style_rule() -> None:
    fragment = project_game_style(resolve_game_style("ZZZ"), CharacterDesignContext(explicit_rendering_preferences={"shading_strategy": "soft_low_contrast"}))
    assert fragment.dropped_rules
    assert any(item["status"] == "dropped" and item["conflict_reason"] for item in fragment.dropped_rules)
    assert "rendering_shading_soft_dominant" in fragment.overridden_claim_ids


def test_user_conflict_adapts_style_rule() -> None:
    fragment = project_game_style(resolve_game_style("ZZZ"), CharacterDesignContext(explicit_rendering_preferences={"edge_treatment": {"mode": "adapt", "value": "soft with major anchors"}}))
    assert fragment.adapted_rules
    assert not fragment.dropped_rules
    assert any(item["status"] == "adapted" for item in fragment.adapted_rules)


def test_user_rendering_override_preserved() -> None:
    preferences = {"edge_treatment": "hard"}
    fragment = project_game_style(resolve_game_style("ZZZ"), CharacterDesignContext(explicit_rendering_preferences=preferences))
    assert preferences == {"edge_treatment": "hard"}
    assert "rendering_edge_treatment_soft" not in fragment.source_claim_ids


def test_global_contract_does_not_duplicate_game_delta() -> None:
    bundle = _compile("genshin_impact")
    assert bundle.prompt.count("CONTEMPORARY_COMMERCIAL_GACHA_ANIME") == 1
    assert not set(bundle.game_style_source_claim_ids).intersection(game_style_registry().profiles["genshin_impact"].excluded_global_baseline_claim_ids)


def test_game_specific_projection_semantic_distinction() -> None:
    prompts = [_compile(style_id).game_style_debug_trace["projected_rules"] for style_id in STYLE_IDS[1:]]
    assert len({tuple(item) for item in prompts}) == 4
    assert any("continuous gradients" in item for rules in prompts for item in rules)
    assert any("clean readable shadow" in item for rules in prompts for item in rules)


def test_same_character_block_all_five_modes() -> None:
    prompts = [_compile(style_id).prompt for style_id in STYLE_IDS]
    assert all(FIXED_CHARACTER in prompt for prompt in prompts)


def test_same_background_all_five_modes() -> None:
    prompts = [_compile(style_id).prompt for style_id in STYLE_IDS]
    assert all(FIXED_BACKGROUND in prompt for prompt in prompts)


def test_same_pose_all_five_modes() -> None:
    prompts = [_compile(style_id).prompt for style_id in STYLE_IDS]
    assert all("stable open stance, both legs visibly separate" in prompt for prompt in prompts)


def test_same_lighting_intent_all_five_modes() -> None:
    prompts = [_compile(style_id).prompt for style_id in STYLE_IDS]
    lighting = "neutral soft directional studio-like daylight, stable key direction, moderate overall contrast"
    assert all(lighting in prompt for prompt in prompts)


def _assert_no_character_drift(field: str, forbidden: str) -> None:
    prompts = [_compile(style_id).prompt for style_id in STYLE_IDS[1:]]
    assert all(FIXED_CHARACTER in prompt for prompt in prompts)
    assert all(forbidden.casefold() not in prompt.casefold() for prompt in prompts)


def test_no_body_style_drift() -> None:
    _assert_no_character_drift("body", "different body")


def test_no_clothing_drift() -> None:
    _assert_no_character_drift("clothing", "different clothing")


def test_no_footwear_drift() -> None:
    _assert_no_character_drift("footwear", "stilettos")


def test_no_hair_drift() -> None:
    _assert_no_character_drift("hair", "different hair")


def test_no_eye_drift() -> None:
    _assert_no_character_drift("eyes", "different eye color")


def test_no_sexiness_drift() -> None:
    _assert_no_character_drift("sexiness", "more sexualized")


def test_no_nonhuman_drift() -> None:
    _assert_no_character_drift("nonhuman", "horns")


def test_style_difference_validity_gate() -> None:
    assert evaluate_style_difference_validity("PASS", "CLEAR_CHARACTER_RENDERING_DIFFERENCE")["status"] == "PASS"
    assert evaluate_style_difference_validity("PASS", "SUBTLE_DIFFERENCE")["status"] == "FAIL"
