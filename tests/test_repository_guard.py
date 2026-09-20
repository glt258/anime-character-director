"""Targeted checks for the development-only source-location guard."""

from pathlib import Path

import pytest

from scripts.repository_guard import (
    DevelopmentLocationError,
    is_installed_skill_path,
    require_development_repository,
)


def test_installed_skill_path_detection() -> None:
    assert is_installed_skill_path(Path(r"C:\Users\30931\.codex\skills\anime-character-director"))
    assert not is_installed_skill_path(Path(r"D:\anime-character-director-release"))


def test_guard_rejects_installed_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "scripts.repository_guard.repository_root",
        lambda _start=None: Path(r"C:\Users\30931\.codex\skills\anime-character-director"),
    )
    with pytest.raises(DevelopmentLocationError, match="Installed Skill directory"):
        require_development_repository(Path(r"C:\Users\30931\.codex\skills\anime-character-director"))
