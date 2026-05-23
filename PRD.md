# Partwright — Product Requirements Document

_Status: draft for review — 2026-05-23_

## 1. Summary

Partwright is a personal toolkit that wraps the recurring workflow for designing
3D-printable parts with [`build123d`](https://build123d.readthedocs.io/). Today,
every new part begins with the same overhead: re-creating the project skeleton,
re-explaining the design to an agent in prose, and re-establishing the
build-and-verify loop. Partwright removes that repeated setup.

Partwright is a **generator**. It produces standalone part repositories and the
planning artifacts that feed them, and it adds a lightweight visual sketching
tool so designs can be communicated with drawings rather than words alone. It is
deliberately **not** a runtime dependency of the parts it produces — each
generated repo is fully self-contained (the `phone-centipede` model), so a
finished part keeps working untouched as Partwright itself evolves.

Three deliverables make up the suite:

1. **New-project scaffolder** — stamps a fresh, standalone `build123d` part repo.
2. **Design-brief & plan generator** — Markdown templates plus a reusable
   interview prompt that turn a step-1 design chat into a structured handoff.
3. **SVG "click-to-draw" sketch tool** — a polygon-lasso sketcher for producing
   quick reference drawings, shipped as an MVP with a clear staged roadmap.

## 2. Background — the current workflow

The existing process has three steps:

1. **Describe & plan.** A chat with Claude to describe the design and produce a
   plan for a build agent.
2. **Build.** That plan is handed to a fresh Claude project, which builds the
   print pipeline (the `build123d` script that emits STLs).
3. **Iterate.** Slice in Bambu Studio, find problems, refine.

Two friction points motivate Partwright:

- **Re-doing infrastructure.** Step 2 always begins from nothing — the same
  `generate.py` skeleton, `CLAUDE.md`, `requirements.txt`, `.gitignore`, `uv`
  environment setup, and verification conventions are rebuilt each time.
- **Describing the design is hard.** Step 1 is the genuinely difficult part:
  pinning down *exactly* what the part is, how it is dimensioned, how it mates
  with other things, and which constraints come from FDM printing. Prose alone
  is a lossy medium for geometry.

### 2.1 The reference exemplar — `phone-centipede`

`~/phone-centipede` is the canonical example of a "good" generated repo and the
gold standard the scaffolder should reproduce. Its notable properties:

- A **single-file Python CLI** (`generate.py`) using `build123d`, with all
  geometry constants named at the top of the file and a deliberate subset
  exposed through `argparse`.
- A module docstring that states the **coordinate-system convention** explicitly
  (right-handed; +X / +Y / +Z each given a physical meaning).
- A `CLAUDE.md` that encodes hard-won lessons: the coordinate system, a
  Python-environment caveat, code-style rules, **boolean-robustness conventions**
  (face-overlap tabs so OCCT never resolves coincident faces), and a
  **"non-obvious geometry decisions"** section recording fixes that deviate from
  a literal reading of the spec.
- An optional reference-data module (`phones.py`) for known input dimensions.
- A `uv`-managed virtual environment, `black` as the formatting source of truth,
  and verification by re-slicing in Bambu Studio plus bounding-box sanity checks.

Partwright's scaffolder exists to reproduce this structure on demand; its brief
generator exists to capture the kind of design knowledge that ends up in that
`CLAUDE.md`.

## 3. Goals and non-goals

### Goals

- Eliminate repeated project setup — a new part repo is one command away.
- Make design intent easy to communicate, via reference sketches and a
  structured interview that surfaces the non-obvious constraints.
- Keep every generated repo self-contained and consistent with the
  `phone-centipede` model.
- Be incrementally extensible, especially the sketch tool, which ships as an MVP
  and grows in well-defined stages with a test checkpoint between each.
- Minimize runtime dependencies and stay robust against local Python-environment
  fragility (see §4).

### Non-goals

- **Not a CAD program.** The sketch tool produces *reference* drawings to aid
  communication, not finished manufacturing geometry.
- **Not a shared library.** Generated parts do not import a common Partwright
  runtime; the suite is a pure generator.
- **Not a slicer or print manager.** Bambu Studio remains the slicing and
  physical-verification tool.
- **Not an interactive form.** Design capture is a conversation, not a fixed
  questionnaire (see §6.2).

## 4. Users and context

Partwright has a single user: Matthew, a maker who designs parametric STL parts.
The working context that shapes the requirements:

- **Toolchain:** `build123d` 0.9.1, `uv` for environments, `black` for
  formatting, Bambu Studio for slicing, macOS.
- **Process:** Claude assists across a step-1 design chat and a separate step-2
  build project; sketches and briefs are the artifacts that move between them.
- **Environment fragility:** the local Homebrew Python installs have a broken
  `pyexpat`, which is why `uv` is used for environments. Partwright should favor
  **standard-library-only** code paths so the toolkit itself never reintroduces
  that class of breakage.

## 5. End-to-end workflow with Partwright

A new part idea flows through Partwright like this:

1. **Sketch.** `partwright sketch` opens the drawing tool. Matthew draws
   reference outlines — the part shape, how pieces fit together — and saves them
   as SVGs into an idea workspace.
2. **Interview & brief.** `partwright brief <idea>` creates an idea workspace
   pre-loaded with blank templates and the interview prompt. In a step-1 Claude
   chat, Matthew points Claude at the interview prompt and attaches the
   sketches; Claude interviews him and fills in `DESIGN_BRIEF.md` (the *what*)
   and `BUILD_PLAN.md` (the *how* — the handoff for the build agent).
3. **Scaffold.** `partwright new <name> --brief <path>` stamps a fresh,
   standalone part repo, seeded from the brief, with `BUILD_PLAN.md` and
   `DESIGN_BRIEF.md` copied in so the repo carries its own plan.
4. **Build.** Matthew opens the new repo as a fresh Claude project. Its
   `CLAUDE.md` points the agent at `BUILD_PLAN.md`, and the agent implements
   `generate.py`.
5. **Iterate.** Slice in Bambu Studio, refine, and record any non-obvious fixes
   in the repo's `CLAUDE.md`.

Partwright owns steps 1–3. Steps 4–5 are unchanged, but they start from a
consistent, well-documented foundation every time.

## 6. Components

### 6.1 New-project scaffolder — `partwright new`

**Purpose.** Generate a standalone `build123d` part repository that matches the
`phone-centipede` structure, so step-2 builds never start from an empty folder.

**Command.**

```
partwright new <project-name> [--dest DIR] [--brief FILE] [--no-git]
```

- `<project-name>` — name of the new repo / directory.
- `--dest DIR` — where to create it (default: current directory). Generated
  repos live wherever Matthew points; Partwright keeps no link to them afterward.
- `--brief FILE` — optional path to a `DESIGN_BRIEF.md`. When supplied, the
  scaffolder reads the brief's structured fields (see §6.2) to pre-populate the
  new repo's constants, CLI flags, coordinate-system notes, and `CLAUDE.md`, and
  copies `DESIGN_BRIEF.md` and (if present) its sibling `BUILD_PLAN.md` into the
  new repo so the part carries its own design record and build handoff.
- `--no-git` — skip the `git init` that the scaffolder otherwise runs on the new
  repo.

**Generated contents.**

| File | Purpose |
| --- | --- |
| `generate.py` | Skeleton single-file CLI: shebang, module docstring with the coordinate-system convention, constants block, geometry-helpers section, assembly section, `argparse` CLI, `main()`. Builds a 10 mm × 10 mm × 10 mm cube — sized by a named constant and exposed via a `--size` flag — so it runs out of the box and demonstrates the constants-plus-argparse pattern. |
| `CLAUDE.md` | Templated guidance: "What this is", coordinate system, Python-env caveat, code style (`black`), boolean-robustness conventions, and an empty "non-obvious geometry decisions" section to grow over time. When a brief is supplied, also carries a pointer line directing any build agent to `BUILD_PLAN.md`. |
| `README.md` | Prerequisites (`uv`), environment setup, usage, development. |
| `requirements.txt` | `build123d` pinned (0.9.1). |
| `requirements-dev.txt` | `-r requirements.txt` plus pinned `black`. |
| `.gitignore` | `.venv/`, `__pycache__/`, `*.pyc`, `*.stl`. |
| `.claude/settings.local.json` | Permission allowlist for running the project's venv Python, adapted from the `phone-centipede` exemplar's file. |
| `BUILD_PLAN.md` | _(only with `--brief`)_ Copied from the idea workspace — the implementation handoff the step-2 build agent works from. |
| `DESIGN_BRIEF.md` | _(only with `--brief`)_ Copied from the idea workspace — the design record (the *what*) kept with the repo for reference. |

**Requirements.**

- The skeleton `generate.py` must run immediately after `uv` env setup and
  produce a valid STL — a 10 mm cube — so the repo is verifiably alive before
  any design work.
- Templates use simple placeholder substitution (standard library only — e.g.
  `string.Template`); no third-party templating dependency.
- The scaffolder runs `git init` on the new repo by default; `--no-git` skips it.
- With `--brief`, the scaffolded repo is self-contained: it carries its own
  `BUILD_PLAN.md` and `DESIGN_BRIEF.md`, and its `CLAUDE.md` points any build
  agent at the plan — so the step-2 build needs no manual file handoff.
- Without `--brief`, the scaffolder produces a generic but complete skeleton.

### 6.2 Design-brief & plan generator — templates + `partwright brief`

**Purpose.** Turn the open-ended step-1 design conversation into two structured
artifacts, and make that conversation thorough by guiding it with a reusable
interview prompt.

**Why templates + a prompt, not a form.** The hard part of step 1 is describing
the design precisely — an adaptive, back-and-forth conversation that surfaces
non-obvious constraints (coordinate conventions, print-orientation gotchas, what
mates with what). A fixed questionnaire captures the easy fields and misses
exactly the parts that matter. The interview is therefore a *prompt that drives
a conversation*, and the templates are the contract its output is written into.

**Deliverables (Markdown, in Partwright's `templates/brief/`).**

- `DESIGN_INTERVIEW.md` — the reusable interview prompt / checklist. It directs
  Claude to interview Matthew across: part purpose and context; what it mates
  with or assembles into; overall form; key dimensions and which are parametric
  versus fixed; named size presets (known-model lookups), if any; units;
  coordinate-system convention; tolerances and fits; FDM
  print constraints (build-plate orientation, overhangs, bridging, supports);
  material; verification approach; multi-component artifacts; and any reference
  sketches provided.
- `DESIGN_BRIEF.md` (template) — the *what*. TOML frontmatter (the
  machine-readable contract the scaffolder consumes) over a Markdown body (prose
  the build agent reads). The schema is specified below.
- `SCHEMA.md` — a short written spec of the `DESIGN_BRIEF.md` frontmatter, so the
  template, the scaffolder, and the brief generator are all built against one
  documented contract.
- `BUILD_PLAN.md` (template) — the *how*. The handoff the step-2 build agent
  works from: implementation steps, geometry approach, the constants to define,
  the CLI surface, file layout, verification steps, and known risks. It is
  designed to produce a `generate.py` of `phone-centipede`'s quality.

**Command.**

```
partwright brief <idea-name> [--dest DIR]
```

Creates an idea workspace folder containing copies of the blank templates and
the interview prompt, plus a `sketches/` subfolder for SVGs. This is a
convenience helper — it copies files, it does **not** run an interactive
questionnaire.

**The `DESIGN_BRIEF.md` schema.** The file is a TOML frontmatter block (fenced
with `+++`) over a Markdown body. The frontmatter is the contract the scaffolder
reads; it is parsed with Python's standard-library `tomllib`, so it adds no
dependency. The schema is specified once here; `templates/brief/SCHEMA.md`
restates it for the build agents, and the template and scaffolder are built
against it.

```toml
+++
project_name = "phone-centipede"          # repo / directory name, identifier-safe
summary      = "A sectioned, dovetail-mating desk phone holder."
units        = "mm"                       # mm | inches — default unit for lengths
components   = ["segment", "nameplate"]   # artifacts the part can build; optional

[coordinate_system]
x = "segment length, along the desk's front edge"
y = "depth, away from the user"
z = "vertical, up off the desk"

[[parameters]]                            # one [[parameters]] block per knob
name    = "segment_length"
meaning = "slab length along X"
default = 101.6                           # in `units` unless `unit` overrides
cli     = false                           # expose as a CLI flag?

[[parameters]]
name    = "slot_angle"
meaning = "slot tilt off vertical, toward +Y"
default = 10.0
unit    = "deg"                           # per-parameter override; omit for lengths
cli     = true
+++
```

How the scaffolder consumes each field:

- `project_name` (**required**) — the new repo's directory name and the
  `generate.py` default STL output name.
- `summary` (optional) — the one-line description placed in the generated
  `CLAUDE.md` ("What this is") and `README.md`.
- `units` (optional, default `mm`) — the unit for every length parameter and the
  unit suffix on generated constants.
- `coordinate_system` (optional) — the per-axis lines reproduced in the
  `generate.py` module docstring and `CLAUDE.md`.
- `parameters` (**required**, one or more) — each becomes a named constant and,
  when `cli = true`, an `argparse` flag. The scaffolder derives the constant name
  and flag from `name` and `unit` (e.g. `slot_angle` + `deg` → constant
  `SLOT_ANGLE_DEG`, flag `--slot-angle`); `meaning` becomes the constant's
  comment and the flag's help text.
- `components` (optional) — a list with more than one entry adds a `--component`
  choice flag; omit it, or give a single entry, for a one-artifact part.

A brief whose TOML fails to parse, or that is missing a required field, is
rejected with a clear error naming the problem — the scaffolder never guesses.

The Markdown body below the frontmatter has eight sections: context & assembly,
tolerances & fits, print constraints, named size presets, verification approach,
reference sketches, out of scope / non-goals, and open questions. Deeper
per-parameter rationale lives in this prose, not in the one-line `meaning` field.

**Later upgrade.** The same interview prompt and templates can be wrapped as a
Cowork skill so the interview triggers naturally in chat. The skill would
package the identical Markdown artifacts — making this a cheap, non-throwaway
upgrade rather than a rewrite.

### 6.3 SVG sketch tool — `partwright sketch`

**Purpose.** A "click-to-draw" sketcher — the polygon-lasso interaction familiar
from Photoshop — for producing quick reference drawings that clarify design
intent to the step-1 agent.

**How it runs.** A single self-contained `sketch.html` (HTML, CSS, JS inline; no
build step) is the drawing canvas. `partwright sketch` starts a tiny local server
(standard-library `http.server`) that serves the page, auto-opens the browser,
and exposes save/load/list endpoints so drawings land directly in the chosen
folder and can be reopened for editing. The **same HTML file also works
double-clicked** (`file://`): when no server is detected, export falls back to a
browser download. The drawing app is written once; the server is an optional
convenience layer over it.

**Command.**

```
partwright sketch [--dest DIR]
```

`--dest` sets the folder drawings save into (default: current directory, or an
idea workspace's `sketches/` folder).

**Dual mode.**

- **Quick mode (default).** Freehand sketching with no scale calibration — for
  getting a rough idea down fast.
- **Precise mode.** A scale is set (by declaring a pixel-to-mm ratio or by
  drawing a calibration segment and assigning it a real length). Vertex
  coordinates are then known in millimeters, and the exported SVG carries
  real-world units and metadata, leaving the door open to importing the outline
  into `build123d` (`import_svg`) as actual geometry later.

**Export format.** Clean SVG (`<polygon>` / `<path>`) with a metadata block
recording mode, scale, and units, so drawings round-trip back into the editor
and remain interpretable downstream.

The MVP scope and the upgrade path are defined in §7.

## 7. SVG sketch tool — staged roadmap

The tool ships as a minimal MVP and grows in numbered stages. Each stage is
built by a separate agent, and there is a test checkpoint between stages so
functionality is validated before the next is added.

- **Stage 1 — MVP: polygon lasso.** Click to place vertices; close the shape by
  clicking the first vertex or pressing Enter; Esc cancels. Vertex editing
  (drag, delete), undo/redo, an optional snap grid, pan/zoom, dual quick/precise
  mode, save/load via the server with a double-click download fallback.
- **Stage 2 — basic shapes.** Rectangles, circles/ellipses, and straight lines
  as discrete primitives, with selection, delete, and z-order, alongside the
  lasso.
- **Stage 3 — dimensions.** Measurement annotations: dimension lines and labels
  along edges or between points, plus free text notes. In precise mode the
  labels report real millimeters.
- **Stage 4 — multi-view.** Multiple labeled panels (e.g. top / front / side
  orthographic views) on one canvas, each with its own coordinate frame,
  exported as a single grouped, labeled SVG.
- **Stage 5 — reference-image tracing (later enhancement).** Load a photo or
  screenshot as a backdrop and trace it with the lasso. The backdrop is for
  tracing only and is not embedded in the exported SVG.

## 8. Architecture and key decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Relationship to generated parts | Pure generator; no shared runtime | Parts stay self-contained and never break when Partwright changes. |
| Sketch tool runtime | CLI-served local server, with the same HTML usable standalone | Clean save/load into idea folders for iteration, with a zero-dependency fallback. |
| Brief generator form | Markdown templates + interview prompt | A design conversation cannot be flattened into a form; templates are the scaffolder contract regardless. |
| Implementation language | Python, `uv`-managed, standard library only where possible | Matches the toolchain; avoids reintroducing local Python-environment fragility. |
| Templating | `string.Template` / plain substitution | No third-party dependency for the scaffolder. |
| Python version | 3.12, for Partwright and every generated repo | One target prevents agents pinning different versions; `uv` provides 3.12 regardless of the local installs. |
| Brief frontmatter | TOML, parsed with the standard-library `tomllib` | Structured, nested config the scaffolder reads; `tomllib` ships in Python 3.12, so the zero-dependency rule holds. |

**Partwright repository layout.**

```
partwright/
  PRD.md                      # this document
  ROADMAP.md                  # phased build plan
  README.md
  pyproject.toml              # `partwright` CLI entry point; Python 3.12, no runtime deps
  partwright/
    __init__.py
    cli.py                    # argument dispatch to subcommands
    scaffold.py               # `partwright new`
    brief.py                  # `partwright brief`
    sketch.py                 # `partwright sketch` (local server)
  templates/
    project/                  # scaffolder templates (generate.py, CLAUDE.md, ...)
    brief/                    # DESIGN_INTERVIEW.md, DESIGN_BRIEF.md, BUILD_PLAN.md, SCHEMA.md
  web/
    sketch.html               # self-contained SVG drawing tool
  examples/
    lidded-box/               # worked example: filled DESIGN_BRIEF.md + BUILD_PLAN.md
  requirements-dev.txt        # black, for developing Partwright itself
  .gitignore
```

Each subcommand module (`scaffold.py`, `brief.py`, `sketch.py`) exposes a single
`run(args)` entry point. `cli.py` owns all argument parsing — the full set of
subcommands and flags — and dispatches the parsed arguments to the right
module's `run`.

**CLI surface.**

- `partwright new <name> [--dest] [--brief] [--no-git]` — scaffold a standalone
  part repo.
- `partwright brief <name> [--dest]` — create an idea workspace with blank
  templates and the interview prompt.
- `partwright sketch [--dest]` — launch the SVG sketch tool.

## 9. Success criteria

- `partwright new` produces a repo whose skeleton `generate.py` runs after `uv`
  setup and emits a valid STL — a 10 mm cube — with no edits.
- A repo scaffolded with `--brief` reflects the brief's parameters and
  coordinate-system notes in `generate.py` and `CLAUDE.md`.
- The interview prompt, run against a known part, can produce a brief detailed
  enough that a build agent could rebuild something of `phone-centipede`'s
  quality from it.
- `partwright sketch` launches, draws a closed polygon, saves an SVG into the
  target folder, and reopens it for editing; the same HTML file works
  double-clicked with download export.
- Partwright has no third-party runtime dependencies.

## 10. Deferred and dropped scope decisions

The open questions from earlier drafts were resolved on 2026-05-23. None of them
gate the initial build; Phases 0–3 of `ROADMAP.md` are the full first scope.

**Deferred — revisit after the initial build.**

- _Cowork skill for the design interview._ The templates-plus-prompt MVP must
  exist and be validated first, and a skill would package the identical Markdown
  files — so nothing is lost by waiting. Revisit once a few real interviews show
  whether the manual "point Claude at the prompt" step is worth eliminating.
- _Precise-mode `import_svg` validation._ Precise mode already records correct
  millimeter scale and units in the exported SVG, which keeps the geometry-import
  door open at no cost. Verifying a clean `build123d` import is premature until a
  concrete part needs a sketch imported as geometry; revisit then.

**Dropped — not in scope.**

- _Scaffolder-generated reference-data module._ A known-model lookup table (the
  `phones.py` pattern) is part-specific content, not skeleton structure, and
  belongs to the step-2 build agent working from `BUILD_PLAN.md`. Instead, the
  interview prompt asks whether the part has named size presets so the brief
  captures them in prose; the scaffolder stays generic.
- _Idea-workspace registry command._ A `partwright` command to register and
  reopen idea workspaces would introduce persistent state — tracking where
  workspaces live and coping with moved or renamed folders — to solve a clutter
  problem that does not yet exist. The filesystem is sufficient; revisit only if
  in-flight ideas become genuinely hard to track.
