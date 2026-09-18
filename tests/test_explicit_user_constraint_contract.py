from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.interaction_candidates import CandidateGenerator  # noqa: E402
from runtime.interaction_runtime import (  # noqa: E402
    CreationMode,
    ExplicitUserConstraintConflict,
    InteractionRuntime,
    _apply_visual_value,
    _visual_sheet,
)
from runtime.natural_language_interaction import ExplicitConstraintExtractor  # noqa: E402
from runtime.regional_style_runtime import (  # noqa: E402
    ExplicitConstraintCoverageGate,
    PromptCompiler,
    build_visual_specification_contract,
)


RUN_B = "快速模式画一个女仆角色，设定是狐狸但是是人类形态，要求通过着装等体现人物魅力，条纹丝袜蓝白然后鞋子是露趾的高跟（但是脚趾被丝袜包裹），有狐耳朵但是白色的。大胸，有扇子。整体色调白色为主，蓝色为辅助。要体现人物魅力"
RUN_A = "AI决策模式画一个女仆长角色，设定是幽灵但是是人类的样貌和全身，要求有两个幽灵娃娃在身边，穿着是女仆装，大胸。可以参考欧美脸型的画法但是整体风格是商业二游的风格"


def _extract(text: str) -> dict:
    return ExplicitConstraintExtractor().extract(text)


def _bundle(constraints: dict, *, dna: dict | None = None):
    records = constraints.get("explicit_constraint_records", {})
    contract = build_visual_specification_contract(
        design_dna=dna or {},
        visual_preferences=constraints,
        explicit_user_fields=constraints.get("explicit_user_fields", ()),
        explicit_constraints=records,
        character_visual_style="clean-line contemporary commercial gacha anime",
    )
    return PromptCompiler().compile(
        character_visual_style="clean-line contemporary commercial gacha anime",
        character_identity="female maid character",
        pose_description="OPEN_PARALLEL_STANCE frontal standee stance with both legs clearly separated",
        pose_family="OPEN_PARALLEL_STANCE",
        visual_specification_contract=contract,
        explicit_constraints=records,
    )


def test_run_b_extracts_required_identity_fields() -> None:
    constraints = _extract(RUN_B)
    assert constraints["role_identity"] == "maid"
    assert constraints["gender_presentation"] == "female"
    assert constraints["costume_identity"] == "maid_outfit"
    assert constraints["human_form_requirement"] == "human_form"
    assert constraints["nonhuman_features"] == "white_fox_ears"


def test_run_b_extracts_lower_body_and_palette_fields() -> None:
    constraints = _extract(RUN_B)
    assert constraints["body_proportion"] == "large_bust"
    assert constraints["props"] == ["fan"]
    assert constraints["legwear"] == "blue_white_striped_stockings"
    assert constraints["footwear"] == "open_toe_high_heels"
    assert constraints["footwear_detail"] == "toes_covered_by_stockings"
    assert constraints["palette_primary"] == "white"
    assert constraints["palette_secondary"] == "blue"


def test_run_b_records_human_hard_provenance() -> None:
    records = _extract(RUN_B)["explicit_constraint_records"]
    for field in ("role_identity", "legwear", "footwear", "palette_primary"):
        assert records[field]["source"] == "human_explicit"
        assert records[field]["priority"] == "HARD"
        assert records[field]["locked"] is True
        assert records[field]["raw_evidence"]


def test_run_a_extracts_head_maid_ghost_human_form_and_dolls() -> None:
    constraints = _extract(RUN_A)
    assert constraints["role_identity"] == "head_maid"
    assert constraints["costume_identity"] == "maid_outfit"
    assert constraints["supernatural_state"] == "ghost"
    assert constraints["human_form_requirement"] == "human_form"
    assert constraints["props"] == ["ghost_dolls"]
    assert constraints["quantity_constraints"] == {"ghost_dolls": 2}


def test_run_a_extracts_bust_face_reference_and_style_contract() -> None:
    constraints = _extract(RUN_A)
    assert constraints["body_proportion"] == "large_bust"
    assert constraints["face_aesthetic_profile"] == "WESTERN_INSPIRED_GACHA_FACE"
    assert constraints["style_contract"] == "contemporary commercial gacha anime"


