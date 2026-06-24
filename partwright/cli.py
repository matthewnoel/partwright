"""Partwright command-line interface — the complete CLI and dispatch contract.

This module owns *all* argument parsing for Partwright: the top-level parser and
every subcommand with every flag and its help text. It parses the command line
into an `argparse.Namespace` and dispatches that namespace to the owning
subcommand module's `run(args)` function.

CONTRACT (Phase 0 froze the original surface; the `install-skill` subcommand
was added later as a deliberate product evolution — extend this file the same
way, by adding a subparser and a `run(args)` module, never by reshaping an
existing subcommand's namespace):

- Each subcommand module (`scaffold`, `brief`, `sketch`, `skill`) exposes
  exactly one public entry point: `run(args)`, where `args` is the parsed
  `argparse.Namespace`. `run` returns an `int` exit code (0 on success) or
  `None` (treated as 0). Modules replace only the *body* of their own `run`;
  they must not change its signature.
- The namespace passed to each `run` carries these attributes:
    new          -> args.project_name (str), args.dest (str),
                    args.brief (str|None), args.no_git (bool)
    brief        -> args.idea_name (str), args.dest (str)
    sketch       -> args.dest (str), args.no_serve (bool)
    install-skill-> args.dest (str|None), args.force (bool)
  Every namespace also carries `args.command` (the subcommand name) and
  `args.func` (the bound `run` callable chosen by the dispatcher).

Standard library only — no third-party imports.
"""

from __future__ import annotations

import argparse
import sys

from partwright import brief, scaffold, sketch, skill

__all__ = ["build_parser", "main"]

PROG = "partwright"
DESCRIPTION = (
    "Partwright — a toolkit for designing 3D-printable build123d parts: "
    "scaffold standalone part repos, generate design briefs, and sketch "
    "reference drawings."
)


def build_parser() -> argparse.ArgumentParser:
    """Construct the complete Partwright argument parser.

    The full CLI surface is defined here and only here. Subcommand modules
    never parse arguments themselves; they receive the parsed namespace.
    """
    parser = argparse.ArgumentParser(
        prog=PROG,
        description=DESCRIPTION,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROG} 0.1.0",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="<command>",
        help="the Partwright subcommand to run",
    )
    # Python 3.12 leaves `dest` optional by default; require a subcommand so
    # `partwright` with no arguments fails cleanly instead of doing nothing.
    subparsers.required = True

    # --- partwright new ------------------------------------------------------
    new_parser = subparsers.add_parser(
        "new",
        help="scaffold a new standalone build123d part repository",
        description=(
            "Stamp a fresh, self-contained build123d part repository that "
            "matches the phone-centipede structure, so a step-2 build never "
            "starts from an empty folder."
        ),
    )
    new_parser.add_argument(
        "project_name",
        metavar="<project-name>",
        help="name of the new repository / directory (should be identifier-safe)",
    )
    new_parser.add_argument(
        "--dest",
        metavar="DIR",
        default=".",
        help="directory in which to create the new repo (default: current directory)",
    )
    new_parser.add_argument(
        "--brief",
        metavar="FILE",
        default=None,
        help=(
            "path to a DESIGN_BRIEF.md whose TOML frontmatter pre-populates the "
            "repo's constants, CLI flags, and coordinate-system notes; the brief "
            "and any sibling BUILD_PLAN.md are copied into the new repo"
        ),
    )
    new_parser.add_argument(
        "--no-git",
        action="store_true",
        help="skip the `git init` the scaffolder otherwise runs on the new repo",
    )
    new_parser.set_defaults(func=scaffold.run)

    # --- partwright brief ----------------------------------------------------
    brief_parser = subparsers.add_parser(
        "brief",
        help="create an idea workspace with blank brief templates",
        description=(
            "Create an idea-workspace folder pre-loaded with the blank design "
            "templates (DESIGN_BRIEF.md, BUILD_PLAN.md), the reusable interview "
            "prompt, and a sketches/ subfolder. This copies files; it does not "
            "run an interactive questionnaire."
        ),
    )
    brief_parser.add_argument(
        "idea_name",
        metavar="<idea-name>",
        help="name of the idea workspace folder to create",
    )
    brief_parser.add_argument(
        "--dest",
        metavar="DIR",
        default=".",
        help="directory in which to create the idea workspace (default: current directory)",
    )
    brief_parser.set_defaults(func=brief.run)

    # --- partwright sketch ---------------------------------------------------
    sketch_parser = subparsers.add_parser(
        "sketch",
        help="launch the SVG click-to-draw sketch tool",
        description=(
            "Start a tiny local server that serves the self-contained SVG "
            "sketch tool and opens it in the browser. Drawings save into the "
            "chosen folder; the same page also works opened directly via "
            "file:// with download-based export."
        ),
    )
    sketch_parser.add_argument(
        "--dest",
        metavar="DIR",
        default=".",
        help="folder that drawings save into (default: current directory)",
    )
    sketch_parser.add_argument(
        "--no-serve",
        action="store_true",
        help=(
            "do not start the server or open a browser; just ensure the dest "
            "folder exists and print the path to the self-contained sketch page, "
            "then exit. Safe to call unattended — the default mode blocks until "
            "Ctrl-C and is for interactive use only."
        ),
    )
    sketch_parser.set_defaults(func=sketch.run)

    # --- partwright install-skill --------------------------------------------
    skill_parser = subparsers.add_parser(
        "install-skill",
        help="install the design-part orchestrator skill for Claude Code",
        description=(
            "Install the 'design-part' skill so one Claude Code session can "
            "orchestrate the whole Partwright flow (interview, brief + plan, "
            "scaffold, build) from a single conversation via /design-part. "
            "Installs at user scope by default, or into a directory's "
            ".claude/skills/ with --dest."
        ),
    )
    skill_scope = skill_parser.add_mutually_exclusive_group()
    skill_scope.add_argument(
        "--user",
        dest="dest",
        action="store_const",
        const=None,
        default=None,
        help="install at user scope, ~/.claude/skills/ (the default)",
    )
    skill_scope.add_argument(
        "--dest",
        metavar="DIR",
        nargs="?",
        const=".",
        help=(
            "install into DIR/.claude/skills/ instead of user scope, so a parent "
            "project folder carries the skill without global context bloat "
            "(default DIR: current directory)"
        ),
    )
    skill_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing installation of the skill",
    )
    skill_parser.set_defaults(func=skill.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse `argv` and dispatch to the selected subcommand's `run(args)`.

    Returns the subcommand's integer exit code (a `None` return is treated as
    success). Intended as the `partwright` console-script entry point.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # `func` is set via set_defaults on every subparser; with a required
    # subcommand it is always present once parsing succeeds.
    result = args.func(args)
    return 0 if result is None else int(result)


if __name__ == "__main__":
    sys.exit(main())
