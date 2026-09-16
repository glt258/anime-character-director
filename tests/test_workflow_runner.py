"""Focused tests for the logical WorkflowRun continuation seam."""

from __future__ import annotations

from types import SimpleNamespace

from runtime.interaction_runtime import CreationMode
from runtime.workflow_runner import (
    CUSTOM_INPUT_GATE,
    CUSTOM_OPTION_ID,
    CheckpointStatus,
    InteractionLocalizer,
    PersistentWorkflowRunner,
    WorkflowRunStatus,
)


def _start(tmp_path):
    return PersistentWorkflowRunner(tmp_path).start_workflow("给我设计一个女性角色，我自己选", CreationMode.USER_DECIDE)


def _to_visual(runner, run_id):
    art = runner.continue_workflow(run_id, "B")
    return runner.continue_workflow(run_id, "A")


def test_01_user_decide_start_creates_one_waiting_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    response = _start(tmp_path)
    run = runner.load_workflow(response.run_id)
    assert response.status == WorkflowRunStatus.WAITING_FOR_INTERACTION.value
    assert run.run_id == response.run_id
    assert run.current_checkpoint == response.checkpoint.checkpoint_id


def test_02_character_reply_continues_to_art_gate_same_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "B")
    assert response.status == WorkflowRunStatus.WAITING_FOR_INTERACTION.value
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert response.run_id == first.run_id


def test_03_art_reply_continues_to_visual_gate_same_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = _to_visual(runner, first.run_id)
    assert response.checkpoint.gate_type == "VISUAL_PREFERENCE_GATE"
    assert response.run_id == first.run_id


def test_04_visual_reply_reaches_generation_ready_same_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    _to_visual(runner, first.run_id)
    response = runner.continue_workflow(first.run_id, "发色银白，鞋子裸足，其他按推荐")
    assert response.status == WorkflowRunStatus.GENERATION_READY.value
    assert response.generation_ready is True
    assert response.run_id == first.run_id


def test_05_complete_user_flow_has_one_workflow_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    _to_visual(runner, first.run_id)
    runner.continue_workflow(first.run_id, "其他按推荐")
    assert len(list(tmp_path.glob("*/workflow_run.json"))) == 1


