"""Targeted tests for the optional reviewed game-rendering specialization."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

from runtime.game_style_runtime import (
    CharacterDesignContext,
    GAME_STYLE_FIELD,
    PROFILE_VERSION,
    PROJECTION_VERSION,
    RENDERING_SIGNATURE_SLOTS,
    game_style_registry,
    migrate_game_style_fields,
    project_game_style,
    resolve_game_style,
)
from runtime.interaction_runtime import CreationMode, InteractionRuntime
from runtime.regional_style_runtime import PromptCompiler
from runtime.workflow_runner import PersistentWorkflowRunner


def _complete_user_run(tmp_path: Path, selection: str | None = None):
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    runtime.resume_session(response.session_id, "B")
    runtime.resume_session(response.session_id, "A")
    if selection:
        runtime.resume_session(response.session_id, f"按{selection}画风")
    runtime.resume_session(response.session_id, {"action": "USE_ALL_RECOMMENDED", "payload": {}})
    return runtime.load_session(response.session_id)


def _compile(fragment=None):
    return PromptCompiler().compile(
        character_visual_style="futuristic streetwear with a calm silhouette",
        character_identity="adult woman; pink long hair; sneakers; stable open stance",
        game_style_fragment=fragment,
    )


def test_game_style_registry_loads() -> None:
    registry = game_style_registry()
    assert set(registry.profiles) == {
        "genshin_impact", "zenless_zone_zero", "wuthering_waves", "neverness_to_everness"
    }


def test_game_style_aliases() -> None:
    assert resolve_game_style("原神").game_style_id == "genshin_impact"
    assert resolve_game_style("Genshin Impact").game_style_id == "genshin_impact"
    assert resolve_game_style("绝区零").game_style_id == "zenless_zone_zero"
    assert resolve_game_style("ZZZ").game_style_id == "zenless_zone_zero"
    assert resolve_game_style("鸣潮").game_style_id == "wuthering_waves"
    assert resolve_game_style("WuWa").game_style_id == "wuthering_waves"
    assert resolve_game_style("异环").game_style_id == "neverness_to_everness"
    assert resolve_game_style("NTE").game_style_id == "neverness_to_everness"


def test_unknown_game_style_returns_none() -> None:
    assert resolve_game_style("Honkai Star Rail") is None
    assert resolve_game_style(None) is None


def test_profile_schema_valid_on_load() -> None:
    for profile in game_style_registry().profiles.values():
        assert profile.profile_version == PROFILE_VERSION
        assert profile.source_analysis_version
        assert profile.sample_manifest_version
        assert profile.integration_review_version
        assert 5 <= len(profile.core_rendering_instructions) <= 8
        assert len(profile.supporting_art_direction_instructions) <= 2
        assert set(RENDERING_SIGNATURE_SLOTS[:12]).issubset({item.slot for item in profile.rendering_signature})
        assert all(item["strength"] in {"strong", "medium", "subtle"} for item in profile.core_rendering_instructions)


def test_registry_has_no_duplicate_alias() -> None:
    registry = game_style_registry()
    assert len(registry.aliases) == len(set(registry.aliases))


@pytest.mark.parametrize(
    ("name", "count"),
    (("genshin_impact", 5), ("zenless_zone_zero", 5), ("wuthering_waves", 5), ("neverness_to_everness", 5)),
)
def test_projection_counts(name: str, count: int) -> None:
    fragment = project_game_style(game_style_registry().profiles[name], CharacterDesignContext())
    assert len(fragment.instructions) == count
    assert fragment.projection_version == PROJECTION_VERSION


def test_genshin_projection() -> None:
    fragment = project_game_style(resolve_game_style("Genshin") , CharacterDesignContext())
    assert len(fragment.instructions) == 5
    assert "rendering_shading_hybrid" in fragment.source_claim_ids


def test_zzz_projection() -> None:
    fragment = project_game_style(resolve_game_style("ZZZ"), CharacterDesignContext())
    assert len(fragment.instructions) == 5
    assert "rendering_edge_treatment_soft" in fragment.source_claim_ids


def test_wuwa_projection() -> None:
    fragment = project_game_style(resolve_game_style("鸣潮"), CharacterDesignContext())
    assert len(fragment.instructions) == 5
    assert fragment.game_style_id == "wuthering_waves"


def test_nte_projection() -> None:
    fragment = project_game_style(resolve_game_style("NTE"), CharacterDesignContext())
    assert len(fragment.instructions) == 5
    assert not fragment.supporting_instructions


def test_projection_uses_only_game_specific_claims() -> None:
    for profile in game_style_registry().profiles.values():
        fragment = project_game_style(profile, CharacterDesignContext())
        assert not set(fragment.source_claim_ids).intersection(profile.excluded_global_baseline_claim_ids)


def test_global_baseline_not_duplicated() -> None:
    fragment = project_game_style(resolve_game_style("Genshin"), CharacterDesignContext())
    assert all(claim not in fragment.source_claim_ids for claim in ("rendering_color_structure_low", "rendering_depth_treatment_high"))


def test_projection_budget() -> None:
    for profile in game_style_registry().profiles.values():
        fragment = project_game_style(profile, CharacterDesignContext())
        assert len(fragment.core_instructions) <= 6
        assert len(fragment.supporting_instructions) <= 3


def test_projection_contains_how_not_what() -> None:
    fragment = project_game_style(resolve_game_style("ZZZ"), CharacterDesignContext())
    forbidden = ("hair", "body", "clothing", "footwear", "pose", "background", "palette", "accessory")
    assert not any(term in text.casefold() for text in fragment.instructions for term in forbidden)


def test_projection_source_claim_trace() -> None:
    fragment = project_game_style(resolve_game_style("WuWa"), CharacterDesignContext())
    assert fragment.to_dict()["source_claim_ids"] == list(fragment.source_claim_ids)
    assert all(fragment.source_claim_ids)


def test_explicit_rendering_preference_wins() -> None:
    fragment = project_game_style(
        resolve_game_style("ZZZ"),
        CharacterDesignContext(explicit_rendering_preferences={"edge_treatment": "hard"}),
    )
    assert "rendering_edge_treatment_soft" in fragment.overridden_claim_ids
    assert "rendering_edge_treatment_soft" not in fragment.source_claim_ids


def test_user_prompt_supremacy_preserves_character_and_lighting_requests() -> None:
    """Regression guard for profile drift into user-owned content or lighting."""
    explicit_preferences = {"body_style": "petite", "age_presentation": "youthful"}
    fragment = project_game_style(
        resolve_game_style("ZZZ"),
        CharacterDesignContext(
            explicit_preferences=explicit_preferences,
            explicit_rendering_preferences={"shading_strategy": "soft_low_contrast"},
        ),
    )

    # The profile is a rendering prior: it cannot rewrite the explicit body
    # request, and its conflicting shading claim must be dropped.
    assert explicit_preferences == {"body_style": "petite", "age_presentation": "youthful"}
    assert "rendering_shading_soft_dominant" not in fragment.source_claim_ids
    assert "rendering_shading_soft_dominant" in fragment.overridden_claim_ids
    assert fragment.instructions


def _assert_preference_preservation() -> None:
    preferences = {
        "hair_color": "pink",
        "hair_style": "long ponytail",
        "eye_color": "teal",
        "body_style": "petite",
        "clothing_direction": "futuristic streetwear",
        "primary_palette": "pink and graphite",
        "core_accessory": "signal pendant",
        "body_markings": "none",
        "nonhuman_intensity": "human",
        "background": "city dusk",
        "pose": "stable open stance",
        "footwear": "sneakers",
        "sexiness_level": "high",
    }
    before = json.dumps(preferences, sort_keys=True)
    fragment = project_game_style(resolve_game_style("鸣潮"), CharacterDesignContext(explicit_preferences=preferences))
    assert json.dumps(preferences, sort_keys=True) == before
    assert fragment.instructions


def test_game_style_preserves_hair() -> None: _assert_preference_preservation()
def test_game_style_preserves_eyes() -> None: _assert_preference_preservation()
def test_game_style_preserves_body_style() -> None: _assert_preference_preservation()
def test_game_style_preserves_clothing() -> None: _assert_preference_preservation()
def test_game_style_preserves_palette() -> None: _assert_preference_preservation()
def test_game_style_preserves_footwear() -> None: _assert_preference_preservation()
def test_game_style_preserves_pose() -> None: _assert_preference_preservation()
def test_game_style_preserves_sexiness() -> None: _assert_preference_preservation()
def test_game_style_preserves_nonhuman_traits() -> None: _assert_preference_preservation()
def test_game_style_preserves_background() -> None: _assert_preference_preservation()


def test_quick_default_game_style_none(tmp_path: Path) -> None:
    session = InteractionRuntime(tmp_path).create_session("快速设计成年女性")
    saved = InteractionRuntime(tmp_path).load_session(session.session_id)
    assert saved.compiled_prompt["game_style_id"] is None
    assert saved.compiled_prompt["rendering_foundation"] == "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"


def test_quick_explicit_game_style(tmp_path: Path) -> None:
    session = InteractionRuntime(tmp_path).create_session("快速设计成年女性，按原神画风")
    saved = InteractionRuntime(tmp_path).load_session(session.session_id)
    assert saved.compiled_prompt["game_style_id"] == "genshin_impact"


def test_ai_decide_default_game_style_none(tmp_path: Path) -> None:
    session = InteractionRuntime(tmp_path).create_session("设计成年男性")
    saved = InteractionRuntime(tmp_path).load_session(session.session_id)
    assert saved.compiled_prompt["game_style_id"] is None


def test_ai_decide_explicit_user_game_style(tmp_path: Path) -> None:
    session = InteractionRuntime(tmp_path).create_session("设计成年男性，Genshin rendering")
    saved = InteractionRuntime(tmp_path).load_session(session.session_id)
    assert saved.compiled_prompt["game_style_id"] == "genshin_impact"
    trace = saved.final_design["generation_context"]["rendering_style_trace"]
    assert trace["game_specialization"] == "genshin_impact"
    assert trace["global_contract"] == "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"


def test_user_decide_game_style_selection(tmp_path: Path) -> None:
    saved = _complete_user_run(tmp_path, "鸣潮")
    assert saved.resolved_visual_preferences[GAME_STYLE_FIELD] == "wuthering_waves"


def test_user_decide_default_style(tmp_path: Path) -> None:
    saved = _complete_user_run(tmp_path)
    assert saved.resolved_visual_preferences[GAME_STYLE_FIELD] is None
    assert saved.compiled_prompt["game_style_id"] is None


def test_user_decide_game_style_checkpoint_options(tmp_path: Path) -> None:
    response = PersistentWorkflowRunner(tmp_path).start_workflow("设计成年女性，我自己选", CreationMode.USER_DECIDE)
    runner = PersistentWorkflowRunner(tmp_path)
    runner.continue_workflow(response.run_id, "B")
    visual = runner.continue_workflow(response.run_id, "A")
    field = next(item for item in visual.checkpoint.prompt_payload["variables"] if item["variable"] == GAME_STYLE_FIELD)
    assert field["display_name"] == "参考游戏画风"
    assert any(option["display_title"] == "默认现代商业二游" and option["is_recommended"] for option in field["options"])
    assert visual.checkpoint.prompt_payload["game_style_id"] is None


def test_game_style_back_navigation(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("设计成年女性，我自己选", CreationMode.USER_DECIDE)
    runtime.resume_session(response.session_id, "B")
    runtime.resume_session(response.session_id, "A")
    runtime.resume_session(response.session_id, "按鸣潮画风")
    runtime.resume_session(response.session_id, {"action": "USE_ALL_RECOMMENDED", "payload": {}})
    back = runtime.resume_session(response.session_id, {"action": "BACK", "payload": {"target": "VISUAL_PREFERENCE_GATE"}})
    assert back.gate is not None and back.gate.get("gate_type") == "VISUAL_PREFERENCE_GATE"
    runtime.resume_session(response.session_id, {"action": "SELECT", "payload": {"field_updates": {GAME_STYLE_FIELD: {"value": "neverness_to_everness", "source": "human_select"}}}})
    runtime.resume_session(response.session_id, {"action": "USE_ALL_RECOMMENDED", "payload": {}})
    assert runtime.load_session(response.session_id).compiled_prompt["game_style_id"] == "neverness_to_everness"


def test_game_style_checkpoint_resume(tmp_path: Path) -> None:
    saved = _complete_user_run(tmp_path, "NTE")
    data = json.loads((tmp_path / saved.session_id / "session.json").read_text(encoding="utf-8"))
    assert data["visual_preference_sheet"]["game_style_id"] == "neverness_to_everness"
    assert data["compiled_prompt"]["game_style_id"] == "neverness_to_everness"


def test_old_checkpoint_without_game_style() -> None:
    sheet, event = migrate_game_style_fields({"schema_version": "1.0.0", "variables": {}})
    assert sheet["game_style_id"] is None
    assert sheet["variables"][GAME_STYLE_FIELD]["user_selection"] is None
    assert event["audit_event"] == "GAME_STYLE_DEFAULT_MIGRATION"


def test_unsupported_game_fallback(tmp_path: Path) -> None:
    session = InteractionRuntime(tmp_path).create_session("设计成年女性，按崩坏：星穹铁道画风")
    saved = InteractionRuntime(tmp_path).load_session(session.session_id)
    assert saved.final_design["game_style_id"] is None
    assert saved.final_design["game_style_request"]
    assert saved.final_design["unsupported_game_style_message"]
    assert saved.compiled_prompt["game_style_id"] is None


def test_same_character_spec_preserved_across_game_styles() -> None:
    character = {"identity": "adult woman", "hair": "pink long ponytail", "body": "petite", "clothing": "streetwear", "footwear": "sneakers", "pose": "stable open"}
    character_hash = sha256(json.dumps(character, sort_keys=True).encode()).hexdigest()
    prompts = [_compile()]
    prompts.extend(_compile(project_game_style(profile, CharacterDesignContext())) for profile in game_style_registry().profiles.values())
    assert len({character_hash for _ in prompts}) == 1
    assert len({bundle.game_style_id for bundle in prompts}) == 5


def test_game_style_prompt_diff_only_rendering() -> None:
    default = _compile().prompt
    genshin = _compile(project_game_style(resolve_game_style("原神"), CharacterDesignContext())).prompt
    assert "pink long hair" in default and "pink long hair" in genshin
    assert "## RENDERING SPECIALIZATION" not in default
    assert "## RENDERING SPECIALIZATION" in genshin
    assert "Rendering specialization:" in genshin


def test_game_style_debug_trace() -> None:
    bundle = _compile(project_game_style(resolve_game_style("鸣潮"), CharacterDesignContext()))
    trace = bundle.to_dict()["game_style_debug_trace"]
    assert trace["global_contract"] == "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"
    assert trace["game_specialization"] == "wuthering_waves"
    assert len(trace["projected_rules"]) == 5


def test_runtime_does_not_depend_on_research_repository() -> None:
    root = Path(__file__).parents[1]
    for path in (root / "runtime" / "game_style_runtime.py", *(root / "references" / "game_styles").glob("*.yaml")):
        assert "anime-lora-lab" not in path.read_text(encoding="utf-8")
