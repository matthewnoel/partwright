"""`partwright new` — scaffold a standalone build123d part repository.

Implements the body of `run(args)` for the `partwright new` subcommand. The
signature is frozen by the dispatch contract in `cli.py`; only the body and the
module-level helpers below belong to Phase 1.

Standard library only: `string.Template` for placeholder substitution,
`tomllib` for the `DESIGN_BRIEF.md` TOML frontmatter, `pathlib` for files, and
`subprocess` for the optional `git init`.
"""

from __future__ import annotations

import argparse
import shutil
import string
import subprocess
import sys
import tomllib
from pathlib import Path

__all__ = ["run"]

# Directory holding the templates/project/ files, resolved relative to this
# module (partwright/scaffold.py -> ../templates/project).
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "project"

# Maps each template file to its rendered name in the generated repo. Files
# whose final name differs from a literal `.template` strip (dotfiles) are
# listed explicitly.
_FILE_MAP = {
    "generate.py.template": "generate.py",
    "preview.py.template": "preview.py",
    "CLAUDE.md.template": "CLAUDE.md",
    "README.md.template": "README.md",
    "reference_README.md.template": "reference/README.md",
    "requirements.txt.template": "requirements.txt",
    "requirements-dev.txt.template": "requirements-dev.txt",
    "gitignore.template": ".gitignore",
    "settings.local.json.template": ".claude/settings.local.json",
}

# Units accepted in the brief's top-level `units` field.
_KNOWN_UNITS = {"mm", "inches"}

# Per-unit abbreviation used as the suffix on a generated constant name.
_UNIT_SUFFIX = {"mm": "MM", "inches": "IN"}


class BriefError(Exception):
    """Raised when a `DESIGN_BRIEF.md` is malformed or missing a field."""


# ----------------------------------------------------------------------------
# Brief parsing
# ----------------------------------------------------------------------------


def _extract_frontmatter(text: str, brief_path: Path) -> str:
    """Return the TOML text between the leading `+++` fences of a brief.

    Raises BriefError if the `+++`-fenced block is absent or unterminated.
    """
    lines = text.splitlines()
    # Find the opening fence: the first non-blank line must be `+++`.
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines) or lines[idx].strip() != "+++":
        raise BriefError(
            f"{brief_path}: no '+++'-fenced TOML frontmatter at the top of the file."
        )
    start = idx + 1
    # Find the closing fence.
    for end in range(start, len(lines)):
        if lines[end].strip() == "+++":
            return "\n".join(lines[start:end])
    raise BriefError(
        f"{brief_path}: TOML frontmatter opened with '+++' but never closed."
    )


def _parse_brief(brief_path: Path) -> dict:
    """Read, parse, and validate a `DESIGN_BRIEF.md` against SCHEMA.md.

    Returns the parsed frontmatter dict. Raises BriefError on any malformed or
    missing required field — the scaffolder never guesses.
    """
    try:
        text = brief_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BriefError(f"cannot read brief {brief_path}: {exc}") from exc

    toml_text = _extract_frontmatter(text, brief_path)
    try:
        data = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:
        raise BriefError(
            f"{brief_path}: TOML frontmatter failed to parse: {exc}"
        ) from exc

    # --- Required: project_name --------------------------------------------
    project_name = data.get("project_name")
    if not isinstance(project_name, str) or not project_name.strip():
        raise BriefError(
            f"{brief_path}: required field 'project_name' is missing or not a string."
        )

    # --- units (optional, default mm) --------------------------------------
    units = data.get("units", "mm")
    if not isinstance(units, str) or units not in _KNOWN_UNITS:
        raise BriefError(
            f"{brief_path}: 'units' must be one of {sorted(_KNOWN_UNITS)}; got {units!r}."
        )
    data["units"] = units

    # --- summary (optional) -------------------------------------------------
    summary = data.get("summary")
    if summary is not None and not isinstance(summary, str):
        raise BriefError(f"{brief_path}: 'summary' must be a string if present.")

    # --- components (optional) ---------------------------------------------
    components = data.get("components")
    if components is not None:
        if not isinstance(components, list) or not all(
            isinstance(c, str) for c in components
        ):
            raise BriefError(
                f"{brief_path}: 'components' must be an array of strings if present."
            )

    # --- coordinate_system (optional) --------------------------------------
    coord = data.get("coordinate_system")
    if coord is not None and not isinstance(coord, dict):
        raise BriefError(
            f"{brief_path}: 'coordinate_system' must be a table if present."
        )

    # --- parameters (required, one or more) --------------------------------
    parameters = data.get("parameters")
    if not isinstance(parameters, list) or not parameters:
        raise BriefError(
            f"{brief_path}: required '[[parameters]]' array is missing or empty."
        )
    for i, param in enumerate(parameters):
        if not isinstance(param, dict):
            raise BriefError(f"{brief_path}: parameter #{i + 1} is not a table.")
        for key in ("name", "meaning", "default", "cli"):
            if key not in param:
                raise BriefError(
                    f"{brief_path}: parameter #{i + 1} is missing required key '{key}'."
                )
        if not isinstance(param["name"], str) or not param["name"].strip():
            raise BriefError(
                f"{brief_path}: parameter #{i + 1} 'name' must be a non-empty string."
            )
        if not isinstance(param["meaning"], str):
            raise BriefError(
                f"{brief_path}: parameter '{param['name']}' 'meaning' must be a string."
            )
        if isinstance(param["default"], bool) or not isinstance(
            param["default"], (int, float)
        ):
            raise BriefError(
                f"{brief_path}: parameter '{param['name']}' 'default' must be a number."
            )
        if not isinstance(param["cli"], bool):
            raise BriefError(
                f"{brief_path}: parameter '{param['name']}' 'cli' must be a boolean."
            )
        unit = param.get("unit")
        if unit is not None and not isinstance(unit, str):
            raise BriefError(
                f"{brief_path}: parameter '{param['name']}' 'unit' must be a string."
            )

    return data


