"""Reviewed game-rendering profiles and their narrow runtime projection.

The research repository produces evidence; this module consumes only the
reviewed, packaged profiles under ``references/game_styles``.  The projector
is intentionally rendering-only: a profile may describe line, value, edge,
material, or detail organization, but it must never become a character
template or a source of identity decisions.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
from pathlib import Path
from typing import Any, Mapping
import unicodedata


PROFILE_VERSION = "game_style_profile_v2"
PROJECTION_VERSION = "game_style_projection_v2"
GAME_STYLE_FIELD = "game_rendering_style"
STYLE_DIFFERENCE_VALIDITY_GATE = "STYLE_DIFFERENCE_VALIDITY_GATE"
_REFERENCE_DIR = Path(__file__).resolve().parents[1] / "references" / "game_styles"
_DEFAULT_TOKENS = {"", "none", "default", "global", "默认", "不指定", "自定义"}
RENDERING_SIGNATURE_SLOTS = (
    "LINE_CONTOUR",
    "INTERNAL_EDGE",
    "PRIMARY_SHADOW",
    "SECONDARY_GRADIENT",
    "SKIN_RENDERING",
    "HAIR_RENDERING",
    "EYE_RENDERING",
    "MATERIAL_SPECULAR",
    "COLOR_VALUE_ORGANIZATION",
    "DETAIL_FREQUENCY",
    "DEPTH_SEPARATION",
    "POST_PROCESSING",
    "HIGHLIGHT_STRATEGY",
    "LOCAL_CONTRAST",
    "SHAPE_DETAIL_HIERARCHY",
)
_REQUIRED_SIGNATURE_SLOTS = frozenset(RENDERING_SIGNATURE_SLOTS[:12])
_VALID_STRENGTHS = frozenset({"strong", "medium", "subtle"})
_VALID_CONFIDENCE = frozenset({"high", "medium", "low", "no reliable discriminator"})
_VALID_SIGNATURE_STATUS = frozenset({"supported", "no_reliable_discriminator"})
_FORBIDDEN_CONTENT_TERMS = (
    "hair", "发色", "发型", "eye", "瞳", "body", "breast", "身材", "outfit", "clothing",
    "服装", "footwear", "鞋", "stocking", "丝袜", "pose", "姿势", "background", "背景",
    "palette", "配色", "accessory", "配件", "sexiness", "性感", "nonhuman", "非人",
    "character identity", "角色身份", "silhouette", "轮廓复制",
)


class GameStyleError(ValueError):
    """Raised when a packaged game-style contract is malformed."""


@dataclass(frozen=True)
class GameStyleContrastProfile:
    """One evidence-backed rendering slot and its relative HOW instruction.

    ``contrastive_instruction`` is deliberately stored beside the absolute
    instruction.  The compiler can therefore explain the delta relative to
    Global without putting a game name or character-design choice in the
    image prompt.
    """

    game_style_id: str
    slot: str
    absolute_instruction: str
    contrastive_instruction: str
    confidence: str
    strength: str
    source_claim_ids: tuple[str, ...] = ()
    status: str = "supported"
    tier: str = "core"

    @classmethod
    def from_mapping(cls, game_style_id: str, data: Mapping[str, Any]) -> "GameStyleContrastProfile":
        slot = str(data.get("slot") or "").upper()
        status = str(data.get("status") or "supported")
        strength = str(data.get("strength") or data.get("rule_strength") or "subtle").lower()
        confidence = str(data.get("confidence") or "medium").lower()
        raw_claims = data.get("source_claim_ids")
        if raw_claims is None and data.get("claim_id"):
            raw_claims = (data.get("claim_id"),)
        claims = tuple(str(item) for item in (raw_claims or ()) if str(item))
        if slot not in RENDERING_SIGNATURE_SLOTS:
            raise GameStyleError(f"unsupported rendering signature slot: {slot}")
        if status not in _VALID_SIGNATURE_STATUS:
            raise GameStyleError(f"unsupported rendering signature status: {status}")
        if strength not in _VALID_STRENGTHS:
            raise GameStyleError(f"unsupported game style rule strength: {strength}")
        if confidence not in _VALID_CONFIDENCE:
            raise GameStyleError(f"unsupported game style rule confidence: {confidence}")
        if status == "supported" and (not data.get("absolute_instruction") or not data.get("contrastive_instruction")):
            raise GameStyleError(f"{game_style_id}:{slot} requires absolute and contrastive instructions")
        if status == "supported" and not claims:
            raise GameStyleError(f"{game_style_id}:{slot} requires source claim ids")
        tier = str(data.get("tier") or "core").lower()
        if tier not in {"core", "supporting", "none"}:
            raise GameStyleError(f"unsupported rendering signature tier: {tier}")
        return cls(
            game_style_id=game_style_id,
            slot=slot,
            absolute_instruction=str(data.get("absolute_instruction") or "no reliable discriminator"),
            contrastive_instruction=str(data.get("contrastive_instruction") or "no reliable discriminator"),
            confidence=confidence,
            strength=strength,
            source_claim_ids=claims,
            status=status,
            tier=tier if status == "supported" else "none",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_style_id": self.game_style_id,
            "slot": self.slot,
            "absolute_instruction": self.absolute_instruction,
            "contrastive_instruction": self.contrastive_instruction,
            "confidence": self.confidence,
            "strength": self.strength,
            "source_claim_ids": list(self.source_claim_ids),
            "status": self.status,
            "tier": self.tier,
        }

    def to_instruction(self) -> dict[str, Any]:
        """Return the compact projected rule consumed by PromptCompiler."""
        return {
            "claim_id": self.source_claim_ids[0] if self.source_claim_ids else "",
            "source_claim_ids": list(self.source_claim_ids),
            "slot": self.slot,
            "absolute_instruction": self.absolute_instruction,
            "contrastive_instruction": self.contrastive_instruction,
            "text": self.absolute_instruction,
            "confidence": self.confidence,
            "strength": self.strength,
            "rule_strength": self.strength,
            "status": self.status,
            "tier": self.tier,
        }


@dataclass(frozen=True)
class GameStyleProfile:
    """Immutable reviewed profile exposed to production callers."""

    game_style_id: str
    display_name: str
    profile_version: str
    source_analysis_version: str
    sample_manifest_version: str
    integration_review_version: str
    rendering_signature: tuple[GameStyleContrastProfile, ...] = ()
    core_rendering_instructions: tuple[dict[str, Any], ...] = ()
    supporting_art_direction_instructions: tuple[dict[str, Any], ...] = ()
    excluded_global_baseline_claim_ids: tuple[str, ...] = ()
    prompt_budget: dict[str, int] = field(default_factory=dict)

    @property
    def contrast_profiles(self) -> tuple[GameStyleContrastProfile, ...]:
        """Compatibility name for callers that consume contrast profiles directly."""
        return self.rendering_signature

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GameStyleProfile":
        game = data.get("game") if isinstance(data.get("game"), Mapping) else {}
        projection = data.get("projection") if isinstance(data.get("projection"), Mapping) else data
        game_style_id = str(game.get("id") or data.get("game_style_id") or "")
        signature = tuple(
            GameStyleContrastProfile.from_mapping(game_style_id, item)
            for item in (projection.get("rendering_signature") or ())
            if isinstance(item, Mapping)
        )
        if not signature:
            # Compatibility reader for pre-v2 artifacts.  Packaged v2 profiles
            # always use rendering_signature, but old checkpoints may still
            # carry the former text-only projection shape.
            signature = tuple(
                GameStyleContrastProfile.from_mapping(
                    game_style_id,
                    {
                        "slot": "DETAIL_FREQUENCY",
                        "absolute_instruction": item.get("text"),
                        "contrastive_instruction": item.get("text"),
                        "confidence": "medium",
                        "strength": "subtle",
                        "source_claim_ids": (item.get("claim_id"),),
                    },
                )
                for item in projection.get("core_rendering_instructions", ())
                if isinstance(item, Mapping)
            )
        core = tuple(item.to_instruction() for item in signature if item.tier == "core")
        supporting = tuple(item.to_instruction() for item in signature if item.tier == "supporting")
        profile = cls(
            game_style_id=game_style_id,
            display_name=str(game.get("display_name") or data.get("display_name") or ""),
            profile_version=str(data.get("profile_version") or PROFILE_VERSION),
            source_analysis_version=str(data.get("source_analysis_version") or ""),
            sample_manifest_version=str(data.get("sample_manifest_version") or ""),
            integration_review_version=str(data.get("integration_review_version") or ""),
            rendering_signature=signature,
            core_rendering_instructions=core or tuple(_instruction(item) for item in projection.get("core_rendering_instructions", ())),
            supporting_art_direction_instructions=supporting or tuple(_instruction(item) for item in projection.get("supporting_art_direction_instructions", ())),
            excluded_global_baseline_claim_ids=tuple(str(item) for item in projection.get("excluded_global_baseline_claim_ids", ())),
            prompt_budget={str(key): int(value) for key, value in dict(projection.get("prompt_budget") or {}).items()},
        )
        _validate_profile(profile)
        return profile

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_style_id": self.game_style_id,
            "display_name": self.display_name,
            "profile_version": self.profile_version,
            "source_analysis_version": self.source_analysis_version,
            "sample_manifest_version": self.sample_manifest_version,
            "integration_review_version": self.integration_review_version,
            "rendering_signature": [item.to_dict() for item in self.rendering_signature],
            "core_rendering_instructions": deepcopy(list(self.core_rendering_instructions)),
            "supporting_art_direction_instructions": deepcopy(list(self.supporting_art_direction_instructions)),
            "excluded_global_baseline_claim_ids": list(self.excluded_global_baseline_claim_ids),
            "prompt_budget": dict(self.prompt_budget),
        }


@dataclass(frozen=True)
class CharacterDesignContext:
    """Context needed to enforce that projection cannot alter character data."""

    explicit_preferences: Mapping[str, Any] = field(default_factory=dict)
    explicit_rendering_preferences: Mapping[str, Any] = field(default_factory=dict)
    global_rendering_contract: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"


@dataclass(frozen=True)
class StyleInstructionFragment:
    """Auditable HOW-style delta inserted after the global rendering contract."""

    game_style_id: str
    profile_version: str
    projection_version: str
    instructions: tuple[str, ...]
    source_claim_ids: tuple[str, ...]
    core_instructions: tuple[str, ...] = ()
    supporting_instructions: tuple[str, ...] = ()
    contrastive_instructions: tuple[str, ...] = ()
    rendering_signature: tuple[dict[str, Any], ...] = ()
    rules: tuple[dict[str, Any], ...] = ()
    global_rendering_contract: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"
    overridden_claim_ids: tuple[str, ...] = ()
    applied_rules: tuple[dict[str, Any], ...] = ()
    adapted_rules: tuple[dict[str, Any], ...] = ()
    dropped_rules: tuple[dict[str, Any], ...] = ()

    @property
    def prompt_text(self) -> str:
        return " ".join(self.instructions)

    @property
    def contrast_profiles(self) -> tuple[dict[str, Any], ...]:
        """Expose projected structured slots without a second storage path."""
        return self.rendering_signature

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_style_id": self.game_style_id,
            "profile_version": self.profile_version,
            "projection_version": self.projection_version,
            "instructions": list(self.instructions),
            "source_claim_ids": list(self.source_claim_ids),
            "core_instructions": list(self.core_instructions),
            "supporting_instructions": list(self.supporting_instructions),
            "contrastive_instructions": list(self.contrastive_instructions),
            "rendering_signature": [dict(item) for item in self.rendering_signature],
            "rules": [dict(item) for item in self.rules],
            "global_rendering_contract": self.global_rendering_contract,
            "overridden_claim_ids": list(self.overridden_claim_ids),
            "applied_rules": [dict(item) for item in self.applied_rules],
            "adapted_rules": [dict(item) for item in self.adapted_rules],
            "dropped_rules": [dict(item) for item in self.dropped_rules],
        }


def _instruction(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping) or not item.get("text") or not item.get("claim_id"):
        raise GameStyleError("each projection instruction requires claim_id and text")
    strength = str(item.get("strength") or item.get("rule_strength") or "subtle").lower()
    if strength in {"hard", "soft"}:
        strength = {"hard": "strong", "soft": "subtle"}[strength]
    if strength not in _VALID_STRENGTHS:
        raise GameStyleError(f"unsupported game style rule strength: {strength}")
    return {
        "claim_id": str(item["claim_id"]),
        "source_claim_ids": [str(item["claim_id"])],
        "slot": str(item.get("slot") or "DETAIL_FREQUENCY").upper(),
        "absolute_instruction": str(item.get("absolute_instruction") or item["text"]),
        "contrastive_instruction": str(item.get("contrastive_instruction") or item["text"]),
        "confidence": str(item.get("confidence") or "medium"),
        "strength": strength,
        "rule_strength": strength,
        "text": str(item["text"]),
    }


def _validate_profile(profile: GameStyleProfile) -> None:
    if not profile.game_style_id or not profile.display_name:
        raise GameStyleError("game style profile requires an id and display name")
    if profile.profile_version != PROFILE_VERSION:
        raise GameStyleError(f"unsupported profile version: {profile.profile_version}")
    if not all((profile.source_analysis_version, profile.sample_manifest_version, profile.integration_review_version)):
        raise GameStyleError(f"{profile.game_style_id} is missing provenance metadata")
    slots = [item.slot for item in profile.rendering_signature]
    if not _REQUIRED_SIGNATURE_SLOTS.issubset(slots):
        missing = sorted(_REQUIRED_SIGNATURE_SLOTS.difference(slots))
        raise GameStyleError(f"{profile.game_style_id} is missing rendering signature slots: {missing}")
    if len(slots) != len(set(slots)):
        raise GameStyleError(f"{profile.game_style_id} contains duplicate rendering signature slots")
    core_max = int(profile.prompt_budget.get("core_max", 6))
    supporting_max = int(profile.prompt_budget.get("supporting_max", 2))
    total_max = int(profile.prompt_budget.get("total_max", 10))
    if not 5 <= len(profile.core_rendering_instructions) <= core_max:
        raise GameStyleError(f"{profile.game_style_id} must project 5-{core_max} core instructions")
    if len(profile.supporting_art_direction_instructions) > supporting_max or len(profile.core_rendering_instructions) + len(profile.supporting_art_direction_instructions) > total_max:
        raise GameStyleError(f"{profile.game_style_id} exceeds its projection budget")
    for instruction in (*profile.core_rendering_instructions, *profile.supporting_art_direction_instructions):
        if instruction.get("slot") not in RENDERING_SIGNATURE_SLOTS:
            raise GameStyleError(f"{profile.game_style_id} contains an invalid rendering slot")
        if any(term in instruction["absolute_instruction"].casefold() for term in _FORBIDDEN_CONTENT_TERMS):
            raise GameStyleError(f"{profile.game_style_id} contains a character-content instruction")
        if set(instruction.get("source_claim_ids", ())).intersection(profile.excluded_global_baseline_claim_ids):
            raise GameStyleError(f"{profile.game_style_id} duplicates a global baseline claim")


def _normalized_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value)).strip().casefold()
    return re.sub(r"[\s_\-:：]+", "", normalized)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - host dependency guard
        raise GameStyleError("loading game style profiles requires the host YAML parser") from error
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise GameStyleError(f"profile is not a mapping: {path.name}")
    return data


class GameStyleRegistry:
    """Load the packaged registry once and resolve aliases without YAML leakage."""

    def __init__(self, root: Path = _REFERENCE_DIR) -> None:
        self.root = Path(root)
        registry_data = _load_yaml(self.root / "registry.yaml")
        entries = registry_data.get("profiles")
        if not isinstance(entries, list) or not entries:
            raise GameStyleError("game style registry has no profiles")
        self._profiles: dict[str, GameStyleProfile] = {}
        self._aliases: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, Mapping):
                raise GameStyleError("registry entries must be mappings")
            canonical = str(entry.get("id") or "")
            if canonical in self._profiles:
                raise GameStyleError(f"duplicate canonical game style id: {canonical}")
            profile_path = self.root / str(entry.get("profile") or "")
            profile = GameStyleProfile.from_mapping(_load_yaml(profile_path))
            if profile.game_style_id != canonical:
                raise GameStyleError(f"registry/profile id mismatch: {canonical}")
            self._profiles[canonical] = profile
            for alias in (canonical, *(str(item) for item in entry.get("aliases", ()) )):
                key = _normalized_alias(alias)
                if not key or (key in self._aliases and self._aliases[key] != canonical):
                    raise GameStyleError(f"duplicate game style alias: {alias}")
                self._aliases[key] = canonical

    @property
    def profiles(self) -> Mapping[str, GameStyleProfile]:
        return self._profiles

    @property
    def aliases(self) -> Mapping[str, str]:
        return self._aliases

    def resolve(self, game_style_id: str | None) -> GameStyleProfile | None:
        if game_style_id is None or _normalized_alias(str(game_style_id)) in {_normalized_alias(item) for item in _DEFAULT_TOKENS}:
            return None
        canonical = self._aliases.get(_normalized_alias(str(game_style_id)))
        return self._profiles.get(canonical) if canonical else None


_REGISTRY: GameStyleRegistry | None = None


def game_style_registry() -> GameStyleRegistry:
    """Return the packaged registry; callers never read profile YAML directly."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = GameStyleRegistry()
    return _REGISTRY


