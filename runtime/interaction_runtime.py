"""Persistent interaction orchestration for the three creation modes.

This module owns session state and gate hand-off. Existing visual-preference,
regional-style, and pose runtimes remain the source of truth for their gates.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import MISSING, asdict, dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from uuid import uuid4

try:
    from .regional_style_runtime import (
        DEFAULT_FACE_AESTHETIC_PROFILE,
        DEFAULT_FACE_AESTHETIC_SOURCE,
        DEFAULT_STYLE_INHERITANCE_POLICY,
        DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        ExplicitConstraintCoverageGate,
        PromptCompiler,
        PromptConstraintConflict,
        build_visual_specification_contract,
        resolve_face_aesthetic_profile,
    )
    from .visual_preference_runtime import (
        AI_IMPLEMENTATION_VARIABLES,
        AI_PROPOSED_OPTIONAL_VARIABLES,
        IDENTITY_VARIABLES,
        VisualPreferenceSession,
    )
    from .natural_language_interaction import ExplicitConstraintExtractor, NaturalLanguageInteractionParser
    from .interaction_candidates import (
        BACKGROUND_SPECIFICATION_FIELDS,
        CANDIDATE_GENERATOR_VERSION,
        CandidateGenerator,
        POSE_SPECIFICATION_FIELDS,
        context_profile,
        select_ai_candidate,
        select_seeded_candidate,
        stable_session_seed,
    )
    from .visual_context_firewall import DEFAULT_BLOCKED_CONTEXT_SOURCES, VisualContextFirewall
    from .cross_run_novelty import DesignSignature, NoveltyGuard, NoveltyPolicy
    from .visual_adherence_critic import VisualAdherenceCritic, VisualAdherenceReview
    from .visual_repair import (
        MAX_REPAIR_ATTEMPTS,
        VisualRepairError,
        VisualRepairPlan,
        build_repair_plan,
        compile_repair_prompt,
        evaluate_repair_attempt,
        initial_best_artifact,
        select_best_artifact,
    )
except ImportError:  # pragma: no cover - supports direct host imports
    from regional_style_runtime import (  # type: ignore
        DEFAULT_FACE_AESTHETIC_PROFILE,
        DEFAULT_FACE_AESTHETIC_SOURCE,
        DEFAULT_STYLE_INHERITANCE_POLICY,
        DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        ExplicitConstraintCoverageGate,
        PromptCompiler,
        PromptConstraintConflict,
        build_visual_specification_contract,
        resolve_face_aesthetic_profile,
    )
    from visual_preference_runtime import (  # type: ignore
        AI_IMPLEMENTATION_VARIABLES,
        AI_PROPOSED_OPTIONAL_VARIABLES,
        IDENTITY_VARIABLES,
        VisualPreferenceSession,
    )
    from natural_language_interaction import ExplicitConstraintExtractor, NaturalLanguageInteractionParser  # type: ignore
    from interaction_candidates import (  # type: ignore
        BACKGROUND_SPECIFICATION_FIELDS,
        CANDIDATE_GENERATOR_VERSION,
        CandidateGenerator,
        POSE_SPECIFICATION_FIELDS,
        context_profile,
        select_ai_candidate,
        select_seeded_candidate,
        stable_session_seed,
    )
    from visual_context_firewall import DEFAULT_BLOCKED_CONTEXT_SOURCES, VisualContextFirewall  # type: ignore
    from cross_run_novelty import DesignSignature, NoveltyGuard, NoveltyPolicy  # type: ignore
    from visual_adherence_critic import VisualAdherenceCritic, VisualAdherenceReview  # type: ignore
    from visual_repair import (  # type: ignore
        MAX_REPAIR_ATTEMPTS,
        VisualRepairError,
        VisualRepairPlan,
        build_repair_plan,
        compile_repair_prompt,
        evaluate_repair_attempt,
        initial_best_artifact,
        select_best_artifact,
    )


INTERACTION_SESSION_VERSION = "1.1.0"
ARTIFACT_CONTINUITY_PENDING = "strict_pending_generation"
ARTIFACT_CONTINUITY_COMPLETE = "strict_complete"
ARTIFACT_CONTINUITY_LEGACY = "legacy_incomplete"


class _ValueEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class CreationMode(_ValueEnum):
    QUICK = "QUICK"
    AI_DECIDE = "AI_DECIDE"
    USER_DECIDE = "USER_DECIDE"


class ExplicitUserConstraintConflict(ValueError):
    """Raised when a current-run UI action contradicts a human hard field."""


class PipelineStage(_ValueEnum):
    INPUT = "INPUT"
    CHARACTER_EXPLORE = "CHARACTER_EXPLORE"
    CHARACTER_DIRECTION_RESOLUTION = "CHARACTER_DIRECTION_RESOLUTION"
    CHARACTER_PLANNING = "CHARACTER_PLANNING"
    ART_EXPLORE = "ART_EXPLORE"
    ART_DIRECTION_RESOLUTION = "ART_DIRECTION_RESOLUTION"
    VISUAL_PREFERENCE_RESOLUTION = "VISUAL_PREFERENCE_RESOLUTION"
    FINAL_DESIGN = "FINAL_DESIGN"
    PLAYABLE_CHARACTER_DESIGN_GATE = "PLAYABLE_CHARACTER_DESIGN_GATE"
    PROMPT_COMPILATION = "PROMPT_COMPILATION"
    GENERATION_READY = "GENERATION_READY"


class SessionStatus(_ValueEnum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    AWAITING_CHARACTER_DIRECTION = "AWAITING_CHARACTER_DIRECTION"
    AWAITING_ART_DIRECTION = "AWAITING_ART_DIRECTION"
    AWAITING_VISUAL_PREFERENCES = "AWAITING_VISUAL_PREFERENCES"
    FINAL_DESIGNING = "FINAL_DESIGNING"
    DESIGN_VALIDATING = "DESIGN_VALIDATING"
    PROMPT_COMPILING = "PROMPT_COMPILING"
    GENERATION_READY = "GENERATION_READY"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    AWAITING_USER_INTERVENTION = "AWAITING_USER_INTERVENTION"
    CANCELLED = "CANCELLED"


class GateType(_ValueEnum):
    CHARACTER_DIRECTION_GATE = "CHARACTER_DIRECTION_GATE"
    ART_DIRECTION_GATE = "ART_DIRECTION_GATE"
    VISUAL_PREFERENCE_GATE = "VISUAL_PREFERENCE_GATE"


class InteractionAction(_ValueEnum):
    SELECT = "SELECT"
    MIX = "MIX"
    CUSTOM = "CUSTOM"
    DELEGATE = "DELEGATE"
    PARTIAL_DELEGATE = "PARTIAL_DELEGATE"
    USE_RECOMMENDED = "USE_RECOMMENDED"
    USE_ALL_RECOMMENDED = "USE_ALL_RECOMMENDED"
    BACK = "BACK"
    CANCEL = "CANCEL"
    REGENERATE_OPTIONS = "REGENERATE_OPTIONS"


class ResolutionStatus(_ValueEnum):
    RESOLVED = "RESOLVED"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    INVALID = "INVALID"
    CANCELLED = "CANCELLED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _value(value: Any) -> Any:
    return value.value if isinstance(value, Enum) else value


def _as_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "to_dict"):
        return deepcopy(value.to_dict())
    return deepcopy(asdict(value))


@dataclass
class InteractionEvent:
    event_id: str
    session_id: str
    gate_id: str
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.action = str(_value(self.action))
        self.payload = dict(self.payload or {})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InteractionEvent":
        return cls(
            event_id=str(data.get("event_id") or uuid4().hex),
            session_id=str(data.get("session_id", "")),
            gate_id=str(data.get("gate_id", "")),
            action=str(data.get("action", "")),
            payload=dict(data.get("payload") or {}),
            timestamp=str(data.get("timestamp") or _now()),
        )


@dataclass
class ModeSwitchEvent:
    from_mode: str
    to_mode: str
    stage: str
    reason: str
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GateResolution:
    gate_id: str
    gate_type: str
    resolution_status: str
    selected_values: dict[str, Any] = field(default_factory=dict)
    decision_source: str | None = None
    human_override: bool = False
    delegated: bool = False
    unresolved_fields: list[str] = field(default_factory=list)
    rationale: str = ""
    timestamp: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        self.gate_type = str(_value(self.gate_type))
        self.resolution_status = str(_value(self.resolution_status))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InteractiveResponse:
    session_id: str
    mode: str
    status: str
    stage: str
    user_message: str
    gate: dict[str, Any] | None = None
    options: list[dict[str, Any]] = field(default_factory=list)
    recommended: Any = None
    unresolved_fields: list[str] = field(default_factory=list)
    allowed_actions: list[str] = field(default_factory=list)
    progress: dict[str, Any] = field(default_factory=dict)
    internal_artifact_refs: dict[str, str] = field(default_factory=dict)
    error_code: str | None = None

    def __post_init__(self) -> None:
        self.mode = str(_value(self.mode))
        self.status = str(_value(self.status))
        self.stage = str(_value(self.stage))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InteractiveResponse":
        values = {}
        for item in fields(cls):
            if item.name in data:
                values[item.name] = deepcopy(data[item.name])
            elif item.default is not MISSING:
                values[item.name] = deepcopy(item.default)
            else:
                values[item.name] = [] if item.type in {"list[dict[str, Any]]", "list[str]"} else {}
        return cls(**values)


@dataclass(frozen=True)
class GenerationArtifact:
    generation_id: str
    run_id: str
    image_path: str
    image_hash: str
    prompt_hash: str
    prompt_bundle_ref: str
    manifest_ref: str
    contract_ref: str
    mode: str
    design_seed: int | None
    created_at: str
    face_aesthetic_profile: str = DEFAULT_FACE_AESTHETIC_PROFILE
    face_aesthetic_source: str = DEFAULT_FACE_AESTHETIC_SOURCE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "GenerationArtifact":
        return cls(
            generation_id=str(data.get("generation_id", "")),
            run_id=str(data.get("run_id", "")),
            image_path=str(data.get("image_path", data.get("image", ""))),
            image_hash=str(data.get("image_hash", "")),
            prompt_hash=str(data.get("prompt_hash", "")),
            prompt_bundle_ref=str(data.get("prompt_bundle_ref", "")),
            manifest_ref=str(data.get("manifest_ref", "")),
            contract_ref=str(data.get("contract_ref", "")),
            mode=str(data.get("mode", "")),
            design_seed=data.get("design_seed"),
            created_at=str(data.get("created_at", "")),
            face_aesthetic_profile=str(data.get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE)),
            face_aesthetic_source=str(data.get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE)),
        )


@dataclass
class CreativeInteractionSession:
    session_id: str
    creation_mode: str
    original_user_input: str
    current_stage: str = PipelineStage.INPUT.value
    current_gate: str | None = None
    status: str = SessionStatus.CREATED.value
    explicit_user_constraints: dict[str, Any] = field(default_factory=dict)
    inherit_previous_visuals: bool = False
    allowed_visual_inheritance: list[str] = field(default_factory=list)
    blocked_context_sources: list[str] = field(default_factory=lambda: list(DEFAULT_BLOCKED_CONTEXT_SOURCES))
    visual_context_firewall_applied: bool = True
    style_inheritance_policy: str = DEFAULT_STYLE_INHERITANCE_POLICY
    face_aesthetic_contract: dict[str, Any] = field(default_factory=dict)
    design_seed: int | None = None
    pending_constraint_updates: dict[str, Any] = field(default_factory=dict)
    delegated_fields: list[str] = field(default_factory=list)
    locked_fields: dict[str, Any] = field(default_factory=dict)
    unresolved_fields: list[str] = field(default_factory=list)
    character_explore_result: list[dict[str, Any]] = field(default_factory=list)
    selected_character_direction: dict[str, Any] | None = None
    character_plan: dict[str, Any] | None = None
    art_explore_result: list[dict[str, Any]] = field(default_factory=list)
    selected_art_direction: dict[str, Any] | None = None
    visual_preference_sheet: dict[str, Any] | None = None
    resolved_visual_preferences: dict[str, Any] = field(default_factory=dict)
    final_design: dict[str, Any] | None = None
    design_gate_result: dict[str, Any] | None = None
    compiled_prompt: dict[str, Any] | None = None
    visual_adherence_review: dict[str, Any] | None = None
    audit_log: list[dict[str, Any]] = field(default_factory=list)
    interaction_history: list[dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    schema_version: str = INTERACTION_SESSION_VERSION
    interaction_session_version: str = INTERACTION_SESSION_VERSION
    gate_payload: dict[str, Any] = field(default_factory=dict)
    gate_sequence: int = 0
    retry_counts: dict[str, int] = field(default_factory=dict)
    candidate_revisions: dict[str, int] = field(default_factory=dict)
    candidate_history: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    artifact_status: dict[str, str] = field(default_factory=dict)
    processed_event_responses: dict[str, dict[str, Any]] = field(default_factory=dict)
    last_response: dict[str, Any] | None = None
    legacy_artifacts: dict[str, Any] = field(default_factory=dict)
    original_image: str | None = None
    original_visual_adherence_review: dict[str, Any] | None = None
    repair_attempts: list[dict[str, Any]] = field(default_factory=list)
    best_artifact: dict[str, Any] | None = None
    repair_status: str | None = None
    generation_artifact: dict[str, Any] | None = None
    artifact_continuity: str = ARTIFACT_CONTINUITY_PENDING
    design_signature: dict[str, Any] | None = None
    novelty_review: dict[str, Any] | None = None
    novelty_history_snapshot: list[dict[str, Any]] | None = None
    novelty_candidate_reviews: dict[str, Any] = field(default_factory=dict)
    novelty_policy: dict[str, Any] = field(default_factory=lambda: NoveltyPolicy().to_dict())
    novelty_resolution_attempt: int = 0
    novelty_status: str | None = None
    human_override_novelty: bool = False

    def __post_init__(self) -> None:
        self.creation_mode = str(_value(self.creation_mode))
        self.current_stage = str(_value(self.current_stage))
        self.status = str(_value(self.status))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CreativeInteractionSession":
        raw = dict(data)
        values: dict[str, Any] = {}
        for item in fields(cls):
            if item.name in raw:
                values[item.name] = deepcopy(raw[item.name])
        values.setdefault("session_id", str(raw.get("id") or uuid4().hex))
        values.setdefault("original_user_input", str(raw.get("input") or raw.get("prompt") or ""))
        values.setdefault("creation_mode", _legacy_mode(raw.get("mode") or raw.get("creation_mode")))
        values.setdefault("schema_version", INTERACTION_SESSION_VERSION)
        values.setdefault("interaction_session_version", values["schema_version"])
        values.setdefault("legacy_artifacts", {})
        if "artifact_continuity" not in raw:
            values["artifact_continuity"] = ARTIFACT_CONTINUITY_LEGACY
        if raw.get("generation_artifact") and isinstance(raw.get("generation_artifact"), Mapping):
            values["generation_artifact"] = deepcopy(dict(raw["generation_artifact"]))
        return cls(**values)


def _session_firewall(session: CreativeInteractionSession) -> VisualContextFirewall:
    return VisualContextFirewall(
        bool(session.inherit_previous_visuals),
        tuple(session.allowed_visual_inheritance),
        tuple(session.blocked_context_sources),
        bool(session.visual_context_firewall_applied),
        str(session.style_inheritance_policy),
    )


def _legacy_mode(mode: Any) -> str:
    value = str(mode or "AI_DECIDE").upper()
    return {
        "DIRECTED": CreationMode.AI_DECIDE.value,
        "EXPLORE": CreationMode.USER_DECIDE.value,
        "AUTO": CreationMode.AI_DECIDE.value,
        "QUICK": CreationMode.QUICK.value,
        "AI_DECIDE": CreationMode.AI_DECIDE.value,
        "USER_DECIDE": CreationMode.USER_DECIDE.value,
    }.get(value, CreationMode.AI_DECIDE.value)


def migrate_legacy_artifact(data: Mapping[str, Any], *, session_id: str | None = None) -> CreativeInteractionSession:
    """Read old creative artifacts without rewriting them."""
    session = CreativeInteractionSession.from_dict({**dict(data), "session_id": session_id or data.get("session_id") or uuid4().hex})
    if not data.get("interaction_session_version"):
        session.legacy_artifacts = deepcopy(dict(data))
        session.artifact_continuity = ARTIFACT_CONTINUITY_LEGACY
        old_state = str(data.get("state", "")).upper()
        state_map = {
            "AWAITING_CHARACTER_SELECTION": SessionStatus.AWAITING_CHARACTER_DIRECTION.value,
            "AWAITING_ART_SELECTION": SessionStatus.AWAITING_ART_DIRECTION.value,
            "AWAITING_VISUAL_PREFERENCE_SELECTION": SessionStatus.AWAITING_VISUAL_PREFERENCES.value,
        }
        session.status = state_map.get(old_state, session.status)
    return session


def detect_creation_mode(user_input: str, explicit_mode: str | CreationMode | None = None) -> str:
    if explicit_mode is not None:
        value = str(_value(explicit_mode)).upper()
        if value in {item.value for item in CreationMode}:
            return value
        aliases = {"QUICK": "QUICK", "AI": "AI_DECIDE", "AI DECIDE": "AI_DECIDE", "USER": "USER_DECIDE", "USER DECIDE": "USER_DECIDE"}
        if value in aliases:
            return aliases[value]
        raise ValueError(f"unsupported creation mode: {explicit_mode}")
    text = user_input.lower()
    user_tokens = ("我自己选", "给我几个方案", "我来选", "每一步让我选", "先给方案", "自己决定")
    quick_tokens = ("快速", "直接来", "随便设计一个", "不用问我", "快一点", "quick")
    ai_tokens = ("你来决定", "你帮我完整设计", "都交给你", "你选最好的", "ai decide")
    if any(token in text for token in user_tokens):
        return CreationMode.USER_DECIDE.value
    if any(token in text for token in quick_tokens):
        return CreationMode.QUICK.value
    if any(token in text for token in ai_tokens):
        return CreationMode.AI_DECIDE.value
    return CreationMode.AI_DECIDE.value


def _extract_constraints(text: str) -> dict[str, Any]:
    constraints = ExplicitConstraintExtractor().extract(text)
    if "design direction failure" in text.lower() or "强制失败" in text:
        constraints["force_design_failure"] = True
    return constraints


def _option(option_id: str, value: Any, reason: str) -> dict[str, Any]:
    return {"id": option_id, "value": value, "reason": reason, "diversity_risk": "low"}


def _direction_design_dna(prior_resolutions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    for item in list(prior_resolutions):
        direction = item.get("direction") if isinstance(item, Mapping) else None
        if isinstance(direction, Mapping) and isinstance(direction.get("design_dna"), Mapping):
            return deepcopy(dict(direction["design_dna"]))
    return {}


def _visual_sheet(
    constraints: Mapping[str, Any],
    *,
    original_input: str | None = None,
    prior_resolutions: Sequence[Mapping[str, Any]] = (),
    visual_context_firewall: VisualContextFirewall | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    firewall = VisualContextFirewall.from_metadata(visual_context_firewall)
    raw_input = str(original_input or constraints.get("raw", ""))
    profile = context_profile(raw_input, constraints)
    design_dna = _direction_design_dna(prior_resolutions)
    face_selection = resolve_face_aesthetic_profile(
        constraints.get("face_aesthetic_profile"),
        source=constraints.get("face_aesthetic_source"),
        explicit_user_selection="face_aesthetic_profile" in constraints.get("explicit_user_fields", ()),
        style_inheritance_policy=firewall.style_inheritance_policy,
    )
    context_values = {
        "urban_watchful": {
            "hair_style_family": "asymmetric long layers",
            "outfit_direction": "structured urban-fantasy layering",
            "dominant_palette": "deep teal with signal amber",
            "major_accessories": "compact city-signal device",
            "background_direction": "quiet city dusk with offset light",
            "character_visual_style": "clean-line contemporary gacha anime",
        },
        "mechanical_kinetic": {
            "hair_style_family": "short high-motion side layers",
            "outfit_direction": "lightweight modular action wear",
            "dominant_palette": "cobalt with warm copper accent",
            "major_accessories": "movable connector panel",
            "background_direction": "layered motion arcs with clean depth",
            "character_visual_style": "clean-line kinetic gacha anime",
        },
        "nonhuman_predatory": {
            "hair_style_family": "segmented swept-back mane",
            "outfit_direction": "anatomy-led asymmetric armor cloth",
            "dominant_palette": "deep umber with cold mineral blue",
            "major_accessories": "single structural horn or bone anchor",
            "background_direction": "cold pressure field with anatomical planes",
            "character_visual_style": "clean-line contemporary gacha anime with nonhuman structure",
            "nonhuman_trait_level": "integrated nonhuman anatomy",
            "body_build": "predatory athletic build",
        },
        "gentle_distinctive": {
            "hair_style_family": "short-to-medium directional layers",
            "outfit_direction": "structured calm everyday layers",
            "dominant_palette": "sage and ink with warm brass accent",
            "major_accessories": "single tactile trust token",
            "background_direction": "warm architectural light with clear breathing room",
            "character_visual_style": "clean-line contemporary gacha anime",
        },
        "specific_adult": {},
    }[profile]
    hair = constraints.get("hair_color", "ash-silver")
    values: dict[str, Any] = {
        "hair_color": hair,
        "hair_style_family": "asymmetric long layers",
        "outfit_direction": "structured contemporary fantasy tailoring",
        "dominant_palette": "deep teal with warm accent",
        "character_visual_style": "clean-line contemporary gacha anime",
        "major_accessories": "one iconic compact tool",
        "body_markings": "none",
        "eye_color": "clear teal",
        "nonhuman_trait_level": constraints.get("nonhuman_trait_level", "human-anime traits"),
        "fanservice_level": "restrained and character-motivated",
        "body_build": "adult balanced athletic build",
        "background_direction": "clean atmospheric gradient with restrained motif",
        "footwear_family": constraints.get("footwear_family", "low asymmetrical boots"),
        "legwear_family": "none",
        "exposure_strategy": "controlled partial exposure",
        "leg_accessory_family": "none",
        "foot_visibility": "both feet readable",
        "visual_reason": "supports identity and a grounded playable-character silhouette",
        "relationship_to_character_style": "supports the selected contemporary design language",
        "relationship_to_pose": "keeps both legs in separate visible lanes",
        "repetition_risk": "low",
        "pose_intent": "STABLE_OPEN",
        "pose_family": "OPEN_PARALLEL_STANCE",
        "face_aesthetic_profile": face_selection.face_aesthetic_profile,
        "face_aesthetic_source": face_selection.face_aesthetic_source,
        "face_aesthetic_is_default": face_selection.face_aesthetic_is_default,
        "style_inheritance_policy": face_selection.style_inheritance_policy,
    }
    values.update(context_values)
    if design_dna:
        values["footwear_family"] = design_dna.get("footwear_category", values["footwear_family"])
    is_succubus_request = any(token in raw_input.lower() for token in ("魅魔", "succubus", "demoness"))
    if design_dna and is_succubus_request:
        values.update(
            {
                "hair_style_family": design_dna.get("hair_structure", values["hair_style_family"]),
                "outfit_direction": design_dna.get("costume_topology", values["outfit_direction"]),
                "dominant_palette": design_dna.get("palette_family", values["dominant_palette"]),
                "background_direction": design_dna.get("background_family", values["background_direction"]),
                "footwear_family": design_dna.get("footwear_category", values["footwear_family"]),
                "legwear_family": design_dna.get("legwear_strategy", values["legwear_family"]),
                "exposure_strategy": design_dna.get("exposure_strategy", values["exposure_strategy"]),
                "pose_family": design_dna.get("pose_family", values["pose_family"]),
            }
        )
        pose_intents = {
            "OPEN_PARALLEL_STANCE": "STABLE_OPEN",
            "NARROW_SEPARATED_STANCE": "NARROW_STANCE",
            "FORWARD_STEP_NON_CROSSING": "ONE_FOOT_FORWARD",
            "LOW_ENERGY_SEPARATED_STANCE": "LOW_ENERGY",
        }
        values["pose_intent"] = pose_intents.get(str(values["pose_family"]), values["pose_intent"])
        if design_dna.get("horn_topology") and "none" not in str(design_dna["horn_topology"]).lower():
            values["nonhuman_trait_level"] = "integrated horn anatomy"
    if prior_resolutions:
        selected = prior_resolutions[-1].get("direction", {})
        if isinstance(selected, Mapping):
            values["relationship_to_character_style"] = f"extends the selected {selected.get('short_label') or selected.get('design_thesis') or 'character direction'}"
            values["visual_reason"] = "keeps the selected character direction coherent while preserving a distinct lower-body read"
    values.update({name: constraints[name] for name in ("hair_color", "footwear_family", "legwear_family", "nonhuman_trait_level") if name in constraints})
    explicit_values = {
        "gender_presentation": constraints.get("gender_presentation"),
        "role_identity": constraints.get("role_identity"),
        "costume_identity": constraints.get("costume_identity"),
        "human_form_requirement": constraints.get("human_form_requirement"),
        "supernatural_state": constraints.get("supernatural_state"),
        "character_state": constraints.get("character_state"),
        "body_proportion": constraints.get("body_proportion"),
        "bust_emphasis": constraints.get("bust_emphasis"),
        "props": constraints.get("props"),
        "companion_type": constraints.get("companion_type"),
        "companion_count": constraints.get("companion_count"),
        "nonhuman_features": constraints.get("nonhuman_features"),
        "hair": constraints.get("hair"),
        "pose": constraints.get("pose"),
        "background": constraints.get("background"),
        "composition": constraints.get("composition"),
        "legwear": constraints.get("legwear"),
        "footwear": constraints.get("footwear"),
        "footwear_detail": constraints.get("footwear_detail"),
        "palette_primary": constraints.get("palette_primary"),
        "palette_secondary": constraints.get("palette_secondary"),
        "horns": constraints.get("horns"),
        "tail": constraints.get("tail"),
        "wings": constraints.get("wings"),
        "quantity_constraints": constraints.get("quantity_constraints"),
    }
    for name, value in explicit_values.items():
        if value is not None:
            values[name] = deepcopy(value)
    if constraints.get("role_identity") in {"maid", "head_maid"} or constraints.get("costume_identity") == "maid_outfit":
        values["outfit_direction"] = "maid-based"
    if constraints.get("body_proportion"):
        values["body_build"] = "large-bust feminine build"
    if constraints.get("props"):
        values["major_accessories"] = ", ".join(str(item) for item in constraints["props"])
    if constraints.get("legwear"):
        values["legwear_family"] = constraints["legwear"]
    if constraints.get("footwear"):
        values["footwear_family"] = constraints["footwear"]
    if constraints.get("palette_primary") or constraints.get("palette_secondary"):
        values["dominant_palette"] = f"{constraints.get('palette_primary', 'white')} dominant / {constraints.get('palette_secondary', 'blue')} secondary"
    user_fields = tuple(IDENTITY_VARIABLES) + (
        "footwear_family",
        "legwear_family",
        "exposure_strategy",
        "leg_accessory_family",
        "foot_visibility",
        "pose_intent",
        "character_visual_style",
        "eye_color",
        "fanservice_level",
        "body_build",
        "nonhuman_trait_level",
        "gender_presentation",
        "role_identity",
        "costume_identity",
        "human_form_requirement",
        "supernatural_state",
        "character_state",
        "body_proportion",
        "bust_emphasis",
        "props",
        "companion_type",
        "companion_count",
        "nonhuman_features",
        "hair",
        "pose",
        "background",
        "composition",
        "legwear",
        "footwear",
        "footwear_detail",
        "palette_primary",
        "palette_secondary",
        "horns",
        "tail",
        "wings",
        "quantity_constraints",
    )
    context_alternatives = {
        "urban_watchful": {
            "hair_color": ("smoke-lilac", "blue-black"),
            "outfit_direction": ("offset city shell", "quiet utility layers"),
            "dominant_palette": ("charcoal and signal amber", "blue-gray and muted red"),
            "major_accessories": ("none", "single reflective ear piece"),
            "background_direction": ("rain-glass city edge", "thin neon reflection"),
        },
        "mechanical_kinetic": {
            "hair_color": ("copper-red", "electric blue"),
            "outfit_direction": ("asymmetric sprint layers", "compact impact jacket"),
            "dominant_palette": ("graphite and orange", "teal and brass"),
            "major_accessories": ("none", "flexible signal band"),
            "background_direction": ("clean trajectory field", "bright workshop geometry"),
        },
        "nonhuman_predatory": {
            "hair_color": ("iron white", "dark indigo"),
            "outfit_direction": ("segmented hide and cloth", "low-center plated wrap"),
            "dominant_palette": ("black-brown and ice blue", "oxblood and mineral gray"),
            "major_accessories": ("none", "bone ridge accent"),
            "background_direction": ("cold fractured plane", "low fog pressure field"),
        },
        "gentle_distinctive": {
            "hair_color": ("dark chestnut", "smoky green-black"),
            "outfit_direction": ("calm structured knit", "asymmetric civic layers"),
            "dominant_palette": ("sage and brass", "ink and ochre"),
            "major_accessories": ("none", "small tactile token"),
            "background_direction": ("quiet courtyard light", "warm window geometry"),
        },
        "specific_adult": {},
    }.get(profile, {})
    profile_reason = {
        "urban_watchful": "都市观察性与隐藏危险感",
        "mechanical_kinetic": "外向动势与非字面机械关系",
        "nonhuman_predatory": "非人结构与压迫性",
        "gentle_distinctive": "亲和力与个人边界",
        "specific_adult": "当前角色输入的核心身份",
    }[profile]
    prior_reason = "，并延续前序已选方向" if prior_resolutions else ""
    variables: dict[str, Any] = {}
    for name, recommended in values.items():
        alternatives = {
            "hair_color": ("muted rose", "blue-black"),
            "hair_style_family": ("short geometric bob", "braided side mass"),
            "outfit_direction": ("soft layered streetwear", "ceremonial modular coat"),
            "dominant_palette": ("ivory and coral", "violet and graphite"),
            "character_visual_style": ("quiet minimalist anime", "geometric high-contrast anime"),
            "major_accessories": ("none", "asymmetric ear communicator"),
            "body_markings": ("none", "small geometric cheek mark"),
            "eye_color": ("amber", "violet"),
            "nonhuman_trait_level": ("subtle fox ears", "none"),
            "fanservice_level": ("none", "strong but non-explicit"),
            "body_build": ("slender adult build", "powerful adult build"),
            "background_direction": ("quiet city dusk", "abstract temporal haze"),
            "footwear_family": ("barefoot with ankle ornament", "flat sneakers"),
            "legwear_family": ("white opaque tights", "sheer tights"),
            "exposure_strategy": ("mostly covered", "full-leg exposure"),
            "leg_accessory_family": ("none", "ankle ornament"),
            "foot_visibility": ("toes visible", "shoes fully visible"),
            "pose_intent": ("RELAXED_ASYMMETRIC", "ONE_FOOT_FORWARD"),
            "pose_family": ("NARROW_SEPARATED_STANCE", "FORWARD_STEP_NON_CROSSING"),
        }.get(name, context_alternatives.get(name, (recommended, f"alternative {name}")))
        option_values = [recommended, *alternatives]
        variables[name] = {
            "variable": name,
            "recommended": recommended,
            "recommendation_reason": f"基于{profile_reason}{prior_reason}，在身份、可读性与约束兼容之间取得平衡。",
            "recommendation_reason_en": f"Context-aware proposal for {profile_reason}{' with the prior direction preserved' if prior_resolutions else ''}; balances identity, readability, and constraint compatibility.",
            "options": [_option(chr(65 + index), value, "distinct identity or presentation trade-off") for index, value in enumerate(option_values)],
            "allow_custom": name in user_fields,
            "allow_ai_delegate": True,
            "user_selection": None,
            "selection_source": None,
            "locked": False,
            "user_visible": name in user_fields,
        }
        if name in {"major_accessories", "body_markings"}:
            variables[name]["options"].append(_option("NONE", "none", "keep the primary anchor clean"))
    for name in constraints.get("explicit_user_fields", []):
        if name not in variables or name not in constraints:
            continue
        variables[name].update(
            user_selection=deepcopy(constraints[name]),
            selection_source="explicit_user",
            locked=True,
        )
    if "forbid_outfit_lower" in constraints:
        variables["outfit_direction"].update(
            user_selection=f"no {constraints['forbid_outfit_lower']}",
            selection_source="explicit_user",
            locked=True,
        )
    return {
        "schema_version": "1.0.0",
        **firewall.to_dict(),
        "regional_visual_language": DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        "regional_visual_language_source": "default_style_policy",
        **face_selection.to_dict(),
        "face_aesthetic_contract": face_selection.to_dict(),
        "explicit_user_request": bool(set(constraints) - {"raw"}),
        "variables": variables,
        "optional_variables": {
            name: {"current_ai_proposal": values.get(name, "policy default"), "alternative_suggestions": [], "user_override_allowed": True}
            for name in AI_PROPOSED_OPTIONAL_VARIABLES
            if name not in variables
        },
        "ai_implementation_variables": list(AI_IMPLEMENTATION_VARIABLES),
        "user_controlled_variables": list(user_fields),
        "lower_body_visual_variables": {name: values[name] for name in ("exposure_strategy", "legwear_family", "leg_accessory_family", "footwear_family", "foot_visibility", "visual_reason", "relationship_to_character_style", "relationship_to_pose", "repetition_risk")},
        "pose_intent": values["pose_intent"],
        "design_dna": deepcopy(design_dna),
    }


def _directions(
    text: str,
    *,
    depth: str,
    kind: str,
    explicit_constraints: Mapping[str, Any] | None = None,
    prior_resolutions: Sequence[Mapping[str, Any]] = (),
    visual_context_firewall: VisualContextFirewall | Mapping[str, Any] | None = None,
    revision: int = 0,
    seed: Any = None,
) -> list[dict[str, Any]]:
    firewall = VisualContextFirewall.from_metadata(visual_context_firewall)
    # QUICK samples one path from the same small legal pool; it does not render all four.
    count = 4
    gate_id = GateType.ART_DIRECTION_GATE.value if kind == "art" else GateType.CHARACTER_DIRECTION_GATE.value
    generated = CandidateGenerator().generate(
        gate_id=gate_id,
        original_input=text,
        explicit_constraints=explicit_constraints,
        prior_resolutions=prior_resolutions,
        generation_context=firewall.generation_context(
            current_user_request=text,
            current_run_choices=prior_resolutions,
            confirmed_gate_outputs=prior_resolutions,
        ),
        style_policy="CONTEMPORARY_COMMERCIAL_GACHA_ANIME",
        revision=revision,
        seed=seed,
    )
    return generated[:count]


class GateResolver:
    """Mode-independent gate interface used by the pipeline."""

    def resolve(
        self,
        session: CreativeInteractionSession,
        gate_type: str | GateType,
        event: InteractionEvent | None = None,
        *,
        payload: Mapping[str, Any] | None = None,
    ) -> GateResolution:
        raise NotImplementedError

    @staticmethod
    def _gate(session: CreativeInteractionSession, gate_type: str | GateType) -> str:
        return session.current_gate or f"{session.session_id}:{str(_value(gate_type)).lower()}"


class QuickGateResolver(GateResolver):
    """Fast, low-depth resolution with explicit requirements preserved."""

    def resolve(self, session: CreativeInteractionSession, gate_type: str | GateType, event: InteractionEvent | None = None, *, payload: Mapping[str, Any] | None = None) -> GateResolution:
        gate = str(_value(gate_type))
        if gate == GateType.CHARACTER_DIRECTION_GATE.value:
            selected = select_seeded_candidate(session.character_explore_result, session.design_seed, salt="character-direction")
            initial_index = next((index for index, item in enumerate(session.character_explore_result) if item.get("id") == selected.get("id")), 0)
            novelty = NoveltyGuard.resolve_quick_candidates(
                session.character_explore_result,
                initial_index,
                policy=NoveltyPolicy.from_mapping(session.novelty_policy),
                history_snapshot=session.novelty_history_snapshot,
            )
            session.novelty_candidate_reviews.update(novelty.get("reviews", {}))
            if novelty.get("selected") is not None:
                selected = novelty["selected"]
                session.novelty_resolution_attempt = max(session.novelty_resolution_attempt, int(novelty.get("attempts", 1)) - 1)
            selected["resolution_metadata"] = {
                "mode": "QUICK",
                "strategy": "seeded_structured_sampling",
                "seed": session.design_seed,
                "candidate_pool_size": len(session.character_explore_result),
                "selected_candidate_id": str(selected.get("id")),
                "novelty_resolution": novelty.get("resolution", "KEEP"),
            }
            return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "quick_ai_fill", delegated=True, rationale="Quick mode sampled one compatible Design DNA from the replayable candidate pool.")
        if gate == GateType.ART_DIRECTION_GATE:
            selected = select_seeded_candidate(session.art_explore_result, session.design_seed, salt="art-direction")
            initial_index = next((index for index, item in enumerate(session.art_explore_result) if item.get("id") == selected.get("id")), 0)
            novelty = NoveltyGuard.resolve_quick_candidates(
                session.art_explore_result,
                initial_index,
                policy=NoveltyPolicy.from_mapping(session.novelty_policy),
                history_snapshot=session.novelty_history_snapshot,
            )
            session.novelty_candidate_reviews.update(novelty.get("reviews", {}))
            if novelty.get("selected") is not None:
                selected = novelty["selected"]
                session.novelty_resolution_attempt = max(session.novelty_resolution_attempt, int(novelty.get("attempts", 1)) - 1)
            selected["resolution_metadata"] = {
                "mode": "QUICK",
                "strategy": "seeded_structured_sampling",
                "seed": session.design_seed,
                "candidate_pool_size": len(session.art_explore_result),
                "selected_candidate_id": str(selected.get("id")),
                "novelty_resolution": novelty.get("resolution", "KEEP"),
            }
            return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "quick_ai_fill", delegated=True, rationale="Quick mode sampled one compatible structured art path from the replayable candidate pool.")
        sheet = session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))
        for name, item in sheet["variables"].items():
            if item.get("user_selection") is None:
                item["user_selection"] = session.explicit_user_constraints.get(name, item["recommended"])
                item["selection_source"] = "explicit_user" if name in session.explicit_user_constraints else "quick_ai_fill"
                item["locked"] = True
        session.visual_preference_sheet = sheet
        return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"variables": _resolved_values(sheet)}, "quick_ai_fill", human_override=bool(session.explicit_user_constraints), delegated=True, rationale="Quick mode filled missing variables while retaining explicit constraints.")


class AIDecideGateResolver(GateResolver):
    """Full exploration with delegated AI selection and concise rationale."""

    def resolve(self, session: CreativeInteractionSession, gate_type: str | GateType, event: InteractionEvent | None = None, *, payload: Mapping[str, Any] | None = None) -> GateResolution:
        gate = str(_value(gate_type))
        if gate == GateType.CHARACTER_DIRECTION_GATE.value:
            filtered = NoveltyGuard.filter_ai_candidates(
                session.character_explore_result,
                policy=NoveltyPolicy.from_mapping(session.novelty_policy),
                history_snapshot=session.novelty_history_snapshot,
            )
            session.novelty_candidate_reviews.update(filtered["reviews"])
            selected = select_ai_candidate(filtered["candidates"] or session.character_explore_result)
            return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "delegated_ai", delegated=True, rationale="Generated and evaluated the full structural candidate pool before selecting the strongest coherent direction.")
        if gate == GateType.ART_DIRECTION_GATE:
            filtered = NoveltyGuard.filter_ai_candidates(
                session.art_explore_result,
                policy=NoveltyPolicy.from_mapping(session.novelty_policy),
                history_snapshot=session.novelty_history_snapshot,
            )
            session.novelty_candidate_reviews.update(filtered["reviews"])
            selected = select_ai_candidate(filtered["candidates"] or session.art_explore_result)
            return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "delegated_ai", delegated=True, rationale="Generated and evaluated the full structural art pool before selecting the strongest coherent direction.")
        sheet = session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))
        for name, item in sheet["variables"].items():
            if item.get("user_selection") is None:
                item["user_selection"] = session.explicit_user_constraints.get(name, item["recommended"])
                item["selection_source"] = "explicit_user" if name in session.explicit_user_constraints else "delegated_ai"
                item["locked"] = True
        session.visual_preference_sheet = sheet
        return GateResolution(self._gate(session, gate), gate, ResolutionStatus.RESOLVED.value, {"variables": _resolved_values(sheet)}, "delegated_ai", human_override=bool(session.explicit_user_constraints), delegated=True, rationale="AI selected the complete visual preference sheet on the user's delegation.")


def _action(event: InteractionEvent | None, payload: Mapping[str, Any] | None) -> str:
    if event is not None:
        return event.action.upper()
    return str((payload or {}).get("action", "")).upper()


def _payload(event: InteractionEvent | None, payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if event is not None:
        return dict(event.payload)
    return dict(payload or {})


def _candidate_resolution(session: CreativeInteractionSession, gate: str, event: InteractionEvent, candidates: Sequence[Mapping[str, Any]]) -> GateResolution:
    payload = event.payload
    action = event.action.upper()
    by_id = {str(item.get("id")): dict(item) for item in candidates}
    if "variable" in payload:
        raise ValueError("candidate gates accept candidate_id, not variable")
    if action in {InteractionAction.SELECT.value, InteractionAction.USE_RECOMMENDED.value, InteractionAction.USE_ALL_RECOMMENDED.value}:
        identifier = str(payload.get("candidate_id", payload.get("selection", payload.get("id", ""))))
        if action != InteractionAction.SELECT and not identifier:
            identifier = str(session.gate_payload.get("recommended", ""))
        if identifier not in by_id and len(identifier) == 1 and identifier.isalpha():
            index = ord(identifier.upper()) - ord("A")
            if 0 <= index < len(candidates):
                identifier = str(candidates[index].get("id"))
        if identifier not in by_id:
            raise ValueError(f"unknown candidate: {identifier}")
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.RESOLVED.value, {"direction": by_id[identifier]}, "human_select" if action == InteractionAction.SELECT.value else "human_accept_recommended", human_override=action == InteractionAction.SELECT.value, rationale=f"Human resolved the gate with direction {identifier}.")
    if action == InteractionAction.MIX.value:
        identifiers = payload.get("selections", payload.get("candidate_ids", payload.get("mix", [])))
        if isinstance(identifiers, str):
            identifiers = [item.strip() for item in identifiers.split("+") if item.strip()]
        identifiers = [
            candidates[ord(str(item).upper()) - ord("A")]["id"]
            if len(str(item)) == 1 and str(item).isalpha() and 0 <= ord(str(item).upper()) - ord("A") < len(candidates)
            else item
            for item in identifiers
        ]
        if not isinstance(identifiers, list) or len(identifiers) < 2 or any(str(item) not in by_id for item in identifiers):
            raise ValueError("MIX requires two or more valid candidate ids")
        selected = {"id": "+".join(map(str, identifiers)), "mix": [by_id[str(item)] for item in identifiers], "summary": " + ".join(by_id[str(item)]["summary"] for item in identifiers)}
        if payload.get("field_mix"):
            selected["field_mix"] = deepcopy(payload["field_mix"])
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "human_mix", human_override=True, rationale="Human combined the requested candidate directions.")
    if action == InteractionAction.CUSTOM.value:
        custom = payload.get("text", payload.get("custom", payload.get("description")))
        if not custom:
            raise ValueError("CUSTOM requires text")
        selected = {"id": "CUSTOM", "summary": str(custom), "custom": str(custom)}
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.RESOLVED.value, {"direction": selected}, "human_custom", human_override=True, rationale="Human supplied a custom direction.")
    if action == InteractionAction.DELEGATE.value:
        selected = max(candidates, key=lambda item: item.get("score", 0))
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.RESOLVED.value, {"direction": dict(selected)}, "delegated_ai", delegated=True, rationale="The current gate was explicitly delegated to AI.")
    if action == InteractionAction.PARTIAL_DELEGATE.value:
        selected = max(candidates, key=lambda item: item.get("score", 0))
        selected = {**selected, "human_fields": deepcopy(payload.get("values", {})), "delegated_fields": deepcopy(payload.get("delegated_fields", []))}
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.PARTIALLY_RESOLVED.value, {"direction": selected}, "delegated_ai", delegated=True, unresolved_fields=list(payload.get("delegated_fields", [])), rationale="Human fields were retained and remaining direction details were delegated.")
    raise ValueError(f"unsupported action for candidate gate: {event.action}")


def _resolved_values(sheet: Mapping[str, Any]) -> dict[str, Any]:
    return {name: item.get("user_selection") for name, item in sheet.get("variables", {}).items() if item.get("user_selection") is not None}


STRUCTURED_VISUAL_FIELDS = frozenset((*POSE_SPECIFICATION_FIELDS, *BACKGROUND_SPECIFICATION_FIELDS))


def _find_option(item: Mapping[str, Any], value: Any) -> str | None:
    for option in item.get("options", []):
        if option.get("value") == value:
            return str(option.get("id"))
    return None


def _apply_visual_value(sheet: dict[str, Any], name: str, *, source: str, option_id: str | None = None, value: Any = None, mix: list[Any] | None = None) -> None:
    variables = sheet.get("variables", {})
    if name not in variables:
        raise ValueError(f"unknown visual preference field: {name}")
    item = variables[name]
    if item.get("selection_source") == "explicit_user" and source != "explicit_user":
        raise ExplicitUserConstraintConflict(f"{name} is locked by the current user's explicit constraint")
    if option_id is not None:
        values = {str(option.get("id")): option.get("value") for option in item.get("options", [])}
        if option_id not in values:
            raise ValueError(f"unknown option {option_id} for {name}")
        value = values[option_id]
    if mix is not None:
        if not mix:
            raise ValueError("mix must contain at least one value")
        value = mix
    if value is None:
        raise ValueError(f"{name} requires option_id or value")
    if source == "human_custom" and not item.get("allow_custom", False):
        raise ValueError(f"custom selection is disabled for {name}")
    item.update(user_selection=deepcopy(value), selection_source=source, locked=False)


def _apply_visual_update(sheet: dict[str, Any], name: str, update: Any, default_source: str) -> None:
    if isinstance(update, Mapping):
        source = str(update.get("source") or ("human_select" if update.get("option_id") else default_source))
        value = update.get("value", update.get("custom"))
        if source == "human_accept_recommended" and update.get("option_id") is None and value is None and update.get("mix") is None and update.get("values") is None:
            value = sheet["variables"][name]["recommended"]
        _apply_visual_value(
            sheet,
            name,
            source=source,
            option_id=update.get("option_id"),
            value=value,
            mix=update.get("mix", update.get("values")),
        )
    else:
        _apply_visual_value(sheet, name, source=default_source, value=update)


def _apply_visual_event(session: CreativeInteractionSession, event: InteractionEvent) -> GateResolution:
    gate = GateType.VISUAL_PREFERENCE_GATE.value
    sheet = session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))
    action = event.action.upper()
    payload = event.payload
    if action in {InteractionAction.SELECT.value, InteractionAction.USE_RECOMMENDED.value, InteractionAction.CUSTOM.value, InteractionAction.MIX.value}:
        updates = payload.get("field_updates")
        if updates:
            default_source = {InteractionAction.SELECT.value: "human_select", InteractionAction.USE_RECOMMENDED.value: "human_accept_recommended", InteractionAction.CUSTOM.value: "human_custom", InteractionAction.MIX.value: "human_mix"}[action]
            for name, update in updates.items():
                if name == "field_mix":
                    continue
                if name in STRUCTURED_VISUAL_FIELDS and name not in sheet.get("variables", {}):
                    InteractionRuntime._record_constraint_update(session, name, update)
                    continue
                _apply_visual_update(sheet, name, update, default_source)
        else:
            name = str(payload.get("variable", ""))
            if not name:
                raise ValueError("visual preference action requires variable")
            source = {InteractionAction.SELECT.value: "human_select", InteractionAction.USE_RECOMMENDED.value: "human_accept_recommended", InteractionAction.CUSTOM.value: "human_custom", InteractionAction.MIX.value: "human_mix"}[action]
            value = payload.get("value", payload.get("custom", payload.get("text")))
            if action == InteractionAction.USE_RECOMMENDED.value and payload.get("option_id") is None and value is None:
                value = sheet["variables"][name]["recommended"]
            if name in STRUCTURED_VISUAL_FIELDS and name not in sheet.get("variables", {}):
                InteractionRuntime._record_constraint_update(session, name, {"value": value, "source": "explicit_user"})
                return GateResolution(
                    session.current_gate or "",
                    gate,
                    ResolutionStatus.PARTIALLY_RESOLVED.value,
                    {"variables": _resolved_values(sheet), "explicit_structured_fields": [name]},
                    "human_custom",
                    human_override=True,
                    rationale="User supplied an explicit structured pose/background field outside the compact preference sheet.",
                )
            _apply_visual_value(sheet, name, source=source, option_id=payload.get("option_id"), value=value, mix=payload.get("values") if action == InteractionAction.MIX.value else None)
    elif action == InteractionAction.USE_ALL_RECOMMENDED.value:
        for name, override in (payload.get("overrides") or payload.get("field_updates") or {}).items():
            _apply_visual_update(sheet, name, override, "human_custom")
        for name, item in sheet["variables"].items():
            if item.get("user_selection") is None:
                item.update(user_selection=deepcopy(item["recommended"]), selection_source="human_accept_recommended")
            item["locked"] = True
    elif action == InteractionAction.PARTIAL_DELEGATE.value:
        values = payload.get("values", payload.get("selections", payload.get("field_updates", {})))
        for name, override in values.items():
            _apply_visual_update(sheet, name, override, "human_custom")
        human_fields = set(payload.get("human_fields") or values.keys())
        for name, item in sheet["variables"].items():
            if item.get("user_selection") is None and name not in human_fields:
                item.update(user_selection=deepcopy(item["recommended"]), selection_source="delegated_ai")
            if item.get("user_selection") is not None:
                item["locked"] = True
    elif action == InteractionAction.DELEGATE.value:
        for name, item in sheet["variables"].items():
            if item.get("user_selection") is None:
                item.update(user_selection=deepcopy(item["recommended"]), selection_source="delegated_ai")
            item["locked"] = True
    else:
        raise ValueError(f"unsupported visual preference action: {event.action}")
    session.visual_preference_sheet = sheet
    unresolved = [name for name, item in sheet["variables"].items() if item.get("user_visible") and item.get("user_selection") is None]
    if unresolved:
        return GateResolution(session.current_gate or "", gate, ResolutionStatus.PARTIALLY_RESOLVED.value, {"variables": _resolved_values(sheet)}, unresolved_fields=unresolved, rationale="The sheet remains open so the user can resolve more visible fields.")
    _lock_with_existing_gate(sheet)
    for item in sheet["variables"].values():
        item["locked"] = True
    return GateResolution(session.current_gate or "", gate, ResolutionStatus.RESOLVED.value, {"variables": _resolved_values(sheet)}, _source_for_sheet(sheet), human_override=_has_human_source(sheet), delegated=_has_delegation_source(sheet), rationale="All visible preference fields now have an explicit or delegated source.")


def _source_for_sheet(sheet: Mapping[str, Any]) -> str:
    sources = {str(item.get("selection_source")) for item in sheet.get("variables", {}).values()}
    if "human_custom" in sources:
        return "human_custom"
    if "human_mix" in sources:
        return "human_mix"
    if "human_select" in sources:
        return "human_select"
    if "human_accept_recommended" in sources:
        return "human_accept_recommended"
    if "delegated_ai" in sources:
        return "delegated_ai"
    return "quick_ai_fill"


def _has_human_source(sheet: Mapping[str, Any]) -> bool:
    return any(str(item.get("selection_source", "")).startswith("human_") for item in sheet.get("variables", {}).values())


def _has_delegation_source(sheet: Mapping[str, Any]) -> bool:
    return any(item.get("selection_source") in {"delegated_ai", "quick_ai_fill"} for item in sheet.get("variables", {}).values())


def _lock_with_existing_gate(sheet: dict[str, Any]) -> None:
    bridge = deepcopy(sheet)
    source_map = {"human_select": "user", "human_mix": "mix", "human_custom": "custom", "human_accept_recommended": "ai_delegate", "delegated_ai": "ai_delegate", "quick_ai_fill": "ai_delegate", "explicit_user": "user"}
    for item in bridge["variables"].values():
        item["selection_source"] = source_map.get(item.get("selection_source"), item.get("selection_source"))
    gate = VisualPreferenceSession()
    gate.propose(bridge)
    gate.open_selection_gate()
    for name in IDENTITY_VARIABLES:
        item = bridge["variables"][name]
        source = item.get("selection_source")
        if source == "user":
            option_id = _find_option(item, item.get("user_selection"))
            if option_id:
                gate.select(name, option_id=option_id)
            else:
                gate.select(name, custom=item.get("user_selection"))
        elif source == "mix":
            gate.select(name, mix=item.get("user_selection"))
        elif source == "custom":
            gate.select(name, custom=item.get("user_selection"))
        else:
            gate.select(name, delegate_to_ai=True)
    gate.lock()


class UserDecideGateResolver(GateResolver):
    """Stops only at the three product gates and resumes on user events."""

    def resolve(self, session: CreativeInteractionSession, gate_type: str | GateType, event: InteractionEvent | None = None, *, payload: Mapping[str, Any] | None = None) -> GateResolution:
        gate = str(_value(gate_type))
        if event is None:
            return GateResolution(self._gate(session, gate), gate, ResolutionStatus.WAITING_FOR_USER.value, unresolved_fields=list(session.unresolved_fields), rationale="User Decide mode exposes this high-impact gate.")
        if gate == GateType.CHARACTER_DIRECTION_GATE.value:
            return _candidate_resolution(session, gate, event, session.character_explore_result)
        if gate == GateType.ART_DIRECTION_GATE.value:
            return _candidate_resolution(session, gate, event, session.art_explore_result)
        return _apply_visual_event(session, event)


class InteractionRuntime:
    """Create, persist, resume, and replay CreativeInteractionSession objects."""

    def __init__(self, session_root: str | Path = "sessions", *, novelty_policy: NoveltyPolicy | Mapping[str, Any] | None = None) -> None:
        self.session_root = Path(session_root)
        self.novelty_policy = novelty_policy if isinstance(novelty_policy, NoveltyPolicy) else NoveltyPolicy.from_mapping(novelty_policy)

    def _session_dir(self, session_id: str) -> Path:
        return self.session_root / session_id

    def _novelty_history_path(self) -> Path:
        return self.session_root / "novelty_history.json"

    def _load_novelty_history(self) -> list[dict[str, Any]]:
        path = self._novelty_history_path()
        if not path.is_file():
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        items = value.get("runs", []) if isinstance(value, Mapping) else value
        return [deepcopy(dict(item)) for item in items if isinstance(item, Mapping)]

    def _save_novelty_history(self, history: Sequence[Mapping[str, Any]]) -> None:
        self.session_root.mkdir(parents=True, exist_ok=True)
        path = self._novelty_history_path()
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(list(history), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def _record_novelty_history(self, session: CreativeInteractionSession) -> None:
        if session.inherit_previous_visuals or session.novelty_status in {None, "EXEMPT", "NOVELTY_EXHAUSTED"} or not session.design_signature:
            return
        generation = session.generation_artifact if isinstance(session.generation_artifact, Mapping) else {}
        record = {
            "run_id": str(generation.get("run_id") or session.session_id),
            "generation_id": str(generation.get("generation_id") or ""),
            "design_signature": deepcopy(session.design_signature),
            "created_at": str(generation.get("created_at") or session.created_at),
            "mode": session.creation_mode,
            "inheritance_status": "fresh",
        }
        history = self._load_novelty_history()
        history = [item for item in history if item.get("run_id") != record["run_id"]]
        history.append(record)
        self._save_novelty_history(history)

    def _save(self, session: CreativeInteractionSession) -> None:
        target = self._session_dir(session.session_id)
        target.mkdir(parents=True, exist_ok=True)
        artifacts = target / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)
        path = target / "session.json"
        temporary = target / "session.json.tmp"
        session.updated_at = _now()
        temporary.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        for name, value in (
            ("visual_preference_sheet.json", session.visual_preference_sheet),
            ("final_design.json", session.final_design),
            ("prompt_bundle.json", session.compiled_prompt),
            ("visual_adherence_review.json", session.visual_adherence_review),
            ("original_visual_adherence_review.json", session.original_visual_adherence_review),
            ("design_signature.json", session.design_signature),
            ("novelty_review.json", session.novelty_review),
            ("novelty_history_snapshot.json", session.novelty_history_snapshot),
            ("novelty_candidate_reviews.json", session.novelty_candidate_reviews),
        ):
            if value is None:
                continue
            artifact_tmp = artifacts / f"{name}.tmp"
            artifact_tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            artifact_tmp.replace(artifacts / name)
        for attempt in session.repair_attempts:
            attempt_id = str(attempt.get("attempt_id", ""))
            attempt_number = int(attempt.get("repair_attempt", 0) or 0)
            if not attempt_id or not attempt_number:
                continue
            attempt_dir = artifacts / "repair" / f"attempt_{attempt_number:02d}"
            attempt_dir.mkdir(parents=True, exist_ok=True)
            for name, value in (
                ("repair_plan.json", attempt.get("repair_plan")),
                ("visual_adherence_review.json", attempt.get("visual_adherence_review")),
                ("repair_result.json", attempt.get("repair_result")),
            ):
                if value is None:
                    continue
                artifact_tmp = attempt_dir / f"{name}.tmp"
                artifact_tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                artifact_tmp.replace(attempt_dir / name)
            prompt = attempt.get("repair_prompt")
            prompt_text = prompt.get("prompt") if isinstance(prompt, Mapping) else prompt
            if prompt_text:
                prompt_tmp = attempt_dir / "repair_prompt.txt.tmp"
                prompt_tmp.write_text(str(prompt_text), encoding="utf-8")
                prompt_tmp.replace(attempt_dir / "repair_prompt.txt")
            if attempt.get("generation") is not None:
                artifact_tmp = attempt_dir / "generation.json.tmp"
                artifact_tmp.write_text(json.dumps(attempt["generation"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                artifact_tmp.replace(attempt_dir / "generation.json")
        generation = session.generation_artifact
        if isinstance(generation, Mapping):
            original_dir = artifacts / "generation" / "original"
            original_dir.mkdir(parents=True, exist_ok=True)

            def write_generation_json(name: str, value: Any) -> None:
                artifact_tmp = original_dir / f"{name}.tmp"
                artifact_tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                artifact_tmp.replace(original_dir / name)

            write_generation_json("generation.json", generation)
            prompt_bundle = session.compiled_prompt or {}
            prompt_text = prompt_bundle.get("prompt") if isinstance(prompt_bundle, Mapping) else None
            if prompt_text:
                prompt_tmp = original_dir / "prompt.txt.tmp"
                prompt_tmp.write_text(str(prompt_text), encoding="utf-8")
                prompt_tmp.replace(original_dir / "prompt.txt")
                write_generation_json("prompt_bundle.json", prompt_bundle)
            manifest = prompt_bundle.get("prompt_adherence_manifest") if isinstance(prompt_bundle, Mapping) else None
            contract = prompt_bundle.get("visual_specification_contract") if isinstance(prompt_bundle, Mapping) else None
            if isinstance(manifest, Mapping):
                write_generation_json("prompt_adherence_manifest.json", manifest)
            if isinstance(contract, Mapping):
                write_generation_json("visual_specification_contract.json", contract)
            write_generation_json("image_metadata.json", {
                "generation_id": generation.get("generation_id"),
                "run_id": generation.get("run_id"),
                "image_path": generation.get("image_path"),
                "image_hash": generation.get("image_hash"),
                "created_at": generation.get("created_at"),
            })
            if session.original_visual_adherence_review is not None:
                write_generation_json("visual_adherence_review.json", session.original_visual_adherence_review)

    def _append_event(self, event: InteractionEvent) -> None:
        target = self._session_dir(event.session_id)
        target.mkdir(parents=True, exist_ok=True)
        with (target / "events.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def load_session(self, session_id: str) -> CreativeInteractionSession:
        target = self._session_dir(session_id)
        path = target / "session.json"
        if path.is_file():
            return CreativeInteractionSession.from_dict(json.loads(path.read_text(encoding="utf-8")))
        legacy = target / "creative_session.json"
        if legacy.is_file():
            return migrate_legacy_artifact(json.loads(legacy.read_text(encoding="utf-8")), session_id=session_id)
        raise FileNotFoundError(f"session not found: {session_id}")

    def create_session(self, user_input: str, mode: str | CreationMode | None = None, *, session_id: str | None = None, seed: Any = None) -> InteractiveResponse:
        constraints = _extract_constraints(user_input)
        firewall = VisualContextFirewall.from_request(user_input, constraints)
        resolved_session_id = uuid4().hex if session_id is None else session_id
        session = CreativeInteractionSession(
            resolved_session_id,
            detect_creation_mode(user_input, mode),
            user_input,
            explicit_user_constraints=constraints,
            inherit_previous_visuals=firewall.inherit_previous_visuals,
            allowed_visual_inheritance=list(firewall.allowed_visual_inheritance),
            blocked_context_sources=list(firewall.blocked_context_sources),
            visual_context_firewall_applied=firewall.visual_context_firewall_applied,
            style_inheritance_policy=firewall.style_inheritance_policy,
            design_seed=stable_session_seed(resolved_session_id) if seed is None else int(seed),
            artifact_continuity=ARTIFACT_CONTINUITY_PENDING,
            novelty_policy=self.novelty_policy.to_dict(),
        )
        self._save(session)
        if constraints.get("constraint_conflicts"):
            session.status = SessionStatus.BLOCKED.value
            session.audit_log.append({
                "event": "current_user_constraint_conflict",
                "error_code": "CURRENT_USER_CONSTRAINT_CONFLICT",
                "conflicts": list(constraints["constraint_conflicts"]),
            })
            self._save(session)
            return self._response(
                session,
                message="当前请求中的显式视觉要求互相冲突，未替你猜测取舍。",
                error_code="CURRENT_USER_CONSTRAINT_CONFLICT",
            )
        response = self._advance(session)
        self._save(session)
        return response

    def resume_session(self, session_id: str, interaction_event: InteractionEvent | Mapping[str, Any] | str) -> InteractiveResponse:
        session = self.load_session(session_id)
        event = self._coerce_event(session, interaction_event)
        if event.event_id in session.processed_event_responses:
            return InteractiveResponse.from_dict(session.processed_event_responses[event.event_id])
        if event.session_id != session.session_id:
            return self._error_response(session, "INVALID_SESSION_EVENT", "这个交互事件不属于当前 Session。")
        if session.current_gate and event.gate_id != session.current_gate:
            return self._error_response(session, "STALE_GATE_EVENT", "这个回复属于旧 Gate，当前状态没有改变。")
        snapshot = deepcopy(session.to_dict())
        previous = {"stage": session.current_stage, "status": session.status, "gate": session.current_gate}
        try:
            action = event.action.upper()
            if action == "INVALID":
                return self._error_response(session, "INVALID_INTERACTION", event.payload.get("clarification_reason") or "这句话还不能安全映射到当前步骤。")
            if action == "AMBIGUOUS":
                return self._error_response(session, "AMBIGUOUS_INTERACTION", event.payload.get("clarification_reason") or "请做一个最小选择。")
            if action != "QUESTION_ONLY":
                self._apply_visual_inheritance_request(session, event.payload.get("raw_text") or event.payload.get("text", ""))
            if action == "QUESTION_ONLY":
                response = self._question_response(session, event.payload.get("question") or event.payload.get("raw_text", ""))
            elif action == "CANCEL":
                response = self._cancel_session(session, event)
            elif action == InteractionAction.REGENERATE_OPTIONS.value:
                response = self._regenerate_options(session, event)
            elif action == "CONSTRAINT_UPDATE":
                response = self._apply_constraint_update(session, event)
            elif action == "CONTINUE":
                response = self._continue_session(session)
            else:
                switched = self._maybe_switch_mode(session, event)
                if switched and session.creation_mode == CreationMode.USER_DECIDE.value and session.current_stage in {PipelineStage.GENERATION_READY.value, PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value}:
                    if session.current_stage == PipelineStage.GENERATION_READY.value or session.current_gate:
                        self._reopen_visual_gate_for_user(session)
                    response = self._response(session, message="已切换到 USER_DECIDE。视觉变量现在交给你选择。")
                elif action == InteractionAction.BACK.value:
                    response = self._rollback(session, event)
                else:
                    response = self._advance(session, event)
        except ExplicitUserConstraintConflict as error:
            restored = CreativeInteractionSession.from_dict(snapshot)
            return self._error_response(restored, "CURRENT_USER_CONSTRAINT_CONFLICT", str(error))
        except (ValueError, KeyError, TypeError) as error:
            restored = CreativeInteractionSession.from_dict(snapshot)
            return self._error_response(restored, "INVALID_INTERACTION", str(error))
        session.interaction_history.append({"event": event.to_dict(), "previous_state": previous, "next_state": {"stage": session.current_stage, "status": session.status, "gate": session.current_gate}})
        session.processed_event_responses[event.event_id] = response.to_dict()
        session.last_response = response.to_dict()
        self._append_event(event)
        self._save(session)
        return response

    def _question_response(self, session: CreativeInteractionSession, question: str) -> InteractiveResponse:
        gate_type = session.gate_payload.get("gate_type")
        if gate_type in {GateType.CHARACTER_DIRECTION_GATE.value, GateType.ART_DIRECTION_GATE.value}:
            recommendation = session.gate_payload.get("recommended")
            message = f"我推荐 {recommendation}：它的身份锚点和轮廓辨识度更强。你仍可以选择其他方案，当前没有替你锁定。"
        elif gate_type == GateType.VISUAL_PREFERENCE_GATE.value:
            message = "当前推荐是为了保持身份、轮廓和规则一致；你仍可以逐项修改或接受推荐，当前没有替你锁定。"
        else:
            message = "我可以解释当前设计，但不会因为这个问题替你做选择。"
        return self._response(session, message=message)

    def _cancel_session(self, session: CreativeInteractionSession, event: InteractionEvent) -> InteractiveResponse:
        session.status = SessionStatus.CANCELLED.value
        session.current_gate = None
        session.gate_payload = {}
        session.unresolved_fields = []
        session.audit_log.append({"event": "cancel", "event_id": event.event_id, "reason": event.payload.get("raw_text", "explicit user cancellation")})
        return self._response(session, message="已取消这个角色设计 Session。")

    def _continue_session(self, session: CreativeInteractionSession) -> InteractiveResponse:
        if session.current_gate and session.unresolved_fields:
            return self._response(session, message="这里还需要你选择、接受推荐，或者交给我决定。")
        if session.status == SessionStatus.GENERATION_READY.value:
            return self._response(session, message="设计已经准备好，可以进入后续生成阶段。")
        return self._advance(session)

    def _apply_pending_constraints_to_sheet(self, session: CreativeInteractionSession) -> None:
        if session.visual_preference_sheet is None:
            return
        for name, update in session.pending_constraint_updates.items():
            if name not in session.visual_preference_sheet.get("variables", {}):
                continue
            _apply_visual_update(session.visual_preference_sheet, name, {**update, "source": "explicit_user"} if isinstance(update, Mapping) else update, "explicit_user")
            item = session.visual_preference_sheet["variables"][name]
            item["locked"] = True
            session.explicit_user_constraints[name] = deepcopy(item.get("user_selection"))
            if name not in session.explicit_user_constraints.get("explicit_user_fields", []):
                session.explicit_user_constraints.setdefault("explicit_user_fields", []).append(name)

    def _apply_constraint_update(self, session: CreativeInteractionSession, event: InteractionEvent) -> InteractiveResponse:
        updates = event.payload.get("field_updates", {})
        if not isinstance(updates, Mapping) or not updates:
            raise ValueError("CONSTRAINT_UPDATE requires field_updates")
        for name, update in updates.items():
            if not isinstance(name, str):
                continue
            self._record_constraint_update(session, name, update)
        self._apply_pending_constraints_to_sheet(session)
        message = "已记下这个明确要求。当前先完成方向选择，之后不会再重复问这个字段。" if session.current_gate and session.gate_payload.get("gate_type") != GateType.VISUAL_PREFERENCE_GATE.value else "已应用你的明确视觉要求；其他字段仍可按推荐或交给我。"
        return self._response(session, message=message)

    def _record_constraint_update(self, session: CreativeInteractionSession, name: str, update: Any) -> None:
        value = deepcopy(update)
        session.pending_constraint_updates[name] = value
        if isinstance(update, Mapping) and update.get("value") is not None:
            session.explicit_user_constraints[name] = deepcopy(update["value"])
        elif not isinstance(update, Mapping):
            session.explicit_user_constraints[name] = deepcopy(update)
        fields_list = session.explicit_user_constraints.setdefault("explicit_user_fields", [])
        if name not in fields_list:
            fields_list.append(name)
        session.audit_log.append({"event": "constraint_update", "field": name, "value": value, "source": "explicit_user", "pending": True})

    def _apply_visual_inheritance_request(self, session: CreativeInteractionSession, text: Any) -> None:
        if not str(text).strip():
            return
        constraints = _extract_constraints(str(text))
        firewall = VisualContextFirewall.from_request(str(text), constraints)
        if not firewall.inherit_previous_visuals:
            return
        session.inherit_previous_visuals = True
        session.allowed_visual_inheritance = list(firewall.allowed_visual_inheritance)
        session.blocked_context_sources = list(firewall.blocked_context_sources)
        session.visual_context_firewall_applied = True
        session.style_inheritance_policy = firewall.style_inheritance_policy
        if session.visual_preference_sheet is not None:
            session.visual_preference_sheet.update(firewall.to_dict())
        session.audit_log.append({"event": "visual_context_firewall", **firewall.to_dict(), "source": "explicit_user_request"})

    def _regenerate_options(self, session: CreativeInteractionSession, event: InteractionEvent) -> InteractiveResponse:
        gate_type = session.gate_payload.get("gate_type")
        count_key = "character_explore" if gate_type == GateType.CHARACTER_DIRECTION_GATE.value else "art_explore" if gate_type == GateType.ART_DIRECTION_GATE.value else None
        if count_key is None:
            raise ValueError("REGENERATE_OPTIONS is only valid at a direction gate")
        previous = session.character_explore_result if count_key == "character_explore" else session.art_explore_result
        count = session.retry_counts.get(count_key, 0) + 1
        session.retry_counts[count_key] = count
        depth = "low" if session.creation_mode == CreationMode.QUICK.value else "full"
        kind = "character" if count_key == "character_explore" else "art"
        generated = _directions(
            session.original_user_input,
            depth=depth,
            kind=kind,
            explicit_constraints=session.explicit_user_constraints,
            prior_resolutions=([{"direction": session.selected_character_direction}] if count_key == "art_explore" and session.selected_character_direction else ()),
            visual_context_firewall=_session_firewall(session),
            revision=count,
            seed=session.design_seed,
        )
        session.candidate_history.setdefault(count_key, []).append({"revision": count - 1, "options": deepcopy(previous), "reason": event.payload.get("raw_text", "user requested another set")})
        session.candidate_revisions[count_key] = count
        if count_key == "character_explore":
            session.character_explore_result = generated
            session.current_stage = PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value
        else:
            session.art_explore_result = generated
            session.current_stage = PipelineStage.ART_DIRECTION_RESOLUTION.value
        session.current_gate = None
        session.gate_payload = {}
        self._open_gate(session, GateType.CHARACTER_DIRECTION_GATE if count_key == "character_explore" else GateType.ART_DIRECTION_GATE, generated)
        session.audit_log.append({"event": "regenerate_options", "gate_type": gate_type, "reason": event.payload.get("raw_text", "user requested another set"), "previous_option_ids": [item.get("id") for item in previous], "new_option_ids": [item.get("id") for item in generated], "user_requested": True})
        return self._response(session, message="已换一批当前阶段的方向；之前的方案保留在历史里。")

    @staticmethod
    def _clear_novelty(session: CreativeInteractionSession) -> None:
        session.design_signature = None
        session.novelty_review = None
        session.novelty_history_snapshot = None
        session.novelty_candidate_reviews = {}
        session.novelty_resolution_attempt = 0
        session.novelty_status = None
        session.human_override_novelty = False

    def _novelty_alternative(self, session: CreativeInteractionSession) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]] | None:
        """Try one deterministic existing candidate without exposing history to design."""
        pools: list[tuple[str, list[dict[str, Any]], dict[str, Any] | None]] = [
            ("character", session.character_explore_result, session.selected_character_direction),
            ("art", session.art_explore_result, session.selected_art_direction),
        ]
        alternatives: list[tuple[str, dict[str, Any]]] = []
        for name, pool, selected in pools:
            current_id = str((selected or {}).get("id", ""))
            indices = [index for index, item in enumerate(pool) if str(item.get("id", "")) != current_id]
            if session.creation_mode == CreationMode.QUICK.value and selected:
                current_index = next((index for index, item in enumerate(pool) if str(item.get("id", "")) == current_id), -1)
                indices = list(range(current_index + 1, len(pool))) + list(range(0, max(0, current_index)))
            else:
                indices.sort(key=lambda index: (pool[index].get("score", 0), pool[index].get("recommendation_score", 0), -index), reverse=True)
            alternatives.extend((name, pool[index]) for index in indices)
        snapshot = session.novelty_history_snapshot or []
        remaining_attempts = max(0, self.novelty_policy.max_resolution_attempts - 1 - session.novelty_resolution_attempt)
        for offset, (name, candidate) in enumerate(alternatives[:remaining_attempts], start=1):
            attempt = session.novelty_resolution_attempt + offset
            probe = deepcopy(session)
            if name == "character":
                probe.selected_character_direction = deepcopy(candidate)
            else:
                probe.selected_art_direction = deepcopy(candidate)
            design = _build_final_design(probe)
            review = NoveltyGuard.evaluate(
                DesignSignature.from_final_design(design),
                policy=self.novelty_policy,
                history_snapshot=snapshot,
                resolution_attempt=attempt,
            )
            if review.novelty_result != "FAIL":
                return name, deepcopy(candidate), {"design": design, "review": review.to_dict()}
        return None

    def _evaluate_novelty(self, session: CreativeInteractionSession) -> bool:
        if session.novelty_history_snapshot is None:
            session.novelty_history_snapshot = NoveltyGuard.snapshot_history(self._load_novelty_history(), self.novelty_policy)
        signature = DesignSignature.from_final_design(session.final_design or {})
        review = NoveltyGuard.evaluate(
            signature,
            policy=self.novelty_policy,
            inherit_previous_visuals=session.inherit_previous_visuals,
            allowed_visual_inheritance=session.allowed_visual_inheritance,
            history_snapshot=session.novelty_history_snapshot,
            resolution_attempt=session.novelty_resolution_attempt,
        )
        if review.novelty_result == "FAIL" and session.creation_mode in {CreationMode.QUICK.value, CreationMode.AI_DECIDE.value}:
            alternative = self._novelty_alternative(session)
            if alternative is not None:
                name, candidate, resolved = alternative
                if name == "character":
                    session.selected_character_direction = candidate
                    session.locked_fields["character_direction"] = deepcopy(candidate)
                else:
                    session.selected_art_direction = candidate
                    session.locked_fields["art_direction"] = deepcopy(candidate)
                session.novelty_resolution_attempt += 1
                session.final_design = resolved["design"]
                signature = DesignSignature.from_final_design(session.final_design)
                review = NoveltyGuard.evaluate(
                    signature,
                    policy=self.novelty_policy,
                    history_snapshot=session.novelty_history_snapshot,
                    resolution_attempt=session.novelty_resolution_attempt,
                )
                session.audit_log.append({"event": "novelty_resolution", "resolution": "DETERMINISTIC_ALTERNATE", "candidate_id": candidate.get("id"), "source": name, "attempt": session.novelty_resolution_attempt})
        if review.novelty_result == "FAIL" and session.creation_mode == CreationMode.USER_DECIDE.value:
            user_result = NoveltyGuard.evaluate_user_candidate(
                session.final_design or {},
                policy=self.novelty_policy,
                history_snapshot=session.novelty_history_snapshot,
                explicit_fields=session.explicit_user_constraints.get("explicit_user_fields", ()),
                delegated_fields=session.delegated_fields,
            )
            session.human_override_novelty = bool(user_result["human_override_novelty"] or session.selected_character_direction or session.selected_art_direction)
            if user_result["delegated_reresolution_allowed"]:
                session.audit_log.append({"event": "novelty_delegated_reresolution_available", "matching_fields": user_result["delegated_matching_fields"]})
        session.design_signature = signature.to_dict()
        session.novelty_review = review.to_dict()
        session.novelty_status = review.novelty_result
        if session.final_design is not None:
            session.final_design["design_signature"] = deepcopy(session.design_signature)
            session.final_design["novelty_review"] = deepcopy(session.novelty_review)
            session.final_design["human_override_novelty"] = session.human_override_novelty
        session.audit_log.append({"event": "novelty_evaluated", "result": review.novelty_result, "nearest_prior_run": review.nearest_prior_run, "structural_similarity": review.structural_similarity, "overall_similarity": review.overall_similarity, "resolution_attempt": session.novelty_resolution_attempt})
        if review.novelty_result == "FAIL" and session.creation_mode in {CreationMode.QUICK.value, CreationMode.AI_DECIDE.value}:
            session.novelty_status = "NOVELTY_EXHAUSTED"
            session.artifact_status["novelty"] = "blocked"
            session.status = SessionStatus.BLOCKED.value
            return False
        session.artifact_status["novelty"] = review.novelty_result.lower()
        return True

    def replay_session(self, session_id: str) -> dict[str, Any]:
        session = self.load_session(session_id)
        events_path = self._session_dir(session_id) / "events.jsonl"
        events = []
        if events_path.is_file():
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        return {
            "session_id": session_id,
            "events": events,
            "audit_log": deepcopy(session.audit_log),
            "interaction_history": deepcopy(session.interaction_history),
            "generation_artifact": deepcopy(session.generation_artifact),
            "artifact_continuity": session.artifact_continuity,
            "design_signature": deepcopy(session.design_signature),
            "novelty_review": deepcopy(session.novelty_review),
            "novelty_history_snapshot": deepcopy(session.novelty_history_snapshot),
            "novelty_candidate_reviews": deepcopy(session.novelty_candidate_reviews),
            "novelty_policy": deepcopy(session.novelty_policy),
            "novelty_resolution_attempt": session.novelty_resolution_attempt,
            "novelty_status": session.novelty_status,
            "human_override_novelty": session.human_override_novelty,
            "visual_adherence_review": deepcopy(session.visual_adherence_review),
            "original_image": session.original_image,
            "original_visual_adherence_review": deepcopy(session.original_visual_adherence_review),
            "repair_attempts": deepcopy(session.repair_attempts),
            "best_artifact": deepcopy(session.best_artifact),
            "repair_status": session.repair_status,
            "face_aesthetic_contract": deepcopy(session.face_aesthetic_contract or (session.final_design or {}).get("face_aesthetic_contract", {})),
        }

    def record_generation_artifact(
        self,
        session_id: str,
        image: str | Path,
        *,
        run_id: str | None = None,
        generation_id: str | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        """Persist the externally generated original image and its exact inputs."""
        image_path = Path(image)
        if not image_path.is_file():
            raise VisualRepairError("generation artifact must provide an existing image")
        session = self.load_session(session_id)
        if session.current_stage != PipelineStage.GENERATION_READY.value:
            raise VisualRepairError("generation artifact requires GENERATION_READY")
        prompt_bundle = session.compiled_prompt or {}
        manifest = prompt_bundle.get("prompt_adherence_manifest") if isinstance(prompt_bundle, Mapping) else None
        contract = prompt_bundle.get("visual_specification_contract") if isinstance(prompt_bundle, Mapping) else None
        prompt = prompt_bundle.get("prompt") if isinstance(prompt_bundle, Mapping) else None
        if not isinstance(prompt, str) or not prompt.strip() or not isinstance(manifest, Mapping) or not isinstance(contract, Mapping):
            raise VisualRepairError("generation artifact requires the current PromptBundle, manifest, and contract")
        if session.design_signature is None or session.novelty_review is None:
            if not self._evaluate_novelty(session):
                raise VisualRepairError("NOVELTY_EXHAUSTED")
        computed_prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        if prompt_hash is not None and prompt_hash != computed_prompt_hash:
            raise VisualRepairError("generation prompt hash does not match the persisted PromptBundle")
        image_hash = sha256(image_path.read_bytes()).hexdigest()
        resolved_run_id = str(run_id or session_id)
        resolved_generation_id = str(generation_id or f"{resolved_run_id}:original")
        existing = session.generation_artifact
        if isinstance(existing, Mapping):
            if all(
                existing.get(name) == value
                for name, value in {
                    "generation_id": resolved_generation_id,
                    "image_hash": image_hash,
                    "prompt_hash": computed_prompt_hash,
                }.items()
            ):
                self._record_novelty_history(session)
                return deepcopy(dict(existing))
            raise VisualRepairError("GENERATION_ARTIFACT_MISMATCH")
        artifact = GenerationArtifact(
            generation_id=resolved_generation_id,
            run_id=resolved_run_id,
            image_path=str(image_path),
            image_hash=image_hash,
            prompt_hash=computed_prompt_hash,
            prompt_bundle_ref="artifacts/generation/original/prompt_bundle.json",
            manifest_ref="artifacts/generation/original/prompt_adherence_manifest.json",
            contract_ref="artifacts/generation/original/visual_specification_contract.json",
            mode=session.creation_mode,
            design_seed=session.design_seed,
            created_at=_now(),
            face_aesthetic_profile=str((session.final_design or {}).get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE)),
            face_aesthetic_source=str((session.final_design or {}).get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE)),
        )
        session.generation_artifact = artifact.to_dict()
        session.artifact_continuity = ARTIFACT_CONTINUITY_COMPLETE
        session.artifact_status["generation"] = "complete"
        self._record_novelty_history(session)
        session.audit_log.append({"event": "generation_artifact_recorded", **artifact.to_dict()})
        self._save(session)
        return artifact.to_dict()

    def _legacy_generation_artifact(self, session: CreativeInteractionSession, image: str | Path) -> dict[str, Any]:
        image_path = Path(image)
        prompt = str((session.compiled_prompt or {}).get("prompt", ""))
        return {
            "generation_id": f"legacy:{session.session_id}:original",
            "run_id": session.session_id,
            "image_path": str(image_path),
            "image_hash": sha256(image_path.read_bytes()).hexdigest(),
            "prompt_hash": sha256(prompt.encode("utf-8")).hexdigest() if prompt else "",
            "prompt_bundle_ref": "",
            "manifest_ref": "",
            "contract_ref": "",
            "mode": session.creation_mode,
            "design_seed": session.design_seed,
            "created_at": session.created_at,
            "face_aesthetic_profile": str((session.final_design or {}).get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE)),
            "face_aesthetic_source": str((session.final_design or {}).get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE)),
        }

    @staticmethod
    def _strict_generation_artifact(session: CreativeInteractionSession) -> Mapping[str, Any]:
        artifact = session.generation_artifact
        if session.artifact_continuity != ARTIFACT_CONTINUITY_COMPLETE or not isinstance(artifact, Mapping):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: strict generation artifact is required")
        required = ("generation_id", "image_path", "image_hash", "prompt_hash")
        if any(not artifact.get(name) for name in required):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: incomplete generation artifact")
        return artifact

    @staticmethod
    def _validate_repair_source(review: Mapping[str, Any], artifact: Mapping[str, Any]) -> None:
        image_path = Path(str(review.get("actual_image", "")))
        if not image_path.is_file():
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: image is missing")
        image_hash = sha256(image_path.read_bytes()).hexdigest()
        if artifact.get("image_hash") != image_hash or (review.get("actual_image_hash") and review.get("actual_image_hash") != artifact.get("image_hash")):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: image hash")
        if artifact.get("prompt_hash") != review.get("prompt_hash"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: prompt hash")
        if artifact.get("generation_id") != review.get("generation_id"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: generation id")

    def _review_generation_artifact(self, session: CreativeInteractionSession, actual_image: str | Path) -> Mapping[str, Any]:
        image_path = Path(actual_image)
        if not image_path.is_file():
            raise VisualRepairError("generation review must provide an existing image")
        artifact = session.generation_artifact
        if not isinstance(artifact, Mapping):
            if session.artifact_continuity != ARTIFACT_CONTINUITY_LEGACY:
                raise VisualRepairError("GENERATION_ARTIFACT_REQUIRED")
            artifact = self._legacy_generation_artifact(session, image_path)
            session.generation_artifact = dict(artifact)
        actual_hash = sha256(image_path.read_bytes()).hexdigest()
        if artifact.get("image_hash") != actual_hash:
            raise VisualRepairError("REVIEW_SOURCE_MISMATCH: image hash")
        prompt = str((session.compiled_prompt or {}).get("prompt", ""))
        expected_prompt_hash = sha256(prompt.encode("utf-8")).hexdigest()
        if artifact.get("prompt_hash") != expected_prompt_hash:
            raise VisualRepairError("REVIEW_SOURCE_MISMATCH: prompt hash")
        return artifact

    def record_visual_adherence_review(
        self,
        session_id: str,
        actual_image: str | Path,
        *,
        observations: Mapping[str, Any],
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        """Persist one post-generation actual-image review for replay."""
        session = self.load_session(session_id)
        artifact = self._review_generation_artifact(session, actual_image)
        if prompt_hash is not None and prompt_hash != artifact.get("prompt_hash"):
            raise VisualRepairError("REVIEW_SOURCE_MISMATCH: prompt hash")
        final_design = session.final_design or {}
        prompt_bundle = session.compiled_prompt or {}
        manifest = prompt_bundle.get("prompt_adherence_manifest") or final_design.get("prompt_adherence_manifest")
        if not isinstance(manifest, Mapping):
            raise ValueError("VisualAdherenceCritic requires a PromptAdherenceManifest")
        review = VisualAdherenceCritic().review(
            actual_image,
            manifest=manifest,
            observations=observations,
            visual_specification_contract=prompt_bundle.get("visual_specification_contract") or final_design.get("visual_specification_contract"),
            final_design=final_design,
            prompt_bundle_metadata=prompt_bundle,
            prompt_hash=prompt_hash,
            generation_id=str(artifact.get("generation_id")),
        )
        session.visual_adherence_review = review.to_dict()
        if session.original_visual_adherence_review is None:
            session.original_image = str(actual_image)
            session.original_visual_adherence_review = review.to_dict()
            session.best_artifact = initial_best_artifact(review, actual_image, generation_artifact=artifact)
        session.repair_status = "ACCEPTED" if review.overall_result == "PASS" else "ADHERENCE_REVIEWED"
        session.artifact_status["visual_adherence_review"] = "fresh"
        session.audit_log.append(
            {
                "event": "visual_adherence_review",
                "actual_image": str(actual_image),
                "overall_result": review.overall_result,
                "failure_types": list(review.failure_types),
            }
        )
        self._save(session)
        return review.to_dict()

    def build_visual_repair_plan(
        self,
        session_id: str,
        *,
        max_attempts: int = MAX_REPAIR_ATTEMPTS,
        include_minor: bool = True,
    ) -> dict[str, Any]:
        """Prepare one idempotent repair attempt; ImageGen remains external."""
        session = self.load_session(session_id)
        generation_artifact = self._strict_generation_artifact(session)
        review_data = session.visual_adherence_review
        if not isinstance(review_data, Mapping):
            raise VisualRepairError("a current VisualAdherenceReview is required before repair planning")
        self._validate_repair_source(review_data, generation_artifact)
        for attempt in reversed(session.repair_attempts):
            if attempt.get("repair_result", {}).get("status") in {"PENDING_GENERATION", "PENDING_REVIEW"}:
                return {"status": session.repair_status or "REPAIR_GENERATED", **deepcopy(attempt)}
        if not session.repair_attempts and str(review_data.get("overall_result")) == "PASS":
            session.repair_status = "ACCEPTED"
            self._save(session)
            return {"status": "ACCEPTED", "repair_plan": None, "repair_prompt": None}
        attempt_number = len(session.repair_attempts) + 1
        if attempt_number > max_attempts:
            session.repair_status = "REPAIR_EXHAUSTED"
            self._save(session)
            return {"status": "REPAIR_EXHAUSTED", "repair_plan": None, "repair_prompt": None}
        prompt_bundle = session.compiled_prompt or {}
        manifest = prompt_bundle.get("prompt_adherence_manifest") or (session.final_design or {}).get("prompt_adherence_manifest")
        contract = prompt_bundle.get("visual_specification_contract") or (session.final_design or {}).get("visual_specification_contract")
        plan = build_repair_plan(
            review_data,
            manifest=manifest if isinstance(manifest, Mapping) else None,
            visual_specification_contract=contract if isinstance(contract, Mapping) else None,
            explicit_hard_fields=tuple((contract or {}).get("explicit_hard_fields", ())) if isinstance(contract, Mapping) else (),
            repair_attempt=attempt_number,
            max_attempts=max_attempts,
            include_minor=include_minor,
            generation_artifact=generation_artifact,
        )
        if not plan.repair_targets:
            session.repair_status = "ACCEPTED" if not review_data.get("repair_targets") else "ADHERENCE_REVIEWED"
            self._save(session)
            return {"status": session.repair_status, "repair_plan": plan.to_dict(), "repair_prompt": None}
        repair_prompt = compile_repair_prompt(prompt_bundle, plan)
        attempt = {
            "attempt_id": plan.attempt_id,
            "repair_attempt": plan.repair_attempt,
            "repair_plan": plan.to_dict(),
            "repair_prompt": repair_prompt.to_dict(),
            "before_review": deepcopy(dict(review_data)),
            "repair_result": {"status": "PENDING_GENERATION", "attempt_id": plan.attempt_id},
            "source_generation_id": plan.source_generation_id,
        }
        session.repair_attempts.append(attempt)
        session.repair_status = "REPAIR_PLANNED"
        session.audit_log.append({"event": "visual_repair_planned", "attempt_id": plan.attempt_id, "repair_targets": [item.get("field") for item in plan.repair_targets]})
        self._save(session)
        return {"status": "REPAIR_PLANNED", **deepcopy(attempt)}

    def record_visual_repair_generation(
        self,
        session_id: str,
        attempt_id: str,
        repair_image: str | Path,
        *,
        repair_prompt: str | None = None,
        prompt_hash: str | None = None,
    ) -> dict[str, Any]:
        """Record an externally generated repair image without generating it."""
        image = Path(repair_image)
        if not image.is_file():
            raise VisualRepairError("repair generation must provide an existing image")
        session = self.load_session(session_id)
        source_artifact = self._strict_generation_artifact(session)
        attempt = next((item for item in session.repair_attempts if item.get("attempt_id") == attempt_id), None)
        if attempt is None:
            raise VisualRepairError(f"unknown repair attempt: {attempt_id}")
        existing = attempt.get("generation")
        if isinstance(existing, Mapping):
            return {"status": "REPAIR_GENERATED", **deepcopy(dict(existing))}
        stored_prompt = (attempt.get("repair_prompt") or {}).get("prompt")
        if repair_prompt is not None and str(repair_prompt) != str(stored_prompt):
            raise VisualRepairError("repair_prompt must equal the persisted RepairPromptBundle prompt")
        if not stored_prompt:
            raise VisualRepairError("repair attempt has no compiled repair prompt")
        computed_hash = sha256(str(stored_prompt).encode("utf-8")).hexdigest()
        if prompt_hash is not None and prompt_hash != computed_hash:
            raise VisualRepairError("repair prompt hash does not match the persisted prompt")
        plan = VisualRepairPlan.from_dict(attempt["repair_plan"])
        if plan.source_generation_id != source_artifact.get("generation_id"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: generation id")
        generation = {
            "generation_id": f"{source_artifact['generation_id']}:repair:{plan.repair_attempt}",
            "source_generation_id": source_artifact["generation_id"],
            "image": str(image),
            "image_path": str(image),
            "image_hash": sha256(image.read_bytes()).hexdigest(),
            "prompt_hash": computed_hash,
            "attempt_id": attempt_id,
        }
        attempt["generation"] = generation
        attempt["repair_result"] = {"status": "PENDING_REVIEW", "attempt_id": attempt_id, "repair_attempt": attempt.get("repair_attempt"), "repair_image": str(image), "image_hash": generation["image_hash"], "prompt_hash": computed_hash, "source_generation_id": source_artifact["generation_id"]}
        session.repair_status = "REPAIR_GENERATED"
        session.audit_log.append({"event": "visual_repair_generated", **generation})
        self._save(session)
        return {"status": "REPAIR_GENERATED", **deepcopy(generation)}

    def record_visual_repair_review(
        self,
        session_id: str,
        attempt_id: str,
        *,
        observations: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Critic-review one repair image and persist comparison/best artifact."""
        session = self.load_session(session_id)
        source_artifact = self._strict_generation_artifact(session)
        attempt = next((item for item in session.repair_attempts if item.get("attempt_id") == attempt_id), None)
        if attempt is None:
            raise VisualRepairError(f"unknown repair attempt: {attempt_id}")
        stored_result = attempt.get("repair_result")
        if isinstance(stored_result, Mapping) and stored_result.get("outcome"):
            return deepcopy(dict(stored_result))
        generation = attempt.get("generation")
        if not isinstance(generation, Mapping):
            raise VisualRepairError("repair review requires a recorded repair generation")
        if generation.get("source_generation_id") != source_artifact.get("generation_id"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: generation id")
        if not Path(str(generation.get("image_path", generation.get("image", "")))).is_file():
            raise VisualRepairError("repair generation image is missing")
        if generation.get("image_hash") != sha256(Path(str(generation.get("image_path", generation.get("image")))).read_bytes()).hexdigest():
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: image hash")
        before = VisualAdherenceReview.from_dict(attempt["before_review"])
        plan = VisualRepairPlan.from_dict(attempt["repair_plan"])
        prompt_bundle = session.compiled_prompt or {}
        manifest = prompt_bundle.get("prompt_adherence_manifest") or (session.final_design or {}).get("prompt_adherence_manifest")
        if not isinstance(manifest, Mapping):
            raise VisualRepairError("VisualAdherenceCritic requires a PromptAdherenceManifest")
        after = VisualAdherenceCritic().review(
            generation["image"],
            manifest=manifest,
            observations=observations,
            visual_specification_contract=prompt_bundle.get("visual_specification_contract") or (session.final_design or {}).get("visual_specification_contract"),
            final_design=session.final_design or {},
            prompt_bundle_metadata={**prompt_bundle, "prompt": attempt["repair_prompt"]["prompt"]},
            prompt_hash=generation.get("prompt_hash"),
            generation_id=str(generation.get("generation_id")),
        )
        comparison = evaluate_repair_attempt(before, after, plan)
        candidate = {
            "image": generation["image"],
            "image_path": generation.get("image_path", generation["image"]),
            "image_hash": generation.get("image_hash"),
            "prompt_hash": generation.get("prompt_hash"),
            "review_id": after.review_id,
            "generation_id": generation.get("generation_id"),
            "source_type": "repair",
            "attempt_id": attempt_id,
            "overall_result": after.overall_result,
        }
        explicit = tuple(
            (prompt_bundle.get("visual_specification_contract") or {}).get("explicit_hard_fields", ())
            if isinstance(prompt_bundle.get("visual_specification_contract"), Mapping)
            else ()
        )
        current_best = session.best_artifact or initial_best_artifact(before, before.actual_image, generation_artifact=source_artifact)
        best = select_best_artifact(current_best, candidate, before, after, explicit_fields=explicit, outcome=comparison["outcome"])
        attempt["visual_adherence_review"] = after.to_dict()
        attempt["repair_result"] = {**comparison, "status": "REPAIR_REVIEWED", "best_artifact": best}
        session.visual_adherence_review = after.to_dict()
        session.best_artifact = best
        if comparison["outcome"] == "SUCCESS":
            session.repair_status = "ACCEPTED"
        elif len(session.repair_attempts) >= plan.max_attempts:
            session.repair_status = "REPAIR_EXHAUSTED"
        else:
            session.repair_status = "REPAIR_REVIEWED"
        session.audit_log.append({"event": "visual_repair_reviewed", "attempt_id": attempt_id, "outcome": comparison["outcome"], "regressions": comparison["regressions"]})
        self._save(session)
        return deepcopy(attempt["repair_result"])

    def switch_mode(self, session_id: str, to_mode: str | CreationMode, *, reason: str = "explicit user request") -> InteractiveResponse:
        session = self.load_session(session_id)
        event = InteractionEvent(uuid4().hex, session_id, session.current_gate or "", InteractionAction.DELEGATE.value, {"to_mode": str(_value(to_mode)), "reason": reason})
        return self.resume_session(session_id, event)

    def _coerce_event(self, session: CreativeInteractionSession, event: InteractionEvent | Mapping[str, Any] | str) -> InteractionEvent:
        if isinstance(event, InteractionEvent):
            return event
        if isinstance(event, Mapping):
            data = dict(event)
            data.setdefault("session_id", session.session_id)
            data.setdefault("gate_id", session.current_gate or "")
            data.setdefault("event_id", uuid4().hex)
            return InteractionEvent.from_dict(data)
        text = str(event).strip()
        context = {
            "current_stage": session.current_stage,
            "current_gate": session.current_gate,
            "gate_type": session.gate_payload.get("gate_type"),
            "options": session.gate_payload.get("options", []),
            "visual_variables": (session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))).get("variables", {}),
            "recommended": session.gate_payload.get("recommended"),
            "mode": session.creation_mode,
            "unresolved_fields": list(session.unresolved_fields),
            "locked_fields": deepcopy(session.locked_fields),
        }
        intent = NaturalLanguageInteractionParser().parse(text, context)
        payload = intent.to_payload()
        if intent.selected_options:
            payload["candidate_id"] = intent.selected_options[0]
            payload["selections"] = list(intent.selected_options)
        if intent.field_updates.get("field_mix"):
            payload["field_mix"] = deepcopy(intent.field_updates["field_mix"])
        if intent.mode_switch_target:
            payload["to_mode"] = intent.mode_switch_target
        if intent.target_gate:
            payload["target"] = intent.target_gate
        if intent.action is None:
            action = intent.intent_type
        else:
            action = intent.action
        if intent.intent_type == "CUSTOM_UPDATE" and intent.field_updates:
            payload["field_updates"] = deepcopy(intent.field_updates)
        if action == InteractionAction.CUSTOM.value and not payload.get("field_updates"):
            payload["text"] = text
        return InteractionEvent(uuid4().hex, session.session_id, session.current_gate or "", action, payload)

    def _resolver(self, session: CreativeInteractionSession) -> GateResolver:
        return {CreationMode.QUICK.value: QuickGateResolver, CreationMode.AI_DECIDE.value: AIDecideGateResolver, CreationMode.USER_DECIDE.value: UserDecideGateResolver}.get(session.creation_mode, AIDecideGateResolver)()

    def _advance(self, session: CreativeInteractionSession, event: InteractionEvent | None = None) -> InteractiveResponse:
        resolver = self._resolver(session)
        pending_event = event
        while True:
            session.status = SessionStatus.RUNNING.value
            stage = session.current_stage
            if stage == PipelineStage.INPUT.value:
                session.current_stage = PipelineStage.CHARACTER_EXPLORE.value
                continue
            if stage == PipelineStage.CHARACTER_EXPLORE.value:
                depth = "low" if session.creation_mode == CreationMode.QUICK.value else "full"
                if session.novelty_history_snapshot is None:
                    session.novelty_history_snapshot = NoveltyGuard.snapshot_history(self._load_novelty_history(), self.novelty_policy)
                session.candidate_revisions["character_explore"] = 0
                session.character_explore_result = _directions(session.original_user_input, depth=depth, kind="character", explicit_constraints=session.explicit_user_constraints, visual_context_firewall=_session_firewall(session), seed=session.design_seed)
                session.current_stage = PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value
                self._open_gate(session, GateType.CHARACTER_DIRECTION_GATE, session.character_explore_result)
                resolution = resolver.resolve(session, GateType.CHARACTER_DIRECTION_GATE, pending_event)
                pending_event = None
                if not self._accept_resolution(session, resolution):
                    return self._response(session)
                continue
            if stage == PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value:
                resolution = resolver.resolve(session, GateType.CHARACTER_DIRECTION_GATE, pending_event)
                pending_event = None
                if not self._accept_resolution(session, resolution):
                    return self._response(session)
                continue
            if stage == PipelineStage.CHARACTER_PLANNING.value:
                direction = session.selected_character_direction or {}
                session.character_plan = {"premise": session.original_user_input, "design_thesis": direction.get("design_thesis", "specific playable identity"), "player_fantasy": "recognizable character with a clear anchor", "open_questions": [], "provenance": "shared_pipeline"}
                session.current_stage = PipelineStage.ART_EXPLORE.value
                continue
            if stage == PipelineStage.ART_EXPLORE.value:
                depth = "low" if session.creation_mode == CreationMode.QUICK.value else "full"
                session.candidate_revisions["art_explore"] = 0
                session.art_explore_result = _directions(
                    session.original_user_input,
                    depth=depth,
                    kind="art",
                    explicit_constraints=session.explicit_user_constraints,
                    prior_resolutions=([{"direction": session.selected_character_direction}] if session.selected_character_direction else ()),
                    visual_context_firewall=_session_firewall(session),
                    seed=session.design_seed,
                )
                session.current_stage = PipelineStage.ART_DIRECTION_RESOLUTION.value
                self._open_gate(session, GateType.ART_DIRECTION_GATE, session.art_explore_result)
                resolution = resolver.resolve(session, GateType.ART_DIRECTION_GATE, pending_event)
                pending_event = None
                if not self._accept_resolution(session, resolution):
                    return self._response(session)
                continue
            if stage == PipelineStage.ART_DIRECTION_RESOLUTION.value:
                resolution = resolver.resolve(session, GateType.ART_DIRECTION_GATE, pending_event)
                pending_event = None
                if not self._accept_resolution(session, resolution):
                    return self._response(session)
                continue
            if stage == PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value:
                if session.visual_preference_sheet is None:
                    session.visual_preference_sheet = _visual_sheet(
                        session.explicit_user_constraints,
                        original_input=session.original_user_input,
                        prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}],
                        visual_context_firewall=_session_firewall(session),
                    )
                self._apply_pending_constraints_to_sheet(session)
                self._open_gate(session, GateType.VISUAL_PREFERENCE_GATE, _visual_gate_options(session.visual_preference_sheet))
                resolution = resolver.resolve(session, GateType.VISUAL_PREFERENCE_GATE, pending_event)
                pending_event = None
                if not self._accept_resolution(session, resolution):
                    return self._response(session)
                continue
            if stage == PipelineStage.FINAL_DESIGN.value:
                session.status = SessionStatus.FINAL_DESIGNING.value
                if session.explicit_user_constraints.get("force_design_failure") and session.retry_counts.get("final_design", 0) == 0:
                    session.retry_counts["final_design"] = 1
                    session.audit_log.append({"event": "design_direction_failure", "reason": "deterministic requested failure", "retry": 1})
                    if session.creation_mode == CreationMode.USER_DECIDE.value:
                        session.current_stage = PipelineStage.ART_DIRECTION_RESOLUTION.value
                        self._open_gate(session, GateType.ART_DIRECTION_GATE, session.art_explore_result)
                        return self._response(session, message="当前视觉方向未通过设计 Gate，请重新选择、CUSTOM 或 DELEGATE。")
                session.final_design = _build_final_design(session)
                session.artifact_status["final_design"] = "fresh"
                if not self._evaluate_novelty(session):
                    return self._response(session, message="当前设计与近期角色结构过度相似，NoveltyGuard 已耗尽有界替代尝试。", error_code="NOVELTY_EXHAUSTED")
                session.current_stage = PipelineStage.PLAYABLE_CHARACTER_DESIGN_GATE.value
                continue
            if stage == PipelineStage.PLAYABLE_CHARACTER_DESIGN_GATE.value:
                session.status = SessionStatus.DESIGN_VALIDATING.value
                session.design_gate_result = _design_gate(session.final_design or {})
                if session.design_gate_result["result"] != "PASS":
                    session.status = SessionStatus.BLOCKED.value
                    return self._response(session, message="Final Design 未通过硬规则，未进入 PromptCompiler。")
                session.current_stage = PipelineStage.PROMPT_COMPILATION.value
                continue
            if stage == PipelineStage.PROMPT_COMPILATION.value:
                session.status = SessionStatus.PROMPT_COMPILING.value
                try:
                    compiled = PromptCompiler().compile(**_compiler_args(session.final_design or {}))
                except PromptConstraintConflict as error:
                    session.status = SessionStatus.BLOCKED.value
                    session.audit_log.append(
                        {
                            "event": "prompt_constraint_conflict",
                            "error_code": error.code,
                            "conflicts": list(error.conflicts),
                        }
                    )
                    session.artifact_status["compiled_prompt"] = "blocked"
                    return self._response(
                        session,
                        message="Prompt 视觉规格存在冲突，未进入 GENERATION_READY。",
                        error_code=error.code,
                    )
                session.compiled_prompt = compiled.to_dict()
                coverage = ExplicitConstraintCoverageGate.evaluate(session.compiled_prompt)
                session.compiled_prompt["explicit_constraint_coverage"] = coverage
                session.compiled_prompt["generation_allowed"] = coverage["generation_allowed"]
                contract = session.compiled_prompt.get("visual_specification_contract")
                if isinstance(contract, dict):
                    if coverage["fields"]:
                        contract["explicit_constraint_coverage"] = deepcopy(coverage)
                        contract["generation_allowed"] = coverage["generation_allowed"]
                    session.compiled_prompt["prompt_adherence_manifest"] = deepcopy(contract)
                if not coverage["generation_allowed"]:
                    session.status = SessionStatus.BLOCKED.value
                    session.artifact_status["compiled_prompt"] = "blocked"
                    session.audit_log.append({
                        "event": "explicit_constraint_coverage_failed",
                        "error_code": "EXPLICIT_CONSTRAINT_COVERAGE_FAILED",
                        "blocking_fields": coverage["blocking_fields"],
                    })
                    return self._response(
                        session,
                        message="显式用户硬约束未完整进入 PromptBundle，未进入 GENERATION_READY。",
                        error_code="EXPLICIT_CONSTRAINT_COVERAGE_FAILED",
                    )
                session.artifact_status["compiled_prompt"] = "fresh"
                session.current_stage = PipelineStage.GENERATION_READY.value
                session.status = SessionStatus.GENERATION_READY.value
                session.current_gate = None
                session.gate_payload = {}
                session.unresolved_fields = []
                return self._response(session)
            raise ValueError(f"unsupported pipeline stage: {stage}")

    def _accept_resolution(self, session: CreativeInteractionSession, resolution: GateResolution) -> bool:
        if resolution.resolution_status in {ResolutionStatus.WAITING_FOR_USER.value, ResolutionStatus.PARTIALLY_RESOLVED.value}:
            session.unresolved_fields = list(resolution.unresolved_fields or _gate_unresolved(session))
            session.status = _waiting_status(session.current_gate)
            return False
        if resolution.resolution_status != ResolutionStatus.RESOLVED.value:
            session.status = SessionStatus.FAILED.value
            return False
        gate = resolution.gate_type
        previous_gate = session.current_gate
        session.audit_log.append({"event": "gate_resolution", "gate_id": resolution.gate_id, "gate_type": gate, "resolution": resolution.to_dict(), "affected_fields": list(resolution.selected_values), "invalidated_artifacts": []})
        session.interaction_history.append({"type": "gate_resolution", "gate_id": resolution.gate_id, "gate_type": gate, "decision_source": resolution.decision_source, "rationale": resolution.rationale})
        if gate == GateType.CHARACTER_DIRECTION_GATE.value:
            session.selected_character_direction = deepcopy(resolution.selected_values["direction"])
            session.locked_fields["character_direction"] = session.selected_character_direction
            session.current_stage = PipelineStage.CHARACTER_PLANNING.value
        elif gate == GateType.ART_DIRECTION_GATE.value:
            session.selected_art_direction = deepcopy(resolution.selected_values["direction"])
            session.locked_fields["art_direction"] = session.selected_art_direction
            session.current_stage = PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value
        elif gate == GateType.VISUAL_PREFERENCE_GATE.value:
            session.resolved_visual_preferences = deepcopy(resolution.selected_values.get("variables", {}))
            session.locked_fields.update(session.resolved_visual_preferences)
            session.delegated_fields = [name for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items() if item.get("selection_source") in {"delegated_ai", "quick_ai_fill"}]
            session.current_stage = PipelineStage.FINAL_DESIGN.value
        session.current_gate = None
        session.gate_payload = {}
        session.unresolved_fields = []
        session.artifact_status["current_gate"] = "resolved"
        self._save(session)
        return True

    def _open_gate(self, session: CreativeInteractionSession, gate: GateType, options: list[dict[str, Any]]) -> None:
        session.gate_sequence += 1
        session.current_gate = f"{session.session_id}:{gate.value.lower()}:{session.gate_sequence}"
        recommended = options[0].get("id") if options and gate != GateType.VISUAL_PREFERENCE_GATE else None
        recommendation_rationale: Any = {}
        if gate == GateType.VISUAL_PREFERENCE_GATE:
            recommended = {name: item.get("recommended") for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items() if item.get("user_visible")}
            recommendation_rationale = {
                name: {
                    "zh": item.get("recommendation_reason", "当前上下文下的推荐方案。"),
                    "en": item.get("recommendation_reason_en", "Context-aware recommendation."),
                }
                for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items()
                if item.get("user_visible")
            }
        elif options:
            selected = options[0]
            recommendation_rationale = {
                "zh": selected.get("rationale_zh", "当前输入下身份、轮廓和约束兼容性最好的方案。"),
                "en": selected.get("rationale_en", "Best balance of identity, silhouette, and constraint compatibility for this input."),
            }
        session.gate_payload = {
            "gate_id": session.current_gate,
            "gate_type": gate.value,
            "options": deepcopy(options),
            "recommended": recommended,
            "recommendation_rationale": deepcopy(recommendation_rationale),
            "original_user_input": session.original_user_input,
            "explicit_constraints": deepcopy(session.explicit_user_constraints),
            "candidate_generator_version": CANDIDATE_GENERATOR_VERSION if gate != GateType.VISUAL_PREFERENCE_GATE else None,
            "candidate_revision": session.candidate_revisions.get("character_explore" if gate == GateType.CHARACTER_DIRECTION_GATE else "art_explore", 0),
        }
        session.unresolved_fields = _gate_unresolved(session)
        session.status = _waiting_status(session.current_gate) if session.creation_mode == CreationMode.USER_DECIDE.value else SessionStatus.RUNNING.value

    def _maybe_switch_mode(self, session: CreativeInteractionSession, event: InteractionEvent) -> bool:
        requested = event.payload.get("to_mode") or event.payload.get("switch_mode") or event.payload.get("mode_switch_target")
        if not requested and "后面你决定" in str(event.payload.get("text", "")):
            requested = CreationMode.AI_DECIDE.value
        if not requested:
            return False
        new_mode = detect_creation_mode("", requested)
        if new_mode == session.creation_mode:
            return False
        switch = ModeSwitchEvent(session.creation_mode, new_mode, session.current_stage, str(event.payload.get("reason", "explicit user request")))
        session.interaction_history.append({"type": "mode_switch", **switch.to_dict()})
        session.audit_log.append({"event": "mode_switch", **switch.to_dict()})
        session.creation_mode = new_mode
        return True

    def _reopen_visual_gate_for_user(self, session: CreativeInteractionSession) -> None:
        sheet = session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))
        for item in sheet.get("variables", {}).values():
            if item.get("selection_source") not in {"explicit_user"}:
                item.update(user_selection=None, selection_source=None, locked=False)
        session.visual_preference_sheet = sheet
        session.final_design = None
        session.design_gate_result = None
        session.compiled_prompt = None
        self._clear_novelty(session)
        session.artifact_status.update({"final_design": "stale", "compiled_prompt": "stale"})
        session.current_stage = PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value
        session.current_gate = None
        self._open_gate(session, GateType.VISUAL_PREFERENCE_GATE, _visual_gate_options(sheet))

    def _rollback(self, session: CreativeInteractionSession, event: InteractionEvent) -> InteractiveResponse:
        target = str(event.payload.get("target", "")).upper()
        target = {
            "CHARACTER_DIRECTION_GATE": "CHARACTER",
            "ART_DIRECTION_GATE": "ART",
            "VISUAL_PREFERENCE_GATE": "VISUAL",
        }.get(target, target)
        if not target and session.current_stage in {PipelineStage.ART_DIRECTION_RESOLUTION.value, PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value}:
            target = "CHARACTER" if session.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value else "ART"
        if target in {"CHARACTER", "CHARACTER_DIRECTION", ""}:
            invalidated = ["character_plan", "art_explore_result", "selected_art_direction", "visual_preference_sheet", "resolved_visual_preferences", "final_design", "design_gate_result", "compiled_prompt"]
            session.character_plan = None
            session.art_explore_result = []
            session.selected_art_direction = None
            session.visual_preference_sheet = None
            session.resolved_visual_preferences = {}
            session.final_design = None
            session.design_gate_result = None
            session.compiled_prompt = None
            session.current_stage = PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value
            self._open_gate(session, GateType.CHARACTER_DIRECTION_GATE, session.character_explore_result)
        else:
            invalidated = ["visual_preference_sheet", "resolved_visual_preferences", "final_design", "design_gate_result", "compiled_prompt"]
            session.visual_preference_sheet = None
            session.resolved_visual_preferences = {}
            session.final_design = None
            session.design_gate_result = None
            session.compiled_prompt = None
            session.current_stage = PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value if target in {"VISUAL", "VISUAL_PREFERENCE"} else PipelineStage.ART_DIRECTION_RESOLUTION.value
            self._open_gate(session, GateType.ART_DIRECTION_GATE if session.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value else GateType.VISUAL_PREFERENCE_GATE, session.art_explore_result if session.current_stage == PipelineStage.ART_DIRECTION_RESOLUTION.value else _visual_gate_options(_visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session))))
        self._clear_novelty(session)
        session.audit_log.append({"event": "rollback_event", "target": target, "invalidated_artifacts": invalidated, "preserved": ["original_user_input", "interaction_history", "previous_choices"]})
        session.artifact_status.update({name: "stale" for name in invalidated})
        return self._response(session, message="已回到上一个可恢复 Gate；旧设计保留在历史中。")

    def _error_response(self, session: CreativeInteractionSession, code: str, message: str) -> InteractiveResponse:
        return self._response(session, status=code, message=message, error_code=code)

    def _response(self, session: CreativeInteractionSession, *, status: str | None = None, message: str | None = None, error_code: str | None = None) -> InteractiveResponse:
        gate = deepcopy(session.gate_payload) if session.current_gate else None
        options = gate.get("options", []) if gate else []
        if session.current_gate and session.gate_payload.get("gate_type") == GateType.VISUAL_PREFERENCE_GATE.value:
            options = _visual_gate_options(session.visual_preference_sheet or _visual_sheet(session.explicit_user_constraints, original_input=session.original_user_input, prior_resolutions=[{"direction": session.selected_character_direction}, {"direction": session.selected_art_direction}], visual_context_firewall=_session_firewall(session)))
        current_status = status or session.status
        return InteractiveResponse(session.session_id, session.creation_mode, current_status, session.current_stage, message or _message(session), gate, options, gate.get("recommended") if gate else None, list(session.unresolved_fields), _allowed_actions(session), _progress(session), {"session": str(self._session_dir(session.session_id) / "session.json"), "events": str(self._session_dir(session.session_id) / "events.jsonl"), "artifacts": str(self._session_dir(session.session_id) / "artifacts")}, error_code)


