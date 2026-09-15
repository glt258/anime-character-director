from __future__ import annotations

from tempfile import TemporaryDirectory

import pytest

from runtime.interaction_runtime import (
    CreationMode,
    InteractionAction,
    InteractionEvent,
    InteractionRuntime,
    PipelineStage,
    SessionStatus,
)
from runtime.natural_language_interaction import (
    ExplicitConstraintExtractor,
    IntentType,
    NaturalLanguageInteractionParser,
)


def candidate_context(count: int = 4) -> dict:
    return {
        "gate_type": "CHARACTER_DIRECTION_GATE",
        "mode": "USER_DECIDE",
        "options": [{"id": chr(65 + index)} for index in range(count)],
    }


def visual_context() -> dict:
    variables = {
        "hair_color": {},
        "outfit_direction": {},
        "footwear_family": {},
        "eye_color": {},
        "legwear_family": {},
        "fanservice_level": {},
    }
    return {"gate_type": "VISUAL_PREFERENCE_GATE", "mode": "USER_DECIDE", "visual_variables": variables}


@pytest.mark.parametrize(
    ("text", "expected"),
    [("A", "A"), ("我选B", "B"), ("B吧", "B"), ("就C", "C"), ("还是B比较好", "B"), ("B，然后继续", "B")],
)
def test_parser_selects_short_natural_candidate_replies(text: str, expected: str) -> None:
    intent = NaturalLanguageInteractionParser().parse(text, candidate_context())
    assert intent.intent_type == IntentType.SELECTION.value
    assert intent.action == "SELECT"
    assert intent.selected_options == [expected]


@pytest.mark.parametrize(
    ("text", "expected"),
    [("第一个", "A"), ("选第二个", "B"), ("第二套", "B"), ("第三个", "C"), ("最后一个", "D")],
)
def test_parser_uses_dynamic_ordinal_mapping(text: str, expected: str) -> None:
    intent = NaturalLanguageInteractionParser().parse(text, candidate_context())
    assert intent.intent_type == IntentType.SELECTION.value
    assert intent.selected_options == [expected]


def test_parser_ordinal_uses_actual_option_count() -> None:
    intent = NaturalLanguageInteractionParser().parse("最后一个", candidate_context(2))
    assert intent.selected_options == ["B"]


def test_parser_ambiguous_middle_requests_minimal_clarification() -> None:
    intent = NaturalLanguageInteractionParser().parse("中间那个", candidate_context())
    assert intent.intent_type == IntentType.AMBIGUOUS.value
    assert intent.needs_clarification is True
    assert "B" in intent.clarification_reason and "C" in intent.clarification_reason


@pytest.mark.parametrize("text", ["为什么推荐B？", "A和B有什么区别？", "你觉得哪个更适合她？"])
def test_parser_questions_are_question_only(text: str) -> None:
    intent = NaturalLanguageInteractionParser().parse(text, candidate_context())
    assert intent.intent_type == IntentType.QUESTION_ONLY.value
    assert intent.action is None


def test_parser_supports_overall_and_field_mix() -> None:
    parser = NaturalLanguageInteractionParser()
    overall = parser.parse("A和C混一下", candidate_context())
    field = parser.parse("A的头发和C的衣服拼一下", candidate_context())
    assert overall.intent_type == IntentType.MIX_SELECTION.value
    assert overall.selected_options == ["A", "C"]
    assert field.field_updates["field_mix"] == {"hair_color": ["A"], "outfit_direction": ["C"]}


def test_parser_separates_delegate_mode_switch_and_partial_delegate() -> None:
    parser = NaturalLanguageInteractionParser()
    assert parser.parse("你来决定", candidate_context()).intent_type == IntentType.DELEGATION.value
    switch = parser.parse("后面都你决定", {**candidate_context(), "mode": "USER_DECIDE"})
    partial = parser.parse("发色、衣服和鞋子我自己选，其他你决定", visual_context())
    assert switch.intent_type == IntentType.MODE_SWITCH.value
    assert switch.mode_switch_target == "AI_DECIDE"
    assert partial.intent_type == IntentType.PARTIAL_DELEGATION.value
    assert set(partial.human_fields) == {"hair_color", "outfit_direction", "footwear_family"}


def test_parser_separates_recommendation_acceptance_from_delegation() -> None:
    parser = NaturalLanguageInteractionParser()
    context = visual_context()
    all_recommended = parser.parse("都按推荐", context)
    one_recommended = parser.parse("发色按推荐", context)
    delegate = parser.parse("你决定", context)
    assert all_recommended.intent_type == IntentType.ACCEPT_ALL_RECOMMENDED.value
    assert one_recommended.intent_type == IntentType.ACCEPT_RECOMMENDED.value
    assert delegate.intent_type == IntentType.DELEGATION.value


