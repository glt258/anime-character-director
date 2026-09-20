"""Regional visual-language contracts, compilation, review, and migration."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence
from datetime import datetime, timezone

try:
    from .game_style_runtime import StyleInstructionFragment
    from .leg_separation_runtime import (
        DEFAULT_LEG_SEPARATION_CONTRACT,
        LEG_GEOMETRY_NEGATIVE,
        LEG_GEOMETRY_POSITIVE,
        NO_CROSSED_LEGS_HARD_INVARIANT,
        POSE_FAMILIES,
        LegSeparationError,
        audit_leg_prompt,
        leg_geometry_constraints,
        rewrite_conflicting_pose_language,
        validate_pose_description,
    )
    from .pose_intent_runtime import (
        PoseIntentContract,
        audit_pose_intent_prompt,
        build_pose_intent_contract,
        normalize_pose_intent_contract,
        pose_intent_prompt_lines,
        resolve_pose_intent,
    )
    from .interaction_candidates import (
        BACKGROUND_SPECIFICATION_FIELDS,
        POSE_SPECIFICATION_FIELDS,
        background_specification_for_family,
        pose_specification_for_family,
    )
    from .visual_context_firewall import VisualContextFirewall
except ImportError:  # pragma: no cover - supports direct host imports
    from game_style_runtime import StyleInstructionFragment  # type: ignore
    from leg_separation_runtime import (  # type: ignore
        DEFAULT_LEG_SEPARATION_CONTRACT,
        LEG_GEOMETRY_NEGATIVE,
        LEG_GEOMETRY_POSITIVE,
        NO_CROSSED_LEGS_HARD_INVARIANT,
        POSE_FAMILIES,
        LegSeparationError,
        audit_leg_prompt,
        leg_geometry_constraints,
        rewrite_conflicting_pose_language,
        validate_pose_description,
    )
    from pose_intent_runtime import (  # type: ignore
        PoseIntentContract,
        audit_pose_intent_prompt,
        build_pose_intent_contract,
        normalize_pose_intent_contract,
        pose_intent_prompt_lines,
        resolve_pose_intent,
    )
    from interaction_candidates import (  # type: ignore
        BACKGROUND_SPECIFICATION_FIELDS,
        POSE_SPECIFICATION_FIELDS,
        background_specification_for_family,
        pose_specification_for_family,
    )
    from visual_context_firewall import VisualContextFirewall  # type: ignore


class RegionalVisualLanguage(str, Enum):
    EAST_ASIAN_CONTEMPORARY_GACHA = "EAST_ASIAN_CONTEMPORARY_GACHA"
    WESTERN_ANIME_INSPIRED = "WESTERN_ANIME_INSPIRED"
    REGION_NEUTRAL_ANIME = "REGION_NEUTRAL_ANIME"
    CUSTOM = "CUSTOM"


class RegionalVisualLanguageSource(str, Enum):
    DEFAULT_STYLE_POLICY = "default_style_policy"
    EXPLICIT_USER_SELECTION = "explicit_user_selection"
    EXPLICIT_USER_OVERRIDE = "explicit_user_override"
    BENCHMARK_DELEGATION = "benchmark_delegation"
    MIGRATED_DEFAULT = "migrated_default"


class FaceAestheticProfile(str, Enum):
    EAST_ASIAN_COMMERCIAL_GACHA_FACE = "EAST_ASIAN_COMMERCIAL_GACHA_FACE"
    WESTERN_INSPIRED_GACHA_FACE = "WESTERN_INSPIRED_GACHA_FACE"
    NEUTRAL_GACHA_FACE = "NEUTRAL_GACHA_FACE"


class FaceAestheticSource(str, Enum):
    SYSTEM_DEFAULT = "system_default"
    HUMAN_EXPLICIT = "human_explicit"
    DELEGATED_RESOLUTION = "delegated_resolution"
    MIGRATED_DEFAULT = "migrated_default"


class StyleInheritancePolicy(str, Enum):
    NO_FACE_AESTHETIC_INHERITANCE = "NO_FACE_AESTHETIC_INHERITANCE"
    EXPLICIT_FACE_AESTHETIC_INHERITANCE_ONLY = "EXPLICIT_FACE_AESTHETIC_INHERITANCE_ONLY"


class DriftType(str, Enum):
    WESTERN_ANIME_STYLE_DRIFT = "WESTERN_ANIME_STYLE_DRIFT"
    WESTERN_FANTASY_CONCEPT_DRIFT = "WESTERN_FANTASY_CONCEPT_DRIFT"
    WESTERN_SUPERHERO_ANATOMY_DRIFT = "WESTERN_SUPERHERO_ANATOMY_DRIFT"
    PSEUDO_ORIENTAL_FANTASY_DEFAULT = "PSEUDO_ORIENTAL_FANTASY_DEFAULT"
    GENERIC_FANTASY_RPG_DRIFT = "GENERIC_FANTASY_RPG_DRIFT"
    CHARACTER_SHEET_PRESENTATION_DRIFT = "CHARACTER_SHEET_PRESENTATION_DRIFT"
    OUTFIT_FAMILY_COLLAPSE = "OUTFIT_FAMILY_COLLAPSE"
    BACKGROUND_PRESENTATION_COLLAPSE = "BACKGROUND_PRESENTATION_COLLAPSE"
    REGIONAL_STYLE_INFANTILIZATION = "REGIONAL_STYLE_INFANTILIZATION"
    ARCHETYPE_SHORTCUT = "ARCHETYPE_SHORTCUT"
    ARCHETYPE_SHORTCUT_REPLACEMENT = "ARCHETYPE_SHORTCUT_REPLACEMENT"
    CONSERVATIVE_COVERAGE_COLLAPSE = "CONSERVATIVE_COVERAGE_COLLAPSE"
    LEGWEAR_FAMILY_COLLAPSE = "LEGWEAR_FAMILY_COLLAPSE"
    FOOTWEAR_FAMILY_COLLAPSE = "FOOTWEAR_FAMILY_COLLAPSE"
    FOOTWEAR_GROUNDING_FAIL = "FOOTWEAR_GROUNDING_FAIL"
    LEGWEAR_GROUNDING_FAIL = "LEGWEAR_GROUNDING_FAIL"
    LOWER_BODY_ANCHOR_MISS = "LOWER_BODY_ANCHOR_MISS"


DEFAULT_REGIONAL_VISUAL_LANGUAGE = RegionalVisualLanguage.EAST_ASIAN_CONTEMPORARY_GACHA.value
DEFAULT_FACE_AESTHETIC_PROFILE = FaceAestheticProfile.EAST_ASIAN_COMMERCIAL_GACHA_FACE.value
DEFAULT_FACE_AESTHETIC_SOURCE = FaceAestheticSource.SYSTEM_DEFAULT.value
DEFAULT_STYLE_INHERITANCE_POLICY = StyleInheritancePolicy.NO_FACE_AESTHETIC_INHERITANCE.value
DEFAULT_FACE_AESTHETIC_GUARDRAILS = (
    "keep anime-first facial abstraction and restrained facial planes",
    "do not drift toward western facial structure or semi-realistic western portrait language",
)
FACE_AESTHETIC_CONTRACTS: dict[str, dict[str, Any]] = {
    DEFAULT_FACE_AESTHETIC_PROFILE: {
        "default_face_region_language": "East Asian commercial gacha anime facial design language",
        "facial_structure_bias": "anime-first facial abstraction, restrained facial planes, clean graphic jaw/chin construction",
        "facial_style_guardrail": "Do not drift toward western facial structure, western illustration-style facial treatment, comic-book facial design, or semi-realistic western portrait language / European-American fantasy portrait language.",
        "regional_face_language": DEFAULT_FACE_AESTHETIC_PROFILE,
        "facial_style_drift": "NONE",
        "guardrails": DEFAULT_FACE_AESTHETIC_GUARDRAILS,
    },
    FaceAestheticProfile.WESTERN_INSPIRED_GACHA_FACE.value: {
        "default_face_region_language": "western-inspired face aesthetics within contemporary commercial gacha anime",
        "facial_structure_bias": "stylized western-inspired facial structure with controlled planes and commercial gacha simplification",
        "facial_style_guardrail": "Keep the same stylized anime-first commercial gacha medium; do not convert the full rendering language into western realistic illustration, western comic-book art, or semi-realistic fantasy portraiture.",
        "regional_face_language": FaceAestheticProfile.WESTERN_INSPIRED_GACHA_FACE.value,
        "facial_style_drift": "NONE",
        "guardrails": (
            "remain within contemporary commercial gacha anime",
            "do not become western realistic illustration or semi-realistic fantasy portraiture",
        ),
    },
    FaceAestheticProfile.NEUTRAL_GACHA_FACE.value: {
        "default_face_region_language": "region-neutral commercial gacha anime facial design language",
        "facial_structure_bias": "stylized anime-first facial abstraction with balanced, non-regionalized facial planes",
        "facial_style_guardrail": "Avoid photorealistic portrait anatomy and avoid drifting into a specific western realistic illustration language.",
        "regional_face_language": FaceAestheticProfile.NEUTRAL_GACHA_FACE.value,
        "facial_style_drift": "NONE",
        "guardrails": (
            "remain stylized anime-first commercial gacha",
            "avoid photorealistic portrait anatomy",
        ),
    },
}
DRIFT_LEVELS = ("NONE", "LOW", "MEDIUM", "HIGH")
REGIONAL_MATCHES = ("STRONG", "ACCEPTABLE", "WEAK", "FAIL")
OUTFIT_FEATURES = (
    "outfit_family",
    "neckline_family",
    "upper_body_structure",
    "lower_body_structure",
    "outer_layer_family",
    "waist_structure",
    "hanging_cloth_presence",
    "cape_presence",
    "sash_presence",
    "major_trim_language",
    "footwear_family",
    "exposure_strategy",
    "legwear_family",
)
BACKGROUND_FEATURES = (
    "background_family",
    "background_motif",
    "giant_circle_presence",
    "decorative_ring_presence",
    "fantasy_platform_presence",
)
OUTFIT_FAMILIES = (
    "contemporary fantasy",
    "urban fantasy",
    "street fashion",
    "elegant sculptural",
    "relaxed luxury",
    "body-framing fashion",
    "ceremonial",
    "performance-inspired",
    "sporty fantasy",
    "utility fashion",
    "minimal premium",
    "soft layered",
    "asymmetrical fashion",
    "experimental silhouette",
    "romantic fantasy",
    "sensual structured",
    "casual-fantasy",
    "tailored fantasy",
    "open-body layered",
    "hybrid fashion",
)
LOWER_BODY_VISUAL_VARIABLES = (
    "exposure_strategy",
    "legwear_family",
    "leg_accessory_family",
    "footwear_family",
    "foot_visibility",
    "visual_reason",
    "relationship_to_character_style",
    "relationship_to_pose",
    "repetition_risk",
)
LOWER_BODY_LEDGER_FEATURES = (
    "exposure_strategy",
    "thigh_exposure",
    "knee_exposure",
    "calf_exposure",
    "ankle_exposure",
    "foot_exposure",
    "legwear_family",
    "stocking_color_family",
    "stocking_opacity",
    "leg_accessory_family",
    "footwear_family",
    "heel_height",
    "open_toe",
    "barefoot",
    "asymmetrical_lower_body",
)
SKIN_EXPOSURE_STRATEGIES = (
    "fully covered",
    "mostly covered",
    "partial thigh exposure",
    "knee / calf exposure",
    "full-leg exposure",
    "asymmetrical exposure",
    "side-leg exposure",
    "ankle / foot emphasis",
)
LEGWEAR_FAMILIES = (
    "none",
    "sheer tights",
    "opaque tights",
    "patterned tights",
    "thigh-high stockings",
    "knee-high stockings",
    "over-knee socks",
    "fitted leggings",
    "fantasy leg wraps",
    "asymmetric legwear",
    "one-leg stocking / one-leg exposed",
    "integrated bodysuit leg section",
    "loose lower-leg fabric",
)
LEG_ACCESSORY_FAMILIES = (
    "none",
    "thigh ring",
    "leg strap",
    "garter-like decorative band",
    "knee ornament",
    "calf strap",
    "ankle ornament",
    "chain detail",
    "fabric tie",
    "asymmetrical leg accessory",
    "integrated armor / hard accent",
)
FOOTWEAR_FAMILIES = (
    "barefoot",
    "barefoot with ankle / instep ornament",
    "toe-loop footwear",
    "open sandals",
    "fantasy sandals",
    "high sandals",
    "low sandals",
    "flats",
    "loafers",
    "pumps",
    "low heels",
    "high heels",
    "platform shoes",
    "sneakers",
    "soft boots",
    "ankle boots",
    "tall boots",
    "open-toe boots",
    "split-toe / tabi-inspired fantasy footwear",
    "foot-wrap construction",
    "partial footwear",
    "asymmetrical footwear",
)


DEFAULT_REGIONAL_STYLE_POLICY: dict[str, Any] = {
    "default": DEFAULT_REGIONAL_VISUAL_LANGUAGE,
    "allow_user_override": True,
    "face_aesthetic": {
        "default": DEFAULT_FACE_AESTHETIC_PROFILE,
        "inheritance_policy": DEFAULT_STYLE_INHERITANCE_POLICY,
        "contracts": deepcopy(FACE_AESTHETIC_CONTRACTS),
    },
    "contracts": {
        DEFAULT_REGIONAL_VISUAL_LANGUAGE: {
            "positive": (
                "anime-first facial abstraction with simplified facial planes, restrained nose and lips, and clean graphic jaw/chin construction",
                "modern East-Asian commercial gacha illustration grammar with a readable playable-character focal point",
                "anime-proportioned, anatomically coherent bodies with controlled muscle definition and no default superhero massing",
                "character-design-first outfit construction; vary outfit families instead of defaulting to generic fantasy robes",
                "polished anime game lighting, intentional material separation, and premium but stylized 2D finish",
                "commercial gacha presentation: finished promotional-quality character illustration, not a model sheet or concept board",
            ),
            "negative": (
                "western comic anatomy",
                "western superhero proportions",
                "western fantasy character concept art",
                "semi-realistic western anime illustration",
                "realistic facial planes, heavy brow ridge, strongly projected realistic nose, realistic full-lip portrait styling",
                "painterly fantasy concept rendering",
            ),
        },
        "WESTERN_ANIME_INSPIRED": {
            "positive": (
                "anime-first facial abstraction with a deliberate western anime-inspired design language",
                "stylized character-design-first illustration with readable commercial 2D presentation",
            ),
            "negative": ("photorealism", "realistic portrait anatomy", "3D-render aesthetics"),
        },
        "REGION_NEUTRAL_ANIME": {
            "positive": (
                "anime-first facial abstraction and stylized, anatomically coherent 2D character design",
                "polished commercial anime illustration with a clear character focal point",
            ),
            "negative": ("photorealism", "realistic portrait anatomy", "3D-render aesthetics"),
        },
        "CUSTOM": {"positive": (), "negative": ()},
    },
    "critic_thresholds": {
        "fail_read_below": 4,
        "acceptable_read_at_least": 6,
        "strong_read_at_least": 8,
        "minimum_confidence": 0.5,
        "outfit_collapse_min_count": 4,
    },
    "lower_body": {
        "adult_free_exploration": True,
        "minor_sexualized_accessories": False,
        "diversity_penalty_is_hard_gate": False,
        "conservative_coverage_min_count": 4,
        "legwear_families": LEGWEAR_FAMILIES,
        "leg_accessory_families": LEG_ACCESSORY_FAMILIES,
        "footwear_families": FOOTWEAR_FAMILIES,
    },
    "pose_constraints": {
        "no_crossed_legs": {
            "enabled": True,
            "severity": "blocking",
            "allow_user_override": False,
            "require_positive_geometry": True,
            "require_actual_image_gate": True,
            "max_pose_only_repair": 1,
        },
        "pose_families": {name: spec.to_dict() for name, spec in POSE_FAMILIES.items()},
    },
    "negative_drift_types": [item.value for item in DriftType],
}


class RegionalStyleError(ValueError):
    """Raised when regional style data is incomplete or contradictory."""


class PromptConstraintConflict(RegionalStyleError):
    """Raised when assembled positive prompt text contradicts a locked field."""

    code = "PROMPT_CONSTRAINT_CONFLICT"

    def __init__(self, conflicts: Sequence[str]) -> None:
        self.conflicts = tuple(str(item) for item in conflicts)
        super().__init__(f"{self.code}: {'; '.join(self.conflicts)}")


HARD_VISUAL_FIELDS = (
    "silhouette_family",
    "hair_structure",
    "horn_topology",
    "upper_body_structure",
    "lower_body_structure",
    "costume_topology",
    "exposure_strategy",
    "legwear_strategy",
    "footwear_category",
    "pose_family",
    "wing_strategy",
    "tail_design",
)
STRONG_VISUAL_FIELDS = (
    "palette_family",
    "material_language",
    "accessory_density",
    "body_line_emphasis",
    "background_family",
    "character_visual_style",
)
_USER_HARD_FIELD_MAP = {
    "hair_color": ("hair_color",),
    "eye_color": ("eye_color",),
    "hair_structure": ("hair_style_family",),
    "costume_topology": ("outfit_direction",),
    "exposure_strategy": ("exposure_strategy",),
    "legwear_strategy": ("legwear_family",),
    "footwear_category": ("footwear_family",),
    "pose_family": ("pose_family",),
    "palette_family": ("dominant_palette",),
    "background_family": ("background_direction",),
    "nonhuman_trait_level": ("nonhuman_trait_level",),
    **{field_name: (field_name,) for field_name in (*POSE_SPECIFICATION_FIELDS, *BACKGROUND_SPECIFICATION_FIELDS)},
}


def _nonempty(value: Any) -> bool:
    return value not in (None, "", (), [], {})


def _first_value(values: Mapping[str, Any], names: Sequence[str]) -> Any:
    for name in names:
        if _nonempty(values.get(name)):
            return values[name]
    return None


def _visual_anti_substitution(
    hard: Mapping[str, Any],
    pose_specification: Mapping[str, str] | None = None,
    background_specification: Mapping[str, str] | None = None,
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    footwear = str(hard.get("footwear_category", "")).lower()
    if "barefoot" in footwear or "bare feet" in footwear:
        result["footwear_category"] = ("no shoes, boots, heels, pumps, or stilettos",)
    elif "combat boot" in footwear:
        result["footwear_category"] = ("do not substitute stilettos, pumps, or generic high heels",)
    elif "open-toe high heel" in footwear or "open toe high heel" in footwear:
        result["footwear_category"] = ("do not substitute combat boots, pumps, or closed footwear",)

    wings = str(hard.get("wing_strategy", "")).lower()
    if any(token in wings for token in ("symbolic", "motif", "graphic")):
        result["wing_strategy"] = ("no physical demon wings or large physical wings",)

    hair = str(hard.get("hair_structure", "")).lower()
    if "bob" in hair or any(token in hair for token in ("short", "jaw-length", "neck-length")):
        result["hair_structure"] = ("do not extend into long flowing or waist-length hair",)

    costume = str(hard.get("costume_topology", "")).lower()
    if "maid" in costume:
        result["costume_topology"] = ("do not substitute armor, trousers, or unrelated fantasy costume topology",)
    if any(token in costume for token in ("trouser", "pants")):
        result["costume_topology"] = ("no skirt, gown, lingerie dress, or high-slit evening dress",)

    background = str(hard.get("background_family", "")).lower()
    architecture_presence = str((background_specification or {}).get("architecture_presence", "")).lower()
    if architecture_presence == "none" or any(token in background for token in ("abstract", "temporal", "haze", "gradient")):
        result["background_specification"] = ("no castle, cathedral, palace, tower complex, or throne-room architecture",)

    pose = {name: str(value).lower() for name, value in (pose_specification or {}).items()}
    if "away from face" in " ".join(pose.values()):
        result["pose_specification"] = ("do not move either hand to the face",)
    if "open palm outward" in pose.get("right_hand_gesture", "") and any(
        token in pose.get("right_arm_action", "") for token in ("extended", "reaching")
    ):
        result["right_hand_gesture"] = ("do not move this hand to the face",)
    return result


@dataclass(frozen=True)
class VisualSpecificationContract:
    """Structured visual lock between Final Design and PromptCompiler."""

    hard_constraints: dict[str, Any] = field(default_factory=dict)
    strong_preferences: dict[str, str] = field(default_factory=dict)
    soft_intent: dict[str, str] = field(default_factory=dict)
    anti_substitution: dict[str, tuple[str, ...]] = field(default_factory=dict)
    explicit_hard_fields: tuple[str, ...] = ()
    priority_order: tuple[str, ...] = (
        "current_run_explicit_user_selection",
        "final_design_hard_specification",
        "art_direction",
        "character_direction",
        "semantic_intent",
    )
    schema_version: str = "1.0.0"
    pose_specification: dict[str, str] = field(default_factory=dict)
    background_specification: dict[str, str] = field(default_factory=dict)
    face_aesthetic_profile: str = DEFAULT_FACE_AESTHETIC_PROFILE
    face_aesthetic_is_default: bool = True
    face_aesthetic_source: str = DEFAULT_FACE_AESTHETIC_SOURCE
    face_aesthetic_guardrails: tuple[str, ...] = DEFAULT_FACE_AESTHETIC_GUARDRAILS
    style_inheritance_policy: str = DEFAULT_STYLE_INHERITANCE_POLICY
    face_aesthetic_contract: dict[str, Any] = field(default_factory=dict)
    explicit_constraints: dict[str, dict[str, Any]] = field(default_factory=dict)
    explicit_constraint_coverage: dict[str, dict[str, Any]] = field(default_factory=dict)
    explicit_constraint_locks: dict[str, Any] = field(default_factory=dict)
    generation_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = deepcopy(asdict(self))
        data["anti_substitution"] = {
            name: list(values) for name, values in self.anti_substitution.items()
        }
        data["explicit_hard_fields"] = list(self.explicit_hard_fields)
        data["priority_order"] = list(self.priority_order)
        data["face_aesthetic_guardrails"] = list(self.face_aesthetic_guardrails)
        if isinstance(data.get("face_aesthetic_contract"), dict):
            data["face_aesthetic_contract"]["face_aesthetic_guardrails"] = list(
                data["face_aesthetic_contract"].get("face_aesthetic_guardrails", ())
            )
        return data


class ExplicitConstraintCoverageGate:
    """Verify that every current-run human hard field survived compilation."""

    @staticmethod
    def evaluate(prompt_bundle: Mapping[str, Any] | PromptBundle) -> dict[str, Any]:
        data = prompt_bundle.to_dict() if isinstance(prompt_bundle, PromptBundle) else dict(prompt_bundle)
        contract = data.get("visual_specification_contract") or {}
        records = contract.get("explicit_constraints") or data.get("explicit_constraints") or {}
        prompt = str(data.get("prompt", ""))
        positive = prompt.split("## Negative Constraints", 1)[0].lower()
        negative = prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[-1].lower()
        fields: dict[str, dict[str, Any]] = {}
        for name, record in records.items():
            record = dict(record) if isinstance(record, Mapping) else {"value": record}
            value = record.get("value")
            if str(name).startswith("raw_hard_constraint_"):
                fields[name] = {**record, "status": "NOT_REPRESENTABLE", "reason": "raw hard constraint preserved verbatim"}
                continue
            if isinstance(value, dict):
                values = [part for key, item in value.items() for part in (key, item)]
            else:
                values = value if isinstance(value, list) else [value]
            tokens = [str(item).replace("_", " ").lower() for item in values if item not in (None, "")]
            matched = [
                token
                for token in tokens
                if any(variant in positive for variant in (token, token.replace(" ", "_"), token.replace(" ", "-")))
            ]
            status = "COVERED" if matched and len(matched) == len(tokens) else "PARTIALLY_COVERED" if matched else "DROPPED"
            if matched and any(token in negative and token not in positive for token in tokens):
                status = "CONFLICTED"
            fields[name] = {**record, "status": status, "matched": matched}
        blocking = [name for name, item in fields.items() if item.get("status") in {"DROPPED", "CONFLICTED"}]
        return {
            "status": "FAIL" if blocking else "PASS",
            "generation_allowed": not blocking,
            "blocking_fields": blocking,
            "fields": fields,
            "gate": "ExplicitConstraintCoverageGate",
        }


def build_visual_specification_contract(
    *,
    design_dna: Mapping[str, Any] | None = None,
    visual_preferences: Mapping[str, Any] | None = None,
    character_visual_style: str = "",
    explicit_user_fields: Sequence[str] = (),
    explicit_constraints: Mapping[str, Any] | None = None,
    soft_intent: Mapping[str, Any] | None = None,
    face_aesthetic_profile: str | None = None,
    face_aesthetic_source: str | None = None,
    style_inheritance_policy: str | None = None,
) -> VisualSpecificationContract:
    """Build a general contract without using archetype-specific defaults."""
    dna = dict(design_dna or {})
    visual = dict(visual_preferences or {})
    explicit = set(str(name) for name in explicit_user_fields)
    requested_face = face_aesthetic_profile or visual.get("face_aesthetic_profile")
    requested_face_source = face_aesthetic_source or visual.get("face_aesthetic_source")
    if requested_face and requested_face_source is None and "face_aesthetic_profile" in explicit:
        requested_face_source = FaceAestheticSource.HUMAN_EXPLICIT.value
    face_selection = resolve_face_aesthetic_profile(
        requested_face,
        source=requested_face_source,
        explicit_user_selection="face_aesthetic_profile" in explicit,
    )
    hard: dict[str, Any] = {}
    explicit_hard: list[str] = []
    records = {
        str(name): dict(record) if isinstance(record, Mapping) else {"value": record, "source": "human_explicit", "priority": "HARD", "locked": True}
        for name, record in dict(explicit_constraints or {}).items()
    }

    for field_name in HARD_VISUAL_FIELDS:
        value = dna.get(field_name)
        for user_key in _USER_HARD_FIELD_MAP.get(field_name, ()):
            if user_key in explicit and _nonempty(visual.get(user_key)):
                value = visual[user_key]
                explicit_hard.append(field_name)
                break
        if _nonempty(value):
            hard[field_name] = str(value)

    for field_name, user_keys in _USER_HARD_FIELD_MAP.items():
        if field_name in hard or not any(user_key in explicit for user_key in user_keys):
            continue
        value = _first_value(visual, user_keys)
        if _nonempty(value):
            hard[field_name] = str(value)
            explicit_hard.append(field_name)

    pose_family = (
        visual.get("pose_family", dna.get("pose_family", "OPEN_PARALLEL_STANCE"))
        if "pose_family" in explicit
        else dna.get("pose_family", "OPEN_PARALLEL_STANCE")
    )
    pose_source = dna.get("pose_specification") if "pose_family" not in explicit else None
    pose_specification = dict(pose_source) if isinstance(pose_source, Mapping) else pose_specification_for_family(pose_family)
    background_family = (
        visual.get("background_direction", dna.get("background_family", ""))
        if "background_direction" in explicit
        else dna.get("background_family", "")
    )
    background_source = dna.get("background_specification") if "background_direction" not in explicit else None
    background_specification = dict(background_source) if isinstance(background_source, Mapping) else background_specification_for_family(background_family)
    for field_name in POSE_SPECIFICATION_FIELDS:
        value = pose_specification.get(field_name)
        if field_name in explicit and _nonempty(visual.get(field_name)):
            value = visual[field_name]
            explicit_hard.append(field_name)
        if _nonempty(value):
            pose_specification[field_name] = str(value)
            hard[field_name] = str(value)
    for field_name in BACKGROUND_SPECIFICATION_FIELDS:
        value = background_specification.get(field_name)
        if field_name in explicit and _nonempty(visual.get(field_name)):
            value = visual[field_name]
            explicit_hard.append(field_name)
        if _nonempty(value):
            background_specification[field_name] = str(value)
            hard[field_name] = str(value)

    strong: dict[str, str] = {}
    for field_name in STRONG_VISUAL_FIELDS:
        value = dna.get(field_name)
        if field_name == "character_visual_style":
            value = character_visual_style or value
        if field_name == "palette_family" and "dominant_palette" in explicit:
            value = visual.get("dominant_palette", value)
        if field_name == "background_family" and "background_direction" in explicit:
            value = visual.get("background_direction", value)
        if _nonempty(value):
            strong[field_name] = str(value)

    mapped_user_fields = {name for names in _USER_HARD_FIELD_MAP.values() for name in names}
    for name in explicit:
        if name not in mapped_user_fields and _nonempty(visual.get(name)):
            strong[name] = str(visual[name])
    strong["face_aesthetic_profile"] = face_selection.face_aesthetic_profile

    explicit_hard_map = {
        "gender_presentation": "gender_presentation",
        "role_identity": "role_identity",
        "costume_identity": "costume_topology",
        "human_form_requirement": "human_form_requirement",
        "supernatural_state": "supernatural_state",
        "character_state": "character_state",
        "body_proportion": "body_proportion",
        "bust_emphasis": "bust_emphasis",
        "props": "props",
        "companion_type": "companion_type",
        "companion_count": "companion_count",
        "nonhuman_features": "nonhuman_features",
        "hair": "hair",
        "pose": "pose",
        "background": "background",
        "composition": "composition",
        "legwear": "legwear_strategy",
        "footwear": "footwear_category",
        "footwear_detail": "footwear_detail",
        "palette_primary": "palette_primary",
        "palette_secondary": "palette_secondary",
        "horns": "horn_topology",
        "tail": "tail_design",
        "wings": "wing_strategy",
        "quantity_constraints": "quantity_constraints",
    }
    for name, record in records.items():
        value = record.get("value")
        if value in (None, ""):
            continue
        target = explicit_hard_map.get(name, name)
        if name == "costume_identity" and str(value) == "maid_outfit":
            value = "maid-based"
        if name == "footwear" and str(value) == "open_toe_high_heels":
            value = "open-toe high heels"
        if name == "legwear" and str(value) == "blue_white_striped_stockings":
            value = "blue-white striped stockings"
        hard[target] = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value)
        explicit_hard.append(target)
    if "palette_primary" in records or "palette_secondary" in records:
        primary = records.get("palette_primary", {}).get("value", "white")
        secondary = records.get("palette_secondary", {}).get("value", "blue")
        hard["palette_family"] = f"{primary} dominant / {secondary} secondary"
        explicit_hard.append("palette_family")
        strong["palette_family"] = hard["palette_family"]

    soft = {
        str(name): str(value)
        for name, value in dict(soft_intent or {}).items()
        if _nonempty(value)
    }
    return VisualSpecificationContract(
        hard_constraints=hard,
        strong_preferences=strong,
        soft_intent=soft,
        anti_substitution=_visual_anti_substitution(hard, pose_specification, background_specification),
        explicit_hard_fields=tuple(dict.fromkeys(explicit_hard)),
        pose_specification=pose_specification,
        background_specification=background_specification,
        face_aesthetic_profile=face_selection.face_aesthetic_profile,
        face_aesthetic_is_default=face_selection.face_aesthetic_is_default,
        face_aesthetic_source=face_selection.face_aesthetic_source,
        face_aesthetic_guardrails=face_selection.face_aesthetic_guardrails,
        style_inheritance_policy=style_inheritance_policy or DEFAULT_STYLE_INHERITANCE_POLICY,
        face_aesthetic_contract=face_selection.to_dict(),
        explicit_constraints=records,
        explicit_constraint_locks=deepcopy(records),
    )


def _normalize_visual_specification_contract(
    value: Mapping[str, Any] | VisualSpecificationContract | None,
) -> VisualSpecificationContract | None:
    if value is None:
        return None
    if isinstance(value, VisualSpecificationContract):
        return value
    data = dict(value)
    hard = {str(k): str(v) for k, v in dict(data.get("hard_constraints") or {}).items()}
    pose_specification = {
        name: str(item)
        for name, item in dict(data.get("pose_specification") or {}).items()
        if name in POSE_SPECIFICATION_FIELDS
    }
    background_specification = {
        name: str(item)
        for name, item in dict(data.get("background_specification") or {}).items()
        if name in BACKGROUND_SPECIFICATION_FIELDS
    }
    if not pose_specification:
        pose_specification = {name: hard[name] for name in POSE_SPECIFICATION_FIELDS if name in hard}
    if not background_specification:
        background_specification = {name: hard[name] for name in BACKGROUND_SPECIFICATION_FIELDS if name in hard}
    return VisualSpecificationContract(
        hard_constraints=hard,
        strong_preferences={str(k): str(v) for k, v in dict(data.get("strong_preferences") or {}).items()},
        soft_intent={str(k): str(v) for k, v in dict(data.get("soft_intent") or {}).items()},
        anti_substitution={str(k): tuple(str(item) for item in values) for k, values in dict(data.get("anti_substitution") or {}).items()},
        explicit_hard_fields=tuple(str(item) for item in data.get("explicit_hard_fields", ())),
        priority_order=tuple(str(item) for item in data.get("priority_order", VisualSpecificationContract.priority_order)),
        schema_version=str(data.get("schema_version", "1.0.0")),
        pose_specification=pose_specification,
        background_specification=background_specification,
        face_aesthetic_profile=str(data.get("face_aesthetic_profile", DEFAULT_FACE_AESTHETIC_PROFILE)),
        face_aesthetic_is_default=bool(data.get("face_aesthetic_is_default", True)),
        face_aesthetic_source=str(data.get("face_aesthetic_source", FaceAestheticSource.MIGRATED_DEFAULT.value)),
        face_aesthetic_guardrails=tuple(str(item) for item in data.get("face_aesthetic_guardrails", DEFAULT_FACE_AESTHETIC_GUARDRAILS)),
        style_inheritance_policy=str(data.get("style_inheritance_policy", DEFAULT_STYLE_INHERITANCE_POLICY)),
        face_aesthetic_contract=deepcopy(dict(data.get("face_aesthetic_contract") or {})),
        explicit_constraints=deepcopy(dict(data.get("explicit_constraints") or {})),
        explicit_constraint_coverage=deepcopy(dict(data.get("explicit_constraint_coverage") or {})),
        explicit_constraint_locks=deepcopy(dict(data.get("explicit_constraint_locks") or {})),
        generation_allowed=bool(data.get("generation_allowed", True)),
    )


def _visual_field_label(name: str) -> str:
    return name.replace("_", " ").title()


def validate_visual_specification_contract(
    contract: VisualSpecificationContract,
    positive_prompt: str,
) -> None:
    """Reject positive prompt substitutions before the GENERATION_READY boundary."""
    text = positive_prompt.lower()
    hard = {name: value.lower() for name, value in contract.hard_constraints.items()}
    conflicts: list[str] = []

    def has(*patterns: str) -> bool:
        return any(re.search(pattern, text) for pattern in patterns)

    palette = hard.get("palette_family", "")
    if palette:
        palette_tokens = {
            "red", "crimson", "scarlet", "orange", "copper", "yellow", "gold", "green", "teal",
            "blue", "cobalt", "cyan", "violet", "purple", "pink", "magenta", "white", "ivory",
            "black", "gray", "grey", "silver", "brown", "umber", "beige", "plum",
        }
        expected_colors = set(re.findall(r"[a-z]+", palette)) & palette_tokens
        mentioned_colors = set(re.findall(r"[a-z]+", text)) & palette_tokens
        if expected_colors and mentioned_colors - expected_colors:
            conflicts.append(
                f"palette_family={palette} conflicts with unexpected palette terms: {sorted(mentioned_colors - expected_colors)}"
            )

    footwear = hard.get("footwear_category", "")
    if "barefoot" in footwear or "bare feet" in footwear:
        if has(r"\b(heels?|boots?|pumps?|stilettos?|shoes?)\b"):
            conflicts.append("footwear_category=barefoot conflicts with shoe/heel positive text")
    elif "combat boot" in footwear and has(r"stiletto|pump shoes?|generic high heels?|\bhigh heels?\b"):
        conflicts.append("footwear_category=combat boots conflicts with heel positive text")

    hair = hard.get("hair_structure", "")
    if ("bob" in hair or "short" in hair) and has(r"long flowing|waist[- ]length|very long hair"):
        conflicts.append("hair_structure short/bob conflicts with long-hair positive text")

    costume = hard.get("costume_topology", "")
    if any(token in costume for token in ("trouser", "pants")) and has(r"\bgown\b|high[- ]slit|lingerie dress|evening dress|\bskirt\b"):
        conflicts.append("costume_topology trousers/pants conflicts with dress/skirt positive text")

    wings = hard.get("wing_strategy", "")
    if any(token in wings for token in ("symbolic", "motif", "graphic")) and has(r"physical demon wings?|large physical wings?"):
        conflicts.append("wing_strategy=symbolic motif conflicts with physical-wing positive text")

    background = hard.get("background_family", "")
    architecture_presence = contract.background_specification.get("architecture_presence", "").lower()
    if architecture_presence == "none" and has(r"\bcastle\b|\bcathedral\b|\bpalace\b|tower(?:ing| complex)?|throne room"):
        conflicts.append("architecture_presence=none conflicts with literal architecture positive text")
    elif any(token in background for token in ("abstract", "temporal", "haze", "gradient")) and has(r"\bcastle\b|\bcathedral\b|throne room|\bpalace\b"):
        conflicts.append("background_family=abstract/temporal conflicts with literal-location positive text")

    legwear = hard.get("legwear_strategy", "")
    if legwear in {"none", "bare legs", "bare-leg exposure"} and has(r"stockings?|tights?|pantyhose"):
        conflicts.append("legwear_strategy=none/bare legs conflicts with legwear positive text")

    pose = hard.get("pose_family", "")
    if "low-energy" in pose and has(r"high[- ]energy|dynamic action pose"):
        conflicts.append("pose_family=low-energy conflicts with high-energy positive text")
    if "open" in pose and has(r"crossed legs?|legs crossed"):
        conflicts.append("pose_family=open stance conflicts with crossed-leg positive text")

    pose_spec = {name: value.lower() for name, value in contract.pose_specification.items()}
    if "away from face" in " ".join(pose_spec.values()) and has(
        r"touching (?:the )?cheek|finger(?:s)? near (?:the )?lips?|hand (?:beside|near) (?:the )?face"
    ):
        conflicts.append("pose hand-away specification conflicts with face-adjacent positive text")
    if "open palm outward" in pose_spec.get("right_hand_gesture", "") and has(
        r"right hand (?:touching|near|beside) (?:the )?(?:face|cheek)|right hand near lips"
    ):
        conflicts.append("right_hand_gesture=open palm outward conflicts with right-hand face gesture")

    exposure = hard.get("exposure_strategy", "")
    if any(token in exposure for token in ("exposure", "exposed", "bare")) and has(r"fully covered|no skin visible"):
        conflicts.append("exposure_strategy requires exposure but positive text says fully covered")
    if "fully covered" in exposure and has(r"bare skin|skin exposure|exposed skin"):
        conflicts.append("exposure_strategy=fully covered conflicts with exposed-skin positive text")

    if conflicts:
        raise PromptConstraintConflict(conflicts)


@dataclass(frozen=True)
class RegionalStyleSelection:
    regional_visual_language: str
    regional_visual_language_source: str
    regional_style_override_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _language(value: str | RegionalVisualLanguage) -> str:
    value = value.value if isinstance(value, RegionalVisualLanguage) else str(value)
    allowed = {item.value for item in RegionalVisualLanguage}
    if value not in allowed:
        raise RegionalStyleError(f"unsupported regional visual language: {value}")
    return value


def resolve_regional_visual_language(
    requested: str | RegionalVisualLanguage | None = None,
    *,
    explicit_user_override: bool = False,
    migrated_default: bool = False,
    override_reason: str | None = None,
    source: str | RegionalVisualLanguageSource | None = None,
) -> RegionalStyleSelection:
    """Resolve the default or an explicit user override without inferring one."""
    source_value = source.value if isinstance(source, RegionalVisualLanguageSource) else source
    explicit_sources = {
        RegionalVisualLanguageSource.EXPLICIT_USER_SELECTION.value,
        RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value,
        RegionalVisualLanguageSource.BENCHMARK_DELEGATION.value,
    }
    if source_value is not None and source_value not in {
        RegionalVisualLanguageSource.DEFAULT_STYLE_POLICY.value,
        *explicit_sources,
        RegionalVisualLanguageSource.MIGRATED_DEFAULT.value,
    }:
        raise RegionalStyleError(f"unsupported regional visual language source: {source_value}")
    if explicit_user_override:
        if source_value not in (None, RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value):
            raise RegionalStyleError("explicit_user_override conflicts with regional style source")
        source_value = RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value
    if migrated_default:
        if source_value not in (None, RegionalVisualLanguageSource.MIGRATED_DEFAULT.value):
            raise RegionalStyleError("migrated_default conflicts with regional style source")
        source_value = RegionalVisualLanguageSource.MIGRATED_DEFAULT.value
    if source_value == RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value and not override_reason:
        raise RegionalStyleError("regional style override requires a reason")
    if requested is None:
        return RegionalStyleSelection(
            DEFAULT_REGIONAL_VISUAL_LANGUAGE,
            source_value
            if source_value is not None
            else RegionalVisualLanguageSource.DEFAULT_STYLE_POLICY.value,
        )
    selected = _language(requested)
    if source_value is None:
        source_value = (
            RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value
            if explicit_user_override
            else RegionalVisualLanguageSource.DEFAULT_STYLE_POLICY.value
        )
    if source_value == RegionalVisualLanguageSource.DEFAULT_STYLE_POLICY.value and selected != DEFAULT_REGIONAL_VISUAL_LANGUAGE:
        raise RegionalStyleError("a non-default regional visual language requires an explicit user override")
    return RegionalStyleSelection(
        selected,
        source_value,
        override_reason if source_value == RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value else None,
    )


def migrate_regional_style_fields(
    artifact: Mapping[str, Any],
    *,
    policy_default: str = DEFAULT_REGIONAL_VISUAL_LANGUAGE,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Copy an old artifact and add regional fields; never mutate the old artifact."""
    migrated = deepcopy(dict(artifact))
    missing = "regional_visual_language" not in migrated
    missing_source = "regional_visual_language_source" not in migrated
    if not missing and not missing_source:
        return migrated, None
    selected = _language(migrated.get("regional_visual_language", policy_default))
    migrated["regional_visual_language"] = selected
    migrated["regional_visual_language_source"] = RegionalVisualLanguageSource.MIGRATED_DEFAULT.value
    event = {
        "event": "regional_visual_language_migration",
        "audit_event": "REGIONAL_VISUAL_LANGUAGE_DEFAULT_MIGRATION",
        "from": "missing_regional_visual_language_fields",
        "old_artifact_version": migrated.get("schema_version", "unknown"),
        "to": selected,
        "new_effective_value": selected,
        "source": RegionalVisualLanguageSource.MIGRATED_DEFAULT.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_explicit_override_later": False,
    }
    return migrated, event


