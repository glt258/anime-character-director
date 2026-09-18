"""Context-aware candidate generation for the human interaction gates.

The generator is deliberately deterministic: the first candidate set is a
function of the input/context, and an explicit regeneration revision is the
only thing that changes it.  This makes persistence and replay testable
without creating a second character-design system.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import hashlib
import random
import re
from typing import Any, Mapping, Sequence


CANDIDATE_GENERATOR_VERSION = "CONTEXT_AWARE_DYNAMIC_INTERACTION_CANDIDATES_V1"

DESIGN_DNA_FIELDS = (
    "silhouette_family",
    "hair_structure",
    "horn_topology",
    "upper_body_structure",
    "lower_body_structure",
    "costume_topology",
    "exposure_strategy",
    "legwear_strategy",
    "footwear_category",
    "accessory_density",
    "pose_family",
    "body_line_emphasis",
    "tail_design",
    "wing_strategy",
    "palette_family",
    "material_language",
    "background_family",
    "pose_specification",
    "background_specification",
)

POSE_SPECIFICATION_FIELDS = (
    "lower_body_pose",
    "weight_distribution",
    "torso_orientation",
    "shoulder_line",
    "arm_configuration",
    "left_arm_action",
    "right_arm_action",
    "left_hand_gesture",
    "right_hand_gesture",
    "head_attitude",
    "gaze_direction",
    "gesture_energy",
)

BACKGROUND_SPECIFICATION_FIELDS = (
    "environment_type",
    "architecture_presence",
    "architecture_language",
    "spatial_structure",
    "atmosphere",
    "lighting_context",
    "ground_plane",
    "depth_structure",
    "background_complexity",
    "dominant_shape_language",
)


_POSE_SPECIFICATIONS: dict[str, dict[str, str]] = {
    "OPEN_PARALLEL_STANCE": {
        "lower_body_pose": "open parallel stance",
        "weight_distribution": "balanced",
        "torso_orientation": "front-facing",
        "shoulder_line": "level relaxed",
        "arm_configuration": "asymmetric open gesture",
        "left_arm_action": "relaxed at side",
        "right_arm_action": "extended outward",
        "left_hand_gesture": "relaxed fingers",
        "right_hand_gesture": "open palm outward",
        "head_attitude": "level",
        "gaze_direction": "direct viewer gaze",
        "gesture_energy": "open confident",
    },
    "NARROW_SEPARATED_STANCE": {
        "lower_body_pose": "narrow separated stance",
        "weight_distribution": "upright balanced",
        "torso_orientation": "upright vertical",
        "shoulder_line": "slightly asymmetric",
        "arm_configuration": "both arms relaxed apart",
        "left_arm_action": "resting near waist",
        "right_arm_action": "raised beside shoulder",
        "left_hand_gesture": "relaxed fingers",
        "right_hand_gesture": "open palm outward",
        "head_attitude": "slight tilt",
        "gaze_direction": "direct viewer gaze",
        "gesture_energy": "composed restrained",
    },
    "FORWARD_STEP_NON_CROSSING": {
        "lower_body_pose": "forward step with separate leg lanes",
        "weight_distribution": "forward-weighted",
        "torso_orientation": "slight forward lean",
        "shoulder_line": "active diagonal",
        "arm_configuration": "one arm extended, one lowered",
        "left_arm_action": "reaching forward",
        "right_arm_action": "relaxed at side",
        "left_hand_gesture": "reaching outward",
        "right_hand_gesture": "neutral hanging hand",
        "head_attitude": "slightly lowered",
        "gaze_direction": "forward focus",
        "gesture_energy": "direct active",
    },
    "OFFSET_NON_OVERLAPPING_STANCE": {
        "lower_body_pose": "offset separated stance",
        "weight_distribution": "asymmetric balanced",
        "torso_orientation": "slight three-quarter turn",
        "shoulder_line": "subtle diagonal",
        "arm_configuration": "one arm extended, one lowered",
        "left_arm_action": "relaxed at side",
        "right_arm_action": "extended outward",
        "left_hand_gesture": "neutral relaxed fingers",
        "right_hand_gesture": "open palm outward",
        "head_attitude": "level",
        "gaze_direction": "direct viewer gaze",
        "gesture_energy": "controlled directional",
    },
    "ASYMMETRIC_WEIGHT_STANCE": {
        "lower_body_pose": "asymmetric planted stance",
        "weight_distribution": "single-leg dominant",
        "torso_orientation": "upright vertical",
        "shoulder_line": "asymmetric relaxed",
        "arm_configuration": "both arms relaxed apart",
        "left_arm_action": "resting near waist",
        "right_arm_action": "relaxed at side",
        "left_hand_gesture": "relaxed fingers",
        "right_hand_gesture": "neutral hanging hand",
        "head_attitude": "slight tilt",
        "gaze_direction": "side glance",
        "gesture_energy": "quiet asymmetry",
    },
    "LOW_ENERGY_SEPARATED_STANCE": {
        "lower_body_pose": "narrow stable separated stance",
        "weight_distribution": "single-leg dominant",
        "torso_orientation": "upright vertical",
        "shoulder_line": "lowered relaxed",
        "arm_configuration": "both arms relaxed low",
        "left_arm_action": "hanging relaxed at side",
        "right_arm_action": "resting at waist",
        "left_hand_gesture": "neutral relaxed fingers",
        "right_hand_gesture": "neutral relaxed fingers",
        "head_attitude": "slight side turn",
        "gaze_direction": "off-camera",
        "gesture_energy": "quiet low-energy",
    },
    "WIDE_ACTIVE_STANCE": {
        "lower_body_pose": "wide grounded stance",
        "weight_distribution": "low-center balanced",
        "torso_orientation": "counter-rotated",
        "shoulder_line": "strong diagonal",
        "arm_configuration": "asymmetric open gesture",
        "left_arm_action": "extended sideways",
        "right_arm_action": "resting at waist",
        "left_hand_gesture": "open palm outward",
        "right_hand_gesture": "relaxed fingers",
        "head_attitude": "chin raised",
        "gaze_direction": "direct viewer gaze",
        "gesture_energy": "bold grounded",
    },
}


def pose_specification_for_family(pose_family: Any) -> dict[str, str]:
    """Return a deterministic whole-body pose spec without face-adjacent defaults."""
    key = str(pose_family or "OPEN_PARALLEL_STANCE").upper()
    source = _POSE_SPECIFICATIONS.get(key, _POSE_SPECIFICATIONS["OPEN_PARALLEL_STANCE"])
    return {name: source[name] for name in POSE_SPECIFICATION_FIELDS}


def background_specification_for_family(background_family: Any) -> dict[str, str]:
    """Expand a legacy background label into executable spatial constraints."""
    text = str(background_family or "").lower()
    abstract = {
        "environment_type": "abstract",
        "architecture_presence": "none",
        "architecture_language": "none",
        "spatial_structure": "layered luminous planes",
        "atmosphere": "soft haze",
        "lighting_context": "diffuse commercial key light",
        "ground_plane": "abstract gradient base",
        "depth_structure": "soft atmospheric depth",
        "background_complexity": "medium",
        "dominant_shape_language": "clean vertical planes",
    }
    if any(token in text for token in ("pressure", "motion", "arc")):
        abstract.update(
            spatial_structure="layered directional planes",
            atmosphere="high-contrast energy haze",
            lighting_context="directional rim light",
            dominant_shape_language="diagonal pressure arcs",
        )
    if "spotlight" in text:
        abstract.update(
            spatial_structure="flat graphic planes",
            atmosphere="clean stage haze",
            lighting_context="single controlled spotlight",
            background_complexity="low",
            dominant_shape_language="circular spotlight bands",
        )
    if "ritual" in text or "architectural" in text:
        return {
            "environment_type": "ritual space",
            "architecture_presence": "minimal",
            "architecture_language": "minimal ceremonial",
            "spatial_structure": "shallow ceremonial layers",
            "atmosphere": "quiet mist",
            "lighting_context": "soft backlight",
            "ground_plane": "visible matte floor",
            "depth_structure": "soft atmospheric depth",
            "background_complexity": "medium",
            "dominant_shape_language": "vertical frames and restrained rings",
        }
    if any(token in text for token in ("urban", "city")):
        return {
            "environment_type": "urban exterior",
            "architecture_presence": "supporting",
            "architecture_language": "modern geometric",
            "spatial_structure": "offset facade depth",
            "atmosphere": "clean dusk air",
            "lighting_context": "cool ambient light with one warm accent",
            "ground_plane": "visible reflective pavement",
            "depth_structure": "layered city depth",
            "background_complexity": "medium",
            "dominant_shape_language": "vertical planes and thin lines",
        }
    if any(token in text for token in ("industrial", "workshop")):
        return {
            "environment_type": "industrial exterior",
            "architecture_presence": "supporting",
            "architecture_language": "industrial geometric",
            "spatial_structure": "deep corridor structure",
            "atmosphere": "high-contrast atmosphere",
            "lighting_context": "hard side light with cool fill",
            "ground_plane": "visible matte industrial floor",
            "depth_structure": "deep layered perspective",
            "background_complexity": "medium-high",
            "dominant_shape_language": "beams, planes, and modular frames",
        }
    return abstract


@dataclass(frozen=True)
class DesignDNA:
    silhouette_family: str
    hair_structure: str
    horn_topology: str
    upper_body_structure: str
    lower_body_structure: str
    costume_topology: str
    exposure_strategy: str
    legwear_strategy: str
    footwear_category: str
    accessory_density: str
    pose_family: str
    body_line_emphasis: str
    tail_design: str
    wing_strategy: str
    palette_family: str
    material_language: str
    background_family: str
    pose_specification: Mapping[str, str] = field(default_factory=dict)
    background_specification: Mapping[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pose_specification"] = dict(self.pose_specification) or pose_specification_for_family(self.pose_family)
        data["background_specification"] = dict(self.background_specification) or background_specification_for_family(self.background_family)
        return data


_SUCCUBUS_DNA: tuple[DesignDNA, ...] = (
    DesignDNA(
        "tapered_hourglass_frame", "short_wavy_side_sweep", "swept_back_blade_horns",
        "fitted_wrap_bodice", "open_hip_leg_line", "bodysuit_plus_cropped_outer_layer",
        "waist_and_back_exposure", "bare_legs", "tall_flat_boots", "one_primary_anchor",
        "OPEN_PARALLEL_STANCE", "forward_shoulders_long_leg_line", "thin_spade_tail",
        "minimal_membrane_wings", "plum_and_copper", "matte_satin_and_soft_leather",
        "clean_gradient_architecture",
    ),
    DesignDNA(
        "vertical_ritual_frame", "high_ponytail_with_ribbon_mass", "crown_like_horns",
        "structured_shouldered_bodice", "split_skirt_columns", "asymmetric_ritual_dress",
        "shoulder_and_back_exposure", "sheer_side_panels", "barefoot_ankle_jewelry", "sparse_symbolic_anchor",
        "NARROW_SEPARATED_STANCE", "elegant_vertical_line", "ribboned_arrow_tail",
        "translucent_wing_motif", "oxblood_and_aged_ivory", "satin_organza_and_brushed_metal",
        "quiet_architectural_haze",
    ),
    DesignDNA(
        "low_center_predatory_frame", "braided_medium_side_mass", "branching_compact_horns",
        "cropped_structured_top", "shorts_with_long_split_overskirt", "shorts_plus_split_overskirt",
        "thigh_and_side_cutout", "opaque_thigh_wraps", "combat_boots", "dense_single_anchor",
        "FORWARD_STEP_NON_CROSSING", "low_center_aggressive_shoulders", "visible_barbed_tail",
        "visible_demon_wings", "deep_teal_and_crimson", "brushed_leather_and_translucent_film",
        "layered_pressure_field",
    ),
    DesignDNA(
        "narrow_dominant_frame", "layered_bob_with_side_lock", "narrow_rear_horns",
        "open_structured_top", "fitted_trousers", "tailored_trousers_plus_open_top",
        "cleavage_and_waist_framing", "none", "platform_shoes", "minimal_graphic_anchor",
        "LOW_ENERGY_SEPARATED_STANCE", "relaxed_dominant_vertical_line", "segmented_ribbon_tail",
        "no_physical_wings_symbolic_motif", "violet_and_graphite", "structured_crepe_and_polished_resin",
        "abstract_spotlight_gradient",
    ),
)

_DEFAULT_DNA: tuple[DesignDNA, ...] = (
    DesignDNA("vertical_spine", "asymmetric_long_layers", "compact_upward_sweep", "structured_shell", "open_trouser_line", "tailored_layered", "controlled_partial_exposure", "none", "low_asymmetrical_boots", "one_primary_anchor", "OPEN_PARALLEL_STANCE", "balanced_vertical_line", "thin_spade_tail", "none", "deep_teal_with_warm_accent", "matte_satin", "clean_gradient_architecture"),
    DesignDNA("offset_balance", "short_geometric_bob", "offset_side_sweep", "soft_structured_wrap", "split_skirt_columns", "offset_layered", "shoulder_and_waist_framing", "sheer_side_panels", "flat_sneakers", "sparse_symbolic_anchor", "NARROW_SEPARATED_STANCE", "asymmetric_weight_line", "ribbon_tail", "abstract_motif", "violet_and_graphite", "soft_fabric_and_resin", "quiet_architectural_haze"),
    DesignDNA("layered_motion", "braided_side_mass", "branching_compact_sweep", "modular_short_outer", "shorts_with_long_split_layer", "modular_split", "side_cutout", "opaque_wraps", "combat_boots", "single_structural_anchor", "FORWARD_STEP_NON_CROSSING", "forward_motion_line", "visible_tail", "partial_membrane", "cobalt_with_copper", "light_panel_and_brushed_metal", "layered_motion_field"),
    DesignDNA("material_hook_frame", "medium_directional_layers", "narrow_rear_sweep", "open_structured_top", "fitted_trousers", "material_contrast_tailoring", "back_framing", "none", "barefoot_ankle_structure", "minimal_graphic_anchor", "LOW_ENERGY_SEPARATED_STANCE", "calm_dominant_line", "none", "none", "sage_and_ink", "matte_crepe_and_polished_resin", "clean_atmospheric_gradient"),
)


def _has(text: str, *terms: str) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def candidate_compatibility(candidate: Mapping[str, Any], constraints: Mapping[str, Any]) -> dict[str, Any]:
    """Reject only candidates matching every attribute of a prohibited unit."""
    candidate_text = str(candidate).lower()
    candidate_attributes = candidate.get("attributes") if isinstance(candidate.get("attributes"), Mapping) else {}
    candidate_attributes = {**candidate_attributes, **{key: value for key, value in candidate.items() if key in {"hair_color", "hair_style_family", "archetype"}}}
    dna = candidate.get("design_dna") if isinstance(candidate.get("design_dna"), Mapping) else {}
    candidate_attributes = {**candidate_attributes, **dict(dna)}
    violations = []
    for item in constraints.get("prohibited_constraints", ()):
        if not isinstance(item, Mapping):
            continue
        attributes = item.get("attributes") if isinstance(item.get("attributes"), Mapping) else {}
        matched = bool(attributes) and all(str(candidate_attributes.get(key, "")).lower() == str(value).lower() for key, value in attributes.items())
        if not matched and not attributes:
            text = str(item.get("text", "")).lower()
            aliases = {
                "literal mechanic visualization": ("literal mechanic", "mechanic uniform", "wrench", "goggles"),
                "human female with cosmetic animal ears only": ("human female", "animal ears"),
            }.get(text, (text,))
            matched = all(alias in candidate_text for alias in aliases if alias)
        if matched:
            violations.append(str(item.get("text", "prohibited constraint")))
    negative = constraints.get("negative_constraints") if isinstance(constraints.get("negative_constraints"), Mapping) else {}
    footwear = str(dna.get("footwear_category", "")).lower()
    pose = str(dna.get("pose_family", "")).lower()
    costume = f"{dna.get('costume_topology', '')} {dna.get('lower_body_structure', '')}".lower()
    if negative.get("forbid_footwear_family") and any(token in footwear for token in ("heel", "platform")):
        violations.append("high heels")
    if negative.get("forbid_crossed_legs") and any(token in pose for token in ("cross", "coy")):
        violations.append("crossed legs")
    if negative.get("forbid_outfit_lower") and str(negative["forbid_outfit_lower"]).lower() in costume:
        violations.append(str(negative["forbid_outfit_lower"]))
    records = constraints.get("explicit_constraint_records")
    if isinstance(records, Mapping):
        aliases = {
            "legwear": "legwear_strategy",
            "footwear": "footwear_category",
            "horns": "horn_topology",
            "tail": "tail_design",
            "wings": "wing_strategy",
        }
        for field_name, record in records.items():
            if field_name not in aliases or not isinstance(record, Mapping):
                continue
            expected = str(record.get("value", "")).lower()
            observed = str(dna.get(aliases[field_name], "")).lower()
            if expected and expected not in observed:
                violations.append(f"explicit {field_name}={expected}")
    return {"status": "incompatible" if violations else "compatible", "violations": violations}


def context_profile(original_input: str, constraints: Mapping[str, Any] | None = None) -> str:
    text = f"{original_input} {(constraints or {}).get('raw', '')}".lower()
    if _has(text, "兽人", "非人", "兽耳", "狼", "狐", "beast", "wolf", "nonhuman"):
        return "nonhuman_predatory"
    if _has(text, "机械", "维修", "设备", "装置", "mechanical", "repair"):
        return "mechanical_kinetic"
    if _has(text, "温柔", "耐心", "信任", "亲和", "gentle", "patient", "trust"):
        return "gentle_distinctive"
    if _has(text, "都市", "城市", "现代", "幻想", "观察", "克制", "危险", "urban", "city", "fantasy"):
        return "urban_watchful"
    return "specific_adult"


def _design_dna_library(original_input: str) -> tuple[DesignDNA, ...]:
    text = f"{original_input}".lower()
    if _has(text, "魅魔", "succubus", "demoness"):
        return _SUCCUBUS_DNA
    return _DEFAULT_DNA


def _apply_explicit_constraints_to_dna(
    dna: Mapping[str, Any],
    constraints: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply human-owned fields before a candidate reaches any gate."""
    result = deepcopy(dict(dna))
    raw = str(constraints.get("raw", "")).lower()
    records = constraints.get("explicit_constraint_records")
    records = records if isinstance(records, Mapping) else {}
    locks: dict[str, Any] = {}

    def value(name: str) -> Any:
        record = records.get(name)
        if isinstance(record, Mapping):
            return record.get("value")
        return constraints.get(name)

    def lock(name: str, target: str | None = None) -> None:
        resolved = value(name)
        if resolved is None:
            return
        result[target or name] = deepcopy(resolved)
        locks[name] = {"value": deepcopy(resolved), "source": "human_explicit", "priority": "HARD", "locked": True}

    role = str(value("role_identity") or "").lower()
    costume = str(value("costume_identity") or "").lower()
    if role in {"maid", "head_maid"} or "maid" in costume:
        result["costume_topology"] = "maid-based"
        locks["costume_identity"] = {"value": value("costume_identity") or "maid_outfit", "source": "human_explicit", "priority": "HARD", "locked": True}
    if value("body_proportion"):
        result["upper_body_structure"] = "large-bust feminine structure"
        result["body_proportion"] = value("body_proportion")
        locks["body_proportion"] = {"value": value("body_proportion"), "source": "human_explicit", "priority": "HARD", "locked": True}
    if value("legwear"):
        lock("legwear", "legwear_strategy")
    if value("footwear"):
        lock("footwear", "footwear_category")
    if value("palette_primary") or value("palette_secondary"):
        primary = value("palette_primary") or str(result.get("palette_family", "")).split()[0]
        secondary = value("palette_secondary") or ""
        result["palette_family"] = f"{primary} dominant" + (f" / {secondary} secondary" if secondary else "")
        for name in ("palette_primary", "palette_secondary"):
            if value(name):
                locks[name] = {"value": value(name), "source": "human_explicit", "priority": "HARD", "locked": True}
    if value("props"):
        props = value("props")
        result["props"] = list(props) if isinstance(props, list) else [props]
        result["major_accessories"] = ", ".join(str(item) for item in result["props"])
        locks["props"] = {"value": deepcopy(props), "source": "human_explicit", "priority": "HARD", "locked": True}
    if value("gender_presentation"):
        result["gender_presentation"] = value("gender_presentation")
    if value("nonhuman_features"):
        result["nonhuman_features"] = value("nonhuman_features")
        if "fox" in str(value("nonhuman_features")).lower():
            result["horn_topology"] = "none"
            result["tail_design"] = "none"
            result["wing_strategy"] = "none"
    if value("human_form_requirement"):
        result["human_form_requirement"] = value("human_form_requirement")
    if value("quantity_constraints"):
        result["quantity_constraints"] = deepcopy(value("quantity_constraints"))
    for name in (
        "character_state",
        "bust_emphasis",
        "companion_type",
        "companion_count",
        "hair",
        "pose",
        "background",
        "composition",
        "footwear_detail",
        "style_contract",
        "face_reference",
    ):
        if value(name) is not None:
            result[name] = deepcopy(value(name))
            locks[name] = {"value": deepcopy(value(name)), "source": "human_explicit", "priority": "HARD", "locked": True}
    for name, target in (("horns", "horn_topology"), ("tail", "tail_design"), ("wings", "wing_strategy")):
        if value(name):
            lock(name, target)
    # Intrusive anatomy is opt-in; identity alone cannot silently re-enable it.
    for name, target in (("horns", "horn_topology"), ("tail", "tail_design"), ("wings", "wing_strategy")):
        if not value(name) and not _has(raw, "魅魔", "succubus", "demoness"):
            result[target] = "none"
    return result, locks


