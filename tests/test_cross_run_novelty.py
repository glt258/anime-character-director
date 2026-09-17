"""Targeted tests for the post-design CrossRunNoveltyGuard boundary."""

from __future__ import annotations

import json

from runtime.cross_run_novelty import DesignSignature, NoveltyGuard, NoveltyPolicy, snapshot_history
from runtime.interaction_runtime import CreationMode, InteractionRuntime
from runtime.visual_context_firewall import VisualContextFirewall


def _design(**changes: object) -> dict:
    dna = {
        "silhouette_family": "hourglass long drape",
        "hair_structure": "long flowing",
        "horn_topology": "large ram horns",
        "upper_body_structure": "fitted wrap bodice",
        "lower_body_structure": "asymmetric skirt",
        "costume_topology": "high-slit dress",
        "exposure_strategy": "controlled side exposure",
        "legwear_strategy": "black sheer stockings",
        "footwear_category": "high heels",
        "accessory_density": "sparse anchor",
        "pose_family": "SENSUAL",
        "body_line_emphasis": "hourglass waist-to-hip",
        "tail_design": "heart tail",
        "wing_strategy": "large physical wings",
        "palette_family": "red and black",
        "material_language": "satin and leather",
        "background_family": "gothic cathedral",
        "pose_specification": {
            "lower_body_pose": "separated stance",
            "torso_orientation": "front-facing",
            "arm_configuration": "one raised one lowered",
            "left_hand_gesture": "hand near face",
            "right_hand_gesture": "relaxed fingers",
        },
        "background_specification": {
            "environment_type": "cathedral interior",
            "architecture_presence": "strong",
            "spatial_structure": "deep nave perspective",
        },
    }
    visual = {
        "hair_color": "crimson",
        "eye_color": "gold",
        "dominant_palette": "red and black",
        "major_accessories": "sparse anchor",
        "background_direction": "gothic cathedral",
        "hair_style_family": "long flowing",
        "outfit_direction": "high-slit dress",
        "footwear_family": "high heels",
        "legwear_family": "black sheer stockings",
        "exposure_strategy": "controlled side exposure",
    }
    pose = dict(dna["pose_specification"])
    background = dict(dna["background_specification"])
    for key, value in changes.items():
        if key in dna:
            dna[key] = value
        elif key in visual:
            visual[key] = value
        elif key in pose:
            pose[key] = value
        elif key in background:
            background[key] = value
        else:
            raise KeyError(key)
    dna["pose_specification"] = pose
    dna["background_specification"] = background
    return {
        "character_identity": "adult succubus",
        "character_visual_style": "commercial gacha anime",
        "design_dna": dna,
        "visual_preferences": visual,
        "lower_body": {"footwear_family": visual["footwear_family"], "legwear_family": visual["legwear_family"]},
        "pose_specification": pose,
        "background_specification": background,
        "explicit_user_constraints": {},
        "prompt": "never enters signature extraction",
    }


def _prior(run_id: str = "prior-a", created_at: str = "2026-09-01T00:00:00Z", design: dict | None = None) -> dict:
    current = design or _design()
    return {
        "run_id": run_id,
        "generation_id": f"{run_id}:original",
        "created_at": created_at,
        "mode": "AI_DECIDE",
        "inheritance_status": "fresh",
        "design_signature": DesignSignature.from_final_design(current).to_dict(),
    }


def test_signature_extraction_is_structured_and_omits_prompt() -> None:
    signature = DesignSignature.from_final_design(_design())
    data = signature.to_dict()
    assert data["fields"]["costume_topology"] == "high-slit dress"
    assert data["fields"]["lower_body_pose"] == "separated stance"
    assert data["fields"]["architecture_presence"] == "strong"
    assert "prompt" not in json.dumps(data, ensure_ascii=False)


def test_signature_round_trip_is_stable() -> None:
    signature = DesignSignature.from_final_design(_design())
    assert DesignSignature.from_dict(signature.to_dict()).to_dict() == signature.to_dict()