@dataclass(frozen=True)
class FaceAestheticSelection:
    face_aesthetic_profile: str
    face_aesthetic_is_default: bool
    face_aesthetic_source: str
    face_aesthetic_guardrails: tuple[str, ...]
    style_inheritance_policy: str = DEFAULT_STYLE_INHERITANCE_POLICY
    default_face_region_language: str = ""
    facial_structure_bias: str = ""
    facial_style_guardrail: str = ""
    regional_face_language: str = ""
    facial_style_drift: str = "NONE"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_face_aesthetic_profile(
    requested: str | FaceAestheticProfile | None = None,
    *,
    source: str | FaceAestheticSource | None = None,
    explicit_user_selection: bool = False,
    migrated_default: bool = False,
    style_inheritance_policy: str | None = None,
) -> FaceAestheticSelection:
    source_value = source.value if isinstance(source, FaceAestheticSource) else source
    if explicit_user_selection:
        source_value = FaceAestheticSource.HUMAN_EXPLICIT.value
    if migrated_default:
        source_value = FaceAestheticSource.MIGRATED_DEFAULT.value
    allowed_sources = {item.value for item in FaceAestheticSource}
    if source_value is not None and source_value not in allowed_sources:
        raise RegionalStyleError(f"unsupported face aesthetic source: {source_value}")
    profile = (
        requested.value if isinstance(requested, FaceAestheticProfile) else str(requested)
        if requested is not None
        else DEFAULT_FACE_AESTHETIC_PROFILE
    )
    if profile not in FACE_AESTHETIC_CONTRACTS:
        raise RegionalStyleError(f"unsupported face aesthetic profile: {profile}")
    if source_value is None:
        source_value = (
            FaceAestheticSource.SYSTEM_DEFAULT.value
            if profile == DEFAULT_FACE_AESTHETIC_PROFILE
            else FaceAestheticSource.DELEGATED_RESOLUTION.value
        )
    if profile != DEFAULT_FACE_AESTHETIC_PROFILE and source_value not in {
        FaceAestheticSource.HUMAN_EXPLICIT.value,
        FaceAestheticSource.DELEGATED_RESOLUTION.value,
    }:
        raise RegionalStyleError("non-default face aesthetic profile requires explicit or delegated resolution")
    contract = FACE_AESTHETIC_CONTRACTS[profile]
    return FaceAestheticSelection(
        profile,
        profile == DEFAULT_FACE_AESTHETIC_PROFILE and source_value in {
            FaceAestheticSource.SYSTEM_DEFAULT.value,
            FaceAestheticSource.MIGRATED_DEFAULT.value,
        },
        source_value,
        tuple(contract["guardrails"]),
        style_inheritance_policy or DEFAULT_STYLE_INHERITANCE_POLICY,
        str(contract["default_face_region_language"]),
        str(contract["facial_structure_bias"]),
        str(contract["facial_style_guardrail"]),
        str(contract["regional_face_language"]),
        str(contract["facial_style_drift"]),
    )