def test_06_each_human_gate_has_an_independent_checkpoint(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    art = runner.continue_workflow(first.run_id, "B")
    visual = runner.continue_workflow(first.run_id, "A")
    run = runner.load_workflow(first.run_id)
    checkpoints = [runner.load_checkpoint(first.run_id, item) for item in run.checkpoint_history]
    assert len(checkpoints) == 3
    assert {item.gate_type for item in checkpoints if item} == {"CHARACTER_DIRECTION_GATE", "ART_DIRECTION_GATE", "VISUAL_PREFERENCE_GATE"}
    assert art.checkpoint.checkpoint_id != visual.checkpoint.checkpoint_id


def test_07_resolved_checkpoint_cannot_be_resolved_again(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    runner.continue_workflow(first.run_id, "B")
    stale = runner.continue_workflow(first.run_id, "A", checkpoint_id=first.checkpoint.checkpoint_id)
    assert stale.error_code == "STALE_CHECKPOINT"


def test_08_old_checkpoint_reply_is_stale_without_mutation(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    current = runner.continue_workflow(first.run_id, "B")
    before = runner.load_workflow(first.run_id).to_dict()
    stale = runner.continue_workflow(first.run_id, "A", checkpoint_id=first.checkpoint.checkpoint_id)
    assert stale.error_code == "STALE_CHECKPOINT"
    assert runner.load_workflow(first.run_id).to_dict() == before
    assert current.checkpoint.checkpoint_id == before["current_checkpoint"]


def test_09_four_real_candidates_keep_custom_as_fifth_display_option(tmp_path) -> None:
    response = _start(tmp_path)
    assert len(response.checkpoint.options) == 5
    assert response.checkpoint.options[-1]["option_id"] == CUSTOM_OPTION_ID
    assert "E｜自定义" in response.user_message


def test_10_three_candidates_get_custom_as_fourth_option() -> None:
    raw = SimpleNamespace(
        gate={"gate_id": "g", "gate_type": "CHARACTER_DIRECTION_GATE"},
        options=[{"id": "A", "design_thesis": "quiet precision"}, {"id": "B", "design_thesis": "controlled anomaly"}, {"id": "C", "design_thesis": "warm social contrast"}],
        recommended="A",
        stage="CHARACTER_DIRECTION_RESOLUTION",
    )
    checkpoint = InteractionLocalizer("zh-CN").checkpoint_for("run", raw)
    assert [item["option_id"] for item in checkpoint.options] == ["A", "B", "C", CUSTOM_OPTION_ID]


def test_11_custom_option_id_is_stable_and_not_letter_d(tmp_path) -> None:
    response = _start(tmp_path)
    ids = [item["option_id"] for item in response.checkpoint.options]
    assert ids[:4] == ["candidate_01", "candidate_02", "candidate_03", "candidate_04"]
    assert ids[-1] == CUSTOM_OPTION_ID


def test_12_custom_option_opens_custom_input_checkpoint(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "E")
    assert response.checkpoint.gate_type == CUSTOM_INPUT_GATE
    assert response.run_id == first.run_id
    assert runner.load_workflow(first.run_id).checkpoint_history[-1] == response.checkpoint.checkpoint_id


def test_13_custom_text_is_human_custom_and_continues(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    runner.continue_workflow(first.run_id, "E")
    response = runner.continue_workflow(first.run_id, "外表乖巧但实际有危险感")
    session = runner.runtime.load_session(first.session_id)
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert any(item.get("resolution", {}).get("decision_source") == "human_custom" for item in session.audit_log if item.get("event") == "gate_resolution")


def test_14_direct_natural_language_custom_skips_custom_option(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "我想自己定：整体偏慵懒，但有一点危险感")
    session = runner.runtime.load_session(first.session_id)
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    assert session.selected_character_direction["id"] == "CUSTOM"
    assert session.selected_character_direction["custom"]


def test_15_chinese_locale_localizes_titles_descriptions_and_recommendation(tmp_path) -> None:
    response = PersistentWorkflowRunner(tmp_path).start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    assert response.checkpoint.options[0]["display_title"] == "身份主轴"
    assert response.checkpoint.options[0]["metadata"]["candidate_generator_version"] == "CONTEXT_AWARE_DYNAMIC_INTERACTION_CANDIDATES_V1"
    assert "推荐" in response.user_message
    assert "quiet precision" not in response.user_message


def test_16_english_locale_renders_english_ui(tmp_path) -> None:
    response = PersistentWorkflowRunner(tmp_path).start_workflow("Design an adult female character, let me choose", CreationMode.USER_DECIDE, interaction_locale="en-US")
    assert response.checkpoint.options[0]["display_title"] == "Identity Spine"
    assert response.checkpoint.options[-1]["display_title"] == "Custom"
    assert "Recommended" in response.user_message


def test_17_locale_changes_display_not_internal_option_ids(tmp_path) -> None:
    zh = PersistentWorkflowRunner(tmp_path / "zh").start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE, interaction_locale="zh-CN")
    en = PersistentWorkflowRunner(tmp_path / "en").start_workflow("Design an adult female character, let me choose", CreationMode.USER_DECIDE, interaction_locale="en-US")
    assert [item["option_id"] for item in zh.checkpoint.options] == [item["option_id"] for item in en.checkpoint.options]
    assert zh.checkpoint.options[0]["display_title"] != en.checkpoint.options[0]["display_title"]


def test_18_chinese_user_message_does_not_leak_internal_terms(tmp_path) -> None:
    response = _start(tmp_path)
    for term in ("WAITING_FOR_USER", "human_custom", "InteractionCheckpoint", "quiet precision"):
        assert term not in response.user_message


def test_19_user_reply_auto_continues_without_continue_keyword(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "B")
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_20_restart_runner_resumes_same_workflow(tmp_path) -> None:
    first_runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    restarted = PersistentWorkflowRunner(tmp_path)
    response = restarted.continue_workflow(first.run_id, "B")
    assert response.run_id == first.run_id
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_21_active_run_routes_short_reply_to_current_checkpoint(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_active_workflow("B")
    assert response.run_id == first.run_id
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_22_explicit_new_role_cancels_old_run_and_starts_new_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    replacement = runner.continue_workflow(first.run_id, "取消这个，重新做一个角色")
    assert runner.load_workflow(first.run_id).status == WorkflowRunStatus.CANCELLED.value
    assert replacement.run_id != first.run_id


def test_23_visual_custom_values_and_recommendations_reach_ready(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    _to_visual(runner, first.run_id)
    ready = runner.continue_workflow(first.run_id, "发色银白，鞋子裸足，其他按推荐")
    session = runner.runtime.load_session(first.session_id)
    assert ready.generation_ready is True
    assert session.final_design["visual_preferences"]["hair_color"] == "silver-white"
    assert session.final_design["visual_preferences"]["footwear_family"] == "barefoot"


def test_24_mode_switch_preserves_run_and_finishes(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "后面都你决定吧")
    run = runner.load_workflow(first.run_id)
    assert response.generation_ready is True
    assert run.creation_mode == CreationMode.AI_DECIDE.value


def test_25_regenerate_options_keeps_run_and_replaces_checkpoint(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "都不喜欢，再来一批")
    assert response.run_id == first.run_id
    assert response.checkpoint.gate_type == "CHARACTER_DIRECTION_GATE"
    assert response.checkpoint.checkpoint_id != first.checkpoint.checkpoint_id


def test_26_custom_checkpoint_history_marks_option_and_input_resolution(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    custom = runner.continue_workflow(first.run_id, "E")
    runner.continue_workflow(first.run_id, "表面随和，实际上很危险")
    history = [runner.load_checkpoint(first.run_id, item) for item in runner.load_workflow(first.run_id).checkpoint_history]
    assert history[0].status == CheckpointStatus.RESOLVED.value
    assert history[1].status == CheckpointStatus.RESOLVED.value
    assert history[1].gate_type == CUSTOM_INPUT_GATE
    assert custom.run_id == first.run_id


def test_27_visual_custom_checkpoint_accepts_field_values_in_one_message(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    _to_visual(runner, first.run_id)
    custom = runner.continue_workflow(first.run_id, "自定义")
    ready = runner.continue_workflow(first.run_id, "发色自定义灰蓝，鞋履裸足，其他按推荐")
    session = runner.runtime.load_session(first.session_id)
    assert custom.checkpoint.gate_type == CUSTOM_INPUT_GATE
    assert ready.generation_ready is True
    assert session.final_design["visual_preferences"]["hair_color"] == "gray-blue"


def test_28_explicit_language_switch_updates_same_run_locale(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    switched = runner.continue_workflow(first.run_id, "后面用英文")
    assert switched.run_id == first.run_id
    assert switched.checkpoint.options[0]["display_title"] == "Identity Spine"
    assert runner.load_workflow(first.run_id).interaction_locale == "en-US"


def test_29_quick_runner_has_zero_human_checkpoints(tmp_path) -> None:
    response = PersistentWorkflowRunner(tmp_path).start_workflow("快速设计一个成年女性角色")
    run = PersistentWorkflowRunner(tmp_path).load_workflow(response.run_id)
    assert response.status == WorkflowRunStatus.GENERATION_READY.value
    assert response.checkpoint is None
    assert run.checkpoint_history == []


def test_30_ai_decide_runner_has_zero_human_checkpoints(tmp_path) -> None:
    response = PersistentWorkflowRunner(tmp_path).start_workflow("你帮我完整设计一个成年男性角色，都交给你")
    run = PersistentWorkflowRunner(tmp_path).load_workflow(response.run_id)
    assert response.status == WorkflowRunStatus.GENERATION_READY.value
    assert response.checkpoint is None
    assert run.checkpoint_history == []


def test_31_language_switch_relocalizes_visual_checkpoint(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    _to_visual(runner, first.run_id)
    switched = runner.continue_workflow(first.run_id, "后面用英文")
    fields = switched.checkpoint.prompt_payload["variables"]
    assert switched.checkpoint.prompt_payload["title"] == "Visual Preferences"
    assert fields[0]["display_name"] == "Hair Color"


def test_32_natural_direction_labels_and_ordinals_continue_same_run(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    first = _start(tmp_path)
    response = runner.continue_workflow(first.run_id, "我更喜欢第二种。")
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"
    runner = PersistentWorkflowRunner(tmp_path / "label")
    first = PersistentWorkflowRunner(tmp_path / "label").start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    response = runner.continue_workflow(first.run_id, f"我选{first.checkpoint.options[0]['display_title']}")
    assert response.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_33_standard_and_direct_custom_language_are_distinct(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path / "standard")
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    custom = runner.continue_workflow(first.run_id, "我想自己定")
    assert custom.checkpoint.gate_type == CUSTOM_INPUT_GATE
    runner = PersistentWorkflowRunner(tmp_path / "direct")
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    direct = runner.continue_workflow(first.run_id, "她应该表面安静，但是带一点危险感，不要太疯")
    assert direct.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_34_recommendation_question_and_duplicate_submission_are_safe(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path / "question")
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    question = runner.continue_workflow(first.run_id, "你推荐哪个？")
    assert question.checkpoint.checkpoint_id == first.checkpoint.checkpoint_id
    runner = PersistentWorkflowRunner(tmp_path / "duplicate")
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    runner.continue_workflow(first.run_id, "B")
    duplicate = runner.continue_workflow(first.run_id, "B")
    assert duplicate.error_code == "DUPLICATE_INTERACTION"
    assert duplicate.checkpoint.gate_type == "ART_DIRECTION_GATE"


def test_35_back_aliases_mode_switch_and_explicit_negative_constraints(tmp_path) -> None:
    runner = PersistentWorkflowRunner(tmp_path / "back")
    first = runner.start_workflow("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
    runner.continue_workflow(first.run_id, "A")
    runner.continue_workflow(first.run_id, "返回上一步")
    response = runner.continue_workflow(first.run_id, "返回上一步")
    assert response.checkpoint.gate_type == "CHARACTER_DIRECTION_GATE"
    runner = PersistentWorkflowRunner(tmp_path / "constraints")
    first = runner.start_workflow("设计一个成年女性角色，不要成熟御姐感，不要高跟鞋，不要交叉腿，我自己选", CreationMode.USER_DECIDE)
    runner.continue_workflow(first.run_id, "A")
    runner.continue_workflow(first.run_id, "B")
    ready = runner.continue_workflow(first.run_id, "其他按推荐")
    negative = runner.runtime.load_session(first.session_id).final_design["explicit_user_constraints"]["negative_constraints"]
    assert ready.generation_ready
    assert {"forbid_mature_older_sister_vibe", "forbid_footwear_family", "forbid_crossed_legs"} <= set(negative)


def test_recommendation_aliases_resolve_only_the_remaining_visual_sheet(tmp_path) -> None:
    for index, message in enumerate(("其他按推荐", "剩下的按推荐", "其他都按推荐", "剩下都用推荐", "其他你推荐就行", "剩下你决定", "其他交给你", "leave the rest to you", "you decide the rest")):
        runner = PersistentWorkflowRunner(tmp_path / str(index))
        first = _start(tmp_path / str(index))
        _to_visual(runner, first.run_id)
        response = runner.continue_workflow(first.run_id, message)
        assert response.generation_ready is True
