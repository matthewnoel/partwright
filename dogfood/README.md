# Dogfooding harness

Tools for **orchestrated dogfooding**: pointing a team of agents at Partwright so
they build real parts with it and report back what the tool got wrong.

## Why this exists

The `design-part` skill is deliberately a *single human-gated conversation*. It
interviews the maker and refuses to write a brief until the maker explicitly says
"yes" (the writing gate in `SKILL.md`). That is correct for a real session, but
it means the normal flow **cannot run unattended** — an autonomous agent has no
maker to interview or to confirm the gate.

This harness takes the other path through the *same* tool. `partwright new
--brief <FILE>` scaffolds a standalone, ready-to-build repo straight from a
pre-authored brief, with no interview. That's the seam orchestrated dogfooding
runs through.

## Layout

```
dogfood/
  run.py                 # non-interactive driver (stdlib only)
  briefs/                # canned, schema-valid DESIGN_BRIEF.md fixtures
    desk-hook/           #   simple, single-component S-hook
    pi-mount/            #   single-component plate with a hole pattern + keyholes
  FEEDBACK_TEMPLATE.md   # what each agent fills in as DOGFOOD_FEEDBACK.md
  work/                  # generated; scaffolded repos + report.json (gitignored)
```

The `examples/lidded-box` brief in the repo root is a third, multi-component
fixture — copy it under `briefs/` (or point `--briefs-dir` at it) to include it.

## The driver

```sh
# 1. Scaffold every brief into dogfood/work/ — deterministic, no network.
python dogfood/run.py

# 2. Also prove each repo renders out of the box (needs uv + network for build123d).
python dogfood/run.py --build

# 3. After agents have built and left DOGFOOD_FEEDBACK.md files, aggregate them.
python dogfood/run.py --collect
```

Every run writes a machine-readable `dogfood/work/report.json` and prints a
summary. The driver exits non-zero if any part failed to scaffold or build, so an
orchestrator or CI step can gate on it.

## The orchestration loop

This is the model to fan out across an agent team. Each agent owns **one** part:

1. **Scaffold** — `python dogfood/run.py` (or scaffold one brief directly) gives
   the agent a standalone repo in `dogfood/work/<name>/`.
2. **Build** — the agent works the repo's own `CLAUDE.md` loop: implement
   `build_part` in `generate.py`, run `generate.py` then `preview.py`, **read
   `preview.png`**, and iterate until the geometry matches `BUILD_PLAN.md`. The
   agent does this work *itself* — do **not** shell out to a nested `claude -p`
   (the skill's Stage 5 does that for the interactive flow; it does not map to a
   subagent/Task orchestrator and needs a human to set the permission posture).
3. **Report** — the agent copies `FEEDBACK_TEMPLATE.md` into the repo as
   `DOGFOOD_FEEDBACK.md` and fills it in *about the tool*, not the part.
4. **Collect** — the orchestrator runs `python dogfood/run.py --collect` and
   reviews the aggregated feedback in `report.json`.

## Adding a fixture

Drop a `briefs/<name>/DESIGN_BRIEF.md` validated against
`partwright/templates/brief/SCHEMA.md` (the `+++` TOML frontmatter is the
machine-readable contract; the eight-section Markdown body is prose for the build
agent). The driver discovers it automatically. Vary complexity on purpose — a
trivial part and a hole-pattern part exercise different corners of the tool.

## Known non-interactive gaps (test targets, not yet fixed)

These are the interactive assumptions an orchestrated run still trips over. They
are what dogfooding is meant to surface and pressure-test:

- **`partwright sketch` blocks forever** (`serve_forever`, opens a browser) with
  no headless/`--no-serve` mode — an agent that runs it hangs.
- **The build agents need `uv` + outbound network** to install build123d/OCCT;
  the scaffolded `settings.local.json` only allowlists `.venv/bin/python` and
  `.venv/bin/black`, not the `uv` install step.
- **Feedback is visual-by-design** (`preview.png`) with no machine-readable
  pass/fail to aggregate across a fleet.
