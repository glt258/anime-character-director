"""Pose-intent contracts, actual-image intent gating, and pose diversity diagnostics."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class PoseIntentType(str, Enum):
    ELEGANT = "ELEGANT"
    SENSUAL = "SENSUAL"
    RELAXED_ASYMMETRIC = "RELAXED_ASYMMETRIC"
    LOW_ENERGY = "LOW_ENERGY"
    NARROW_STANCE = "NARROW_STANCE"
    ONE_FOOT_FORWARD = "ONE_FOOT_FORWARD"
    OPEN_STANCE = "OPEN_STANCE"
    WIDE_ACTIVE = "WIDE_ACTIVE"
    STABLE_OPEN = "STABLE_OPEN"
    CUSTOM = "CUSTOM"
    UNKNOWN_LEGACY_POSE_INTENT = "UNKNOWN_LEGACY_POSE_INTENT"


class PoseIntentFailureType(str, Enum):
    POSE_INTENT_FAIL = "POSE_INTENT_FAIL"
    POSE_SEMANTIC_EROSION = "POSE_SEMANTIC_EROSION"
    POSE_SAFETY_OVERCONSTRAINT = "POSE_SAFETY_OVERCONSTRAINT"
    NARROW_STANCE_EXPANDED = "NARROW_STANCE_EXPANDED"
    ONE_FOOT_FORWARD_DEPTH_MISSING = "ONE_FOOT_FORWARD_DEPTH_MISSING"
    LOW_ENERGY_READ_MISSING = "LOW_ENERGY_READ_MISSING"
    SENSUAL_POSE_REDUCED_TO_OUTFIT = "SENSUAL_POSE_REDUCED_TO_OUTFIT"
    ELEGANT_POSE_REDUCED_TO_NEUTRAL = "ELEGANT_POSE_REDUCED_TO_NEUTRAL"
    RELAXED_ASYMMETRY_MISSING = "RELAXED_ASYMMETRY_MISSING"


POSE_INTENT_TYPES = tuple(item.value for item in PoseIntentType)
POSE_INTENT_PASS_RESULTS = {"STRONG", "ACCEPTABLE"}

_SIGNAL_SPECS: dict[str, dict[str, Any]] = {
    "ELEGANT": {
        "required_body_signals": (
            "controlled posture",
            "clean torso line",
            "composed shoulders",
            "refined arm placement",
            "graceful weight distribution",
            "intentional body asymmetry",
        ),
        "minimum_visible_signals": 3,
        "stance_width_requirement": "NORMAL_OR_NARROW",
        "asymmetry_requirement": "INTENTIONAL",
        "energy_level": "MEDIUM_OR_LOW",
        "torso_requirement": "UPRIGHT_OR_TILTED",
        "arm_requirement": "REFINED",
        "head_requirement": "NEUTRAL_TILTED_OR_TURNED",
        "forbidden_shortcuts": ("ordinary neutral standing with only a beautiful outfit", "exaggerated S-curve"),
    },
    "SENSUAL": {
        "required_body_signals": (
            "body confidence",
            "torso waist relationship",
            "controlled hip orientation",
            "relaxed shoulder",
            "gaze head angle",
            "arm placement",
        ),
        "minimum_visible_signals": 4,
        "stance_width_requirement": "ANY_SAFE_WIDTH",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "MEDIUM_OR_LOW",
        "torso_requirement": "TILTED_FORWARD_OR_BACK",
        "arm_requirement": "CONTROLLED",
        "head_requirement": "TILTED_OR_TURNED",
        "forbidden_shortcuts": ("outfit-only sensuality", "clothing fanservice replacing body language"),
    },
    "RELAXED_ASYMMETRIC": {
        "required_body_signals": (
            "shoulder asymmetry",
            "unequal weight distribution",
            "softened knee",
            "torso offset",
            "asymmetric arm placement",
            "asymmetric head angle",
        ),
        "minimum_visible_signals": 3,
        "stance_width_requirement": "ANY_SAFE_WIDTH",
        "asymmetry_requirement": "REQUIRED",
        "energy_level": "MEDIUM_OR_LOW",
        "torso_requirement": "RELAXED_OR_TILTED",
        "arm_requirement": "ASYMMETRIC",
        "head_requirement": "TILTED_OR_TURNED",
        "forbidden_shortcuts": ("mirror-symmetrical standing", "one leg crossing the other"),
    },
    "LOW_ENERGY": {
        "required_body_signals": (
            "lowered shoulders",
            "softened knees",
            "settled weight",
            "quiet arm placement",
            "reduced torso tension",
            "soft gaze",
        ),
        "minimum_visible_signals": 2,
        "stance_width_requirement": "ANY_SAFE_WIDTH",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "LOW",
        "torso_requirement": "RELAXED",
        "arm_requirement": "RELAXED_OR_CLOSED",
        "head_requirement": "TILTED_OR_NEUTRAL",
        "forbidden_shortcuts": ("upright alert military stance", "active combat readiness"),
    },
    "NARROW_STANCE": {
        "required_body_signals": ("narrow stance width",),
        "minimum_visible_signals": 1,
        "stance_width_requirement": "NARROW",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "ANY",
        "torso_requirement": "ANY",
        "arm_requirement": "ANY",
        "head_requirement": "ANY",
        "forbidden_shortcuts": ("expanding the requested narrow stance into a normal open stance",),
    },
    "ONE_FOOT_FORWARD": {
        "required_body_signals": ("clear forward foot depth", "balanced step response"),
        "minimum_visible_signals": 1,
        "depth_requirement": "FORWARD_LEFT_OR_RIGHT",
        "stance_width_requirement": "ANY_SAFE_WIDTH",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "ANY",
        "torso_requirement": "NATURAL_RESPONSE",
        "arm_requirement": "ANY",
        "head_requirement": "ANY",
        "forbidden_shortcuts": ("same-plane feet pretending to be a forward step",),
    },
    "OPEN_STANCE": {
        "required_body_signals": ("open stance width",),
        "minimum_visible_signals": 1,
        "stance_width_requirement": "NORMAL_OR_WIDE",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "ANY",
        "torso_requirement": "ANY",
        "arm_requirement": "ANY",
        "head_requirement": "ANY",
        "forbidden_shortcuts": ("closed or tucked leg arrangement",),
    },
    "WIDE_ACTIVE": {
        "required_body_signals": ("wide active stance", "active body language"),
        "minimum_visible_signals": 1,
        "stance_width_requirement": "WIDE",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "HIGH_OR_MEDIUM",
        "torso_requirement": "TILTED_OR_FORWARD",
        "arm_requirement": "ACTIVE",
        "head_requirement": "TURNED_OR_NEUTRAL",
        "forbidden_shortcuts": ("quiet neutral standing",),
    },
    "STABLE_OPEN": {
        "required_body_signals": ("stable open stance",),
        "minimum_visible_signals": 1,
        "stance_width_requirement": "NORMAL_OR_WIDE",
        "asymmetry_requirement": "OPTIONAL",
        "energy_level": "ANY",
        "torso_requirement": "UPRIGHT_OR_RELAXED",
        "arm_requirement": "ANY",
        "head_requirement": "ANY",
        "forbidden_shortcuts": ("unstable posture",),
    },
    "CUSTOM": {
        "required_body_signals": ("custom body-language signal",),
        "minimum_visible_signals": 1,
        "stance_width_requirement": "CUSTOM",
        "asymmetry_requirement": "CUSTOM",
        "energy_level": "CUSTOM",
        "torso_requirement": "CUSTOM",
        "arm_requirement": "CUSTOM",
        "head_requirement": "CUSTOM",
        "forbidden_shortcuts": ("replacing the custom body-language request with a neutral default",),
    },
    "UNKNOWN_LEGACY_POSE_INTENT": {
        "required_body_signals": (),
        "minimum_visible_signals": 0,
        "stance_width_requirement": "UNKNOWN",
        "asymmetry_requirement": "UNKNOWN",
        "energy_level": "UNKNOWN",
        "torso_requirement": "UNKNOWN",
        "arm_requirement": "UNKNOWN",
        "head_requirement": "UNKNOWN",
        "forbidden_shortcuts": (),
    },
}

_POSE_FAMILY_TO_INTENT = {
    "OPEN_PARALLEL_STANCE": "STABLE_OPEN",
    "WIDE_ACTIVE_STANCE": "WIDE_ACTIVE",
    "NARROW_SEPARATED_STANCE": "NARROW_STANCE",
    "LOW_ENERGY_SEPARATED_STANCE": "LOW_ENERGY",
    "FORWARD_STEP_NON_CROSSING": "ONE_FOOT_FORWARD",
}


def _text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)


def _canonical(value: Any) -> str:
    return _text(value).strip().lower().replace("_", " ").replace("-", " ")


def _canonical_signal(value: Any) -> str:
    return " ".join(_canonical(value).split())


def _enum_value(value: str | Enum | None) -> str | None:
    if isinstance(value, Enum):
        return str(value.value)
    if value is None:
        return None
    return str(value).strip().upper()


def resolve_pose_intent(value: str | PoseIntentType | None, pose_description: str = "") -> str:
    explicit = _enum_value(value)
    if explicit:
        aliases = {
            "NARROW": "NARROW_STANCE",
            "ONE FOOT FORWARD": "ONE_FOOT_FORWARD",
            "LOW ENERGY": "LOW_ENERGY",
            "RELAXED ASYMMETRIC": "RELAXED_ASYMMETRIC",
            "OPEN": "OPEN_STANCE",
            "WIDE": "WIDE_ACTIVE",
            "STABLE": "STABLE_OPEN",
        }
        explicit = aliases.get(explicit, explicit)
        if explicit not in POSE_INTENT_TYPES:
            raise ValueError(f"unsupported pose intent: {explicit}")
        return explicit
    return infer_pose_intent_from_text(pose_description)


def infer_pose_intent_from_text(text: str) -> str:
    lowered = _canonical(text)
    checks = (
        (("relaxed asymmetric", "asymmetric relaxed"), "RELAXED_ASYMMETRIC"),
        (("low energy", "quiet", "low-energy"), "LOW_ENERGY"),
        (("narrow",), "NARROW_STANCE"),
        (("one foot forward", "forward step", "slight depth"), "ONE_FOOT_FORWARD"),
        (("sensual", "seductive"), "SENSUAL"),
        (("elegant",), "ELEGANT"),
        (("wide active", "athletic"), "WIDE_ACTIVE"),
        (("open stance",), "OPEN_STANCE"),
        (("stable open", "stable standard", "standard standee"), "STABLE_OPEN"),
    )
    for phrases, intent in checks:
        if any(phrase in lowered for phrase in phrases):
            return intent
    return "CUSTOM" if lowered else "STABLE_OPEN"


@dataclass(frozen=True)
class PoseIntentContract:
    requested_intent: str
    resolved_pose_family: str
    required_body_signals: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
    minimum_visible_signals: int
    leg_safety_required: bool = True
    depth_requirement: str = "ANY"
    stance_width_requirement: str = "ANY"
    asymmetry_requirement: str = "OPTIONAL"
    energy_level: str = "ANY"
    torso_requirement: str = "ANY"
    arm_requirement: str = "ANY"
    head_requirement: str = "ANY"

    def __post_init__(self) -> None:
        if self.requested_intent not in POSE_INTENT_TYPES:
            raise ValueError(f"unsupported pose intent: {self.requested_intent}")
        if self.minimum_visible_signals < 0:
            raise ValueError("minimum_visible_signals must be non-negative")
        if self.leg_safety_required is not True:
            raise ValueError("pose intent cannot disable leg safety")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_pose_intent_contract(
    requested_intent: str | PoseIntentType,
    *,
    resolved_pose_family: str = "",
    custom_body_signals: list[str] | tuple[str, ...] | None = None,
) -> PoseIntentContract:
    intent = resolve_pose_intent(requested_intent)
    spec = dict(_SIGNAL_SPECS[intent])
    signals = tuple(custom_body_signals or spec["required_body_signals"])
    if intent == "CUSTOM" and custom_body_signals:
        spec["minimum_visible_signals"] = min(len(signals), max(1, spec["minimum_visible_signals"]))
    return PoseIntentContract(
        requested_intent=intent,
        resolved_pose_family=resolved_pose_family,
        required_body_signals=signals,
        forbidden_shortcuts=tuple(spec["forbidden_shortcuts"]),
        minimum_visible_signals=int(spec["minimum_visible_signals"]),
        leg_safety_required=True,
        depth_requirement=str(spec.get("depth_requirement", "ANY")),
        stance_width_requirement=str(spec.get("stance_width_requirement", "ANY")),
        asymmetry_requirement=str(spec.get("asymmetry_requirement", "OPTIONAL")),
        energy_level=str(spec.get("energy_level", "ANY")),
        torso_requirement=str(spec.get("torso_requirement", "ANY")),
        arm_requirement=str(spec.get("arm_requirement", "ANY")),
        head_requirement=str(spec.get("head_requirement", "ANY")),
    )


def normalize_pose_intent_contract(value: Mapping[str, Any] | PoseIntentContract) -> PoseIntentContract:
    if isinstance(value, PoseIntentContract):
        return value
    if not isinstance(value, Mapping):
        raise ValueError("pose_intent_contract must be an object")
    base = build_pose_intent_contract(
        str(value.get("requested_intent", "CUSTOM")),
        resolved_pose_family=str(value.get("resolved_pose_family", "")),
    ).to_dict()
    base.update(dict(value))
    return PoseIntentContract(
        requested_intent=str(base["requested_intent"]),
        resolved_pose_family=str(base.get("resolved_pose_family", "")),
        required_body_signals=tuple(str(item) for item in base.get("required_body_signals", ())),
        forbidden_shortcuts=tuple(str(item) for item in base.get("forbidden_shortcuts", ())),
        minimum_visible_signals=int(base.get("minimum_visible_signals", 0)),
        leg_safety_required=bool(base.get("leg_safety_required", True)),
        depth_requirement=str(base.get("depth_requirement", "ANY")),
        stance_width_requirement=str(base.get("stance_width_requirement", "ANY")),
        asymmetry_requirement=str(base.get("asymmetry_requirement", "OPTIONAL")),
        energy_level=str(base.get("energy_level", "ANY")),
        torso_requirement=str(base.get("torso_requirement", "ANY")),
        arm_requirement=str(base.get("arm_requirement", "ANY")),
        head_requirement=str(base.get("head_requirement", "ANY")),
    )


def pose_intent_prompt_lines(contract: PoseIntentContract) -> tuple[str, ...]:
    return (
        "## POSE INTENT",
        f"Requested Pose Intent: {contract.requested_intent}",
        f"Resolved Pose Family: {contract.resolved_pose_family or 'not yet resolved'}",
        "Required Body Language Signals:",
        *(f"- {signal}" for signal in contract.required_body_signals),
        f"Minimum Visible Signals: {contract.minimum_visible_signals}",
        f"Depth Requirement: {contract.depth_requirement}",
        f"Stance Width Requirement: {contract.stance_width_requirement}",
        f"Asymmetry Requirement: {contract.asymmetry_requirement}",
        f"Energy Level: {contract.energy_level}",
        f"Torso Requirement: {contract.torso_requirement}",
        f"Arm Requirement: {contract.arm_requirement}",
        f"Head Requirement: {contract.head_requirement}",
        "Forbidden Pose-Intent Shortcuts:",
        *(f"- {shortcut}" for shortcut in contract.forbidden_shortcuts),
        "Pose intent must be visible in actual body language, not only in clothing, styling, or decoration.",
        "Leg safety remains mandatory and is enforced by the separate LegSeparationContract and actual-image gate.",
    )


def audit_pose_intent_prompt(prompt: str, requested_intent: str | None = None) -> dict[str, Any]:
    text = str(prompt)
    section = "## POSE INTENT" in text
    signals = "Required Body Language Signals:" in text and "Minimum Visible Signals:" in text
    intent_present = requested_intent is None or f"Requested Pose Intent: {requested_intent}" in text
    return {
        "pose_intent_section_present": section,
        "pose_intent_body_signals_present": signals,
        "requested_pose_intent_present": intent_present,
        "passed": all((section, signals, intent_present)),
    }


def migrate_pose_intent_fields(artifact: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Attach pose intent to legacy artifacts without mutating the input."""
    migrated = deepcopy(dict(artifact))
    if "pose_intent" in migrated and "pose_intent_contract" in migrated:
        normalize_pose_intent_contract(migrated["pose_intent_contract"])
        return migrated, None
    family = str(migrated.get("pose_family", ""))
    intent = str(migrated.get("pose_intent", "")) or _POSE_FAMILY_TO_INTENT.get(family, "")
    if not intent:
        intent = "UNKNOWN_LEGACY_POSE_INTENT"
    contract = build_pose_intent_contract(intent, resolved_pose_family=family)
    migrated["pose_intent"] = intent
    migrated["pose_intent_contract"] = contract.to_dict()
    event = {
        "event": "pose_intent_migration",
        "audit_event": "POSE_INTENT_DEFAULT_MIGRATION",
        "old_artifact_version": migrated.get("schema_version", "unknown"),
        "from_pose_family": family or None,
        "new_effective_value": intent,
        "reliable_mapping": intent != "UNKNOWN_LEGACY_POSE_INTENT",
    }
    return migrated, event


