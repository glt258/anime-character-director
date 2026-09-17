from __future__ import annotations

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.interaction_candidates import (
    CandidateGenerator,
    background_specification_for_family,
    select_seeded_candidate,
)
from runtime.interaction_runtime import CreationMode, InteractionRuntime
from runtime.natural_language_interaction import ExplicitConstraintExtractor
from runtime.regional_style_runtime import (
    PromptCompiler,
    PromptConstraintConflict,
    build_visual_specification_contract,
)


def _pose(**overrides: str) -> dict[str, str]:
    value = {
        "lower_body_pose": "open parallel stance",
        "weight_distribution": "balanced",
        "torso_orientation": "upright front-facing",
        "shoulder_line": "level relaxed",
        "arm_configuration": "asymmetric open gesture",
        "left_arm_action": "relaxed low",
        "right_arm_action": "extended outward",
        "left_hand_gesture": "relaxed fingers",
        "right_hand_gesture": "open palm outward",
        "head_attitude": "level",
        "gaze_direction": "direct viewer gaze",
        "gesture_energy": "open confident",
    }
    value.update(overrides)
    return value


def _background(**overrides: str) -> dict[str, str]:
    value = {
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
    value.update(overrides)
    return value


def _bundle(pose: dict[str, str], background: dict[str, str], *, pose_family: str = "OPEN_PARALLEL_STANCE", positive: str | None = None):
    dna = {
        "pose_family": pose_family,
        "background_family": background.get("environment_type", "abstract"),
        "pose_specification": pose,
        "background_specification": background,
    }
    contract = build_visual_specification_contract(design_dna=dna)
    return PromptCompiler().compile(
        character_visual_style="clean-line contemporary commercial gacha anime",
        pose_description=f"{pose_family} frontal standee stance with both legs clearly separated",
        pose_family=pose_family,
        visual_specification_contract=contract,
        positive_prompt_fragment=positive,
    )


def test_hand_gesture_is_explicitly_compiled() -> None:
    bundle = _bundle(_pose(), _background())
    assert "Left Hand: relaxed fingers" in bundle.prompt
    assert "Right Hand: open palm outward" in bundle.prompt
    assert "Right Arm: extended outward" in bundle.prompt


def test_hands_away_from_face_protects_against_face_attractor() -> None:
    bundle = _bundle(
        _pose(
            arm_configuration="hands away from face",
            left_hand_gesture="away from face",
            right_hand_gesture="away from face",
        ),
        _background(),
    )
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert not any(term in positive for term in ("touching cheek", "finger near lips", "hand beside face"))
    assert "do not move either hand to the face" in bundle.prompt.lower()


def test_pose_structural_variants_change_compiled_structure() -> None:
    bundles = [
        _bundle(_pose(), _background()),
        _bundle(
            _pose(
                lower_body_pose="forward step",
                weight_distribution="forward-weighted",
                torso_orientation="slight forward lean",
                left_arm_action="held near waist",
                right_arm_action="reaching forward",
                head_attitude="slightly lowered",
                gaze_direction="forward focus",
            ),
            _background(),
            pose_family="FORWARD_STEP_NON_CROSSING",
        ),
        _bundle(
            _pose(
                lower_body_pose="narrow stable stance",
                torso_orientation="three-quarter turn",
                arm_configuration="both arms relaxed low",
                left_arm_action="relaxed low",
                right_arm_action="relaxed low",
                left_hand_gesture="neutral relaxed fingers",
                right_hand_gesture="neutral relaxed fingers",
                head_attitude="slight side turn",
                gaze_direction="off-camera",
            ),
            _background(),
            pose_family="NARROW_SEPARATED_STANCE",
        ),
    ]
    assert len({bundle.prompt for bundle in bundles}) == 3
    assert all("## POSE SPECIFICATION" in bundle.prompt for bundle in bundles)


def test_background_without_architecture_is_positive_and_literal_location_free() -> None:
    bundle = _bundle(_pose(), _background())
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "architecture presence: none" in positive
    assert "spatial structure: layered luminous planes" in positive
    assert not any(term in positive for term in ("castle", "cathedral", "palace", "tower", "throne room"))


def test_architecture_is_allowed_without_gothic_inference() -> None:
    bundle = _bundle(
        _pose(),
        _background(
            environment_type="open fantasy plaza",
            architecture_presence="dominant",
            architecture_language="modern geometric fantasy",
            spatial_structure="deep open plaza perspective",
            background_complexity="medium-high",
        ),
    )
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "architecture language: modern geometric fantasy" in positive
    assert "gothic cathedral" not in positive


def test_abstract_label_expands_to_structured_background_dna() -> None:
    spec = background_specification_for_family("layered pressure field")
    assert spec["environment_type"] == "abstract"
    assert spec["architecture_presence"] == "none"
    assert spec["spatial_structure"] == "layered directional planes"
    assert spec["background_complexity"] == "medium"
    bundle = _bundle(_pose(), spec)
    assert "Architecture Presence: none" in bundle.prompt
    assert "Spatial Structure: layered directional planes" in bundle.prompt


def test_background_conflict_is_rejected_before_generation_ready() -> None:
    with pytest.raises(PromptConstraintConflict, match="PROMPT_CONSTRAINT_CONFLICT"):
        _bundle(_pose(), _background(), positive="towering castle")


def test_quick_replay_keeps_pose_and_background_dna_stable() -> None:
    request = "画一个魅魔角色，要求有魅魔角，体现魅力，性感暴露但是不涉黄"
    with TemporaryDirectory() as first_dir, TemporaryDirectory() as replay_dir:
        first = InteractionRuntime(first_dir).create_session(request, CreationMode.QUICK, seed=101)
        replay = InteractionRuntime(replay_dir).create_session(request, CreationMode.QUICK, seed=101)
        first_design = InteractionRuntime(first_dir).load_session(first.session_id).final_design
        replay_design = InteractionRuntime(replay_dir).load_session(replay.session_id).final_design
    assert first_design["pose_specification"] == replay_design["pose_specification"]
    assert first_design["background_specification"] == replay_design["background_specification"]


def test_quick_seeded_sampling_varies_upper_gesture_and_background_structure() -> None:
    candidates = CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input="succubus")
    selected = [select_seeded_candidate(candidates, seed, salt="character-direction") for seed in range(8)]
    gestures = {item["design_dna"]["pose_specification"]["right_hand_gesture"] for item in selected}
    backgrounds = {item["design_dna"]["background_specification"]["spatial_structure"] for item in selected}
    assert len(gestures) >= 2
    assert len(backgrounds) >= 2
    assert all("gothic" not in json.dumps(item["design_dna"]).lower() for item in selected)