def _waiting_status(gate_id: str | None) -> str:
    if not gate_id:
        return SessionStatus.RUNNING.value
    name = gate_id.split(":")[-2] if ":" in gate_id else ""
    return {"character_direction_gate": SessionStatus.AWAITING_CHARACTER_DIRECTION.value, "art_direction_gate": SessionStatus.AWAITING_ART_DIRECTION.value, "visual_preference_gate": SessionStatus.AWAITING_VISUAL_PREFERENCES.value}.get(name, SessionStatus.RUNNING.value)


def _gate_unresolved(session: CreativeInteractionSession) -> list[str]:
    gate = session.gate_payload.get("gate_type")
    if gate in {GateType.CHARACTER_DIRECTION_GATE.value, GateType.ART_DIRECTION_GATE.value}:
        return ["direction"]
    if gate == GateType.VISUAL_PREFERENCE_GATE.value:
        return [name for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items() if item.get("user_visible") and item.get("user_selection") is None]
    return []


def _visual_gate_options(sheet: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "variable": name,
            "options": deepcopy(item.get("options", [])),
            "recommended": item.get("recommended"),
            "recommendation_reason": item.get("recommendation_reason"),
            "recommendation_reason_en": item.get("recommendation_reason_en"),
            "locked": bool(item.get("locked")),
            "resolved": item.get("user_selection") is not None,
        }
        for name, item in sheet.get("variables", {}).items()
        if item.get("user_visible") and item.get("selection_source") != "explicit_user"
    ]