# ----------------------------------------------------------------------------
# Brief -> code derivation (SCHEMA.md "Constant and flag derivation rule")
# ----------------------------------------------------------------------------


def _constant_name(param: dict, default_units: str) -> str:
    """Derive a generated constant name: NAME uppercased + unit suffix."""
    unit = param.get("unit") or default_units
    suffix = _UNIT_SUFFIX.get(unit, unit.upper())
    return f"{param['name'].upper()}_{suffix}"


def _flag_name(param: dict) -> str:
    """Derive a CLI flag: name with underscores -> hyphens, '--' prefixed."""
    return "--" + param["name"].replace("_", "-")


# black wraps any source line that exceeds this many columns; the generated
# `generate.py` must already be black-clean, so the renderers below pre-wrap.
_BLACK_LINE_LENGTH = 88


def _format_default(value) -> str:
    """Render a numeric default the way the generated source should carry it."""
    if isinstance(value, float):
        return repr(value)
    return str(value)


def _dq(text: str) -> str:
    """Return `text` as a double-quoted Python string literal (black's quote)."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _constant_line(const: str, value_src: str, comment: str) -> str:
    """Render `CONST = value  # comment`, pre-wrapped the way black would.

    black, faced with a too-long `NAME = value  # comment`, parenthesizes the
    value and moves the comment onto the value's line. Emit that form directly
    when the single-line version would exceed the line-length limit.
    """
    single = f"{const} = {value_src}  # {comment}"
    if len(single) <= _BLACK_LINE_LENGTH:
        return single
    return f"{const} = (\n    {value_src}  # {comment}\n)"


def _render_seeded_constants(brief: dict) -> str:
    """Build the named-constants block seeded from the brief's parameters."""
    units = brief["units"]
    lines = [
        "",
        "# === Seeded from DESIGN_BRIEF.md ============================================",
        "# These constants come from the design brief. The placeholder geometry above",
        "# does not use them yet — a build agent wires them into `build_part` when the",
        "# real part is implemented (see BUILD_PLAN.md).",
    ]
    for param in brief["parameters"]:
        const = _constant_name(param, units)
        lines.append(
            _constant_line(const, _format_default(param["default"]), param["meaning"])
        )
    return "\n".join(lines)


def _render_seeded_cli_args(brief: dict) -> str:
    """Build the argparse add_argument calls for cli=true parameters."""
    units = brief["units"]
    components = brief.get("components") or []
    blocks: list[str] = []

    if len(components) > 1:
        choices = ", ".join(_dq(c) for c in components)
        blocks.append(
            "    p.add_argument(\n"
            '        "--component",\n'
            f"        choices=[{choices}],\n"
            f"        default={_dq(components[0])},\n"
            "        help=(\n"
            '            "Which artifact to build. Seeded from the brief; the "\n'
            '            "placeholder geometry ignores it."\n'
            "        ),\n"
            "    )\n"
        )

    for param in brief["parameters"]:
        if not param["cli"]:
            continue
        const = _constant_name(param, units)
        flag = _flag_name(param)
        # Escape for embedding inside an f-string literal: backslashes and
        # double quotes for the literal, and braces so they are not read as
        # f-string replacement fields.
        help_text = (
            param["meaning"]
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("{", "{{")
            .replace("}", "}}")
        )
        blocks.append(
            f"    p.add_argument(\n"
            f'        "{flag}",\n'
            f"        type=float,\n"
            f"        default={const},\n"
            f'        metavar="VALUE",\n'
            f'        help=f"{help_text} (default: {{{const}}}).",\n'
            f"    )\n"
        )
    return "".join(blocks)