def resolve_game_style(game_style_id: str | None) -> GameStyleProfile | None:
    """Resolve canonical IDs and aliases; unsupported values fail closed to global style."""
    return game_style_registry().resolve(game_style_id)


def normalize_game_style_request(value: Any) -> tuple[str | None, str | None]:
    """Return ``(canonical_id, original_request)`` for checkpoint-safe fallback."""
    if value is None or _normalized_alias(str(value)) in {_normalized_alias(item) for item in _DEFAULT_TOKENS}:
        return None, None
    raw = str(value).strip()
    profile = resolve_game_style(raw)
    return (profile.game_style_id if profile else None), raw


def project_game_style(profile: GameStyleProfile, context: CharacterDesignContext | Mapping[str, Any]) -> StyleInstructionFragment:
    """Project evidence-backed rendering HOW rules after user conflicts.

    The projector owns the only profile-to-prompt conversion point.  Keeping
    conflict handling here prevents one caller from accidentally letting a
    soft game prior outrank an explicit rendering request.
    """
    if not isinstance(profile, GameStyleProfile):
        raise TypeError("project_game_style requires a resolved GameStyleProfile")
    if not isinstance(context, CharacterDesignContext):
        context = CharacterDesignContext(
            explicit_preferences=dict(context.get("explicit_preferences") or {}),
            explicit_rendering_preferences=dict(context.get("explicit_rendering_preferences") or {}),
            global_rendering_contract=str(context.get("global_rendering_contract") or "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"),
        )
    _validate_profile(profile)
    explicit_rendering = {str(key).casefold(): value for key, value in context.explicit_rendering_preferences.items()}

    slot_preferences = {
        "LINE_CONTOUR": ("edge_treatment", "line_contour"),
        "INTERNAL_EDGE": ("edge_treatment", "internal_edge"),
        "PRIMARY_SHADOW": ("shading_strategy", "primary_shadow", "lighting"),
        "SECONDARY_GRADIENT": ("shading_strategy", "secondary_gradient", "lighting"),
        "DETAIL_FREQUENCY": ("detail_density", "texture_detail", "detail_frequency"),
        "MATERIAL_SPECULAR": ("material_specular", "specular"),
        "LOCAL_CONTRAST": ("local_contrast",),
        "DEPTH_SEPARATION": ("depth_separation",),
        "COLOR_VALUE_ORGANIZATION": ("color_value_organization", "color_structure"),
        "POST_PROCESSING": ("post_processing",),
    }

    def explicit_override(item: Mapping[str, Any]) -> tuple[str, Any] | None:
        keys = slot_preferences.get(str(item.get("slot", "")).upper(), ())
        for key in keys:
            if key in explicit_rendering:
                return key, explicit_rendering[key]
        return None

    def override_mode(value: Any) -> str:
        if isinstance(value, Mapping):
            return str(value.get("mode") or value.get("resolution") or "drop").casefold()
        text = str(value).casefold()
        return "adapt" if any(token in text for token in ("adapt", "compatible", "mixed", "localized")) else "drop"

    projected: list[dict[str, Any]] = []
    applied: list[dict[str, Any]] = []
    adapted: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    all_items = (*profile.core_rendering_instructions, *profile.supporting_art_direction_instructions)
    for original in all_items:
        item = dict(original)
        claims = tuple(str(value) for value in item.get("source_claim_ids", (item.get("claim_id"),)) if value)
        key_value = explicit_override(item)
        trace = {
            "slot": item["slot"],
            "claim_ids": list(claims),
            "strength": item.get("strength", "subtle"),
            "confidence": item.get("confidence", "medium"),
            "conflict_reason": None,
        }
        if key_value is None:
            trace["status"] = "applied"
            projected.append(item)
            applied.append(trace)
            continue
        key, value = key_value
        trace["user_field"] = key
        trace["user_value"] = value
        if override_mode(value) == "adapt":
            adapted_item = dict(item)
            adapted_item["absolute_instruction"] = (
                f"Keep the explicit user rendering preference for {key} as the controlling local treatment; "
                f"{item['absolute_instruction']}"
            )
            adapted_item["text"] = adapted_item["absolute_instruction"]
            adapted_item["status"] = "adapted"
            projected.append(adapted_item)
            trace.update(status="adapted", conflict_reason=f"adapted around explicit {key}")
            adapted.append(trace)
        else:
            trace.update(status="dropped", conflict_reason=f"explicit user rendering preference overrides {key}")
            dropped.append(trace)
    core_items = tuple(item for item in projected if item.get("tier") == "core")
    supporting_items = tuple(item for item in projected if item.get("tier") == "supporting")
    core = tuple(item["absolute_instruction"] for item in core_items)
    supporting = tuple(item["absolute_instruction"] for item in supporting_items)
    instructions = core + supporting
    contrastive = tuple(item["contrastive_instruction"] for item in (*core_items, *supporting_items))
    claim_ids = tuple(
        claim
        for item in (*core_items, *supporting_items)
        for claim in item.get("source_claim_ids", (item.get("claim_id"),))
        if claim
    )
    overridden = tuple(claim for item in dropped for claim in item.get("claim_ids", ()))
    if any(term in text.casefold() for text in instructions for term in _FORBIDDEN_CONTENT_TERMS):
        raise GameStyleError("game style projection attempted to change character content")
    # Explicit rendering preferences remain authoritative; the profile is a soft delta.
    _ = context.explicit_preferences, context.explicit_rendering_preferences
    return StyleInstructionFragment(
        game_style_id=profile.game_style_id,
        profile_version=profile.profile_version,
        projection_version=PROJECTION_VERSION,
        instructions=instructions,
        source_claim_ids=claim_ids,
        core_instructions=core,
        supporting_instructions=supporting,
        contrastive_instructions=contrastive,
        rendering_signature=tuple(item.to_dict() for item in profile.rendering_signature),
        rules=tuple(dict(item) for item in (*core_items, *supporting_items)),
        global_rendering_contract=context.global_rendering_contract,
        overridden_claim_ids=overridden,
        applied_rules=tuple(applied),
        adapted_rules=tuple(adapted),
        dropped_rules=tuple(dropped),
    )