def _allowed_actions(session: CreativeInteractionSession) -> list[str]:
    if not session.current_gate:
        return []
    actions = [item.value for item in InteractionAction]
    return actions


def _progress(session: CreativeInteractionSession) -> dict[str, Any]:
    stages = ["Concept", "Art Direction", "Visual Preferences", "Final Design"]
    index = {PipelineStage.CHARACTER_EXPLORE.value: 0, PipelineStage.CHARACTER_DIRECTION_RESOLUTION.value: 0, PipelineStage.CHARACTER_PLANNING.value: 1, PipelineStage.ART_EXPLORE.value: 1, PipelineStage.ART_DIRECTION_RESOLUTION.value: 1, PipelineStage.VISUAL_PREFERENCE_RESOLUTION.value: 2, PipelineStage.FINAL_DESIGN.value: 3, PipelineStage.PLAYABLE_CHARACTER_DESIGN_GATE.value: 3, PipelineStage.PROMPT_COMPILATION.value: 3, PipelineStage.GENERATION_READY.value: 4}.get(session.current_stage, 0)
    return {"completed": stages[:index], "current": stages[index] if index < len(stages) else "Generation Ready", "stages": stages}


def _message(session: CreativeInteractionSession) -> str:
    if session.status == SessionStatus.CANCELLED.value:
        return "这个角色设计 Session 已取消。"
    if session.status == SessionStatus.GENERATION_READY.value:
        return "设计已完成并通过 Playable Character Design Gate，已到 GENERATION_READY；本轮未调用 imagegen。"
    if session.status == SessionStatus.AWAITING_CHARACTER_DIRECTION.value:
        return "这里有几个角色方向。请选择一个，也可以 MIX、CUSTOM 或 DELEGATE。"
    if session.status == SessionStatus.AWAITING_ART_DIRECTION.value:
        return "角色方向已锁定。下面是视觉方向，请选择、混合或委托 AI。"
    if session.status == SessionStatus.AWAITING_VISUAL_PREFERENCES.value:
        return "视觉偏好表已准备。你可以只修改少数身份字段，其余使用推荐。"
    return "设计流程正在继续。"


