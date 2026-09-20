"""Targeted tests for the optional local style-reference interface."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from runtime.image_request import build_image_request
from runtime.interaction_runtime import InteractionRuntime
from runtime.regional_style_runtime import PromptCompiler
from runtime.style_references import (
    DEFAULT_MAX_IMAGES,
    MAX_REFERENCE_IMAGES,
    ReferenceConditioningConfig,
    ReferenceLibrary,
    apply_reference_preferences,
    build_style_conditioning_context,
    resolve_asset_root,
    resolve_style_references,
)


PNG_1X1 = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
GAME_IDS = ("genshin_impact", "zenless_zone_zero", "wuthering_waves", "neverness_to_everness")


def _fixture_library(tmp_path: Path) -> Path:
    root = tmp_path / "assets"
    games: dict[str, dict[str, list[dict[str, object]]]] = {}
    for game_id in GAME_IDS:
        references = []
        for index in range(1, 7):
            relative = f"{game_id}/{game_id}_ref_{index:03d}.png"
            path = root / "game_style_references" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(PNG_1X1)
            references.append(
                {
                    "id": f"{game_id}_ref_{index:03d}",
                    "game_style_id": game_id,
                    "canonical_character_id": f"{game_id}:character_{index:03d}",
                    "character_name": f"Character {index}",
                    "gender_presentation": "female",
                    "nonhuman_level": "human",
                    "relative_path": relative,
                    "sha256": hashlib.sha256(PNG_1X1).hexdigest(),
                    "width": 1,
                    "height": 1,
                    "source_type": "official",
                    "source_site": "fixture",
                    "source_page": "https://example.invalid/character",
                    "source_file_url": "https://example.invalid/image.png",
                    "official_verified": False,
                    "roles": ["overall_character_art", "face_eye_skin"] if index % 2 else ["costume_structure", "material_rendering"],
                    "quality_rank": 5 if index <= 3 else 4,
                    "selection_reason": ["fixture"],
                }
            )
        games[game_id] = {"references": references}
    manifest = {"schema_version": "local_style_reference_manifest_v1", "library_version": "v1", "games": games}
    manifest_path = root / "game_style_references" / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return root


def test_local_asset_root_resolution(tmp_path: Path) -> None:
    config = tmp_path / "local.yaml"
    config.write_text("local_assets:\n  root: D:\\configured-assets\n", encoding="utf-8")
    assert resolve_asset_root("D:/explicit", env={"ANIME_CHARACTER_DIRECTOR_ASSET_ROOT": "D:/env"}, config_path=config) == Path("D:/explicit")
    assert resolve_asset_root(env={"ANIME_CHARACTER_DIRECTOR_ASSET_ROOT": "D:/env"}, config_path=config) == Path("D:/env")
    assert resolve_asset_root(env={}, config_path=config) == Path("D:/configured-assets")


def test_reference_manifest_schema() -> None:
    schema = json.loads((Path(__file__).parents[1] / "references/local_style_references/manifest.schema.json").read_text(encoding="utf-8"))
    assert schema["$defs"]["game"]["additionalProperties"] is False
    assert schema["properties"]["games"]["additionalProperties"]["$ref"] == "#/$defs/game"


def test_reference_library_loads(tmp_path: Path) -> None:
    assert ReferenceLibrary(_fixture_library(tmp_path)).library_available


def test_reference_file_exists(tmp_path: Path) -> None:
    refs = resolve_style_references("genshin_impact", asset_root=_fixture_library(tmp_path))
    assert refs and all(Path(item.absolute_path).is_file() for item in refs)


def test_reference_sha256_integrity(tmp_path: Path) -> None:
    refs = resolve_style_references("genshin_impact", asset_root=_fixture_library(tmp_path))
    assert all(item.sha256 == hashlib.sha256(Path(item.absolute_path).read_bytes()).hexdigest() for item in refs)


def _assert_game_resolution(game_id: str, tmp_path: Path) -> None:
    refs = resolve_style_references(game_id, asset_root=_fixture_library(tmp_path))
    assert len(refs) == DEFAULT_MAX_IMAGES
    assert all(item.game_style_id == game_id for item in refs)


def test_resolve_genshin_references(tmp_path: Path) -> None:
    _assert_game_resolution("genshin_impact", tmp_path)


def test_resolve_zzz_references(tmp_path: Path) -> None:
    _assert_game_resolution("zenless_zone_zero", tmp_path)


def test_resolve_wuwa_references(tmp_path: Path) -> None:
    _assert_game_resolution("wuthering_waves", tmp_path)


def test_resolve_nte_references(tmp_path: Path) -> None:
    _assert_game_resolution("neverness_to_everness", tmp_path)


def test_reference_max_images(tmp_path: Path) -> None:
    refs = resolve_style_references("genshin_impact", max_images=99, asset_root=_fixture_library(tmp_path))
    assert len(refs) == MAX_REFERENCE_IMAGES


def test_reference_selection_deterministic(tmp_path: Path) -> None:
    root = _fixture_library(tmp_path)
    first = [item.reference_id for item in resolve_style_references("genshin_impact", context={"request": "pink adult woman"}, asset_root=root)]
    second = [item.reference_id for item in resolve_style_references("genshin_impact", context={"request": "pink adult woman"}, asset_root=root)]
    assert first == second


def test_reference_selection_cross_character(tmp_path: Path) -> None:
    refs = resolve_style_references("genshin_impact", max_images=MAX_REFERENCE_IMAGES, asset_root=_fixture_library(tmp_path))
    assert len({item.canonical_character_id for item in refs}) == len(refs)


def test_missing_library_fallback(tmp_path: Path) -> None:
    bundle = ReferenceLibrary(tmp_path / "missing").resolve("genshin_impact")
    assert bundle.available is False
    assert bundle.fallback_reason == "LOCAL_REFERENCE_LIBRARY_UNAVAILABLE"


def test_missing_image_skipped(tmp_path: Path) -> None:
    root = _fixture_library(tmp_path)
    (root / "game_style_references/genshin_impact/genshin_impact_ref_001.png").unlink()
    bundle = ReferenceLibrary(root).resolve("genshin_impact", max_images=MAX_REFERENCE_IMAGES)
    assert bundle.available and len(bundle.references) == MAX_REFERENCE_IMAGES
    assert bundle.warnings


def test_bad_manifest_yaml_only(tmp_path: Path) -> None:
    root = tmp_path / "assets/game_style_references"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text("{not-json", encoding="utf-8")
    bundle = ReferenceLibrary(tmp_path / "assets").resolve("genshin_impact")
    assert bundle.available is False
    assert bundle.fallback_reason == "LOCAL_REFERENCE_MANIFEST_INVALID"


def test_reference_bundle_schema(tmp_path: Path) -> None:
    payload = ReferenceLibrary(_fixture_library(tmp_path)).resolve("genshin_impact").to_dict()
    assert {"game_style_id", "library_version", "references", "selection_reason", "available", "fallback_reason", "warnings"}.issubset(payload)


def test_user_constraints_higher_priority_contract() -> None:
    assert apply_reference_preferences({"hair": "long", "rendering": "soft"}, {"hair": "short"}) == {"rendering": "soft"}


def test_no_reference_images_tracked_by_git() -> None:
    root = Path(__file__).parents[1]
    tracked = subprocess.check_output(["git", "ls-files"], cwd=root, text=True).splitlines()
    tracked = [
        path for path in tracked
        if path.startswith("references/local_style_references/")
        and Path(path).suffix.casefold() in {".png", ".jpg", ".jpeg", ".webp"}
    ]
    assert tracked == []


def test_repository_operates_without_local_assets(tmp_path: Path) -> None:
    assert resolve_style_references("future_game", asset_root=tmp_path / "does-not-exist") == []


def test_reference_conditioning_quick_enabled(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "genshin_impact",
        mode="QUICK",
        asset_root=_fixture_library(tmp_path),
    )
    assert context.reference_mode == "yaml_plus_local_references"
    assert context.drift_tolerance == "style_forward"
    assert context.reference_bundle.available
    assert context.reference_bundle.max_images_used == 3


def test_reference_conditioning_ai_decide_enabled(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "zenless_zone_zero",
        mode="AI_DECIDE",
        asset_root=_fixture_library(tmp_path),
    )
    assert context.reference_mode == "yaml_plus_local_references"
    assert context.drift_tolerance == "balanced"
    assert context.reference_bundle.available


def test_runtime_quick_reference_conditioning_enabled(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("ANIME_CHARACTER_DIRECTOR_ASSET_ROOT", str(_fixture_library(tmp_path)))
    response = InteractionRuntime(tmp_path / "sessions").create_session("快速设计成年女性，按原神画风")
    prompt_bundle = InteractionRuntime(tmp_path / "sessions").load_session(response.session_id).compiled_prompt
    assert prompt_bundle["reference_conditioning"]["reference_bundle"]["reference_conditioning_mode"] == "yaml_plus_local_references"
    assert prompt_bundle["image_request"]["used_local_references"] is True


def test_runtime_ai_decide_reference_conditioning_enabled(tmp_path: Path, monkeypatch: Any) -> None:
    monkeypatch.setenv("ANIME_CHARACTER_DIRECTOR_ASSET_ROOT", str(_fixture_library(tmp_path)))
    response = InteractionRuntime(tmp_path / "sessions").create_session("设计成年男性，Genshin rendering")
    prompt_bundle = InteractionRuntime(tmp_path / "sessions").load_session(response.session_id).compiled_prompt
    assert prompt_bundle["reference_conditioning"]["drift_tolerance"] == "balanced"
    assert prompt_bundle["image_request"]["reference_image_paths"]


def test_reference_conditioning_disabled_fallback(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "genshin_impact",
        mode="QUICK",
        asset_root=_fixture_library(tmp_path),
        config=ReferenceConditioningConfig(enabled=False),
    )
    assert context.reference_mode == "disabled"
    assert context.reference_bundle.fallback_reason == "LOCAL_REFERENCE_CONDITIONING_DISABLED"


def test_yaml_plus_local_references_request_build(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "wuthering_waves",
        mode="QUICK",
        asset_root=_fixture_library(tmp_path),
    )
    bundle = PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        character_identity="adult woman with short pink hair and sneakers",
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
        creation_mode="QUICK",
    ).to_dict()
    request = build_image_request(bundle, mode="QUICK")
    assert request.used_local_references
    assert request.reference_image_paths == tuple(item.absolute_path for item in context.reference_bundle.references)
    assert request.mode == "QUICK"


def test_reference_paths_attached(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=_fixture_library(tmp_path))
    compiled = PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
    ).to_dict()
    assert build_image_request(compiled).reference_image_paths


def test_reference_max_images_respected(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "genshin_impact",
        asset_root=_fixture_library(tmp_path),
        config={"max_local_style_references": 99},
    )
    assert context.reference_bundle.max_images_used == MAX_REFERENCE_IMAGES


def test_reference_bundle_empty_fallback(tmp_path: Path) -> None:
    root = _fixture_library(tmp_path)
    for path in (root / "game_style_references/genshin_impact").glob("*.png"):
        path.unlink()
    context = build_style_conditioning_context("genshin_impact", asset_root=root)
    assert context.reference_mode == "yaml_only"
    assert context.reference_bundle.fallback_reason == "LOCAL_REFERENCE_LIBRARY_ALL_REFERENCES_INVALID"


def test_missing_library_yaml_only(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=tmp_path / "missing")
    assert context.reference_mode == "yaml_only"
    assert context.reference_bundle.fallback_reason == "LOCAL_REFERENCE_LIBRARY_UNAVAILABLE"


def test_missing_image_yaml_only(tmp_path: Path) -> None:
    root = _fixture_library(tmp_path)
    for path in (root / "game_style_references/genshin_impact").glob("*.png"):
        path.unlink()
    context = build_style_conditioning_context("genshin_impact", asset_root=root)
    assert context.reference_mode == "yaml_only"
    assert not context.reference_bundle.available


def test_explicit_user_constraints_override_reference_style(tmp_path: Path) -> None:
    context = build_style_conditioning_context(
        "genshin_impact",
        asset_root=_fixture_library(tmp_path),
        explicit_constraints={"hair_color": {"value": "white", "priority": "HARD"}},
    )
    assert apply_reference_preferences({"hair_color": "long pink", "material": "soft"}, {"hair_color": "white"}) == {"material": "soft"}
    assert "Explicit user constraints have higher priority" in PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        explicit_constraints={"hair_color": {"value": "white", "priority": "HARD"}},
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
    ).prompt


def test_no_reference_character_copy_contract_present(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=_fixture_library(tmp_path))
    prompt = PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
    ).prompt
    assert "Do not copy a reference character identity" in prompt


def test_reference_conditioning_mode_auto(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=_fixture_library(tmp_path))
    assert context.reference_bundle.reference_conditioning_mode == "yaml_plus_local_references"


def test_quick_style_drift_policy_style_forward(tmp_path: Path) -> None:
    assert build_style_conditioning_context("genshin_impact", mode="QUICK", asset_root=_fixture_library(tmp_path)).drift_tolerance == "style_forward"


def test_ai_decide_style_drift_policy_balanced(tmp_path: Path) -> None:
    assert build_style_conditioning_context("genshin_impact", mode="AI_DECIDE", asset_root=_fixture_library(tmp_path)).drift_tolerance == "balanced"


def test_prompt_compiler_mentions_reference_usage_policy(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=_fixture_library(tmp_path))
    prompt = PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
    ).prompt
    assert "style references" in prompt
    assert "unlocked design space" in prompt


def test_debug_trace_contains_reference_selection(tmp_path: Path) -> None:
    context = build_style_conditioning_context("genshin_impact", asset_root=_fixture_library(tmp_path))
    bundle = PromptCompiler().compile(
        character_visual_style="clean contemporary gacha anime",
        visual_context_firewall={"visual_context_firewall_applied": True},
        reference_conditioning=context,
    ).to_dict()
    trace = bundle["game_style_debug_trace"]["reference_conditioning"]
    assert trace["reference_bundle"]["max_images_used"] == DEFAULT_MAX_IMAGES
    assert trace["reference_bundle"]["references"][0]["absolute_path"]


def test_c_runtime_untouched() -> None:
    """The release repository is the only implementation boundary for this task."""
    assert Path(__file__).parents[1].resolve() == Path("D:/anime-character-director-release").resolve()
