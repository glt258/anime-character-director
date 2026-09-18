from __future__ import annotations

from scripts.run_three_mode_ux_acceptance_v1 import (
    CaseContext,
    ProvenanceSemanticClass,
    normalize_provenance,
    run_u6,
)


def test_explicit_user_and_human_explicit_are_human_explicit() -> None:
    assert normalize_provenance("explicit_user") is ProvenanceSemanticClass.HUMAN_EXPLICIT
    assert normalize_provenance("human_explicit") is ProvenanceSemanticClass.HUMAN_EXPLICIT


def test_recommendation_acceptance_is_human_selection_not_explicit_text() -> None:
    assert normalize_provenance("human_accept_recommended") is ProvenanceSemanticClass.HUMAN_SELECTION
    assert normalize_provenance("human_accept_recommended") is not ProvenanceSemanticClass.HUMAN_EXPLICIT


def test_human_selection_remains_distinct_from_explicit_text() -> None:
    assert normalize_provenance("human_select") is ProvenanceSemanticClass.HUMAN_SELECTION
    assert normalize_provenance("human_select") is not ProvenanceSemanticClass.HUMAN_EXPLICIT


def test_ai_and_system_sources_keep_their_own_semantics() -> None:
    assert normalize_provenance("delegated_ai") is ProvenanceSemanticClass.AI_RESOLVED
    assert normalize_provenance("quick_ai_fill") is ProvenanceSemanticClass.AI_RESOLVED
    assert normalize_provenance("policy_default") is ProvenanceSemanticClass.SYSTEM_DEFAULT


def test_unknown_provenance_fails_closed() -> None:
    assert normalize_provenance("totally_invalid_source") is ProvenanceSemanticClass.UNKNOWN


def test_u6_accept_all_recommended_preserves_explicit_and_selection_ownership() -> None:
    context = CaseContext()
    try:
        review = run_u6(context)
        session = context.runtime.load_session(context.primary_session_id or "")
        sources = {
            name: item.get("selection_source")
            for name, item in (session.visual_preference_sheet or {}).get("variables", {}).items()
        }
        events = [item.get("event", {}) for item in session.interaction_history]

        assert review.correctness == "PASS"
        assert session.status == "GENERATION_READY"
        assert any(event.get("action") == "USE_ALL_RECOMMENDED" for event in events)
        assert normalize_provenance(sources["gender_presentation"]) is ProvenanceSemanticClass.HUMAN_EXPLICIT
        assert all(
            source == "human_accept_recommended"
            and normalize_provenance(source) is ProvenanceSemanticClass.HUMAN_SELECTION
            for field, source in sources.items()
            if field != "gender_presentation"
        )
    finally:
        context.close()