def test_cosmetic_only_reskin_fails() -> None:
    review = NoveltyGuard.evaluate(DesignSignature.from_final_design(_design(hair_color="silver", palette_family="blue and black")), [_prior()])
    assert review.novelty_result == "FAIL"
    assert review.structural_similarity > review.cosmetic_similarity
    assert "hair_color" in review.different_fields


def test_structural_redesign_passes_with_same_archetype() -> None:
    current = _design(
        silhouette_family="narrow vertical",
        hair_structure="layered bob",
        horn_topology="rear blade horns",
        upper_body_structure="open structured top",
        lower_body_structure="fitted trousers",
        costume_topology="tailored trousers plus open top",
        footwear_category="platform shoes",
        wing_strategy="symbolic motif",
        pose_family="WIDE_GROUNDED",
        lower_body_pose="wide grounded stance",
        torso_orientation="stable frontal",
        arm_configuration="arm extended sideways",
        left_hand_gesture="open palm",
        right_hand_gesture="relaxed fingers",
        palette_family="violet and graphite",
        background_family="abstract spotlight",
        environment_type="abstract stage",
        architecture_presence="none",
        spatial_structure="flat graphic planes",
    )
    assert NoveltyGuard.evaluate(DesignSignature.from_final_design(current), [_prior()]).novelty_result == "PASS"


def test_borderline_fixture_matches_silhouette_and_horns_only() -> None:
    current = _design(
        costume_topology="tailored bodice and cropped shorts",
        lower_body_structure="fitted trousers",
        footwear_category="platform shoes",
        wing_strategy="symbolic motif",
        pose_family="WIDE_GROUNDED",
        lower_body_pose="wide grounded stance",
        arm_configuration="arm extended sideways",
    )
    review = NoveltyGuard.evaluate(DesignSignature.from_final_design(current), [_prior()])
    assert review.novelty_result == "BORDERLINE"
    assert set(("silhouette_family", "horn_topology")).issubset(review.matching_fields)


def test_explicit_variation_is_exempt() -> None:
    review = NoveltyGuard.evaluate(DesignSignature.from_final_design(_design()), [_prior()], inherit_previous_visuals=True)
    assert review.novelty_result == "EXEMPT"


def test_partial_inheritance_does_not_fail_when_structure_differs() -> None:
    current = _design(
        silhouette_family="narrow vertical",
        costume_topology="tailored trousers plus open top",
        lower_body_structure="fitted trousers",
        footwear_category="platform shoes",
        pose_family="WIDE_GROUNDED",
        lower_body_pose="wide grounded stance",
        wing_strategy="symbolic motif",
        hair_color="crimson",
    )
    review = NoveltyGuard.evaluate(DesignSignature.from_final_design(current), [_prior()], allowed_visual_inheritance=("hair_color=crimson",))
    assert review.novelty_result == "EXEMPT"


def test_background_only_change_cannot_pass_high_structural_collision() -> None:
    current = _design(background_family="abstract spotlight", environment_type="abstract stage", architecture_presence="none", spatial_structure="flat graphic planes")
    assert NoveltyGuard.evaluate(DesignSignature.from_final_design(current), [_prior()]).novelty_result == "FAIL"


def test_pose_structure_is_compared_beyond_pose_family_label() -> None:
    current = _design(pose_family="OTHER_LABEL")
    review = NoveltyGuard.evaluate(DesignSignature.from_final_design(current), [_prior()])
    assert review.structural_similarity >= 0.70
    assert "lower_body_pose" in review.matching_fields


def test_quick_chooses_next_deterministic_candidate() -> None:
    candidates = [{"id": "A", "final_design": _design()}, {"id": "B", "final_design": _design(silhouette_family="narrow vertical", costume_topology="tailored trousers", lower_body_structure="fitted trousers", footwear_category="platform shoes", pose_family="WIDE_GROUNDED", lower_body_pose="wide grounded stance", wing_strategy="symbolic motif")}]
    result = NoveltyGuard.resolve_quick_candidates(candidates, 0, [_prior()])
    assert result["selected"]["id"] == "B"
    assert result["resolution"] == "DETERMINISTIC_ALTERNATE"
    assert result == NoveltyGuard.resolve_quick_candidates(candidates, 0, [_prior()])


