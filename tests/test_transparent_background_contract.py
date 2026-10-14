"""Regression contract for default transparent character generation and PNG checks."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")


def test_transparent_background_generation_and_png_validation_contract() -> None:
    checks = {
        "all standard modes use the default rule": (
            "For every normal new-character generation in `QUICK`, `AI_DECIDE`, or `USER_DECIDE`" in SKILL
        ),
        "default requests transparent ImageGen output": "transparent_background: true" in SKILL,
        "an explicit rendered scene remains supported": "transparent_background: false" in SKILL,
        "AI-only background choices do not override the default": (
            "AI-resolved `BackgroundDNA` alone is not an explicit scene request." in SKILL
        ),
        "non-background prompt clauses remain unchanged": (
            "Leave every non-background prompt clause unchanged." in SKILL
        ),
        "PNG format and alpha data are inspected": (
            'assert image.format == "PNG"' in SKILL
            and '"A" in image.getbands() or "transparency" in image.info' in SKILL
        ),
        "decoded alpha contains transparent and opaque pixels": (
            "assert alpha_minimum == 0" in SKILL and "assert alpha_maximum > 0" in SKILL
        ),
        "empty outside samples must be fully transparent": (
            "outside_samples" in SKILL and "alpha.getpixel(point) == 0" in SKILL
        ),
        "file validation stays separate from character-design gates": (
            "Keep this technical file check separate from character-design gates." in SKILL
        ),
    }
    failed = [name for name, passed in checks.items() if not passed]
    assert not failed, f"transparent-background contract failed: {failed}"
