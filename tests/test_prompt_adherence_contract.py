from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.regional_style_runtime import (  # noqa: E402
    PromptCompiler,
    PromptConstraintConflict,
    build_visual_specification_contract,
)


FIXTURES = {
    "A": {
        "silhouette_family": "lean open silhouette",
        "hair_structure": "short wavy hair",
        "horn_topology": "swept-back blade horns",
        "upper_body_structure": "fitted sleeveless upper body",
        "lower_body_structure": "high-waist lower body",
        "costume_topology": "bodysuit + cropped outer layer",
        "exposure_strategy": "waist/back exposure",
        "legwear_strategy": "bare legs",
        "footwear_category": "tall flat boots",
        "pose_family": "OPEN_PARALLEL_STANCE",
        "wing_strategy": "minimal membrane wings",
        "tail_design": "slender pointed tail",
        "palette_family": "black and warm crimson",
        "material_language": "matte technical fabric",
        "accessory_density": "minimal",
        "body_line_emphasis": "clean waist line",
        "background_family": "soft abstract gradient",
    },
    "B": {
        "silhouette_family": "upright narrow silhouette",
        "hair_structure": "high ponytail",
        "horn_topology": "crown-like horns",
        "upper_body_structure": "structured open shoulder bodice",
        "lower_body_structure": "asymmetric ritual skirt structure",
        "costume_topology": "asymmetric ritual dress",
        "exposure_strategy": "shoulder/back exposure",
        "legwear_strategy": "none",
        "footwear_category": "barefoot ankle jewelry",
        "pose_family": "NARROW_SEPARATED_STANCE",
        "wing_strategy": "translucent motif wings",
        "tail_design": "ribbon-like tail",
        "palette_family": "ivory and violet",
        "material_language": "translucent layered textile",
        "accessory_density": "moderate",
        "body_line_emphasis": "long vertical line",
        "background_family": "abstract ritual haze",
    },
    "C": {
        "silhouette_family": "forward-moving compact silhouette",
        "hair_structure": "braided medium hair",
        "horn_topology": "branching compact horns",
        "upper_body_structure": "open fitted harness top",
        "lower_body_structure": "shorts + split overskirt",
        "costume_topology": "shorts + split overskirt",
        "exposure_strategy": "thigh/side exposure",
        "legwear_strategy": "short socks",
        "footwear_category": "combat boots",
        "pose_family": "FORWARD_STEP_NON_CROSSING",
        "wing_strategy": "visible demon wings",
        "tail_design": "segmented arrow tail",
        "palette_family": "cobalt and copper",
        "material_language": "leather and brushed metal",
        "accessory_density": "focused structural accents",
        "body_line_emphasis": "active diagonal line",
        "background_family": "layered motion arcs",
    },
    "D": {
        "silhouette_family": "balanced tailored silhouette",
        "hair_structure": "layered bob",
        "horn_topology": "narrow rear horns",
        "upper_body_structure": "open structured top",
        "lower_body_structure": "tailored trousers",
        "costume_topology": "tailored trousers + open structured top",
        "exposure_strategy": "cleavage/waist framing",
        "legwear_strategy": "none",
        "footwear_category": "platform shoes",
        "pose_family": "LOW_ENERGY_SEPARATED_STANCE",
        "wing_strategy": "symbolic graphic wing motif",
        "tail_design": "small heart tail",
        "palette_family": "deep teal and muted red",
        "material_language": "soft tailored suiting",
        "accessory_density": "single ornament",
        "body_line_emphasis": "controlled waist framing",
        "background_family": "abstract temporal haze",
    },
}


def _bundle(dna: dict[str, str], *, identity: str = "adult succubus character", **kwargs: object):
    contract = build_visual_specification_contract(
        design_dna=dna,
        visual_preferences=kwargs.pop("visual_preferences", None),
        explicit_user_fields=kwargs.pop("explicit_user_fields", ()),
        character_visual_style="clean-line contemporary commercial gacha anime",
    )
    return PromptCompiler().compile(
        character_visual_style="clean-line contemporary commercial gacha anime",
        character_identity=identity,
        pose_description=f"{dna['pose_family']} frontal standee stance with both legs clearly separated",
        pose_family=dna["pose_family"],
        visual_specification_contract=contract,
        **kwargs,
    )


def test_design_dna_hard_fields_are_emitted_in_final_prompt() -> None:
    bundle = _bundle(FIXTURES["D"])
    for field in (
        "layered bob",
        "narrow rear horns",
        "tailored trousers + open structured top",
        "platform shoes",
        "symbolic graphic wing motif",
        "LOW_ENERGY_SEPARATED_STANCE",
    ):
        assert field in bundle.prompt
    assert "## HARD DESIGN SPECIFICATION" in bundle.prompt
    assert bundle.prompt_adherence_manifest["hard_constraints"]["hair_structure"] == "layered bob"


