"""Guard development scripts against editing an installed Skill copy."""

from __future__ import annotations

from pathlib import Path
import subprocess


class DevelopmentLocationError(RuntimeError):
    """Raised when a development-only script is run from the C: copy."""


def repository_root(start: Path | None = None) -> Path:
    """Resolve the Git root for ``start`` and fail closed when it is unknown."""
    location = Path(start or Path.cwd()).resolve()
    result = subprocess.run(
        ("git", "-C", str(location), "rev-parse", "--show-toplevel"),
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise DevelopmentLocationError(f"Cannot resolve a Git repository root from {location}")
    return Path(result.stdout.strip()).resolve()


def is_installed_skill_path(root: Path) -> bool:
    """Return whether ``root`` is under the Codex installed Skill directory."""
    parts = tuple(part.casefold() for part in Path(root).parts)
    return any(parts[index : index + 2] == (".codex", "skills") for index in range(len(parts) - 1))


def require_development_repository(start: Path | None = None) -> Path:
    """Allow development scripts only when the resolved root is the D: source."""
    root = repository_root(start)
    if is_installed_skill_path(root):
        raise DevelopmentLocationError(
            "Installed Skill directory detected. Development changes must be made in the D: source repository."
        )
    return root
