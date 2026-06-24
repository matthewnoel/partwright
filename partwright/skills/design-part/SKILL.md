---
name: design-part
description: >-
  Orchestrate the whole Partwright flow for designing a 3D-printable build123d
  part from a single Claude Code session: interview the maker, write the design
  brief and build plan, scaffold the standalone part repo, then spawn the build
  agent. Use when the maker wants to design, model, or 3D-print a new part, or
  says things like "let's design a part", "I want to print a bracket/holder/jig",
  or invokes /design-part.
---

# Partwright orchestrator

You are the **single Claude Code the maker talks to** for an entire part-design
session. Everything below happens in *this* conversation — the maker should never
have to open a second chat or hand-copy files between sessions. You drive the
`partwright` CLI as your tool, and you spawn a separate headless build agent only
for the final, non-interactive build step.

Confirm `partwright` is installed first: run `partwright --version`. If it is
missing, tell the maker to `uv tool install` it (see the Partwright README) and
stop.

## The flow

Work through these stages in order. Do not race ahead — the interview is the part
that matters most, and it has a hard writing gate (stage 3).

### 1. Sketch (optional)

If the maker has a shape in mind that's easier drawn than described, offer to open
the sketch tool:

```
partwright sketch --dest <idea-workspace>/sketches
```

Skip this if they'd rather just talk. Reference drawings are an aid, not a
requirement.

### 2. Create the idea workspace

Pick a short, identifier-safe idea name with the maker, then:

```
partwright brief <idea-name> --dest <somewhere sensible>
```

This stamps a workspace containing `DESIGN_INTERVIEW.md`, blank `DESIGN_BRIEF.md`
and `BUILD_PLAN.md`, and a `sketches/` folder.

### 3. Run the interview — inline, in this session

**Read the workspace's `DESIGN_INTERVIEW.md` and run that interview yourself, in
this chat.** It is the single source of truth for how to interview and — this is
the important part — for **when you are allowed to write the brief and plan**.

Honor its **Writing gate** strictly. You are biased toward finishing early;
resist it. Do **not** write `DESIGN_BRIEF.md` or `BUILD_PLAN.md` until:

- every interview topic has an explicit answer or a recorded `N/A`;
- every dimension, derived formula, and the coordinate system has been reflected
  back and confirmed;
- open questions are enumerated and shown; and
- you have presented the coverage checklist and the maker has explicitly answered
  *yes* to "Ready for me to write the brief and plan?"

A new question, a fresh detail, "maybe", or silence is **not** a yes. Fold it in
and re-ask. When the gate is genuinely passed, write both files into the
workspace, validating the brief's frontmatter against `SCHEMA.md`.

### 4. Scaffold the part repo

Once the brief and plan exist:

```
partwright new <project-name> --brief <idea-workspace>/DESIGN_BRIEF.md --dest <repos-dir>
```

This stamps a standalone build123d repo, seeded from the brief, with
`BUILD_PLAN.md`, `DESIGN_BRIEF.md`, and the sketches copied in. The repo's
`CLAUDE.md` already points a build agent at `BUILD_PLAN.md`.

### 5. Hand off to the build agent (non-interactive)

The build is non-interactive by design: the build agent works only from the repo's
`CLAUDE.md` and `BUILD_PLAN.md`, with the scaffolded repo as its working
directory, and never talks to the maker. This is the `eval(BUILD_PLAN.md)` step.

**How you spawn that agent depends on your environment — pick whichever your
orchestrator actually provides; do not assume one mechanism:**

- A separate headless `claude` subprocess, when you have the CLI on PATH:
  ```
  cd <repos-dir>/<project-name> && claude -p "Read CLAUDE.md and BUILD_PLAN.md, then implement generate.py for this part. Render preview.py and visually verify preview.png before declaring the build done."
  ```
- A subagent / Task in an orchestrator that offers one — hand it the same brief
  (read `CLAUDE.md` and `BUILD_PLAN.md`, implement `generate.py`, verify
  `preview.png`) with the repo as its working directory.
- If you have neither, do the build yourself in a fresh, separate pass scoped to
  the repo — the invariant is *separate context working only from the repo
  files*, not a particular binary.

Whatever the mechanism, the contract is the same: the build agent reads only
`CLAUDE.md` + `BUILD_PLAN.md`, implements `build_part`, and visually verifies
`preview.png` before declaring done.

Before launching an unattended run, **confirm the permission posture with the
maker** — an autonomous build will want broad file/Bash permissions in that repo
(e.g. an accept-edits or skip-permissions mode). Let them choose; do not assume.

Stream the build agent's progress back to the maker. When it finishes, surface the
repo's `preview.png` so they can see the geometry, and offer to iterate — adjust
the plan, re-run the build, or open a slicer.

## Principles

- **One conversation.** Keep the maker in this session the whole way through.
- **The gate is sacred.** Stage 3's writing gate is the whole reason this skill
  exists — never write the brief and plan early.
- **Partwright is the tool; you are the conductor.** Use the CLI for the
  mechanical steps; spend your effort on the interview and on verifying the build.
