"""Focused coverage for the Codex-native interaction seam."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from runtime.codex_interaction_adapter import NativeInteractionAdapter, NativeInteractionError
from runtime.interaction_runtime import CreationMode
from runtime.workflow_runner import PersistentWorkflowRunner


def _start(tmp_path):
    runner = PersistentWorkflowRunner(tmp_path)
    response = runner.start_workflow("设计一个现代都市幻想少女角色，我自己选", CreationMode.USER_DECIDE)
    return runner, response


def _single_answer(spec, index=0):
    option = spec.questions[0].options[index]
    return {"answers": {spec.questions[0].question_id: {"answers": [option.label]}}}


def _custom_answer(spec, text="安静但危险感来自眼神"):
    return {"answers": {spec.questions[0].question_id: {"answers": ["Other"], "other": text}}}


def test_nui_t01_direction_checkpoint_becomes_three_choice_native_spec(tmp_path):
    runner, response = _start(tmp_path)
    spec = runner.native_interaction_spec(response.run_id, checkpoint_id=response.checkpoint.checkpoint_id)
    request = spec.to_request_user_input()
    assert len(spec.questions) == 1
    assert len(request["questions"][0]["options"]) == 3
    assert spec.questions[0].options[0].recommended is True
    assert "推荐" in spec.questions[0].options[0].label or "Recommended" in spec.questions[0].options[0].label
    assert all(option.candidate_id != "__CUSTOM__" for option in spec.questions[0].options)


def test_nui_t02_recommendation_is_first_and_only_an_annotation(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    assert spec.questions[0].options[0].recommended is True
    assert runner.load_workflow(first.run_id).current_checkpoint == first.checkpoint.checkpoint_id


def test_nui_t03_label_maps_to_stable_candidate_id_and_continues_same_run(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    response = runner.continue_native_workflow(first.run_id, _single_answer(spec, 1), checkpoint_id=spec.checkpoint_id)
    session = runner.runtime.load_session(first.session_id)
    assert response.run_id == first.run_id
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert session.selected_character_direction["id"] == spec.questions[0].options[1].candidate_id


def test_nui_t04_duplicate_label_fails_closed():
    checkpoint = SimpleNamespace(
        status="OPEN",
        checkpoint_id="cp",
        gate_id="gate",
        gate_type="CHARACTER_DIRECTION_GATE",
        custom_input_allowed=True,
        prompt_payload={"prompt": "choose", "candidate_revision": 0},
        options=[
            {"option_id": "candidate_01", "display_title": "Same", "display_description": "one", "is_recommended": True},
            {"option_id": "candidate_02", "display_title": "Same", "display_description": "two", "is_recommended": False},
            {"option_id": "candidate_03", "display_title": "Third", "display_description": "three", "is_recommended": False},
        ],
    )
    adapter = NativeInteractionAdapter()
    spec = adapter.build(checkpoint)
    with pytest.raises(NativeInteractionError, match="Duplicate label") as error:
        adapter.resolve(spec, {"answers": {"direction": {"answers": ["Same"]}}})
    assert error.value.code == "DUPLICATE_NATIVE_LABEL"


def test_nui_t05_invalid_answer_fails_closed(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    invalid = runner.continue_native_workflow(
        first.run_id,
        {"answers": {"wrong_question": {"answers": ["not a current label"]}}},
        checkpoint_id=spec.checkpoint_id,
    )
    assert invalid.error_code == "INVALID_NATIVE_ANSWER"
    assert runner.load_workflow(first.run_id).current_checkpoint == spec.checkpoint_id
    stale = runner.continue_native_workflow(
        first.run_id,
        {**_single_answer(spec), "candidate_revision": spec.revision + 1},
        checkpoint_id=spec.checkpoint_id,
    )
    assert stale.error_code == "STALE_NATIVE_ANSWER"
    assert runner.load_workflow(first.run_id).current_checkpoint == spec.checkpoint_id


def test_nui_t06_stale_revision_fails_closed_without_mutation(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    before = runner.load_workflow(first.run_id).to_dict()
    response = runner.continue_native_workflow(
        first.run_id,
        {**_single_answer(spec), "candidate_revision": spec.revision + 1},
        checkpoint_id=spec.checkpoint_id,
    )
    assert response.error_code == "STALE_NATIVE_ANSWER"
    assert runner.load_workflow(first.run_id).to_dict() == before


def test_nui_t07_other_maps_to_custom_and_auto_continues(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    response = runner.continue_native_workflow(first.run_id, _custom_answer(spec), checkpoint_id=spec.checkpoint_id)
    session = runner.runtime.load_session(first.session_id)
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert session.selected_character_direction["id"] == "CUSTOM"
    assert session.selected_character_direction["custom"] == "安静但危险感来自眼神"


def test_nui_t08_custom_text_is_persisted(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    text = "安静但危险感来自眼神"
    runner.continue_native_workflow(first.run_id, _custom_answer(spec, text), checkpoint_id=spec.checkpoint_id)
    session = runner.runtime.load_session(first.session_id)
    assert session.selected_character_direction["custom"] == text


def test_nui_t09_restart_rebuilds_identical_spec(tmp_path):
    runner, first = _start(tmp_path)
    before = runner.native_interaction_spec(first.run_id)
    after = PersistentWorkflowRunner(tmp_path).native_interaction_spec(first.run_id)
    assert after.to_dict() == before.to_dict()


def test_nui_t10_back_reopens_same_candidate_spec_without_regeneration(tmp_path):
    runner, first = _start(tmp_path)
    character = runner.native_interaction_spec(first.run_id)
    art_response = runner.continue_native_workflow(first.run_id, _single_answer(character), checkpoint_id=character.checkpoint_id)
    art = runner.native_interaction_spec(first.run_id, checkpoint_id=art_response.checkpoint.checkpoint_id)
    visual = runner.continue_native_workflow(first.run_id, _single_answer(art), checkpoint_id=art.checkpoint_id)
    back = runner.continue_workflow(first.run_id, "返回上一步")
    restored = runner.native_interaction_spec(first.run_id, checkpoint_id=back.checkpoint.checkpoint_id)
    assert visual.checkpoint.gate_type == "VISUAL_PREFERENCE_GATE"
    assert back.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert restored.to_dict()["questions"] == art.to_dict()["questions"]


def test_nui_t11_regenerate_changes_revision_and_invalidates_old_spec(tmp_path):
    runner, first = _start(tmp_path)
    old = runner.native_interaction_spec(first.run_id)
    regenerated = runner.continue_workflow(first.run_id, "换一批")
    new = runner.native_interaction_spec(first.run_id, checkpoint_id=regenerated.checkpoint.checkpoint_id)
    assert new.revision == old.revision + 1
    stale = runner.continue_native_workflow(first.run_id, {**_single_answer(old), "candidate_revision": old.revision}, checkpoint_id=old.checkpoint_id)
    assert stale.error_code == "STALE_CHECKPOINT"


def test_nui_t12_visual_preference_is_multi_question_and_resolves_once(tmp_path):
    runner, first = _start(tmp_path)
    character = runner.native_interaction_spec(first.run_id)
    art_response = runner.continue_native_workflow(first.run_id, _single_answer(character), checkpoint_id=character.checkpoint_id)
    art = runner.native_interaction_spec(first.run_id, checkpoint_id=art_response.checkpoint.checkpoint_id)
    visual_response = runner.continue_native_workflow(first.run_id, _single_answer(art), checkpoint_id=art.checkpoint_id)
    response = visual_response
    question_ids = []
    while not response.generation_ready:
        visual = runner.native_interaction_spec(first.run_id, checkpoint_id=response.checkpoint.checkpoint_id)
        assert 1 <= len(visual.questions) <= 3
        question_ids.extend(question.question_id for question in visual.questions)
        answer = {"answers": {question.question_id: {"answers": [question.options[0].label]} for question in visual.questions}}
        response = runner.continue_native_workflow(first.run_id, answer, checkpoint_id=visual.checkpoint_id)
    assert len(question_ids) >= 2
    assert response.generation_ready is True
    assert len(list(tmp_path.glob("*/workflow_run.json"))) == 1


def test_nui_t13_duplicate_native_submission_does_not_advance_twice(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    answer = _single_answer(spec)
    next_response = runner.continue_native_workflow(first.run_id, answer, checkpoint_id=spec.checkpoint_id)
    duplicate = runner.continue_native_workflow(first.run_id, answer, checkpoint_id=spec.checkpoint_id)
    assert duplicate.error_code == "STALE_CHECKPOINT"
    assert runner.load_workflow(first.run_id).current_checkpoint == next_response.checkpoint.checkpoint_id


def test_nui_t14_missing_answer_fails_closed_without_mutation(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    before = runner.load_workflow(first.run_id).to_dict()
    response = runner.continue_native_workflow(
        first.run_id,
        {"answers": {spec.questions[0].question_id: {"answers": []}}},
        checkpoint_id=spec.checkpoint_id,
    )
    assert response.error_code == "MISSING_NATIVE_ANSWER"
    assert runner.load_workflow(first.run_id).to_dict() == before


def test_nui_t15_bare_native_freeform_text_maps_to_custom(tmp_path):
    runner, first = _start(tmp_path)
    spec = runner.native_interaction_spec(first.run_id)
    response = runner.continue_native_workflow(
        first.run_id,
        {"answers": {spec.questions[0].question_id: {"answers": ["用户直接输入的独特方向"]}}},
        checkpoint_id=spec.checkpoint_id,
    )
    session = runner.runtime.load_session(first.session_id)
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert session.selected_character_direction["id"] == "CUSTOM"
    assert session.selected_character_direction["custom"] == "用户直接输入的独特方向"


def test_nui_t16_native_flow_stops_before_imagegen(tmp_path):
    runner, first = _start(tmp_path)
    character = runner.native_interaction_spec(first.run_id)
    art_response = runner.continue_native_workflow(first.run_id, _single_answer(character), checkpoint_id=character.checkpoint_id)
    art = runner.native_interaction_spec(first.run_id, checkpoint_id=art_response.checkpoint.checkpoint_id)
    response = runner.continue_native_workflow(first.run_id, _single_answer(art), checkpoint_id=art.checkpoint_id)
    while not response.generation_ready:
        visual = runner.native_interaction_spec(first.run_id, checkpoint_id=response.checkpoint.checkpoint_id)
        answer = {"answers": {question.question_id: {"answers": [question.options[0].label]} for question in visual.questions}}
        response = runner.continue_native_workflow(first.run_id, answer, checkpoint_id=visual.checkpoint_id)
    assert response.generation_ready is True
    assert response.error_code is None
    assert not any(path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} for path in tmp_path.rglob("*"))
