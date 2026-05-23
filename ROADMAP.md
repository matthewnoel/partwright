# Partwright — Build Plan & Orchestration Roadmap

_Status: draft for review — 2026-05-23. Companion to `PRD.md`._

This document describes how Partwright will be built by orchestrating sub-agents.
It defines the phases, what each phase's agent delivers, how each phase is
verified, and the sequencing between them.

## Orchestration strategy

The build splits into a blocking foundation phase, a parallel core-build phase,
an integration check, then the staged sketch-tool upgrades.

```
Phase 0  Foundation                         (1 agent, blocking)
            |
   +--------+--------+
   |        |        |
Phase 1  Phase 2  Phase 3   Scaffolder / Brief generator / SVG MVP
   |        |        |      (3 agents, parallel — no shared files)
   +--------+--------+
            |
         Integration verification           (1 verifier agent)
            |
        [ test checkpoint — Matthew uses the suite ]
            |
Phase 4 -> 5 -> 6 -> 7   SVG Stages 2, 3, 4, 5
                         (1 agent each, sequential, test between)
```

**Why Phases 1–3 can run in parallel.** Phase 0 builds the *entire* CLI surface
in `cli.py` — every subcommand and every flag — and ships each subcommand module
(`scaffold.py`, `brief.py`, `sketch.py`) as a stub exposing one `run(args)`
function. It also freezes the `DESIGN_BRIEF.md` frontmatter schema. After Phase
0, each of Phases 1–3 implements only the body of its own module's `run` and adds
its own template or web assets; `cli.py`, `__init__.py`, and the other two
modules are never touched again. No two agents share a file, so the three phases
run concurrently and merge without conflict.

**Initial orchestration target: Phases 0–3 plus the integration-verification pass.** That delivers a
fully usable suite (scaffolder, brief generator, sketch-tool MVP). SVG Stages
2–5 are specified here but are built only after Matthew has tested the MVP, one
agent per stage, matching the staged-upgrade approach agreed for the tool.

## Phase 0 — Foundation

**Agent:** 1, sequential, blocks all others.

**Deliverables.**

- Partwright repo skeleton: `pyproject.toml` (Python 3.12, `partwright` console
  entry point, no runtime dependencies), `partwright/__init__.py` (empty),
  `README.md`, `.gitignore`, `requirements-dev.txt` (pinned `black`).
- `partwright/cli.py` — the **complete** CLI and the frozen dispatch contract:
  the top-level parser plus all three subcommands with every flag and help text
  (`new <name> [--dest] [--brief] [--no-git]`, `brief <name> [--dest]`,
  `sketch [--dest]`). It parses arguments and dispatches the resulting namespace
  to the owning module's `run(args)`. `cli.py` is frozen after this phase.
- `partwright/scaffold.py`, `partwright/brief.py`, `partwright/sketch.py` — each a
  stub exposing a single `run(args)` function that prints a "not yet implemented"
  notice. Phases 1–3 replace only the body of their own `run`.
- `templates/brief/SCHEMA.md` — the `DESIGN_BRIEF.md` frontmatter schema,
  transcribed from PRD §6.2 (the authoritative source). This is the contract
  Phases 1 and 2 build against.
- `examples/lidded-box/` — the test fixture for Phase 1 and the integration
  pass: a *filled* `DESIGN_BRIEF.md` for a friction-fit lidded box (conforming
  exactly to `SCHEMA.md`) and a matching `BUILD_PLAN.md`.
- Empty `templates/project/` and `web/` directories (Phases 1 and 3 populate
  them).

**Verification.** `partwright --help` and each `partwright <cmd> --help` run
cleanly and show the full flag set; each subcommand stub executes and reports
"not implemented"; the example brief in `examples/lidded-box/` parses as valid
TOML frontmatter and conforms to `SCHEMA.md`.

## Phase 1 — New-project scaffolder (`partwright new`)

**Agent:** 1, parallel with Phases 2 and 3. **Depends on:** Phase 0.

**Reference.** The agent must study `~/phone-centipede` closely — its
`generate.py`, `CLAUDE.md`, `README.md`, requirements files, `.gitignore`, and
`.claude/settings.local.json` are the gold standard the output must match.

**Deliverables.**