def validate_game_style_preference_preservation(
    fragment: StyleInstructionFragment | Mapping[str, Any] | None,
    context: CharacterDesignContext | Mapping[str, Any],
) -> None:
    """Hard-gate a projected fragment before generation can proceed.

    The gate is deliberately conservative: any instruction that names a
    character-content field is rejected, while explicit rendering preferences
    are allowed only when the conflicting claim was removed by the projector.
    """
    if fragment is None:
        return
    data = fragment.to_dict() if isinstance(fragment, StyleInstructionFragment) else dict(fragment)
    instructions = tuple(str(item) for item in data.get("instructions", ()))
    if any(term in text.casefold() for text in instructions for term in _FORBIDDEN_CONTENT_TERMS):
        raise GameStyleError("preference preservation gate rejected a content-changing game rule")
    if not isinstance(context, CharacterDesignContext):
        context = CharacterDesignContext(
            explicit_preferences=dict(context.get("explicit_preferences") or {}),
            explicit_rendering_preferences=dict(context.get("explicit_rendering_preferences") or {}),
            global_rendering_contract=str(context.get("global_rendering_contract") or "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"),
        )
    claim_ids = set(str(item) for item in data.get("source_claim_ids", ()))
    overridden = set(str(item) for item in data.get("overridden_claim_ids", ()))
    adapted_claims = {
        str(claim)
        for item in data.get("adapted_rules", ())
        if isinstance(item, Mapping)
        for claim in item.get("claim_ids", ())
    }
    for key in context.explicit_rendering_preferences:
        token = {
            "edge_treatment": "edge_treatment",
            "shading_strategy": "shading",
            "detail_density": "detail_density",
            "texture_detail": "texture_detail",
        }.get(str(key).casefold())
        if token and any(token in claim.casefold() for claim in claim_ids):
            if any(claim in adapted_claims for claim in claim_ids):
                continue
            raise GameStyleError(f"explicit rendering preference was not preserved: {key}")
        if token and any(token in claim.casefold() for claim in overridden):
            continue


