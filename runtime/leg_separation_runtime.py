"""Hard no-crossed-legs invariant, pose planning, and actual-image gate."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
import re
from typing import Any, Mapping

try:
    from .pose_intent_runtime import migrate_pose_intent_fields
except ImportError:  # pragma: no cover - supports direct host imports
    from pose_intent_runtime import migrate_pose_intent_fields  # type: ignore


NO_CROSSED_LEGS_HARD_INVARIANT = True
MAX_LEG_POSE_REPAIR = 1


class LegSeparationError(ValueError):
    """Raised when a pose or candidate violates the hard leg invariant."""


class LegFailureType(str, Enum):
    LEG_CROSSING_BLOCKING_FAIL = "LEG_CROSSING_BLOCKING_FAIL"
    THIGH_CROSSING_FAIL = "THIGH_CROSSING_FAIL"
    KNEE_CROSSING_FAIL = "KNEE_CROSSING_FAIL"
    CALF_CROSSING_FAIL = "CALF_CROSSING_FAIL"
    ANKLE_CROSSING_FAIL = "ANKLE_CROSSING_FAIL"
    LEG_CENTERLINE_CROSSING_FAIL = "LEG_CENTERLINE_CROSSING_FAIL"
    LEG_OCCLUSION_UNCERTAIN = "LEG_OCCLUSION_UNCERTAIN"
    SAFE_POSE_PRIOR_OVERRIDE_FAIL = "SAFE_POSE_PRIOR_OVERRIDE_FAIL"


@dataclass(frozen=True)
class LegSeparationContract:
    thighs_separate: bool = True
    knees_separate: bool = True
    calves_separate: bool = True
    ankles_separate: bool = True
    feet_separate: bool = True
    no_centerline_crossing: bool = True
    no_leg_occlusion_crossing: bool = True
    readable_negative_space: bool = True

    def __post_init__(self) -> None:
        if not all(asdict(self).values()):
            raise LegSeparationError("LegSeparationContract is a hard all-true invariant")

    def to_dict(self) -> dict[str, bool]:
        return asdict(self)


DEFAULT_LEG_SEPARATION_CONTRACT = LegSeparationContract()


@dataclass(frozen=True)
class PoseFamilySpec:
    name: str
    leg_crossing_risk: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


POSE_FAMILIES: dict[str, PoseFamilySpec] = {
    "OPEN_PARALLEL_STANCE": PoseFamilySpec(
        "OPEN_PARALLEL_STANCE", "LOW", "natural separated stance with both legs in their own lanes"
    ),
    "OFFSET_NON_OVERLAPPING_STANCE": PoseFamilySpec(
        "OFFSET_NON_OVERLAPPING_STANCE", "LOW", "one foot may be slightly forward without lane crossover"
    ),
    "ASYMMETRIC_WEIGHT_STANCE": PoseFamilySpec(
        "ASYMMETRIC_WEIGHT_STANCE", "LOW", "weight shifts to one side while thighs, knees, calves, and ankles stay separate"
    ),
    "WIDE_ACTIVE_STANCE": PoseFamilySpec(
        "WIDE_ACTIVE_STANCE", "LOW", "active wide stance with independent left and right leg lanes"
    ),
    "NARROW_SEPARATED_STANCE": PoseFamilySpec(
        "NARROW_SEPARATED_STANCE", "LOW", "narrow stance with a visible gap and no leg overlap"
    ),
    "LOW_ENERGY_SEPARATED_STANCE": PoseFamilySpec(
        "LOW_ENERGY_SEPARATED_STANCE", "LOW", "quiet separated stance with low energy and readable legs"
    ),
    "FORWARD_STEP_NON_CROSSING": PoseFamilySpec(
        "FORWARD_STEP_NON_CROSSING", "LOW", "forward step constrained to the same lateral lane"
    ),
    "FORBIDDEN_CROSSED_STANCE": PoseFamilySpec(
        "FORBIDDEN_CROSSED_STANCE", "FORBIDDEN", "crossed, scissored, or intertwined leg geometry"
    ),
}

_FORBIDDEN_POSE_PHRASES = (
    "crossed-leg",
    "crossed leg",
    "crossed legs",
    "crossed thigh",
    "crossed knee",
    "crossed calf",
    "crossed ankle",
    "scissor stance",
    "scissor-leg",
    "scissor leg",
    "intertwined leg",
    "leg-over-leg",
    "leg over leg",
    "ankle-cross",
    "ankle cross",
    "coy leg pose",
    "inward crossed",
    "one leg passing across the centerline",
    "one leg crossing in front",
    "fashion-model crossed",
    "fashion model crossed",
    "closed-leg twist",
)
_RISKY_POSE_PHRASES = (
    "fashion stance",
    "model stance",
    "elegant crossed stance",
    "demure crossed stance",
    "graceful crossed pose",
    "seductive crossed stance",
)

LEG_GEOMETRY_POSITIVE = (
    "both legs clearly separated",
    "both thighs independently readable",
    "both knees independently readable",
    "both calves independently readable",
    "both ankles independently readable",
    "both feet independently readable",
    "visible negative space between the legs",
    "neither leg passes across the other",
    "neither leg overlaps the other",
    "stable non-crossing stance",
)
LEG_GEOMETRY_NEGATIVE = (
    "no crossed legs",
    "no crossed thighs",
    "no crossed knees",
    "no crossed calves",
    "no crossed ankles",
    "no scissor stance",
    "no intertwined legs",
    "no overlapping leg silhouette",
    "no one-leg-in-front-of-the-other crossing",
    "no fashion-model crossed-leg pose",
)


def _text(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    return str(value)


def _contains_phrase(text: str, phrases: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def rewrite_conflicting_pose_language(text: str) -> str:
    """Rewrite style language that commonly activates a crossed-leg prior."""
    result = str(text)
    replacements = {
        "elegant model pose": "elegant separated stance",
        "fashion model stance": "fashion stance with separated legs",
        "fashion stance": "fashion-forward separated stance",
        "model stance": "model-like separated stance",
        "coy stance": "coy separated stance",
        "closed-leg twist": "closed but separated stance",
        "ankle-cross pose": "ankle-separated pose",
        "coy leg pose": "coy separated-leg pose",
        "leg-over-leg standing": "separated-leg standing",
        "inward crossed pose": "inward-facing separated stance",
        "seductive stance": "seductive separated stance",
        "relaxed feminine stance": "relaxed feminine stance with stable separated-leg geometry",
        "fashion-model crossed-leg pose": "fashion pose with separated legs",
        "fashion model crossed-leg pose": "fashion pose with separated legs",
        "elegant crossed stance": "elegant separated stance",
        "demure crossed stance": "demure separated stance",
        "graceful crossed pose": "graceful separated pose",
        "seductive crossed stance": "seductive separated stance",
        "crossed-leg": "separated-leg",
        "crossed legs": "separated legs",
        "crossed leg": "separated leg",
        "crossed ankles": "separated ankles",
        "scissor stance": "separated stance",
        "intertwined legs": "separated legs",
    }
    for source, replacement in replacements.items():
        result = re.sub(re.escape(source), replacement, result, flags=re.IGNORECASE)
    return result


def _infer_pose_family(text: str) -> str:
    lowered = text.lower()
    if _contains_phrase(lowered, _FORBIDDEN_POSE_PHRASES):
        return "FORBIDDEN_CROSSED_STANCE"
    if "wide" in lowered or "active" in lowered or "athletic" in lowered:
        return "WIDE_ACTIVE_STANCE"
    if "narrow" in lowered:
        return "NARROW_SEPARATED_STANCE"
    if "low energy" in lowered or "quiet" in lowered or "still" in lowered:
        return "LOW_ENERGY_SEPARATED_STANCE"
    if "forward" in lowered or "step" in lowered:
        return "FORWARD_STEP_NON_CROSSING"
    if "asymmetric" in lowered or "asymmetrical" in lowered or "weight" in lowered or "elegant" in lowered:
        return "ASYMMETRIC_WEIGHT_STANCE"
    return "OPEN_PARALLEL_STANCE"


def validate_pose_description(pose_description: str, pose_family: str | None = None) -> str:
    """Reject crossed-leg language before it can reach PromptCompiler."""
    text = _text(pose_description).strip()
    if _contains_phrase(text, _FORBIDDEN_POSE_PHRASES) or _contains_phrase(text, _RISKY_POSE_PHRASES):
        raise LegSeparationError("VALIDATION_ERROR: pose language conflicts with the hard no-crossed-legs invariant")
    family = pose_family or _infer_pose_family(text)
    if family not in POSE_FAMILIES:
        raise LegSeparationError(f"unknown pose family: {family}")
    if POSE_FAMILIES[family].leg_crossing_risk == "FORBIDDEN":
        raise LegSeparationError(f"VALIDATION_ERROR: pose family {family} is forbidden")
    return family


def leg_geometry_constraints(pose_family: str) -> tuple[str, ...]:
    """Return positive geometry wording tuned to a safe pose family."""
    family = POSE_FAMILIES.get(pose_family)
    if family is None or family.leg_crossing_risk == "FORBIDDEN":
        raise LegSeparationError(f"pose family {pose_family} cannot receive a leg contract")
    additions = {
        "WIDE_ACTIVE_STANCE": ("wide stance is allowed, but each leg stays in its own lateral lane",),
        "NARROW_SEPARATED_STANCE": ("narrow stance is allowed only with a visible gap between both leg chains",),
        "FORWARD_STEP_NON_CROSSING": ("one foot may be slightly forward only inside its own lateral lane",),
    }
    return LEG_GEOMETRY_POSITIVE + additions.get(pose_family, ())


def normalize_leg_separation_contract(value: Mapping[str, Any] | None = None) -> LegSeparationContract:
    if value is None:
        return DEFAULT_LEG_SEPARATION_CONTRACT
    expected = DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
    for name in expected:
        if value.get(name, True) is not True:
            raise LegSeparationError(f"leg separation contract cannot disable {name}")
    return DEFAULT_LEG_SEPARATION_CONTRACT


@dataclass(frozen=True)
class LegSeparationGateResult:
    actual_image: str
    result: str
    contract: dict[str, bool]
    thigh_relation: str
    knee_relation: str
    calf_relation: str
    ankle_relation: str
    foot_relation: str
    centerline_crossing: bool | None
    leg_negative_space: bool | None
    failure_types: tuple[str, ...] = ()
    issues: tuple[str, ...] = ()
    evidence_source: str = "human_actual_image_review"
    stance_family: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_RELATION_KEYS = {
    "thigh_relation": LegFailureType.THIGH_CROSSING_FAIL.value,
    "knee_relation": LegFailureType.KNEE_CROSSING_FAIL.value,
    "calf_relation": LegFailureType.CALF_CROSSING_FAIL.value,
    "ankle_relation": LegFailureType.ANKLE_CROSSING_FAIL.value,
    "foot_relation": LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value,
}
_SEPARATE_VALUES = {"separate", "separated", "clear", "readable", "pass", "none", "no"}
_CROSSED_VALUES = {"crossed", "overlap", "overlapping", "blocked", "fail", "yes", "true"}
_UNCERTAIN_VALUES = {"uncertain", "unknown", "occluded", "not visible", ""}


def _relation_state(value: Any) -> str:
    if isinstance(value, bool):
        return "crossed" if value else "separate"
    lowered = _text(value).strip().lower()
    if lowered in _SEPARATE_VALUES or any(token in lowered for token in ("separate", "independent", "readable")):
        return "separate"
    if lowered in _CROSSED_VALUES or any(token in lowered for token in ("cross", "overlap", "intertwine")):
        return "crossed"
    if lowered in _UNCERTAIN_VALUES:
        return "uncertain"
    return "uncertain"


def _bool_state(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    lowered = _text(value).strip().lower()
    if lowered in {"true", "yes", "pass", "clear", "present"}:
        return True
    if lowered in {"false", "no", "fail", "absent"}:
        return False
    return None


class LegSeparationGate:
    """Actual-image hard gate; UNCERTAIN is non-promotable."""

    def review(
        self,
        actual_image: str | Path,
        *,
        observations: Mapping[str, Any],
        contract: Mapping[str, Any] | None = None,
    ) -> LegSeparationGateResult:
        image = Path(actual_image)
        if not image.is_file():
            raise LegSeparationError("LegSeparationGate requires an existing actual image")
        normalize_leg_separation_contract(contract)
        relations = {name: _relation_state(observations.get(name)) for name in _RELATION_KEYS}
        centerline = _bool_state(observations.get("centerline_crossing"))
        negative_space = _bool_state(observations.get("leg_negative_space"))
        failures: list[str] = []
        issues: list[str] = []
        uncertain = False
        for name, failure in _RELATION_KEYS.items():
            state = relations[name]
            if state == "crossed":
                failures.extend((failure, LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value))
                issues.append(f"{name} is crossed or overlapping")
            elif state == "uncertain":
                uncertain = True
                issues.append(f"{name} is not independently readable")
        if centerline is True:
            failures.extend((LegFailureType.LEG_CENTERLINE_CROSSING_FAIL.value, LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value))
            issues.append("a leg crosses the body centerline")
        elif centerline is None:
            uncertain = True
            issues.append("centerline crossing is uncertain")
        if negative_space is False:
            failures.extend((LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value, LegFailureType.LEG_OCCLUSION_UNCERTAIN.value))
            issues.append("leg negative space is absent")
        elif negative_space is None:
            uncertain = True
            issues.append("leg negative space is uncertain")
        if _bool_state(observations.get("safe_pose_prior_override_fail")) is True:
            failures.append(LegFailureType.SAFE_POSE_PRIOR_OVERRIDE_FAIL.value)
            issues.append("the actual image reverted to a crossed-leg prior despite a safe pose specification")
        if failures:
            result = "FAIL"
        elif uncertain:
            failures.append(LegFailureType.LEG_OCCLUSION_UNCERTAIN.value)
            result = "UNCERTAIN"
        else:
            result = "PASS"
        return LegSeparationGateResult(
            str(image),
            result,
            DEFAULT_LEG_SEPARATION_CONTRACT.to_dict(),
            relations["thigh_relation"],
            relations["knee_relation"],
            relations["calf_relation"],
            relations["ankle_relation"],
            relations["foot_relation"],
            centerline,
            negative_space,
            tuple(dict.fromkeys(failures)),
            tuple(issues),
            stance_family=_text(observations.get("stance_family", observations.get("pose_family", ""))),
        )


def candidate_promotion_status(
    gate: LegSeparationGateResult,
    *,
    first_pass_benchmark: bool = False,
    pose_intent_gate: Any | None = None,
) -> str:
    if gate.result == "PASS":
        pose_result = (
            getattr(pose_intent_gate, "result", None)
            if pose_intent_gate is not None
            else None
        )
        if isinstance(pose_intent_gate, Mapping):
            pose_result = pose_intent_gate.get("result")
        if pose_intent_gate is not None and pose_result not in {"STRONG", "ACCEPTABLE"}:
            return "POSE_INTENT_FAIL"
        return "PROMOTED_TO_CANDIDATE"
    if first_pass_benchmark:
        if any(
            failure in gate.failure_types
            for failure in (
                LegFailureType.LEG_CROSSING_BLOCKING_FAIL.value,
                LegFailureType.SAFE_POSE_PRIOR_OVERRIDE_FAIL.value,
            )
        ):
            return "FIRST_PASS_LEG_CROSSING_FAIL"
        return "FIRST_PASS_LEG_GEOMETRY_UNCERTAIN"
    return "REJECTED_BY_HARD_ANATOMY_GATE"


def promote_candidate(
    gate: LegSeparationGateResult,
    *,
    first_pass_benchmark: bool = False,
    pose_intent_gate: Any | None = None,
) -> dict[str, Any]:
    status = candidate_promotion_status(
        gate,
        first_pass_benchmark=first_pass_benchmark,
        pose_intent_gate=pose_intent_gate,
    )
    return {
        "candidate_promotion_status": status,
        "promoted": status == "PROMOTED_TO_CANDIDATE",
        "blocking": status != "PROMOTED_TO_CANDIDATE",
        "leg_separation_gate": gate.to_dict(),
        "pose_intent_gate": (
            pose_intent_gate.to_dict()
            if hasattr(pose_intent_gate, "to_dict")
            else pose_intent_gate
        ),
    }


def prepare_pose_only_repair(final_design: Mapping[str, Any], pose_repair_count: int) -> dict[str, Any]:
    """Allow one pose-only regeneration while preserving every design identity field."""
    if pose_repair_count >= MAX_LEG_POSE_REPAIR:
        return {
            "status": "LEG_GEOMETRY_UNRESOLVED",
            "pose_repair_count": pose_repair_count,
            "preserve": tuple(final_design.keys()),
            "change_only": ("stance", "leg geometry"),
        }
    preserved = deepcopy(dict(final_design))
    return {
        "status": "POSE_ONLY_REGENERATION",
        "pose_repair_count": pose_repair_count + 1,
        "preserve": tuple(preserved.keys()),
        "change_only": ("stance", "leg geometry"),
        "positive_geometry": LEG_GEOMETRY_POSITIVE,
        "negative_geometry": LEG_GEOMETRY_NEGATIVE,
        "design_snapshot": preserved,
    }


def validate_pose_options(options: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Fail closed for user-visible pose options before Human selection."""
    normalized: list[dict[str, Any]] = []
    for option in options:
        item = dict(option)
        description = _text(item.get("pose_description", item.get("value", "")))
        family = validate_pose_description(description, item.get("pose_family"))
        item["pose_family"] = family
        item["leg_crossing_risk"] = POSE_FAMILIES[family].leg_crossing_risk
        item["leg_separation_contract"] = DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
        normalized.append(item)
    return normalized