def _build_final_design(session: CreativeInteractionSession) -> dict[str, Any]:
    visual = session.resolved_visual_preferences
    firewall = _session_firewall(session)
    face_selection = resolve_face_aesthetic_profile(
        visual.get("face_aesthetic_profile"),
        source=visual.get("face_aesthetic_source"),
        explicit_user_selection="face_aesthetic_profile" in session.explicit_user_constraints.get("explicit_user_fields", ()),
        style_inheritance_policy=firewall.style_inheritance_policy,
    )
    lower_body = {name: visual.get(name) for name in ("exposure_strategy", "legwear_family", "leg_accessory_family", "footwear_family", "foot_visibility", "visual_reason", "relationship_to_character_style", "relationship_to_pose", "repetition_risk")}
    direction = session.selected_art_direction or {}
    identity = session.selected_character_direction or {}
    design_dna = deepcopy(identity.get("design_dna") or direction.get("design_dna") or {})
    design = {
        "character_identity": f"{identity.get('summary', session.original_user_input)}; anchor: {identity.get('primary_anchor', 'specific head and silhouette identity')}",
        "character_visual_style": direction.get("structure", "clean-line contemporary commercial gacha anime"),
        "pose_description": f"{design_dna.get('pose_family', 'OPEN_PARALLEL_STANCE')} frontal standee stance with both legs clearly separated",
        "pose_intent": visual.get("pose_intent", "STABLE_OPEN"),
        "pose_family": design_dna.get("pose_family", visual.get("pose_family", "OPEN_PARALLEL_STANCE")),
        "regional_visual_language": DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        "regional_visual_language_source": "default_style_policy",
        **face_selection.to_dict(),
        "face_aesthetic_contract": face_selection.to_dict(),
        "lower_body": lower_body,
        "visual_preferences": visual,
        "design_dna": design_dna,
        "provenance": {name: (session.visual_preference_sheet or {}).get("variables", {}).get(name, {}).get("selection_source", "policy_default") for name in visual},
        **firewall.to_dict(),
    }
    for key, value in session.explicit_user_constraints.items():
        if key not in {"raw", "force_design_failure", "gender", "age_group", "explicit_user_fields", "explicit_constraint_records", "raw_hard_constraints", "constraint_conflicts", "positive_constraints", "negative_constraints", "prohibited", "prohibited_constraints", "constraint_provenance"}:
            design.setdefault("visual_preferences", {})[key] = value
            design["provenance"][key] = "explicit_user"
            if key in lower_body:
                design["lower_body"][key] = value
    design["age_group"] = session.explicit_user_constraints.get("age_group", "adult")
    design["explicit_user_constraints"] = deepcopy(session.explicit_user_constraints)
    explicit_records = deepcopy(session.explicit_user_constraints.get("explicit_constraint_records") or {})
    for index, record in enumerate(session.explicit_user_constraints.get("raw_hard_constraints") or ()):
        explicit_records[f"raw_hard_constraint_{index}"] = deepcopy(record)
    design["explicit_constraint_records"] = explicit_records
    design["constraint_priority"] = "explicit_user > human_selection > human_accept_recommended > delegated_ai > policy_default"
    visual_contract = build_visual_specification_contract(
        design_dna=design_dna,
        visual_preferences=design["visual_preferences"],
        character_visual_style=str(design["character_visual_style"]),
        explicit_user_fields=session.explicit_user_constraints.get("explicit_user_fields", ()),
        explicit_constraints=explicit_records,
        soft_intent={"fanservice_level": design["visual_preferences"].get("fanservice_level")},
        face_aesthetic_profile=face_selection.face_aesthetic_profile,
        face_aesthetic_source=face_selection.face_aesthetic_source,
        style_inheritance_policy=face_selection.style_inheritance_policy,
    )
    design["visual_specification_contract"] = visual_contract.to_dict()
    design["prompt_adherence_manifest"] = visual_contract.to_dict()
    design["pose_specification"] = deepcopy(visual_contract.pose_specification)
    design["background_specification"] = deepcopy(visual_contract.background_specification)
    design["generation_context"] = firewall.generation_context(
        current_user_request=session.original_user_input,
        current_run_choices=(
            {"character_direction": deepcopy(identity)},
            {"art_direction": deepcopy(direction)},
        ),
        confirmed_gate_outputs=(
            {"character_direction": deepcopy(identity)},
            {"art_direction": deepcopy(direction)},
            {"visual_preferences": deepcopy(design["visual_preferences"])},
        ),
    )
    design["generation_context"].update(
        {
            "visual_specification_contract": visual_contract.to_dict(),
            "prompt_adherence_manifest": visual_contract.to_dict(),
            "face_aesthetic_contract": face_selection.to_dict(),
        }
    )
    session.face_aesthetic_contract = face_selection.to_dict()
    return design


