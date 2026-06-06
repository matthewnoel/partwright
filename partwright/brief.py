"""`partwright brief` — create an idea workspace from the blank templates.

Phase 0 stub. Phase 2 replaces only the body of `run(args)` below; the
signature is frozen by the dispatch contract in `cli.py`.

`run` is a convenience helper: it stamps an idea-workspace folder containing
copies of the three blank brief templates and a `sketches/` subfolder. It does
not run an interactive questionnaire — the interview happens in a step-1 Claude
chat driven by the copied `DESIGN_INTERVIEW.md`.

Standard library only.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

__all__ = ["run"]

# The blank templates copied into every idea workspace, in the order they are
# listed back to the user. Names are relative to `templates/brief/`.
_TEMPLATE_FILES = (
    "DESIGN_INTERVIEW.md",
    "DESIGN_BRIEF.md",
    "BUILD_PLAN.md",
)

# Subfolder created for reference SVGs from `partwright sketch`.
_SKETCHES_DIRNAME = "sketches"


def _templates_dir() -> Path:
    """Absolute path to Partwright's `templates/brief/` directory.

    `brief.py` lives at `<repo>/partwright/brief.py`, so the templates are a
    sibling of `partwright/` at `<repo>/templates/brief/`.
    """
    return Path(__file__).resolve().parent.parent / "templates" / "brief"


def run(args: argparse.Namespace) -> int:
    """Entry point for `partwright brief`.

    Receives the parsed namespace from `cli.py`. Relevant attributes:
    `args.idea_name`, `args.dest`.

    Creates `<dest>/<idea_name>/` containing copies of the three blank brief
    templates and an empty `sketches/` subfolder, then prints a short summary.

    Returns an integer exit code: 0 on success, non-zero on error.
    """
    idea_name = args.idea_name
    if not idea_name or not idea_name.strip():
        print("partwright brief: error: idea name must not be empty.")
        return 1

    templates_dir = _templates_dir()

    # Fail early with a clear message if the installed templates are missing,
    # rather than producing a half-populated workspace.
    missing = [name for name in _TEMPLATE_FILES if not (templates_dir / name).is_file()]
    if missing:
        print(
            "partwright brief: error: missing brief template(s): " + ", ".join(missing)
        )
        print(f"  expected under: {templates_dir}")
        return 1

    workspace = Path(args.dest).expanduser() / idea_name

    if workspace.exists():
        print(f"partwright brief: error: workspace already exists: {workspace}")
        print("  choose a different idea name or remove the existing folder.")
        return 1

    try:
        workspace.mkdir(parents=True)
        for name in _TEMPLATE_FILES:
            shutil.copyfile(templates_dir / name, workspace / name)
        sketches_dir = workspace / _SKETCHES_DIRNAME
        sketches_dir.mkdir()
    except OSError as exc:
        print(f"partwright brief: error: could not create workspace: {exc}")
        return 1

    print(f"Created idea workspace: {workspace}")
    for name in _TEMPLATE_FILES:
        print(f"  + {name}")
    print(f"  + {_SKETCHES_DIRNAME}/")
    print()
    print("Next steps:")
    print(f"  1. Draw reference outlines:  partwright sketch --dest {sketches_dir}")
    print(
        "  2. In a step-1 Claude chat, point Claude at "
        "DESIGN_INTERVIEW.md and attach the sketches."
    )
    print("  3. Claude interviews you and fills in DESIGN_BRIEF.md and BUILD_PLAN.md.")
    print(
        f"  4. Scaffold the repo:  partwright new {idea_name} "
        f"--brief {workspace / 'DESIGN_BRIEF.md'}"
    )
    print("     (sketches in this workspace are copied into the repo's reference/).")
    return 0
