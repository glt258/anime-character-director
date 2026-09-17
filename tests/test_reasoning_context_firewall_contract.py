"""Acceptance checks for the Skill-level reasoning context firewall."""

from __future__ import annotations

import json
from pathlib import Path

from runtime.visual_context_firewall import VisualContextFirewall


ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")
WORKFLOW = (ROOT / "references" / "workflow.md").read_text(encoding="utf-8")


OLD_VISUALS = {
    "visual_preferences": {
        "hair_color": "crimson long hair",
        "hair_style_family": "long hair",
        "legwear_family": "black sheer stockings",
        "footwear_family": "high heels",
        "outfit_direction": "burgundy gothic dress",
        "background_direction": "gothic cathedral",
        "pose": "hand near face",
    },
    "image_prompt": "old prompt with ram horns",
    "critic_summary": "approved safe template",
}


def _serialized(value: object) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def test_fresh_run_context_excludes_complete_previous_design() -> None:
    context = VisualContextFirewall().generation_context(
        current_user_request="使用 AI_DECIDE 模式画一个魅魔角色，要求有魅魔角，体现魅力，性感暴露但是不涉黄。",
        historical_visual_context=OLD_VISUALS,
    )
    serialized = _serialized(context)

    assert context["scope"] == "current_run_only"
    assert "history" not in context
    for marker in ("crimson long hair", "ram horns", "gothic dress", "high heels", "gothic cathedral", "hand near face"):
        assert marker not in serialized


def test_previous_preference_choices_cannot_fill_unselected_fields() -> None:
    context = VisualContextFirewall().generation_context(
        current_user_request="设计一个新的成年魅魔角色，有角，体现魅力。",
        current_run_choices=({"id": "current_run_choice"},),
        historical_visual_context=OLD_VISUALS,
    )
    serialized = _serialized(context)

    assert context["current_run_choices"] == [{"id": "current_run_choice"}]
    for marker in ("black sheer stockings", "high heels", "long hair", "crimson", "burgundy"):
        assert marker not in serialized


def test_explicit_inheritance_authorizes_only_the_named_field() -> None:
    request = "沿用上一版的红发，其他重新设计。"
    history = {**OLD_VISUALS, "visual_preferences": {**OLD_VISUALS["visual_preferences"], "hair_color": "红发"}}
    firewall = VisualContextFirewall.from_request(
        request,
        {"explicit_user_fields": ["hair_color"], "hair_color": "红发"},
    )
    context = firewall.generation_context(
        current_user_request=request,
        historical_visual_context=history,
    )

    assert firewall.inherit_previous_visuals is True
    assert context["explicitly_inherited_visuals"] == {"hair_color": "红发"}
    assert "hair_style_family" not in context["explicitly_inherited_visuals"]
    assert "footwear_family" not in context["explicitly_inherited_visuals"]
    assert "gothic cathedral" not in _serialized(context)


def test_explicit_overall_variation_may_authorize_inheritance() -> None:
    request = "参考上一版整体设计做一个变体。"
    firewall = VisualContextFirewall.from_request(request)
    context = firewall.generation_context(
        current_user_request=request,
        historical_visual_context=OLD_VISUALS,
    )

    assert firewall.inherit_previous_visuals is True
    assert "previous_run_visual_design" in firewall.allowed_visual_inheritance
    assert context["explicitly_inherited_visuals"] == OLD_VISUALS


def test_skill_and_workflow_publish_the_reasoning_firewall_contract() -> None:
    checks = {
        "fresh visual run": "fresh visual run" in SKILL and "fresh visual run" in WORKFLOW,
        "build current run context": "BUILD_CURRENT_RUN_CONTEXT" in SKILL and "CurrentRunContext" in WORKFLOW,
        "no preference inference": "Do not infer current visual preferences from previous runs." in SKILL,
        "history is not positive evidence": "not positive design evidence" in SKILL,
        "history direction is forbidden": "history → Codex reasoning → new visual choice" in SKILL and "history → Codex reasoning → new visual choice" in WORKFLOW,
        "fresh-run example": "上一版效果不错，因此继续使用红色长发" in SKILL,
        "field-only inheritance": "authorizes only the named hair-color field" in WORKFLOW,
        "overall variation exception": "整体设计做一个变体" in WORKFLOW,
    }
    failed = [name for name, passed in checks.items() if not passed]
    assert not failed, f"reasoning context firewall contract failed: {failed}"


if __name__ == "__main__":
    test_fresh_run_context_excludes_complete_previous_design()
    test_previous_preference_choices_cannot_fill_unselected_fields()
    test_explicit_inheritance_authorizes_only_the_named_field()
    test_explicit_overall_variation_may_authorize_inheritance()
    test_skill_and_workflow_publish_the_reasoning_firewall_contract()
    print("reasoning context firewall: PASS")