def _design_gate(final_design: Mapping[str, Any]) -> dict[str, Any]:
    required = ("character_identity", "character_visual_style", "pose_description", "lower_body")
    missing = [name for name in required if not final_design.get(name)]
    return {"result": "FAIL" if missing else "PASS", "missing": missing, "hard_rules": ["Style Contract", "Regional Visual Language", "Pose System Frozen", "Lower-Body rules", "Playable Character Design Gate"], "rationale": "All required design handoff fields are present." if not missing else "Required handoff fields are missing."}


def _compiler_args(final_design: Mapping[str, Any]) -> dict[str, Any]:
    identity = str(final_design.get("character_identity", "specific playable character identity"))
    visual = final_design.get("visual_preferences") or {}
    explicit = final_design.get("explicit_user_constraints") or {}
    structured = list(explicit.get("prohibited_constraints") or [])
    prompt_structured = [item for item in structured if str(item.get("text")) != "crossed legs"]
    negative = {
        name: value
        for name, value in (explicit.get("negative_constraints") or {}).items()
        if name != "forbid_crossed_legs" and not (structured and name.startswith("forbid_hair_"))
    }
    contract = final_design.get("visual_specification_contract")
    explicit_records = final_design.get("explicit_constraint_records") or explicit.get("explicit_constraint_records") or {}
    if not contract:
        contract = build_visual_specification_contract(
            design_dna=final_design.get("design_dna"),
            visual_preferences=visual,
            character_visual_style=str(final_design.get("character_visual_style", "")),
            explicit_user_fields=explicit.get("explicit_user_fields", ()),
            explicit_constraints=explicit_records,
        ).to_dict()
    return {
        "character_visual_style": str(final_design.get("character_visual_style", "clean-line contemporary gacha anime")),
        "character_identity": identity,
        "prohibited_constraints": prompt_structured,
        "explicit_negative_constraints": negative,
        "regional_visual_language": final_design.get("regional_visual_language", DEFAULT_REGIONAL_VISUAL_LANGUAGE),
        "regional_visual_language_source": final_design.get("regional_visual_language_source", "default_style_policy"),
        "lower_body": final_design.get("lower_body"),
        "age_group": final_design.get("age_group", "adult"),
        "fanservice_level": visual.get("fanservice_level"),
        "pose_description": final_design.get("pose_description"),
        "pose_family": final_design.get("pose_family"),
        "pose_intent": final_design.get("pose_intent"),
        "face_aesthetic_profile": final_design.get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE),
        "face_aesthetic_source": final_design.get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE),
        "style_inheritance_policy": final_design.get("style_inheritance_policy", DEFAULT_STYLE_INHERITANCE_POLICY),
        "visual_specification_contract": contract,
        "explicit_constraints": explicit_records,
        "visual_context_firewall": {name: deepcopy(final_design.get(name)) for name in ("inherit_previous_visuals", "allowed_visual_inheritance", "blocked_context_sources", "visual_context_firewall_applied", "style_inheritance_policy")},
    }