def _render_seeded_param_prints(brief: dict) -> str:
    """Build the resolved-parameter print() lines for cli=true parameters."""
    components = brief.get("components") or []
    lines: list[str] = []
    if len(components) > 1:
        lines.append('    print(f"  Component            : {args.component}")\n')
    for param in brief["parameters"]:
        if not param["cli"]:
            continue
        attr = param["name"]
        label = param["name"].replace("_", " ")
        label = (label[:20]).ljust(20)
        lines.append(f'    print(f"  {label}: {{args.{attr}}}")\n')
    return "".join(lines)


# ----------------------------------------------------------------------------
# Coordinate-system / summary rendering
# ----------------------------------------------------------------------------


def _coord_lines(brief: dict | None):
    """Return (docstring_block, claude_block) for the coordinate-system notes."""
    default = {
        "x": "first in-plane axis",
        "y": "second in-plane axis",
        "z": "vertical, up off the build plate",
    }
    coord = (brief or {}).get("coordinate_system") or {}
    axes = {k: coord.get(k) or default[k] for k in ("x", "y", "z")}

    doc = "\n".join(f"    +{axis.upper()} : {axes[axis]}" for axis in ("x", "y", "z"))
    claude = "\n".join(
        f"- **+{axis.upper()}** — {axes[axis]}" for axis in ("x", "y", "z")
    )
    return doc, claude


def _summary_blocks(brief: dict | None):
    """Return (docstring, claude, readme) summary fragments for substitution.

    The placeholder occupies its own line directly after a heading line; that
    line carries its own trailing newline. An empty fragment ("") leaves a
    single blank line between heading and body. A populated fragment is
    "\\n<summary>": its leading newline makes a blank line above the summary,
    and the placeholder line's own newline closes it.
    """
    summary = (brief or {}).get("summary")
    if summary:
        block = f"\n{summary}"
        return (block, block, block)
    return ("", "", "")


# ----------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------


def _build_substitutions(project_name: str, brief: dict | None) -> dict:
    """Assemble the full placeholder -> value mapping for string.Template."""
    coord_doc, coord_claude = _coord_lines(brief)
    summary_doc, summary_claude, summary_readme = _summary_blocks(brief)

    if brief is not None:
        seeded_constants = _render_seeded_constants(brief)
        seeded_cli_args = _render_seeded_cli_args(brief)
        seeded_param_prints = _render_seeded_param_prints(brief)
        build_plan_pointer = (
            "\n## Build plan\n\n"
            "A `BUILD_PLAN.md` accompanies this repo. A build agent implementing "
            "the real geometry in `generate.py` should work from `BUILD_PLAN.md` "
            "as the implementation handoff, and `DESIGN_BRIEF.md` as the design "
            "record.\n"
        )
    else:
        seeded_constants = ""
        seeded_cli_args = ""
        seeded_param_prints = ""
        build_plan_pointer = ""

    return {
        "project_name": project_name,
        "default_output": f"{project_name}.stl",
        "cube_size_default": "10.0",
        "coord_docstring": coord_doc,
        "coord_claude": coord_claude,
        "summary_docstring": summary_doc,
        "summary_claude": summary_claude,
        "summary_readme": summary_readme,
        "seeded_constants": seeded_constants,
        "seeded_cli_args": seeded_cli_args,
        "seeded_param_prints": seeded_param_prints,
        "build_plan_pointer": build_plan_pointer,
    }


def _render_file(template_path: Path, subs: dict) -> str:
    """Render one template file via string.Template substitution."""
    raw = template_path.read_text(encoding="utf-8")
    return string.Template(raw).substitute(subs)


# ----------------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------------


