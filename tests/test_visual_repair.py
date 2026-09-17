"""Focused non-image tests for the bounded targeted visual repair loop."""

from __future__ import annotations

from pathlib import Path
import json
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.interaction_runtime import InteractionRuntime  # noqa: E402
from runtime.visual_adherence_critic import VisualAdherenceReview  # noqa: E402
from runtime.workflow_runner import PersistentWorkflowRunner  # noqa: E402
from runtime.visual_repair import (  # noqa: E402
    VisualRepairError,
    build_repair_plan,
    compile_repair_prompt,
    evaluate_repair_attempt,
    initial_best_artifact,
    select_best_artifact,
    should_repair,
)
from runtime.regional_style_runtime import build_visual_specification_contract  # noqa: E402


IMAGE = Path(__file__)


def _review(
    values: dict[str, tuple[str, str, str | None]],
    *,
    image: str = "original.png",
    prompt_hash: str = "source-prompt",
) -> VisualAdherenceReview:
    fields = {}
    targets = []
    for name, (required, result, observed) in values.items():
        failure_types = ["TYPE 3"] if result == "FAIL" else ["TYPE 4"] if result == "PARTIAL" else []
        fields[name] = {"required": required, "observed": observed, "result": result, "failure_types": failure_types, "rationale": ""}
        if result in {"FAIL", "PARTIAL"}:
            targets.append({"field": name, "required": required, "observed": observed, "result": result, "failure_types": failure_types})
    overall = "FAIL" if any(item["result"] == "FAIL" for item in fields.values()) else "PARTIAL" if targets else "PASS"
    return VisualAdherenceReview(
        image,
        overall,
        fields,
        tuple(sorted({code for item in fields.values() for code in item["failure_types"]})),
        (),
        {"result": "PASS"},
        tuple(targets),
        "test review",
        prompt_hash=prompt_hash,
    )


def _plan(review: VisualAdherenceReview, *, explicit: tuple[str, ...] = (), include_minor: bool = True):
    hard = {name: item["required"] for name, item in review.field_results.items()}
    return build_repair_plan(
        review,
        manifest={"hard_constraints": hard},
        visual_specification_contract={"hard_constraints": hard, "explicit_hard_fields": list(explicit), "anti_substitution": {}},
        repair_attempt=1,
        include_minor=include_minor,
    )


def test_repair_plan_uses_only_critic_targets_and_locks_pass_hard_fields() -> None:
    review = _review(
        {
            "hair_structure": ("braided medium", "PASS", "braided medium"),
            "costume_topology": ("structured open top", "PASS", "structured open top"),
            "lower_body_structure": ("fitted trousers", "PASS", "fitted trousers"),
            "footwear_category": ("combat boots", "PASS", "combat boots"),
            "pose_family": ("OPEN_PARALLEL_STANCE", "PASS", "OPEN_PARALLEL_STANCE"),
            "head_attitude": ("chin raised", "PARTIAL", "level chin"),
            "architecture_language": ("modern geometric", "PARTIAL", "gothic"),
        }
    )
    plan = _plan(review)

    assert [item["field"] for item in plan.repair_targets] == ["head_attitude", "architecture_language"]
    assert set(plan.locked_fields) == {"hair_structure", "costume_topology", "lower_body_structure", "footwear_category", "pose_family"}


def test_repair_prompt_has_no_unrelated_repair_instruction() -> None:
    review = _review({"hair_structure": ("braided medium", "PASS", "braided medium"), "background": ("minimal stage", "PARTIAL", "busy city")})
    plan = _plan(review)
    bundle = compile_repair_prompt(
        {"prompt": "current hard specification", "visual_context_firewall_applied": True, "rendering_foundation": "gacha anime"},
        plan,
    )

    target_section = bundle.prompt.split("## TARGETED REPAIR", 1)[1].split("## UNCHANGED HARD SPECIFICATION", 1)[0]
    assert "background" in target_section
    assert "Strengthen only hair_structure" not in target_section
    assert "redesign" not in target_section.lower()


