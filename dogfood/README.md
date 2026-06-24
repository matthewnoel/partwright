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

# 4. Turn that feedback into ready-to-file GitHub issue payloads (issues.json).
python dogfood/run.py --emit-issues
```

Every run writes a machine-readable `dogfood/work/report.json` and prints a
summary. The driver exits non-zero if any part failed to scaffold or build, so an
orchestrator or CI step can gate on it.

`--emit-issues` writes `dogfood/work/issues.json` — one issue payload (title,
labels, body) per feedback file, with a `severity:<level>` label parsed from the
feedback and a `looks_unfilled` flag on copies that are still the blank template.
The driver stays offline and credential-free: it emits payloads, and the
orchestrator files the fileable ones via its own GitHub tooling. That's the seam
that gives improvement tracking a real lifecycle (feedback → tracked issue)
instead of a JSON snapshot.

## The orchestration loop

This is the model to fan out across an agent team. Each agent owns **one** part:

1. **Scaffold** — `python dogfood/run.py` (or scaffold one brief directly) gives
   the agent a standalone repo in `dogfood/work/<name>/`.
2. **Build** — the agent works the repo's own `CLAUDE.md` loop: implement
   `build_part` in `generate.py`, run `generate.py` then `preview.py`, **read
   `preview.png`**, and iterate until the geometry matches `BUILD_PLAN.md`. The
   agent does this work *itself* with the repo as its working directory — it does
   not need to shell out to a nested `claude -p`. (The skill's Stage 5 is now
   orchestrator-agnostic about how the build agent is spawned; a subagent/Task
   driving the repo directly satisfies the same contract.)
3. **Report** — the agent copies `FEEDBACK_TEMPLATE.md` into the repo as
   `DOGFOOD_FEEDBACK.md` and fills it in *about the tool*, not the part.
4. **Collect & track** — the orchestrator runs `python dogfood/run.py
   --emit-issues`, reviews the aggregated feedback in `report.json`, and files
   the fileable findings as GitHub issues so each improvement is tracked to
   closure. `issues.json` is a *starting point*, not the final cut — see
   "Filing issues from a pass" below.

## The build-agent prompt

Each per-part build agent gets the same two-part brief. Give it the repo path
and tell it explicitly that the job has two halves — building and *reporting on
the tool*, not just building — or it will skip the feedback:

> You are a Partwright build agent dogfooding the tool. You own ONE part: the
> repo scaffolded at `dogfood/work/<name>/`. Work only in that directory.
>
> **Build:** Read `CLAUDE.md`, `DESIGN_BRIEF.md` (and `BUILD_PLAN.md` if
> present), and `reference/`. Replace the placeholder `build_part` in
> `generate.py` with the real geometry (keep it callable with no args). Run
> `generate.py`, then `preview.py`, then **read `preview.png`** and iterate
> until the geometry matches the brief. Run `generate.py --check` to confirm a
> single watertight solid, and `black` after edits.
>
> **Report:** Copy `dogfood/FEEDBACK_TEMPLATE.md` into the repo as
> `DOGFOOD_FEEDBACK.md` and fill in every section honestly **about the tool**
> (friction, what the scaffold got right, what's missing, did the visual loop
> work) — not about the part. Pick one severity: blocker | major | minor | nit.

Vary the parts across agents so different corners of the tool get exercised.

## Filing issues from a pass

`--emit-issues` writes one payload *per feedback file*. That is raw material,
not the issue list to file verbatim. Before opening issues:

- **Dedup by distinct problem, not by part.** If two agents hit the same gap
  (e.g. the same missing dev dep), that is **one** issue citing both, not two.
  Conversely, one feedback file usually contains several distinct findings worth
  splitting into separate issues.
- **Verify each claim against the source before filing.** An agent's report can
  be wrong or imprecise. Confirm it in the code (e.g. open `scaffold.py` to
  check a "file isn't generated" claim) and cite the file/line in the issue, so
  the maintainer gets a located, reproduced problem — not a rumor.
- **Label consistently.** Keep the `dogfood` + `severity:<level>` labels the
  driver emits, and add `bug` vs `enhancement` by your own read of the finding.
- **Skip `looks_unfilled` payloads** — those are blank templates an agent never
  filled in.
- **Close the loop.** When a fix merges, close its issue with a pointer to the
  commit so the feedback → tracked → fixed → closed lifecycle is complete.

## Adding a fixture

Drop a `briefs/<name>/DESIGN_BRIEF.md` validated against
`partwright/templates/brief/SCHEMA.md` (the `+++` TOML frontmatter is the
machine-readable contract; the eight-section Markdown body is prose for the build
agent). The driver discovers it automatically. Vary complexity on purpose — a
trivial part and a hole-pattern part exercise different corners of the tool.

## Non-interactive gaps — addressed, and remaining

Closed so an orchestrated run no longer trips over them:

- **`partwright sketch` hanging** — fixed with `partwright sketch --no-serve`,
  which resolves the dest and the page path, prints them, and exits without
  serving or opening a browser. Safe to call unattended.
- **Build permission friction** — the scaffolded `settings.local.json` now
  allowlists `uv venv` and `uv pip install` alongside `.venv/bin/python` and
  `.venv/bin/black`, so an unattended build isn't blocked on the install step.
  (The agent's environment still needs `uv` + outbound network for build123d.)
- **Nested-`claude` coupling** — the skill's Stage 5 is now orchestrator-agnostic
  about how the build agent is spawned.

Still worth pressure-testing through dogfooding:

- **The interactive `/design-part` flow itself** — the interview writing gate and
  the live sketch step are inherently human-in-the-loop; this harness exercises
  the CLI and the scaffolded build loop, not that experience.
- **Geometry feedback is visual** (`preview.png`); `report.json` gives
  machine-readable scaffold/build pass/fail, but correctness of the *shape* still
  needs an agent (or human) reading the preview.
