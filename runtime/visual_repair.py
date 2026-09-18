"""Targeted, manifest-driven visual repair planning and review comparison.

This module deliberately does not inspect pixels or call ImageGen.  It turns
an existing VisualAdherenceCritic result into a bounded repair prompt and
compares the externally observed follow-up result.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from .adherence_policy import evaluate_adherence_disposition
    from .visual_adherence_critic import RESULTS, VisualAdherenceReview
except ImportError:  # pragma: no cover - supports direct host imports
    from adherence_policy import evaluate_adherence_disposition  # type: ignore
    from visual_adherence_critic import RESULTS, VisualAdherenceReview  # type: ignore


MAX_REPAIR_ATTEMPTS = 2
REPAIR_SEVERITIES = ("CRITICAL", "MAJOR", "MINOR", "INFORMATIONAL", "IGNORE")
REPAIR_OUTCOMES = ("SUCCESS", "PARTIAL_SUCCESS", "NO_IMPROVEMENT", "REGRESSION", "FAILED")
REPAIR_STATUSES = (
    "GENERATION_READY",
    "IMAGE_GENERATED",
    "ADHERENCE_REVIEWED",
    "REPAIR_PLANNED",
    "REPAIR_GENERATED",
    "REPAIR_REVIEWED",
    "ACCEPTED",
    "REPAIR_EXHAUSTED",
)


class VisualRepairError(ValueError):
    """Raised when a repair plan or attempt cannot be safely formed."""


def _mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise VisualRepairError("visual repair inputs must be mappings")
    return value


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


def _image_hash(path: str | Path) -> str | None:
    image = Path(path)
    if not image.is_file():
        return None
    return sha256(image.read_bytes()).hexdigest()


def review_id(review: VisualAdherenceReview | Mapping[str, Any]) -> str:
    data = _mapping(review)
    existing = data.get("review_id")
    if existing:
        return str(existing)
    return _canonical_hash(
        {
            "actual_image": data.get("actual_image"),
            "actual_image_hash": data.get("actual_image_hash"),
            "prompt_hash": data.get("prompt_hash"),
            "generation_id": data.get("generation_id"),
            "field_results": data.get("field_results", {}),
            "anatomy_check": data.get("anatomy_check", {}),
        }
    )


def _result(value: Any) -> str:
    normalized = str(value or "NOT_EVALUABLE").upper()
    return normalized if normalized in RESULTS else "NOT_EVALUABLE"


def _failure_types(target: Mapping[str, Any]) -> tuple[str, ...]:
    values = target.get("failure_types", ())
    if isinstance(values, str):
        values = (values,)
    return tuple(str(item).upper() for item in values)


def _field_set(*sources: Any) -> set[str]:
    result: set[str] = set()
    for source in sources:
        if isinstance(source, Mapping):
            result.update(str(name) for name in source)
        elif source:
            result.update(str(name) for name in source)
    return result


def _contract_data(contract: Mapping[str, Any] | None) -> Mapping[str, Any]:
    return _mapping(contract) if contract is not None else {}


def _severity(
    target: Mapping[str, Any],
    *,
    explicit_fields: set[str],
    required_strict_fields: set[str],
    anti_substitution_fields: set[str],
) -> str:
    field = str(target.get("field", ""))
    result = _result(target.get("result", target.get("status")))
    if field in explicit_fields:
        return "CRITICAL"
    if result == "FAIL":
        return "MAJOR"
    if result == "PARTIAL" and (field in required_strict_fields or field in anti_substitution_fields):
        return "MAJOR"
    if result == "PARTIAL":
        return "MINOR"
    return "IGNORE"


def _instruction(target: Mapping[str, Any], locked_fields: Mapping[str, Any]) -> dict[str, Any]:
    field = str(target.get("field", ""))
    required = target.get("required")
    observed = target.get("observed")
    failures = _failure_types(target)
    if field == "face_aesthetic_profile":
        text = (
            f"Restore the face to {required}. Reduce western facial-bone emphasis and prevent semi-realistic western portrait drift. Preserve costume, silhouette, pose, props, palette, and background exactly."
            if "EAST_ASIAN" in str(required)
            else f"Restore the face to {required} within contemporary commercial gacha anime. Do not convert the full rendering language into western realistic illustration. Preserve costume, silhouette, pose, props, palette, and background exactly."
        )
        return {"field": field, "strategy": "replacement", "text": text, "locked_field_names": sorted(locked_fields)}
    if field == "facial_style_drift":
        return {
            "field": field,
            "strategy": "strengthen_only",
            "text": "Correct only facial style drift and restore the contracted face aesthetic. Preserve costume, silhouette, pose, props, palette, and background exactly.",
            "locked_field_names": sorted(locked_fields),
        }
    if "TYPE 3" in failures:
        if field == "footwear_category" and "combat boot" in str(required).lower():
            prohibition = "Do not use heels, stilettos, pumps, or generic high heels."
        elif field == "footwear_category" and "barefoot" in str(required).lower():
            prohibition = "Do not use shoes, boots, heels, pumps, or stilettos."
        else:
            prohibition = f"Do not repeat the observed substitution: {observed}."
        text = f"Replace the incorrect {field} with {required}. {prohibition} Preserve all other design elements exactly."
        strategy = "replacement"
    elif "TYPE 4" in failures:
        text = f"Strengthen only {field}: make {required} visibly clear. Keep all other design elements unchanged."
        strategy = "strengthen_only"
    else:
        text = f"Correct only {field} to {required}. Preserve all other design elements exactly."
        strategy = "targeted_correction"
    return {"field": field, "strategy": strategy, "text": text, "locked_field_names": sorted(locked_fields)}


@dataclass(frozen=True)
class VisualRepairPlan:
    source_image: str
    source_prompt_hash: str | None
    source_review_id: str
    repair_attempt: int
    repair_targets: tuple[dict[str, Any], ...]
    locked_fields: dict[str, Any]
    preserve_fields: dict[str, Any]
    repair_instructions: tuple[dict[str, Any], ...]
    anti_regression_constraints: tuple[dict[str, Any], ...]
    max_attempts: int = MAX_REPAIR_ATTEMPTS
    source_image_hash: str | None = None
    attempt_id: str = ""
    source_generation_id: str | None = None
    face_aesthetic_contract: dict[str, Any] = field(default_factory=dict)
    actionable_repair_targets: tuple[dict[str, Any], ...] = ()
    informational_deviations: tuple[dict[str, Any], ...] = ()
    adherence_disposition: dict[str, Any] | None = None
    repair_trigger_decision: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.repair_attempt < 1:
            raise VisualRepairError("repair_attempt must start at 1")
        if self.max_attempts < 1:
            raise VisualRepairError("max_attempts must be positive")
        if self.repair_attempt > self.max_attempts:
            raise VisualRepairError("REPAIR_EXHAUSTED")
        if not self.attempt_id:
            object.__setattr__(self, "attempt_id", f"{self.source_review_id}:attempt:{self.repair_attempt}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_image": self.source_image,
            "source_image_hash": self.source_image_hash,
            "source_prompt_hash": self.source_prompt_hash,
            "source_generation_id": self.source_generation_id,
            "source_review_id": self.source_review_id,
            "repair_attempt": self.repair_attempt,
            "attempt_id": self.attempt_id,
            "repair_targets": deepcopy(list(self.repair_targets)),
            "locked_fields": deepcopy(self.locked_fields),
            "preserve_fields": deepcopy(self.preserve_fields),
            "repair_instructions": deepcopy(list(self.repair_instructions)),
            "anti_regression_constraints": deepcopy(list(self.anti_regression_constraints)),
            "max_attempts": self.max_attempts,
            "face_aesthetic_contract": deepcopy(self.face_aesthetic_contract),
            "actionable_repair_targets": deepcopy(list(self.actionable_repair_targets or self.repair_targets)),
            "informational_deviations": deepcopy(list(self.informational_deviations)),
            "adherence_disposition": deepcopy(self.adherence_disposition),
            "repair_trigger_decision": deepcopy(self.repair_trigger_decision),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VisualRepairPlan":
        return cls(
            source_image=str(data.get("source_image", "")),
            source_image_hash=data.get("source_image_hash"),
            source_prompt_hash=data.get("source_prompt_hash"),
            source_generation_id=data.get("source_generation_id"),
            source_review_id=str(data.get("source_review_id", "")),
            repair_attempt=int(data.get("repair_attempt", 1)),
            attempt_id=str(data.get("attempt_id", "")),
            repair_targets=tuple(deepcopy(data.get("repair_targets", ()))),
            locked_fields=deepcopy(dict(data.get("locked_fields") or {})),
            preserve_fields=deepcopy(dict(data.get("preserve_fields") or {})),
            repair_instructions=tuple(deepcopy(data.get("repair_instructions", ()))),
            anti_regression_constraints=tuple(deepcopy(data.get("anti_regression_constraints", ()))),
            max_attempts=int(data.get("max_attempts", MAX_REPAIR_ATTEMPTS)),
            face_aesthetic_contract=deepcopy(dict(data.get("face_aesthetic_contract") or {})),
            actionable_repair_targets=tuple(deepcopy(data.get("actionable_repair_targets", data.get("repair_targets", ())))),
            informational_deviations=tuple(deepcopy(data.get("informational_deviations", ()))),
            adherence_disposition=deepcopy(dict(data.get("adherence_disposition") or {})) if data.get("adherence_disposition") is not None else None,
            repair_trigger_decision=deepcopy(dict(data.get("repair_trigger_decision") or {})) if data.get("repair_trigger_decision") is not None else None,
        )


@dataclass(frozen=True)
class RepairPromptBundle:
    prompt: str
    original_prompt: str
    source_prompt_hash: str | None
    prompt_hash: str
    repair_plan: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "original_prompt": self.original_prompt,
            "source_prompt_hash": self.source_prompt_hash,
            "prompt_hash": self.prompt_hash,
            "repair_plan": deepcopy(self.repair_plan),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RepairPromptBundle":
        return cls(
            str(data.get("prompt", "")),
            str(data.get("original_prompt", "")),
            data.get("source_prompt_hash"),
            str(data.get("prompt_hash", "")),
            deepcopy(dict(data.get("repair_plan") or {})),
        )


def build_repair_plan(
    review: VisualAdherenceReview | Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] | None = None,
    visual_specification_contract: Mapping[str, Any] | None = None,
    explicit_hard_fields: tuple[str, ...] | list[str] = (),
    required_strict_fields: tuple[str, ...] | list[str] = (),
    repair_attempt: int = 1,
    max_attempts: int = MAX_REPAIR_ATTEMPTS,
    include_minor: bool = True,
    generation_artifact: Mapping[str, Any] | None = None,
    final_design: Mapping[str, Any] | None = None,
    manual_repair_fields: Sequence[str] = (),
) -> VisualRepairPlan:
    """Build only from policy-approved actionable targets and current-run data."""
    data = _mapping(review)
    if generation_artifact is not None:
        artifact = _mapping(generation_artifact)
        source_image = str(data.get("actual_image", ""))
        image_hash = data.get("actual_image_hash") or _image_hash(source_image)
        if artifact.get("image_hash") != image_hash or (data.get("actual_image_hash") and artifact.get("image_hash") != data.get("actual_image_hash")):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: image hash")
        if artifact.get("prompt_hash") != data.get("prompt_hash"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: prompt hash")
        if artifact.get("generation_id") != data.get("generation_id"):
            raise VisualRepairError("REPAIR_SOURCE_MISMATCH: generation id")
    contract = _contract_data(visual_specification_contract)
    manifest_data = _mapping(manifest) if manifest is not None else {}
    hard_sources = [
        manifest_data.get("face_aesthetic_contract"),
        contract.get("face_aesthetic_contract"),
        manifest_data.get("hard_constraints"),
        manifest_data.get("pose_specification"),
        manifest_data.get("background_specification"),
        contract.get("hard_constraints"),
        contract.get("pose_specification"),
        contract.get("background_specification"),
    ]
    hard_fields = _field_set(*hard_sources)
    strong_fields = _field_set(manifest_data.get("strong_preferences"), contract.get("strong_preferences"))
    explicit_fields = _field_set(explicit_hard_fields, contract.get("explicit_hard_fields"))
    strict_fields = _field_set(required_strict_fields)
    anti_fields = _field_set(contract.get("anti_substitution"))
    field_results = data.get("field_results") if isinstance(data.get("field_results"), Mapping) else {}

    stored_disposition = data.get("adherence_disposition")
    stored_trigger = data.get("repair_trigger_decision")
    if manual_repair_fields or not isinstance(stored_disposition, Mapping):
        disposition = evaluate_adherence_disposition(
            data,
            manifest=manifest_data,
            visual_specification_contract=contract,
            final_design=final_design,
            manual_repair_fields=manual_repair_fields,
        ).to_dict()
        stored_disposition = disposition
        stored_trigger = disposition["repair_trigger_decision"]
    else:
        disposition = deepcopy(dict(stored_disposition))
    trigger = stored_trigger if isinstance(stored_trigger, Mapping) else disposition.get("repair_trigger_decision", {})
    actionable_source = trigger.get("actionable_repair_targets") if isinstance(trigger, Mapping) else None
    informational = trigger.get("informational_deviations", ()) if isinstance(trigger, Mapping) else ()
    if actionable_source is None:
        actionable_source = disposition.get("actionable_repair_targets", ())

    targets: list[dict[str, Any]] = []
    for raw_target in actionable_source or ():
        if not isinstance(raw_target, Mapping) or not raw_target.get("field"):
            continue
        target = deepcopy(dict(raw_target))
        field = str(target["field"])
        if field in field_results and isinstance(field_results[field], Mapping):
            target.setdefault("result", field_results[field].get("result"))
            target.setdefault("required", field_results[field].get("required"))
            target.setdefault("observed", field_results[field].get("observed"))
        importance = str(target.get("repair_importance") or "").upper()
        severity = importance if importance in REPAIR_SEVERITIES else _severity(
            target,
            explicit_fields=explicit_fields,
            required_strict_fields=strict_fields,
            anti_substitution_fields=anti_fields,
        )
        if severity in {"MINOR", "INFORMATIONAL", "IGNORE"} and not include_minor:
            continue
        target["repair_severity"] = severity
        target.setdefault("repair_importance", "INFORMATIONAL" if severity == "IGNORE" else severity)
        targets.append(target)

    if repair_attempt > max_attempts:
        raise VisualRepairError("REPAIR_EXHAUSTED")

    locked: dict[str, Any] = {}
    preserved: dict[str, Any] = {}
    if isinstance(field_results, Mapping):
        for field, result in field_results.items():
            if field in hard_fields and isinstance(result, Mapping) and _result(result.get("result")) == "PASS":
                locked[str(field)] = deepcopy(result.get("required"))
            elif field in strong_fields and isinstance(result, Mapping) and _result(result.get("result")) == "PASS":
                preserved[str(field)] = deepcopy(result.get("required"))
    anti_substitution = contract.get("anti_substitution") if isinstance(contract.get("anti_substitution"), Mapping) else {}
    face_contract = manifest_data.get("face_aesthetic_contract") or contract.get("face_aesthetic_contract") or {
        name: contract.get(name)
        for name in (
            "face_aesthetic_profile",
            "face_aesthetic_source",
            "face_aesthetic_guardrails",
            "style_inheritance_policy",
        )
        if contract.get(name) not in (None, "", (), [], {})
    }
    constraints = [
        {"field": field, "required": deepcopy(value), "rule": "must remain PASS", "strength": "HARD"}
        for field, value in locked.items()
    ]
    constraints.extend(
        {
            "field": field,
            "required": deepcopy(value),
            "rule": "strong preference must not regress",
            "strength": "STRONG",
            "regression_class": "STRONG_PREFERENCE_REGRESSION",
        }
        for field, value in preserved.items()
    )
    constraints.extend(
        {"field": str(field), "rule": deepcopy(values)}
        for field, values in anti_substitution.items()
        if str(field) in locked or any(str(target.get("field")) == str(field) for target in targets)
    )
    instructions = tuple(_instruction(target, locked) for target in targets)
    source_image = str(data.get("actual_image", ""))
    return VisualRepairPlan(
        source_image=source_image,
        source_image_hash=data.get("actual_image_hash") or _image_hash(source_image),
        source_prompt_hash=data.get("prompt_hash"),
        source_review_id=review_id(data),
        source_generation_id=str(generation_artifact.get("generation_id")) if generation_artifact and generation_artifact.get("generation_id") else data.get("generation_id"),
        repair_attempt=repair_attempt,
        repair_targets=tuple(targets),
        locked_fields=locked,
        preserve_fields=preserved,
        repair_instructions=instructions,
        anti_regression_constraints=tuple(constraints),
        max_attempts=max_attempts,
        face_aesthetic_contract=deepcopy(dict(face_contract)) if isinstance(face_contract, Mapping) else {},
        actionable_repair_targets=tuple(deepcopy(targets)),
        informational_deviations=tuple(deepcopy(informational or ())),
        adherence_disposition=deepcopy(dict(disposition)),
        repair_trigger_decision=deepcopy(dict(trigger)) if isinstance(trigger, Mapping) else None,
    )


def should_repair(plan: VisualRepairPlan | Mapping[str, Any], *, include_minor: bool = False) -> bool:
    data = _mapping(plan)
    targets = data.get("actionable_repair_targets", data.get("repair_targets", ()))
    if include_minor:
        return bool(targets)
    return any(str(item.get("repair_severity")) not in {"MINOR", "INFORMATIONAL", "IGNORE"} for item in targets if isinstance(item, Mapping))


def _prompt_data(bundle: Any) -> Mapping[str, Any]:
    return _mapping(bundle)


def compile_repair_prompt(
    original_prompt_bundle: Mapping[str, Any] | Any,
    plan: VisualRepairPlan | Mapping[str, Any],
) -> RepairPromptBundle:
    """Compile a new prompt without mutating the original PromptBundle."""
    metadata = _prompt_data(original_prompt_bundle)
    if metadata.get("visual_context_firewall_applied") is False:
        raise VisualRepairError("Visual Context Firewall must be applied before repair compilation")
    original_prompt = str(metadata.get("prompt", "")).strip()
    if not original_prompt:
        raise VisualRepairError("repair compilation requires the current-run original prompt")
    repair_plan = VisualRepairPlan.from_dict(_mapping(plan)) if not isinstance(plan, VisualRepairPlan) else plan
    lines = [
        "## GLOBAL RENDERING CONTRACT",
        str(metadata.get("rendering_foundation", "CONTEMPORARY_COMMERCIAL_GACHA_ANIME")),
        str(metadata.get("regional_visual_language", "")),
        "",
        "## CHARACTER IDENTITY",
        str(metadata.get("character_identity", metadata.get("character_visual_style", "current approved character identity"))),
        "",
        "## LOCKED / PRESERVE EXACTLY",
        "PRESERVE EXACTLY / DO NOT REDESIGN",
        *(f"{field}: {value}" for field, value in repair_plan.locked_fields.items()),
        "",
        "## PRESERVE VISUAL DIRECTION",
        *(
            f"Maintain the established {field}: {value}. Do not redesign this visual direction during targeted repair."
            for field, value in repair_plan.preserve_fields.items()
        ),
        "",
        "## TARGETED REPAIR",
        *(item["text"] for item in repair_plan.repair_instructions),
        "",
        "## UNCHANGED HARD SPECIFICATION",
        original_prompt,
        "",
        "## FACE AESTHETIC CONTRACT",
    ]
    if repair_plan.face_aesthetic_contract:
        lines.extend(
            f"{name}: {value}"
            for name, value in repair_plan.face_aesthetic_contract.items()
            if value not in (None, "", (), [], {})
        )
    lines.extend(("", "## BACKGROUND / POSE SPECIFICATION"))
    contract = metadata.get("visual_specification_contract")
    if isinstance(contract, Mapping):
        for section in ("pose_specification", "background_specification"):
            values = contract.get(section)
            if isinstance(values, Mapping):
                lines.extend(f"{field}: {value}" for field, value in values.items())
    lines.extend(("", "## ANTI-REGRESSION"))
    lines.extend(f"{item['field']}: {item.get('required', item.get('rule'))}" for item in repair_plan.anti_regression_constraints)
    lines.extend(("", "## NEGATIVE / DO-NOT-SUBSTITUTE"))
    for item in repair_plan.repair_instructions:
        if item["strategy"] == "replacement":
            lines.append(item["text"])
    prompt = "\n".join(lines)
    return RepairPromptBundle(
        prompt=prompt,
        original_prompt=original_prompt,
        source_prompt_hash=repair_plan.source_prompt_hash,
        prompt_hash=sha256(prompt.encode("utf-8")).hexdigest(),
        repair_plan=repair_plan.to_dict(),
    )


def _review_score(review: VisualAdherenceReview | Mapping[str, Any], explicit_fields: set[str]) -> tuple[int, int, int, int]:
    data = _mapping(review)
    fields = data.get("field_results") if isinstance(data.get("field_results"), Mapping) else {}
    critical_bad = sum(
        1
        for field in explicit_fields
        if isinstance(fields.get(field), Mapping) and _result(fields[field].get("result")) in {"FAIL", "PARTIAL"}
    )
    failures = sum(1 for item in fields.values() if isinstance(item, Mapping) and _result(item.get("result")) == "FAIL")
    partials = sum(1 for item in fields.values() if isinstance(item, Mapping) and _result(item.get("result")) == "PARTIAL")
    not_evaluable = sum(1 for item in fields.values() if isinstance(item, Mapping) and _result(item.get("result")) == "NOT_EVALUABLE")
    return critical_bad, failures, partials, not_evaluable


def initial_best_artifact(
    review: VisualAdherenceReview | Mapping[str, Any],
    image: str | Path | None = None,
    *,
    generation_artifact: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    data = _mapping(review)
    result = {
        "image": str(image or data.get("actual_image", "")),
        "image_path": str(image or data.get("actual_image", "")),
        "image_hash": data.get("actual_image_hash"),
        "prompt_hash": data.get("prompt_hash"),
        "review_id": review_id(data),
        "generation_id": data.get("generation_id"),
        "source_type": "original",
        "attempt_id": None,
        "overall_result": data.get("overall_result"),
        "selection_basis": "adherence_only",
        "score": list(_review_score(data, set())),
    }
    if generation_artifact is not None:
        artifact = _mapping(generation_artifact)
        result.update(
            {
                "generation_id": artifact.get("generation_id"),
                "image_path": artifact.get("image_path", result["image_path"]),
                "image_hash": artifact.get("image_hash", result["image_hash"]),
                "prompt_hash": artifact.get("prompt_hash", result["prompt_hash"]),
            }
        )
    return result


def evaluate_repair_attempt(
    before_review: VisualAdherenceReview | Mapping[str, Any],
    after_review: VisualAdherenceReview | Mapping[str, Any] | None,
    plan: VisualRepairPlan | Mapping[str, Any],
) -> dict[str, Any]:
    """Compare two observations; no aesthetic or pixel-level score is used."""
    if after_review is None:
        return {"outcome": "FAILED", "reason": "re-review is required before accepting a repair"}
    before = _mapping(before_review)
    after = _mapping(after_review)
    repair_plan = VisualRepairPlan.from_dict(_mapping(plan)) if not isinstance(plan, VisualRepairPlan) else plan
    before_fields = before.get("field_results") if isinstance(before.get("field_results"), Mapping) else {}
    after_fields = after.get("field_results") if isinstance(after.get("field_results"), Mapping) else {}
    regressions = []
    for field, old in before_fields.items():
        if not isinstance(old, Mapping) or _result(old.get("result")) != "PASS":
            continue
        new = after_fields.get(field)
        if isinstance(new, Mapping) and _result(new.get("result")) in {"PARTIAL", "FAIL"}:
            regression_class = (
                "HARD_REGRESSION" if field in repair_plan.locked_fields
                else "STRONG_PREFERENCE_REGRESSION" if field in repair_plan.preserve_fields
                else "REGRESSION"
            )
            regressions.append({"field": field, "before": "PASS", "after": _result(new.get("result")), "class": regression_class})
    target_results: list[dict[str, Any]] = []
    improved: list[str] = []
    unresolved: list[str] = []
    rank = {"PASS": 0, "PARTIAL": 1, "FAIL": 2, "NOT_EVALUABLE": 3}
    for target in repair_plan.repair_targets:
        field = str(target.get("field"))
        old_result = _result(before_fields.get(field, {}).get("result")) if isinstance(before_fields.get(field), Mapping) else "NOT_EVALUABLE"
        new_result = _result(after_fields.get(field, {}).get("result")) if isinstance(after_fields.get(field), Mapping) else "NOT_EVALUABLE"
        target_results.append({"field": field, "before": old_result, "after": new_result})
        if rank[new_result] < rank[old_result]:
            improved.append(field)
        if new_result != "PASS":
            unresolved.append(field)
    if regressions:
        outcome = "REGRESSION"
    elif not unresolved:
        outcome = "SUCCESS"
    elif improved:
        outcome = "PARTIAL_SUCCESS"
    else:
        outcome = "NO_IMPROVEMENT"
    return {
        "attempt_id": repair_plan.attempt_id,
        "repair_attempt": repair_plan.repair_attempt,
        "outcome": outcome,
        "target_results": target_results,
        "improved_targets": improved,
        "unresolved_targets": unresolved,
        "regressions": regressions,
        "best_artifact_policy": "keep_original_on_regression; otherwise update only on strictly better adherence",
    }


def select_best_artifact(
    current: Mapping[str, Any],
    candidate: Mapping[str, Any],
    before_review: VisualAdherenceReview | Mapping[str, Any],
    after_review: VisualAdherenceReview | Mapping[str, Any],
    *,
    explicit_fields: tuple[str, ...] | list[str] = (),
    outcome: str | None = None,
) -> dict[str, Any]:
    if outcome == "REGRESSION":
        return deepcopy(dict(current))
    explicit = set(str(field) for field in explicit_fields)
    before_score = _review_score(before_review, explicit)
    after_score = _review_score(after_review, explicit)
    if after_score >= before_score:
        return deepcopy(dict(current))
    result = deepcopy(dict(candidate))
    result["selection_basis"] = "adherence_only"
    result["score"] = list(after_score)
    return result


__all__ = [
    "MAX_REPAIR_ATTEMPTS",
    "REPAIR_OUTCOMES",
    "REPAIR_SEVERITIES",
    "REPAIR_STATUSES",
    "RepairPromptBundle",
    "VisualRepairError",
    "VisualRepairPlan",
    "build_repair_plan",
    "compile_repair_prompt",
    "evaluate_repair_attempt",
    "initial_best_artifact",
    "review_id",
    "select_best_artifact",
    "should_repair",
]
