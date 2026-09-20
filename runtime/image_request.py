"""Build the backend-neutral image-generation handoff.

The local runtime stops before calling ImageGen.  This module keeps the
request shape ready for that later boundary while making reference attachment
optional and safe to ignore by text-only backends.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CompiledImageRequest:
    """A complete generation request, including validated local references."""

    prompt_text: str
    negative_text: str = ""
    reference_image_paths: tuple[str, ...] = ()
    reference_metadata: dict[str, Any] = field(default_factory=dict)
    mode: str = "AI_DECIDE"
    style_game_id: str | None = None
    used_yaml_profile: bool = False
    used_local_references: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stable backend handoff without changing the prompt."""
        data = asdict(self)
        data["reference_image_paths"] = list(self.reference_image_paths)
        return data


def build_image_request(
    prompt_bundle: Mapping[str, Any],
    *,
    mode: str | None = None,
) -> CompiledImageRequest:
    """Attach references only when the compiled conditioning payload is active."""
    conditioning = prompt_bundle.get("reference_conditioning")
    if not isinstance(conditioning, Mapping):
        conditioning = {}
    bundle = conditioning.get("reference_bundle")
    if not isinstance(bundle, Mapping):
        bundle = conditioning.get("payload")
    if not isinstance(bundle, Mapping):
        bundle = {}
    references = bundle.get("references", ())
    paths = tuple(
        str(item.get("absolute_path"))
        for item in references
        if isinstance(item, Mapping) and item.get("absolute_path")
    )
    active = bool(
        bundle.get("enabled")
        and bundle.get("available")
        and bundle.get("reference_conditioning_mode") == "yaml_plus_local_references"
        and paths
    )
    return CompiledImageRequest(
        prompt_text=str(prompt_bundle.get("prompt", "")),
        negative_text="\n".join(str(item) for item in prompt_bundle.get("negative_constraints", ())),
        reference_image_paths=paths if active else (),
        reference_metadata={
            "game_style_id": bundle.get("game_style_id"),
            "library_version": bundle.get("library_version"),
            "reference_ids": [
                str(item.get("reference_id"))
                for item in references
                if isinstance(item, Mapping) and item.get("reference_id")
            ],
            "roles": [
                list(item.get("roles", ()))
                for item in references
                if isinstance(item, Mapping)
            ],
            "selection_reason": list(bundle.get("selection_reason", ())),
            "fallback_reason": bundle.get("fallback_reason"),
            "reference_conditioning_mode": bundle.get("reference_conditioning_mode", "yaml_only"),
            "style_drift_policy": bundle.get("style_drift_policy"),
        },
        mode=str(mode or prompt_bundle.get("creation_mode") or "AI_DECIDE"),
        style_game_id=(
            str(prompt_bundle.get("game_style_id") or bundle.get("game_style_id"))
            if (prompt_bundle.get("game_style_id") or bundle.get("game_style_id"))
            else None
        ),
        used_yaml_profile=bool(prompt_bundle.get("game_style_id") or conditioning.get("style_profile")),
        used_local_references=active,
    )


__all__ = ["CompiledImageRequest", "build_image_request"]
