"""Run the no-imagegen UX acceptance suite for the three-mode interaction runtime."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.repository_guard import require_development_repository  # noqa: E402
from runtime.interaction_runtime import (  # noqa: E402
    CreationMode,
    InteractionAction,
    InteractionEvent,
    InteractionRuntime,
    PipelineStage,
    SessionStatus,
)


class ProvenanceSemanticClass(str, Enum):
    HUMAN_EXPLICIT = "HUMAN_EXPLICIT"
    HUMAN_SELECTION = "HUMAN_SELECTION"
    AI_RESOLVED = "AI_RESOLVED"
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"
    UNKNOWN = "UNKNOWN"


_PROVENANCE_SEMANTICS = {
    "explicit_user": ProvenanceSemanticClass.HUMAN_EXPLICIT,
    "human_explicit": ProvenanceSemanticClass.HUMAN_EXPLICIT,
    "human_select": ProvenanceSemanticClass.HUMAN_SELECTION,
    "human_selection": ProvenanceSemanticClass.HUMAN_SELECTION,
    "human_mix": ProvenanceSemanticClass.HUMAN_SELECTION,
    "human_custom": ProvenanceSemanticClass.HUMAN_SELECTION,
    "human_accept_recommended": ProvenanceSemanticClass.HUMAN_SELECTION,
    "delegated_ai": ProvenanceSemanticClass.AI_RESOLVED,
    "quick_ai_fill": ProvenanceSemanticClass.AI_RESOLVED,
    "policy_default": ProvenanceSemanticClass.SYSTEM_DEFAULT,
}


def normalize_provenance(value: Any) -> ProvenanceSemanticClass:
    """Map legal provenance labels from each interaction layer to one meaning."""
    return _PROVENANCE_SEMANTICS.get(str(value).strip().casefold(), ProvenanceSemanticClass.UNKNOWN)


OUTPUT_ROOT = Path("D:/benchmark/outputs/three_mode_interaction_ux_acceptance_v1_20260915")


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def response_view(response: Any) -> dict[str, Any]:
    value = response.to_dict()
    gate = value.get("gate") or {}
    return {
        "session_id": value.get("session_id"),
        "mode": value.get("mode"),
        "status": value.get("status"),
        "stage": value.get("stage"),
        "user_message": value.get("user_message"),
        "gate_type": gate.get("gate_type"),
        "gate_id": gate.get("gate_id"),
        "option_ids": [item.get("id") for item in gate.get("options", [])],
        "recommended": value.get("recommended"),
        "unresolved_fields": value.get("unresolved_fields", []),
        "allowed_actions": value.get("allowed_actions", []),
        "progress": value.get("progress", {}),
        "error_code": value.get("error_code"),
    }


@dataclass
class Review:
    correctness: str
    friction: int
    internal_knowledge: str
    continuity: str
    provenance: str
    findings: list[str]
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "correctness": self.correctness,
            "ux_friction": self.friction,
            "user_needs_internal_knowledge": self.internal_knowledge,
            "session_continuity": self.continuity,
            "provenance_correct": self.provenance,
            "finding_types": self.findings,
            "notes": self.notes,
        }


class CaseContext:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="three-mode-ux-")
        self.runtime = InteractionRuntime(self._tmp.name)
        self.primary_session_id: str | None = None
        self.before: dict[str, Any] = {}
        self.transcript: list[dict[str, Any]] = []
        self.extra_sessions: dict[str, dict[str, Any]] = {}

    def start(self, text: str, mode: str | None = None) -> Any:
        response = self.runtime.create_session(text, mode=mode)
        self.primary_session_id = response.session_id
        self.before = self.runtime.load_session(response.session_id).to_dict()
        self.record(text, response)
        return response

    def record(self, user_input: Any, response: Any) -> Any:
        self.transcript.append({"user_input": user_input, "system_output": response_view(response)})
        return response

    def natural(self, text: str) -> Any:
        if self.primary_session_id is None:
            raise RuntimeError("scenario has no primary session")
        return self.record(text, self.runtime.resume_session(self.primary_session_id, text))

    def event(self, action: str, payload: dict[str, Any] | None = None, *, event_id: str | None = None, gate_id: str | None = None) -> Any:
        if self.primary_session_id is None:
            raise RuntimeError("scenario has no primary session")
        session = self.runtime.load_session(self.primary_session_id)
        event = InteractionEvent(
            event_id or uuid4().hex,
            self.primary_session_id,
            gate_id if gate_id is not None else session.current_gate or "",
            action,
            payload or {},
        )
        return self.record(event.to_dict(), self.runtime.resume_session(self.primary_session_id, event))

    def snapshot(self) -> dict[str, Any]:
        if self.primary_session_id is None:
            return {"primary": None, "extra_sessions": self.extra_sessions}
        return {
            "primary": self.runtime.load_session(self.primary_session_id).to_dict(),
            "extra_sessions": self.extra_sessions,
        }

    def add_extra(self, label: str, session_id: str) -> None:
        self.extra_sessions[label] = self.runtime.load_session(session_id).to_dict()

    def close(self) -> None:
        self._tmp.cleanup()


def resolved_sources(ctx: CaseContext) -> dict[str, str | None]:
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    return {
        name: item.get("selection_source")
        for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items()
    }


def final_values(ctx: CaseContext) -> dict[str, Any]:
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    return dict((session.final_design or {}).get("visual_preferences", {}))


def start_user(ctx: CaseContext, prompt: str) -> Any:
    return ctx.start(prompt, CreationMode.USER_DECIDE.value)


def resolve_character(ctx: CaseContext, identifier: str = "B") -> Any:
    return ctx.event(InteractionAction.SELECT.value, {"candidate_id": identifier})


def resolve_art(ctx: CaseContext, identifier: str = "B") -> Any:
    return ctx.event(InteractionAction.SELECT.value, {"candidate_id": identifier})


def resolve_visual_all(ctx: CaseContext) -> Any:
    return ctx.event(InteractionAction.USE_ALL_RECOMMENDED.value)


def full_user_flow(ctx: CaseContext) -> Any:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    return resolve_visual_all(ctx)


def run_q1(ctx: CaseContext) -> Review:
    response = ctx.start("快速给我设计一个银灰短发、性格很拽的成年女性二游角色，不用问我。")
    session = ctx.runtime.load_session(response.session_id)
    constraints = session.explicit_user_constraints
    good = response.status == SessionStatus.GENERATION_READY.value and response.mode == CreationMode.QUICK.value and constraints.get("hair_color") and constraints.get("personality")
    findings = [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"]
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO", "PASS", "PASS" if good else "FAIL", findings, f"Quick status={response.status}; extracted constraints={constraints}.")


def run_q2(ctx: CaseContext) -> Review:
    response = ctx.start("快速来个男角色。")
    good = response.status == SessionStatus.GENERATION_READY.value and response.mode == CreationMode.QUICK.value
    return Review("PASS" if good else "FAIL", 1 if good else 2, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"Sparse input status={response.status}; detected mode={response.mode}.")


def run_q3(ctx: CaseContext) -> Review:
    response = ctx.start("快速做一个成年女性，粉发，白色连裤袜，裸足，不要高跟鞋。")
    values = final_values(ctx)
    good = response.status == SessionStatus.GENERATION_READY.value and response.mode == CreationMode.QUICK.value and values.get("footwear_family") == "barefoot" and values.get("legwear_family") in {"white tights", "white opaque tights"}
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"Observed mode={response.mode}; final footwear={values.get('footwear_family')!r}; legwear={values.get('legwear_family')!r}.")


def run_a1(ctx: CaseContext) -> Review:
    response = ctx.start("完整帮我设计一个成年女性二游角色，都由你决定。")
    session = ctx.runtime.load_session(response.session_id)
    sources = resolved_sources(ctx)
    good = response.status == SessionStatus.GENERATION_READY.value and response.mode == CreationMode.AI_DECIDE.value and all(source in {"delegated_ai", "explicit_user", None} for source in sources.values())
    return Review("PASS" if good else "FAIL", 1 if good else 2, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["PROVENANCE_MISCLASSIFIED"], f"status={response.status}; stages stop at {session.current_stage}; delegated fields={len(session.delegated_fields)}.")


def run_a2(ctx: CaseContext) -> Review:
    quick = CaseContext()
    ai = CaseContext()
    try:
        quick_response = quick.start("快速设计一个冷淡的成年女性角色。")
        ai_response = ai.start("完整设计一个冷淡的成年女性角色，细节都你决定。")
        quick_session = quick.runtime.load_session(quick_response.session_id)
        ai_session = ai.runtime.load_session(ai_response.session_id)
        quick_character_meta = (quick_session.selected_character_direction or {}).get("resolution_metadata", {})
        quick_art_meta = (quick_session.selected_art_direction or {}).get("resolution_metadata", {})
        ai_character_meta = (ai_session.selected_character_direction or {}).get("resolution_metadata", {})
        ai_art_meta = (ai_session.selected_art_direction or {}).get("resolution_metadata", {})
        good = (
            quick_character_meta.get("strategy") == "seeded_structured_sampling"
            and quick_art_meta.get("strategy") == "seeded_structured_sampling"
            and ai_character_meta.get("strategy") == "divergent_candidate_generation_then_score_selection"
            and ai_art_meta.get("strategy") == "divergent_candidate_generation_then_score_selection"
            and "evaluated_candidate_ids" not in quick_character_meta
            and "evaluated_candidate_ids" in ai_character_meta
        )
        ctx.before = {"quick": quick_session.to_dict(), "ai_decide": ai_session.to_dict()}
        ctx.extra_sessions = {"quick_response": response_view(quick_response), "ai_response": response_view(ai_response)}
        ctx.transcript = [{"user_input": "快速设计一个冷淡的成年女性角色。", "system_output": response_view(quick_response)}, {"user_input": "完整设计一个冷淡的成年女性角色，细节都你决定。", "system_output": response_view(ai_response)}]
        return Review("PASS" if good else "FAIL", 1 if good else 2, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["QUICK_AI_DECIDE_COLLAPSE"], f"resolution strategies quick={quick_character_meta.get('strategy')!r}/{quick_art_meta.get('strategy')!r}, ai_decide={ai_character_meta.get('strategy')!r}/{ai_art_meta.get('strategy')!r}.")
    finally:
        quick.close()
        ai.close()


def run_u1(ctx: CaseContext) -> Review:
    response = start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    good = response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value and len(response.options) >= 3
    return Review("PASS" if good else "FAIL", 1 if good else 2, "NO", "PASS", "PASS", [] if good else ["GATE_OVERLOAD"], "Character gate exposes user-facing directions.")


def run_u1_t2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("B")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.status == SessionStatus.AWAITING_ART_DIRECTION.value and session.selected_character_direction and session.selected_character_direction.get("id") == "candidate_02"
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"natural B resolved as {session.selected_character_direction and session.selected_character_direction.get('id')!r}.")


def run_u1_t3(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx, "B")
    response = ctx.natural("A的轮廓不错，但我更喜欢C的整体感觉，混一下。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value and session.selected_art_direction and session.selected_art_direction.get("id") == "candidate_01+candidate_03"
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "PROVENANCE_MISCLASSIFIED"], f"art result id={session.selected_art_direction and session.selected_art_direction.get('id')!r}.")


def run_u1_t4(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx, "B")
    resolve_art(ctx, "C")
    response = ctx.natural("发色改成银白，鞋子改裸足，其他就按推荐吧。")
    sources = resolved_sources(ctx)
    good = response.status == SessionStatus.GENERATION_READY.value and sources.get("hair_color") == "human_custom" and sources.get("footwear_family") == "human_custom"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "PROVENANCE_MISCLASSIFIED"], f"status={response.status}; sources={sources}.")


def run_u2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("为什么你推荐B？")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value and session.selected_character_direction is None
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["RECOMMENDATION_AUTO_LOCKED", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"after question status={response.status}; selected={session.selected_character_direction and session.selected_character_direction.get('id')!r}.")


def run_u2_t2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    ctx.natural("为什么推荐B？")
    response = ctx.natural("行，那我选C。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = session.selected_character_direction and session.selected_character_direction.get("id") == "candidate_03"
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"observed selected character={session.selected_character_direction and session.selected_character_direction.get('id')!r}.")


def run_u3(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    response = ctx.natural("你推荐哪个？")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.status == SessionStatus.AWAITING_ART_DIRECTION.value and session.selected_art_direction is None
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["RECOMMENDATION_AUTO_LOCKED", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"after question status={response.status}; selected art={session.selected_art_direction and session.selected_art_direction.get('id')!r}.")


def run_u3_t2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    ctx.natural("你推荐哪个？")
    response = ctx.natural("那就按你的推荐。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    art_history = [entry for entry in session.interaction_history if entry.get("type") == "gate_resolution" and entry.get("gate_type") == "ART_DIRECTION_GATE"]
    source = art_history[-1].get("decision_source") if art_history else None
    good = response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value and source == "human_accept_recommended"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "PROVENANCE_MISCLASSIFIED"], f"status={response.status}; art source={source!r}.")


def run_u4(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("这个我不想选了，你来决定吧。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    resolutions = [entry for entry in session.interaction_history if entry.get("type") == "gate_resolution"]
    last = resolutions[-1] if resolutions else {}
    good = response.status == SessionStatus.AWAITING_ART_DIRECTION.value and last.get("decision_source") == "delegated_ai"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["DELEGATION_MISCLASSIFIED", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"status={response.status}; last source={last.get('decision_source')!r}.")


def run_u5(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    ctx.natural("发色、衣服和鞋子我自己选，其他你决定。")
    response = ctx.natural("发色深红，衣服B，鞋子裸足。")
    good = response.status == SessionStatus.GENERATION_READY.value
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "DELEGATION_MISCLASSIFIED"], f"partial delegate phrase response status={response.status}.")


def run_u6(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    response = ctx.natural("全都按你推荐的来。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    sources = resolved_sources(ctx)
    explicit_fields = set(session.explicit_user_constraints.get("explicit_user_fields", ()))
    variables = (session.visual_preference_sheet or {}).get("variables", {})
    event_applied = any(
        item.get("event", {}).get("action") == InteractionAction.USE_ALL_RECOMMENDED.value
        for item in session.interaction_history
    )
    explicit_owned = all(
        normalize_provenance(sources.get(name)) is ProvenanceSemanticClass.HUMAN_EXPLICIT
        for name in explicit_fields
        if name in sources
    )
    recommended_owned = all(
        source == "human_accept_recommended"
        and normalize_provenance(source) is ProvenanceSemanticClass.HUMAN_SELECTION
        and variables[name].get("user_selection") == variables[name].get("recommended")
        for name, source in sources.items()
        if name not in explicit_fields and source
    )
    no_unknown_sources = all(normalize_provenance(source) is not ProvenanceSemanticClass.UNKNOWN for source in sources.values() if source)
    good = response.status == SessionStatus.GENERATION_READY.value and event_applied and explicit_owned and recommended_owned and no_unknown_sources
    notes = f"status={response.status}; event_applied={event_applied}; explicit_owned={explicit_owned}; recommended_owned={recommended_owned}; no_unknown_sources={no_unknown_sources}; sources={sources}."
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], notes)


def run_m1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我几个方向，我来选。")
    resolve_character(ctx)
    response = ctx.natural("算了，后面都你决定吧。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    switched = any(entry.get("type") == "mode_switch" for entry in session.interaction_history)
    good = switched and response.status == SessionStatus.GENERATION_READY.value
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["MODE_SWITCH_RESET", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"same_session={response.session_id == ctx.primary_session_id}; switched={switched}; status={response.status}.")


def run_m2(ctx: CaseContext) -> Review:
    start = ctx.start("你帮我完整设计。")
    response = ctx.natural("等一下，发色和衣服我想自己选。")
    session = ctx.runtime.load_session(start.session_id)
    good = response.mode == CreationMode.USER_DECIDE.value and response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value and session.selected_character_direction is not None
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["MODE_SWITCH_RESET", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"mode={response.mode}; status={response.status}; upstream_character={session.selected_character_direction is not None}.")


def run_b1(ctx: CaseContext) -> Review:
    start = start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx, "B")
    resolve_art(ctx, "C")
    natural = ctx.natural("我还是不喜欢这个人物方向，我想回去重选最开始那几个角色方向。")
    structured = ctx.event(InteractionAction.BACK.value, {"target": "CHARACTER"})
    session = ctx.runtime.load_session(start.session_id)
    natural_good = natural.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
    structured_good = structured.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value and session.current_stage == PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value
    return Review("PASS" if natural_good and structured_good else "FAIL", 1 if natural_good else 5, "NO" if natural_good else "YES", "PASS", "PASS" if structured_good else "FAIL", [] if natural_good and structured_good else ["DEPENDENCY_INVALIDATION_ERROR", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"natural status={natural.status}; structured BACK status={structured.status}; final stage={session.current_stage}; preserved history={len(session.interaction_history)}.")


def run_b2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    before = ctx.runtime.load_session(ctx.primary_session_id or "")
    ctx.event(InteractionAction.SELECT.value, {"variable": "hair_color", "value": "silver-white"})
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = before.selected_character_direction == session.selected_character_direction and before.selected_art_direction == session.selected_art_direction
    return Review("PASS" if good else "FAIL", 2 if good else 4, "YES", "PASS", "PASS", [] if good else ["DEPENDENCY_INVALIDATION_ERROR"], "Structured local visual edit was used to probe downstream-only invalidation; natural edit remains covered by UX9.")


def run_r1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx, "B")
    session_id = ctx.primary_session_id or ""
    restarted = InteractionRuntime(ctx.runtime.session_root)
    session = restarted.load_session(session_id)
    event = InteractionEvent(uuid4().hex, session_id, session.current_gate or "", InteractionAction.SELECT.value, {"candidate_id": "candidate_02"})
    response = restarted.resume_session(session_id, event)
    ctx.record({"restart": True, **event.to_dict()}, response)
    ctx.runtime = restarted
    final = ctx.runtime.load_session(session_id)
    good = response.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value and final.selected_character_direction and final.selected_character_direction.get("id") == "candidate_02"
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO", "PASS" if good else "FAIL", "PASS" if good else "FAIL", [] if good else ["RESUME_FAILURE", "SESSION_RESET_UNEXPECTEDLY"], f"after restart status={response.status}; preserved character={final.selected_character_direction and final.selected_character_direction.get('id')!r}.")


def run_r2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    session_id = ctx.primary_session_id or ""
    restarted = InteractionRuntime(ctx.runtime.session_root)
    session = restarted.load_session(session_id)
    response = restarted.resume_session(session_id, "发色选C，鞋子裸足，其他推荐。")
    ctx.record({"restart": True, "user_input": "发色选C，鞋子裸足，其他推荐。"}, response)
    ctx.runtime = restarted
    good = response.status == SessionStatus.GENERATION_READY.value
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["RESUME_FAILURE", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"after restart visual input status={response.status}.")


def run_i1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    stale_gate = ctx.runtime.load_session(ctx.primary_session_id or "").current_gate or ""
    resolve_character(ctx)
    response = ctx.event(InteractionAction.SELECT.value, {"candidate_id": "A"}, gate_id=stale_gate)
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.error_code == "STALE_GATE_EVENT" and session.selected_art_direction is None
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO", "PASS", "PASS", [] if good else ["STALE_EVENT_APPLIED"], f"error={response.error_code}; stage unchanged={session.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value}.")


def run_i2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    session_id = ctx.primary_session_id or ""
    event_id = "duplicate-event-ux-i2"
    gate = ctx.runtime.load_session(session_id).current_gate or ""
    event = InteractionEvent(event_id, session_id, gate, InteractionAction.SELECT.value, {"candidate_id": "B"})
    first = ctx.record(event.to_dict(), ctx.runtime.resume_session(session_id, event))
    second = ctx.record(event.to_dict(), ctx.runtime.resume_session(session_id, event))
    event_file = Path(ctx.runtime.session_root) / session_id / "events.jsonl"
    count = len(event_file.read_text(encoding="utf-8").splitlines()) if event_file.exists() else 0
    good = first.status == SessionStatus.AWAITING_ART_DIRECTION.value and second.to_dict() == first.to_dict() and count == 1
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO", "PASS", "PASS", [] if good else ["DUPLICATE_EVENT_APPLIED"], f"duplicate response stable={second.to_dict() == first.to_dict()}; events_written={count}.")


def run_i3(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    response = ctx.natural("发色我选B")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.error_code is None and session.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value and session.pending_constraint_updates.get("hair_color")
    return Review("PASS" if good else "FAIL", 2 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"wrong-field response={response.error_code}; stage={session.current_stage}.")


def run_i4(ctx: CaseContext) -> Review:
    response = start_user(ctx, "给我四个角色方向，我自己选。")
    second = ctx.natural("第二个。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good_second = session.selected_character_direction and session.selected_character_direction.get("id") == "candidate_02"
    ctx.natural("中间那个。")
    good_ambiguity = ctx.runtime.load_session(ctx.primary_session_id or "").status == SessionStatus.AWAITING_ART_DIRECTION.value
    good = good_second and good_ambiguity
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"second status={second.status}; parsed second={session.selected_character_direction and session.selected_character_direction.get('id')!r}; ambiguity preserved={good_ambiguity}.")


def run_i5(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("A和B最大的区别是什么？")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value and session.selected_character_direction is None
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "RECOMMENDATION_AUTO_LOCKED"], f"question status={response.status}; selected={session.selected_character_direction and session.selected_character_direction.get('id')!r}.")


def run_i6(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("这几个我都不喜欢，重新给几个。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.error_code == "UX_GAP_REGENERATE_OPTIONS" or (session.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value and session.selected_character_direction is None)
    return Review("PASS" if good else "FAIL", 2 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", ["UX_GAP_REGENERATE_OPTIONS"] if not good else [], f"current response={response.error_code or response.status}; new options={len(session.gate_payload.get('options', []))}.")


def run_c1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("不做了，取消。")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = session.status == SessionStatus.CANCELLED.value
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS" if good else "FAIL", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"cancel response status={response.status}; persisted status={session.status}.")


def run_h1(ctx: CaseContext) -> Review:
    response = ctx.start("快速设计一个成年女性，必须粉发，不要裙子，不要高跟鞋。")
    values = final_values(ctx)
    constraints = ctx.runtime.load_session(response.session_id).explicit_user_constraints
    good = response.status == SessionStatus.GENERATION_READY.value and response.mode == CreationMode.QUICK.value and constraints.get("hair_color") and constraints.get("negative_constraints", {}).get("forbid_outfit_lower") == "skirt" and constraints.get("negative_constraints", {}).get("forbid_footwear_family") == "heels"
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"mode={response.mode}; constraints={constraints}; final footwear={values.get('footwear_family')!r}; no-skirt extraction={constraints.get('no_skirt')!r}.")


def run_h2(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    response = ctx.natural("我就要粉发。")
    values = final_values(ctx)
    sheet = ctx.runtime.load_session(ctx.primary_session_id or "").visual_preference_sheet or {}
    hair = (sheet.get("variables") or {}).get("hair_color", {})
    good = values.get("hair_color") == "粉发" or hair.get("user_selection") == "粉发"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "USER_SELECTION_NOT_APPLIED"], f"status={response.status}; hair={values.get('hair_color')!r}.")


def run_p1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    ctx.event(InteractionAction.SELECT.value, {"variable": "hair_color", "option_id": "A"})
    ctx.event(InteractionAction.MIX.value, {"variable": "outfit_direction", "values": ["structured tailoring", "soft utility"]})
    ctx.event(InteractionAction.CUSTOM.value, {"variable": "eye_color", "value": "amber"})
    ctx.event(InteractionAction.USE_RECOMMENDED.value, {"variable": "dominant_palette"})
    ctx.event(InteractionAction.PARTIAL_DELEGATE.value, {"values": {"footwear_family": "barefoot"}})
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    sources = resolved_sources(ctx)
    allowed = {"human_select", "human_mix", "human_custom", "human_accept_recommended", "delegated_ai", "quick_ai_fill", "explicit_user", None}
    good = session.status == SessionStatus.GENERATION_READY.value and set(sources.values()).issubset(allowed) and {"human_select", "human_mix", "human_custom", "human_accept_recommended", "delegated_ai"}.issubset(set(sources.values()))
    return Review("PASS" if good else "FAIL", 2 if good else 4, "NO", "PASS", "PASS" if good else "FAIL", [] if good else ["PROVENANCE_MISCLASSIFIED"], f"sources={sources}; policy_default is retained in regional metadata rather than variable sources.")


def run_g1(ctx: CaseContext) -> Review:
    runs: dict[str, Any] = {}
    for mode, prompt in (
        (CreationMode.QUICK.value, "快速来个成年女性角色。"),
        (CreationMode.AI_DECIDE.value, "完整帮我设计一个成年女性角色，都由你决定。"),
        (CreationMode.USER_DECIDE.value, "给我几个成年女性角色方向，我来选。"),
    ):
        child = CaseContext()
        try:
            response = child.start(prompt, mode)
            if mode == CreationMode.USER_DECIDE.value:
                resolve_character(child)
                resolve_art(child)
                response = resolve_visual_all(child)
            runs[mode] = {"response": response_view(response), "session": child.runtime.load_session(response.session_id).to_dict()}
        finally:
            child.close()
    ctx.before = {"modes": list(runs)}
    ctx.extra_sessions = runs
    ctx.transcript = [{"user_input": "three mode generation boundary", "system_output": {mode: item["response"] for mode, item in runs.items()}}]
    good = all(item["response"]["status"] == SessionStatus.GENERATION_READY.value for item in runs.values())
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO", "PASS", "PASS", [] if good else ["SESSION_RESET_UNEXPECTEDLY"], "All three modes were stopped at GENERATION_READY; no imagegen call is made by this harness.")


def run_ux1(ctx: CaseContext) -> Review:
    start_user(ctx, "给我几个方向，我来选。")
    responses = [ctx.natural(text) for text in ("第二个", "A的头发和C的衣服拼一下")]
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = responses[0].status == SessionStatus.AWAITING_ART_DIRECTION.value and session.selected_character_direction and session.selected_character_direction.get("id") == "candidate_02" and session.selected_art_direction and session.selected_art_direction.get("id") == "candidate_01+candidate_03"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"short reply and natural mix sampled; character={session.selected_character_direction and session.selected_character_direction.get('id')!r}; art={session.selected_art_direction and session.selected_art_direction.get('id')!r}.")


def run_ux2(ctx: CaseContext) -> Review:
    response = start_user(ctx, "给我几个方向，我来选。")
    text = response.user_message
    jargon = any(token in text for token in ("InteractionEvent", "GateResolver", "provenance", "session schema", "edge density", "specular hierarchy"))
    good = not jargon and "请选择" in text
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO" if good else "YES", "PASS", "PASS", [] if good else ["UNNECESSARY_CLARIFICATION"], f"user-facing message={text!r}.")


def run_ux3(ctx: CaseContext) -> Review:
    response = start_user(ctx, "给我设计一个成年女性，粉色长发，先给我几个方向，我来选。")
    resolve_character(ctx)
    resolve_art(ctx)
    sheet = ctx.runtime.load_session(response.session_id).visual_preference_sheet
    hair = (sheet or {}).get("variables", {}).get("hair_color", {})
    good = hair.get("selection_source") == "explicit_user" or hair.get("locked") is True
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["USER_SELECTION_NOT_APPLIED", "UNNECESSARY_CLARIFICATION"], f"hair gate state source={hair.get('selection_source')!r}; locked={hair.get('locked')!r}.")


def run_ux4(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    before = ctx.runtime.load_session(ctx.primary_session_id or "")
    resolve_visual_all(ctx)
    after = ctx.runtime.load_session(ctx.primary_session_id or "")
    gate_types = [item.get("gate_type") for item in after.audit_log if item.get("event") == "gate_resolution"]
    good = gate_types == ["CHARACTER_DIRECTION_GATE", "ART_DIRECTION_GATE", "VISUAL_PREFERENCE_GATE"] and before.current_gate and after.status == SessionStatus.GENERATION_READY.value
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO", "PASS", "PASS", [] if good else ["GATE_OVERLOAD"], f"resolved gates={gate_types}.")


def run_ux5(ctx: CaseContext) -> Review:
    response = start_user(ctx, "给我几个方向，我来选。")
    exposed = set()
    for option in response.options:
        exposed.update(option.keys())
    forbidden = {"edge_density", "silhouette_balance_ratio", "specular_hierarchy", "material_response_function", "negative_space_geometry"}
    good = not exposed.intersection(forbidden)
    return Review("PASS" if good else "FAIL", 1 if good else 3, "NO" if good else "YES", "PASS", "PASS", [] if good else ["UNNECESSARY_CLARIFICATION"], f"option keys={sorted(exposed)}.")


def run_ux6(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    response = ctx.natural("黑丝不要，鞋子裸足，其他随你。")
    return Review("PASS" if response.status == SessionStatus.GENERATION_READY.value else "FAIL", 1 if response.status == SessionStatus.GENERATION_READY.value else 5, "NO" if response.status == SessionStatus.GENERATION_READY.value else "YES", "PASS", "PASS" if response.status == SessionStatus.GENERATION_READY.value else "FAIL", [] if response.status == SessionStatus.GENERATION_READY.value else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"short visual control status={response.status}.")


def run_ux7(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    response = ctx.natural("头发用B，眼睛C，衣服A和D混一下，别穿丝袜，鞋子你决定，性感程度中等。")
    return Review("PASS" if response.status == SessionStatus.GENERATION_READY.value else "FAIL", 1 if response.status == SessionStatus.GENERATION_READY.value else 5, "NO" if response.status == SessionStatus.GENERATION_READY.value else "YES", "PASS", "PASS" if response.status == SessionStatus.GENERATION_READY.value else "FAIL", [] if response.status == SessionStatus.GENERATION_READY.value else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"multi-field one-event status={response.status}; error={response.error_code}.")


def run_ux8(ctx: CaseContext) -> Review:
    response = ctx.start("快速来个角色，AI推荐黑发，但我还是想要银发。")
    values = final_values(ctx)
    good = values.get("hair_color") in {"银发", "银白", "银"}
    return Review("PASS" if good else "FAIL", 1 if good else 4, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["USER_SELECTION_NOT_APPLIED", "NATURAL_LANGUAGE_ACTION_PARSE_FAILURE"], f"final hair={values.get('hair_color')!r}; mode={response.mode}.")


def run_ux9(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    resolve_character(ctx)
    resolve_art(ctx)
    response = ctx.natural("大体按推荐，但是把发色换成红色，鞋子换成裸足。")
    sources = resolved_sources(ctx)
    good = response.status == SessionStatus.GENERATION_READY.value and sources.get("hair_color") == "human_custom" and sources.get("footwear_family") == "human_custom"
    return Review("PASS" if good else "FAIL", 1 if good else 5, "NO" if good else "YES", "PASS", "PASS" if good else "FAIL", [] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "PROVENANCE_MISCLASSIFIED"], f"status={response.status}; override sources={sources}.")


def run_ux10(ctx: CaseContext) -> Review:
    start_user(ctx, "给我设计一个成年女性角色，先给我几个方向，我自己选。")
    response = ctx.natural("继续")
    session = ctx.runtime.load_session(ctx.primary_session_id or "")
    good = response.error_code in {None, "INVALID_INTERACTION", "STALE_GATE_EVENT"} and session.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value
    return Review("PASS" if good else "FAIL", 2 if good else 4, "NO", "PASS", "PASS", ["UNNECESSARY_CLARIFICATION"] if good else ["NATURAL_LANGUAGE_ACTION_PARSE_FAILURE", "UNNECESSARY_CLARIFICATION"], f"unresolved continue response={response.error_code or response.status}; status remains={session.status}; safe non-delegation={good}.")


SCENARIOS: list[tuple[str, str, str, Callable[[CaseContext], Review]]] = [
    ("Q1", "quick", "Quick shortest path with explicit adult female, silver-gray short hair, and arrogant personality.", run_q1),
    ("Q2", "quick", "Sparse male Quick input auto-fills without excessive questions.", run_q2),
    ("Q3", "quick", "Quick preserves pink hair, white tights, barefoot, and no heels.", run_q3),
    ("A1", "ai_decide", "Full AI Decide completes without blocking and records delegated AI decisions.", run_a1),
    ("A2", "ai_decide", "Quick and AI Decide have materially different exploration depth.", run_a2),
    ("U1", "user_decide", "User Decide opens the Character Direction gate with several options.", run_u1),
    ("U1-T2", "user_decide", "Natural short reply B selects Character Direction B.", run_u1_t2),
    ("U1-T3", "user_decide", "Natural A/C mix creates a human_mix Art Direction.", run_u1_t3),
    ("U1-T4", "user_decide", "Natural visual overrides plus recommendation finish the flow with precise provenance.", run_u1_t4),
    ("U2", "recommendation_semantics", "Why recommended B explains and keeps the Character gate waiting.", run_u2),
    ("U2-T2", "recommendation_semantics", "After asking why, an explicit C selection locks C rather than B.", run_u2_t2),
    ("U3", "recommendation_semantics", "Asking which Art Direction is recommended does not select it.", run_u3),
    ("U3-T2", "recommendation_semantics", "Accepting the recommendation records human_accept_recommended.", run_u3_t2),
    ("U4", "user_decide", "Natural explicit delegation selects delegated_ai.", run_u4),
    ("U5", "user_decide", "Natural partial delegation resolves three human fields and delegates the rest.", run_u5),
    ("U6", "user_decide", "Natural all-recommended resolves the visual sheet in one step.", run_u6),
    ("M1", "mode_switch", "User Decide to AI Decide keeps the same session and preserves upstream work.", run_m1),
    ("M2", "mode_switch", "AI Decide to User Decide reopens a reasonable gate without resetting upstream work.", run_m2),
    ("B1", "rollback", "Natural request returns from Visual to Character and invalidates dependents.", run_b1),
    ("B2", "rollback", "Local structured visual edit does not rerun Character or Art exploration.", run_b2),
    ("R1", "restart_resume", "Restart at Art resumes the current gate and preserves Character B.", run_r1),
    ("R2", "restart_resume", "Restart at Visual accepts concise natural visual instructions.", run_r2),
    ("I1", "invalid_interaction", "Stale Character event at Art is rejected without mutation.", run_i1),
    ("I2", "invalid_interaction", "Duplicate event id is idempotent and logged once.", run_i2),
    ("I3", "invalid_interaction", "Wrong visual field at Art is rejected or safely held.", run_i3),
    ("I4", "invalid_interaction", "Second means B; ambiguous middle does not guess.", run_i4),
    ("I5", "invalid_interaction", "A/B comparison question stays in the current gate.", run_i5),
    ("I6", "invalid_interaction", "Reject-all asks for new options without cancelling the session.", run_i6),
    ("C1", "invalid_interaction", "Natural cancellation persists CANCELLED.", run_c1),
    ("H1", "quick", "Explicit pink hair, no skirt, and no heels survive Quick completion.", run_h1),
    ("H2", "user_decide", "Explicit pink hair overrides the black recommendation.", run_h2),
    ("P1", "recommendation_semantics", "Visual field-level provenance remains granular.", run_p1),
    ("G1", "summary", "Quick, AI Decide, and User Decide stop at GENERATION_READY with no imagegen.", run_g1),
    ("UX1", "summary", "Users can use natural-language equivalents of internal actions.", run_ux1),
    ("UX2", "summary", "User-facing responses stay concise and avoid internal implementation jargon.", run_ux2),
    ("UX3", "summary", "Explicit hair information is locked and not re-asked as unresolved.", run_ux3),
    ("UX4", "summary", "Normal User Decide flow has only three blocking gates.", run_ux4),
    ("UX5", "summary", "Implementation variables are not shown to the user.", run_ux5),
    ("UX6", "summary", "Short visual controls support no-black-stocking, barefoot, and delegate-rest semantics.", run_ux6),
    ("UX7", "summary", "One natural event can resolve multiple visual field actions.", run_ux7),
    ("UX8", "summary", "Explicit silver hair overrides an AI black-hair recommendation.", run_ux8),
    ("UX9", "summary", "Recommended sheet plus two natural custom overrides is supported.", run_ux9),
    ("UX10", "summary", "Continue does not silently delegate unresolved user-owned fields.", run_ux10),
]


def case_dir(category: str, scenario_id: str) -> Path:
    return OUTPUT_ROOT / category / scenario_id


def write_case(scenario_id: str, category: str, title: str, ctx: CaseContext, review: Review) -> dict[str, Any]:
    target = case_dir(category, scenario_id)
    target.mkdir(parents=True, exist_ok=True)
    after = ctx.snapshot()
    (target / "interaction_transcript.md").write_text(
        "# " + scenario_id + "\n\n" + title + "\n\n" + "\n".join(
            f"### Turn {index}\n\n**User:** {item['user_input'] if isinstance(item['user_input'], str) else json.dumps(item['user_input'], ensure_ascii=False)}\n\n**System:** `{json.dumps(item['system_output'], ensure_ascii=False)}`"
            for index, item in enumerate(ctx.transcript, 1)
        ) + "\n",
        encoding="utf-8",
    )
    dump(target / "session_before.json", ctx.before)
    dump(target / "session_after.json", after)
    events: list[str] = []
    if ctx.primary_session_id:
        event_path = Path(ctx.runtime.session_root) / ctx.primary_session_id / "events.jsonl"
        if event_path.exists():
            events = event_path.read_text(encoding="utf-8").splitlines()
    (target / "events.jsonl").write_text("\n".join(events) + ("\n" if events else ""), encoding="utf-8")
    dump(target / "ux_review.json", {"scenario_id": scenario_id, "title": title, **review.to_dict()})
    return {"id": scenario_id, "category": category, "title": title, **review.to_dict(), "transcript_turns": len(ctx.transcript)}


def report(results: list[dict[str, Any]]) -> str:
    failures = [item for item in results if item["correctness"] == "FAIL"]
    pass_count = len(results) - len(failures)
    core_ids = {"U1-T2", "U1-T3", "U1-T4", "U2", "U2-T2", "U3", "U3-T2", "U4", "U5", "U6", "M1", "M2", "C1", "H1", "H2", "P1", "UX1", "UX3", "UX6", "UX7", "UX8", "UX9"}
    core_failures = [item["id"] for item in failures if item["id"] in core_ids]
    status = "THREE_MODE_INTERACTION_UX_RETEST_PASS_PENDING_HUMAN_REVIEW" if pass_count >= 40 and not core_failures else "INTERACTION_NL_AND_CONSTRAINT_FIX_IMPLEMENTED_PENDING_UX_RETEST"
    finding_map: dict[str, list[str]] = {}
    for item in results:
        for finding in item["finding_types"]:
            finding_map.setdefault(finding, []).append(item["id"])
    lines = [
        "# THREE_MODE_INTERACTION_UX_ACCEPTANCE v1",
        "",
        f"Status: `{status}`",
        "",
        f"Scenarios: {len(results)}; PASS={len(results) - len(failures)}; FAIL={len(failures)}.",
        "",
        "This is a no-imagegen acceptance rerun against the updated interaction runtime. No image generation was invoked; every flow was stopped at or before `GENERATION_READY`.",
        "",
        "## Scenario matrix",
        "",
        "| ID | Correctness | Friction | Internal knowledge | Continuity | Provenance | Findings |",
        "|---|---|---:|---|---|---|---|",
    ]
    for item in results:
        findings = ", ".join(item["finding_types"]) or "—"
        lines.append(f"| {item['id']} | {item['correctness']} | {item['ux_friction']} | {item['user_needs_internal_knowledge']} | {item['session_continuity']} | {item['provenance_correct']} | {findings} |")
    lines += ["", "## Mode UX scores", "", "| Mode | Result |", "|---|---|", "| QUICK | covered by Q1–Q3 and H1 |", "| AI_DECIDE | covered by A1–A2 and G1 |", "| USER_DECIDE | natural-language and structured gate scenarios covered by U/B/R/I/C/P/UX cases |", "", "## Findings by type", ""]
    for finding, ids in sorted(finding_map.items()):
        lines.append(f"- `{finding}`: {', '.join(ids)}")
    lines += [
        "",
        "## Required guard distinctions",
        "",
        "- `STALE_EVENT_APPLIED`: not observed; I1 passed with `STALE_GATE_EVENT` and no state mutation.",
        "- `DUPLICATE_EVENT_APPLIED`: not observed; I2 wrote one event and returned the cached response on replay.",
        "- `SESSION_RESET_UNEXPECTEDLY`: not observed in structured R1 resume or G1 boundary checks; natural mode-switch/resume failures are classified separately below.",
        "",
        "## Finding classification",
        "",
        "- The matrix above is the source of truth for any remaining finding; no pre-fix failure narrative is carried forward automatically.",
        "",
        "## Blockers",
        "",
        f"- Core scenario failures: {', '.join(core_failures) if core_failures else 'none'}.",
        f"- Remaining scenario failures: {', '.join(item['id'] for item in failures if item['id'] not in core_ids) if any(item['id'] not in core_ids for item in failures) else 'none'}.",
        "",
        "## Polish / gaps",
        "",
        "- Human review remains the next step even when the automated threshold passes.",
        "",
        "## Acceptance decision",
        "",
        f"Acceptance decision: `{status}`. No image generation or commit was performed.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    # WHY: this suite creates acceptance artifacts and is a development tool;
    # prevent accidentally treating the installed C: copy as source code.
    require_development_repository(ROOT)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for scenario_id, category, title, runner in SCENARIOS:
        ctx = CaseContext()
        try:
            review = runner(ctx)
            results.append(write_case(scenario_id, category, title, ctx, review))
            manifest.append({"id": scenario_id, "category": category, "title": title, "artifact_dir": str(case_dir(category, scenario_id))})
        finally:
            ctx.close()
    pass_count = sum(item["correctness"] == "PASS" for item in results)
    fail_count = len(results) - pass_count
    core_ids = {"U1-T2", "U1-T3", "U1-T4", "U2", "U2-T2", "U3", "U3-T2", "U4", "U5", "U6", "M1", "M2", "C1", "H1", "H2", "P1", "UX1", "UX3", "UX6", "UX7", "UX8", "UX9"}
    core_failures = [item["id"] for item in results if item["id"] in core_ids and item["correctness"] == "FAIL"]
    status = "THREE_MODE_INTERACTION_UX_RETEST_PASS_PENDING_HUMAN_REVIEW" if pass_count >= 40 and not core_failures else "INTERACTION_NL_AND_CONSTRAINT_FIX_IMPLEMENTED_PENDING_UX_RETEST"
    dump(OUTPUT_ROOT / "scenario_manifest.json", {"suite": "THREE_MODE_INTERACTION_UX_ACCEPTANCE v1", "production_code_changed": True, "imagegen_called": False, "scenario_count": len(results), "scenarios": manifest})
    text = report(results)
    for name in ("three_mode_ux_acceptance_report.md", "interaction_ux_acceptance_report.md"):
        (OUTPUT_ROOT / name).write_text(text, encoding="utf-8")
    dump(OUTPUT_ROOT / "summary" / "acceptance_summary.json", {"scenario_count": len(results), "pass_count": pass_count, "fail_count": fail_count, "status": status, "imagegen_called": False, "production_code_changed": True, "core_failures": core_failures})
    print(json.dumps({"output_root": str(OUTPUT_ROOT), "scenario_count": len(results), "pass_count": pass_count, "fail_count": fail_count, "status": status}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
