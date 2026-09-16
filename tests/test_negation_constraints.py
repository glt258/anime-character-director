from __future__ import annotations

from tempfile import TemporaryDirectory

from runtime.interaction_candidates import candidate_compatibility
from runtime.interaction_runtime import CreationMode, InteractionRuntime
from runtime.natural_language_interaction import ExplicitConstraintExtractor, IntentType, NaturalLanguageInteractionParser


def _visual_context() -> dict:
    return {
        "gate_type": "VISUAL_PREFERENCE_GATE",
        "mode": "USER_DECIDE",
        "visual_variables": {
            name: {}
            for name in ("hair_color", "outfit_direction", "footwear_family", "eye_color", "legwear_family", "fanservice_level")
        },
    }


def _texts(constraints: dict) -> list[str]:
    return [item["text"] for item in constraints["prohibited_constraints"]]


def test_neg_scope_01_compound_hair_is_one_same_entity_prohibition() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要粉色长发")
    assert _texts(constraints) == ["pink long hair"]
    assert constraints["prohibited_constraints"] == [
        {
            "kind": "combination",
            "scope": "same_entity",
            "text": "pink long hair",
            "attributes": {"hair_color": "pink", "hair_style_family": "long hair"},
        }
    ]
    assert "forbid_hair_color" not in constraints["negative_constraints"]
    assert "forbid_hair_style_family" not in constraints["negative_constraints"]


def test_neg_scope_02_separate_hair_negations_remain_independent() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要粉色，也不要长发")
    assert _texts(constraints) == ["pink hair", "long hair"]
    assert not any(item["kind"] == "combination" for item in constraints["prohibited_constraints"])


def test_neg_scope_03_phrase_list_keeps_units() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要粉色长发和白色连衣裙、蕾丝")
    assert _texts(constraints) == ["pink long hair", "white dress", "lace"]
    assert len(constraints["prohibited_constraints"]) == 3


def test_neg_scope_04_allows_pink_accents_but_prohibits_pink_long_hair() -> None:
    constraints = ExplicitConstraintExtractor().extract("可以用粉色点缀，但不要粉色长发")
    assert _texts(constraints) == ["pink long hair"]
    assert "hair_color" not in constraints


def test_neg_scope_05_long_hair_is_positive_but_pink_long_hair_is_not() -> None:
    constraints = ExplicitConstraintExtractor().extract("可以留长发，但不要粉色长发")
    assert constraints["hair_style_family"] == "long hair"
    assert "hair_color" not in constraints
    assert _texts(constraints) == ["pink long hair"]


def test_neg_scope_06_black_stockings_heels_and_crossed_legs_are_independent() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要默认黑丝高跟鞋，不要交叉腿")
    assert _texts(constraints) == ["black stockings", "high heels", "crossed legs"]
    assert not any(item["kind"] == "combination" for item in constraints["prohibited_constraints"])


def test_neg_scope_07_mature_vibe_is_not_cool_elegance() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要成熟御姐感，但可以保留冷酷优雅")
    assert _texts(constraints) == ["mature older-sister vibe"]
    assert all("cool elegance" not in text for text in _texts(constraints))


def test_neg_scope_08_archetype_boundary_is_not_four_atomic_bans() -> None:
    constraints = ExplicitConstraintExtractor().extract("她不能只是普通人类女性加动物耳朵")
    assert _texts(constraints) == ["human female with cosmetic animal ears only"]
    assert constraints["prohibited_constraints"][0]["kind"] == "archetype"
    assert "female" not in _texts(constraints)
    assert "animal ears" not in _texts(constraints)


def test_character_d_and_b_keep_high_level_units() -> None:
    extractor = ExplicitConstraintExtractor()
    d = extractor.extract("不要使用粉色长发、白色连衣裙、蕾丝、软妹系等常见模板。")
    assert _texts(d) == ["pink long hair", "white dress", "lace", "soft-girl styling"]

    b = extractor.extract("不要把她设计成拿着扳手、戴着护目镜的字面化机械师")
    assert _texts(b) == ["literal mechanic visualization"]
    assert all(term not in _texts(b) for term in ("wrench", "goggles", "mechanic uniform"))


