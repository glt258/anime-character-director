"""Small content contract for optional glove and legwear asymmetry guidance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
POSE = (ROOT / "references" / "pose-and-footwear-diversity.md").read_text(encoding="utf-8")
VARIANTS = (ROOT / "references" / "standee-variants.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")


def test_optional_asymmetric_costume_contract() -> None:
    checks = {
        "partial glove coverage": "Partial finger glove coverage" in POSE,
        "exposed finger is not missing anatomy": "exposed skin" in POSE and "missing finger" in POSE,
        "anatomy can pass": "Anatomy: PASS" in POSE,
        "costume detail label": "Costume Design" in POSE,
        "different gloves allowed": "different glove structures" in POSE,
        "one-leg hosiery allowed": "one-leg hosiery" in POSE,
        "symmetric hosiery remains valid": "symmetric" in POSE,
        "asymmetry is optional": "not a requirement for every character" in POSE,
        "Human can request symmetry": "fully symmetric legwear" in POSE,
        "Human can request asymmetry": "glove_coverage_variant" in VARIANTS,
        "Canon is protected": "Canon-frozen" in POSE and "Human-approved Canon" in WORKFLOW,
        "standee shows both sides": "both sides visible" in VARIANTS,
        "lore reason is optional": "Do not force a lore explanation" in POSE,
        "no new hard gate": "no new hard gate" in WORKFLOW and "not a hard gate" in SKILL,
        "no new validator": "do not create a new mode" in VARIANTS and "no new hard gate or validator" in WORKFLOW,
        "existing variants mode only": "existing `variants` mode" in VARIANTS,
    }
    failed = [name for name, passed in checks.items() if not passed]
    assert not failed, f"asymmetric costume guidance contract failed: {failed}"


if __name__ == "__main__":
    test_optional_asymmetric_costume_contract()
    print("asymmetric costume guidance contract: PASS")