def test_parser_parses_field_updates_and_constraint_language() -> None:
    intent = NaturalLanguageInteractionParser().parse("眼睛C，衣服A和D混一下，鞋子裸足，性感程度中等", visual_context())
    assert intent.intent_type == IntentType.CUSTOM_UPDATE.value
    assert intent.field_updates["eye_color"]["option_id"] == "C"
    assert intent.field_updates["outfit_direction"]["mix"] == ["A", "D"]
    assert intent.field_updates["footwear_family"]["value"] == "barefoot"
    assert intent.field_updates["fanservice_level"]["value"] == "moderate"


def test_explicit_constraint_extractor_preserves_last_explicit_hair_choice() -> None:
    constraints = ExplicitConstraintExtractor().extract("AI推荐黑发，但我还是想要银发。")
    assert constraints["hair_color"] == "银发"
    assert constraints["explicit_user_fields"] == ["hair_color"]


def test_explicit_constraint_extractor_keeps_positive_and_negative_constraints() -> None:
    constraints = ExplicitConstraintExtractor().extract("成年女性，粉发，白色连裤袜，裸足，不要裙子，不要高跟鞋。")
    assert constraints["age_group"] == "adult"
    assert constraints["gender"] == "female"
    assert constraints["hair_color"] == "粉发"
    assert constraints["legwear_family"] == "white opaque tights"
    assert constraints["footwear_family"] == "barefoot"
    assert constraints["negative_constraints"]["forbid_outfit_lower"] == "skirt"
    assert constraints["negative_constraints"]["forbid_footwear_family"] == "heels"


def event(runtime: InteractionRuntime, session_id: str, action: str, payload: dict | None = None, event_id: str | None = None) -> InteractionEvent:
    session = runtime.load_session(session_id)
    return InteractionEvent(event_id or action.lower(), session_id, session.current_gate or "", action, payload or {})


def to_visual(runtime: InteractionRuntime, session_id: str) -> None:
    runtime.resume_session(session_id, event(runtime, session_id, "SELECT", {"candidate_id": "B"}, "char"))
    runtime.resume_session(session_id, event(runtime, session_id, "SELECT", {"candidate_id": "C"}, "art"))


def test_runtime_natural_short_selection_and_mix() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我设计一个成年女性角色，先给我几个方向，我自己选。", CreationMode.USER_DECIDE)
        selected = runtime.resume_session(first.session_id, "B")
        mixed = runtime.resume_session(first.session_id, "A的轮廓不错，但我更喜欢C的整体感觉，混一下。")
        session = runtime.load_session(first.session_id)
        assert selected.status == SessionStatus.AWAITING_ART_DIRECTION.value
        assert session.selected_character_direction["id"] == "B"
        assert mixed.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert session.selected_art_direction["id"] == "A+C"
        assert any(item.get("decision_source") == "human_mix" for item in session.interaction_history)


def test_runtime_question_does_not_advance_or_select() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        before = runtime.load_session(first.session_id).to_dict()
        response = runtime.resume_session(first.session_id, "为什么推荐B？")
        after = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
        assert response.error_code is None
        assert after.current_gate == before["current_gate"]
        assert after.selected_character_direction is None
        assert not any(item.get("decision_source") for item in after.interaction_history)


def test_runtime_question_followed_by_explicit_selection_uses_new_choice() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        runtime.resume_session(first.session_id, "为什么推荐B？")
        response = runtime.resume_session(first.session_id, "行，那我选C。")
        session = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_ART_DIRECTION.value
        assert session.selected_character_direction["id"] == "C"


def test_runtime_natural_visual_overrides_accept_recommendation_and_finishes() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        to_visual(runtime, first.session_id)
        response = runtime.resume_session(first.session_id, "大体按推荐，但是把发色换成红色，鞋子换成裸足。")
        session = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert session.visual_preference_sheet["variables"]["hair_color"]["selection_source"] == "human_custom"
        assert session.visual_preference_sheet["variables"]["footwear_family"]["selection_source"] == "human_custom"
        assert "human_accept_recommended" in {item.get("selection_source") for item in session.visual_preference_sheet["variables"].values()}


def test_runtime_natural_partial_delegate_waits_for_named_values_then_finishes() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        to_visual(runtime, first.session_id)
        waiting = runtime.resume_session(first.session_id, "发色、衣服和鞋子我自己选，其他你决定。")
        session = runtime.load_session(first.session_id)
        assert waiting.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert set(session.unresolved_fields) == {"hair_color", "outfit_direction", "footwear_family"}
        response = runtime.resume_session(first.session_id, "发色深红，衣服B，鞋子裸足。")
        session = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert session.visual_preference_sheet["variables"]["hair_color"]["selection_source"] == "human_custom"
        assert session.visual_preference_sheet["variables"]["outfit_direction"]["selection_source"] == "human_select"


def test_runtime_natural_accept_recommended_preserves_source() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        to_visual(runtime, first.session_id)
        response = runtime.resume_session(first.session_id, "发色按推荐")
        session = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert session.visual_preference_sheet["variables"]["hair_color"]["selection_source"] == "human_accept_recommended"