- `templates/project/` — the scaffolder templates: `generate.py` skeleton
  (module docstring with coordinate-system convention, named-constants block,
  geometry-helpers section, assembly section, `argparse` CLI, `main()`; builds a
  10 mm cube sized by a named constant and exposed via a `--size` flag, so it
  runs out of the box), `CLAUDE.md`,
  `README.md`, `requirements.txt` (`build123d==0.9.1`), `requirements-dev.txt`,
  `.gitignore`, and `.claude/settings.local.json` (adapted from the exemplar's file).
- `partwright/scaffold.py` — fills in the `run(args)` body for `partwright new`:
  placeholder substitution with `string.Template` (stdlib only); when `--brief`
  is given, parses the `DESIGN_BRIEF.md` TOML frontmatter with the stdlib
  `tomllib` module (per `SCHEMA.md`) and seeds
  constants, CLI flags, and coordinate-system notes, copies `DESIGN_BRIEF.md` and
  (if present) its sibling `BUILD_PLAN.md` into the new repo, and writes a
  pointer line *into* the generated `CLAUDE.md` directing a build agent *to*
  `BUILD_PLAN.md`. Runs `git init` on the new repo unless `--no-git` is passed.

**Verification.** Scaffold a throwaway project; create its `uv` venv (Python 3.12); install
`build123d`; run its `generate.py`; confirm a valid STL is produced and that its
bounding box is a 10 mm cube. If installing `build123d` in the sandbox is prohibitively
slow, fall back to: AST/structure validation of the generated `generate.py`, a
`black --check` pass, and confirmation all expected files exist. Also scaffold
once *with* the `examples/lidded-box/` brief and confirm the brief's fields
appear in the output, that `BUILD_PLAN.md` and `DESIGN_BRIEF.md` were copied into
the repo, and that `CLAUDE.md` contains the pointer line.

## Phase 2 — Design-brief & plan generator

**Agent:** 1, parallel with Phases 1 and 3. **Depends on:** Phase 0.

**Deliverables.**

- `templates/brief/DESIGN_INTERVIEW.md` — the reusable interview prompt
  covering, at minimum: part purpose and context; mating/assembly; overall form;
  key dimensions and parametric-vs-fixed; named size presets (known-model
  lookups), if any; units; coordinate-system convention;
  tolerances and fits; FDM print constraints (build-plate orientation,
  overhangs, bridging, supports); material; verification approach;
  multi-component artifacts; reference-sketch handling.
- `templates/brief/DESIGN_BRIEF.md` — the *what* template: TOML frontmatter
  conforming to `SCHEMA.md`, plus a Markdown body with the eight sections named
  in PRD §6.2 (context & assembly; tolerances & fits; print constraints; named
  size presets; verification approach; reference sketches; out of scope /
  non-goals; open questions).
- `templates/brief/BUILD_PLAN.md` — the *how* template: the build-agent handoff
  (implementation steps, geometry approach, constants, CLI surface, file layout,
  verification, known risks), structured to yield a `generate.py` of
  `phone-centipede` quality.
- `partwright/brief.py` — fills in the `run(args)` body for `partwright brief`:
  creates an idea workspace folder with copies of the blank templates
  (`DESIGN_BRIEF.md`, `BUILD_PLAN.md`), the interview prompt, and a `sketches/`
  subfolder.

**Verification.** Run `partwright brief test-idea`; confirm the workspace and all
files are created. Sanity-check the interview prompt by tracing it against
`phone-centipede`: an interview following the prompt should be capable of
eliciting that part's coordinate system, parameters, tolerances, and the
non-obvious print-orientation constraints. Confirm the `DESIGN_BRIEF.md`
template's frontmatter conforms to `SCHEMA.md` exactly.

## Phase 3 — SVG sketch tool MVP (Stage 1)

**Agent:** 1, parallel with Phases 1 and 2. **Depends on:** Phase 0.

**Deliverables.**

- `web/sketch.html` — one self-contained file (HTML + CSS + JS inline, no build
  step, no required CDN assets). Stage 1 features: polygon lasso (click to add
  vertices, close on first-vertex click or Enter, Esc to cancel); vertex editing
  (drag, delete); undo/redo; optional snap grid; pan/zoom; dual quick/precise
  mode (precise mode sets a px-to-mm scale via ratio entry or a calibration
  segment); SVG export with a metadata block (mode, scale, units); reopen an
  existing SVG to edit it.
- `partwright/sketch.py` — fills in the `run(args)` body for `partwright sketch`: a stdlib
  `http.server` that serves `sketch.html`, auto-opens the browser, and provides
  endpoints to save an SVG into `--dest`, list saved SVGs, and load one back.
- Standalone fallback: when `sketch.html` is opened via `file://` (no server),
  export falls back to a browser download; the page detects which mode it is in.

**Verification.** Launch `partwright sketch`; load the page; draw and close a
polygon; save it; confirm a valid SVG lands in `--dest`; reopen it and confirm
the geometry round-trips. Confirm precise mode records a correct mm scale in the
exported metadata. Confirm the file opened directly via `file://` still draws
and exports via download.

## Integration verification

**Agent:** 1 verifier (independent), after Phases 1–3 merge. This is a gate, not
a numbered phase — it runs between Phase 3 and the SVG stages.

**Checks.** All three subcommands work end-to-end from a single `partwright`
install; the PRD §5 workflow runs through cleanly (`brief` → `sketch` into the
idea workspace → `new --brief` consuming that brief and baking `BUILD_PLAN.md`
into the result); no file conflicts or regressions from the parallel merge; Partwright still has zero runtime
dependencies; `black --check` passes on `partwright/`.

**Output.** A short pass/fail report. Failures are routed back to the owning
phase's follow-up before the test checkpoint.

## Test checkpoint

Matthew uses the Phases 0–3 suite on a real idea. Feedback is gathered before
any SVG upgrade work begins.

## Phases 4–7 — SVG sketch tool Stages 2–5

Built one agent per stage, sequentially, with a test checkpoint between each.
Each stage extends `web/sketch.html` (and `sketch.py` only if save/load needs
it) without regressing earlier stages.

- **Phase 4 — Stage 2: basic shapes.** Rectangle, circle/ellipse, line
  primitives; selection, delete, z-order.
- **Phase 5 — Stage 3: dimensions.** Dimension lines and labels, free text
  notes; real-mm labels in precise mode.
- **Phase 6 — Stage 4: multi-view.** Multiple labeled orthographic panels, each
  with its own coordinate frame; single grouped SVG export.
- **Phase 7 — Stage 5: reference-image tracing.** Load a backdrop image to trace
  over; backdrop is tracing-only and excluded from the exported SVG.

## Verification principles (all phases)

- Every build agent verifies its own deliverable before reporting done.
- Each agent works against the live Partwright folder; the orchestrator confirms
  actual file changes rather than relying on the agent's summary.
- Standard library only for Partwright runtime code; `build123d` and `black`
  belong to *generated* repos, not to Partwright itself.
- The integration-verification pass provides an independent end-to-end check
  before the test checkpoint.