def test_ai_candidates_diverge_in_upper_gesture_and_background_structure() -> None:
    candidates = CandidateGenerator().generate(gate_id="CHARACTER_DIRECTION_GATE", original_input="succubus")
    assert len({item["design_dna"]["pose_specification"]["arm_configuration"] for item in candidates}) >= 2
    assert len({item["design_dna"]["pose_specification"]["right_hand_gesture"] for item in candidates}) >= 2
    assert len({item["design_dna"]["background_specification"]["spatial_structure"] for item in candidates}) >= 2


def test_explicit_user_hand_choice_beats_seductive_semantic_intent() -> None:
    contract = build_visual_specification_contract(
        design_dna={
            "pose_family": "OPEN_PARALLEL_STANCE",
            "pose_specification": _pose(right_hand_gesture="touching cheek", right_arm_action="bent near face"),
            "background_family": "abstract",
        },
        visual_preferences={"right_hand_gesture": "open palm outward", "right_arm_action": "extended outward"},
        explicit_user_fields=("right_hand_gesture", "right_arm_action"),
        soft_intent={"fanservice_level": "seductive"},
    )
    assert contract.pose_specification["right_hand_gesture"] == "open palm outward"
    assert contract.hard_constraints["right_hand_gesture"] == "open palm outward"
    bundle = _bundle(
        contract.pose_specification,
        contract.background_specification,
        positive="seductive adult character",
    )
    assert "Right Hand: open palm outward" in bundle.prompt