def test_repair_prompt_keeps_target_priority_and_preservation_as_separate_sections() -> None:
    review = _review({"hair_structure": ("braided medium", "PASS", "braided medium"), "background": ("minimal stage", "PARTIAL", "busy city")})
    bundle = compile_repair_prompt({"prompt": "current hard specification", "visual_context_firewall_applied": True}, _plan(review))
    assert bundle.prompt.index("## LOCKED / PRESERVE EXACTLY") < bundle.prompt.index("## TARGETED REPAIR")
    assert bundle.prompt.index("## TARGETED REPAIR") < bundle.prompt.index("## UNCHANGED HARD SPECIFICATION")
    assert "hair_structure: braided medium" in bundle.prompt


def test_repair_module_does_not_expose_character_design_entrypoints() -> None:
    source = (Path(__file__).resolve().parents[1] / "runtime" / "visual_repair.py").read_text(encoding="utf-8")
    assert "CandidateGenerator" not in source
    assert "DesignDNA" not in source
    assert "AI_DECIDE" not in source


def test_explicit_user_field_is_critical() -> None:
    review = _review({"footwear_category": ("barefoot", "FAIL", "high heels")})
    plan = _plan(review, explicit=("footwear_category",))
    assert plan.repair_targets[0]["repair_severity"] == "CRITICAL"


def test_type_3_is_replacement_and_type_4_is_strengthen_only() -> None:
    replacement = _plan(_review({"footwear_category": ("combat boots", "FAIL", "high heels")}))
    fine_grained = _plan(_review({"head_attitude": ("chin raised", "PARTIAL", "level chin")}))

    assert replacement.repair_instructions[0]["strategy"] == "replacement"
    assert "Replace" in replacement.repair_instructions[0]["text"]
    assert fine_grained.repair_instructions[0]["strategy"] == "strengthen_only"
    assert "Strengthen only" in fine_grained.repair_instructions[0]["text"]


def test_minor_partial_can_be_excluded_by_policy() -> None:
    review = _review({"head_attitude": ("chin raised", "PARTIAL", "level chin")})
    plan = _plan(review, include_minor=True)
    assert plan.repair_targets
    assert should_repair(plan) is False
    assert should_repair(plan, include_minor=True) is True


def test_re_review_is_required_before_success() -> None:
    plan = _plan(_review({"background": ("minimal stage", "PARTIAL", "busy city")}))
    assert evaluate_repair_attempt(_review({"background": ("minimal stage", "PARTIAL", "busy city")}), None, plan)["outcome"] == "FAILED"


def test_regression_is_detected_and_original_best_is_preserved() -> None:
    before = _review({"footwear_category": ("combat boots", "PASS", "combat boots"), "background": ("minimal", "PARTIAL", "busy")})
    after = _review({"footwear_category": ("combat boots", "FAIL", "heels"), "background": ("minimal", "PASS", "minimal")})
    plan = _plan(before)
    result = evaluate_repair_attempt(before, after, plan)
    original = initial_best_artifact(before)
    candidate = {"image": "repair.png", "prompt_hash": "repair", "review_id": "after"}

    assert result["outcome"] == "REGRESSION"
    assert select_best_artifact(original, candidate, before, after, outcome=result["outcome"]) == original


@pytest.mark.parametrize(
    ("before_result", "after_result", "expected"),
    [("FAIL", "PASS", "SUCCESS"), ("FAIL", "PARTIAL", "PARTIAL_SUCCESS"), ("PARTIAL", "PARTIAL", "NO_IMPROVEMENT")],
)
def test_repair_outcomes(before_result: str, after_result: str, expected: str) -> None:
    before = _review({"background": ("minimal", before_result, "wrong")})
    after = _review({"background": ("minimal", after_result, "still wrong")})
    assert evaluate_repair_attempt(before, after, _plan(before))["outcome"] == expected