def validate_final_design(final_design: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the Final Design handoff before PromptCompiler."""
    if not isinstance(final_design, Mapping):
        raise LegSeparationError("VALIDATION_ERROR: Final Design must be an object")
    normalized = deepcopy(dict(final_design))
    description = _text(normalized.get("pose_description", normalized.get("pose", "stable standard standee stance")))
    family = validate_pose_description(description, normalized.get("pose_family"))
    normalized["pose_family"] = family
    normalized["leg_crossing_risk"] = POSE_FAMILIES[family].leg_crossing_risk
    normalized["leg_separation_contract"] = DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
    normalized["pose_description"] = rewrite_conflicting_pose_language(description)
    pose_intent_fields, _ = migrate_pose_intent_fields(normalized)
    normalized["pose_intent"] = pose_intent_fields["pose_intent"]
    normalized["pose_intent_contract"] = pose_intent_fields["pose_intent_contract"]
    return normalized


def audit_leg_prompt(prompt: str) -> dict[str, Any]:
    """Fail the Prompt Audit when any hard leg section is missing."""
    text = str(prompt)
    positive = all(item in text for item in LEG_GEOMETRY_POSITIVE)
    negative = all(item in text for item in LEG_GEOMETRY_NEGATIVE)
    contract = "## LEG GEOMETRY / ANATOMY CONSTRAINT" in text
    pose_safe = "Leg Crossing Risk: FORBIDDEN" not in text
    pose_section = text.split("## LEG GEOMETRY / ANATOMY CONSTRAINT", 1)[0]
    conflicting = not _contains_phrase(pose_section, _FORBIDDEN_POSE_PHRASES)
    return {
        "leg_separation_contract_present": contract,
        "positive_leg_geometry_present": positive,
        "negative_cross_leg_constraint_present": negative,
        "pose_family_safe": pose_safe,
        "conflicting_pose_language_absent": conflicting,
        "passed": all((contract, positive, negative, pose_safe, conflicting)),
    }


def migrate_leg_separation_fields(artifact: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Attach the current hard invariant to legacy artifacts without mutating them."""
    migrated = deepcopy(dict(artifact))
    event = None
    if "leg_separation_contract" not in migrated:
        migrated["leg_separation_contract"] = DEFAULT_LEG_SEPARATION_CONTRACT.to_dict()
        event = {
            "event": "leg_separation_contract_migration",
            "audit_event": "NO_CROSSED_LEGS_HARD_INVARIANT_MIGRATION",
            "old_artifact_version": migrated.get("schema_version", "unknown"),
        }
    if "pose_family" not in migrated:
        description = _text(migrated.get("pose", migrated.get("pose_description", "")))
        migrated["pose_family"] = _infer_pose_family(description)
        event = event or {
            "event": "pose_family_migration",
            "audit_event": "POSE_FAMILY_DEFAULT_MIGRATION",
            "old_artifact_version": migrated.get("schema_version", "unknown"),
        }
    return migrated, event