def _normalized_features(observations: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(observations)
    nested = observations.get("actual_pose_features")
    if isinstance(nested, Mapping):
        values = {**dict(nested), **values}
    return values


def _value(values: Mapping[str, Any], key: str, allowed: set[str]) -> str:
    value = _canonical(values.get(key, ""))
    aliases = {
        "same plane": "SAME_PLANE",
        "forward left": "FORWARD_LEFT",
        "forward right": "FORWARD_RIGHT",
        "left": "LEFT",
        "right": "RIGHT",
        "centered": "CENTERED",
        "normal": "NORMAL",
        "narrow": "NARROW",
        "wide": "WIDE",
        "soft": "SOFT",
        "bent": "BENT",
        "straight": "STRAIGHT",
        "upright": "UPRIGHT",
        "relaxed": "RELAXED",
        "tilted": "TILTED",
        "forward": "FORWARD",
        "back": "BACK",
        "level": "LEVEL",
        "asymmetric": "ASYMMETRIC",
        "active": "ACTIVE",
        "closed": "CLOSED",
        "turned": "TURNED",
        "neutral": "NEUTRAL",
        "high": "HIGH",
        "medium": "MEDIUM",
        "low": "LOW",
    }
    result = aliases.get(value, value.replace(" ", "_").upper())
    return result if result in allowed else "UNCERTAIN"


def _explicit_signals(values: Mapping[str, Any]) -> set[str]:
    raw = values.get("visible_signals", values.get("signals", ()))
    if isinstance(raw, str):
        raw = [raw]
    return {_canonical_signal(item) for item in raw if str(item).strip()}


def _actual_signals(values: Mapping[str, Any]) -> tuple[set[str], dict[str, str]]:
    stance = _value(values, "stance_width", {"NARROW", "NORMAL", "WIDE", "UNCERTAIN"})
    depth = _value(values, "foot_depth", {"SAME_PLANE", "FORWARD_LEFT", "FORWARD_RIGHT", "UNCERTAIN"})
    weight = _value(values, "weight_distribution", {"CENTERED", "LEFT", "RIGHT", "UNCERTAIN"})
    knee = _value(values, "knee_state", {"STRAIGHT", "SOFT", "BENT", "UNCERTAIN"})
    torso = _value(values, "torso", {"UPRIGHT", "RELAXED", "TILTED", "FORWARD", "BACK", "UNCERTAIN"})
    shoulder = _value(values, "shoulder_relation", {"LEVEL", "ASYMMETRIC", "RELAXED", "UNCERTAIN"})
    arm = _value(values, "arm_activity", {"ACTIVE", "RELAXED", "ASYMMETRIC", "CLOSED", "UNCERTAIN"})
    head = _value(values, "head_angle", {"NEUTRAL", "TILTED", "TURNED", "UNCERTAIN"})
    energy = _value(values, "energy_read", {"HIGH", "MEDIUM", "LOW", "UNCERTAIN"})
    features = {
        "stance_width": stance,
        "foot_depth": depth,
        "weight_distribution": weight,
        "knee_state": knee,
        "torso": torso,
        "shoulder_relation": shoulder,
        "arm_activity": arm,
        "head_angle": head,
        "energy_read": energy,
    }
    signals = _explicit_signals(values)
    if stance == "NARROW":
        signals.add("narrow stance width")
    if stance == "WIDE":
        signals.update(("wide stance width", "wide active stance"))
    if stance in {"NORMAL", "WIDE"}:
        signals.add("open stance width")
    if depth in {"FORWARD_LEFT", "FORWARD_RIGHT"}:
        signals.update(("clear forward foot depth", "balanced step response"))
    if weight in {"LEFT", "RIGHT"}:
        signals.update(("graceful weight distribution", "unequal weight distribution", "settled weight"))
    if knee in {"SOFT", "BENT"}:
        signals.add("softened knee")
    if torso in {"UPRIGHT", "TILTED"}:
        signals.update(("controlled posture", "clean torso line"))
    if torso in {"RELAXED", "TILTED", "FORWARD", "BACK"}:
        signals.update(("torso offset", "torso waist relationship"))
    if shoulder == "ASYMMETRIC":
        signals.update(("shoulder asymmetry", "composed shoulders"))
    if shoulder in {"LEVEL", "RELAXED", "ASYMMETRIC"}:
        signals.add("composed shoulders")
    if shoulder == "RELAXED":
        signals.add("lowered shoulders")
    if arm in {"RELAXED", "ASYMMETRIC", "CLOSED"}:
        signals.update(("refined arm placement", "arm placement"))
    if arm == "ASYMMETRIC":
        signals.add("asymmetric arm placement")
    if arm == "RELAXED":
        signals.add("quiet arm placement")
    if arm == "ACTIVE":
        signals.add("active body language")
    if head in {"TILTED", "TURNED"}:
        signals.update(("gaze head angle", "asymmetric head angle"))
    if head in {"NEUTRAL", "TILTED"}:
        signals.add("soft gaze")
    if torso == "RELAXED":
        signals.add("reduced torso tension")
    if weight in {"LEFT", "RIGHT"} and torso in {"TILTED", "FORWARD", "BACK"}:
        signals.update(("body confidence", "controlled hip orientation"))
    if shoulder == "RELAXED" or arm in {"RELAXED", "ASYMMETRIC"}:
        signals.add("relaxed shoulder")
    if any(
        (
            shoulder == "ASYMMETRIC",
            arm == "ASYMMETRIC",
            head in {"TILTED", "TURNED"},
            weight in {"LEFT", "RIGHT"},
        )
    ):
        signals.add("intentional body asymmetry")
    return signals, features


def _core_signals(intent: str) -> tuple[str, ...]:
    return {
        "ELEGANT": ("controlled posture", "refined arm placement", "intentional body asymmetry"),
        "SENSUAL": ("body confidence", "torso waist relationship", "controlled hip orientation", "gaze head angle"),
        "RELAXED_ASYMMETRIC": ("shoulder asymmetry", "unequal weight distribution", "asymmetric arm placement"),
        "LOW_ENERGY": ("lowered shoulders", "quiet arm placement", "reduced torso tension"),
    }.get(intent, ())


@dataclass(frozen=True)
class PoseIntentGateResult:
    actual_image: str
    requested_intent: str
    resolved_pose_family: str
    result: str
    overall_pose_intent_match: str
    contract: dict[str, Any]
    stance_width: str
    foot_depth: str
    weight_distribution: str
    knee_state: str
    torso: str
    shoulder_relation: str
    arm_activity: str
    head_angle: str
    energy_read: str
    matched_signals: tuple[str, ...] = ()
    missing_signals: tuple[str, ...] = ()
    failure_types: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    evidence_source: str = "human_actual_image_review"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PoseIntentGate:
    """Evaluate requested body language from actual-image observations."""

    def review(
        self,
        actual_image: str | Path,
        *,
        observations: Mapping[str, Any],
        contract: Mapping[str, Any] | PoseIntentContract | None = None,
        requested_intent: str | PoseIntentType | None = None,
    ) -> PoseIntentGateResult:
        image = Path(actual_image)
        if not image.is_file():
            raise ValueError("PoseIntentGate requires an existing actual image")
        values = _normalized_features(observations)
        if contract is None:
            contract = build_pose_intent_contract(
                requested_intent or values.get("requested_intent", "STABLE_OPEN"),
                resolved_pose_family=str(values.get("resolved_pose_family", "")),
            )
        normalized_contract = normalize_pose_intent_contract(contract)
        signals, features = _actual_signals(values)
        required = tuple(_canonical_signal(item) for item in normalized_contract.required_body_signals)
        matched = tuple(signal for signal in required if signal in signals)
        missing = tuple(signal for signal in required if signal not in signals)
        core_missing = [signal for signal in _core_signals(normalized_contract.requested_intent) if signal not in signals]
        issues: list[str] = []
        failures: list[str] = []
        intent = normalized_contract.requested_intent
        width = features["stance_width"]
        depth = features["foot_depth"]
        energy = features["energy_read"]
        if intent == "NARROW_STANCE" and width != "NARROW":
            failures.append(PoseIntentFailureType.NARROW_STANCE_EXPANDED.value)
            issues.append("requested narrow stance is not present in the actual image")
        if intent == "ONE_FOOT_FORWARD" and depth not in {"FORWARD_LEFT", "FORWARD_RIGHT"}:
            failures.append(PoseIntentFailureType.ONE_FOOT_FORWARD_DEPTH_MISSING.value)
            issues.append("requested forward foot depth is missing or same-plane")
        if intent == "LOW_ENERGY" and energy != "LOW":
            failures.append(PoseIntentFailureType.LOW_ENERGY_READ_MISSING.value)
            issues.append("actual energy read is not LOW")
        if intent == "RELAXED_ASYMMETRIC" and len(
            {signal for signal in _core_signals(intent) if signal in signals}
        ) < 2:
            failures.append(PoseIntentFailureType.RELAXED_ASYMMETRY_MISSING.value)
            issues.append("actual asymmetry is not sufficiently visible")
        if intent == "SENSUAL" and len(core_missing) >= 2 and bool(values.get("outfit_only_sensuality")):
            failures.append(PoseIntentFailureType.SENSUAL_POSE_REDUCED_TO_OUTFIT.value)
            issues.append("sensual read is carried by outfit rather than body language")
        if intent == "ELEGANT" and core_missing:
            failures.append(PoseIntentFailureType.ELEGANT_POSE_REDUCED_TO_NEUTRAL.value)
            issues.append("elegant body-language core is incomplete")
        if bool(values.get("leg_gate_result") == "PASS") and (missing or core_missing or failures):
            failures.append(PoseIntentFailureType.POSE_SAFETY_OVERCONSTRAINT.value)
            issues.append("leg safety passed but requested pose intent was materially lost")
        if intent == "UNKNOWN_LEGACY_POSE_INTENT":
            failures.append(PoseIntentFailureType.POSE_INTENT_FAIL.value)
            issues.append("legacy artifact has no reliable pose-intent mapping")
        threshold = normalized_contract.minimum_visible_signals
        enough = len(matched) >= threshold
        if not enough or core_missing or failures:
            result = "FAIL" if not enough or failures else "WEAK"
        else:
            result = "STRONG" if len(matched) == len(required) or not missing else "ACCEPTABLE"
        if result in {"WEAK", "FAIL"}:
            failures.insert(0, PoseIntentFailureType.POSE_INTENT_FAIL.value)
            failures.append(PoseIntentFailureType.POSE_SEMANTIC_EROSION.value)
        return PoseIntentGateResult(
            str(image),
            intent,
            normalized_contract.resolved_pose_family,
            result,
            result,
            normalized_contract.to_dict(),
            features["stance_width"],
            features["foot_depth"],
            features["weight_distribution"],
            features["knee_state"],
            features["torso"],
            features["shoulder_relation"],
            features["arm_activity"],
            features["head_angle"],
            features["energy_read"],
            tuple(dict.fromkeys(matched)),
            tuple(dict.fromkeys(missing + tuple(core_missing))),
            tuple(dict.fromkeys(failures)),
            tuple(dict.fromkeys(issues)),
        )


@dataclass(frozen=True)
class PoseValidationResult:
    overall_result: str
    leg_result: str
    pose_intent_result: str
    failure_types: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compose_pose_validation(leg_gate: Any, pose_intent_gate: PoseIntentGateResult) -> PoseValidationResult:
    leg_result = str(getattr(leg_gate, "result", leg_gate.get("result", "FAIL") if isinstance(leg_gate, Mapping) else "FAIL"))
    intent_result = pose_intent_gate.result
    leg_pass = leg_result == "PASS"
    intent_pass = intent_result in POSE_INTENT_PASS_RESULTS
    if leg_pass and intent_pass:
        overall = "POSE_VALID"
    elif leg_pass:
        overall = "POSE_INTENT_FAIL"
    elif intent_pass:
        overall = "FAIL"
    else:
        overall = "FAIL"
    failures = list(pose_intent_gate.failure_types)
    if not leg_pass:
        failures.append("LEG_SAFETY_FAIL")
    return PoseValidationResult(overall, leg_result, intent_result, tuple(dict.fromkeys(failures)))


MAX_POSE_INTENT_REPAIR = 1


def prepare_pose_intent_repair(
    final_design: Mapping[str, Any],
    pose_intent_gate: PoseIntentGateResult,
    pose_repair_count: int = 0,
) -> dict[str, Any]:
    """Plan a bounded body-language-only repair while preserving design identity."""
    if pose_intent_gate.result in POSE_INTENT_PASS_RESULTS:
        return {"status": "POSE_INTENT_ALREADY_VALID", "pose_repair_count": pose_repair_count}
    if pose_repair_count >= MAX_POSE_INTENT_REPAIR:
        return {
            "status": "POSE_INTENT_UNRESOLVED",
            "pose_repair_count": pose_repair_count,
            "preserve": tuple(final_design.keys()),
            "change_only": (
                "body language",
                "stance width",
                "foot depth",
                "torso",
                "shoulder",
                "arms",
                "head",
                "energy level",
            ),
            "revalidate_leg_separation_gate": True,
        }
    preserved = deepcopy(dict(final_design))
    return {
        "status": "POSE_INTENT_ONLY_REPAIR",
        "pose_repair_count": pose_repair_count + 1,
        "preserve": tuple(preserved.keys()),
        "change_only": (
            "body language",
            "stance width",
            "foot depth",
            "torso",
            "shoulder",
            "arms",
            "head",
            "energy level",
        ),
        "revalidate_leg_separation_gate": True,
        "design_snapshot": preserved,
    }


POSE_DIVERSITY_FIELDS = (
    "stance_width",
    "foot_depth",
    "weight_distribution",
    "knee_state",
    "torso",
    "shoulder_relation",
    "arm_activity",
    "head_angle",
    "energy_read",
)


@dataclass
class PoseDiversityLedger:
    records: list[dict[str, Any]] = field(default_factory=list)

    def add(self, record: Mapping[str, Any]) -> dict[str, Any]:
        normalized = {name: record.get(name, "UNCERTAIN") for name in POSE_DIVERSITY_FIELDS}
        normalized.update({key: value for key, value in record.items() if key not in normalized})
        self.records.append(deepcopy(normalized))
        return deepcopy(normalized)

    def to_dict(self) -> dict[str, Any]:
        return {"fields": POSE_DIVERSITY_FIELDS, "records": deepcopy(self.records)}

    def homogenization(self, *, user_requested_uniform: bool = False, minimum_repetition: int = 2) -> dict[str, Any]:
        return detect_safe_pose_homogenization(
            self.records,
            user_requested_uniform=user_requested_uniform,
            minimum_repetition=minimum_repetition,
        )


def detect_safe_pose_homogenization(
    records: list[Mapping[str, Any]],
    *,
    user_requested_uniform: bool = False,
    minimum_repetition: int = 2,
) -> dict[str, Any]:
    if user_requested_uniform or len(records) < minimum_repetition:
        return {
            "result": "NONE",
            "detected_fields": [],
            "repetition_count": 0,
            "hard_gate": False,
            "user_requested_uniform": user_requested_uniform,
        }
    detected: list[str] = []
    for field_name in POSE_DIVERSITY_FIELDS:
        values = [record.get(field_name, "UNCERTAIN") for record in records]
        if len(set(map(str, values))) == 1:
            detected.append(field_name)
    signatures = [tuple(str(record.get(name, "UNCERTAIN")) for name in POSE_DIVERSITY_FIELDS) for record in records]
    counts = {signature: signatures.count(signature) for signature in set(signatures)}
    repetition_count = max(counts.values(), default=0)
    result = "SAFE_POSE_HOMOGENIZATION" if len(detected) >= 5 or repetition_count >= minimum_repetition else "NONE"
    return {
        "result": result,
        "detected_fields": detected,
        "repetition_count": repetition_count,
        "hard_gate": False,
        "user_requested_uniform": user_requested_uniform,
    }
