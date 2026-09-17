"""Post-design structural novelty checks for completed character runs.

Historical data enters this module as compact signatures only.  It is never a
source of positive design context.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
import json
import re
from typing import Any, Mapping, Sequence


NOVELTY_GUARD_VERSION = "CROSS_RUN_NOVELTY_GUARD_V1"
NOVELTY_RESULTS = ("PASS", "BORDERLINE", "FAIL", "EXEMPT")

STRUCTURAL_WEIGHTS = {
    "silhouette_family": 3.0,
    "costume_topology": 3.0,
    "upper_body_structure": 2.5,
    "lower_body_structure": 3.0,
    "footwear_category": 2.5,
    "horn_topology": 2.5,
    "wing_strategy": 2.0,
    "pose_family": 1.5,
    "lower_body_pose": 2.0,
    "torso_orientation": 1.5,
    "arm_configuration": 1.5,
    "hand_gesture_pattern": 1.5,
}
SECONDARY_WEIGHTS = {
    "hair_structure": 1.5,
    "exposure_strategy": 1.25,
    "legwear_strategy": 1.25,
    "tail_design": 1.25,
    "body_line_emphasis": 0.75,
    "accessory_density": 0.5,
    "material_language": 1.0,
    "background_family": 0.35,
    "environment_type": 0.35,
    "architecture_presence": 0.25,
    "spatial_structure": 0.4,
}
COSMETIC_WEIGHTS = {
    "hair_color": 0.25,
    "eye_color": 0.15,
    "palette_family": 0.25,
    "accessory_tint": 0.1,
    "minor_ornaments": 0.1,
}


def _text(value: Any) -> str:
    if value is None or value == "":
        return "<unspecified>"
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, (list, tuple, set)):
        return json.dumps(list(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def _tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", _text(value).casefold()))


def _field_similarity(left: Any, right: Any) -> float:
    left_text, right_text = _text(left), _text(right)
    if left_text == "<unspecified>" or right_text == "<unspecified>":
        return 0.0
    if left_text.casefold() == right_text.casefold():
        return 1.0
    left_tokens, right_tokens = _tokens(left), _tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _pick(*sources: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for source in sources:
        for key in keys:
            if key in source and source[key] not in (None, ""):
                return source[key]
    return "<unspecified>"


@dataclass(frozen=True)
class DesignSignature:
    """Compact, field-level representation used only by NoveltyGuard."""

    fields: Mapping[str, str]
    version: str = NOVELTY_GUARD_VERSION

    @classmethod
    def from_final_design(cls, final_design: Mapping[str, Any]) -> "DesignSignature":
        dna = final_design.get("design_dna") if isinstance(final_design.get("design_dna"), Mapping) else {}
        visual = final_design.get("visual_preferences") if isinstance(final_design.get("visual_preferences"), Mapping) else {}
        lower = final_design.get("lower_body") if isinstance(final_design.get("lower_body"), Mapping) else {}
        pose = final_design.get("pose_specification") if isinstance(final_design.get("pose_specification"), Mapping) else {}
        pose = pose or (dna.get("pose_specification") if isinstance(dna.get("pose_specification"), Mapping) else {})
        background = final_design.get("background_specification") if isinstance(final_design.get("background_specification"), Mapping) else {}
        background = background or (dna.get("background_specification") if isinstance(dna.get("background_specification"), Mapping) else {})
        fields = {
            "silhouette_family": _pick(dna, final_design, keys=("silhouette_family", "silhouette")),
            "hair_structure": _pick(dna, visual, final_design, keys=("hair_structure", "hair_style_family")),
            "hair_color": _pick(visual, final_design, keys=("hair_color",)),
            "horn_topology": _pick(dna, visual, final_design, keys=("horn_topology", "ear_horn_shape")),
            "upper_body_structure": _pick(dna, final_design, keys=("upper_body_structure", "upper_body")),
            "lower_body_structure": _pick(dna, lower, final_design, keys=("lower_body_structure", "lower_body")),
            "costume_topology": _pick(dna, visual, final_design, keys=("costume_topology", "outfit_direction", "costume_structure")),
            "exposure_strategy": _pick(dna, lower, visual, keys=("exposure_strategy",)),
            "legwear_strategy": _pick(dna, lower, visual, keys=("legwear_strategy", "legwear_family")),
            "footwear_category": _pick(dna, lower, visual, keys=("footwear_category", "footwear_family")),
            "wing_strategy": _pick(dna, final_design, keys=("wing_strategy", "wings")),
            "tail_design": _pick(dna, final_design, keys=("tail_design", "tail")),
            "pose_family": _pick(dna, final_design, visual, keys=("pose_family",)),
            "lower_body_pose": _pick(pose, keys=("lower_body_pose",)),
            "torso_orientation": _pick(pose, keys=("torso_orientation",)),
            "arm_configuration": _pick(pose, keys=("arm_configuration",)),
            "hand_gesture_pattern": _text({
                "left": _pick(pose, keys=("left_hand_gesture",)),
                "right": _pick(pose, keys=("right_hand_gesture",)),
            }),
            "body_line_emphasis": _pick(dna, final_design, keys=("body_line_emphasis",)),
            "accessory_density": _pick(dna, final_design, keys=("accessory_density",)),
            "material_language": _pick(dna, final_design, keys=("material_language",)),
            "background_family": _pick(dna, visual, final_design, keys=("background_family", "background_direction")),
            "environment_type": _pick(background, keys=("environment_type",)),
            "architecture_presence": _pick(background, keys=("architecture_presence",)),
            "spatial_structure": _pick(background, keys=("spatial_structure",)),
            "palette_family": _pick(dna, visual, final_design, keys=("palette_family", "dominant_palette", "palette")),
            "eye_color": _pick(visual, final_design, keys=("eye_color",)),
            "accessory_tint": _pick(visual, final_design, keys=("accessory_tint", "major_accessories_color")),
            "minor_ornaments": _pick(visual, final_design, keys=("minor_ornaments", "hairstyle_ornament")),
        }
        return cls({name: _text(value) for name, value in fields.items()})

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DesignSignature":
        fields = data.get("fields") if isinstance(data.get("fields"), Mapping) else data
        return cls({str(name): _text(value) for name, value in fields.items() if str(name) != "version"}, str(data.get("version", NOVELTY_GUARD_VERSION)))

    def to_dict(self) -> dict[str, Any]:
        return {"version": self.version, "fields": dict(self.fields)}


@dataclass(frozen=True)
class NoveltyPolicy:
    recent_n: int = 8
    structural_fail_threshold: float = 0.70
    structural_borderline_threshold: float = 0.22
    overall_fail_threshold: float = 0.62
    overall_borderline_threshold: float = 0.28
    max_resolution_attempts: int = 2

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None = None) -> "NoveltyPolicy":
        values = dict(data or {})
        allowed = {item.name for item in cls.__dataclass_fields__.values()}
        return cls(**{name: values[name] for name in allowed if name in values})

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NoveltyReview:
    current_signature: DesignSignature
    compared_prior_runs: tuple[dict[str, Any], ...] = ()
    nearest_prior_run: str | None = None
    overall_similarity: float = 0.0
    structural_similarity: float = 0.0
    cosmetic_similarity: float = 0.0
    matching_fields: tuple[str, ...] = ()
    different_fields: tuple[str, ...] = ()
    novelty_result: str = "PASS"
    resolution_attempt: int = 0
    history_snapshot: tuple[dict[str, Any], ...] = ()
    field_similarity: Mapping[str, float] = field(default_factory=dict)
    version: str = NOVELTY_GUARD_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "current_signature": self.current_signature.to_dict(),
            "compared_prior_runs": deepcopy(list(self.compared_prior_runs)),
            "nearest_prior_run": self.nearest_prior_run,
            "overall_similarity": self.overall_similarity,
            "structural_similarity": self.structural_similarity,
            "cosmetic_similarity": self.cosmetic_similarity,
            "matching_fields": list(self.matching_fields),
            "different_fields": list(self.different_fields),
            "novelty_result": self.novelty_result,
            "resolution_attempt": self.resolution_attempt,
            "history_snapshot": deepcopy(list(self.history_snapshot)),
            "field_similarity": dict(self.field_similarity),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "NoveltyReview":
        return cls(
            current_signature=DesignSignature.from_dict(data.get("current_signature") or {}),
            compared_prior_runs=tuple(deepcopy(data.get("compared_prior_runs") or ())),
            nearest_prior_run=data.get("nearest_prior_run"),
            overall_similarity=float(data.get("overall_similarity", 0.0)),
            structural_similarity=float(data.get("structural_similarity", 0.0)),
            cosmetic_similarity=float(data.get("cosmetic_similarity", 0.0)),
            matching_fields=tuple(data.get("matching_fields") or ()),
            different_fields=tuple(data.get("different_fields") or ()),
            novelty_result=str(data.get("novelty_result", "PASS")),
            resolution_attempt=int(data.get("resolution_attempt", 0) or 0),
            history_snapshot=tuple(deepcopy(data.get("history_snapshot") or ())),
            field_similarity={str(k): float(v) for k, v in (data.get("field_similarity") or {}).items()},
            version=str(data.get("version", NOVELTY_GUARD_VERSION)),
        )


def _signature_from_candidate(candidate: Mapping[str, Any]) -> DesignSignature:
    signature = candidate.get("design_signature") or candidate.get("signature")
    if isinstance(signature, DesignSignature):
        return signature
    if isinstance(signature, Mapping):
        return DesignSignature.from_dict(signature)
    design = candidate.get("final_design") or candidate.get("design")
    if isinstance(design, Mapping):
        return DesignSignature.from_final_design(design)
    return DesignSignature.from_final_design(candidate)


def _history_record(value: Any, index: int = 0) -> dict[str, Any] | None:
    if isinstance(value, DesignSignature):
        signature = value
        source: Mapping[str, Any] = {}
    elif isinstance(value, Mapping):
        source = value
        raw = source.get("design_signature") or source.get("signature")
        if isinstance(raw, DesignSignature):
            signature = raw
        elif isinstance(raw, Mapping):
            signature = DesignSignature.from_dict(raw)
        elif isinstance(source.get("final_design"), Mapping):
            signature = DesignSignature.from_final_design(source["final_design"])
        elif isinstance(source.get("fields"), Mapping):
            signature = DesignSignature.from_dict(source)
        else:
            return None
    else:
        return None
    if source.get("inherit_previous_visuals") or str(source.get("inheritance_status", "")).lower() in {"inherited", "exempt"}:
        return None
    return {
        "run_id": str(source.get("run_id", source.get("session_id", f"prior-{index}"))),
        "generation_id": str(source.get("generation_id", "")),
        "design_signature": signature.to_dict(),
        "created_at": str(source.get("created_at", "")),
        "mode": str(source.get("mode", source.get("creation_mode", ""))),
        "inheritance_status": str(source.get("inheritance_status", "fresh")),
    }


def snapshot_history(prior_runs: Sequence[Any], policy: NoveltyPolicy | Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    resolved = policy if isinstance(policy, NoveltyPolicy) else NoveltyPolicy.from_mapping(policy)
    records = [record for index, item in enumerate(prior_runs) if (record := _history_record(item, index)) is not None]
    by_run = {record["run_id"]: record for record in records}
    records = list(by_run.values())
    records.sort(key=lambda item: (item.get("created_at", ""), item.get("run_id", "")))
    return deepcopy(records[-max(0, int(resolved.recent_n)):])


def _weighted_similarity(current: DesignSignature, prior: DesignSignature, weights: Mapping[str, float]) -> tuple[float, dict[str, float]]:
    scores = {name: round(_field_similarity(current.fields.get(name), prior.fields.get(name)), 6) for name in weights}
    denominator = sum(weight for name, weight in weights.items() if current.fields.get(name) != "<unspecified>" and prior.fields.get(name) != "<unspecified>")
    if denominator <= 0:
        return 0.0, scores
    return sum(weights[name] * scores[name] for name in weights) / denominator, scores


class NoveltyGuard:
    """Compare a completed design after generation inputs are assembled."""

    @staticmethod
    def snapshot_history(prior_runs: Sequence[Any], policy: NoveltyPolicy | Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
        return snapshot_history(prior_runs, policy)

    @staticmethod
    def evaluate(
        current_signature: DesignSignature,
        prior_runs: Sequence[Any] = (),
        *,
        policy: NoveltyPolicy | Mapping[str, Any] | None = None,
        inherit_previous_visuals: bool = False,
        allowed_visual_inheritance: Sequence[str] = (),
        history_snapshot: Sequence[Mapping[str, Any]] | None = None,
        resolution_attempt: int = 0,
    ) -> NoveltyReview:
        resolved = policy if isinstance(policy, NoveltyPolicy) else NoveltyPolicy.from_mapping(policy)
        snapshot = [deepcopy(dict(item)) for item in history_snapshot] if history_snapshot is not None else snapshot_history(prior_runs, resolved)
        if inherit_previous_visuals or allowed_visual_inheritance:
            return NoveltyReview(current_signature, tuple(snapshot), novelty_result="EXEMPT", resolution_attempt=resolution_attempt, history_snapshot=tuple(snapshot))
        if not snapshot:
            return NoveltyReview(current_signature, resolution_attempt=resolution_attempt, history_snapshot=())
        comparisons = []
        for record in snapshot:
            raw = record.get("design_signature") if isinstance(record, Mapping) else None
            if not isinstance(raw, Mapping):
                continue
            prior = DesignSignature.from_dict(raw)
            structural, structural_scores = _weighted_similarity(current_signature, prior, STRUCTURAL_WEIGHTS)
            secondary, secondary_scores = _weighted_similarity(current_signature, prior, SECONDARY_WEIGHTS)
            cosmetic, cosmetic_scores = _weighted_similarity(current_signature, prior, COSMETIC_WEIGHTS)
            all_weights = {**STRUCTURAL_WEIGHTS, **SECONDARY_WEIGHTS, **COSMETIC_WEIGHTS}
            overall, all_scores = _weighted_similarity(current_signature, prior, all_weights)
            comparisons.append({"record": record, "structural": structural, "overall": overall, "cosmetic": cosmetic, "scores": {**structural_scores, **secondary_scores, **cosmetic_scores, **all_scores}})
        if not comparisons:
            return NoveltyReview(current_signature, tuple(snapshot), resolution_attempt=resolution_attempt, history_snapshot=tuple(snapshot))
        nearest = max(comparisons, key=lambda item: (item["structural"], item["overall"], item["record"].get("run_id", "")))
        scores = nearest["scores"]
        matching = tuple(name for name, score in scores.items() if score >= 0.75)
        different = tuple(name for name, score in scores.items() if score < 0.75)
        if nearest["structural"] >= resolved.structural_fail_threshold or (
            nearest["structural"] >= resolved.structural_borderline_threshold and nearest["overall"] >= resolved.overall_fail_threshold
        ):
            result = "FAIL"
        elif nearest["structural"] >= resolved.structural_borderline_threshold or nearest["overall"] >= resolved.overall_borderline_threshold:
            result = "BORDERLINE"
        else:
            result = "PASS"
        return NoveltyReview(
            current_signature,
            tuple(snapshot),
            str(nearest["record"].get("run_id") or "") or None,
            round(nearest["overall"], 6),
            round(nearest["structural"], 6),
            round(nearest["cosmetic"], 6),
            matching,
            different,
            result,
            resolution_attempt,
            tuple(snapshot),
            {name: round(score, 6) for name, score in scores.items()},
        )

    @staticmethod
    def filter_ai_candidates(
        candidates: Sequence[Mapping[str, Any]],
        prior_runs: Sequence[Any] = (),
        *,
        policy: NoveltyPolicy | Mapping[str, Any] | None = None,
        history_snapshot: Sequence[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        reviews: dict[str, dict[str, Any]] = {}
        valid = []
        for candidate in candidates:
            candidate_id = str(candidate.get("id", candidate.get("candidate_id", len(reviews))))
            review = NoveltyGuard.evaluate(_signature_from_candidate(candidate), prior_runs, policy=policy, history_snapshot=history_snapshot)
            reviews[candidate_id] = review.to_dict()
            if review.novelty_result != "FAIL" and candidate.get("quality_valid", candidate.get("constraint_compatibility", {}).get("status", "compatible") == "compatible") is not False:
                valid.append(deepcopy(candidate))
        return {"candidates": valid, "reviews": reviews, "novelty_exhausted": not bool(valid) and bool(candidates)}

    @staticmethod
    def resolve_quick_candidates(
        candidates: Sequence[Mapping[str, Any]],
        initial_index: int,
        prior_runs: Sequence[Any] = (),
        *,
        policy: NoveltyPolicy | Mapping[str, Any] | None = None,
        history_snapshot: Sequence[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        resolved = policy if isinstance(policy, NoveltyPolicy) else NoveltyPolicy.from_mapping(policy)
        if not candidates:
            return {"selected": None, "attempts": 0, "resolution": "NOVELTY_EXHAUSTED", "reviews": {}}
        order = list(range(max(0, initial_index), len(candidates))) + list(range(0, max(0, initial_index)))
        reviews: dict[str, dict[str, Any]] = {}
        for attempt, index in enumerate(order[: max(1, resolved.max_resolution_attempts)], start=0):
            candidate = candidates[index]
            review = NoveltyGuard.evaluate(_signature_from_candidate(candidate), prior_runs, policy=resolved, history_snapshot=history_snapshot, resolution_attempt=attempt)
            candidate_id = str(candidate.get("id", candidate.get("candidate_id", index)))
            reviews[candidate_id] = review.to_dict()
            if review.novelty_result != "FAIL":
                return {"selected": deepcopy(candidate), "selected_index": index, "attempts": attempt + 1, "resolution": "KEEP" if attempt == 0 else "DETERMINISTIC_ALTERNATE", "reviews": reviews}
        return {"selected": None, "attempts": min(len(order), max(1, resolved.max_resolution_attempts)), "resolution": "NOVELTY_EXHAUSTED", "reviews": reviews}

    @staticmethod
    def evaluate_user_candidate(
        candidate: Mapping[str, Any],
        prior_runs: Sequence[Any] = (),
        *,
        explicit_fields: Sequence[str] = (),
        delegated_fields: Sequence[str] = (),
        policy: NoveltyPolicy | Mapping[str, Any] | None = None,
        history_snapshot: Sequence[Mapping[str, Any]] | None = None,
        inherit_previous_visuals: bool = False,
        allowed_visual_inheritance: Sequence[str] = (),
    ) -> dict[str, Any]:
        review = NoveltyGuard.evaluate(
            _signature_from_candidate(candidate), prior_runs, policy=policy,
            history_snapshot=history_snapshot, inherit_previous_visuals=inherit_previous_visuals,
            allowed_visual_inheritance=allowed_visual_inheritance,
        )
        aliases = {"hair_style_family": "hair_structure", "outfit_direction": "costume_topology", "dominant_palette": "palette_family", "footwear_family": "footwear_category", "legwear_family": "legwear_strategy"}
        explicit_signature_fields = {aliases.get(name, name) for name in explicit_fields}
        delegated_signature_fields = {aliases.get(name, name) for name in delegated_fields}
        explicit_overlap = sorted(explicit_signature_fields.intersection(review.matching_fields))
        delegated_overlap = sorted(delegated_signature_fields.intersection(review.matching_fields))
        return {
            "candidate": deepcopy(candidate),
            "review": review.to_dict(),
            "human_override_novelty": bool(review.novelty_result == "FAIL" and explicit_overlap),
            "explicit_matching_fields": explicit_overlap,
            "delegated_matching_fields": delegated_overlap,
            "delegated_reresolution_allowed": bool(review.novelty_result == "FAIL" and delegated_overlap and not explicit_overlap),
        }


def design_signature_from_final_design(final_design: Mapping[str, Any]) -> DesignSignature:
    return DesignSignature.from_final_design(final_design)


__all__ = [
    "COSMETIC_WEIGHTS",
    "DesignSignature",
    "NoveltyGuard",
    "NoveltyPolicy",
    "NoveltyReview",
    "NOVELTY_GUARD_VERSION",
    "NOVELTY_RESULTS",
    "SECONDARY_WEIGHTS",
    "STRUCTURAL_WEIGHTS",
    "design_signature_from_final_design",
    "snapshot_history",
]
