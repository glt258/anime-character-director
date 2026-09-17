"""Keep historical visual context out of new character-generation runs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence


DEFAULT_BLOCKED_CONTEXT_SOURCES = (
    "previous_run_character_design",
    "previous_run_candidates",
    "previous_run_image_prompts",
    "previous_run_visual_critic_summary",
    "previous_run_image_description",
    "unrequested_historical_visual_features",
)

_VISUAL_FIELDS = (
    "hair_color",
    "hair_style_family",
    "outfit_direction",
    "dominant_palette",
    "major_accessories",
    "body_markings",
    "eye_color",
    "nonhuman_trait_level",
    "fanservice_level",
    "body_build",
    "background_direction",
    "footwear_family",
    "legwear_family",
    "exposure_strategy",
    "leg_accessory_family",
    "foot_visibility",
    "pose_intent",
    "pose_family",
    "character_visual_style",
)

_HISTORY_REFERENCE = r"(?:上一版|上一张|前一个角色|上一个角色|之前(?:的)?(?:角色|版本|设计|那张)?|previous(?:\s+(?:run|design|character|version|image))?|prior(?:\s+(?:run|design|character|version|image))?|last\s+(?:run|design|character|version|image))"
_INHERIT_REQUEST = r"(?:沿用|参考|基于|保留|继承|继续|变体|variation|continuation|inherit(?:ance)?|based\s+on|keep|retain|preserve)"
_EXPLICIT_INHERITANCE = re.compile(
    rf"(?:{_INHERIT_REQUEST}).{{0,32}}(?:{_HISTORY_REFERENCE})|(?:{_HISTORY_REFERENCE}).{{0,32}}(?:{_INHERIT_REQUEST})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class VisualContextFirewall:
    """The only historical visuals allowed into generation are user-named ones."""

    inherit_previous_visuals: bool = False
    allowed_visual_inheritance: tuple[str, ...] = ()
    blocked_context_sources: tuple[str, ...] = DEFAULT_BLOCKED_CONTEXT_SOURCES
    visual_context_firewall_applied: bool = True

    @classmethod
    def from_request(cls, text: str, constraints: Mapping[str, Any] | None = None) -> "VisualContextFirewall":
        raw = str(text)
        constraints = constraints or {}
        explicit_fields = set(constraints.get("explicit_user_fields", ()))
        has_specific_keep = bool(re.search(r"(?:保留|keep|retain|preserve)", raw, re.IGNORECASE)) and bool(explicit_fields.intersection(_VISUAL_FIELDS))
        if not _EXPLICIT_INHERITANCE.search(raw) and not has_specific_keep:
            return cls()
        allowed = [
            f"{name}={constraints[name]}"
            for name in _VISUAL_FIELDS
            if name in explicit_fields and name in constraints
        ]
        if not allowed:
            allowed.append("previous_run_visual_design")
        return cls(True, tuple(allowed))

    @classmethod
    def from_metadata(cls, metadata: Mapping[str, Any] | "VisualContextFirewall" | None) -> "VisualContextFirewall":
        if isinstance(metadata, cls):
            return metadata
        data = dict(metadata or {})
        return cls(
            bool(data.get("inherit_previous_visuals", False)),
            tuple(data.get("allowed_visual_inheritance") or ()),
            tuple(data.get("blocked_context_sources") or DEFAULT_BLOCKED_CONTEXT_SOURCES),
            bool(data.get("visual_context_firewall_applied", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def generation_context(
        self,
        *,
        current_user_request: str,
        current_run_choices: Sequence[Mapping[str, Any]] = (),
        confirmed_gate_outputs: Sequence[Mapping[str, Any]] = (),
        global_style_contract: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME",
        historical_visual_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build generation inputs; historical data is filtered or omitted here."""
        context: dict[str, Any] = {
            "scope": "current_run_only",
            "current_user_request": str(current_user_request),
            "current_run_choices": deepcopy(list(current_run_choices)),
            "confirmed_gate_outputs": deepcopy(list(confirmed_gate_outputs)),
            "global_style_contract": global_style_contract,
            "inherit_previous_visuals": self.inherit_previous_visuals,
            "allowed_visual_inheritance": list(self.allowed_visual_inheritance),
            "blocked_context_sources": list(self.blocked_context_sources),
            "visual_context_firewall_applied": self.visual_context_firewall_applied,
        }
        inherited = self._filter_historical_visuals(historical_visual_context)
        if inherited:
            context["explicitly_inherited_visuals"] = inherited
        return context

    def anti_repetition_context(self, historical_visual_context: Any) -> dict[str, Any]:
        """Expose history to similarity checks without making it generation input."""
        return {
            "purpose": "anti_repetition_only",
            "generation_allowed": False,
            "blocked_context_sources": list(self.blocked_context_sources),
            "history": deepcopy(historical_visual_context),
        }

    def _filter_historical_visuals(self, history: Mapping[str, Any] | None) -> dict[str, Any]:
        if not self.inherit_previous_visuals or not history:
            return {}
        if "previous_run_visual_design" in self.allowed_visual_inheritance:
            return deepcopy(dict(history))
        allowed_fields = {
            item.split("=", 1)[0]
            for item in self.allowed_visual_inheritance
            if "=" in item
        }
        final_design = history.get("final_design") if isinstance(history.get("final_design"), Mapping) else {}
        source = history.get("visual_preferences") if isinstance(history.get("visual_preferences"), Mapping) else final_design.get("visual_preferences") if isinstance(final_design.get("visual_preferences"), Mapping) else history
        return {
            field: deepcopy(source[field])
            for field in allowed_fields
            if field in source
        }


__all__ = ["DEFAULT_BLOCKED_CONTEXT_SOURCES", "VisualContextFirewall"]