def test_ai_filters_failures_after_quality_validation() -> None:
    candidates = [
        {"id": "A", "final_design": _design(), "quality_valid": True},
        {"id": "B", "final_design": _design(silhouette_family="narrow vertical", hair_structure="layered bob", horn_topology="rear blade horns", upper_body_structure="open structured top", costume_topology="tailored trousers", lower_body_structure="fitted trousers", footwear_category="platform shoes", pose_family="WIDE_GROUNDED", lower_body_pose="wide grounded stance", torso_orientation="stable frontal", arm_configuration="arm extended sideways", left_hand_gesture="open palm", right_hand_gesture="relaxed fingers", wing_strategy="symbolic motif"), "quality_valid": True},
        {"id": "C", "final_design": _design(costume_topology="tailored bodice and cropped shorts", lower_body_structure="fitted trousers", footwear_category="platform shoes", wing_strategy="symbolic motif", pose_family="WIDE_GROUNDED", lower_body_pose="wide grounded stance", arm_configuration="arm extended sideways"), "quality_valid": True},
        {"id": "D", "final_design": _design(silhouette_family="narrow vertical", hair_structure="layered bob", horn_topology="rear blade horns", upper_body_structure="open structured top", costume_topology="tailored trousers", lower_body_structure="fitted trousers", footwear_category="platform shoes", pose_family="WIDE_GROUNDED", lower_body_pose="wide grounded stance", torso_orientation="stable frontal", arm_configuration="arm extended sideways", left_hand_gesture="open palm", right_hand_gesture="relaxed fingers", wing_strategy="symbolic motif"), "quality_valid": True},
    ]
    result = NoveltyGuard.filter_ai_candidates(candidates, [_prior()])
    assert [item["id"] for item in result["candidates"]] == ["B", "C", "D"]
    assert result["reviews"]["A"]["novelty_result"] == "FAIL"
    assert result["reviews"]["B"]["novelty_result"] == "PASS"
    assert result["reviews"]["C"]["novelty_result"] == "BORDERLINE"
    assert result["reviews"]["D"]["novelty_result"] == "PASS"


def test_user_explicit_choice_is_preserved_as_override() -> None:
    result = NoveltyGuard.evaluate_user_candidate(_design(), [_prior()], explicit_fields=("hair_style_family",))
    assert result["human_override_novelty"] is True
    assert result["candidate"]["design_dna"]["hair_structure"] == "long flowing"


def test_user_delegated_field_can_be_reresolved() -> None:
    result = NoveltyGuard.evaluate_user_candidate(_design(), [_prior()], delegated_fields=("footwear_family",))
    assert result["delegated_reresolution_allowed"] is True


def test_resolution_attempts_are_bounded() -> None:
    policy = NoveltyPolicy(max_resolution_attempts=2)
    candidates = [{"id": "A", "final_design": _design()}, {"id": "B", "final_design": _design(hair_color="silver")}]
    result = NoveltyGuard.resolve_quick_candidates(candidates, 0, [_prior()], policy=policy)
    assert result["resolution"] == "NOVELTY_EXHAUSTED"
    assert result["attempts"] == 2


def test_history_window_is_recent_and_configurable() -> None:
    old = _prior("old", "2026-01-01T00:00:00Z")
    recent = _prior("recent", "2026-09-01T00:00:00Z")
    snapshot = snapshot_history([old, recent], NoveltyPolicy(recent_n=1))
    assert [item["run_id"] for item in snapshot] == ["recent"]


def test_repair_artifacts_from_one_run_are_not_duplicate_history() -> None:
    duplicate = _prior("same-run", "2026-09-01T00:00:00Z")
    repair = _prior("same-run", "2026-09-02T00:00:00Z", _design(silhouette_family="narrow vertical"))
    assert len(snapshot_history([duplicate, repair])) == 1
    assert snapshot_history([duplicate, repair])[0]["generation_id"] == "same-run:original"


