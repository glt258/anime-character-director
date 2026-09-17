"""Focused tests for the manifest-driven actual-image adherence critic."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.interaction_runtime import InteractionRuntime  # noqa: E402
from runtime.visual_adherence_critic import (  # noqa: E402
    VisualAdherenceCritic,
    VisualAdherenceError,
)
from runtime.workflow_runner import PersistentWorkflowRunner  # noqa: E402


IMAGE = Path(__file__)


def _manifest(**fields: object) -> dict[str, object]:
    return {
        "hard_constraints": dict(fields),
        "strong_preferences": {},
        "pose_specification": {},
        "background_specification": {},
    }


def _anatomy(*, hand: str = "PASS", feet: str = "PASS") -> dict[str, object]:
    return {
        "hand_anatomy_check": {"result": hand},
        "foot_visibility_and_integrity_check": {"result": feet},
    }


def _observations(manifest: dict[str, object], **overrides: object) -> dict[str, object]:
    fields = manifest["hard_constraints"]
    assert isinstance(fields, dict)
    result = {
        "field_results": {
            name: {"observed": value, "result": "PASS"}
            for name, value in fields.items()
        },
        **_anatomy(),
    }
    result["field_results"].update(overrides)
    return result


def test_manifest_is_the_only_required_visual_source() -> None:
    manifest = _manifest(hair_structure="braided medium")
    observations = _observations(manifest)
    review = VisualAdherenceCritic().review(
        IMAGE,
        manifest=manifest,
        observations=observations,
        final_design={"hair_structure": "crimson long hair", "background": "gothic cathedral"},
        prompt_bundle_metadata={"prompt": "crimson long hair, gothic cathedral"},
    )

    assert review.manifest_fields == ("hair_structure",)
    serialized = json.dumps(review.to_dict(), ensure_ascii=False)
    assert "crimson long hair" not in serialized
    assert "gothic cathedral" not in serialized


def test_field_result_and_failure_type_are_stable() -> None:
    manifest = _manifest(footwear_category="combat boots")
    observations = _observations(
        manifest,
        footwear_category={
            "observed": "high heels",
            "result": "FAIL",
            "failure_types": ["TYPE 3 ImageGen Archetype Substitution"],
        },
    )
    review = VisualAdherenceCritic().review(IMAGE, manifest=manifest, observations=observations)

    assert review.overall_result == "FAIL"
    assert review.field_results["footwear_category"] == {
        "required": "combat boots",
        "observed": "high heels",
        "result": "FAIL",
        "failure_types": ["TYPE 3"],
        "rationale": "",
    }
    assert review.failure_types == ("TYPE 3",)
    assert review.repair_targets[0]["field"] == "footwear_category"


@pytest.mark.parametrize(
    ("field", "expected_type"),
    [
        ("hair_structure", "TYPE 1"),
        ("horn_topology", "TYPE 2"),
        ("costume_topology", "TYPE 3"),
        ("palette_family", "TYPE 4"),
        ("architecture_presence", "TYPE 5"),
        ("footwear_category", "TYPE 6"),
    ],
)
def test_failure_type_labels_are_normalized(field: str, expected_type: str) -> None:
    manifest = _manifest(**{field: "required"})
    observations = _observations(
        manifest,
        **{
            field: {
                "observed": "wrong",
                "result": "FAIL",
                "failure_types": [expected_type],
            }
        },
    )
    review = VisualAdherenceCritic().review(IMAGE, manifest=manifest, observations=observations)
    assert expected_type in review.failure_types


def test_manifest_driven_not_evaluable_and_background_fields() -> None:
    manifest = {
        "hard_constraints": {},
        "strong_preferences": {"palette_family": "deep teal / crimson"},
        "pose_specification": {},
        "background_specification": {
            "environment_type": "minimal stage-like environment",
            "architecture_presence": "none",
            "spatial_structure": "shallow depth",
        },
    }
    observations = {**_anatomy(), "field_results": {"palette_family": {"observed": "deep teal / crimson", "result": "PASS"}}}
    review = VisualAdherenceCritic().review(IMAGE, manifest=manifest, observations=observations)

    assert review.field_results["environment_type"]["result"] == "NOT_EVALUABLE"
    assert "architecture_presence" in review.not_evaluable_fields
    assert "TYPE 5" not in review.failure_types
    assert review.overall_result == "PARTIAL"


def test_anatomy_report_covers_hands_and_feet() -> None:
    manifest = _manifest(hair_structure="braided side mass")
    review = VisualAdherenceCritic().review(
        IMAGE,
        manifest=manifest,
        observations={
            "field_results": {"hair_structure": {"observed": "braided side mass", "result": "PASS"}},
            "hand_anatomy_check": {"result": "PASS", "finger_count": "clear", "palm": "visible"},
            "foot_visibility_and_integrity_check": {"result": "PASS", "visible_or_occluded": "visible", "impossible_shoe_attachment": "none"},
        },
    )

    assert review.anatomy_check["result"] == "PASS"
    assert review.anatomy_check["hand_anatomy_check"]["finger_count"] == "clear"
    assert review.anatomy_check["foot_visibility_and_integrity_check"]["visible_or_occluded"] == "visible"


def test_anatomy_failure_is_type_six_and_repairable() -> None:
    manifest = _manifest(footwear_category="barefoot")
    review = VisualAdherenceCritic().review(
        IMAGE,
        manifest=manifest,
        observations={
            "field_results": {"footwear_category": {"observed": "barefoot", "result": "PASS"}},
            "hand_anatomy_check": {"result": "FAIL", "finger_fusion": "present"},
            "foot_visibility_and_integrity_check": {"result": "PASS"},
        },
    )

    assert review.overall_result == "FAIL"
    assert review.failure_types == ("TYPE 6",)
    assert review.repair_targets[-1]["field"] == "anatomy_check"


def test_prompt_hash_and_replay_round_trip_are_stable() -> None:
    manifest = _manifest(palette_family="deep teal / crimson")
    review = VisualAdherenceCritic().review(
        IMAGE,
        manifest=manifest,
        observations=_observations(manifest),
        prompt_bundle_metadata={"prompt": "stable prompt"},
    )
    restored = review.from_dict(review.to_dict())

    assert review.prompt_hash
    assert restored.to_dict() == review.to_dict()


def test_acceptance_fixtures_a_to_d_pass_with_labeled_observations() -> None:
    fixtures = {
        "A": {"environment_type": "abstract graphic field", "architecture_presence": "none", "right_hand_gesture": "open palm outward", "footwear_category": "flat boots"},
        "B": {"environment_type": "industrial support setting", "architecture_presence": "support structures", "right_arm_action": "extended forward", "footwear_category": "barefoot with ankle ornament"},
        "C": {"hair_structure": "braided side mass", "footwear_category": "combat boots", "environment_type": "minimal stage-like environment", "background_complexity": "low"},
        "D": {"costume_topology": "tailored trousers", "wing_strategy": "symbolic wings", "architecture_presence": "dominant", "right_arm_action": "resting at waist"},
    }
    for fixture in fixtures.values():
        manifest = _manifest(**fixture)
        review = VisualAdherenceCritic().review(IMAGE, manifest=manifest, observations=_observations(manifest))
        assert review.overall_result == "PASS"


def test_runtime_and_workflow_persist_review_for_replay(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("快速画一个成年魅魔角色")
    session = runtime.load_session(response.session_id)
    assert session.compiled_prompt and session.final_design
    runtime.record_generation_artifact(session.session_id, IMAGE)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = manifest["hard_constraints"] | manifest["strong_preferences"]
    observations = {
        "field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()},
        **_anatomy(),
    }

    direct = runtime.record_visual_adherence_review(session.session_id, IMAGE, observations=observations)
    replay = runtime.replay_session(session.session_id)

    assert direct == replay["visual_adherence_review"]
    assert (tmp_path / session.session_id / "artifacts" / "visual_adherence_review.json").is_file()


def test_workflow_runner_exposes_review_seam(tmp_path: Path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    response = runner.start_workflow("快速给我来一个粉发成年女性", mode="QUICK")
    workflow = runner.load_workflow(response.run_id)
    session = runner.runtime.load_session(workflow.session_id)
    runner.record_generation_artifact(response.run_id, IMAGE)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = manifest["hard_constraints"] | manifest["strong_preferences"]
    observations = {
        "field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()},
        **_anatomy(),
    }

    review = runner.record_visual_adherence_review(response.run_id, IMAGE, observations=observations)

    assert review["overall_result"] == "PASS"
    assert runner.runtime.replay_session(workflow.session_id)["visual_adherence_review"] == review


def test_invalid_actual_image_is_rejected() -> None:
    with pytest.raises(VisualAdherenceError):
        VisualAdherenceCritic().review("missing-image.png", manifest=_manifest(hair_structure="braided"), observations={})