def test_candidate_dna_applies_all_run_b_hard_fields() -> None:
    constraints = _extract(RUN_B)
    candidates = CandidateGenerator().generate(
        gate_id="CHARACTER_DIRECTION_GATE",
        original_input=RUN_B,
        explicit_constraints=constraints,
        seed=11,
    )
    assert candidates
    for candidate in candidates:
        dna = candidate["design_dna"]
        assert dna["costume_topology"] == "maid-based"
        assert dna["legwear_strategy"] == "blue_white_striped_stockings"
        assert dna["footwear_category"] == "open_toe_high_heels"
        assert dna["palette_family"] == "white dominant / blue secondary"
        assert dna["upper_body_structure"] == "large-bust feminine structure"


def test_fox_ears_do_not_auto_add_horns_tail_or_wings() -> None:
    constraints = _extract(RUN_B)
    candidate = CandidateGenerator().generate(
        gate_id="CHARACTER_DIRECTION_GATE", original_input=RUN_B, explicit_constraints=constraints
    )[0]
    dna = candidate["design_dna"]
    assert dna["nonhuman_features"] == "white_fox_ears"
    assert dna["horn_topology"] == "none"
    assert dna["tail_design"] == "none"
    assert dna["wing_strategy"] == "none"


def test_explicit_horns_are_opt_in_and_preserved() -> None:
    constraints = _extract("画一个魅魔角色，有魅魔角")
    candidate = CandidateGenerator().generate(
        gate_id="CHARACTER_DIRECTION_GATE", original_input="画一个魅魔角色，有魅魔角", explicit_constraints=constraints
    )[0]
    assert candidate["design_dna"]["horn_topology"] == "demon horns"


def test_candidate_records_constraint_locks() -> None:
    candidate = CandidateGenerator().generate(
        gate_id="CHARACTER_DIRECTION_GATE", original_input=RUN_B, explicit_constraints=_extract(RUN_B)
    )[0]
    assert candidate["explicit_constraint_locks"]["footwear"]["priority"] == "HARD"


def test_visual_sheet_locks_explicit_fields_before_quick_fill() -> None:
    constraints = _extract(RUN_B)
    sheet = _visual_sheet(constraints, original_input=RUN_B)
    for field in ("role_identity", "costume_identity", "legwear", "footwear", "palette_primary"):
        assert sheet["variables"][field]["selection_source"] == "explicit_user"
        assert sheet["variables"][field]["locked"] is True


def test_visual_sheet_keeps_explicit_footwear_over_context_defaults() -> None:
    sheet = _visual_sheet(_extract(RUN_B), original_input=RUN_B)
    assert sheet["variables"]["footwear_family"]["user_selection"] == "open_toe_high_heels"
    assert sheet["variables"]["legwear_family"]["user_selection"] == "blue_white_striped_stockings"


def test_quick_workflow_reaches_ready_with_explicit_contract() -> None:
    with TemporaryDirectory() as directory:
        response = InteractionRuntime(directory).create_session(RUN_B, CreationMode.QUICK, seed=13)
    assert response.status == "GENERATION_READY"


def test_quick_workflow_final_design_retains_explicit_records() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session(RUN_B, CreationMode.QUICK, seed=14)
        session = runtime.load_session(response.session_id)
    assert session.final_design["explicit_constraint_records"]["footwear"]["source"] == "human_explicit"
    assert session.final_design["visual_specification_contract"]["hard_constraints"]["footwear_category"] == "open-toe high heels"


def test_compiled_prompt_has_dedicated_explicit_block() -> None:
    prompt = _bundle(_extract(RUN_B)).prompt
    assert "## USER EXPLICIT HARD REQUIREMENTS" in prompt
    assert "Footwear: open_toe_high_heels" in prompt
    assert "Source: human_explicit" in prompt
    assert "Priority: HARD" in prompt


def test_compiled_prompt_does_not_retain_conflicting_dna_defaults() -> None:
    bundle = _bundle(_extract(RUN_B), dna={"palette_family": "deep teal with crimson", "footwear_category": "combat boots"})
    assert "open-toe high heels" in bundle.prompt
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0]
    assert "combat boots" not in positive
    assert "deep teal with crimson" not in positive