def test_barefoot_positive_section_has_no_footwear_substitution_terms() -> None:
    bundle = _bundle(FIXTURES["B"])
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "barefoot ankle jewelry" in positive
    assert not any(term in positive for term in ("heels", "boots", "pumps", "stilettos"))
    assert any(term in bundle.prompt.lower() for term in ("no shoes", "no boots", "no heels"))


def test_symbolic_wings_are_not_rewritten_as_physical_wings() -> None:
    bundle = _bundle(FIXTURES["D"])
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "symbolic graphic wing motif" in positive
    assert "physical demon wings" not in positive


def test_layered_bob_has_no_long_hair_substitution() -> None:
    bundle = _bundle(FIXTURES["D"])
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "layered bob" in positive
    assert "long flowing" not in positive
    assert "waist-length" not in positive


def test_tailored_trousers_and_open_top_have_no_dress_substitution() -> None:
    bundle = _bundle(FIXTURES["D"])
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "tailored trousers + open structured top" in positive
    assert not any(term in positive for term in ("gown", "high-slit", "lingerie dress", "evening dress"))


def test_abstract_temporal_background_has_no_literal_location_substitution() -> None:
    bundle = _bundle(FIXTURES["D"])
    positive = bundle.prompt.split("## NEGATIVE / DO-NOT-SUBSTITUTE", 1)[0].lower()
    assert "abstract temporal haze" in positive
    assert not any(term in positive for term in ("castle", "cathedral", "throne room", "palace"))


def test_prompt_conflict_is_rejected_before_generation_ready() -> None:
    with pytest.raises(PromptConstraintConflict, match="PROMPT_CONSTRAINT_CONFLICT"):
        _bundle(FIXTURES["C"], positive_prompt_fragment="stiletto heels")


def test_user_decide_explicit_footwear_beats_lower_priority_dna() -> None:
    bundle = _bundle(
        {**FIXTURES["C"], "footwear_category": "combat boots"},
        visual_preferences={"footwear_family": "barefoot"},
        explicit_user_fields=("footwear_family",),
    )
    assert bundle.visual_specification_contract["hard_constraints"]["footwear_category"] == "barefoot"


def test_user_decide_explicit_palette_and_background_are_hard_fields() -> None:
    contract = build_visual_specification_contract(
        design_dna=FIXTURES["D"],
        visual_preferences={"dominant_palette": "acid green and white", "background_direction": "plain studio void"},
        explicit_user_fields=("dominant_palette", "background_direction"),
    )
    assert contract.hard_constraints["palette_family"] == "acid green and white"
    assert contract.hard_constraints["background_family"] == "plain studio void"


def test_same_archetype_fixture_keeps_a_to_d_structural_contracts_independent() -> None:
    contracts = [
        build_visual_specification_contract(
            design_dna=dna,
            character_visual_style="clean-line contemporary commercial gacha anime",
        ).to_dict()
        for dna in FIXTURES.values()
    ]
    assert len({item["hard_constraints"]["costume_topology"] for item in contracts}) == 4
    assert len({item["hard_constraints"]["footwear_category"] for item in contracts}) == 4
    assert len({item["hard_constraints"]["pose_family"] for item in contracts}) == 4
    assert all("gothic" not in json.dumps(item).lower() for item in contracts)


def test_semantic_intent_does_not_mutate_hard_visual_fields() -> None:
    base = FIXTURES["D"]
    hard_sections = []
    for intent in ("elegant", "dangerous", "playful", "seductive"):
        bundle = _bundle(base, identity=f"adult succubus character, {intent}")
        hard_sections.append(bundle.prompt.split("## HARD DESIGN SPECIFICATION", 1)[1].split("## POSE", 1)[0])
    assert len(set(hard_sections)) == 1


def test_visual_contract_and_manifest_are_replay_stable() -> None:
    bundle = _bundle(FIXTURES["D"])
    replay_contract = json.loads(json.dumps(bundle.visual_specification_contract, ensure_ascii=False))
    replay_manifest = json.loads(json.dumps(bundle.prompt_adherence_manifest, ensure_ascii=False))
    assert replay_contract == replay_manifest
    assert replay_contract["schema_version"] == "1.0.0"


def test_runtime_final_design_carries_contract_and_keeps_identity_separate() -> None:
    from tempfile import TemporaryDirectory

    from runtime.interaction_runtime import CreationMode, InteractionRuntime

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        response = runtime.create_session("succubus character", CreationMode.QUICK, seed=101)
        session = runtime.load_session(response.session_id)
    assert response.status == "GENERATION_READY"
    final_design = session.final_design
    assert final_design is not None
    assert "Design DNA:" not in final_design["character_identity"]
    assert final_design["generation_context"]["visual_specification_contract"] == final_design["visual_specification_contract"]
    assert session.compiled_prompt["prompt_adherence_manifest"] == final_design["prompt_adherence_manifest"]
