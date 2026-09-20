"""Resolve optional local character-art references without coupling ImageGen.

The library is deliberately a side channel: the normal text/YAML workflow
continues to work when the local asset root is absent.  Callers receive
validated ``StyleReference`` values and never need to read the manifest or
construct asset paths themselves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
import struct
from typing import Any, Mapping, Sequence


ASSET_ROOT_ENV = "ANIME_CHARACTER_DIRECTOR_ASSET_ROOT"
DEFAULT_MAX_IMAGES = 3
MAX_REFERENCE_IMAGES = 4
MANIFEST_FILENAME = "manifest.json"
LIBRARY_DIRECTORY = "game_style_references"
DEFAULT_CONFIG_PATH = Path.home() / ".codex" / "anime-character-director.local.yaml"
DEFAULT_ASSET_ROOT = Path.home() / ".codex" / "anime-character-director-assets"
KNOWN_LOCAL_ASSET_ROOT = Path("D:/anime-character-director-assets")
SUPPORTED_GAME_STYLE_IDS = frozenset(
    {
        "genshin_impact",
        "zenless_zone_zero",
        "wuthering_waves",
        "neverness_to_everness",
    }
)
REFERENCE_CONDITIONING_MODES = frozenset(
    {"disabled", "yaml_only", "yaml_plus_local_references", "auto"}
)
STYLE_DRIFT_POLICIES = frozenset({"strict", "balanced", "style_forward"})
REFERENCE_ROLES = frozenset(
    {
        "face_eye_skin",
        "hair_rendering",
        "body_presentation",
        "silhouette_design",
        "costume_structure",
        "material_rendering",
        "detail_hierarchy",
        "color_organization",
        "shadow_lighting",
        "ornament_language",
        "overall_character_art",
    }
)


class ReferenceManifestError(ValueError):
    """Raised when a present local manifest violates the v1 contract."""


@dataclass(frozen=True)
class StyleReference:
    """A validated local image plus the provenance needed for auditability."""

    reference_id: str
    game_style_id: str
    canonical_character_id: str
    character_name: str
    gender_presentation: str
    nonhuman_level: str
    absolute_path: str
    roles: tuple[str, ...]
    sha256: str
    width: int
    height: int
    source_type: str
    official_verified: bool
    quality_rank: int
    source_site: str = ""
    source_page: str = ""
    source_file_url: str = ""
    source_dataset: str = ""
    provenance_ref: str = ""
    selection_reason: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a reference without exposing a second path format."""
        data = asdict(self)
        data["roles"] = list(self.roles)
        data["selection_reason"] = list(self.selection_reason)
        return data


