"""`partwright install-skill` — install the design-part orchestrator skill.

Implements the body of `run(args)` for the `partwright install-skill`
subcommand. The signature is frozen by the dispatch contract in `cli.py`.

The bundled skill (`partwright/skills/design-part/`) turns one Claude Code
session into the orchestrator for the whole Partwright flow. This command copies
it to where Claude Code looks for skills, at either of two scopes:

- user scope (default):   ~/.claude/skills/design-part/
- directory scope:        <DIR>/.claude/skills/design-part/

Directory scope lets a parent folder that holds several part projects carry the
skill without adding it to global context everywhere.

Standard library only.
"""

from __future__ import annotations

import argparse
import os
import shutil
from importlib.resources import files
from pathlib import Path

__all__ = ["run"]

# Name of the bundled skill directory, reused as the install destination name.
_SKILL_NAME = "design-part"


def _source_dir() -> Path:
    """Absolute path to the bundled `skills/design-part/` directory.

    Ships inside the package, resolved through importlib.resources so it is found
    whether Partwright runs from a clone or an installed wheel.
    """
    return Path(str(files("partwright") / "skills" / _SKILL_NAME))


def _user_skills_dir() -> Path:
    """The user-scope Claude Code skills directory.

    Honors `CLAUDE_CONFIG_DIR` when set, matching how Claude Code locates its own
    configuration; otherwise falls back to `~/.claude`.
    """
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    base = Path(config_dir).expanduser() if config_dir else Path.home() / ".claude"
    return base / "skills"


def run(args: argparse.Namespace) -> int:
    """Entry point for `partwright install-skill`.

    Receives the parsed namespace from `cli.py`. Relevant attributes:
    `args.dest` (str|None — directory scope when given), `args.force` (bool).
    A `None` dest means user scope.

    Returns an integer exit code: 0 on success, non-zero on error.
    """
    source = _source_dir()
    if not (source / "SKILL.md").is_file():
        print(
            "partwright install-skill: error: bundled skill is missing from the install."
        )
        print(f"  expected: {source / 'SKILL.md'}")
        return 1

    if args.dest is None:
        skills_dir = _user_skills_dir()
        scope = "user"
    else:
        skills_dir = Path(args.dest).expanduser() / ".claude" / "skills"
        scope = "directory"

    target = skills_dir / _SKILL_NAME

    if target.exists() and not args.force:
        print(f"partwright install-skill: error: skill already installed at {target}")
        print("  pass --force to overwrite it.")
        return 1

    try:
        skills_dir.mkdir(parents=True, exist_ok=True)
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(source, target)
    except OSError as exc:
        print(f"partwright install-skill: error: could not install skill: {exc}")
        return 1

    print(f"Installed the '{_SKILL_NAME}' skill ({scope} scope):")
    print(f"  {target}")
    print()
    print("In a Claude Code session, start a design with:  /design-part")
    if scope == "directory":
        print("  (available within that directory and its subfolders).")
    return 0
