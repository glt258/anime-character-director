"""Small, dependency-free runtime gate for user-owned visual identity choices."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

try:
    from .regional_style_runtime import (
        DEFAULT_FACE_AESTHETIC_PROFILE,
        DEFAULT_FACE_AESTHETIC_SOURCE,
        DEFAULT_STYLE_INHERITANCE_POLICY,
        DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        FaceAestheticProfile,
        RegionalVisualLanguage,
        migrate_face_aesthetic_fields,
        migrate_regional_style_fields,
        resolve_face_aesthetic_profile,
    )
    from .leg_separation_runtime import migrate_leg_separation_fields, validate_pose_options
    from .pose_intent_runtime import migrate_pose_intent_fields, normalize_pose_intent_contract, resolve_pose_intent
except ImportError:  # pragma: no cover - supports direct host imports
    from regional_style_runtime import (  # type: ignore
        DEFAULT_FACE_AESTHETIC_PROFILE,
        DEFAULT_FACE_AESTHETIC_SOURCE,
        DEFAULT_STYLE_INHERITANCE_POLICY,
        DEFAULT_REGIONAL_VISUAL_LANGUAGE,
        FaceAestheticProfile,
        RegionalVisualLanguage,
        migrate_face_aesthetic_fields,
        migrate_regional_style_fields,
        resolve_face_aesthetic_profile,
    )
    from leg_separation_runtime import migrate_leg_separation_fields, validate_pose_options  # type: ignore
    from pose_intent_runtime import migrate_pose_intent_fields, normalize_pose_intent_contract, resolve_pose_intent  # type: ignore


USER_OWNED_IDENTITY_VARIABLES = (
    "hair_color",
    "hair_style_family",
    "outfit_direction",
    "dominant_palette",
    "major_accessories",
    "body_markings",
    "nonhuman_trait_level",
    "background_direction",
)

AI_PROPOSED_OPTIONAL_VARIABLES = (
    "footwear_family",
    "legwear",
    "exposure_strategy",
    "legwear_family",
    "leg_accessory_family",
    "foot_visibility",
    "lower_body_visual_reason",
    "gloves",
    "eye_color",
    "makeup_intensity",
    "nail_design",
    "weapon_tool_family",
    "pose_intent",
    "pose_family",
    "expression_family",
    "visible_skin_level",
    "secondary_accessories",
    "asymmetry_level",
    "hairstyle_ornament",
    "tattoo_placement",
    "tail_shape_length",
    "ear_horn_shape",
    "material_emphasis",
)

AI_IMPLEMENTATION_VARIABLES = (
    "silhouette_balance",
    "shape_language",
    "negative_space",
    "edge_language",
    "clothing_construction",
    "seam_placement",
    "closure_system",
    "material_hierarchy",
    "fabric_behavior",
    "anchor_hierarchy",
    "detail_density",
    "visual_rhythm",
    "color_proportion",
    "secondary_color_coordination",
    "prop_construction",
    "functional_plausibility",
    "visualized_narrative_logic",
    "foreground_background_separation",
    "pose_weight_distribution",
    "hand_gesture_refinement",
    "anatomy_safe_implementation",
    "line_cel_shading_language",
    "prompt_compiler_formatting",
)

IDENTITY_VARIABLES = USER_OWNED_IDENTITY_VARIABLES
OPTIONAL_VARIABLES = AI_PROPOSED_OPTIONAL_VARIABLES
IMPLEMENTATION_VARIABLES = AI_IMPLEMENTATION_VARIABLES
DEFAULT_GLOBAL_RENDERING_STYLE = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME"

STATES = (
    "ART_SELECTED",
    "VISUAL_PREFERENCES_PROPOSED",
    "AWAITING_VISUAL_PREFERENCE_SELECTION",
    "VISUAL_PREFERENCES_LOCKED",
    "FINAL_DESIGNED",
    "DESIGN_REVIEWED",
    "GENERATION_READY",
)

_BLACK_HAIR_TOKENS = {
    "black",
    "near-black",
    "blue-black",
    "charcoal-black",
    "very dark navy",
    "dark navy",
    "ebony",
}


class GateError(ValueError):
    """Raised when the workflow tries to bypass a Human-owned decision."""


def _value_text(value: Any) -> str:
    if isinstance(value, list):
        return " + ".join(str(item) for item in value)
    return str(value)


def _is_black_hair(value: Any) -> bool:
    text = _value_text(value).strip().lower()
    return text in _BLACK_HAIR_TOKENS or any(token in text for token in ("near-black", "blue-black", "charcoal-black"))


def validate_sheet(sheet: dict[str, Any]) -> None:
    """Validate the runtime-relevant shape and the hair-diversity policy."""
    if not isinstance(sheet, dict) or not isinstance(sheet.get("variables"), dict):
        raise GateError("visual preference sheet must contain a variables object")
    variables = sheet["variables"]
    missing = [name for name in IDENTITY_VARIABLES if name not in variables]
    if missing:
        raise GateError(f"missing identity variables: {', '.join(missing)}")
    for name, item in variables.items():
        if not isinstance(item, dict):
            raise GateError(f"{name} must be an object")
        for key in ("recommended", "recommendation_reason", "options", "allow_custom", "allow_ai_delegate"):
            if key not in item:
                raise GateError(f"{name} is missing {key}")
        if not isinstance(item["options"], list) or not item["options"]:
            raise GateError(f"{name}.options must contain at least one candidate")
        for option in item["options"]:
            if not isinstance(option, dict) or not {"id", "value", "reason", "diversity_risk"} <= option.keys():
                raise GateError(f"{name}.options entries require id, value, reason, diversity_risk")
    if isinstance(variables.get("pose_family"), dict):
        try:
            validate_pose_options(variables["pose_family"]["options"])
        except ValueError as error:
            raise GateError(f"pose_family contains a forbidden pose: {error}") from error
    if "pose_intent" in sheet:
        try:
            resolve_pose_intent(sheet["pose_intent"])
        except ValueError as error:
            raise GateError(f"unsupported pose_intent: {error}") from error
    if "pose_intent_contract" in sheet:
        try:
            normalize_pose_intent_contract(sheet["pose_intent_contract"])
        except ValueError as error:
            raise GateError(f"invalid pose_intent_contract: {error}") from error
    for name in ("major_accessories", "body_markings"):
        if not any(_value_text(option["value"]).strip().lower() == "none" for option in variables[name]["options"]):
            raise GateError(f"{name} must always expose a none option")
    hair = variables["hair_color"]
    explicit_user_request = bool(sheet.get("explicit_user_request"))
    if _is_black_hair(hair["recommended"]) and not explicit_user_request:
        raise GateError("AI may not recommend black hair without an explicit user request")
    regional = sheet.get("regional_visual_language", DEFAULT_REGIONAL_VISUAL_LANGUAGE)
    if regional not in {item.value for item in RegionalVisualLanguage}:
        raise GateError(f"unsupported regional visual language: {regional}")
    source = sheet.get("regional_visual_language_source", "default_style_policy")
    allowed_sources = {
        "default_style_policy",
        "explicit_user_selection",
        "explicit_user_override",
        "benchmark_delegation",
        "migrated_default",
    }
    if source not in allowed_sources:
        raise GateError(f"unsupported regional visual language source: {source}")
    if source == "explicit_user_override" and not sheet.get("regional_style_override_reason"):
        raise GateError("regional style override requires a reason")
    face = sheet.get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE)
    try:
        resolve_face_aesthetic_profile(
            face,
            source=sheet.get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE),
            style_inheritance_policy=sheet.get("style_inheritance_policy", DEFAULT_STYLE_INHERITANCE_POLICY),
        )
    except ValueError as error:
        raise GateError(f"invalid face_aesthetic_profile: {error}") from error


def _new_audit(sheet: dict[str, Any]) -> dict[str, Any]:
    decisions = {}
    for name in IDENTITY_VARIABLES:
        item = sheet["variables"][name]
        decisions[name] = {
            "selection": item.get("user_selection"),
            "source": item.get("selection_source"),
            "locked": bool(item.get("locked")),
        }
    return {
        "policy": "Human Audit Policy",
        "regional_visual_language": sheet.get("regional_visual_language", DEFAULT_REGIONAL_VISUAL_LANGUAGE),
        "regional_visual_language_source": sheet.get("regional_visual_language_source", "default_style_policy"),
        "face_aesthetic_contract": deepcopy(sheet.get("face_aesthetic_contract") or {
            "face_aesthetic_profile": sheet.get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE),
            "face_aesthetic_source": sheet.get("face_aesthetic_source", DEFAULT_FACE_AESTHETIC_SOURCE),
        }),
        "identity_variables": decisions,
        "all_identity_decisions_explicit": all(
            decision["source"] in {"user", "mix", "custom", "ai_delegate"}
            for decision in decisions.values()
        ),
    }


@dataclass
class VisualPreferenceSession:
    state: str = "ART_SELECTED"
    sheet: dict[str, Any] | None = None
    audit: dict[str, Any] | None = None
    history: list[dict[str, str]] = field(default_factory=list)

    def propose(self, sheet: dict[str, Any]) -> dict[str, Any]:
        if self.state != "ART_SELECTED":
            raise GateError(f"cannot propose preferences from {self.state}")
        leg_migrated_sheet, leg_event = migrate_leg_separation_fields(sheet)
        pose_migrated_sheet, pose_event = migrate_pose_intent_fields(leg_migrated_sheet)
        migrated_sheet, migration_event = migrate_regional_style_fields(pose_migrated_sheet)
        migrated_sheet, face_event = migrate_face_aesthetic_fields(migrated_sheet)
        validate_sheet(migrated_sheet)
        self.sheet = deepcopy(migrated_sheet)
        if migration_event:
            self.history.append(migration_event)
        if leg_event:
            self.history.append(leg_event)
        if pose_event:
            self.history.append(pose_event)
        if face_event:
            self.history.append(face_event)
        for item in self.sheet["variables"].values():
            item.setdefault("user_selection", None)
            item.setdefault("selection_source", None)
            item["locked"] = False
        self.state = "VISUAL_PREFERENCES_PROPOSED"
        self.history.append({"from": "ART_SELECTED", "to": self.state, "event": "propose"})
        return deepcopy(self.sheet)

    def open_selection_gate(self) -> None:
        if self.state != "VISUAL_PREFERENCES_PROPOSED":
            raise GateError(f"cannot open selection gate from {self.state}")
        self.state = "AWAITING_VISUAL_PREFERENCE_SELECTION"
        self.history.append({"from": "VISUAL_PREFERENCES_PROPOSED", "to": self.state, "event": "open_gate"})

    def select(
        self,
        variable: str,
        *,
        option_id: str | None = None,
        custom: Any = None,
        mix: list[Any] | None = None,
        delegate_to_ai: bool = False,
    ) -> None:
        if self.state != "AWAITING_VISUAL_PREFERENCE_SELECTION" or self.sheet is None:
            raise GateError("visual preference selection is not open")
        if variable not in IDENTITY_VARIABLES:
            raise GateError(f"{variable} is not a blocking identity variable")
        choices = [option for option in self.sheet["variables"][variable]["options"] if option.get("id") == option_id]
        if option_id and not choices:
            raise GateError(f"unknown option {option_id} for {variable}")
        if custom is not None and not self.sheet["variables"][variable]["allow_custom"]:
            raise GateError(f"custom selection is disabled for {variable}")
        if delegate_to_ai and not self.sheet["variables"][variable]["allow_ai_delegate"]:
            raise GateError(f"AI delegation is disabled for {variable}")
        if sum(value is not None for value in (option_id, custom, mix)) + int(delegate_to_ai) != 1:
            raise GateError("choose exactly one of option_id, custom, mix, or delegate_to_ai")
        item = self.sheet["variables"][variable]
        if option_id:
            selection, source = choices[0]["value"], "user"
        elif custom is not None:
            selection, source = custom, "custom"
        elif mix is not None:
            if not mix:
                raise GateError("mix must contain at least one value")
            selection, source = mix, "mix"
        else:
            selection, source = item["recommended"], "ai_delegate"
        item.update(user_selection=selection, selection_source=source, locked=False)

    def lock(self) -> dict[str, Any]:
        if self.state != "AWAITING_VISUAL_PREFERENCE_SELECTION" or self.sheet is None:
            raise GateError("visual preferences are not awaiting selection")
        missing = [
            name for name in IDENTITY_VARIABLES
            if self.sheet["variables"][name].get("selection_source") not in {"user", "mix", "custom", "ai_delegate"}
        ]
        if missing:
            raise GateError(f"explicit decision required before lock: {', '.join(missing)}")
        for name in IDENTITY_VARIABLES:
            self.sheet["variables"][name]["locked"] = True
        self.audit = _new_audit(self.sheet)
        if not self.audit["all_identity_decisions_explicit"]:
            raise GateError("Human Audit Policy failed: an identity decision is implicit")
        self.state = "VISUAL_PREFERENCES_LOCKED"
        self.history.append({"from": "AWAITING_VISUAL_PREFERENCE_SELECTION", "to": self.state, "event": "lock"})
        return deepcopy(self.audit)

    def advance_to_final_design(self) -> None:
        if self.state != "VISUAL_PREFERENCES_LOCKED":
            raise GateError("Final Design is blocked until visual preferences are locked")
        self.state = "FINAL_DESIGNED"

    def advance_to_generation_ready(self) -> None:
        if self.state != "DESIGN_REVIEWED":
            raise GateError("Generation Ready requires Design Review")
        self.state = "GENERATION_READY"

    def complete_design_review(self) -> None:
        if self.state != "FINAL_DESIGNED":
            raise GateError("Design Review requires Final Design")
        self.state = "DESIGN_REVIEWED"

    def write_artifacts(self, output_dir: str | Path) -> tuple[Path, Path]:
        if self.sheet is None:
            raise GateError("no visual preference sheet exists")
        target = Path(output_dir)
        target.mkdir(parents=True, exist_ok=True)
        sheet_path = target / "visual_preference_sheet.json"
        report_path = target / "visual_preference_report.md"
        payload = {**self.sheet, "state": self.state, "audit": self.audit, "history": self.history}
        sheet_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(render_report(self.sheet, self.state, self.audit), encoding="utf-8")
        return sheet_path, report_path


def render_report(sheet: dict[str, Any], state: str, audit: dict[str, Any] | None = None) -> str:
    lines = [
        "# Visual Preference Report",
        "",
        f"- State: `{state}`",
        "- AI may recommend; the Human owns identity-variable decisions.",
        "",
        "## Rendering Style",
        "",
        "### Three-layer Style Architecture",
        "",
        f"- Rendering Foundation: `{DEFAULT_GLOBAL_RENDERING_STYLE}`",
        f"- Regional Visual Language: `{sheet.get('regional_visual_language', DEFAULT_REGIONAL_VISUAL_LANGUAGE)}`",
        f"- Regional Source: `{sheet.get('regional_visual_language_source', 'default_style_policy')}`",
        "- Character Visual Style is case-specific design language and cannot override the regional layer.",
        "",
        "- Character Visual Style belongs to character design and never replaces the rendering medium.",
        f"- Global Rendering Style: `{DEFAULT_GLOBAL_RENDERING_STYLE}` (default)",
        "- Rendering-style override is allowed only when the user explicitly requests it.",
        "",
        "## Identity Variables",
        "",
    ]
    for name in IDENTITY_VARIABLES:
        item = sheet["variables"][name]
        lines.extend([
            f"### {name}",
            f"- Recommended: `{item['recommended']}`",
            f"- Recommendation reason: {item['recommendation_reason']}",
            "- Options:",
        ])
        for option in item["options"]:
            lines.append(f"  - {option['id']}. `{option['value']}` — {option['reason']} (diversity risk: `{option['diversity_risk']}`)")
        lines.extend([
            f"- User Override Allowed: `{bool(item['allow_custom'])}`",
            f"- AI Delegation Allowed: `{bool(item['allow_ai_delegate'])}`",
            f"- User Selection: `{item.get('user_selection')}`",
            f"- Locked: `{bool(item.get('locked'))}`",
            "",
        ])
    lines.extend(["## Current AI Proposal", "", "Optional variables remain proposals and do not block the gate.", ""])
    for name, item in sheet.get("optional_variables", {}).items():
        lines.append(f"- `{name}`: `{item.get('current_ai_proposal')}`; alternatives: {item.get('alternative_suggestions', [])}; User Override Allowed: `{bool(item.get('user_override_allowed', True))}`")
    lower_body = sheet.get("lower_body_visual_variables")
    if lower_body:
        lines.extend(["", "## Lower-Body Visual Variables", "", "Fanservice level and lower-body coverage remain independent decisions."])
        for name, value in lower_body.items():
            lines.append(f"- `{name}`: `{value}`")
    if audit:
        lines.extend(["", "## Human Audit", "", f"- All identity decisions explicit: `{audit['all_identity_decisions_explicit']}`"])
    return "\n".join(lines) + "\n"
