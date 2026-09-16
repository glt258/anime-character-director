"""Focused acceptance checks for contextual interaction candidates."""

from __future__ import annotations

import json

from runtime.interaction_runtime import CreationMode
from runtime.interaction_candidates import CANDIDATE_GENERATOR_VERSION, CandidateGenerator
from runtime.workflow_runner import CUSTOM_INPUT_GATE, PersistentWorkflowRunner


A_INPUT = "设计一个现代都市幻想题材的少女角色。她安静克制、观察力很强，但有一点危险感。不要成熟御姐感，不要传统制服模板，不要默认黑丝高跟鞋，不要交叉腿。"
B_INPUT = "设计一个性格外向、动作很快的少女角色。她和机械设备、维修工作有长期关系，但不要把她设计成拿着扳手、戴着护目镜的字面化机械师。姿势要有动态感，不要交叉腿。"
C_INPUT = "设计一个冷血、危险、具有强烈压迫感的女性兽人角色。她不能只是普通人类女性加动物耳朵，需要在轮廓、体态、局部结构和服装语言上体现真正的非人感。不要默认高跟鞋。"
D_INPUT = "设计一个温柔、耐心、很容易让人信任的年轻女性角色，但不要使用粉色长发、白色连衣裙、蕾丝、软妹系等常见模板。"


def _candidate_text(candidates: list[dict]) -> str:
    return json.dumps(candidates, ensure_ascii=False).lower()


def test_gate_one_candidates_are_contextual_and_use_stable_ids() -> None:
    generator = CandidateGenerator()
    a = generator.generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=A_INPUT)
    b = generator.generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=B_INPUT)
    assert [item["id"] for item in a] == ["candidate_01", "candidate_02", "candidate_03", "candidate_04"]
    assert a != b
    assert all(item["candidate_generator_version"] == CANDIDATE_GENERATOR_VERSION for item in a)


def test_character_a_candidates_respect_negative_constraints() -> None:
    text = _candidate_text(CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=A_INPUT))
    assert "成熟御姐" not in text
    assert "高跟鞋" not in text
    assert "黑丝" not in text
    assert "交叉腿" not in text


def test_character_b_is_mechanical_without_literal_job_props() -> None:
    text = _candidate_text(CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=B_INPUT))
    assert "扳手" not in text
    assert "护目镜" not in text
    assert "机械师制服" not in text
    assert "nonliteral_mechanical_identity" in text


def test_character_c_changes_species_read_and_silhouette() -> None:
    candidates = CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=C_INPUT)
    silhouettes = {item["visual_implications"]["silhouette"]["zh"] for item in candidates}
    anchors = {item["visual_implications"]["primary_anchor"]["zh"] for item in candidates}
    assert len(silhouettes) == 4
    assert len(anchors) == 4
    assert all("nonhuman_silhouette_and_anatomy" in item["constraint_compatibility"]["checked"] for item in candidates)


def test_character_d_avoids_soft_template_defaults() -> None:
    candidates = CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input=D_INPUT)
    assert len(candidates) == 4
    assert all(item["constraint_compatibility"]["status"] == "compatible" for item in candidates)
    text = _candidate_text(candidates)
    for forbidden in ("粉色长发", "白色连衣裙", "蕾丝", "软妹"):
        assert forbidden not in text


def test_gate_two_uses_previous_character_resolution(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow(A_INPUT, CreationMode.USER_DECIDE, interaction_locale="zh-CN")
    second = runner.continue_workflow(first.run_id, "A")
    assert second.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert all(item["metadata"]["generation_context"]["prior_direction"] for item in second.checkpoint.options[:-1])


def test_restart_and_back_preserve_the_same_candidate_set(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow(A_INPUT, CreationMode.USER_DECIDE)
    original = first.checkpoint.options
    restarted = PersistentWorkflowRunner(tmp_path).load_checkpoint(first.run_id)
    assert restarted.options == original
    runner.continue_workflow(first.run_id, "A")
    back = runner.continue_workflow(first.run_id, "返回上一步")
    assert back.checkpoint.gate_type == "CHARACTER_DIRECTION_GATE"
    assert back.checkpoint.options[:-1] == original[:-1]


def test_regenerate_changes_revision_and_preserves_history(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow(A_INPUT, CreationMode.USER_DECIDE)
    regenerated = runner.continue_workflow(first.run_id, "换一批")
    session = runner.runtime.load_session(first.session_id)
    assert regenerated.checkpoint.options[:-1] != first.checkpoint.options[:-1]
    assert session.candidate_revisions["character_explore"] == 1
    assert session.candidate_history["character_explore"][0]["options"] == [item["metadata"] for item in first.checkpoint.options[:-1]]


def test_recommendation_is_current_candidate_and_custom_remains_available(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow(A_INPUT, CreationMode.USER_DECIDE)
    ids = [item["option_id"] for item in first.checkpoint.options[:-1]]
    assert first.checkpoint.prompt_payload["recommendation"]["option_id"] in ids
    custom = runner.continue_workflow(first.run_id, "E")
    assert custom.checkpoint.gate_type == CUSTOM_INPUT_GATE


def test_contextual_visual_gate_changes_with_character_profile(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow(B_INPUT, CreationMode.USER_DECIDE)
    art = runner.continue_workflow(first.run_id, "A")
    visual = runner.continue_workflow(first.run_id, "B")
    fields = {item["variable"]: item for item in visual.checkpoint.prompt_payload["variables"]}
    assert fields["outfit_direction"]["options"][0]["display_title"] == "lightweight modular action wear"
    assert fields["outfit_direction"]["recommendation_rationale"]
    assert art.checkpoint.prompt_payload["original_user_input"] == B_INPUT