def game_style_gate_variable(selected: str | None = None, *, source: str | None = None) -> dict[str, Any]:
    """Build the single User Decide field without treating it as character identity."""
    options = [{"id": "DEFAULT", "value": None, "reason": "使用全局现代商业二游渲染契约。", "diversity_risk": "low"}]
    for profile in game_style_registry().profiles.values():
        options.append({"id": profile.game_style_id, "value": profile.game_style_id, "reason": f"使用已审核的 {profile.display_name} 渲染增量。", "diversity_risk": "low"})
    canonical, request = normalize_game_style_request(selected)
    return {
        "variable": GAME_STYLE_FIELD,
        "recommended": None,
        "recommendation_reason": "只影响画法与渲染语言，不改变发色、身材、服装、鞋履等设计选择。",
        "recommendation_reason_en": "Changes rendering language only; it does not change hair, body, clothing, footwear, or other design choices.",
        "options": options,
        "allow_custom": True,
        "allow_ai_delegate": True,
        "user_selection": canonical,
        "selection_source": source,
        "locked": bool(source),
        "user_visible": True,
        "requested_value": request,
    }


def migrate_game_style_fields(sheet: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Add the optional field in memory so old checkpoints continue as global style."""
    migrated = deepcopy(dict(sheet))
    variables = migrated.setdefault("variables", {})
    if GAME_STYLE_FIELD in variables:
        migrated.setdefault("game_style_id", variables[GAME_STYLE_FIELD].get("user_selection"))
        migrated.setdefault("game_style_request", variables[GAME_STYLE_FIELD].get("requested_value"))
        return migrated, None
    variables[GAME_STYLE_FIELD] = game_style_gate_variable()
    migrated.setdefault("game_style_id", None)
    migrated.setdefault("game_style_request", None)
    return migrated, {
        "event": "game_style_migration",
        "audit_event": "GAME_STYLE_DEFAULT_MIGRATION",
        "new_effective_value": None,
        "source": "migrated_default",
    }


def unsupported_game_style_message(request: str | None) -> str | None:
    """Return stable UX copy for an unsupported explicit game request."""
    if request and resolve_game_style(request) is None and _normalized_alias(request) not in {_normalized_alias(item) for item in _DEFAULT_TOKENS}:
        return "当前没有该游戏的已验证 Style Profile，将继续使用默认现代商业二游渲染风格。"
    return None


def evaluate_style_difference_validity(
    character_preservation: str,
    rendering_difference: str,
) -> dict[str, Any]:
    """Apply the v2 post-generation gate without accepting a weak style read."""
    character_ok = str(character_preservation).upper() == "PASS"
    rendering_ok = str(rendering_difference).upper() == "CLEAR_CHARACTER_RENDERING_DIFFERENCE"
    return {
        "gate": STYLE_DIFFERENCE_VALIDITY_GATE,
        "status": "PASS" if character_ok and rendering_ok else "FAIL",
        "character_preservation": str(character_preservation),
        "rendering_difference": str(rendering_difference),
        "reason": "character preservation and clear subject rendering difference are both required",
    }
