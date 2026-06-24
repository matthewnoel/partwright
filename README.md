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

Install the `design-part` skill once (`partwright install-skill`) and you drive
the whole thing from **one** Claude Code conversation — no pasting prompts into a
second chat, no hand-copying files between sessions:

```
/design-part  in Claude Code
   ├─ partwright sketch   →  draw design intent (optional)      →  reference SVGs
   ├─ partwright brief    →  interview you, in this session     →  DESIGN_BRIEF.md + BUILD_PLAN.md
   ├─ partwright new      →  scaffold the repo (sketches → reference/)
   └─ claude (headless)   →  build agent works from BUILD_PLAN.md
                             → generate.py → preview.py → preview.png → iterate
Bambu Studio              →  slice & physically verify
```

One Claude orchestrates: it interviews you live, writes the brief and plan only
once you say go, scaffolds the repo, then spawns a separate headless `claude` to
build the part from the plan. The `partwright` subcommands below are the tools it
drives — you can also run them by hand.

The thing that makes this low-friction is the **visual loop**: the generated repo
renders a multi-view `preview.png` of its own geometry, so Claude verifies the
shape visually — and shows it to you — before you ever open a slicer. Reference
drawings in `reference/` and the structured brief keep design intent flowing
through every stage, so the part is rarely described in prose alone.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) — the only thing you need to install.
  It provides the Python 3.12 interpreter Partwright runs on (the standard
  library `tomllib` needs 3.11+), so you never manage a virtualenv by hand.

Partwright has **zero third-party runtime dependencies** — everything it needs
ships with the Python standard library, bundled into the package.

## Install

Install it once as a global CLI with `uv tool` — no virtualenv, no activation, no
clone to keep around:

```sh
uv tool install git+https://github.com/matthewnoel/partwright
```

That puts a `partwright` command on your `PATH`. Then install the orchestrator
skill so one Claude Code session can run the whole flow:

```sh
partwright install-skill
```

`install-skill` drops the `design-part` skill into `~/.claude/skills/`; use
`partwright install-skill --dest <dir>` instead to scope it to a single project
folder (`<dir>/.claude/skills/`) rather than your global config.

To run a one-off without installing, use `uvx`:

```sh
uvx --from git+https://github.com/matthewnoel/partwright partwright sketch
```

(Once Partwright is published to PyPI, `uv tool install partwright` and
`uvx partwright` will work by bare name.)

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

### `partwright install-skill`

```
partwright install-skill [--user | --dest DIR] [--force]
```

Installs the `design-part` Claude Code skill — the orchestrator that runs the
whole flow from one session (see *Recommended working model*). `--user` (the
default) installs to `~/.claude/skills/`; `--dest DIR` installs to
`DIR/.claude/skills/` so a parent project folder carries the skill without
adding it to your global config. `--force` overwrites an existing copy. After
installing, start a design with `/design-part` in Claude Code.

## Development

Partwright targets Python 3.12 and is formatted with
[`black`](https://black.readthedocs.io/) — the formatting source of truth. Run it
straight from a clone with `uv run`:

```sh
uv run --python 3.12 python -m partwright --help   # run without installing
uv run --with black black partwright/
uv run --with black black --check partwright/
```

## Repository layout

```
partwright/
  README.md               # this file
  pyproject.toml          # package metadata; `partwright` entry point, no runtime deps
  partwright/              # the CLI package (standard library only)
    cli.py                # complete CLI + dispatch to subcommand run(args)
    scaffold.py           # `partwright new`
    brief.py              # `partwright brief`
    sketch.py             # `partwright sketch`
    skill.py              # `partwright install-skill`
    templates/
      project/            # scaffolder templates
      brief/              # design-brief templates + SCHEMA.md
    web/
      sketch.html         # self-contained SVG sketch tool
    skills/
      design-part/        # the orchestrator skill (SKILL.md)
  examples/
    lidded-box/           # worked example: filled DESIGN_BRIEF.md + BUILD_PLAN.md
  requirements-dev.txt    # black, for developing Partwright itself
```
