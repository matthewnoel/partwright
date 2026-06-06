# Partwright

A personal toolkit for designing 3D-printable parts with
[`build123d`](https://build123d.readthedocs.io/). Partwright is a **generator**:
it stamps standalone part repositories, turns design conversations into
structured handoff documents, and provides a lightweight SVG sketch tool for
communicating design intent with drawings.

Partwright is **not** a runtime dependency of the parts it produces. Every
repository it generates is fully self-contained, so a finished part keeps
working untouched as Partwright itself evolves.

## What it does

Three subcommands, one per stage of the design workflow:

- `partwright sketch` — launch a click-to-draw SVG sketch tool for quick
  reference drawings.
- `partwright brief` — create an idea workspace pre-loaded with the design
  templates and the interview prompt.
- `partwright new` — scaffold a fresh, standalone `build123d` part repository,
  optionally seeded from a filled design brief.

## Recommended working model

The commands chain into one low-friction loop; each stage hands a concrete
artifact to the next:

```
partwright sketch    →  draw design intent            →  reference SVGs
partwright brief     →  interview in a Claude chat     →  DESIGN_BRIEF.md + BUILD_PLAN.md
partwright new       →  scaffold the repo (sketches copied into reference/)
open in Claude Code  →  implement build_part → generate.py → preview.py
                        → read preview.png → show you → iterate   (the visual loop)
Bambu Studio         →  slice & physically verify
```

The thing that makes this low-friction is the **visual loop**: the generated repo
renders a multi-view `preview.png` of its own geometry, so Claude verifies the
shape visually — and shows it to you — before you ever open a slicer. Reference
drawings in `reference/` and the structured brief keep design intent flowing
through every stage, so the part is rarely described in prose alone.

## Requirements

- Python 3.12 (Partwright uses the standard-library `tomllib`, which needs
  Python 3.11+; 3.12 is the supported target).
- [`uv`](https://docs.astral.sh/uv/) — recommended for managing the Python
  environment. The local Homebrew Python installs on this machine have a broken
  `pyexpat`, so `uv` is used to provide a reliable 3.12 interpreter.

Partwright has **zero third-party runtime dependencies** — everything it needs
ships with the Python standard library.

## Install

Using `uv`:

```sh
uv venv .venv --python 3.12
uv pip install -e .
source .venv/bin/activate
```

This installs the `partwright` console entry point and activates the
environment, so the `partwright` command is on your `PATH`. In a new shell,
re-activate with `source .venv/bin/activate` — or skip activation entirely and
prefix commands with `uv run` (e.g. `uv run partwright sketch`).

You can also run Partwright without installing it, straight from a clone:

```sh
python -m partwright --help
```

(`python` here must be a 3.12 interpreter — e.g. `uv run --python 3.12 python -m partwright --help`.)

## Usage

```sh
# Sketch reference drawings into a folder
partwright sketch --dest ./my-idea/sketches

# Create an idea workspace with blank templates and the interview prompt
partwright brief my-idea --dest ./ideas

# Scaffold a standalone part repo, seeded from a filled brief
partwright new my-part --brief ./ideas/my-idea/DESIGN_BRIEF.md --dest ./repos
```

Run `partwright --help` or `partwright <command> --help` for the full flag set.

### `partwright new`

```
partwright new <project-name> [--dest DIR] [--brief FILE] [--no-git]
```

Scaffolds a standalone `build123d` part repository matching the
`phone-centipede` structure. `--brief` pre-populates the repo's constants, CLI
flags, and coordinate-system notes from a `DESIGN_BRIEF.md`; `--no-git` skips
the `git init` the scaffolder otherwise runs.

### `partwright brief`

```
partwright brief <idea-name> [--dest DIR]
```

Creates an idea-workspace folder with copies of the blank `DESIGN_BRIEF.md` and
`BUILD_PLAN.md` templates, the `DESIGN_INTERVIEW.md` prompt, and a `sketches/`
subfolder.

### `partwright sketch`

```
partwright sketch [--dest DIR]
```

Serves the self-contained SVG sketch tool from a tiny local server and opens it
in the browser. Drawings save into `--dest`. The same HTML file also works
opened directly via `file://`, falling back to a browser download.

## Development

Partwright targets Python 3.12 and is formatted with
[`black`](https://black.readthedocs.io/) — the formatting source of truth.

```sh
uv pip install -r requirements-dev.txt
black partwright/
black --check partwright/
```

## Repository layout

```
partwright/
  PRD.md                  # product requirements
  ROADMAP.md              # phased build plan
  README.md               # this file
  pyproject.toml          # package metadata; `partwright` entry point, no runtime deps
  partwright/              # the CLI package (standard library only)
    cli.py                # complete CLI + dispatch to subcommand run(args)
    scaffold.py           # `partwright new`
    brief.py              # `partwright brief`
    sketch.py             # `partwright sketch`
  templates/
    project/              # scaffolder templates
    brief/                # design-brief templates + SCHEMA.md
  web/
    sketch.html           # self-contained SVG sketch tool
  examples/
    lidded-box/           # worked example: filled DESIGN_BRIEF.md + BUILD_PLAN.md
  requirements-dev.txt    # black, for developing Partwright itself
```
