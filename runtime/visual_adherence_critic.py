"""Manifest-driven post-generation visual adherence review.

The critic consumes an existing image and human/model-labeled observations. It
does not infer a new design from prompt text and never repairs or regenerates.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping


RESULTS = ("PASS", "PARTIAL", "FAIL", "NOT_EVALUABLE")
ANATOMY_RESULTS = ("PASS", "FAIL", "NOT_EVALUABLE")

TIER1_FIELDS = (
    "face_aesthetic_profile",
    "facial_style_drift",
    "regional_face_language",
    "hair_color",
    "hair_structure",
    "horn_topology",
    "costume_topology",
    "lower_body_structure",
    "exposure_strategy",
    "legwear_strategy",
    "footwear_category",
    "wing_strategy",
    "tail_design",
    "silhouette_family",
    "lower_body_pose",
    "torso_orientation",
    "left_arm_action",
    "right_arm_action",
    "left_hand_gesture",
    "right_hand_gesture",
    "head_attitude",
    "gaze_direction",
    "environment_type",
    "architecture_presence",
    "architecture_language",
    "spatial_structure",
    "background_complexity",
    "palette_family",
)

HAND_CHECK_FIELDS = (
    "finger_count",
    "finger_fusion",
    "placement",
    "palm",
    "wrist",
    "arm_connection",
    "extra_limb",
    "missing_limb",
)

FOOT_CHECK_FIELDS = (
    "visible_or_occluded",
    "malformed_foot",
    "extra_foot",
    "missing_foot",
    "impossible_shoe_attachment",
)

FAILURE_TYPE_LABELS = {
    "TYPE 1": "Prompt Specification Failure",
    "TYPE 2": "Prompt Conflict",
    "TYPE 3": "ImageGen Archetype Substitution",
    "TYPE 4": "Weak Fine-Grained Adherence",
    "TYPE 5": "Composition / Visibility Failure",
    "TYPE 6": "Rendering / Anatomy Error",
}


class VisualAdherenceError(ValueError):
    """Raised when a post-generation review input is invalid."""


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    if not isinstance(value, Mapping):
        raise VisualAdherenceError("visual adherence inputs must be mappings")
    return value


def _nonempty(value: Any) -> bool:
    return value not in (None, "", (), [], {})


def _text(value: Any) -> str:
    return str(value).strip().casefold()


def _compare(required: Any, observed: Any) -> str:
    if not _nonempty(observed):
        return "NOT_EVALUABLE"
    required_text = _text(required)
    observed_text = _text(observed)
    if required_text == observed_text or required_text in observed_text:
        return "PASS"
    return "PARTIAL"


def _failure_codes(values: Any) -> list[str]:
    if values is None:
        return []
    raw_values = [values] if isinstance(values, str) else list(values)
    codes: list[str] = []
    for value in raw_values:
        text = str(value).strip()
        code = next((item for item in FAILURE_TYPE_LABELS if text.upper().startswith(item)), None)
        if code is None:
            raise VisualAdherenceError(f"unknown failure type: {value}")
        if code not in codes:
            codes.append(code)
    return codes


def _default_failure_type(field: str, result: str) -> str | None:
    if result == "NOT_EVALUABLE":
        return None
    if result == "PARTIAL":
        return "TYPE 4"
    if field in {
        "facial_style_drift",
        "face_aesthetic_profile",
        "regional_face_language",
    }:
        return "TYPE 3"
    if field in {
        "lower_body_pose",
        "torso_orientation",
        "left_arm_action",
        "right_arm_action",
        "left_hand_gesture",
        "right_hand_gesture",
        "head_attitude",
        "gaze_direction",
        "environment_type",
        "architecture_presence",
        "architecture_language",
        "spatial_structure",
        "background_complexity",
    }:
        return "TYPE 5"
    return "TYPE 3"


def _part_check(raw: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    if raw is None:
        return {"result": "NOT_EVALUABLE", **{name: "NOT_EVALUABLE" for name in fields}}
    if isinstance(raw, Mapping):
        result = str(raw.get("result", "NOT_EVALUABLE")).upper()
        details = {name: deepcopy(raw.get(name, "NOT_EVALUABLE")) for name in fields}
    else:
        result = str(raw).upper()
        details = {name: "NOT_EVALUABLE" for name in fields}
    if result not in ANATOMY_RESULTS:
        raise VisualAdherenceError(f"anatomy result must be PASS, FAIL, or NOT_EVALUABLE: {result}")
    return {"result": result, **details}


@dataclass(frozen=True)
class VisualAdherenceReview:
    actual_image: str
    overall_result: str
    field_results: dict[str, dict[str, Any]]
    failure_types: tuple[str, ...]
    not_evaluable_fields: tuple[str, ...]
    anatomy_check: dict[str, Any]
    repair_targets: tuple[dict[str, Any], ...]
    summary: str
    evidence_source: str = "human_actual_image_review"
    prompt_hash: str | None = None
    manifest_fields: tuple[str, ...] = ()
    actual_image_hash: str | None = None
    review_id: str | None = None
    generation_id: str | None = None
    adherence_disposition: dict[str, Any] | None = None
    repair_trigger_decision: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "actual_image": self.actual_image,
            "overall_result": self.overall_result,
            "field_results": deepcopy(self.field_results),
            "failure_types": list(self.failure_types),
            "not_evaluable_fields": list(self.not_evaluable_fields),
            "anatomy_check": deepcopy(self.anatomy_check),
            "repair_targets": deepcopy(list(self.repair_targets)),
            "summary": self.summary,
            "evidence_source": self.evidence_source,
            "prompt_hash": self.prompt_hash,
            "manifest_fields": list(self.manifest_fields),
            "actual_image_hash": self.actual_image_hash,
            "review_id": self.review_id,
            "generation_id": self.generation_id,
            "adherence_disposition": deepcopy(self.adherence_disposition),
            "repair_trigger_decision": deepcopy(self.repair_trigger_decision),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VisualAdherenceReview":
        return cls(
            str(data["actual_image"]),
            str(data["overall_result"]),
            deepcopy(dict(data.get("field_results") or {})),
            tuple(str(item) for item in data.get("failure_types", ())),
            tuple(str(item) for item in data.get("not_evaluable_fields", ())),
            deepcopy(dict(data.get("anatomy_check") or {})),
            tuple(deepcopy(item) for item in data.get("repair_targets", ())),
            str(data.get("summary", "")),
            str(data.get("evidence_source", "human_actual_image_review")),
            data.get("prompt_hash"),
            tuple(str(item) for item in data.get("manifest_fields", ())),
            data.get("actual_image_hash"),
            data.get("review_id"),
            data.get("generation_id"),
            deepcopy(dict(data.get("adherence_disposition") or {})) if data.get("adherence_disposition") is not None else None,
            deepcopy(dict(data.get("repair_trigger_decision") or {})) if data.get("repair_trigger_decision") is not None else None,
        )


class VisualAdherenceCritic:
    """Review actual-image adherence using only fields present in the manifest."""

    def review(
        self,
        actual_image: str | Path,
        *,
        manifest: Mapping[str, Any],
        observations: Mapping[str, Any],
        visual_specification_contract: Mapping[str, Any] | None = None,
        final_design: Mapping[str, Any] | None = None,
        final_design_summary: Mapping[str, Any] | str | None = None,
        prompt_bundle_metadata: Mapping[str, Any] | None = None,
        prompt_hash: str | None = None,
        generation_id: str | None = None,
    ) -> VisualAdherenceReview:
        image = Path(actual_image)
        if not image.is_file():
            raise VisualAdherenceError("VisualAdherenceCritic requires an existing actual image")
        manifest_data = _as_mapping(manifest)
        observation_data = _as_mapping(observations)
        # These inputs are accepted for the workflow seam and provenance only.
        # Required values always come from the PromptAdherenceManifest.
        _ = visual_specification_contract, final_design, final_design_summary
        metadata = _as_mapping(prompt_bundle_metadata) if prompt_bundle_metadata is not None else {}

        sources = (
            manifest_data.get("face_aesthetic_contract"),
            manifest_data,
            manifest_data.get("hard_constraints"),
            manifest_data.get("strong_preferences"),
            manifest_data.get("pose_specification"),
            manifest_data.get("background_specification"),
        )
        required: dict[str, Any] = {}
        labeled_fields = observation_data.get("field_results")
        face_observation_requested = any(
            name in observation_data or (isinstance(labeled_fields, Mapping) and name in labeled_fields)
            for name in ("facial_style_drift", "regional_face_language")
        )
        for source in sources:
            if isinstance(source, Mapping):
                for name in TIER1_FIELDS:
                    if name in {"facial_style_drift", "regional_face_language"} and not face_observation_requested:
                        continue
                    if name not in required and _nonempty(source.get(name)):
                        required[name] = deepcopy(source[name])

        top_level_failures = observation_data.get("failure_types", {})
        field_results: dict[str, dict[str, Any]] = {}
        failure_types: list[str] = []
        not_evaluable: list[str] = []
        repair_targets: list[dict[str, Any]] = []
        for name in TIER1_FIELDS:
            if name not in required:
                continue
            raw = labeled_fields.get(name) if isinstance(labeled_fields, Mapping) and name in labeled_fields else observation_data.get(name)
            if isinstance(raw, Mapping):
                observed = deepcopy(raw.get("observed", raw.get("value")))
                result = str(raw.get("result", _compare(required[name], observed))).upper()
                rationale = str(raw.get("rationale", ""))
                raw_failures = raw.get("failure_types")
            else:
                observed = deepcopy(raw)
                result = _compare(required[name], observed)
                rationale = ""
                raw_failures = None
            if result not in RESULTS:
                raise VisualAdherenceError(f"field result must be PASS, PARTIAL, FAIL, or NOT_EVALUABLE: {name}")
            if raw_failures is None and isinstance(top_level_failures, Mapping):
                raw_failures = top_level_failures.get(name)
            codes = _failure_codes(raw_failures)
            if result != "PASS" and not codes:
                default = _default_failure_type(name, result)
                codes = [default] if default else []
            for code in codes:
                if code not in failure_types:
                    failure_types.append(code)
            if result == "NOT_EVALUABLE":
                not_evaluable.append(name)
            field_results[name] = {
                "required": deepcopy(required[name]),
                "observed": observed,
                "result": result,
                "failure_types": codes,
                "rationale": rationale,
            }
            if result in {"FAIL", "PARTIAL"}:
                repair_targets.append(
                    {
                        "field": name,
                        "required": deepcopy(required[name]),
                        "observed": observed,
                        "failure_types": codes,
                        "action": "review or repair this field before acceptance",
                    }
                )

        anatomy_source = observation_data.get("anatomy_check")
        if not isinstance(anatomy_source, Mapping):
            anatomy_source = {}
        hand = _part_check(observation_data.get("hand_anatomy_check", anatomy_source.get("hand_anatomy_check")), HAND_CHECK_FIELDS)
        feet = _part_check(
            observation_data.get("foot_visibility_and_integrity_check", anatomy_source.get("foot_visibility_and_integrity_check")),
            FOOT_CHECK_FIELDS,
        )
        parts = (hand, feet)
        anatomy_result = "FAIL" if any(item["result"] == "FAIL" for item in parts) else "NOT_EVALUABLE" if any(item["result"] == "NOT_EVALUABLE" for item in parts) else "PASS"
        if anatomy_result == "FAIL" and "TYPE 6" not in failure_types:
            failure_types.append("TYPE 6")
        anatomy_check = {
            "result": anatomy_result,
            "hand_anatomy_check": hand,
            "foot_visibility_and_integrity_check": feet,
        }
        if anatomy_result != "PASS":
            if anatomy_result == "NOT_EVALUABLE":
                for name in ("hand_anatomy_check", "foot_visibility_and_integrity_check"):
                    if name not in not_evaluable:
                        not_evaluable.append(name)
            repair_targets.append({"field": "anatomy_check", "result": anatomy_result, "failure_types": ["TYPE 6"] if anatomy_result == "FAIL" else [], "action": "inspect visible hands, limbs, feet, and shoe attachment"})

        results = [item["result"] for item in field_results.values()]
        if "FAIL" in results or anatomy_result == "FAIL":
            overall = "FAIL"
        elif "PARTIAL" in results or "NOT_EVALUABLE" in results or anatomy_result == "NOT_EVALUABLE":
            overall = "PARTIAL"
        else:
            overall = "PASS"
        digest = prompt_hash
        if digest is None and isinstance(metadata.get("prompt"), str):
            digest = sha256(metadata["prompt"].encode("utf-8")).hexdigest()
        image_digest = sha256(image.read_bytes()).hexdigest()
        computed_review_id = sha256(
            json.dumps(
                {
                    "actual_image_hash": image_digest,
                    "prompt_hash": digest,
                    "generation_id": generation_id,
                    "field_results": field_results,
                    "anatomy_check": anatomy_check,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        summary = f"Actual-image adherence review: {overall}; {len(field_results)} manifest fields checked, {len(repair_targets)} repair target(s)."
        return VisualAdherenceReview(
            str(image),
            overall,
            field_results,
            tuple(failure_types),
            tuple(not_evaluable),
            anatomy_check,
            tuple(repair_targets),
            summary,
            prompt_hash=digest,
            manifest_fields=tuple(name for name in TIER1_FIELDS if name in required),
            actual_image_hash=image_digest,
            review_id=computed_review_id,
            generation_id=generation_id,
        )


__all__ = [
    "ANATOMY_RESULTS",
    "FAILURE_TYPE_LABELS",
    "FOOT_CHECK_FIELDS",
    "HAND_CHECK_FIELDS",
    "RESULTS",
    "TIER1_FIELDS",
    "VisualAdherenceCritic",
    "VisualAdherenceError",
    "VisualAdherenceReview",
]