def test_history_snapshot_replay_is_stable_after_new_history() -> None:
    current = DesignSignature.from_final_design(_design(hair_color="silver"))
    snapshot = NoveltyGuard.snapshot_history([_prior()])
    first = NoveltyGuard.evaluate(current, history_snapshot=snapshot)
    later = NoveltyGuard.evaluate(current, [_prior("later", "2026-09-03T00:00:00Z", _design(silhouette_family="narrow vertical"))], history_snapshot=snapshot)
    assert later.to_dict() == first.to_dict()


def test_firewall_history_signature_has_no_positive_generation_path() -> None:
    history = _prior()
    firewall = VisualContextFirewall()
    context = firewall.generation_context(current_user_request="new succubus", historical_visual_context=history)
    analysis = firewall.anti_repetition_context(history)
    assert "design_signature" not in context
    assert "design_signature" in analysis["history"]


def test_runtime_keeps_history_marker_out_of_all_positive_generation_inputs(tmp_path) -> None:
    history = _prior()
    history["design_signature"]["fields"]["hair_color"] = "HISTORICAL_ONLY_MARKER"
    (tmp_path / "novelty_history.json").write_text(json.dumps([history], ensure_ascii=False), encoding="utf-8")
    response = InteractionRuntime(tmp_path).create_session("成年魅魔角色", CreationMode.QUICK, seed=3)
    session = InteractionRuntime(tmp_path).load_session(response.session_id)
    positive_inputs = {
        "character": session.character_explore_result,
        "art": session.art_explore_result,
        "preferences": session.visual_preference_sheet,
        "final_context": (session.final_design or {}).get("generation_context"),
        "prompt": (session.compiled_prompt or {}).get("prompt"),
    }
    assert "HISTORICAL_ONLY_MARKER" not in json.dumps(positive_inputs, ensure_ascii=False)


def test_runtime_evaluates_before_prompt_compilation_without_history_injection(tmp_path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("成年魅魔角色", CreationMode.QUICK, seed=3)
    session = runtime.load_session(response.session_id)
    assert session.novelty_status == "PASS"
    assert session.novelty_review is not None
    assert "history_snapshot" not in session.final_design["generation_context"]
    assert "design_signature" not in session.compiled_prompt["prompt"]


def test_runtime_persists_signature_and_replay(tmp_path) -> None:
    runtime = InteractionRuntime(tmp_path)
    response = runtime.create_session("成年魅魔角色", CreationMode.QUICK, seed=3)
    image = tmp_path / "image.png"
    image.write_bytes(b"test-image")
    runtime.record_generation_artifact(response.session_id, image)
    session = runtime.load_session(response.session_id)
    replay = runtime.replay_session(response.session_id)
    assert session.generation_artifact is not None
    assert session.design_signature is not None
    assert replay["design_signature"] == session.design_signature
    history = json.loads((tmp_path / "novelty_history.json").read_text(encoding="utf-8"))
    assert len(history) == 1 and history[0]["run_id"] == response.session_id


def test_runtime_uses_completed_history_only_for_novelty(tmp_path) -> None:
    runtime = InteractionRuntime(tmp_path)
    first = runtime.create_session("成年魅魔角色", CreationMode.QUICK, seed=3)
    image = tmp_path / "first.png"
    image.write_bytes(b"first-image")
    runtime.record_generation_artifact(first.session_id, image)
    second = runtime.create_session("成年魅魔角色", CreationMode.QUICK, seed=3)
    saved = runtime.load_session(second.session_id)
    assert saved.novelty_status == "PASS"
    assert saved.novelty_resolution_attempt == 1
    assert "history_snapshot" not in saved.final_design["generation_context"]


if __name__ == "__main__":
    test_cosmetic_only_reskin_fails()
    test_structural_redesign_passes_with_same_archetype()
    print("cross-run novelty: PASS")
