from __future__ import annotations

from tempfile import TemporaryDirectory

from runtime.interaction_candidates import CandidateGenerator, validate_candidate_diversity
from runtime.interaction_runtime import CreationMode, InteractionRuntime


SUCCUBUS_REQUEST = "画一个魅魔角色，要求有魅魔角，体现魅力，性感暴露但是不涉黄"


def _quick_design(seed: int) -> dict:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session(SUCCUBUS_REQUEST, CreationMode.QUICK, seed=seed)
        return runtime.load_session(response.session_id).to_dict()


def test_design_dna_covers_structural_fields_and_rejects_cosmetic_only_variants() -> None:
    candidates = CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=SUCCUBUS_REQUEST)
    assert len(candidates) == 4
    assert all("design_dna" in item for item in candidates)
    assert all({"costume_topology", "horn_topology", "pose_family", "footwear_category"} <= item["design_dna"].keys() for item in candidates)
    assert validate_candidate_diversity(candidates)["status"] == "PASS"

    cosmetic_only = [
        {"id": "a", "hair_color": "red", "hair_style_family": "long hair", "outfit_direction": "gothic dress", "footwear_family": "heels"},
        {"id": "b", "hair_color": "silver", "hair_style_family": "long hair", "outfit_direction": "gothic dress", "footwear_family": "heels"},
    ]
    result = validate_candidate_diversity(cosmetic_only)
    assert result["status"] == "LOW_STRUCTURAL_DIVERSITY"
    assert result["valid"] is False


def test_quick_seed_is_replayable_and_changes_structural_design_path() -> None:
    first = _quick_design(101)
    replay = _quick_design(101)
    other = _quick_design(102)
    assert first["design_seed"] == replay["design_seed"] == 101
    assert first["final_design"]["design_dna"] == replay["final_design"]["design_dna"]
    assert first["selected_character_direction"]["resolution_metadata"]["strategy"] == "seeded_structured_sampling"
    assert first["final_design"]["design_dna"] != other["final_design"]["design_dna"]


def test_ai_decide_uses_divergent_pool_and_not_quick_sampling() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session(SUCCUBUS_REQUEST, CreationMode.AI_DECIDE, seed=101)
        session = runtime.load_session(response.session_id)
        assert len(session.character_explore_result) == 4
        assert len({item["design_dna"]["costume_topology"] for item in session.character_explore_result}) == 4
        metadata = session.selected_character_direction["resolution_metadata"]
        assert metadata["strategy"] == "divergent_candidate_generation_then_score_selection"
        assert metadata["candidate_pool_size"] == 4
        assert session.selected_character_direction["id"] != _quick_design(101)["selected_character_direction"]["id"]


def test_final_prompt_contains_selected_design_dna_and_policy_constraints() -> None:
    session = _quick_design(101)
    dna = session["final_design"]["design_dna"]
    prompt = session["compiled_prompt"]["prompt"]
    assert dna["horn_topology"] in prompt
    assert dna["costume_topology"] in prompt
    assert dna["pose_family"] in prompt
    assert "no leg crossover" in prompt