def migrate_face_aesthetic_fields(
    artifact: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Add the current face contract in memory without rewriting old artifacts."""
    migrated = deepcopy(dict(artifact))
    has_profile = "face_aesthetic_profile" in migrated
    has_contract = isinstance(migrated.get("face_aesthetic_contract"), Mapping)
    if has_profile and has_contract:
        return migrated, None
    existing_profile = migrated.get("face_aesthetic_profile")
    selection = resolve_face_aesthetic_profile(
        existing_profile,
        source=migrated.get("face_aesthetic_source") or (
            FaceAestheticSource.DELEGATED_RESOLUTION.value
            if existing_profile and existing_profile != DEFAULT_FACE_AESTHETIC_PROFILE
            else None
        ),
        migrated_default=not existing_profile,
    )
    migrated.update(selection.to_dict())
    migrated["face_aesthetic_contract"] = selection.to_dict()
    event = {
        "event": "face_aesthetic_migration",
        "audit_event": "FACE_AESTHETIC_DEFAULT_MIGRATION",
        "old_artifact_version": migrated.get("schema_version", "unknown"),
        "new_effective_value": selection.face_aesthetic_profile,
        "source": selection.face_aesthetic_source,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return migrated, event


def load_style_policy(path: str | Path) -> dict[str, Any]:
    """Load the YAML policy at the host boundary; the runtime default stays dependency-free."""
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - only used on hosts without YAML support
        raise RegionalStyleError("loading YAML style policy requires the host YAML parser") from error
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("regional_visual_language"), dict):
        raise RegionalStyleError("style policy is missing regional_visual_language")
    regional = data["regional_visual_language"]
    policy = deepcopy(DEFAULT_REGIONAL_STYLE_POLICY)
    policy["default"] = regional.get("default", policy["default"])
    policy["allow_user_override"] = bool(regional.get("allow_user_override", True))
    contract = regional.get("contract")
    if isinstance(contract, dict):
        policy["contracts"][policy["default"]] = {
            "positive": tuple(contract.get("positive", ())),
            "negative": tuple(contract.get("negative", ())),
        }
    if isinstance(regional.get("critic_thresholds"), dict):
        policy["critic_thresholds"].update(regional["critic_thresholds"])
    if isinstance(regional.get("drift_types"), list):
        policy["negative_drift_types"] = list(regional["drift_types"])
    if isinstance(data.get("lower_body_visual_language"), dict):
        policy["lower_body"].update(data["lower_body_visual_language"])
    if isinstance(data.get("pose_constraints"), dict):
        policy["pose_constraints"].update(data["pose_constraints"])
    face_policy = data.get("face_aesthetic")
    if isinstance(face_policy, dict):
        policy["face_aesthetic"].update(
            {key: value for key, value in face_policy.items() if key != "contracts"}
        )
        if isinstance(face_policy.get("contracts"), dict):
            policy["face_aesthetic"]["contracts"].update(deepcopy(face_policy["contracts"]))
    return policy


_MINOR_AGE_GROUPS = {"minor", "juvenile", "clearly_juvenile"}
_SEXUALIZED_LEG_ACCESSORIES = {"thigh ring", "leg strap", "garter-like decorative band"}


def validate_lower_body_design(
    lower_body: Mapping[str, Any],
    *,
    age_group: str = "adult",
) -> dict[str, Any]:
    """Validate explicit lower-body choices while keeping the vocabulary open-ended."""
    if not isinstance(lower_body, Mapping):
        raise RegionalStyleError("lower_body must be an object")
    required = (
        "exposure_strategy",
        "legwear_family",
        "leg_accessory_family",
        "footwear_family",
        "foot_visibility",
        "visual_reason",
    )
    missing = [name for name in required if not str(lower_body.get(name, "")).strip()]
    if missing:
        raise RegionalStyleError(f"lower_body is missing: {', '.join(missing)}")
    normalized = {name: lower_body.get(name) for name in LOWER_BODY_VISUAL_VARIABLES}
    normalized["age_group"] = age_group
    if str(age_group).lower() in _MINOR_AGE_GROUPS:
        accessory = str(normalized["leg_accessory_family"]).strip().lower()
        reason = str(normalized["visual_reason"]).lower()
        if accessory in _SEXUALIZED_LEG_ACCESSORIES or any(token in reason for token in ("fetish", "erotic", "sexualized")):
            raise RegionalStyleError("minor characters cannot receive sexualized lower-body framing or accessories")
    return normalized


def _lower_body_prompt_lines(lower_body: Mapping[str, Any]) -> tuple[str, ...]:
    labels = {
        "exposure_strategy": "Skin Exposure Strategy",
        "legwear_family": "Legwear Family",
        "leg_accessory_family": "Leg Accessory Family",
        "footwear_family": "Footwear Family",
        "foot_visibility": "Foot Visibility",
        "visual_reason": "Visual Reason",
        "relationship_to_character_style": "Relationship to Character Visual Style",
        "relationship_to_pose": "Relationship to Pose",
        "repetition_risk": "Repetition Risk",
    }
    return tuple(
        f"{labels[name]}: {lower_body[name]}"
        for name in LOWER_BODY_VISUAL_VARIABLES
        if lower_body.get(name) not in (None, "")
    )


@dataclass(frozen=True)
class LowerBodyDesignReview:
    age_group: str
    exposure_strategy: Any
    legwear_family: Any
    leg_accessory_family: Any
    footwear_family: Any
    foot_visibility: Any
    visual_reason: str
    relationship_to_character_style: Any
    relationship_to_pose: Any
    repetition_risk: Any
    genericness_risk: str
    result: str
    fanservice_is_independent: bool = True
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def review_lower_body_design(
    lower_body: Mapping[str, Any],
    *,
    age_group: str = "adult",
    fanservice_level: str | None = None,
) -> LowerBodyDesignReview:
    """Review lower-body design; fanservice is intentionally not used as coverage logic."""
    normalized = validate_lower_body_design(lower_body, age_group=age_group)
    footwear = str(normalized["footwear_family"]).lower()
    legwear = str(normalized["legwear_family"]).lower()
    outfit_family = str(
        lower_body.get("outfit_family", lower_body.get("lower_body_structure", lower_body.get("outfit_direction", "")))
    ).lower()
    reason = str(normalized["visual_reason"]).lower()
    generic_pair = any(token in outfit_family for token in ("trouser", "pants", "generic")) and "boot" in footwear
    generic_pair = generic_pair or ("skirt" in outfit_family and "boot" in footwear)
    genericness_risk = "HIGH" if generic_pair and reason in {"", "default", "standard", "because it is safe"} else "LOW"
    issues = ("generic pants/boots pair lacks a character-specific reason",) if genericness_risk == "HIGH" else ()
    return LowerBodyDesignReview(
        normalized["age_group"],
        normalized["exposure_strategy"],
        normalized["legwear_family"],
        normalized["leg_accessory_family"],
        normalized["footwear_family"],
        normalized["foot_visibility"],
        str(normalized["visual_reason"]),
        normalized["relationship_to_character_style"],
        normalized["relationship_to_pose"],
        normalized["repetition_risk"],
        genericness_risk,
        "PASS_WITH_NOTE" if issues else "PASS",
        fanservice_is_independent=True,
        issues=issues,
    )


@dataclass(frozen=True)
class LowerBodyGroundingReview:
    actual_image: str
    result: str
    issues: tuple[str, ...]
    detected_drift_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _feature_text(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(str(item) for item in value.values())
    return str(value)


def _feature_matches(expected: Any, actual: Any) -> bool:
    if expected in (None, ""):
        return True
    if actual in (None, ""):
        return False
    expected_text = _feature_text(expected).strip().lower()
    actual_text = _feature_text(actual).strip().lower()
    return expected_text == actual_text or expected_text in actual_text


def check_lower_body_grounding(
    actual_image: str | Path,
    *,
    final_design: Mapping[str, Any],
    actual_features: Mapping[str, Any],
) -> LowerBodyGroundingReview:
    """Compare locked lower-body intent with actual-image labels."""
    image = Path(actual_image)
    if not image.is_file():
        raise RegionalStyleError("lower-body grounding requires an existing actual image")
    expected = final_design.get("lower_body", final_design.get("lower_body_visual_variables", final_design))
    issues: list[str] = []
    drifts: list[str] = []
    if not _feature_matches(expected.get("footwear_family"), actual_features.get("footwear_family")):
        issues.append("footwear family does not match the Final Design")
        drifts.append(DriftType.FOOTWEAR_GROUNDING_FAIL.value)
    if not _feature_matches(expected.get("legwear_family"), actual_features.get("legwear_family")):
        issues.append("legwear family does not match the Final Design")
        drifts.append(DriftType.LEGWEAR_GROUNDING_FAIL.value)
    expected_accessory = expected.get("leg_accessory_family")
    actual_accessory = actual_features.get("leg_accessory_family")
    if expected_accessory not in (None, "", "none", "NONE") and not _feature_matches(expected_accessory, actual_accessory):
        issues.append("leg accessory anchor is missing from the actual image")
        drifts.append(DriftType.LOWER_BODY_ANCHOR_MISS.value)
    return LowerBodyGroundingReview(str(image), "PASS" if not issues else "FAIL", tuple(issues), tuple(drifts))


@dataclass(frozen=True)
class PromptBundle:
    rendering_foundation: str
    regional_visual_language: str
    regional_visual_language_source: str
    character_visual_style: str
    positive_constraints: tuple[str, ...]
    negative_constraints: tuple[str, ...]
    lower_body_variables: dict[str, Any]
    lower_body_constraints: tuple[str, ...]
    prompt: str
    pose_description: str = "stable standard standee stance"
    pose_family: str = "OPEN_PARALLEL_STANCE"
    leg_crossing_risk: str = "LOW"
    leg_separation_contract: dict[str, bool] = field(
        default_factory=lambda: DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
    )
    leg_geometry_constraints: tuple[str, ...] = LEG_GEOMETRY_POSITIVE
    pose_intent: str = "STABLE_OPEN"
    pose_intent_contract: dict[str, Any] = field(default_factory=dict)
    inherit_previous_visuals: bool = False
    allowed_visual_inheritance: tuple[str, ...] = ()
    blocked_context_sources: tuple[str, ...] = ()
    visual_context_firewall_applied: bool = True
    visual_specification_contract: dict[str, Any] = field(default_factory=dict)
    prompt_adherence_manifest: dict[str, Any] = field(default_factory=dict)
    face_aesthetic_profile: str = DEFAULT_FACE_AESTHETIC_PROFILE
    face_aesthetic_is_default: bool = True
    face_aesthetic_source: str = DEFAULT_FACE_AESTHETIC_SOURCE
    face_aesthetic_guardrails: tuple[str, ...] = DEFAULT_FACE_AESTHETIC_GUARDRAILS
    style_inheritance_policy: str = DEFAULT_STYLE_INHERITANCE_POLICY
    explicit_constraints: dict[str, dict[str, Any]] = field(default_factory=dict)
    explicit_constraint_coverage: dict[str, dict[str, Any]] = field(default_factory=dict)
    explicit_constraint_locks: dict[str, Any] = field(default_factory=dict)
    generation_allowed: bool = True
    game_style_id: str | None = None
    game_style_profile_version: str | None = None
    game_style_projection_version: str | None = None
    game_style_instructions: tuple[str, ...] = ()
    game_style_source_claim_ids: tuple[str, ...] = ()
    game_style_debug_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for name in (
            "positive_constraints",
            "negative_constraints",
            "lower_body_constraints",
            "leg_geometry_constraints",
            "face_aesthetic_guardrails",
            "game_style_instructions",
            "game_style_source_claim_ids",
        ):
            data[name] = list(data[name])
        pose_contract = data.get("pose_intent_contract")
        if isinstance(pose_contract, dict):
            for name in ("required_body_signals", "forbidden_shortcuts"):
                if name in pose_contract:
                    pose_contract[name] = list(pose_contract[name])
        return data


class PromptCompiler:
    """Compile global, regional, character, and optional rendering deltas."""

    def __init__(self, policy: Mapping[str, Any] | None = None) -> None:
        self.policy = policy or DEFAULT_REGIONAL_STYLE_POLICY

    def compile(
        self,
        *,
        character_visual_style: str,
        character_identity: str = "",
        regional_visual_language: str | RegionalVisualLanguage | None = None,
        regional_visual_language_source: str | None = None,
        regional_style_override_reason: str | None = None,
        rendering_foundation: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME",
        lower_body: Mapping[str, Any] | None = None,
        age_group: str = "adult",
        fanservice_level: str | None = None,
        pose_description: str | None = None,
        pose_family: str | None = None,
        pose_intent: str | None = None,
        pose_intent_contract: Mapping[str, Any] | PoseIntentContract | None = None,
        prohibited_constraints: Sequence[Mapping[str, Any]] | None = None,
        explicit_negative_constraints: Mapping[str, Any] | None = None,
        visual_context_firewall: Mapping[str, Any] | VisualContextFirewall | None = None,
        visual_specification_contract: Mapping[str, Any] | VisualSpecificationContract | None = None,
        positive_prompt_fragment: str | None = None,
        face_aesthetic_profile: str | FaceAestheticProfile | None = None,
        face_aesthetic_source: str | FaceAestheticSource | None = None,
        style_inheritance_policy: str | None = None,
        explicit_constraints: Mapping[str, Any] | None = None,
        game_style_fragment: StyleInstructionFragment | Mapping[str, Any] | None = None,
    ) -> PromptBundle:
        firewall = VisualContextFirewall.from_metadata(visual_context_firewall)
        if not firewall.visual_context_firewall_applied:
            raise RegionalStyleError("Visual Context Firewall must be applied before prompt compilation")
        source_value = regional_visual_language_source
        explicit = source_value == RegionalVisualLanguageSource.EXPLICIT_USER_OVERRIDE.value
        selection = resolve_regional_visual_language(
            regional_visual_language,
            explicit_user_override=explicit,
            override_reason=regional_style_override_reason,
            source=source_value,
        )
        if regional_visual_language_source and regional_visual_language_source != selection.regional_visual_language_source:
            raise RegionalStyleError("regional style source does not match the resolved selection")
        contract = self.policy.get("contracts", {}).get(selection.regional_visual_language)
        if contract is None:
            raise RegionalStyleError(f"style policy has no contract for {selection.regional_visual_language}")
        positive = tuple(contract.get("positive", ()))
        negative = tuple(contract.get("negative", ()))
        safe_style = rewrite_conflicting_pose_language(character_visual_style)
        pose_text = pose_description or "stable standard standee stance"
        try:
            resolved_pose_family = validate_pose_description(pose_text, pose_family)
        except LegSeparationError as error:
            raise RegionalStyleError(str(error)) from error
        pose_spec = POSE_FAMILIES[resolved_pose_family]
        requested_pose_intent = resolve_pose_intent(pose_intent, pose_text)
        intent_contract = (
            pose_intent_contract
            if isinstance(pose_intent_contract, PoseIntentContract)
            else build_pose_intent_contract(
                requested_pose_intent,
                resolved_pose_family=resolved_pose_family,
            )
            if pose_intent_contract is None
            else normalize_pose_intent_contract(pose_intent_contract)
        )
        if intent_contract.resolved_pose_family and intent_contract.resolved_pose_family != resolved_pose_family:
            raise RegionalStyleError("pose intent contract family does not match the resolved pose family")
        if not intent_contract.resolved_pose_family:
            intent_contract = build_pose_intent_contract(
                intent_contract.requested_intent,
                resolved_pose_family=resolved_pose_family,
                custom_body_signals=intent_contract.required_body_signals,
            ) if intent_contract.requested_intent == "CUSTOM" else build_pose_intent_contract(
                intent_contract.requested_intent,
                resolved_pose_family=resolved_pose_family,
            )
        leg_positive = leg_geometry_constraints(resolved_pose_family)
        leg_negative = tuple(LEG_GEOMETRY_NEGATIVE)
        normalize_contract = DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
        lower_body_variables: dict[str, Any] = {}
        lower_body_constraints: tuple[str, ...] = ()
        if lower_body is not None:
            lower_body_variables = validate_lower_body_design(lower_body, age_group=age_group)
            review_lower_body_design(lower_body, age_group=age_group, fanservice_level=fanservice_level)
            lower_body_constraints = _lower_body_prompt_lines(lower_body_variables)
        visual_contract = _normalize_visual_specification_contract(visual_specification_contract)
        game_fragment = game_style_fragment.to_dict() if isinstance(game_style_fragment, StyleInstructionFragment) else dict(game_style_fragment or {})
        game_instructions = tuple(str(item) for item in game_fragment.get("instructions", ()))
        game_claim_ids = tuple(str(item) for item in game_fragment.get("source_claim_ids", ()))
        face_selection = resolve_face_aesthetic_profile(
            visual_contract.face_aesthetic_profile if visual_contract is not None else face_aesthetic_profile,
            source=(visual_contract.face_aesthetic_source if visual_contract is not None else face_aesthetic_source),
            style_inheritance_policy=(visual_contract.style_inheritance_policy if visual_contract is not None else style_inheritance_policy),
        )
        prompt_lines = [
            "## GLOBAL RENDERING MEDIUM",
            "## Rendering Foundation",
            rendering_foundation,
            "",
            "## REGIONAL VISUAL LANGUAGE",
            "## Regional Visual Language",
            selection.regional_visual_language,
            *positive,
            "",
            "## FACE AESTHETIC CONTRACT",
            f"Face Aesthetic Profile: {face_selection.face_aesthetic_profile}",
            f"Default Face Region Language: {face_selection.default_face_region_language}",
            f"Facial Structure Bias: {face_selection.facial_structure_bias}",
            f"Facial Style Guardrail: {face_selection.facial_style_guardrail}",
            f"Style Inheritance Policy: {face_selection.style_inheritance_policy}",
            "",
            "## CHARACTER VISUAL STYLE",
            "## Character Visual Style",
            safe_style,
        ]
        if character_identity:
            prompt_lines.extend(("", "## CHARACTER IDENTITY", character_identity))
        if explicit_constraints:
            prompt_lines.extend(("", "## USER EXPLICIT HARD REQUIREMENTS"))
            for name, record in explicit_constraints.items():
                record = record if isinstance(record, Mapping) else {"value": record}
                value = record.get("value")
                if isinstance(value, list):
                    value = ", ".join(str(item) for item in value)
                if name == "quantity_constraints" and isinstance(record.get("value"), Mapping):
                    value = ", ".join(
                        f"exactly {count} {str(item).replace('_', ' ')}"
                        for item, count in record["value"].items()
                    )
                prompt_lines.extend(
                    (
                        f"{_visual_field_label(name)}: {value}",
                        f"Source: {record.get('source', 'human_explicit')}",
                        f"Priority: {record.get('priority', 'HARD')}",
                        f"Evidence: {record.get('raw_evidence', '')}",
                    )
                )
        if game_instructions:
            prompt_lines.extend(
                (
                    "",
                    "## OPTIONAL GAME RENDERING STYLE",
                    f"Game Rendering Style: {game_fragment.get('game_style_id', '')}",
                    "These are rendering-language deltas only; preserve all character content and explicit user choices.",
                    *game_instructions,
                )
            )
        if visual_contract is not None:
            if visual_contract.hard_constraints:
                prompt_lines.extend(("", "## HARD DESIGN SPECIFICATION"))
                prompt_lines.extend(
                    f"{_visual_field_label(name)}: {value}"
                    for name, value in visual_contract.hard_constraints.items()
                    if name not in (*POSE_SPECIFICATION_FIELDS, *BACKGROUND_SPECIFICATION_FIELDS)
                )
            if visual_contract.strong_preferences:
                prompt_lines.extend(("", "## STRONG VISUAL DIRECTION"))
                prompt_lines.extend(
                    f"{_visual_field_label(name)}: {value}"
                    for name, value in visual_contract.strong_preferences.items()
                )
            if visual_contract.soft_intent:
                prompt_lines.extend(("", "## SOFT CHARACTER INTENT"))
                prompt_lines.extend(
                    f"{_visual_field_label(name)}: {value}"
                    for name, value in visual_contract.soft_intent.items()
                )
            if visual_contract.pose_specification:
                pose_labels = {
                    "lower_body_pose": "Lower Body",
                    "weight_distribution": "Weight",
                    "torso_orientation": "Torso",
                    "shoulder_line": "Shoulder Line",
                    "arm_configuration": "Arm Configuration",
                    "left_arm_action": "Left Arm",
                    "right_arm_action": "Right Arm",
                    "left_hand_gesture": "Left Hand",
                    "right_hand_gesture": "Right Hand",
                    "head_attitude": "Head",
                    "gaze_direction": "Gaze",
                    "gesture_energy": "Gesture Energy",
                }
                prompt_lines.extend(
                    (
                        "",
                        "## POSE SPECIFICATION",
                    *(
                        f"{pose_labels[name]}: {value}"
                        for name, value in visual_contract.pose_specification.items()
                        if name in pose_labels
                    ),
                    )
                )
            if visual_contract.background_specification:
                background_labels = {
                    "environment_type": "Environment",
                    "architecture_presence": "Architecture Presence",
                    "architecture_language": "Architecture Language",
                    "spatial_structure": "Spatial Structure",
                    "atmosphere": "Atmosphere",
                    "lighting_context": "Lighting Context",
                    "ground_plane": "Ground Plane",
                    "depth_structure": "Depth Structure",
                    "background_complexity": "Complexity",
                    "dominant_shape_language": "Dominant Shape Language",
                }
                prompt_lines.extend(
                    (
                        "",
                        "## BACKGROUND SPECIFICATION",
                    *(
                        f"{background_labels[name]}: {value}"
                        for name, value in visual_contract.background_specification.items()
                        if name in background_labels
                    ),
                    )
                )
            if positive_prompt_fragment:
                prompt_lines.extend(("", "## ADDITIONAL POSITIVE VISUAL SPECIFICATION", positive_prompt_fragment))
        prompt_lines.extend(
            (
                "",
                "## POSE",
                f"Pose Family: {resolved_pose_family}",
                f"Leg Crossing Risk: {pose_spec.leg_crossing_risk}",
                f"Pose: {rewrite_conflicting_pose_language(pose_text)} with both legs clearly separated and no leg crossover",
            )
        )
        prompt_lines.extend(("", *pose_intent_prompt_lines(intent_contract)))
        prompt_lines.extend(
            (
                "",
                "## LEG GEOMETRY / ANATOMY CONSTRAINT",
                "## POSITIVE LEG GEOMETRY",
                *leg_positive,
                "",
                "## NEGATIVE LEG GEOMETRY — HARD INVARIANT",
                *leg_negative,
            )
        )
        if prohibited_constraints:
            prompt_lines.extend(
                (
                    "",
                    "## EXPLICIT PROHIBITED CONSTRAINTS",
                    *(
                        f"Avoid {item.get('text')}; preserve scope={item.get('scope', 'independent')} ({item.get('kind', 'concept')})."
                        for item in prohibited_constraints
                    ),
                )
            )
        if lower_body_constraints:
            prompt_lines.extend(("", "## Lower-Body Design", *lower_body_constraints))
        positive_prompt = "\n".join(
            line
            for line in prompt_lines
            if not line.startswith("Avoid ")
            and line not in leg_negative
            and line != "## NEGATIVE LEG GEOMETRY — HARD INVARIANT"
        )
        if visual_contract is not None and visual_contract.anti_substitution:
            prompt_lines.extend(("", "## NEGATIVE / DO-NOT-SUBSTITUTE"))
            prompt_lines.extend(
                f"{_visual_field_label(name)}: {', '.join(values)}"
                for name, values in visual_contract.anti_substitution.items()
            )
        if explicit_negative_constraints:
            prompt_lines.extend(
                (
                    "",
                    "## EXPLICIT USER NEGATIVE CONSTRAINTS",
                    *(f"{name}: {value}" for name, value in explicit_negative_constraints.items()),
                )
            )
        prompt_lines.extend(("", "## Negative Constraints", *negative, *leg_negative))
        compiled_prompt = "\n".join(prompt_lines)
        if visual_contract is not None:
            validate_visual_specification_contract(visual_contract, positive_prompt)
        if not audit_leg_prompt(compiled_prompt)["passed"]:
            raise RegionalStyleError("Prompt Audit failed: hard leg geometry is incomplete or conflicting")
        if not audit_pose_intent_prompt(compiled_prompt, intent_contract.requested_intent)["passed"]:
            raise RegionalStyleError("Prompt Audit failed: pose intent section is incomplete")
        return PromptBundle(
            rendering_foundation,
            selection.regional_visual_language,
            selection.regional_visual_language_source,
            safe_style,
            positive,
            negative + leg_negative,
            lower_body_variables,
            lower_body_constraints,
            compiled_prompt,
            pose_text,
            resolved_pose_family,
            pose_spec.leg_crossing_risk,
            normalize_contract,
            leg_positive,
            intent_contract.requested_intent,
            intent_contract.to_dict(),
            firewall.inherit_previous_visuals,
            firewall.allowed_visual_inheritance,
            firewall.blocked_context_sources,
            firewall.visual_context_firewall_applied,
            visual_contract.to_dict() if visual_contract is not None else {},
            visual_contract.to_dict() if visual_contract is not None else {},
            face_aesthetic_profile=face_selection.face_aesthetic_profile,
            face_aesthetic_is_default=face_selection.face_aesthetic_is_default,
            face_aesthetic_source=face_selection.face_aesthetic_source,
            face_aesthetic_guardrails=face_selection.face_aesthetic_guardrails,
            style_inheritance_policy=face_selection.style_inheritance_policy,
            explicit_constraints={
                str(name): dict(record) if isinstance(record, Mapping) else {"value": record}
                for name, record in dict(explicit_constraints or {}).items()
            },
            explicit_constraint_locks=deepcopy(dict(explicit_constraints or {})),
            game_style_id=game_fragment.get("game_style_id"),
            game_style_profile_version=game_fragment.get("profile_version"),
            game_style_projection_version=game_fragment.get("projection_version"),
            game_style_instructions=game_instructions,
            game_style_source_claim_ids=game_claim_ids,
            game_style_debug_trace={
                "global_contract": rendering_foundation,
                "game_specialization": game_fragment.get("game_style_id"),
                "projected_rules": list(game_instructions),
                "profile_version": game_fragment.get("profile_version"),
                "projection_version": game_fragment.get("projection_version"),
                "source_claim_ids": list(game_claim_ids),
            },
        )


def _score(value: Any, name: str) -> int:
    if type(value) is not int or not 1 <= value <= 10:
        raise RegionalStyleError(f"{name} must be an integer from 1 to 10")
    return value


@dataclass(frozen=True)
class RegionalStyleReview:
    actual_image: str
    target_regional_visual_language: str
    regional_visual_language_match: str
    east_asian_gacha_read: int
    western_anime_drift: str
    western_concept_art_drift: str
    facial_abstraction_match: int
    body_rendering_match: int
    costume_language_match: int
    presentation_match: int
    confidence: float
    result: str
    evidence_source: str = "human_actual_image_review"
    maturity_read: int | None = None
    expected_regional_visual_language: str | None = None
    perceived_regional_visual_language: str | None = None
    outfit_language_match: int | None = None
    material_language_match: int | None = None
    pseudo_oriental_default_detected: bool = False
    detected_drift_types: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class RegionalStyleCritic:
    """Evaluate an existing image from labeled observations, never from prompt text."""

    def __init__(self, policy: Mapping[str, Any] | None = None) -> None:
        self.policy = policy or DEFAULT_REGIONAL_STYLE_POLICY

    def review(
        self,
        actual_image: str | Path,
        *,
        observations: Mapping[str, Any],
        target_regional_visual_language: str = DEFAULT_REGIONAL_VISUAL_LANGUAGE,
    ) -> RegionalStyleReview:
        image = Path(actual_image)
        if not image.is_file():
            raise RegionalStyleError("RegionalStyleCritic requires an existing actual image")
        target = _language(target_regional_visual_language)
        required = (
            "east_asian_gacha_read",
            "western_anime_drift",
            "western_concept_art_drift",
            "facial_abstraction_match",
            "body_rendering_match",
            "costume_language_match",
            "presentation_match",
            "confidence",
        )
        missing = [name for name in required if name not in observations]
        if missing:
            raise RegionalStyleError(f"actual-image observations missing: {', '.join(missing)}")
        read = _score(observations["east_asian_gacha_read"], "east_asian_gacha_read")
        scores = [
            _score(observations[name], name)
            for name in ("facial_abstraction_match", "body_rendering_match", "costume_language_match", "presentation_match")
        ]
        drift_values = {
            name: str(observations[name]).upper()
            for name in ("western_anime_drift", "western_concept_art_drift")
        }
        if any(value not in DRIFT_LEVELS for value in drift_values.values()):
            raise RegionalStyleError("drift values must be NONE, LOW, MEDIUM, or HIGH")
        confidence = observations["confidence"]
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise RegionalStyleError("confidence must be between 0 and 1")
        thresholds = self.policy.get("critic_thresholds", {})
        fail_read = int(thresholds.get("fail_read_below", 4))
        acceptable_read = int(thresholds.get("acceptable_read_at_least", 6))
        strong_read = int(thresholds.get("strong_read_at_least", 8))
        min_confidence = float(thresholds.get("minimum_confidence", 0.5))
        superhero_drift = str(observations.get("western_superhero_anatomy_drift", "NONE")).upper()
        if superhero_drift not in DRIFT_LEVELS:
            raise RegionalStyleError("western_superhero_anatomy_drift must be NONE, LOW, MEDIUM, or HIGH")
        maturity_read = observations.get("maturity_read")
        if maturity_read is not None:
            maturity_read = _score(maturity_read, "maturity_read")
        maturity_required = bool(observations.get("maturity_required", False))
        optional_drift_names = {
            "western_superhero_anatomy_drift": DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value,
            "generic_fantasy_rpg_drift": DriftType.GENERIC_FANTASY_RPG_DRIFT.value,
            "character_sheet_presentation_drift": DriftType.CHARACTER_SHEET_PRESENTATION_DRIFT.value,
            "background_presentation_collapse": DriftType.BACKGROUND_PRESENTATION_COLLAPSE.value,
        }
        detected_drifts = {str(value) for value in observations.get("detected_drift_types", ())}
        for name, drift in optional_drift_names.items():
            level = str(observations.get(name, "NONE")).upper()
            if level not in DRIFT_LEVELS:
                raise RegionalStyleError(f"{name} must be NONE, LOW, MEDIUM, or HIGH")
            if level in {"MEDIUM", "HIGH"}:
                detected_drifts.add(drift)
        pseudo_oriental = bool(observations.get("pseudo_oriental_default_detected", False))
        if pseudo_oriental:
            detected_drifts.add(DriftType.PSEUDO_ORIENTAL_FANTASY_DEFAULT.value)
        if bool(observations.get("archetype_shortcut_replacement", False)):
            detected_drifts.add(DriftType.ARCHETYPE_SHORTCUT_REPLACEMENT.value)
        for value, drift in (
            (drift_values["western_anime_drift"], DriftType.WESTERN_ANIME_STYLE_DRIFT.value),
            (drift_values["western_concept_art_drift"], DriftType.WESTERN_FANTASY_CONCEPT_DRIFT.value),
            (superhero_drift, DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value),
        ):
            if value in {"MEDIUM", "HIGH"}:
                detected_drifts.add(drift)
        perceived = observations.get("perceived_regional_visual_language")
        if perceived and str(perceived) != target:
            detected_drifts.add(DriftType.WESTERN_ANIME_STYLE_DRIFT.value)
        severe = any(value == "HIGH" for value in drift_values.values()) or (
            target == DEFAULT_REGIONAL_VISUAL_LANGUAGE and superhero_drift == "HIGH"
        ) or pseudo_oriental or any(
            str(observations.get(name, "NONE")).upper() == "HIGH" for name in optional_drift_names
        )
        average = sum(scores) / len(scores)
        if (
            confidence < min_confidence
            or read < fail_read
            or (target == DEFAULT_REGIONAL_VISUAL_LANGUAGE and severe)
            or (maturity_required and (maturity_read is None or maturity_read < acceptable_read))
        ):
            match = "FAIL"
        elif read < acceptable_read or average < acceptable_read or any(value == "MEDIUM" for value in drift_values.values()):
            match = "WEAK"
        elif read >= strong_read and average >= strong_read and not any(value == "MEDIUM" for value in drift_values.values()):
            match = "STRONG"
        else:
            match = "ACCEPTABLE"
        return RegionalStyleReview(
            str(image),
            target,
            match,
            read,
            drift_values["western_anime_drift"],
            drift_values["western_concept_art_drift"],
            scores[0],
            scores[1],
            scores[2],
            scores[3],
            float(confidence),
            "STYLE_VALID" if match in {"STRONG", "ACCEPTABLE"} else "FAIL",
            maturity_read=maturity_read,
            expected_regional_visual_language=target,
            perceived_regional_visual_language=str(perceived) if perceived else None,
            outfit_language_match=scores[2],
            material_language_match=_score(observations["material_language_match"], "material_language_match")
            if "material_language_match" in observations
            else None,
            pseudo_oriental_default_detected=pseudo_oriental,
            detected_drift_types=tuple(sorted(detected_drifts)),
            rationale=str(observations.get("rationale", "Actual-image review from human-labeled observations.")),
        )


@dataclass(frozen=True)
class StrongFemaleRegionalStyleReview:
    result: str
    commercial_gacha_anime_read: bool
    western_superhero_anatomy_drift: str
    issues: tuple[str, ...] = ()
    detected_drift_types: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def review_strong_female_regional_style(
    observations: Mapping[str, Any],
) -> StrongFemaleRegionalStyleReview:
    """Check strength through deliberate proportions, not superhero massing."""
    drift = str(observations.get("western_superhero_anatomy_drift", "NONE")).upper()
    if drift not in DRIFT_LEVELS:
        raise RegionalStyleError("western_superhero_anatomy_drift must be NONE, LOW, MEDIUM, or HIGH")
    body_text = " ".join(
        str(observations.get(name, ""))
        for name in ("body_grammar", "body_type", "archetype_shortcut", "regional_body_notes")
    ).lower()
    issues: list[str] = []
    if drift in {"MEDIUM", "HIGH"}:
        issues.append("strength reads as western superhero massing")
    if any(token in body_text for token in ("amazon warrior", "bodybuilder", "superhero heroine", "giant trapezius")):
        issues.append("strong-female shortcut replaces character-specific anime proportions")
    commercial_read = bool(observations.get("commercial_gacha_anime_read", True))
    if not commercial_read:
        issues.append("body does not read as a commercial gacha anime character")
    return StrongFemaleRegionalStyleReview(
        "FAIL" if issues else "PASS",
        commercial_read,
        drift,
        tuple(issues),
        (DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value,) if issues and drift in {"MEDIUM", "HIGH"} else (),
    )


@dataclass(frozen=True)
class MaleRegionalBodyReview:
    result: str
    body_type: str
    western_heroic_triangle_drift: str
    issues: tuple[str, ...] = ()
    detected_drift_types: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def review_male_regional_body(observations: Mapping[str, Any]) -> MaleRegionalBodyReview:
    """Keep male anatomy varied instead of defaulting to a Western RPG triangle."""
    allowed_body_types = {"slender", "lean", "compact", "athletic", "broad", "heavy", "mature", ""}
    body_type = str(observations.get("body_type", "")).lower()
    if body_type not in allowed_body_types:
        raise RegionalStyleError(f"unsupported male body_type: {body_type}")
    drift = str(observations.get("western_heroic_triangle_drift", "NONE")).upper()
    if drift not in DRIFT_LEVELS:
        raise RegionalStyleError("western_heroic_triangle_drift must be NONE, LOW, MEDIUM, or HIGH")
    body_text = " ".join(
        str(observations.get(name, ""))
        for name in ("body_grammar", "regional_body_notes", "archetype_shortcut")
    ).lower()
    issues: list[str] = []
    if drift in {"MEDIUM", "HIGH"} or any(
        token in body_text for token in ("huge shoulders", "giant arms", "huge chest", "heroic triangle")
    ):
        issues.append("male body defaults to oversized western heroic massing")
    return MaleRegionalBodyReview(
        "FAIL" if issues else "PASS",
        body_type,
        drift,
        tuple(issues),
        (DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value,) if issues else (),
    )


def detect_generic_fantasy_rpg_drift(
    observed_features: Mapping[str, Any],
    *,
    character_specific_reason: str | None = None,
) -> dict[str, Any]:
    """Detect a repeated fantasy-RPG costume recipe without banning a justified design."""
    text = " ".join(str(value) for value in observed_features.values()).lower()
    signals = {
        "robe_like_structure": any(token in text for token in ("robe", "robe-like")),
        "sash": "sash" in text,
        "gold_trim": any(token in text for token in ("gold trim", "golden trim")),
        "long_hanging_panels": any(token in text for token in ("long hanging", "hanging panel")),
        "ornamental_belt": "ornamental belt" in text,
        "cloak": any(token in text for token in ("cloak", "cape")),
        "generic_fantasy_boots": "fantasy boot" in text or "generic boot" in text,
    }
    count = sum(signals.values())
    justified = bool(character_specific_reason and character_specific_reason.strip())
    result = "NONE" if count < 3 or justified else "HIGH" if count >= 4 else "MEDIUM"
    return {
        "result": result,
        "signals": [name for name, present in signals.items() if present],
        "detected_drift_types": [DriftType.GENERIC_FANTASY_RPG_DRIFT.value] if result != "NONE" else [],
        "hard_gate": False,
    }


def detect_archetype_shortcut_replacement(
    archetype: str,
    observed_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Flag when an archetype merely swaps one cliché for another."""
    text = " ".join(str(value) for value in observed_features.values()).lower()
    shortcuts = {
        "mature male": ("western fantasy brute", "huge square jaw", "giant trapezius"),
        "young social male": ("desert rogue prince",),
        "androgynous woman": ("dark pseudo-oriental uniform",),
        "strong woman": ("amazon warrior", "bodybuilder"),
        "partial beast": ("generic elegant kemonomimi",),
    }
    matched = [token for token in shortcuts.get(archetype.strip().lower(), ()) if token in text]
    return {
        "result": "HIGH" if matched else "NONE",
        "archetype": archetype,
        "matched_shortcuts": matched,
        "detected_drift_types": [DriftType.ARCHETYPE_SHORTCUT_REPLACEMENT.value] if matched else [],
        "hard_gate": bool(matched),
    }


@dataclass(frozen=True)
class StyleGateResult:
    global_rendering_result: str
    regional_visual_language_result: str
    character_visual_style_result: str
    detected_drift_types: tuple[str, ...]
    overall_result: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GachaStyleCritic:
    """Keep the existing global gacha stage and add regional Stage B."""

    def __init__(self, regional_critic: RegionalStyleCritic | None = None) -> None:
        self.regional_critic = regional_critic or RegionalStyleCritic()

    def review(
        self,
        actual_image: str | Path,
        *,
        global_rendering_result: str,
        observations: Mapping[str, Any],
        character_visual_style_result: str = "PASS",
        detected_drift_types: tuple[str, ...] = (),
        target_regional_visual_language: str = DEFAULT_REGIONAL_VISUAL_LANGUAGE,
    ) -> tuple[RegionalStyleReview, StyleGateResult]:
        regional = self.regional_critic.review(
            actual_image,
            observations=observations,
            target_regional_visual_language=target_regional_visual_language,
        )
        drifts = set(detected_drift_types)
        drifts.update(regional.detected_drift_types)
        if regional.western_anime_drift in {"MEDIUM", "HIGH"}:
            drifts.add(DriftType.WESTERN_ANIME_STYLE_DRIFT.value)
        if regional.western_concept_art_drift in {"MEDIUM", "HIGH"}:
            drifts.add(DriftType.WESTERN_FANTASY_CONCEPT_DRIFT.value)
        if str(observations.get("western_superhero_anatomy_drift", "NONE")).upper() in {"MEDIUM", "HIGH"}:
            drifts.add(DriftType.WESTERN_SUPERHERO_ANATOMY_DRIFT.value)
        if observations.get("maturity_required") and (regional.maturity_read is None or regional.maturity_read < 6):
            drifts.add(DriftType.REGIONAL_STYLE_INFANTILIZATION.value)
        gate = StyleGateResult(
            global_rendering_result,
            regional.regional_visual_language_match,
            character_visual_style_result,
            tuple(sorted(drifts)),
            "STYLE_VALID"
            if global_rendering_result == "PASS"
            and regional.result == "STYLE_VALID"
            and character_visual_style_result == "PASS"
            else "FAIL",
        )
        return regional, gate


def make_outfit_feature_ledger_record(
    actual_image: str | Path,
    observed_features: Mapping[str, Any],
) -> dict[str, Any]:
    """Create an actual-image, human-labeled outfit feature record."""
    image = Path(actual_image)
    if not image.is_file():
        raise RegionalStyleError("outfit ledger requires an existing actual image")
    return {
        "actual_image": str(image),
        "evidence_source": "human_actual_image_review",
        "outfit_features": {name: observed_features.get(name) for name in OUTFIT_FEATURES},
        "lower_body_features": {name: observed_features.get(name) for name in LOWER_BODY_LEDGER_FEATURES},
        "background_features": {name: observed_features.get(name) for name in BACKGROUND_FEATURES},
    }


def detect_outfit_family_collapse(
    records: list[Mapping[str, Any]],
    *,
    user_requested_uniform: bool = False,
    minimum_count: int = 4,
) -> dict[str, Any]:
    """Diagnose repeated outfit grammar without making it a hard gate."""
    if user_requested_uniform or len(records) < minimum_count:
        return {"result": "NONE", "detected_fields": [], "hard_gate": False, "minimum_count": minimum_count}
    detected: list[str] = []
    for field in OUTFIT_FEATURES:
        values = [record.get("outfit_features", {}).get(field) for record in records]
        meaningful = [value for value in values if value not in (None, False, "", "none", "NONE")]
        if len(meaningful) >= minimum_count:
            counts: dict[str, int] = {}
            for value in meaningful:
                key = json.dumps(value, ensure_ascii=False, sort_keys=True)
                counts[key] = counts.get(key, 0) + 1
            if max(counts.values(), default=0) >= minimum_count:
                detected.append(field)
    result = "HIGH" if len(detected) >= 3 else "MEDIUM" if detected else "NONE"
    return {
        "result": result,
        "detected_fields": detected,
        "hard_gate": False,
        "minimum_count": minimum_count,
        "diagnostic": DriftType.OUTFIT_FAMILY_COLLAPSE.value if result != "NONE" else None,
    }


def detect_background_presentation_collapse(
    records: list[Mapping[str, Any]],
    *,
    user_requested_background: bool = False,
    minimum_count: int = 4,
) -> dict[str, Any]:
    """Diagnose repeated background templates without turning them into a style gate."""
    if user_requested_background or len(records) < minimum_count:
        return {"result": "NONE", "detected_fields": [], "hard_gate": False, "minimum_count": minimum_count}
    detected: list[str] = []
    for field in BACKGROUND_FEATURES:
        values = [record.get("background_features", {}).get(field) for record in records]
        values = [value for value in values if value not in (None, "", False, "none", "NONE")]
        if len(values) < minimum_count:
            continue
        counts: dict[str, int] = {}
        for value in values:
            key = json.dumps(value, ensure_ascii=False, sort_keys=True)
            counts[key] = counts.get(key, 0) + 1
        if max(counts.values(), default=0) >= minimum_count:
            detected.append(field)
    result = "HIGH" if len(detected) >= 2 else "MEDIUM" if detected else "NONE"
    return {
        "result": result,
        "detected_fields": detected,
        "hard_gate": False,
        "minimum_count": minimum_count,
        "diagnostic": DriftType.BACKGROUND_PRESENTATION_COLLAPSE.value if result != "NONE" else None,
    }


def detect_lower_body_collapse(
    records: list[Mapping[str, Any]],
    *,
    user_requested_uniform: bool = False,
    minimum_count: int = 4,
) -> dict[str, Any]:
    """Report repeated conservative coverage, legwear, and footwear patterns."""
    empty = {
        "detected_drift_types": [],
        "repetition_penalty": 0,
        "hard_gate": False,
        "minimum_count": minimum_count,
        "patterns": [],
    }
    if user_requested_uniform or len(records) < minimum_count:
        return empty

    def feature(record: Mapping[str, Any], name: str) -> Any:
        return record.get("lower_body_features", {}).get(
            name,
            record.get("outfit_features", {}).get(name),
        )

    def repeated(name: str) -> bool:
        values = [feature(record, name) for record in records]
        values = [value for value in values if value not in (None, "", False, "none", "NONE")]
        if len(values) < minimum_count:
            return False
        counts: dict[str, int] = {}
        for value in values:
            key = json.dumps(value, ensure_ascii=False, sort_keys=True)
            counts[key] = counts.get(key, 0) + 1
        return max(counts.values(), default=0) >= minimum_count

    patterns: list[str] = []
    for record in records:
        lower_text = " ".join(
            _feature_text(record.get("outfit_features", {}).get(name, ""))
            for name in ("lower_body_structure", "outfit_family")
        ).lower()
        footwear_text = _feature_text(feature(record, "footwear_family")).lower()
        legwear_text = _feature_text(feature(record, "legwear_family")).lower()
        exposure_text = _feature_text(feature(record, "thigh_exposure")).lower()
        if any(token in lower_text for token in ("trouser", "pants")) and "boot" in footwear_text:
            patterns.append("trousers + boots")
        elif "skirt" in lower_text and "boot" in footwear_text:
            patterns.append("long skirt + boots")
        elif ("bare" in exposure_text or "none" in legwear_text) and "heel" in footwear_text:
            patterns.append("bare legs + heels")
        elif "black" in legwear_text and "heel" in footwear_text:
            patterns.append("black stockings + heels")
    repeated_patterns = sorted({pattern for pattern in patterns if patterns.count(pattern) >= minimum_count})
    covered = sum(
        feature(record, "thigh_exposure") is not None
        and _feature_text(feature(record, "thigh_exposure")).lower()
        in {"false", "none", "fully covered", "mostly covered"}
        for record in records
    )
    detected: list[str] = []
    if covered >= minimum_count:
        detected.append(DriftType.CONSERVATIVE_COVERAGE_COLLAPSE.value)
    if repeated("legwear_family"):
        detected.append(DriftType.LEGWEAR_FAMILY_COLLAPSE.value)
    if repeated("footwear_family"):
        detected.append(DriftType.FOOTWEAR_FAMILY_COLLAPSE.value)
    detected.extend(
        drift
        for drift in (DriftType.CONSERVATIVE_COVERAGE_COLLAPSE.value,)
        if repeated_patterns and drift not in detected
    )
    return {
        "detected_drift_types": sorted(set(detected)),
        "repetition_penalty": len(set(detected)) + len(repeated_patterns),
        "hard_gate": False,
        "minimum_count": minimum_count,
        "patterns": repeated_patterns,
    }
