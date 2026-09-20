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


PROFILE_VERSION = "game_style_profile_v1"
PROJECTION_VERSION = "game_style_projection_v1"
GAME_STYLE_FIELD = "game_rendering_style"
_REFERENCE_DIR = Path(__file__).resolve().parents[1] / "references" / "game_styles"
_DEFAULT_TOKENS = {"", "none", "default", "global", "默认", "不指定", "自定义"}
_FORBIDDEN_CONTENT_TERMS = (
    "hair", "发色", "发型", "eye", "瞳", "body", "breast", "身材", "outfit", "clothing",
    "服装", "footwear", "鞋", "stocking", "丝袜", "pose", "姿势", "background", "背景",
    "palette", "配色", "accessory", "配件", "sexiness", "性感", "nonhuman", "非人",
    "character identity", "角色身份", "silhouette", "轮廓复制",
)


class GameStyleError(ValueError):
    """Raised when a packaged game-style contract is malformed."""


@dataclass(frozen=True)
class GameStyleProfile:
    """Immutable reviewed profile exposed to production callers."""

    game_style_id: str
    display_name: str
    profile_version: str
    source_analysis_version: str
    sample_manifest_version: str
    integration_review_version: str
    core_rendering_instructions: tuple[dict[str, Any], ...] = ()
    supporting_art_direction_instructions: tuple[dict[str, Any], ...] = ()
    excluded_global_baseline_claim_ids: tuple[str, ...] = ()
    prompt_budget: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "GameStyleProfile":
        game = data.get("game") if isinstance(data.get("game"), Mapping) else {}
        projection = data.get("projection") if isinstance(data.get("projection"), Mapping) else data
        profile = cls(
            game_style_id=str(game.get("id") or data.get("game_style_id") or ""),
            display_name=str(game.get("display_name") or data.get("display_name") or ""),
            profile_version=str(data.get("profile_version") or PROFILE_VERSION),
            source_analysis_version=str(data.get("source_analysis_version") or ""),
            sample_manifest_version=str(data.get("sample_manifest_version") or ""),
            integration_review_version=str(data.get("integration_review_version") or ""),
            core_rendering_instructions=tuple(_instruction(item) for item in projection.get("core_rendering_instructions", ())),
            supporting_art_direction_instructions=tuple(_instruction(item) for item in projection.get("supporting_art_direction_instructions", ())),
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
    global_rendering_contract: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"
    overridden_claim_ids: tuple[str, ...] = ()

    @property
    def prompt_text(self) -> str:
        return " ".join(self.instructions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_style_id": self.game_style_id,
            "profile_version": self.profile_version,
            "projection_version": self.projection_version,
            "instructions": list(self.instructions),
            "source_claim_ids": list(self.source_claim_ids),
            "core_instructions": list(self.core_instructions),
            "supporting_instructions": list(self.supporting_instructions),
            "global_rendering_contract": self.global_rendering_contract,
            "overridden_claim_ids": list(self.overridden_claim_ids),
        }


def _instruction(item: Any) -> dict[str, Any]:
    if not isinstance(item, Mapping) or not item.get("text") or not item.get("claim_id"):
        raise GameStyleError("each projection instruction requires claim_id and text")
    strength = str(item.get("rule_strength", "soft"))
    if strength not in {"hard", "soft"}:
        raise GameStyleError(f"unsupported game style rule strength: {strength}")
    return {
        "claim_id": str(item["claim_id"]),
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
    core_max = int(profile.prompt_budget.get("core_max", 6))
    supporting_max = int(profile.prompt_budget.get("supporting_max", 3))
    if len(profile.core_rendering_instructions) > core_max or len(profile.supporting_art_direction_instructions) > supporting_max:
        raise GameStyleError(f"{profile.game_style_id} exceeds its projection budget")
    for instruction in (*profile.core_rendering_instructions, *profile.supporting_art_direction_instructions):
        if any(term in instruction["text"].casefold() for term in _FORBIDDEN_CONTENT_TERMS):
            raise GameStyleError(f"{profile.game_style_id} contains a character-content instruction")


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
    """Project only reviewed HOW-style instructions within the verified budget."""
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

    def keep(item: Mapping[str, Any]) -> bool:
        claim = str(item["claim_id"]).casefold()
        # WHY: a user-specified rendering property is a hard local override;
        # dropping only the conflicting claim preserves compatible game deltas.
        return not any(
            token in claim
            for key, token in {
                "edge_treatment": "edge_treatment",
                "shading_strategy": "shading",
                "detail_density": "detail_density",
                "texture_detail": "texture_detail",
            }.items()
            if key in explicit_rendering
        )

    core_items = tuple(item for item in profile.core_rendering_instructions if keep(item))
    supporting_items = tuple(item for item in profile.supporting_art_direction_instructions if keep(item))
    overridden = tuple(
        item["claim_id"]
        for item in (*profile.core_rendering_instructions, *profile.supporting_art_direction_instructions)
        if not keep(item)
    )
    core = tuple(item["text"] for item in core_items)
    supporting = tuple(item["text"] for item in supporting_items)
    instructions = core + supporting
    claim_ids = tuple(item["claim_id"] for item in (*core_items, *supporting_items))
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
        global_rendering_contract=context.global_rendering_contract,
        overridden_claim_ids=overridden,
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
    for key in context.explicit_rendering_preferences:
        token = {
            "edge_treatment": "edge_treatment",
            "shading_strategy": "shading",
            "detail_density": "detail_density",
            "texture_detail": "texture_detail",
        }.get(str(key).casefold())
        if token and any(token in claim.casefold() for claim in claim_ids):
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
