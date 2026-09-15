"""Focused regression tests for the Design Ownership gate."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.visual_preference_runtime import (  # noqa: E402
    IDENTITY_VARIABLES,
    GateError,
    VisualPreferenceSession,
)


def make_sheet() -> dict:
    variables = {}
    for name in IDENTITY_VARIABLES:
        variables[name] = {
            "variable": name,
            "recommended": "recommended-value",
            "recommendation_reason": "supports the selected concept",
            "options": [
                {"id": "A", "value": "recommended-value", "reason": "clear identity", "diversity_risk": "low"},
                {"id": "B", "value": "alternative-value", "reason": "useful contrast", "diversity_risk": "low"},
            ],
            "allow_custom": True,
            "allow_ai_delegate": True,
            "user_selection": None,
            "locked": False,
        }
        if name in {"major_accessories", "body_markings"}:
            variables[name]["options"].append(
                {"id": "NONE", "value": "none", "reason": "no core mark or accessory", "diversity_risk": "low"}
            )
    return {"schema_version": "1.0.0", "variables": variables, "optional_variables": {}}


def test_lock_requires_an_explicit_decision_for_every_identity_variable() -> None:
    session = VisualPreferenceSession()
    session.propose(make_sheet())
    session.open_selection_gate()
    session.select("hair_color", option_id="A")
    try:
        session.lock()
    except GateError as error:
        assert "hair_style_family" in str(error)
    else:
        raise AssertionError("implicit identity decisions must not pass the gate")


def test_user_can_mix_customise_and_delegate_then_lock() -> None:
    session = VisualPreferenceSession()
    session.propose(make_sheet())
    session.open_selection_gate()
    for name in IDENTITY_VARIABLES:
        if name == "hair_color":
            session.select(name, mix=["ashen celadon-silver", "muted gray-violet"])
        elif name == "outfit_direction":
            session.select(name, custom="coat-based silhouette")
        elif name == "dominant_palette":
            session.select(name, delegate_to_ai=True)
        else:
            session.select(name, option_id="A")
    audit = session.lock()
    assert session.state == "VISUAL_PREFERENCES_LOCKED"
    assert audit["all_identity_decisions_explicit"] is True
    session.advance_to_final_design()
    session.complete_design_review()
    session.advance_to_generation_ready()


def test_black_hair_is_not_an_implicit_ai_default() -> None:
    sheet = make_sheet()
    sheet["variables"]["hair_color"]["recommended"] = "black"
    try:
        session = VisualPreferenceSession()
        session.propose(sheet)
    except GateError as error:
        assert "black hair" in str(error)
    else:
        raise AssertionError("black hair must require an explicit user request")


def test_report_and_json_artifacts_are_written(tmp_path: Path) -> None:
    session = VisualPreferenceSession()
    session.propose(make_sheet())
    session.open_selection_gate()
    for name in IDENTITY_VARIABLES:
        session.select(name, option_id="A")
    session.lock()
    sheet_path, report_path = session.write_artifacts(tmp_path)
    payload = json.loads(sheet_path.read_text(encoding="utf-8"))
    assert payload["state"] == "VISUAL_PREFERENCES_LOCKED"
    report = report_path.read_text(encoding="utf-8")
    assert "Current AI Proposal" in report
    assert "Global Rendering Style" in report
    assert "CONTEMPORARY_COMMERCIAL_GACHA_ANIME" in report


if __name__ == "__main__":
    test_lock_requires_an_explicit_decision_for_every_identity_variable()
    test_user_can_mix_customise_and_delegate_then_lock()
    test_black_hair_is_not_an_implicit_ai_default()
    print("visual preference runtime: PASS")