def test_coverage_gate_passes_run_b() -> None:
    bundle = _bundle(_extract(RUN_B))
    coverage = ExplicitConstraintCoverageGate.evaluate(bundle)
    assert coverage["status"] == "PASS"
    assert coverage["generation_allowed"] is True
    assert coverage["fields"]["footwear"]["status"] == "COVERED"


def test_coverage_gate_marks_dropped_field() -> None:
    bundle = _bundle(_extract(RUN_B)).to_dict()
    bundle["prompt"] = bundle["prompt"].replace("Footwear: open_toe_high_heels", "Footwear: omitted")
    coverage = ExplicitConstraintCoverageGate.evaluate(bundle)
    assert coverage["fields"]["footwear"]["status"] == "DROPPED"
    assert coverage["generation_allowed"] is False


def test_coverage_gate_preserves_unrepresentable_raw_hard_constraint() -> None:
    constraints = _extract("画一个女仆角色，硬性要求：保留一枚旧银色胸针")
    constraints["explicit_constraint_records"]["raw_hard_constraint_0"] = constraints["raw_hard_constraints"][0]
    bundle = _bundle(constraints)
    coverage = ExplicitConstraintCoverageGate.evaluate(bundle)
    assert coverage["fields"]["raw_hard_constraint_0"]["status"] == "NOT_REPRESENTABLE"
    assert coverage["generation_allowed"] is True
    assert "保留一枚旧银色胸针" in bundle.prompt


def test_runtime_blocks_when_explicit_coverage_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from runtime import interaction_runtime as module

    class FailingGate:
        @staticmethod
        def evaluate(bundle):
            return {"status": "FAIL", "generation_allowed": False, "blocking_fields": ["footwear"], "fields": {"footwear": {"status": "DROPPED"}}}

    monkeypatch.setattr(module, "ExplicitConstraintCoverageGate", FailingGate)
    with TemporaryDirectory() as directory:
        response = InteractionRuntime(directory).create_session(RUN_B, CreationMode.QUICK, seed=16)
    assert response.status == "BLOCKED"
    assert response.error_code == "EXPLICIT_CONSTRAINT_COVERAGE_FAILED"


def test_runtime_rejects_conflicting_explicit_footwear() -> None:
    with TemporaryDirectory() as directory:
        response = InteractionRuntime(directory).create_session("画一个女仆角色，鞋子是露趾高跟但要赤脚", CreationMode.QUICK, seed=17)
    assert response.status == "BLOCKED"
    assert response.error_code == "CURRENT_USER_CONSTRAINT_CONFLICT"


def test_manifest_contains_explicit_constraint_records() -> None:
    bundle = _bundle(_extract(RUN_B))
    manifest = bundle.to_dict()["prompt_adherence_manifest"]
    assert manifest["explicit_constraints"]["palette_primary"]["value"] == "white"
    assert manifest["explicit_constraints"]["palette_primary"]["priority"] == "HARD"


def test_replay_preserves_current_run_explicit_constraints() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session(RUN_B, CreationMode.QUICK, seed=18)
        session = runtime.load_session(response.session_id)
        replay = runtime.replay_session(session.session_id)
    assert replay["audit_log"]
    assert session.final_design["explicit_constraint_records"]["role_identity"]["source"] == "human_explicit"


def test_user_decide_conflicting_update_is_blocked() -> None:
    sheet = _visual_sheet(_extract(RUN_B), original_input=RUN_B)
    with pytest.raises(ExplicitUserConstraintConflict):
        _apply_visual_value(sheet, "footwear", source="human_select", value="combat_boots")


def test_unmentioned_intrusive_features_are_not_defaulted() -> None:
    constraints = _extract("画一个女仆角色")
    candidate = CandidateGenerator().generate(
        gate_id="CHARACTER_DIRECTION_GATE", original_input="画一个女仆角色", explicit_constraints=constraints
    )[0]
    assert candidate["design_dna"]["horn_topology"] == "none"
    assert candidate["design_dna"]["tail_design"] == "none"
    assert candidate["design_dna"]["wing_strategy"] == "none"


def test_legacy_hair_constraint_shape_remains_compatible() -> None:
    constraints = _extract("使用银发")
    assert constraints["hair_color"] == "银发"
    assert "hair_color" in constraints["explicit_user_fields"]
    assert constraints["explicit_constraint_records"]["hair_color"]["source"] == "human_explicit"