def normalize_design_seed(seed: Any) -> int:
    if seed is None:
        return 0
    try:
        return int(seed)
    except (TypeError, ValueError):
        digest = hashlib.sha256(str(seed).encode("utf-8")).digest()
        return int.from_bytes(digest[:8], "big")


def stable_session_seed(session_id: str) -> int:
    return normalize_design_seed(session_id)


def select_seeded_candidate(candidates: Sequence[Mapping[str, Any]], seed: Any, *, salt: str) -> dict[str, Any]:
    if not candidates:
        raise ValueError("cannot select from an empty candidate set")
    rng = random.Random(f"{normalize_design_seed(seed)}:{salt}")
    return deepcopy(candidates[rng.randrange(len(candidates))])


def select_ai_candidate(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not candidates:
        raise ValueError("cannot select from an empty candidate set")
    ranked = sorted(
        enumerate(candidates),
        key=lambda pair: (pair[1].get("score", 0), pair[1].get("recommendation_score", 0), -pair[0]),
        reverse=True,
    )
    selected = deepcopy(ranked[0][1])
    selected["resolution_metadata"] = {
        "mode": "AI_DECIDE",
        "strategy": "divergent_candidate_generation_then_score_selection",
        "candidate_pool_size": len(candidates),
        "evaluated_candidate_ids": [str(item.get("id")) for item in candidates],
        "selected_candidate_id": str(selected.get("id")),
    }
    return selected


def _route(
    slug: str,
    zh: str,
    en: str,
    zh_description: str,
    en_description: str,
    zh_silhouette: str,
    en_silhouette: str,
    zh_anchor: str,
    en_anchor: str,
    zh_shape: str,
    en_shape: str,
    score: int,
    *tags: str,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "title_zh": zh,
        "title_en": en,
        "description_zh": zh_description,
        "description_en": en_description,
        "silhouette_zh": zh_silhouette,
        "silhouette_en": en_silhouette,
        "anchor_zh": zh_anchor,
        "anchor_en": en_anchor,
        "shape_zh": zh_shape,
        "shape_en": en_shape,
        "score": score,
        "tags": tags,
    }


_CHARACTER_ROUTES: dict[str, tuple[dict[str, Any], ...]] = {
    "urban_watchful": (
        _route("urban_night_observer", "静默夜行者", "Silent Night Observer", "以克制、观察性和距离感为核心，危险感藏在极少的动作和锐利视线里。", "A restrained, observant presence whose danger is carried by minimal movement and a sharp gaze.", "细长纵向轮廓，轻量外层与窄幅下身形成干净的城市剪影。", "A long vertical silhouette with a light outer layer and a narrow lower profile.", "微弱暖色信号点打断冷色轮廓。", "A small warm signal interrupts the cool silhouette.", "低动作密度、清晰边缘、局部不对称。", "Low motion density, clean edges, and a localized asymmetry.", 96, "urban", "observant", "restrained", "signal"),
        _route("low_temperature_predator", "低温捕食者", "Low-Temperature Predator", "保留少女感和现代感，用前倾重心、收紧肩线与更明确的视线落实潜在攻击性。", "Keeps a youthful modern read while making latent aggression legible through a forward center of gravity and tightened shoulders.", "上身略向前压，下身保持开放分离，重心集中在肩颈与视线。", "A slight forward compression above an open, separated lower stance.", "锐利眼神与短促的肩部切线构成第一记忆点。", "A sharp gaze and a short shoulder cut form the first memory hook.", "硬朗斜切线配柔和基础层，避免成熟化。", "Crisp diagonal cuts over a soft base layer without aging the character up.", 93, "urban", "danger", "forward", "youthful"),
        _route("city_edge_ghost", "城市边缘幽灵", "City-Edge Ghost", "重点放在难以捉摸的异质存在感：她像总在人群边缘出现，却不依赖夸张符号。", "Prioritizes an elusive edge-of-the-crowd presence without relying on loud symbols.", "偏移式外轮廓和不对称下摆制造像素级可辨识的侧向重量。", "An offset outer contour and asymmetric hem create a readable side-weighted silhouette.", "一块不连续的几何色面像城市反光一样短暂出现。", "A broken geometric color block appears like a brief city reflection.", "偏移、留白、短线条节奏。", "Offset balance, negative space, and short-line rhythm.", 91, "urban", "elusive", "offset", "negative_space"),
        _route("masked_approachable", "伪装亲和者", "Masked Approachable", "第一眼保持容易接近的少女气质，再用一个克制而锋利的局部结构暴露不安感。", "Reads approachable at first, then reveals unease through one restrained, sharp structural detail.", "圆润上身与利落下摆对照，视觉重量集中在一侧而非全身堆叠。", "A rounded upper read contrasts with a crisp hem, with weight concentrated on one side.", "柔和表情旁的单一锐角结构负责反差。", "One angular structural detail beside a calm expression carries the contrast.", "圆角基础形加单点锐角，不引入模板制服。", "Rounded base shapes with one sharp interruption, without a uniform template.", 88, "urban", "contrast", "approachable", "single_anchor"),
    ),
    "mechanical_kinetic": (
        _route("kinetic_service_runner", "高速检修奔线者", "Kinetic Service Runner", "把长期设备经验转化为快速解决问题的身体语言，角色首先是外向、有吸引力的行动者。", "Turns long equipment experience into fast problem-solving body language; the character remains an outgoing, appealing mover first.", "前后错开的动态轮廓，短外层与可摆动的下摆让动作方向一眼可读。", "A staggered dynamic contour with a short outer layer and a movable hem.", "一条沿身体偏移的结构线暗示快速调整与路径判断。", "An offset construction line suggests rapid adjustment and route reading.", "速度线式分割、轻量层叠、局部硬材质。", "Speed-like paneling, light layering, and localized hard material.", 96, "mechanical", "kinetic", "outgoing", "nonliteral"),
        _route("resonant_operator", "外放共振操作者", "Expressive Resonance Operator", "机械关系通过节奏、反应速度和材质反馈表现，而不是把职业工具直接挂在身上。", "Expresses the mechanical relationship through rhythm, reaction speed, and material feedback rather than literal tools.", "大幅单侧上身量感配轻快下身，形成有弹性的斜向剪影。", "A broad one-sided upper mass paired with a light lower body creates a springy diagonal silhouette.", "会随动作改变读法的可动连接片成为记忆点。", "A movable connector panel changes its read with motion.", "软硬材质交替、圆角结构与短促切面。", "Alternating soft and hard materials with rounded structures and short cuts.", 93, "mechanical", "responsive", "outgoing", "material_contrast"),
        _route("modular_leap", "轻装跃迁者", "Lightweight Leap Operator", "强调灵活、外向和临场应变，把设备经验压缩成轻便而有个人风格的穿着结构。", "Emphasizes agility, openness, and improvisation by compressing equipment experience into a light personal wardrobe structure.", "紧凑核心轮廓外接一块可展开的侧向层，跳跃方向明确。", "A compact core silhouette extends into one deployable side layer with a clear leap direction.", "可展开侧层与发束共同形成记忆弧线。", "A deployable side layer and a hair mass form a shared memory arc.", "轻薄片层、弹性边缘、清楚的连接关系。", "Light panels, elastic edges, and legible connections.", 90, "mechanical", "agile", "outgoing", "modular"),
        _route("improvised_rhythm", "即兴节奏拼接者", "Improvised Rhythm Builder", "将维修现场的快速判断转成富有节奏的外向表现，保留可抽取角色所需的清晰主锚点。", "Turns rapid field decisions into an expressive rhythm while keeping one clear anchor for a collectible character.", "不规则但平衡的拼接轮廓，左右视觉重量有意错开。", "An irregular but balanced patchwork silhouette with deliberately offset visual weight.", "一处不同节奏的拼接结构打破整体重复。", "One off-beat construction break interrupts the overall rhythm.", "形状节奏优先于道具堆叠，材质层级少而明确。", "Shape rhythm takes priority over prop clutter, with few clear material tiers.", 87, "mechanical", "improvised", "rhythmic", "anchor"),
    ),
    "nonhuman_predatory": (
        _route("forward_hunter_frame", "前倾猎相", "Forward Hunter Frame", "通过前倾重心、非人比例和更长的肢体节奏建立压迫感，不依赖暴露或人类化装饰。", "Builds pressure through a forward center of gravity, nonhuman proportion, and elongated limb rhythm rather than exposure or humanized decoration.", "肩胯关系偏窄、躯干前倾，四肢节奏比人类女性更长更利。", "A narrow shoulder-to-hip relationship and forward torso create a sharper, elongated limb rhythm.", "颌线与肩胛结构共同组成捕食者记忆点。", "The jawline and shoulder-blade structure form a predatory memory hook.", "长斜线、低重心、局部硬质表面。", "Long diagonals, low center of gravity, and localized hard surfaces.", 97, "nonhuman", "predatory", "anatomy", "low_center"),
        _route("low_center_beast", "沉重兽相", "Low-Center Beast Form", "把危险感放在下沉的体态、宽窄反差和非人关节节奏上，保持商业立绘的可读性。", "Places danger in a lowered body, width contrast, and nonhuman joint rhythm while preserving commercial readability.", "下沉重心与宽肩窄腰形成稳定、压迫性的块面轮廓。", "A lowered center with broad shoulders and a narrow waist creates a stable, pressuring block silhouette.", "非人关节转折和短尾部结构提供局部识别。", "Nonhuman joint turns and a short tail structure provide local recognition.", "块面、短折线、厚薄材质对比。", "Block shapes, short turns, and thick-thin material contrast.", 94, "nonhuman", "pressure", "joint", "mass"),
        _route("segmented_cold_body", "节段冷体", "Segmented Cold Body", "让非人感进入身体分区和服装边界，角色仍是现代二游审美中的强记忆女性兽人。", "Moves the nonhuman read into body segmentation and clothing boundaries while staying within a modern collectible-game aesthetic.", "纵向分节和偏移胸腹结构改变身体的连续读法。", "Vertical segmentation and offset torso construction change how the body is read as a continuous form.", "一组与身体节奏一致的角、骨或鳞片形结构成为锚点。", "A horn, bone, or scale-like structure aligned with the body rhythm becomes the anchor.", "节段化边缘、冷硬材质、少量柔性过渡。", "Segmented edges, cold hard materials, and limited soft transitions.", 91, "nonhuman", "segmented", "cold", "body_structure"),
        _route("silent_pressure_guard", "静压守望者", "Silent Pressure Warden", "用几乎不动的表情、异常稳定的站姿和明确的非人结构传达冷血压迫感。", "Conveys cold pressure through a nearly still expression, a stable stance, and unmistakable nonhuman structure.", "竖直主轴配低幅外扩结构，静态立绘也有压迫性的边界。", "A vertical axis with restrained outward spread keeps pressure visible in a static standee.", "眼部、耳角或面部骨性结构只保留一处强锚点。", "Only one strong anchor remains around the eyes, ears, horns, or facial bone structure.", "大留白、低饱和冷色、单点锐利边缘。", "Generous negative space, cool low saturation, and one sharp edge.", 88, "nonhuman", "cold", "static_pressure", "single_anchor"),
    ),
    "gentle_distinctive": (
        _route("steady_trust_anchor", "稳态信任者", "Steady Trust Anchor", "把亲和力放在稳定的视线、开放但不松散的姿态和可靠的结构比例上。", "Builds trust through a steady gaze, an open but controlled stance, and reliable proportions.", "中等外扩上身配清晰下身分区，轮廓稳而不软。", "A moderately open upper body and clear lower divisions create a stable, unsentimental silhouette.", "一处有方向性的肩部或发束形状提供个人记忆点。", "One directional shoulder or hair shape provides the personal memory hook.", "温和曲线配结构化边缘，色面分区简洁。", "Gentle curves meet structured edges with simple color blocking.", 96, "gentle", "trust", "steady", "structured"),
        _route("patient_wayfinder", "耐心引路人", "Patient Wayfinder", "用清楚的空间秩序和轻微偏移表达耐心，让亲和力来自可依靠的设计逻辑。", "Uses clear spatial order and a slight offset to express patience, making warmth feel dependable rather than generic.", "前后两层长度错开，形成向前引导的开放轮廓。", "Two layers with offset lengths form an open contour that guides the eye forward.", "一条连续的引导线从发型延伸到服装边界。", "A continuous guide line runs from the hair shape into the garment boundary.", "连续线、低饱和对比、少量硬质收口。", "Continuous lines, low-saturation contrast, and a few hard closures.", 93, "gentle", "patient", "guiding", "continuity"),
        _route("quiet_civic_light", "静暖秩序者", "Quiet Civic Light", "保留容易信任的气质，但用城市化材质和不对称组织避免落入常见的柔软模板。", "Keeps a trustworthy read while using urban materials and asymmetric organization to avoid a familiar soft template.", "偏置式上身结构与直落下摆形成利落、可站立的轮廓。", "An offset upper structure and straight hem create a crisp standing silhouette.", "局部暖色反射面成为亲和力之外的辨识点。", "A small warm reflective plane adds recognition beyond approachability.", "直线框架、柔性内层、金属或树脂小面积对比。", "Linear framing, a soft inner layer, and a small metal or resin contrast.", 90, "gentle", "urban", "asymmetry", "material"),
        _route("grounded_companion", "有棱角的陪伴者", "Grounded Companion", "亲和力与明确边界并存，靠真实的姿态和一个有棱角的视觉锚点建立记忆。", "Combines approachability with clear boundaries, using believable posture and one angular anchor for memory.", "短外轮廓包住稳定核心，局部向外伸展形成个人节奏。", "A short outer contour frames a stable core with one outward extension.", "单一偏硬配件或发束成为可信赖感之外的锋面。", "One firm accessory or hair section supplies a sharp facet beyond trust.", "圆形核心、尖角中断、克制材质层级。", "A rounded core, a pointed interruption, and restrained material hierarchy.", 87, "gentle", "companion", "boundary", "anchor"),
    ),
    "specific_adult": (
        _route("identity_spine", "身份主轴", "Identity Spine", "从原始输入提炼一个清晰的身份主轴，以纵向轮廓和单一主锚点保持商业角色可读。", "Extracts one clear identity spine from the input, using a vertical silhouette and one primary anchor for readability.", "纵向主轴与开放下身形成可读、可复用的立绘轮廓。", "A vertical spine and open lower body form a readable standee silhouette.", "单一头部或肩部锚点负责第一眼识别。", "One head or shoulder anchor carries first-glance recognition.", "清晰边缘、少量不对称、稳定色面。", "Clean edges, limited asymmetry, and stable color blocks.", 92, "identity", "vertical", "anchor", "readability"),
        _route("offset_balance", "偏移平衡", "Offset Balance", "把输入中的关键特征放到轮廓一侧，形成真正可视化的差异而不是只换形容词。", "Places the input's key trait on one side of the contour to create a visual difference rather than an adjective swap.", "一侧外扩、一侧收紧，形成明显的左右重量差。", "One side expands while the other tightens, creating clear left-right weight contrast.", "偏移色面或构造线作为记忆锚。", "An offset color block or construction line acts as the memory anchor.", "不对称分区、边缘节奏、材料对照。", "Asymmetric zoning, edge rhythm, and material contrast.", 90, "offset", "asymmetry", "contrast", "structure"),
        _route("layered_motion", "层叠动势", "Layered Motion", "用层次长度和身体方向表达输入要求，让角色即使静止也保留动作潜能。", "Uses layer lengths and body direction to express the input while retaining motion potential in a static pose.", "短核心加长侧层，形成前后深度和明确的动作方向。", "A short core with a longer side layer creates depth and a clear action direction.", "动态发束或服装边界提供可追踪的视觉路径。", "A dynamic hair mass or garment edge provides a traceable visual path.", "长度差、轻重材质、方向性切线。", "Length contrast, light-heavy materials, and directional cuts.", 88, "motion", "layered", "direction", "depth"),
        _route("material_memory", "材质记忆点", "Material Memory", "把角色记忆集中到材质关系和局部构造，避免符号堆积并保留二游商业完成度。", "Concentrates memory in material relationships and local construction, avoiding symbol clutter while preserving commercial finish.", "简洁主体轮廓配一块清楚的材质突变区域。", "A simple main contour carries one clear material-shift region.", "材质突变本身成为可识别锚点。", "The material shift itself becomes the recognizable anchor.", "软硬、哑光高光、细线粗面形成层级。", "Soft-hard, matte-gloss, and fine-line broad-surface hierarchy.", 86, "material", "contrast", "anchor", "hierarchy"),
    ),
}


_ART_ROUTES: dict[str, tuple[dict[str, Any], ...]] = {
    "urban_watchful": (
        _route("cool_reflection_slice", "冷反光切片", "Cool Reflection Slice", "让已选角色方向落到冷暖反射、城市纵深和局部锐角上，保持克制的观看距离。", "Translates the chosen character direction into cool-warm reflection, urban depth, and one sharp angle.", "竖向背景切片与人物长轮廓同向，画面重心偏离中心。", "Vertical background slices follow the long figure and shift the composition off-center.", "冷色大面中的一处暖反光成为画面锚点。", "One warm reflection inside a cool field anchors the image.", "纵向构图、清透雾层、单点高光。", "Vertical composition, clear atmospheric depth, and one highlight.", 95, "urban", "vertical", "reflection", "distance"),
        _route("edge_lighting_lane", "边缘光行道", "Edge-Light Lane", "以边缘光和狭长留白表现难以接近的危险感，不把职业或世界观做成道具。", "Uses edge light and narrow negative space to show danger without turning worldbuilding into props.", "人物置于偏移光带中，左右边界清楚，双腿保持独立可见。", "The figure sits in an offset light lane with clear boundaries and independent legs.", "一条窄光带沿肩颈或发束走向。", "A narrow light band follows the shoulder or hair direction.", "低饱和底色、锐利边缘光、少量粒子。", "Low-saturation base, crisp rim light, and restrained particles.", 92, "urban", "rim_light", "negative_space", "open_lanes"),
        _route("offset_facade", "偏移立面", "Offset Facade", "将城市异质感压缩成非对称立面和材质边界，突出角色而不是背景装饰。", "Compresses urban otherness into an asymmetric facade and material boundary so the character stays primary.", "一侧背景块面压住画面，另一侧留出干净呼吸区。", "One background mass presses into the frame while the other side breathes.", "人物侧向构造线与背景边界形成呼应。", "A side construction line echoes the background boundary.", "平面块、透明层、细线轮廓的三层秩序。", "Three-layer order of planes, translucent depth, and fine contour.", 89, "urban", "offset", "facade", "breathing_room"),
        _route("quiet_signal_frame", "静默信号框", "Silent Signal Frame", "用一个简短的图形信号框定角色的观看关系，保留亲近可能但不削弱异质感。", "Frames the viewing relationship with one brief graphic signal while keeping the otherness intact.", "窄框式构图包住角色主轴，底部留出开放空间。", "A narrow frame contains the figure's spine with open space below.", "信号图形与眼神方向相交。", "The signal graphic intersects the gaze direction.", "圆角框、单锐角、轻雾背景。", "Rounded frame, one sharp corner, and a light haze.", 86, "urban", "frame", "signal", "contrast"),
    ),
    "mechanical_kinetic": (
        _route("trajectory_panels", "轨迹面板", "Trajectory Panels", "以轨迹、连接和速度方向落实机械关系，画面仍优先服务外向行动者。", "Uses trajectories, connections, and speed direction to express the mechanical relation while serving the outgoing mover.", "多段斜向面板把人物动作切成可读节拍。", "Multiple diagonal panels divide the action into readable beats.", "一条可追踪连接线跨越发束与服装边界。", "One traceable connection crosses the hair and garment boundary.", "轻量面板、透明结构、少量硬质高光。", "Light panels, translucent structure, and sparse hard highlights.", 95, "mechanical", "trajectory", "connection", "kinetic"),
        _route("responsive_arc", "响应弧线", "Responsive Arc", "把快速反应和设备反馈转译成环形动作构图与材质回弹，而不是工具陈列。", "Translates fast reactions and equipment feedback into an arc composition and material rebound rather than tool display.", "人物与背景形成半环形动线，身体重心保持开放。", "The figure and background form a half-arc movement while the body stays open.", "一段可动弧线连接手部动作和肩部轮廓。", "A movable arc connects the hand action to the shoulder contour.", "弹性边缘、亮暗交替、圆角接口。", "Elastic edges, alternating light-dark, and rounded interfaces.", 92, "mechanical", "arc", "feedback", "open"),
        _route("modular_depth", "模块纵深", "Modular Depth", "用前后模块和清晰的重叠关系表现长期设备经验，避免职业符号化。", "Uses front-back modules and clear overlap to express long equipment experience without literal job symbols.", "近景小模块、人物主体、远景薄层构成三段纵深。", "A small foreground module, main figure, and thin background layer create three depths.", "唯一的模块接口成为视觉记忆点。", "One module interface becomes the memory point.", "哑光主体、局部金属、透明边缘。", "Matte body, localized metal, and translucent edges.", 89, "mechanical", "modular", "depth", "interface"),
        _route("playful_impact_grid", "活跃冲击格", "Playful Impact Grid", "以不规则网格和跃动留白承接外向性格，让动势不依赖杂乱道具。", "Uses an irregular grid and bouncing negative space to carry extroversion without prop clutter.", "斜向网格与前踏方向统一，人物边界保持干净。", "A diagonal grid follows the forward step while the figure boundary stays clean.", "一个偏离网格的色块承担记忆。", "One grid-breaking color block carries the memory.", "高低明度跳跃、短线、干净色面。", "Value jumps, short lines, and clean color fields.", 86, "mechanical", "grid", "playful", "impact"),
    ),
    "nonhuman_predatory": (
        _route("anatomical_depth", "非人结构纵深", "Anatomical Depth", "让非人结构成为画面构图的一部分，强化压迫感而不依靠裸露。", "Makes the nonhuman structure part of the composition, intensifying pressure without relying on exposure.", "前景压低、人物主轴前倾、背景留白形成三层压迫。", "A lowered foreground, forward figure axis, and negative background create layered pressure.", "角、颌或肩胛形体与背景切面互相咬合。", "Horn, jaw, or shoulder-blade forms interlock with the background plane.", "硬边、低重心、冷色大面。", "Hard edges, low center, and cool broad surfaces.", 97, "nonhuman", "anatomy", "pressure", "interlock"),
        _route("cold_mass_formation", "冷质量编队", "Cold Mass Formation", "用块面和体态编队传达兽性压迫，保持现代二游画面的节奏与可读性。", "Uses block masses and body formation to convey beast pressure with modern collectible-game readability.", "低位块面围绕下沉主体，形成稳定的视觉重力。", "Low masses surround the lowered figure and create visual gravity.", "一处非人局部结构切穿大块面。", "One nonhuman local structure cuts through the broad mass.", "厚薄块面、短折线、窄高光。", "Thick-thin masses, short turns, and narrow highlights.", 93, "nonhuman", "mass", "gravity", "cold"),
        _route("segmented_boundary", "节段边界", "Segmented Boundary", "以身体节段与服装边界的对应关系建立真正的非人读法。", "Builds a real nonhuman read through correspondence between body segments and garment boundaries.", "纵向分段将人物切成连续但非人化的节拍。", "Vertical segmentation divides the figure into a continuous but nonhuman rhythm.", "节段连接点成为唯一高密度区域。", "A segment junction becomes the only high-density area.", "冷硬材质、少量柔性过渡、清晰闭合线。", "Cold hard materials, limited soft transitions, and clear closure lines.", 90, "nonhuman", "segmented", "boundary", "rhythm"),
        _route("silent_threat_space", "静压威胁场", "Silent Threat Space", "以留白、低幅姿态和一处锐利局部结构留住冷血危险感。", "Holds cold danger through negative space, low-amplitude posture, and one sharp local structure.", "人物占比克制，周围留白把边界压力推向观者。", "A restrained figure scale lets surrounding negative space push pressure outward.", "眼部或面部骨性结构承担唯一强对比。", "The eye or facial bone structure carries the only strong contrast.", "大留白、单锐角、低饱和渐变。", "Generous negative space, one sharp angle, and a low-saturation gradient.", 87, "nonhuman", "negative_space", "threat", "single_anchor"),
    ),
    "gentle_distinctive": (
        _route("architectural_warmth", "建筑暖光", "Architectural Warmth", "用有秩序的暖光和清晰框架承接信任感，视觉锚点保持在角色本身。", "Uses ordered warm light and a clear frame to carry trust while keeping the anchor on the character.", "人物置于稳定框架内，顶部留出呼吸区。", "The figure sits in a stable frame with breathing room above.", "一条暖光边界沿肩部或发束延伸。", "A warm light boundary follows the shoulder or hair mass.", "温暖渐变、硬边框架、少量哑光层。", "Warm gradient, hard frame, and sparse matte layers.", 95, "gentle", "warm", "frame", "trust"),
        _route("guiding_path", "引导路径", "Guiding Path", "把耐心和可靠感变成观者可追踪的视线路径，而不是装饰性堆叠。", "Turns patience and reliability into a traceable eye path rather than decorative accumulation.", "前景线条从画面边缘引向人物开放下身。", "A foreground line leads from the frame edge to the open lower body.", "线条终点与面部表情形成闭环。", "The line endpoint closes a loop with the facial expression.", "连续线、低对比材质、单点亮色。", "Continuous lines, low-contrast materials, and one accent color.", 92, "gentle", "guiding", "path", "open"),
        _route("asymmetric_shelter", "偏置庇护", "Asymmetric Shelter", "用偏置结构表达照顾感，同时保留清楚的边界和个人风格。", "Uses offset structure to express care while keeping clear boundaries and personal style.", "一侧轻薄遮护层包住人物，另一侧完全留白。", "A light shelter layer covers one side while the other side stays open.", "遮护边界的折角提供记忆点。", "A fold at the shelter boundary provides the memory point.", "软内层、硬收口、低饱和色面。", "Soft inner layer, hard closure, and low-saturation fields.", 89, "gentle", "shelter", "offset", "boundary"),
        _route("quiet_color_break", "静色断点", "Quiet Color Break", "用一处不预期的色彩断点让亲和力拥有清晰记忆，而不是回到默认模板。", "Uses one unexpected color break to give approachability a clear memory instead of a default template.", "大面积安静背景托住简洁主体，断点偏离中心。", "A quiet broad background supports a simple figure with the break off-center.", "断点沿发束、袖口或鞋部形成短路径。", "The break forms a short path along hair, cuff, or footwear.", "低饱和主体、单色断点、清线条。", "Low-saturation body, one color break, and clean lines.", 86, "gentle", "color_break", "off_center", "memory"),
    ),
    "specific_adult": (
        _route("clear_playable_frame", "清晰可玩框架", "Clear Playable Frame", "把当前输入压缩成清楚的商业立绘框架，保持一个可记忆的视觉入口。", "Compresses the current input into a clear commercial standee frame with one memorable entry point.", "主体居中偏移，背景纵深和下身空间都保持开放。", "The figure is slightly off-center with open depth and lower-body space.", "一个头部或肩部形体作为入口。", "One head or shoulder form is the entry point.", "清线条、稳定块面、有限高光。", "Clean line, stable blocks, and limited highlights.", 92, "clear", "playable", "frame", "anchor"),
        _route("contrast_planes", "对照色面", "Contrast Planes", "以三块有关系的色面和材质边界让当前角色方向被看见。", "Makes the current direction visible through three related color planes and material boundaries.", "左右色面不等重，轮廓因此产生可读偏移。", "Unequal left-right color planes create a readable contour offset.", "中间断点负责记忆。", "A central break carries the memory.", "哑光、透明、细线三层对照。", "Matte, translucent, and fine-line contrast.", 89, "contrast", "planes", "material", "offset"),
        _route("motion_depth_stack", "动势纵深", "Motion Depth Stack", "用前后层次和方向性留白保留静态画面的动作潜能。", "Retains motion potential through depth layers and directional negative space.", "前层短、主体清楚、后层长，形成明确运动路径。", "Short front layer, clear figure, and long rear layer create a motion path.", "一条方向性边缘线串起画面。", "One directional edge line ties the image together.", "轻重叠层、斜切边缘、低噪声背景。", "Light overlap, diagonal edges, and a low-noise background.", 87, "motion", "depth", "direction", "space"),
        _route("single_material_hook", "单一材质钩点", "Single Material Hook", "把辨识度收束到一个材质钩点，避免同时堆叠多个符号。", "Concentrates recognition in one material hook instead of stacking several symbols.", "主体轮廓保持简洁，局部材质区域打破连续性。", "The main contour stays simple while one material area breaks continuity.", "材质钩点直接承担记忆。", "The material hook carries the memory directly.", "软硬材质、哑光高光、简洁背景。", "Soft-hard material, matte-gloss contrast, and a simple background.", 84, "material", "single_anchor", "simple", "contrast"),
    ),
}


def _prior_label(prior_resolutions: Sequence[Mapping[str, Any]]) -> str:
    for item in reversed(list(prior_resolutions)):
        direction = item.get("direction") if isinstance(item, Mapping) else None
        if isinstance(direction, Mapping):
            return str(direction.get("title_en") or direction.get("short_label") or direction.get("design_thesis") or "the selected character direction")
    return "the selected character direction"


def validate_candidate_diversity(candidates: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    comparisons = []
    fields = DESIGN_DNA_FIELDS
    for index, left in enumerate(candidates):
        for right in candidates[index + 1 :]:
            left_sig = _structural_signature(left)
            right_sig = _structural_signature(right)
            overlaps = {name: int(left_sig.get(name) == right_sig.get(name)) for name in fields}
            differences = sum(not value for value in overlaps.values())
            comparisons.append({"left": left.get("id"), "right": right.get("id"), "overlap": overlaps, "structural_differences": differences, "valid": differences >= 2})
    valid = all(item["valid"] for item in comparisons)
    return {
        "valid": valid,
        "status": "PASS" if valid else "LOW_STRUCTURAL_DIVERSITY",
        "comparisons": comparisons,
        "checked_dimensions": list(fields),
        "cosmetic_dimensions": ["hair_color", "eye_color", "accessory_tint"],
    }


def _structural_signature(candidate: Mapping[str, Any]) -> dict[str, Any]:
    dna = candidate.get("design_dna") if isinstance(candidate.get("design_dna"), Mapping) else {}
    visual = candidate.get("visual_implications") if isinstance(candidate.get("visual_implications"), Mapping) else {}
    silhouette = visual.get("silhouette") if isinstance(visual.get("silhouette"), Mapping) else {}
    aliases = {
        "silhouette_family": ("silhouette_family", "silhouette", silhouette.get("en")),
        "hair_structure": ("hair_structure", "hair_style_family"),
        "horn_topology": ("horn_topology", "ear_horn_shape"),
        "upper_body_structure": ("upper_body_structure", "upper_body"),
        "lower_body_structure": ("lower_body_structure", "lower_body"),
        "costume_topology": ("costume_topology", "outfit_direction", "costume_structure"),
        "exposure_strategy": ("exposure_strategy",),
        "legwear_strategy": ("legwear_strategy", "legwear_family"),
        "footwear_category": ("footwear_category", "footwear_family"),
        "accessory_density": ("accessory_density",),
        "pose_family": ("pose_family",),
        "body_line_emphasis": ("body_line_emphasis",),
        "tail_design": ("tail_design", "tail"),
        "wing_strategy": ("wing_strategy", "wings"),
        "palette_family": ("palette_family", "dominant_palette", "palette"),
        "material_language": ("material_language",),
        "background_family": ("background_family", "background_direction"),
        "pose_specification": ("pose_specification",),
        "background_specification": ("background_specification",),
    }
    signature = {}
    for name, keys in aliases.items():
        value = next((dna[key] for key in keys if key in dna), None)
        if value is None:
            value = next((candidate[key] for key in keys if key in candidate), None)
        signature[name] = str(value) if value is not None else "<unspecified>"
    return signature


class CandidateGenerator:
    """Generate deterministic, context-specific candidates for interaction gates."""

    def generate(
        self,
        *,
        gate_id: str,
        original_input: str,
        explicit_constraints: Mapping[str, Any] | None = None,
        prior_resolutions: Sequence[Mapping[str, Any]] = (),
        generation_context: Mapping[str, Any] | None = None,
        style_policy: str = "CONTEMPORARY_COMMERCIAL_GACHA_ANIME",
        locale: str = "en-US",
        revision: int = 0,
        seed: Any = None,
    ) -> list[dict[str, Any]]:
        constraints = dict(explicit_constraints or {})
        profile = context_profile(original_input, constraints)
        kind = "art" if gate_id == "ART_DIRECTION_GATE" else "character"
        routes = list((_ART_ROUTES if kind == "art" else _CHARACTER_ROUTES)[profile])
        if revision:
            shift = revision % len(routes)
            routes = routes[shift:] + routes[:shift]
        prior_label = _prior_label(prior_resolutions)
        dna_library = _design_dna_library(original_input)
        result = []
        for index, route in enumerate(routes, start=1):
            context_note_zh = f"围绕已选的“{prior_label}”继续展开。" if kind == "art" and prior_resolutions else ""
            context_note_en = f"Continues from the selected {prior_label}." if kind == "art" and prior_resolutions else ""
            dna = dna_library[(index - 1) % len(dna_library)]
            dna_dict, explicit_locks = _apply_explicit_constraints_to_dna(dna.to_dict(), constraints)
            result.append({
                "id": f"candidate_{index:02d}",
                "candidate_id": f"candidate_{index:02d}",
                "short_label": route["slug"],
                "title_zh": route["title_zh"],
                "title_en": route["title_en"],
                "description_zh": f"{route['description_zh']}{context_note_zh}",
                "description_en": f"{route['description_en']} {context_note_en}".strip(),
                "summary": f"{route['description_en']} {context_note_en}".strip(),
                "design_thesis": route["slug"],
                "primary_anchor": route["anchor_en"],
                "structure": route["silhouette_en"],
                "visual_implications": {
                    "silhouette": {"zh": route["silhouette_zh"], "en": route["silhouette_en"]},
                    "shape_language": {"zh": route["shape_zh"], "en": route["shape_en"]},
                    "primary_anchor": {"zh": route["anchor_zh"], "en": route["anchor_en"]},
                    "material_hierarchy": {"zh": "服装主体、局部硬质面与清晰色面分层。", "en": "Clear hierarchy between the body, localized hard surface, and color planes."},
                },
                "constraint_compatibility": self._compatibility(profile, original_input, constraints),
                "rationale_zh": f"它把当前输入中的{self._profile_reason_zh(profile)}落实为可视化的轮廓、形状语言和单一记忆锚点。",
                "rationale_en": f"It turns the input's {self._profile_reason_en(profile)} into a visible silhouette, shape language, and single memory anchor.",
                "recommendation_score": route["score"],
                "score": route["score"],
                "identity_source": "context_aware_candidate_generator",
                "candidate_generator_version": CANDIDATE_GENERATOR_VERSION,
                "design_dna": dna_dict,
                "explicit_constraint_locks": deepcopy(explicit_locks),
                "generation_context": {
                    "profile": profile,
                    "gate_id": gate_id,
                    "style_policy": style_policy,
                    "revision": revision,
                    "seed": normalize_design_seed(seed) if seed is not None else None,
                    "prior_direction": prior_label if prior_resolutions else None,
                    **dict(generation_context or {}),
                },
                "diversity_signature": {
                    "semantic": route["tags"][0],
                    "silhouette": route["tags"][1],
                    "outfit_structure": route["tags"][2],
                    "personality_read": route["tags"][3],
                    "visual_anchor": route["slug"],
                    "upper_body_gesture": dna_dict["pose_specification"].get("arm_configuration"),
                    "hand_gesture": [
                        dna_dict["pose_specification"].get("left_hand_gesture"),
                        dna_dict["pose_specification"].get("right_hand_gesture"),
                    ],
                    "background_structure": [
                        dna_dict["background_specification"].get("environment_type"),
                        dna_dict["background_specification"].get("architecture_presence"),
                        dna_dict["background_specification"].get("spatial_structure"),
                    ],
                },
            })
        for item in result:
            item["constraint_compatibility"].update(candidate_compatibility(item, constraints))
        result = [item for item in result if item["constraint_compatibility"]["status"] == "compatible"]
        diversity = validate_candidate_diversity(result)
        if not diversity["valid"]:
            raise ValueError(f"candidate diversity validation failed for {gate_id}")
        for item in result:
            item["diversity_validation"] = deepcopy(diversity)
        return result

    @staticmethod
    def _profile_reason_zh(profile: str) -> str:
        return {"urban_watchful": "都市观察性与隐藏危险感", "mechanical_kinetic": "外向动势与非字面机械关系", "nonhuman_predatory": "非人结构与压迫性", "gentle_distinctive": "亲和力与个人边界", "specific_adult": "角色输入中的核心身份"}[profile]

    @staticmethod
    def _profile_reason_en(profile: str) -> str:
        return {"urban_watchful": "urban observation and hidden danger", "mechanical_kinetic": "outgoing motion and a nonliteral mechanical relationship", "nonhuman_predatory": "nonhuman structure and pressure", "gentle_distinctive": "trust and personal boundaries", "specific_adult": "the core identity in the character input"}[profile]

    @staticmethod
    def _compatibility(profile: str, original_input: str, constraints: Mapping[str, Any]) -> dict[str, Any]:
        text = f"{original_input} {constraints.get('raw', '')}"
        checked = ["age_gender_read", "style_contract", "visual_distinction"]
        if _has(text, "不要交叉腿", "不交叉腿", "禁止交叉腿", "no crossed legs"):
            checked.append("forbid_crossed_legs")
        if _has(text, "不要高跟鞋", "不穿高跟鞋", "no high heels"):
            checked.append("forbid_high_heels")
        if profile == "mechanical_kinetic":
            checked.append("nonliteral_mechanical_identity")
        if profile == "nonhuman_predatory":
            checked.append("nonhuman_silhouette_and_anatomy")
        if profile == "gentle_distinctive":
            checked.append("anti_soft_template")
        return {"status": "compatible", "checked": checked, "violations": [], "constraint_source": "original_input_and_explicit_constraints"}


__all__ = [
    "CANDIDATE_GENERATOR_VERSION",
    "DESIGN_DNA_FIELDS",
    "POSE_SPECIFICATION_FIELDS",
    "BACKGROUND_SPECIFICATION_FIELDS",
    "DesignDNA",
    "CandidateGenerator",
    "candidate_compatibility",
    "context_profile",
    "normalize_design_seed",
    "select_ai_candidate",
    "select_seeded_candidate",
    "stable_session_seed",
    "validate_candidate_diversity",
    "pose_specification_for_family",
    "background_specification_for_family",
]