def test_runtime_natural_delegate_and_cancel() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        delegated = runtime.resume_session(first.session_id, "你来决定")
        assert delegated.status == SessionStatus.AWAITING_ART_DIRECTION.value
        second = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        cancelled = runtime.resume_session(second.session_id, "不做了，取消。")
        assert cancelled.status == SessionStatus.CANCELLED.value
        assert runtime.load_session(second.session_id).status == SessionStatus.CANCELLED.value


def test_runtime_regenerate_options_keeps_same_session_and_history() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        old_gate = first.gate["gate_id"]
        response = runtime.resume_session(first.session_id, "这几个我都不喜欢，重新给几个。")
        session = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
        assert response.session_id == first.session_id
        assert response.gate["gate_id"] != old_gate
        record = [item for item in session.audit_log if item.get("event") == "regenerate_options"][-1]
        assert record["user_requested"] is True
        assert record["previous_option_ids"] == record["new_option_ids"]


def test_runtime_wrong_field_is_pending_not_current_gate_selection() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        runtime.resume_session(first.session_id, "B")
        before = runtime.load_session(first.session_id)
        response = runtime.resume_session(first.session_id, "发色我选B")
        after = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_ART_DIRECTION.value
        assert after.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value
        assert after.selected_art_direction is None
        assert after.pending_constraint_updates["hair_color"]["option_id"] == "B"
        assert before.current_gate == after.current_gate


def test_runtime_user_to_ai_natural_mode_switch_keeps_session() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        response = runtime.resume_session(first.session_id, "B")
        switched = runtime.resume_session(first.session_id, "算了，后面都你决定吧。")
        assert response.status == SessionStatus.AWAITING_ART_DIRECTION.value
        assert switched.status == SessionStatus.GENERATION_READY.value
        assert switched.session_id == first.session_id
        assert runtime.load_session(first.session_id).creation_mode == CreationMode.AI_DECIDE.value


def test_runtime_ai_to_user_natural_mode_switch_reopens_visual_gate() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        ready = runtime.create_session("你帮我完整设计。", CreationMode.AI_DECIDE)
        switched = runtime.resume_session(ready.session_id, "等等，我想自己选")
        session = runtime.load_session(ready.session_id)
        assert switched.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert switched.mode == CreationMode.USER_DECIDE.value
        assert session.selected_character_direction is not None
        assert session.selected_art_direction is not None


def test_runtime_explicit_constraints_lock_and_reach_prompt() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session("快速做一个成年女性，粉发，白色连裤袜，裸足，不要裙子，不要高跟鞋。")
        session = runtime.load_session(response.session_id)
        values = session.final_design["visual_preferences"]
        prompt = session.compiled_prompt["prompt"]
        assert response.mode == CreationMode.QUICK.value
        assert values["hair_color"] == "粉发"
        assert values["legwear_family"] == "white opaque tights"
        assert values["footwear_family"] == "barefoot"
        assert session.final_design["explicit_user_constraints"]["negative_constraints"]["forbid_outfit_lower"] == "skirt"
        assert "forbid_outfit_lower" in prompt and "forbid_footwear_family" in prompt


def test_runtime_explicit_hair_is_not_reasked_at_visual_gate() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我设计一个成年女性，粉色长发，先给我几个方向，我来选。", CreationMode.USER_DECIDE)
        runtime.resume_session(first.session_id, "B")
        response = runtime.resume_session(first.session_id, "C")
        assert response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert all(item["variable"] != "hair_color" for item in response.options)


def test_runtime_stale_and_duplicate_guards_survive_natural_parser() -> None:
    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        old_gate = first.gate["gate_id"]
        runtime.resume_session(first.session_id, "B")
        stale = runtime.resume_session(first.session_id, InteractionEvent("stale", first.session_id, old_gate, "SELECT", {"candidate_id": "A"}))
        assert stale.error_code == "STALE_GATE_EVENT"
        session = runtime.load_session(first.session_id)
        duplicate_event = InteractionEvent("duplicate", first.session_id, session.current_gate or "", "SELECT", {"candidate_id": "C"})
        first_response = runtime.resume_session(first.session_id, duplicate_event)
        second_response = runtime.resume_session(first.session_id, duplicate_event)
        assert first_response.to_dict() == second_response.to_dict()
        assert len([line for line in runtime.replay_session(first.session_id)["events"] if line["event_id"] == "duplicate"]) == 1


def test_legacy_session_loads_with_new_pending_constraint_default(tmp_path) -> None:
    session_dir = tmp_path / "legacy"
    session_dir.mkdir()
    (session_dir / "creative_session.json").write_text('{"prompt":"old character","state":"AWAITING_ART_SELECTION"}', encoding="utf-8")
    session = InteractionRuntime(tmp_path).load_session("legacy")
    assert session.pending_constraint_updates == {}


if __name__ == "__main__":
    print("natural language interaction tests: PASS")
