"""Focused regression tests for the persistent three-mode interaction layer."""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.interaction_runtime import (  # noqa: E402
    CreationMode,
    InteractionAction,
    InteractionEvent,
    InteractionRuntime,
    SessionStatus,
)


def _event(runtime: InteractionRuntime, session_id: str, action: str, payload: dict | None = None, *, event_id: str | None = None) -> InteractionEvent:
    session = runtime.load_session(session_id)
    return InteractionEvent(event_id or action.lower(), session_id, session.current_gate or "", action, payload or {})


def _to_visual_gate(runtime: InteractionRuntime, session_id: str) -> None:
    session = runtime.load_session(session_id)
    runtime.resume_session(session_id, InteractionEvent("character-select", session_id, session.current_gate or "", "SELECT", {"candidate_id": "B"}))
    session = runtime.load_session(session_id)
    runtime.resume_session(session_id, InteractionEvent("art-select", session_id, session.current_gate or "", "MIX", {"selections": ["A", "C"]}))


def test_quick_mode_reaches_generation_ready_without_waiting_and_keeps_explicit_hair() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        response = InteractionRuntime(directory).create_session("快速给我来一个粉发成年女性")
        session = InteractionRuntime(directory).load_session(response.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert response.stage == "GENERATION_READY"
        assert session.final_design["visual_preferences"]["hair_color"] == "粉发"
        assert session.final_design["provenance"]["hair_color"] == "explicit_user"
        assert not any(item.get("status") == "WAITING_FOR_USER" for item in session.audit_log)
        assert session.compiled_prompt and "NO_CROSSED_LEGS" not in session.compiled_prompt["prompt"]
        assert "no leg crossover" in session.compiled_prompt["prompt"]


def test_ai_decide_runs_full_exploration_and_records_delegated_ai() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session("你帮我完整设计一个成年女性角色，都交给你")
        session = runtime.load_session(response.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert len(session.character_explore_result) == 4
        assert len(session.art_explore_result) == 4
        sources = [item["resolution"]["decision_source"] for item in session.audit_log if item.get("event") == "gate_resolution"]
        assert sources == ["delegated_ai", "delegated_ai", "delegated_ai"]


def test_user_decide_selection_is_a_resume_event_and_all_recommended_finishes() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我设计一个女角色，我自己选", CreationMode.USER_DECIDE)
        assert first.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
        _to_visual_gate(runtime, first.session_id)
        session = runtime.load_session(first.session_id)
        response = runtime.resume_session(first.session_id, InteractionEvent("visual-all", first.session_id, session.current_gate or "", "USE_ALL_RECOMMENDED", {"overrides": {"hair_color": {"option_id": "B"}, "footwear_family": {"option_id": "C"}}}))
        saved = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert saved.final_design["visual_preferences"]["hair_color"] == "muted rose"
        assert saved.final_design["visual_preferences"]["footwear_family"] == "flat sneakers"
        assert saved.visual_preference_sheet["variables"]["hair_color"]["selection_source"] == "human_select"


def test_partial_delegate_resolves_only_unselected_fields_with_provenance() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("我想自己选一个角色", CreationMode.USER_DECIDE)
        _to_visual_gate(runtime, first.session_id)
        session = runtime.load_session(first.session_id)
        response = runtime.resume_session(first.session_id, InteractionEvent("partial", first.session_id, session.current_gate or "", "PARTIAL_DELEGATE", {"values": {"hair_color": {"option_id": "B"}, "outfit_direction": {"option_id": "C"}, "footwear_family": {"option_id": "B"}}}))
        saved = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert saved.visual_preference_sheet["variables"]["hair_color"]["selection_source"] == "human_select"
        assert saved.visual_preference_sheet["variables"]["eye_color"]["selection_source"] == "delegated_ai"
        assert "eye_color" in saved.delegated_fields


def test_back_invalidates_dependents_but_preserves_history_and_reopens_character_gate() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案，我来选", CreationMode.USER_DECIDE)
        old_character_gate = first.gate["gate_id"]
        runtime.resume_session(first.session_id, InteractionEvent("select-character", first.session_id, old_character_gate, "SELECT", {"candidate_id": "B"}))
        session = runtime.load_session(first.session_id)
        response = runtime.resume_session(first.session_id, InteractionEvent("back", first.session_id, session.current_gate or "", "BACK", {}))
        saved = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
        assert saved.art_explore_result == []
        assert saved.final_design is None and saved.compiled_prompt is None
        assert any(item.get("event") == "rollback_event" for item in saved.audit_log)
        assert saved.interaction_history
        stale = runtime.resume_session(first.session_id, InteractionEvent("old", first.session_id, old_character_gate, "SELECT", {"candidate_id": "A"}))
        assert stale.error_code == "STALE_GATE_EVENT"


def test_mode_switch_to_ai_decide_continues_current_session() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("我来选角色", CreationMode.USER_DECIDE)
        session = runtime.load_session(first.session_id)
        runtime.resume_session(first.session_id, _event(runtime, first.session_id, InteractionAction.SELECT.value, {"candidate_id": "B"}, event_id="select"))
        session = runtime.load_session(first.session_id)
        response = runtime.resume_session(first.session_id, InteractionEvent("switch", first.session_id, session.current_gate or "", "DELEGATE", {"to_mode": "AI_DECIDE", "reason": "后面你决定吧"}))
        saved = runtime.load_session(first.session_id)
        assert response.status == SessionStatus.GENERATION_READY.value
        assert saved.creation_mode == CreationMode.AI_DECIDE.value
        assert any(item.get("type") == "mode_switch" for item in saved.interaction_history)


def test_restart_resume_and_idempotency_do_not_apply_event_twice() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("我自己选", CreationMode.USER_DECIDE)
        session = runtime.load_session(first.session_id)
        event = InteractionEvent("once", first.session_id, session.current_gate or "", "SELECT", {"candidate_id": "B"})
        runtime.resume_session(first.session_id, event)
        restarted = InteractionRuntime(directory)
        saved = restarted.load_session(first.session_id)
        duplicate = restarted.resume_session(first.session_id, event)
        assert saved.status == SessionStatus.AWAITING_ART_DIRECTION.value
        assert duplicate.to_dict() == saved.last_response
        events = restarted.replay_session(first.session_id)["events"]
        assert len([item for item in events if item["event_id"] == "once"]) == 1


def test_ai_decide_can_switch_back_to_user_decide_at_last_recoverable_gate() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        ready = runtime.create_session("你帮我完整设计一个成年女性角色，都交给你", CreationMode.AI_DECIDE)
        response = runtime.switch_mode(ready.session_id, CreationMode.USER_DECIDE, reason="让我选择发色")
        saved = runtime.load_session(ready.session_id)
        assert response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value
        assert saved.creation_mode == CreationMode.USER_DECIDE.value
        assert saved.final_design is None and saved.compiled_prompt is None
        assert (Path(directory) / ready.session_id / "artifacts" / "visual_preference_sheet.json").is_file()


def test_recommendation_is_not_selection_and_invalid_action_does_not_pollute_session() -> None:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("给我几个方案", CreationMode.USER_DECIDE)
        before = runtime.load_session(first.session_id).to_dict()
        assert first.recommended == "A"
        assert first.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
        invalid = runtime.resume_session(first.session_id, InteractionEvent("invalid", first.session_id, first.gate["gate_id"], "SELECT", {"variable": "hair_color", "option_id": "B"}))
        after = runtime.load_session(first.session_id).to_dict()
        assert invalid.error_code == "INVALID_INTERACTION"
        assert after["current_gate"] == before["current_gate"]
        assert after["selected_character_direction"] is None


def test_legacy_artifact_loads_with_ai_decide_default(tmp_path: Path) -> None:
    session_dir = tmp_path / "legacy"
    session_dir.mkdir()
    (session_dir / "creative_session.json").write_text(json.dumps({"prompt": "old character", "state": "AWAITING_ART_SELECTION"}), encoding="utf-8")
    session = InteractionRuntime(tmp_path).load_session("legacy")
    assert session.creation_mode == CreationMode.AI_DECIDE.value
    assert session.status == SessionStatus.AWAITING_ART_DIRECTION.value
    assert session.legacy_artifacts["prompt"] == "old character"


if __name__ == "__main__":
    test_quick_mode_reaches_generation_ready_without_waiting_and_keeps_explicit_hair()
    test_ai_decide_runs_full_exploration_and_records_delegated_ai()
    print("interaction runtime: PASS")