def run(args: argparse.Namespace) -> int:
    """Entry point for `partwright new`.

    Receives the parsed namespace from `cli.py`. Relevant attributes:
    `args.project_name`, `args.dest`, `args.brief`, `args.no_git`.

    Returns an integer exit code (0 on success, non-zero on error).
    """
    project_name = args.project_name
    dest_dir = Path(args.dest).expanduser()
    repo_dir = dest_dir / project_name

    # --- Parse the brief first so a bad brief fails before any files exist --
    brief: dict | None = None
    brief_path: Path | None = None
    build_plan_path: Path | None = None
    copied_sketches = 0
    if args.brief is not None:
        brief_path = Path(args.brief).expanduser()
        if not brief_path.is_file():
            print(f"error: brief not found: {brief_path}", file=sys.stderr)
            return 1
        try:
            brief = _parse_brief(brief_path)
        except BriefError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        sibling = brief_path.parent / "BUILD_PLAN.md"
        if sibling.is_file():
            build_plan_path = sibling

    # --- Refuse to clobber an existing directory ---------------------------
    if repo_dir.exists():
        print(f"error: destination already exists: {repo_dir}", file=sys.stderr)
        return 1

    # --- Verify the template directory is present --------------------------
    if not _TEMPLATE_DIR.is_dir():
        print(
            f"error: scaffolder templates not found at {_TEMPLATE_DIR}",
            file=sys.stderr,
        )
        return 1

    # --- Render every template file ---------------------------------------
    subs = _build_substitutions(project_name, brief)
    try:
        repo_dir.mkdir(parents=True)
        for template_name, out_name in _FILE_MAP.items():
            template_path = _TEMPLATE_DIR / template_name
            if not template_path.is_file():
                print(
                    f"error: missing template file: {template_path}",
                    file=sys.stderr,
                )
                return 1
            rendered = _render_file(template_path, subs)
            out_path = repo_dir / out_name
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered, encoding="utf-8")

        # --- Copy the brief and build plan into the new repo --------------
        if brief_path is not None:
            (repo_dir / "DESIGN_BRIEF.md").write_text(
                brief_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
        if build_plan_path is not None:
            (repo_dir / "BUILD_PLAN.md").write_text(
                build_plan_path.read_text(encoding="utf-8"), encoding="utf-8"
            )

        # --- Copy reference sketches from the idea workspace --------------
        # The brief's sibling `sketches/` (populated by `partwright sketch`)
        # carries the SVGs into the repo's `reference/` so the build agent can
        # see the design intent without a manual file handoff.
        if brief_path is not None:
            sketches_src = brief_path.parent / "sketches"
            if sketches_src.is_dir():
                reference_dir = repo_dir / "reference"
                reference_dir.mkdir(parents=True, exist_ok=True)
                for svg in sorted(sketches_src.glob("*.svg")):
                    shutil.copyfile(svg, reference_dir / svg.name)
                    copied_sketches += 1
    except OSError as exc:
        print(f"error: failed to write the new repo: {exc}", file=sys.stderr)
        return 1

    # --- git init ----------------------------------------------------------
    git_initialized = False
    if not args.no_git:
        try:
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=repo_dir,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            git_initialized = True
        except FileNotFoundError:
            print(
                "warning: git not found on PATH; skipped 'git init'.",
                file=sys.stderr,
            )
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or b"").decode("utf-8", "replace").strip()
            print(
                f"warning: 'git init' failed ({stderr}); repo created without git.",
                file=sys.stderr,
            )

    # --- Resolved-parameters summary --------------------------------------
    print(f"Scaffolded project: {project_name}")
    print(f"  Location           : {repo_dir}")
    print(f"  Brief              : {brief_path if brief_path else '(none)'}")
    if brief is not None:
        print(f"  Summary            : {brief.get('summary') or '(none)'}")
        print(f"  Units              : {brief['units']}")
        components = brief.get("components") or []
        if components:
            print(f"  Components         : {', '.join(components)}")
        print("  Seeded constants   :")
        for param in brief["parameters"]:
            const = _constant_name(param, brief["units"])
            flag = _flag_name(param) if param["cli"] else "(no flag)"
            print(f"    {const} = {_format_default(param['default'])}  [{flag}]")
        if build_plan_path is not None:
            print("  BUILD_PLAN.md      : copied into the repo")
        print("  DESIGN_BRIEF.md    : copied into the repo")
    print(f"  git initialized    : {git_initialized}")
    if copied_sketches:
        suffix = "" if copied_sketches == 1 else "es"
        print(f"  Reference sketches : {copied_sketches} sketch{suffix} -> reference/")
    print()
    print("Next steps:")
    print(f"  1. cd {repo_dir}")
    print("  2. uv venv .venv --python 3.12")
    print("     uv pip install -r requirements.txt    # build123d + preview deps")
    print("  3. Sanity-check the skeleton:")
    print("       .venv/bin/python generate.py        # writes the STL")
    print("       .venv/bin/python preview.py         # writes preview.png")
    print("  4. Open this folder in Claude Code; its CLAUDE.md drives the loop:")
    print("       implement build_part -> generate.py -> preview.py ->")
    print("       read preview.png -> iterate.")
    print("  5. Add design intent: drop SVGs/photos in reference/, or run")
    print(f"       partwright sketch --dest {repo_dir / 'reference'}")

    return 0