def test_best_artifact_updates_only_on_adherence_improvement() -> None:
    before = _review({"background": ("minimal", "FAIL", "busy")})
    after = _review({"background": ("minimal", "PASS", "minimal")}, image="repair.png", prompt_hash="repair-prompt")
    original = initial_best_artifact(before)
    candidate = {"image": "repair.png", "prompt_hash": "repair-prompt", "review_id": "after"}

    selected = select_best_artifact(original, candidate, before, after, outcome="SUCCESS")
    assert selected["image"] == "repair.png"
    assert selected["selection_basis"] == "adherence_only"


def test_max_attempts_and_successful_target_removal() -> None:
    review = _review({"head_attitude": ("chin raised", "PARTIAL", "level"), "architecture_language": ("modern", "PARTIAL", "gothic")})
    with pytest.raises(VisualRepairError, match="REPAIR_EXHAUSTED"):
        build_repair_plan(review, repair_attempt=3, max_attempts=2)
    after = _review({"head_attitude": ("chin raised", "PASS", "raised"), "architecture_language": ("modern", "PARTIAL", "gothic")})
    next_plan = _plan(after)
    assert [item["field"] for item in next_plan.repair_targets] == ["architecture_language"]


def test_plan_has_source_linkage_and_round_trips() -> None:
    plan = _plan(_review({"background": ("minimal", "PARTIAL", "busy")}, image=str(IMAGE)))
    restored = plan.from_dict(plan.to_dict())
    assert plan.source_review_id
    assert plan.source_prompt_hash == "source-prompt"
    assert restored.to_dict() == plan.to_dict()


def test_repair_compilation_does_not_mutate_original_or_accept_history_context() -> None:
    original = {"prompt": "current prompt", "visual_context_firewall_applied": True, "history": "crimson long hair; gothic cathedral"}
    snapshot = dict(original)
    bundle = compile_repair_prompt(original, _plan(_review({"background": ("minimal", "PARTIAL", "busy")})))
    assert original == snapshot
    assert "crimson long hair" not in bundle.prompt
    assert "gothic cathedral" not in bundle.prompt


def test_repair_compilation_fails_closed_without_visual_firewall() -> None:
    with pytest.raises(VisualRepairError, match="Visual Context Firewall"):
        compile_repair_prompt({"prompt": "current prompt", "visual_context_firewall_applied": False}, _plan(_review({"background": ("minimal", "PARTIAL", "busy")})))


def test_anatomy_failure_is_a_repair_target() -> None:
    review = _review({"footwear_category": ("combat boots", "PASS", "combat boots")})
    anatomy_target = VisualAdherenceReview(
        review.actual_image,
        "FAIL",
        review.field_results,
        ("TYPE 6",),
        (),
        {"result": "FAIL"},
        ({"field": "anatomy_check", "result": "FAIL", "failure_types": ["TYPE 6"]},),
        "anatomy",
        prompt_hash=review.prompt_hash,
    )
    plan = _plan(anatomy_target)
    assert plan.repair_targets[0]["field"] == "anatomy_check"
    assert plan.repair_targets[0]["repair_severity"] == "MAJOR"


