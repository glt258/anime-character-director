"""Deterministic separation of adherence truth from repair disposition."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class AdherencePolicyError(ValueError):
    """Raised when policy metadata cannot be interpreted safely."""


class Ownership(str, Enum):
    HUMAN_EXPLICIT = "HUMAN_EXPLICIT"
    HUMAN_SELECTION = "HUMAN_SELECTION"
    SYSTEM_INVARIANT = "SYSTEM_INVARIANT"
    AI_RESOLVED = "AI_RESOLVED"
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"


class RepairImportance(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    INFORMATIONAL = "INFORMATIONAL"


class RepairRisk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Disposition(str, Enum):
    ACCEPT = "ACCEPT"
    ACCEPT_WITH_DEVIATIONS = "ACCEPT_WITH_DEVIATIONS"
    REPAIR_RECOMMENDED = "REPAIR_RECOMMENDED"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    BLOCKED = "BLOCKED"


OWNERSHIP_ALIASES = {
    "explicit_user": Ownership.HUMAN_EXPLICIT,
    "human_explicit": Ownership.HUMAN_EXPLICIT,
    "human_select": Ownership.HUMAN_SELECTION,
    "human_selection": Ownership.HUMAN_SELECTION,
    "human_mix": Ownership.HUMAN_SELECTION,
    "human_custom": Ownership.HUMAN_SELECTION,
    "human_accept_recommended": Ownership.HUMAN_SELECTION,
    "delegated_ai": Ownership.AI_RESOLVED,
    "quick_ai_fill": Ownership.AI_RESOLVED,
    "ai_resolved": Ownership.AI_RESOLVED,
    "policy_default": Ownership.SYSTEM_DEFAULT,
    "system_default": Ownership.SYSTEM_DEFAULT,
    "system_invariant": Ownership.SYSTEM_INVARIANT,
}
IMPORTANCE_ORDER = {
    RepairImportance.INFORMATIONAL.value: 0,
    RepairImportance.MINOR.value: 1,
    RepairImportance.MAJOR.value: 2,
    RepairImportance.CRITICAL.value: 3,
}
VALID_RESULTS = {"PASS", "PARTIAL", "FAIL", "NOT_EVALUABLE"}
HUMAN_OWNERS = {Ownership.HUMAN_EXPLICIT.value, Ownership.HUMAN_SELECTION.value}
SYSTEM_FIELDS = {
    "anatomy_check",
    "hand_anatomy_check",
    "foot_visibility_and_integrity_check",
    "global_rendering_style",
    "rendering_foundation",
    "contract_conflict",
}
FIELD_DEFAULTS = {
    "anatomy_check": {"ownership": Ownership.SYSTEM_INVARIANT.value, "repair_importance": RepairImportance.CRITICAL.value},
    "hand_anatomy_check": {"ownership": Ownership.SYSTEM_INVARIANT.value, "repair_importance": RepairImportance.CRITICAL.value},
    "foot_visibility_and_integrity_check": {"ownership": Ownership.SYSTEM_INVARIANT.value, "repair_importance": RepairImportance.CRITICAL.value},
    "global_rendering_style": {"ownership": Ownership.SYSTEM_INVARIANT.value, "repair_importance": RepairImportance.MAJOR.value},
    "rendering_foundation": {"ownership": Ownership.SYSTEM_INVARIANT.value, "repair_importance": RepairImportance.MAJOR.value},
    "architecture_presence": {"repair_importance": RepairImportance.MINOR.value},
    "architecture_language": {"repair_importance": RepairImportance.MINOR.value},
    "background_complexity": {"repair_importance": RepairImportance.MINOR.value},
}
EXPLICIT_FIELD_ALIASES = {
    "costume_identity": "costume_topology",
    "legwear": "legwear_strategy",
    "footwear": "footwear_category",
    "footwear_detail": "footwear_detail",
    "background": "background_direction",
    "pose": "pose_family",
    "horns": "horn_topology",
    "tail": "tail_design",
    "wings": "wing_strategy",
}


def _mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    return value if isinstance(value, Mapping) else {}


def _normalize_ownership(value: Any) -> str:
    if isinstance(value, Ownership):
        return value.value
    normalized = str(value or "").strip().casefold()
    if normalized in OWNERSHIP_ALIASES:
        return OWNERSHIP_ALIASES[normalized].value
    if str(value) in {item.value for item in Ownership}:
        return str(value)
    raise AdherencePolicyError(f"unsupported ownership: {value}")


def _result(value: Any) -> str:
    normalized = str(value or "NOT_EVALUABLE").upper()
    if normalized not in VALID_RESULTS:
        raise AdherencePolicyError(f"unsupported adherence result: {value}")
    return normalized


def _aggregate(results: Sequence[str]) -> str:
    if not results:
        return "NOT_APPLICABLE"
    if "FAIL" in results:
        return "FAIL"
    if "PARTIAL" in results:
        return "PARTIAL"
    if "NOT_EVALUABLE" in results:
        return "NOT_EVALUABLE"
    return "PASS"


def _field_metadata(
    *,
    manifest: Mapping[str, Any],
    contract: Mapping[str, Any],
    final_design: Mapping[str, Any],
    fields: set[str],
) -> tuple[dict[str, dict[str, Any]], bool]:
    metadata: dict[str, dict[str, Any]] = {}
    has_explicit_metadata = False
    for source in (final_design.get("field_metadata"), manifest.get("field_metadata"), contract.get("field_metadata")):
        if not isinstance(source, Mapping):
            continue
        for name, raw in source.items():
            if not isinstance(raw, Mapping):
                continue
            item = dict(raw)
            if "ownership" in item:
                item["ownership"] = _normalize_ownership(item["ownership"])
                has_explicit_metadata = True
            metadata[str(name)] = {**metadata.get(str(name), {}), **item}

    provenance = final_design.get("provenance")
    if isinstance(provenance, Mapping):
        for name, source in provenance.items():
            if str(name) not in metadata:
                metadata[str(name)] = {}
            metadata[str(name)]["ownership"] = _normalize_ownership(source)
            has_explicit_metadata = True

    variables = final_design.get("visual_preferences")
    if isinstance(variables, Mapping):
        for name, item in variables.items():
            if isinstance(item, Mapping) and item.get("selection_source"):
                metadata.setdefault(str(name), {})["ownership"] = _normalize_ownership(item["selection_source"])
                has_explicit_metadata = True

    explicit_fields = set(str(item) for item in contract.get("explicit_hard_fields", ()))
    explicit_constraints = contract.get("explicit_constraints") or manifest.get("explicit_constraints") or {}
    if isinstance(explicit_constraints, Mapping):
        for name, raw in explicit_constraints.items():
            record = raw if isinstance(raw, Mapping) else {"value": raw}
            target = str(record.get("target_field") or EXPLICIT_FIELD_ALIASES.get(str(name), name))
            if record.get("source"):
                metadata.setdefault(target, {})["ownership"] = _normalize_ownership(record["source"])
                has_explicit_metadata = True
            explicit_fields.add(target)
    for field in explicit_fields:
        metadata.setdefault(field, {}).setdefault("ownership", Ownership.HUMAN_EXPLICIT.value)

    for name in fields:
        metadata.setdefault(name, {})
    return metadata, has_explicit_metadata


def _contract_strength(field: str, metadata: Mapping[str, Any], manifest: Mapping[str, Any], contract: Mapping[str, Any]) -> str:
    if metadata.get("strength"):
        return str(metadata["strength"]).upper()
    for key, strength in (("hard_constraints", "HARD"), ("strong_preferences", "STRONG"), ("soft_intent", "SOFT")):
        if field in manifest.get(key, {}) or field in contract.get(key, {}):
            return strength
    return "SOFT"


def _default_ownership(field: str, strength: str, metadata: Mapping[str, Any]) -> tuple[str, bool]:
    if field in SYSTEM_FIELDS:
        return Ownership.SYSTEM_INVARIANT.value, False
    if metadata.get("ownership"):
        return _normalize_ownership(metadata["ownership"]), True
    if strength == "HARD":
        return Ownership.AI_RESOLVED.value, False
    return Ownership.SYSTEM_DEFAULT.value, False


def _default_importance(ownership: str, result: str) -> str:
    if result == "NOT_EVALUABLE":
        return RepairImportance.INFORMATIONAL.value
    if result == "FAIL":
        return RepairImportance.CRITICAL.value if ownership in HUMAN_OWNERS or ownership == Ownership.SYSTEM_INVARIANT.value else RepairImportance.MINOR.value if ownership == Ownership.AI_RESOLVED.value else RepairImportance.INFORMATIONAL.value
    if result == "PARTIAL":
        return RepairImportance.MAJOR.value if ownership in HUMAN_OWNERS or ownership == Ownership.SYSTEM_INVARIANT.value else RepairImportance.INFORMATIONAL.value
    return RepairImportance.INFORMATIONAL.value


def _importance(metadata: Mapping[str, Any], field: str, ownership: str, result: str) -> str:
    base = _default_importance(ownership, result)
    explicit_override = metadata.get("repair_importance", metadata.get("criticality"))
    if explicit_override is not None:
        value = str(explicit_override).upper()
        if value not in IMPORTANCE_ORDER:
            raise AdherencePolicyError(f"unsupported repair importance: {explicit_override}")
        return value
    default_override = FIELD_DEFAULTS.get(field, {}).get("repair_importance")
    if default_override is None:
        return base
    value = str(default_override).upper()
    if value not in IMPORTANCE_ORDER:
        raise AdherencePolicyError(f"unsupported repair importance: {default_override}")
    return value if IMPORTANCE_ORDER[value] >= IMPORTANCE_ORDER[base] else base


def _risk(metadata: Mapping[str, Any], importance: str, ownership: str) -> str:
    value = str(metadata.get("repair_risk", "")).upper()
    if value:
        if value not in {item.value for item in RepairRisk}:
            raise AdherencePolicyError(f"unsupported repair risk: {value}")
        return value
    if ownership in HUMAN_OWNERS or ownership == Ownership.SYSTEM_INVARIANT.value:
        return RepairRisk.MEDIUM.value if importance in {"CRITICAL", "MAJOR"} else RepairRisk.HIGH.value
    return RepairRisk.HIGH.value


def _target(
    field: str,
    raw: Mapping[str, Any],
    *,
    metadata: Mapping[str, Any],
    ownership: str,
    strength: str,
    manual_requested: bool,
) -> dict[str, Any]:
    result = _result(raw.get("result"))
    importance = _importance(metadata, field, ownership, result)
    risk = _risk(metadata, importance, ownership)
    allow_high_risk = bool(metadata.get("allow_high_risk_auto_repair", False))
    configured = metadata.get("auto_repair_eligible")
    auto_eligible = ownership in HUMAN_OWNERS | {Ownership.SYSTEM_INVARIANT.value} and importance in {"CRITICAL", "MAJOR"}
    if configured is not None:
        auto_eligible = bool(configured) and auto_eligible
    if risk == RepairRisk.HIGH.value and not allow_high_risk:
        auto_eligible = False
    target = deepcopy(dict(raw))
    target.update(
        {
            "field": field,
            "result": result,
            "ownership": ownership,
            "contract_strength": strength,
            "repair_importance": importance,
            "repair_risk": risk,
            "auto_repair_eligible": auto_eligible,
            "manual_repair_available": result in {"FAIL", "PARTIAL"},
            "manual_repair_requested": manual_requested,
        }
    )
    return target


@dataclass(frozen=True)
class RepairTriggerDecision:
    disposition: str
    repair_required: bool
    auto_repair_eligible: bool
    manual_repair_available: bool
    repair_risk: str
    actionable_repair_targets: tuple[dict[str, Any], ...]
    informational_deviations: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["actionable_repair_targets"] = deepcopy(list(self.actionable_repair_targets))
        data["informational_deviations"] = deepcopy(list(self.informational_deviations))
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "RepairTriggerDecision":
        return cls(
            disposition=str(data.get("disposition", Disposition.BLOCKED.value)),
            repair_required=bool(data.get("repair_required", False)),
            auto_repair_eligible=bool(data.get("auto_repair_eligible", False)),
            manual_repair_available=bool(data.get("manual_repair_available", False)),
            repair_risk=str(data.get("repair_risk", RepairRisk.HIGH.value)),
            actionable_repair_targets=tuple(deepcopy(data.get("actionable_repair_targets", ()))),
            informational_deviations=tuple(deepcopy(data.get("informational_deviations", ()))),
        )


@dataclass(frozen=True)
class AdherenceDisposition:
    strict_overall_result: str
    human_constraint_result: str
    system_invariant_result: str
    ai_design_fidelity_result: str
    blocking_failures: tuple[dict[str, Any], ...]
    nonblocking_failures: tuple[dict[str, Any], ...]
    repair_trigger_decision: RepairTriggerDecision
    disposition_source: str = "current_policy"

    @property
    def disposition(self) -> str:
        return self.repair_trigger_decision.disposition

    def to_dict(self) -> dict[str, Any]:
        return {
            "strict_overall_result": self.strict_overall_result,
            "human_constraint_result": self.human_constraint_result,
            "system_invariant_result": self.system_invariant_result,
            "ai_design_fidelity_result": self.ai_design_fidelity_result,
            "blocking_failures": deepcopy(list(self.blocking_failures)),
            "nonblocking_failures": deepcopy(list(self.nonblocking_failures)),
            "repair_required": self.repair_trigger_decision.repair_required,
            "auto_repair_eligible": self.repair_trigger_decision.auto_repair_eligible,
            "manual_repair_available": self.repair_trigger_decision.manual_repair_available,
            "repair_risk": self.repair_trigger_decision.repair_risk,
            "actionable_repair_targets": deepcopy(list(self.repair_trigger_decision.actionable_repair_targets)),
            "informational_deviations": deepcopy(list(self.repair_trigger_decision.informational_deviations)),
            "disposition": self.disposition,
            "disposition_source": self.disposition_source,
            "repair_trigger_decision": self.repair_trigger_decision.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "AdherenceDisposition":
        trigger = data.get("repair_trigger_decision") if isinstance(data.get("repair_trigger_decision"), Mapping) else data
        return cls(
            strict_overall_result=str(data.get("strict_overall_result", data.get("overall_result", "NOT_EVALUABLE"))),
            human_constraint_result=str(data.get("human_constraint_result", "NOT_APPLICABLE")),
            system_invariant_result=str(data.get("system_invariant_result", "NOT_APPLICABLE")),
            ai_design_fidelity_result=str(data.get("ai_design_fidelity_result", "NOT_APPLICABLE")),
            blocking_failures=tuple(deepcopy(data.get("blocking_failures", ()))),
            nonblocking_failures=tuple(deepcopy(data.get("nonblocking_failures", ()))),
            repair_trigger_decision=RepairTriggerDecision.from_dict(trigger),
            disposition_source=str(data.get("disposition_source", "legacy_derived")),
        )


def evaluate_adherence_disposition(
    review: Mapping[str, Any] | Any,
    *,
    manifest: Mapping[str, Any] | None = None,
    visual_specification_contract: Mapping[str, Any] | None = None,
    final_design: Mapping[str, Any] | None = None,
    manual_repair_fields: Sequence[str] = (),
) -> AdherenceDisposition:
    """Classify critic deviations without changing the critic's strict result."""
    data = _mapping(review)
    manifest_data = _mapping(manifest)
    contract = _mapping(visual_specification_contract)
    design = _mapping(final_design)
    fields = data.get("field_results") if isinstance(data.get("field_results"), Mapping) else {}
    field_names = [str(name) for name in fields]
    if isinstance(data.get("anatomy_check"), Mapping) and "anatomy_check" not in field_names:
        field_names.append("anatomy_check")
    metadata, has_explicit_metadata = _field_metadata(
        manifest=manifest_data,
        contract=contract,
        final_design=design,
        fields=field_names,
    )
    manual = {str(item) for item in manual_repair_fields}
    evaluated: list[dict[str, Any]] = []
    for field in field_names:
        raw = fields.get(field, {}) if isinstance(fields.get(field), Mapping) else {}
        if field == "anatomy_check":
            raw = data.get("anatomy_check") if isinstance(data.get("anatomy_check"), Mapping) else {"result": "NOT_EVALUABLE"}
        result = _result(raw.get("result"))
        item_metadata = dict(metadata.get(field, {}))
        strength = _contract_strength(field, item_metadata, manifest_data, contract)
        ownership, exact = _default_ownership(field, strength, item_metadata)
        target = _target(field, raw, metadata=item_metadata, ownership=ownership, strength=strength, manual_requested=field in manual)
        target["legacy_derived"] = not exact
        evaluated.append(target)

    human_results = [item["result"] for item in evaluated if item["ownership"] in HUMAN_OWNERS]
    system_results = [item["result"] for item in evaluated if item["ownership"] == Ownership.SYSTEM_INVARIANT.value]
    ai_results = [item["result"] for item in evaluated if item["ownership"] in {Ownership.AI_RESOLVED.value, Ownership.SYSTEM_DEFAULT.value}]
    blocking = [
        item
        for item in evaluated
        if item["result"] == "FAIL"
        and item["ownership"] in HUMAN_OWNERS | {Ownership.SYSTEM_INVARIANT.value}
    ]
    recommended = [
        item
        for item in evaluated
        if item["result"] == "PARTIAL"
        and item["ownership"] in HUMAN_OWNERS | {Ownership.SYSTEM_INVARIANT.value}
    ]
    actionable = [
        item
        for item in evaluated
        if item["result"] in {"FAIL", "PARTIAL"}
        and (item["auto_repair_eligible"] or item["manual_repair_requested"])
    ]
    informational = [
        item
        for item in evaluated
        if item["result"] in {"FAIL", "PARTIAL"} and item not in actionable
    ]
    has_not_evaluable = any(item["result"] == "NOT_EVALUABLE" for item in evaluated)
    if has_not_evaluable:
        disposition = Disposition.BLOCKED.value
    elif blocking:
        disposition = Disposition.REPAIR_REQUIRED.value
    elif recommended or actionable:
        disposition = Disposition.REPAIR_RECOMMENDED.value
    elif informational:
        disposition = Disposition.ACCEPT_WITH_DEVIATIONS.value
    else:
        disposition = Disposition.ACCEPT.value

    risks = [str(item["repair_risk"]) for item in actionable + informational]
    repair_risk = RepairRisk.HIGH.value if RepairRisk.HIGH.value in risks else RepairRisk.MEDIUM.value if risks else RepairRisk.LOW.value
    trigger = RepairTriggerDecision(
        disposition=disposition,
        repair_required=bool(blocking),
        auto_repair_eligible=any(bool(item["auto_repair_eligible"]) for item in actionable),
        manual_repair_available=bool(actionable or informational) and not has_not_evaluable,
        repair_risk=repair_risk,
        actionable_repair_targets=tuple(deepcopy(actionable)),
        informational_deviations=tuple(deepcopy(informational)),
    )
    return AdherenceDisposition(
        strict_overall_result=str(data.get("overall_result", "NOT_EVALUABLE")),
        human_constraint_result=_aggregate(human_results),
        system_invariant_result=_aggregate(system_results),
        ai_design_fidelity_result=_aggregate(ai_results),
        blocking_failures=tuple(deepcopy(blocking)),
        nonblocking_failures=tuple(deepcopy(recommended + informational)),
        repair_trigger_decision=trigger,
        disposition_source="current_policy" if has_explicit_metadata else "legacy_derived",
    )


__all__ = [
    "AdherenceDisposition",
    "AdherencePolicyError",
    "Disposition",
    "Ownership",
    "RepairImportance",
    "RepairRisk",
    "RepairTriggerDecision",
    "evaluate_adherence_disposition",
]