def test_explicit_hand_language_is_extracted_as_hard_fields() -> None:
    constraints = ExplicitConstraintExtractor().extract("右手向前伸出，张开手掌，左手放低")
    assert constraints["right_hand_gesture"] == "open palm outward"
    assert constraints["right_arm_action"] == "extended outward"
    assert constraints["left_arm_action"] == "relaxed at side"
    assert "right_hand_gesture" in constraints["explicit_user_fields"]


def test_pose_background_manifest_and_replay_serialization_are_stable() -> None:
    bundle = _bundle(_pose(), _background())
    payload = json.loads(json.dumps(bundle.prompt_adherence_manifest, ensure_ascii=False))
    assert payload["pose_specification"] == bundle.visual_specification_contract["pose_specification"]
    assert payload["background_specification"] == bundle.visual_specification_contract["background_specification"]
    assert payload["hard_constraints"]["right_hand_gesture"] == "open palm outward"


P1_P4 = {
    "P1": (_pose(), _background(), "OPEN_PARALLEL_STANCE"),
    "P2": (
        _pose(
            lower_body_pose="forward step",
            weight_distribution="forward-weighted",
            torso_orientation="slight forward lean",
            left_arm_action="held near waist",
            right_arm_action="reaching forward",
            arm_configuration="one arm extended, one lowered",
            left_hand_gesture="away from face",
            right_hand_gesture="away from face",
            head_attitude="slightly lowered",
            gaze_direction="forward focus",
        ),
        _background(
            environment_type="industrial fantasy exterior",
            architecture_presence="supporting",
            architecture_language="industrial geometric",
            spatial_structure="deep corridor structure",
            atmosphere="high contrast atmosphere",
        ),
        "FORWARD_STEP_NON_CROSSING",
    ),
    "P3": (
        _pose(
            lower_body_pose="narrow stable stance",
            torso_orientation="three-quarter turn",
            arm_configuration="both arms relaxed low",
            left_arm_action="relaxed low",
            right_arm_action="relaxed low",
            left_hand_gesture="neutral relaxed fingers",
            right_hand_gesture="neutral relaxed fingers",
            head_attitude="slight side turn",
            gaze_direction="off-camera",
        ),
        _background(
            environment_type="minimal stage-like environment",
            architecture_presence="minimal",
            architecture_language="minimal stage framing",
            spatial_structure="flat graphic planes",
            background_complexity="low",
        ),
        "NARROW_SEPARATED_STANCE",
    ),
    "P4": (
        _pose(
            lower_body_pose="wide grounded stance",
            weight_distribution="low-center balanced",
            torso_orientation="counter-rotated",
            left_arm_action="extended sideways",
            right_arm_action="resting at waist",
            left_hand_gesture="away from face",
            right_hand_gesture="away from face",
            head_attitude="chin slightly raised",
        ),
        _background(
            environment_type="open fantasy plaza",
            architecture_presence="dominant",
            architecture_language="modern geometric fantasy",
            spatial_structure="deep spatial structure",
            background_complexity="medium-high",
        ),
        "WIDE_ACTIVE_STANCE",
    ),
}


def test_prompt_level_acceptance_fixtures_p1_to_p4() -> None:
    bundles = {name: _bundle(pose, background, pose_family=family) for name, (pose, background, family) in P1_P4.items()}
    assert all("## POSE SPECIFICATION" in bundle.prompt for bundle in bundles.values())
    assert all("## BACKGROUND SPECIFICATION" in bundle.prompt for bundle in bundles.values())
    assert bundles["P1"].visual_specification_contract["background_specification"]["architecture_presence"] == "none"
    assert bundles["P2"].visual_specification_contract["pose_specification"]["right_arm_action"] == "reaching forward"
    assert bundles["P3"].visual_specification_contract["background_specification"]["spatial_structure"] == "flat graphic planes"
    assert bundles["P4"].visual_specification_contract["background_specification"]["architecture_language"] == "modern geometric fantasy"
    assert len({bundle.visual_specification_contract["pose_specification"]["right_hand_gesture"] for bundle in bundles.values()}) >= 2
    assert all("gothic" not in bundle.prompt.lower() for bundle in bundles.values())