def test_workflow_runner_exposes_repair_status_and_plan(tmp_path: Path) -> None:
    runner = PersistentWorkflowRunner(tmp_path)
    response = runner.start_workflow("adult succubus character", mode="QUICK", seed=11)
    session = runner.runtime.load_session(response.session_id)
    runner.record_generation_artifact(response.run_id, IMAGE)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = {name: value for source in ("hard_constraints", "strong_preferences", "pose_specification", "background_specification") for name, value in manifest.get(source, {}).items()}
    observations = {"field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()}, "hand_anatomy_check": {"result": "PASS"}, "foot_visibility_and_integrity_check": {"result": "PASS"}}
    first_field = next(iter(fields))
    observations["field_results"][first_field] = {"observed": "wrong", "result": "FAIL"}
    runner.record_visual_adherence_review(response.run_id, IMAGE, observations=observations)
    planned = runner.build_visual_repair_plan(response.run_id)
    assert planned["status"] == "REPAIR_PLANNED"
    assert runner.load_workflow(response.run_id).status == "REPAIR_PLANNED"


def test_runtime_persists_repair_replay_and_idempotent_resume(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=7)
    session = runtime.load_session(response.session_id)
    original_artifact = runtime.record_generation_artifact(response.session_id, IMAGE)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = {name: value for source in ("hard_constraints", "strong_preferences", "pose_specification", "background_specification") for name, value in manifest.get(source, {}).items()}
    observations = {"field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()}, "hand_anatomy_check": {"result": "PASS"}, "foot_visibility_and_integrity_check": {"result": "PASS"}}
    first_field = next(iter(fields))
    observations["field_results"][first_field] = {"observed": "wrong", "result": "FAIL", "failure_types": ["TYPE 3"]}
    runtime.record_visual_adherence_review(response.session_id, IMAGE, observations=observations)

    planned = runtime.build_visual_repair_plan(response.session_id)
    attempt_id = planned["attempt_id"]
    prompt = planned["repair_prompt"]["prompt"]
    generated = runtime.record_visual_repair_generation(response.session_id, attempt_id, IMAGE, repair_prompt=prompt)
    assert generated["status"] == "REPAIR_GENERATED"
    assert runtime.record_visual_repair_generation(response.session_id, attempt_id, IMAGE)["image"] == str(IMAGE)
    observations["field_results"][first_field] = {"observed": fields[first_field], "result": "PASS"}
    reviewed = runtime.record_visual_repair_review(response.session_id, attempt_id, observations=observations)
    replay = runtime.replay_session(response.session_id)

    assert reviewed["outcome"] == "SUCCESS"
    assert runtime.record_visual_repair_review(response.session_id, attempt_id, observations=observations) == reviewed
    assert replay["repair_attempts"][0]["repair_result"] == reviewed
    assert replay["best_artifact"]["image"] == str(IMAGE)
    assert replay["generation_artifact"]["generation_id"] == original_artifact["generation_id"]
    assert replay["best_artifact"]["generation_id"] == generated["generation_id"]
    assert (tmp_path / response.session_id / "artifacts" / "repair" / "attempt_01" / "repair_plan.json").is_file()
    assert (tmp_path / response.session_id / "artifacts" / "repair" / "attempt_01" / "repair_prompt.txt").read_text(encoding="utf-8") == prompt


def _strong_plan(review: VisualAdherenceReview):
    return build_repair_plan(
        review,
        manifest={
            "hard_constraints": {"architecture_language": "modern geometric"},
            "strong_preferences": {"palette_family": "violet / graphite"},
        },
        visual_specification_contract={
            "hard_constraints": {"architecture_language": "modern geometric"},
            "strong_preferences": {"palette_family": "violet / graphite"},
            "anti_substitution": {},
        },
    )


def test_lower_body_structure_is_an_independent_hard_lock() -> None:
    review = _review({
        "costume_topology": ("tailored trousers + open top", "PASS", "tailored trousers + open top"),
        "lower_body_structure": ("fitted trousers", "PASS", "fitted trousers"),
        "architecture_language": ("modern geometric", "PARTIAL", "gothic"),
    })
    plan = _plan(review)
    assert plan.locked_fields["lower_body_structure"] == "fitted trousers"
    assert plan.locked_fields["costume_topology"] == "tailored trousers + open top"
    assert any(item["field"] == "lower_body_structure" and item["strength"] == "HARD" for item in plan.anti_regression_constraints)


def test_lower_body_regression_is_classified_as_hard_regression() -> None:
    before = _review({"lower_body_structure": ("fitted trousers", "PASS", "fitted trousers")})
    after = _review({"lower_body_structure": ("fitted trousers", "FAIL", "skirt")})
    result = evaluate_repair_attempt(before, after, _plan(before))
    assert result["outcome"] == "REGRESSION"
    assert result["regressions"] == [{"field": "lower_body_structure", "before": "PASS", "after": "FAIL", "class": "HARD_REGRESSION"}]


def test_palette_pass_is_preserved_without_becoming_a_hard_lock() -> None:
    review = _review({"palette_family": ("violet / graphite", "PASS", "violet / graphite"), "architecture_language": ("modern geometric", "PARTIAL", "gothic")})
    plan = _strong_plan(review)
    assert "palette_family" not in plan.locked_fields
    assert plan.preserve_fields["palette_family"] == "violet / graphite"
    assert any(item["field"] == "palette_family" and item["strength"] == "STRONG" for item in plan.anti_regression_constraints)
    bundle = compile_repair_prompt({"prompt": "current prompt", "visual_context_firewall_applied": True}, plan)
    assert "Maintain the established palette_family: violet / graphite." in bundle.prompt


def test_palette_remains_a_strong_visual_preference_globally() -> None:
    contract = build_visual_specification_contract(design_dna={"palette_family": "violet / graphite"})
    assert contract.strong_preferences["palette_family"] == "violet / graphite"
    assert "palette_family" not in contract.hard_constraints


def test_palette_regression_is_classified_as_strong_preference_regression() -> None:
    before = _review({"palette_family": ("violet / graphite", "PASS", "violet / graphite"), "architecture_language": ("modern geometric", "PARTIAL", "gothic")})
    after = _review({"palette_family": ("violet / graphite", "FAIL", "crimson / gold"), "architecture_language": ("modern geometric", "PASS", "modern geometric")})
    result = evaluate_repair_attempt(before, after, _strong_plan(before))
    assert result["outcome"] == "REGRESSION"
    assert result["regressions"][0]["class"] == "STRONG_PREFERENCE_REGRESSION"


def test_generation_artifact_persists_exact_original_chain(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=19)
    artifact = runtime.record_generation_artifact(response.session_id, IMAGE, run_id="run-19")
    session = runtime.load_session(response.session_id)
    assert artifact["generation_id"] == "run-19:original"
    assert artifact["image_hash"] and artifact["prompt_hash"]
    assert artifact["run_id"] == "run-19"
    assert session.artifact_continuity == "strict_complete"
    original = tmp_path / response.session_id / "artifacts" / "generation" / "original"
    assert (original / "generation.json").is_file()
    assert (original / "prompt.txt").read_text(encoding="utf-8") == session.compiled_prompt["prompt"]
    assert (original / "prompt_adherence_manifest.json").is_file()
    assert (original / "visual_specification_contract.json").is_file()
    assert (original / "image_metadata.json").is_file()


def test_review_is_bound_to_generation_identity(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=20)
    artifact = runtime.record_generation_artifact(response.session_id, IMAGE, run_id="run-20")
    review = runtime.record_visual_adherence_review(response.session_id, IMAGE, observations={"hand_anatomy_check": {"result": "PASS"}, "foot_visibility_and_integrity_check": {"result": "PASS"}})
    assert review["generation_id"] == artifact["generation_id"]
    assert review["actual_image_hash"] == artifact["image_hash"]
    assert review["prompt_hash"] == artifact["prompt_hash"]
    assert (tmp_path / response.session_id / "artifacts" / "generation" / "original" / "visual_adherence_review.json").is_file()


def _runtime_with_failed_review(tmp_path: Path):
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=21)
    artifact = runtime.record_generation_artifact(response.session_id, IMAGE, run_id="run-21")
    session = runtime.load_session(response.session_id)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = {name: value for source in ("hard_constraints", "strong_preferences", "pose_specification", "background_specification") for name, value in manifest.get(source, {}).items()}
    observations = {"field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()}, "hand_anatomy_check": {"result": "PASS"}, "foot_visibility_and_integrity_check": {"result": "PASS"}}
    first = next(iter(fields))
    observations["field_results"][first] = {"observed": "wrong", "result": "FAIL"}
    runtime.record_visual_adherence_review(response.session_id, IMAGE, observations=observations)
    return runtime, response, artifact


@pytest.mark.parametrize("tampered", ["image_hash", "prompt_hash"])
def test_repair_rejects_mismatched_source_hash(tmp_path: Path, tampered: str) -> None:
    runtime, response, _ = _runtime_with_failed_review(tmp_path)
    session = runtime.load_session(response.session_id)
    session.generation_artifact[tampered] = "tampered"
    runtime._save(session)
    with pytest.raises(VisualRepairError, match="REPAIR_SOURCE_MISMATCH"):
        runtime.build_visual_repair_plan(response.session_id)


def test_repair_rejects_mismatched_source_generation_id(tmp_path: Path) -> None:
    runtime, response, _ = _runtime_with_failed_review(tmp_path)
    session = runtime.load_session(response.session_id)
    session.visual_adherence_review["generation_id"] = "other-generation"
    runtime._save(session)
    with pytest.raises(VisualRepairError, match="REPAIR_SOURCE_MISMATCH"):
        runtime.build_visual_repair_plan(response.session_id)


def test_best_artifact_carries_generation_identity(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=22)
    artifact = runtime.record_generation_artifact(response.session_id, IMAGE, run_id="run-22")
    session = runtime.load_session(response.session_id)
    manifest = session.compiled_prompt["prompt_adherence_manifest"]
    fields = {name: value for source in ("hard_constraints", "strong_preferences", "pose_specification", "background_specification") for name, value in manifest.get(source, {}).items()}
    observations = {"field_results": {name: {"observed": value, "result": "PASS"} for name, value in fields.items()}, "hand_anatomy_check": {"result": "PASS"}, "foot_visibility_and_integrity_check": {"result": "PASS"}}
    runtime.record_visual_adherence_review(response.session_id, IMAGE, observations=observations)
    best = runtime.load_session(response.session_id).best_artifact
    assert best["generation_id"] == artifact["generation_id"]
    assert best["image_hash"] == artifact["image_hash"]
    assert best["source_type"] == "original"


def test_replay_does_not_invoke_critic_or_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime, response, _ = _runtime_with_failed_review(tmp_path)
    monkeypatch.setattr("runtime.interaction_runtime.VisualAdherenceCritic.review", lambda *args, **kwargs: pytest.fail("replay invoked critic"))
    replay = runtime.replay_session(response.session_id)
    assert replay["generation_artifact"]["generation_id"]
    assert replay["visual_adherence_review"]


def test_legacy_session_is_readable_but_marked_incomplete(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    (legacy / "creative_session.json").write_text(json.dumps({"session_id": "legacy", "input": "old character", "state": "COMPLETED"}), encoding="utf-8")
    session = InteractionRuntime(tmp_path).load_session("legacy")
    assert session.artifact_continuity == "legacy_incomplete"
    assert session.generation_artifact is None
    assert InteractionRuntime(tmp_path).replay_session("legacy")["artifact_continuity"] == "legacy_incomplete"


def test_new_session_cannot_enter_repair_without_complete_generation_artifact(tmp_path: Path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("adult succubus character", "QUICK", seed=23)
    session = runtime.load_session(response.session_id)
    assert session.artifact_continuity == "strict_pending_generation"
    session.visual_adherence_review = {"overall_result": "FAIL", "repair_targets": [{"field": "background"}]}
    runtime._save(session)
    with pytest.raises(VisualRepairError, match="strict generation artifact"):
        runtime.build_visual_repair_plan(response.session_id)