def resume_session(session_root: str | Path, session_id: str, interaction_event: InteractionEvent | Mapping[str, Any] | str) -> InteractiveResponse:
    return InteractionRuntime(session_root).resume_session(session_id, interaction_event)


def replay_session(session_root: str | Path, session_id: str) -> dict[str, Any]:
    return InteractionRuntime(session_root).replay_session(session_id)


def record_generation_artifact(
    session_root: str | Path,
    session_id: str,
    image: str | Path,
    *,
    run_id: str | None = None,
    generation_id: str | None = None,
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return InteractionRuntime(session_root).record_generation_artifact(
        session_id,
        image,
        run_id=run_id,
        generation_id=generation_id,
        prompt_hash=prompt_hash,
    )


def record_visual_adherence_review(
    session_root: str | Path,
    session_id: str,
    actual_image: str | Path,
    *,
    observations: Mapping[str, Any],
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return InteractionRuntime(session_root).record_visual_adherence_review(
        session_id,
        actual_image,
        observations=observations,
        prompt_hash=prompt_hash,
    )


def build_visual_repair_plan(
    session_root: str | Path,
    session_id: str,
    *,
    max_attempts: int = MAX_REPAIR_ATTEMPTS,
    include_minor: bool = True,
) -> dict[str, Any]:
    return InteractionRuntime(session_root).build_visual_repair_plan(session_id, max_attempts=max_attempts, include_minor=include_minor)


def record_visual_repair_generation(
    session_root: str | Path,
    session_id: str,
    attempt_id: str,
    repair_image: str | Path,
    *,
    repair_prompt: str | None = None,
    prompt_hash: str | None = None,
) -> dict[str, Any]:
    return InteractionRuntime(session_root).record_visual_repair_generation(
        session_id,
        attempt_id,
        repair_image,
        repair_prompt=repair_prompt,
        prompt_hash=prompt_hash,
    )


def record_visual_repair_review(
    session_root: str | Path,
    session_id: str,
    attempt_id: str,
    *,
    observations: Mapping[str, Any],
) -> dict[str, Any]:
    return InteractionRuntime(session_root).record_visual_repair_review(session_id, attempt_id, observations=observations)


__all__ = [
    "AIDecideGateResolver",
    "CreationMode",
    "DEFAULT_BLOCKED_CONTEXT_SOURCES",
    "CreativeInteractionSession",
    "GenerationArtifact",
    "GateResolution",
    "GateResolver",
    "GateType",
    "InteractionAction",
    "InteractionEvent",
    "InteractionRuntime",
    "InteractiveResponse",
    "ModeSwitchEvent",
    "PipelineStage",
    "QuickGateResolver",
    "ResolutionStatus",
    "SessionStatus",
    "UserDecideGateResolver",
    "VisualAdherenceCritic",
    "VisualAdherenceReview",
    "VisualContextFirewall",
    "VisualRepairError",
    "VisualRepairPlan",
    "build_visual_repair_plan",
    "detect_creation_mode",
    "migrate_legacy_artifact",
    "record_visual_adherence_review",
    "record_generation_artifact",
    "record_visual_repair_generation",
    "record_visual_repair_review",
    "replay_session",
    "resume_session",
]