def test_prompt_compiler_receives_compound_scope_without_atomizing_it() -> None:
    text = "不要粉色长发"
    with TemporaryDirectory() as directory:
        response = InteractionRuntime(directory).create_session(text, CreationMode.QUICK)
        prompt = InteractionRuntime(directory).load_session(response.session_id).compiled_prompt["prompt"]
    lowered = prompt.lower()
    assert "avoid pink long hair" in lowered
    assert "forbid_hair_color" not in lowered
    assert "forbid_hair_style_family" not in lowered
    assert "no pink" not in lowered
    assert "no long hair" not in lowered


def test_candidate_compatibility_rejects_only_the_compound_match() -> None:
    constraints = ExplicitConstraintExtractor().extract("不要粉色长发")
    candidates = [
        {"id": "pink-long", "attributes": {"hair_color": "pink", "hair_style_family": "long hair"}},
        {"id": "brown-long", "attributes": {"hair_color": "brown", "hair_style_family": "long hair"}},
        {"id": "pink-short", "attributes": {"hair_color": "pink", "hair_style_family": "short hair"}},
        {"id": "black-short", "attributes": {"hair_color": "black", "hair_style_family": "short hair"}},
    ]
    results = {item["id"]: candidate_compatibility(item, constraints) for item in candidates}
    assert results["pink-long"]["status"] == "incompatible"
    assert all(results[item]["status"] == "compatible" for item in ("brown-long", "pink-short", "black-short"))

    footwear = ExplicitConstraintExtractor().extract("不要高跟鞋")
    assert candidate_compatibility({"attributes": {"footwear_family": "high heels"}}, footwear)["status"] == "incompatible"
    assert candidate_compatibility({"attributes": {"footwear_family": "ankle boots"}}, footwear)["status"] == "compatible"


def test_rec_01_to_04_recommendation_aliases_apply_to_unresolved_fields() -> None:
    parser = NaturalLanguageInteractionParser()
    for text in ("其他按推荐", "剩下的按推荐", "其他都按推荐", "剩下都用推荐"):
        intent = parser.parse(text, _visual_context())
        assert intent.intent_type == IntentType.ACCEPT_ALL_RECOMMENDED.value
        assert intent.action == "USE_ALL_RECOMMENDED"
        assert not intent.field_updates


def test_rec_05_to_06_delegation_aliases_are_distinct_and_do_not_override_locked_fields() -> None:
    parser = NaturalLanguageInteractionParser()
    for text in ("其他你推荐就行", "剩下你决定", "其他交给你", "leave the rest to you", "you decide the rest"):
        intent = parser.parse(text, _visual_context())
        assert intent.intent_type in {IntentType.ACCEPT_ALL_RECOMMENDED.value, IntentType.PARTIAL_DELEGATION.value}

    with TemporaryDirectory() as directory:
        runtime = InteractionRuntime(directory)
        first = runtime.create_session("设计一个成年女性角色，我自己选", CreationMode.USER_DECIDE)
        runtime.resume_session(first.session_id, "A")
        runtime.resume_session(first.session_id, "A")
        partial = runtime.resume_session(first.session_id, "发色银白")
        assert partial.status != "ERROR"
        ready = runtime.resume_session(first.session_id, "剩下的按推荐")
        assert ready.status == "GENERATION_READY"
        sheet = runtime.load_session(first.session_id).visual_preference_sheet
        assert sheet["variables"]["hair_color"]["user_selection"] == "silver-white"
        assert sheet["variables"]["hair_color"]["selection_source"] == "human_custom"
        assert sheet["variables"]["hair_color"]["locked"] is True