@dataclass(frozen=True)
class StyleReferenceBundle:
    """Resolver output, including graceful-fallback state and warnings."""

    game_style_id: str
    library_version: str = "v1"
    references: tuple[StyleReference, ...] = ()
    selection_reason: tuple[str, ...] = ()
    available: bool = False
    fallback_reason: str | None = None
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return the stable bundle schema used by debug tooling and tests."""
        return {
            "game_style_id": self.game_style_id,
            "library_version": self.library_version,
            "references": [item.to_dict() for item in self.references],
            "selection_reason": list(self.selection_reason),
            "available": self.available,
            "fallback_reason": self.fallback_reason,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ReferenceConditioningConfig:
    """Runtime switches for optional reference conditioning.

    The defaults keep the existing text/YAML path intact when no supported
    local library is available.  ``auto`` only promotes to local references
    after the manifest and selected files have passed validation.
    """

    enabled: bool = True
    max_images: int = DEFAULT_MAX_IMAGES
    mode: str = "auto"
    style_drift_policy_default_quick: str = "style_forward"
    style_drift_policy_default_ai_decide: str = "balanced"

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None = None) -> "ReferenceConditioningConfig":
        """Normalize config aliases and reject invalid policy values early."""
        raw = dict(value or {})
        section = raw.get("local_references")
        if isinstance(section, Mapping):
            raw = {**raw, **dict(section)}
        enabled = raw.get("enable_local_style_references", raw.get("enabled", True))
        if isinstance(enabled, str):
            enabled = enabled.strip().lower() not in {"0", "false", "no", "off"}
        max_images = raw.get("max_local_style_references", raw.get("max_images", DEFAULT_MAX_IMAGES))
        mode = str(raw.get("reference_conditioning_mode", raw.get("mode", "auto"))).strip().lower()
        quick_policy = str(raw.get("style_drift_policy_default_quick", "style_forward")).strip().lower()
        ai_policy = str(raw.get("style_drift_policy_default_ai_decide", "balanced")).strip().lower()
        if mode not in REFERENCE_CONDITIONING_MODES:
            raise ValueError(f"unsupported reference_conditioning_mode: {mode}")
        if quick_policy not in STYLE_DRIFT_POLICIES or ai_policy not in STYLE_DRIFT_POLICIES:
            raise ValueError("unsupported style drift policy")
        try:
            max_images = int(max_images)
        except (TypeError, ValueError) as error:
            raise ValueError("max_local_style_references must be an integer") from error
        if max_images < 1:
            raise ValueError("max_local_style_references must be positive")
        return cls(bool(enabled), min(max_images, MAX_REFERENCE_IMAGES), mode, quick_policy, ai_policy)

    def policy_for(self, mode: str | None) -> str:
        """Return the mode-specific drift policy without changing user locks."""
        return self.style_drift_policy_default_quick if str(mode).upper() == "QUICK" else self.style_drift_policy_default_ai_decide


@dataclass(frozen=True)
class ReferenceConditioningPayload:
    """Stable handoff describing selected images or a YAML-only fallback."""

    enabled: bool
    available: bool
    game_style_id: str | None
    library_version: str
    references: tuple[StyleReference, ...] = ()
    max_images_used: int = 0
    selection_reason: tuple[str, ...] = ()
    fallback_reason: str | None = None
    reference_conditioning_mode: str = "yaml_only"
    style_drift_policy: str = "balanced"
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize paths and selection metadata for debug/request artifacts."""
        return {
            "enabled": self.enabled,
            "available": self.available,
            "game_style_id": self.game_style_id,
            "library_version": self.library_version,
            "references": [item.to_dict() for item in self.references],
            "max_images_used": self.max_images_used,
            "selection_reason": list(self.selection_reason),
            "fallback_reason": self.fallback_reason,
            "reference_conditioning_mode": self.reference_conditioning_mode,
            "style_drift_policy": self.style_drift_policy,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class StyleConditioningContext:
    """The single internal object passed from style resolution to compilation."""

    game_style_id: str | None
    style_profile: Mapping[str, Any] | None
    reference_bundle: ReferenceConditioningPayload
    reference_mode: str
    drift_tolerance: str
    explicit_constraints: Mapping[str, Any]
    fallback_state: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe context for prompt and generation artifacts."""
        return {
            "game_style_id": self.game_style_id,
            "style_profile": dict(self.style_profile or {}),
            "reference_bundle": self.reference_bundle.to_dict(),
            "reference_mode": self.reference_mode,
            "drift_tolerance": self.drift_tolerance,
            "explicit_constraints": dict(self.explicit_constraints),
            "fallback_state": dict(self.fallback_state),
        }


def resolve_asset_root(
    explicit_asset_root: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    config_path: str | os.PathLike[str] | None = None,
) -> Path:
    """Resolve the asset root in the documented explicit/env/config/default order."""
    if explicit_asset_root:
        return Path(explicit_asset_root).expanduser()
    environment = os.environ if env is None else env
    if environment.get(ASSET_ROOT_ENV):
        return Path(environment[ASSET_ROOT_ENV]).expanduser()
    local_config = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    configured = _read_local_asset_root(local_config)
    if configured:
        return configured
    # WHY: the release workspace has a documented machine-local asset folder;
    # keep it discoverable while retaining the portable ~/.codex fallback.
    if (KNOWN_LOCAL_ASSET_ROOT / LIBRARY_DIRECTORY / MANIFEST_FILENAME).is_file():
        return KNOWN_LOCAL_ASSET_ROOT
    return DEFAULT_ASSET_ROOT


def _read_local_asset_root(path: Path) -> Path | None:
    """Read only the small supported YAML subset; no YAML dependency is needed."""
    if not path.is_file():
        return None
    value = _read_local_config(path).get("local_assets.root")
    return Path(value).expanduser() if value else None


def _read_local_config(path: Path) -> dict[str, Any]:
    """Read the tiny scalar YAML subset used by the local, non-Git config."""
    if not path.is_file():
        return {}
    values: dict[str, Any] = {}
    section = ""
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and stripped.endswith(":"):
            section = stripped[:-1].strip()
            continue
        if ":" not in stripped:
            continue
        key, _, raw_value = stripped.partition(":")
        raw_value = raw_value.split(" #", 1)[0].strip().strip("\"'")
        if raw_value.lower() in {"true", "false"}:
            value: Any = raw_value.lower() == "true"
        else:
            try:
                value = int(raw_value)
            except ValueError:
                value = os.path.expandvars(raw_value)
        values[f"{section}.{key.strip()}" if section else key.strip()] = value
    return values


def load_reference_conditioning_config(
    config_path: str | os.PathLike[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> ReferenceConditioningConfig:
    """Load config, environment overrides, and test/runtime overrides."""
    path = Path(config_path).expanduser() if config_path else DEFAULT_CONFIG_PATH
    values: dict[str, Any] = {}
    file_values = _read_local_config(path)
    for key, value in file_values.items():
        values[key.rsplit(".", 1)[-1]] = value
    values.update(dict(overrides or {}))
    environment = os.environ if env is None else env
    env_keys = {
        "enable_local_style_references": "ANIME_CHARACTER_DIRECTOR_ENABLE_LOCAL_STYLE_REFERENCES",
        "max_local_style_references": "ANIME_CHARACTER_DIRECTOR_MAX_LOCAL_STYLE_REFERENCES",
        "reference_conditioning_mode": "ANIME_CHARACTER_DIRECTOR_REFERENCE_CONDITIONING_MODE",
        "style_drift_policy_default_quick": "ANIME_CHARACTER_DIRECTOR_STYLE_DRIFT_POLICY_DEFAULT_QUICK",
        "style_drift_policy_default_ai_decide": "ANIME_CHARACTER_DIRECTOR_STYLE_DRIFT_POLICY_DEFAULT_AI_DECIDE",
    }
    for key, env_key in env_keys.items():
        if env_key in environment:
            values[key] = environment[env_key]
    return ReferenceConditioningConfig.from_mapping(values)


def apply_reference_preferences(
    reference_preferences: Mapping[str, Any],
    explicit_user_constraints: Mapping[str, Any],
) -> dict[str, Any]:
    """Filter style-derived preferences so explicit user fields always win.

    This intentionally stays a small ownership helper rather than a prompt
    merger: reference preferences may fill unlocked fields, but silently
    merging two visual specifications here would make ownership ambiguous.
    """
    locked = set(explicit_user_constraints.get("locked_fields", ()))
    locked.update(key for key in explicit_user_constraints if key != "locked_fields")
    return {key: value for key, value in reference_preferences.items() if key not in locked}


class ReferenceLibrary:
    """Load, validate, and deterministically select local style references."""

    def __init__(self, asset_root: str | os.PathLike[str] | None = None) -> None:
        self.asset_root = resolve_asset_root(asset_root)
        self.library_root = self.asset_root / LIBRARY_DIRECTORY
        self.manifest_path = self.library_root / MANIFEST_FILENAME
        self._manifest_error: str | None = None
        self._manifest = self._load_manifest()

    @property
    def library_available(self) -> bool:
        """Whether a valid manifest is present; individual image failures are later warnings."""
        return self._manifest is not None

    def resolve(
        self,
        game_style_id: str,
        roles: Sequence[str] | None = None,
        max_images: int = DEFAULT_MAX_IMAGES,
        context: Mapping[str, Any] | None = None,
    ) -> StyleReferenceBundle:
        """Select validated, cross-character references with a stable ordering."""
        if max_images < 1:
            raise ValueError("max_images must be positive")
        limit = min(max_images, MAX_REFERENCE_IMAGES)
        if self._manifest is None:
            return StyleReferenceBundle(
                game_style_id=game_style_id,
                available=False,
                fallback_reason=self._manifest_error or "LOCAL_REFERENCE_LIBRARY_UNAVAILABLE",
            )

        entry = self._manifest["games"].get(game_style_id)
        if not isinstance(entry, Mapping):
            return StyleReferenceBundle(
                game_style_id=game_style_id,
                library_version=self._manifest["library_version"],
                available=False,
                fallback_reason="LOCAL_REFERENCE_GAME_UNAVAILABLE",
            )

        warnings: list[str] = []
        valid: list[StyleReference] = []
        for raw in entry.get("references", ()):
            try:
                valid.append(self._materialize_reference(raw, game_style_id))
            except (OSError, ReferenceManifestError) as error:
                warnings.append(str(error))

        if not valid:
            return StyleReferenceBundle(
                game_style_id=game_style_id,
                library_version=self._manifest["library_version"],
                available=False,
                fallback_reason="LOCAL_REFERENCE_LIBRARY_ALL_REFERENCES_INVALID",
                warnings=tuple(warnings),
            )

        requested_roles = tuple(roles or (context or {}).get("preferred_roles", ()))
        requested_roles = tuple(role for role in requested_roles if role in REFERENCE_ROLES)
        excluded = set((context or {}).get("exclude_canonical_character_ids", ()))
        selected = _select_references(valid, requested_roles, limit, context or {}, excluded)
        return StyleReferenceBundle(
            game_style_id=game_style_id,
            library_version=self._manifest["library_version"],
            references=tuple(selected),
            selection_reason=(
                "deterministic_manifest_selection",
                "cross_character_preferred",
                f"max_images_capped_at_{MAX_REFERENCE_IMAGES}",
            ),
            available=bool(selected),
            fallback_reason=None if selected else "LOCAL_REFERENCE_LIBRARY_ALL_REFERENCES_INVALID",
            warnings=tuple(warnings),
        )

    def inspect(self, game_style_id: str) -> dict[str, Any]:
        """Return a JSON-safe debug view without making callers read the manifest."""
        bundle = self.resolve(game_style_id)
        return {
            "game_style_id": game_style_id,
            "asset_root": str(self.asset_root),
            "library_available": self.library_available,
            **bundle.to_dict(),
        }

    def inspect_all(self) -> list[dict[str, Any]]:
        """Inspect every game declared by the manifest, including future game IDs."""
        if self._manifest is None:
            return []
        return [self.inspect(game_id) for game_id in sorted(self._manifest["games"])]

    def _load_manifest(self) -> dict[str, Any] | None:
        if not self.manifest_path.is_file():
            return None
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            _validate_manifest(data)
        except (OSError, json.JSONDecodeError, ReferenceManifestError):
            # IMPORTANT: a broken optional asset must never break text/YAML generation.
            self._manifest_error = "LOCAL_REFERENCE_MANIFEST_INVALID"
            return None
        return data

    def _materialize_reference(self, raw: Any, game_style_id: str) -> StyleReference:
        if not isinstance(raw, Mapping):
            raise ReferenceManifestError(f"{game_style_id}: reference entry must be an object")
        relative = str(raw["relative_path"])
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ReferenceManifestError(f"{raw.get('id', '<unknown>')}: unsafe relative_path")
        path = (self.library_root / relative_path).resolve()
        try:
            path.relative_to(self.library_root.resolve())
        except ValueError as error:
            raise ReferenceManifestError(f"{raw.get('id', '<unknown>')}: path escapes library root") from error
        if not path.is_file():
            raise OSError(f"{raw.get('id', '<unknown>')}: image missing: {relative}")
        digest = _sha256(path)
        if digest != raw["sha256"]:
            raise OSError(f"{raw.get('id', '<unknown>')}: sha256 mismatch")
        dimensions = _image_dimensions(path)
        if dimensions is None or dimensions != (int(raw["width"]), int(raw["height"])):
            raise OSError(f"{raw.get('id', '<unknown>')}: invalid or mismatched image dimensions")
        return StyleReference(
            reference_id=str(raw["id"]),
            game_style_id=game_style_id,
            canonical_character_id=str(raw["canonical_character_id"]),
            character_name=str(raw["character_name"]),
            gender_presentation=str(raw["gender_presentation"]),
            nonhuman_level=str(raw["nonhuman_level"]),
            absolute_path=str(path),
            roles=tuple(str(role) for role in raw["roles"]),
            sha256=digest,
            width=int(raw["width"]),
            height=int(raw["height"]),
            source_type=str(raw["source_type"]),
            official_verified=bool(raw["official_verified"]),
            quality_rank=int(raw["quality_rank"]),
            source_site=str(raw.get("source_site") or ""),
            source_page=str(raw.get("source_page") or ""),
            source_file_url=str(raw.get("source_file_url") or ""),
            source_dataset=str(raw.get("source_dataset") or ""),
            provenance_ref=str(raw.get("provenance_ref") or ""),
            selection_reason=tuple(str(item) for item in raw.get("selection_reason", ())),
        )


def _validate_manifest(data: Any) -> None:
    """Validate trust-boundary fields before path or image access."""
    if not isinstance(data, Mapping):
        raise ReferenceManifestError("reference manifest must be an object")
    if data.get("schema_version") != "local_style_reference_manifest_v1":
        raise ReferenceManifestError("unsupported reference manifest schema_version")
    if not isinstance(data.get("library_version"), str) or not data["library_version"]:
        raise ReferenceManifestError("reference manifest requires library_version")
    games = data.get("games")
    if not isinstance(games, Mapping):
        raise ReferenceManifestError("reference manifest requires a games object")
    seen_ids: set[str] = set()
    for game_id, game in games.items():
        if not isinstance(game, Mapping) or not isinstance(game.get("references"), list):
            raise ReferenceManifestError(f"{game_id}: references must be a list")
        for ref in game["references"]:
            if not isinstance(ref, Mapping):
                raise ReferenceManifestError(f"{game_id}: reference must be an object")
            required = (
                "id", "game_style_id", "canonical_character_id", "character_name", "gender_presentation",
                "nonhuman_level", "relative_path", "sha256", "width", "height",
                "source_type", "official_verified", "roles", "quality_rank", "source_page", "source_file_url",
            )
            missing = [key for key in required if key not in ref]
            if missing:
                raise ReferenceManifestError(f"{game_id}: missing fields {missing}")
            reference_id = str(ref["id"])
            if reference_id in seen_ids:
                raise ReferenceManifestError(f"duplicate reference id: {reference_id}")
            seen_ids.add(reference_id)
            if str(ref["game_style_id"]) != str(game_id):
                raise ReferenceManifestError(f"{reference_id}: game_style_id does not match its game bucket")
            if not str(ref["canonical_character_id"]):
                raise ReferenceManifestError(f"{reference_id}: canonical_character_id is empty")
            if not isinstance(ref["roles"], list) or not ref["roles"] or not all(isinstance(role, str) for role in ref["roles"]) or not set(ref["roles"]).issubset(REFERENCE_ROLES):
                raise ReferenceManifestError(f"{reference_id}: invalid roles")
            if not isinstance(ref["sha256"], str) or len(ref["sha256"]) != 64 or any(char not in "0123456789abcdef" for char in ref["sha256"]):
                raise ReferenceManifestError(f"{reference_id}: sha256 must be lowercase hexadecimal")
            if not isinstance(ref["width"], int) or isinstance(ref["width"], bool) or not isinstance(ref["height"], int) or isinstance(ref["height"], bool) or ref["width"] <= 0 or ref["height"] <= 0:
                raise ReferenceManifestError(f"{reference_id}: dimensions must be positive")
            if not isinstance(ref["official_verified"], bool):
                raise ReferenceManifestError(f"{reference_id}: official_verified must be boolean")
            if ref["source_type"] not in {"official", "wiki"}:
                raise ReferenceManifestError(f"{reference_id}: source_type must be official or wiki")
            if not isinstance(ref["source_page"], str) or not ref["source_page"] or not isinstance(ref["source_file_url"], str) or not ref["source_file_url"]:
                raise ReferenceManifestError(f"{reference_id}: provenance URLs are required")
            if not isinstance(ref["quality_rank"], int) or isinstance(ref["quality_rank"], bool) or not 1 <= ref["quality_rank"] <= 5:
                raise ReferenceManifestError(f"{reference_id}: quality_rank must be 1-5")


def _select_references(
    candidates: Sequence[StyleReference],
    requested_roles: Sequence[str],
    limit: int,
    context: Mapping[str, Any],
    excluded: set[str],
) -> list[StyleReference]:
    """Greedy stable selection: role fit first, quality second, character diversity third."""
    role_weights = {
        "overall_character_art": 5,
        "face_eye_skin": 4,
        "hair_rendering": 4,
        "body_presentation": 4,
        "silhouette_design": 3,
        "costume_structure": 3,
        "material_rendering": 2,
        "detail_hierarchy": 2,
        "color_organization": 2,
        "shadow_lighting": 1,
        "ornament_language": 1,
    }
    context_key = json.dumps(context, ensure_ascii=False, sort_keys=True, default=str)

    def key(item: StyleReference) -> tuple[int, int, str, str]:
        role_score = sum(role_weights.get(role, 0) for role in item.roles)
        if requested_roles:
            role_score = sum(10 if role in requested_roles else 0 for role in item.roles)
        stable_tie = hashlib.sha256(f"{context_key}:{item.reference_id}".encode("utf-8")).hexdigest()
        return (-role_score, -item.quality_rank, stable_tie, item.reference_id)

    ordered = sorted((item for item in candidates if item.canonical_character_id not in excluded), key=key)
    selected: list[StyleReference] = []
    used_characters: set[str] = set()
    for item in ordered:
        if item.canonical_character_id in used_characters:
            continue
        selected.append(item)
        used_characters.add(item.canonical_character_id)
        if len(selected) == limit:
            return selected
    # If a future manifest has too few unique characters, fill the requested cap
    # rather than failing an otherwise usable local library.
    for item in ordered:
        if item not in selected:
            selected.append(item)
        if len(selected) == limit:
            break
    return selected


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_dimensions(path: Path) -> tuple[int, int] | None:
    """Read dimensions for the formats allowed by the local manifest."""
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP" and len(data) >= 30:
        if data[12:16] == b"VP8X":
            return (1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little"))
        return None
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            index += 2
            if marker in {0xD8, 0xD9}:
                continue
            if index + 2 > len(data):
                return None
            length = int.from_bytes(data[index:index + 2], "big")
            if marker in set(range(0xC0, 0xC4)) | set(range(0xC5, 0xC8)) | set(range(0xC9, 0xCC)) | set(range(0xCD, 0xD0)):
                if index + 7 > len(data):
                    return None
                return (int.from_bytes(data[index + 5:index + 7], "big"), int.from_bytes(data[index + 3:index + 5], "big"))
            if length < 2:
                return None
            index += length
    return None


def resolve_style_reference_bundle(
    game_style_id: str,
    roles: Sequence[str] | None = None,
    max_images: int = DEFAULT_MAX_IMAGES,
    context: Mapping[str, Any] | None = None,
    *,
    asset_root: str | os.PathLike[str] | None = None,
) -> StyleReferenceBundle:
    """Return validated selections and fallback metadata for the compiler seam."""
    return ReferenceLibrary(asset_root).resolve(game_style_id, roles, max_images, context)


def build_style_conditioning_context(
    game_style_id: str | None,
    *,
    mode: str | None = None,
    style_profile: Mapping[str, Any] | None = None,
    explicit_constraints: Mapping[str, Any] | None = None,
    requested_game_style_id: str | None = None,
    roles: Sequence[str] | None = None,
    context: Mapping[str, Any] | None = None,
    asset_root: str | os.PathLike[str] | None = None,
    config_path: str | os.PathLike[str] | None = None,
    config: ReferenceConditioningConfig | Mapping[str, Any] | None = None,
) -> StyleConditioningContext:
    """Resolve YAML plus optional local references at one production seam.

    ``auto`` is intentionally fail-closed: unsupported styles, malformed
    manifests, empty selections, and internal resolver errors all return a
    valid YAML-only context with a machine-readable fallback reason.
    """
    config_error: str | None = None
    try:
        if isinstance(config, ReferenceConditioningConfig):
            settings = config
        else:
            settings = load_reference_conditioning_config(config_path, overrides=config)
    except (OSError, ValueError, TypeError) as error:
        # IMPORTANT: malformed optional config follows the same YAML-only
        # fallback as a malformed manifest instead of breaking generation.
        settings = ReferenceConditioningConfig()
        config_error = f"LOCAL_REFERENCE_CONFIG_INVALID:{type(error).__name__}"
    requested_mode = settings.mode if mode is None else str(mode).strip().lower()
    if requested_mode not in REFERENCE_CONDITIONING_MODES:
        requested_mode = "auto"
    policy = settings.policy_for(mode)
    explicit = dict(explicit_constraints or {})
    requested_style = requested_game_style_id or game_style_id

    def fallback(reason: str, *, disabled: bool = False) -> StyleConditioningContext:
        payload = ReferenceConditioningPayload(
            enabled=not disabled,
            available=False,
            game_style_id=game_style_id,
            library_version="v1",
            fallback_reason=reason,
            reference_conditioning_mode="disabled" if disabled else "yaml_only",
            style_drift_policy=policy,
        )
        return StyleConditioningContext(
            game_style_id=game_style_id,
            style_profile=style_profile,
            reference_bundle=payload,
            reference_mode=payload.reference_conditioning_mode,
            drift_tolerance=policy,
            explicit_constraints=explicit,
            fallback_state={
                "requested_game_style_id": requested_style,
                "requested_mode": requested_mode,
                "reason": reason,
                "yaml_only": not disabled,
            },
        )

    if not settings.enabled or requested_mode == "disabled":
        return fallback("LOCAL_REFERENCE_CONDITIONING_DISABLED", disabled=True)
    if config_error:
        return fallback(config_error)
    if requested_mode == "yaml_only":
        return fallback("REFERENCE_CONDITIONING_MODE_YAML_ONLY")
    if not game_style_id or game_style_id not in SUPPORTED_GAME_STYLE_IDS:
        return fallback("UNSUPPORTED_GAME_STYLE")
    try:
        bundle = resolve_style_reference_bundle(
            game_style_id,
            roles=roles,
            max_images=settings.max_images,
            context=context,
            asset_root=asset_root,
        )
    except Exception as error:  # pragma: no cover - defensive boundary for optional assets
        return fallback(f"LOCAL_REFERENCE_CONDITIONING_ERROR:{type(error).__name__}")
    if not bundle.references:
        return fallback(bundle.fallback_reason or "LOCAL_REFERENCE_SELECTION_EMPTY")
    payload = ReferenceConditioningPayload(
        enabled=True,
        available=True,
        game_style_id=game_style_id,
        library_version=bundle.library_version,
        references=bundle.references,
        max_images_used=len(bundle.references),
        selection_reason=bundle.selection_reason,
        fallback_reason=None,
        reference_conditioning_mode="yaml_plus_local_references",
        style_drift_policy=policy,
        warnings=bundle.warnings,
    )
    return StyleConditioningContext(
        game_style_id=game_style_id,
        style_profile=style_profile,
        reference_bundle=payload,
        reference_mode=payload.reference_conditioning_mode,
        drift_tolerance=policy,
        explicit_constraints=explicit,
        fallback_state={
            "requested_game_style_id": requested_style,
            "requested_mode": requested_mode,
            "reason": None,
            "yaml_only": False,
        },
    )


def resolve_style_references(
    game_style_id: str,
    roles: Sequence[str] | None = None,
    max_images: int = DEFAULT_MAX_IMAGES,
    context: Mapping[str, Any] | None = None,
    *,
    asset_root: str | os.PathLike[str] | None = None,
) -> list[StyleReference]:
    """Formal resolver API requested by callers that only need selected images."""
    return list(resolve_style_reference_bundle(game_style_id, roles, max_images, context, asset_root=asset_root).references)


def main(argv: Sequence[str] | None = None) -> int:
    """Development-only inspection CLI; it never downloads or mutates assets."""
    parser = argparse.ArgumentParser(description="Inspect the optional local style reference library")
    parser.add_argument("command", choices=("inspect", "inspect-all"))
    parser.add_argument("game_style_id", nargs="?")
    parser.add_argument("--asset-root", dest="asset_root")
    args = parser.parse_args(argv)
    library = ReferenceLibrary(args.asset_root)
    if args.command == "inspect":
        if not args.game_style_id:
            parser.error("inspect requires game_style_id")
        payload: Any = library.inspect(args.game_style_id)
    else:
        payload = library.inspect_all()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by the CLI command
    raise SystemExit(main())
